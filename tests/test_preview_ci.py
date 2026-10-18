"""Exercise the trust boundary without Cloudflare credentials or remote mutations."""

import copy
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import preview_ci as ci
import publish

HEAD, BASE, BUILD = "a" * 40, "b" * 40, "c" * 40
NOW = datetime(2026, 10, 17, tzinfo=timezone.utc)


def fixture():
    run = {"id": 101, "run_attempt": 2, "workflow_id": 10, "path": ci.WORKFLOW,
           "repository": {"full_name": ci.REPO}, "head_repository": {"full_name": ci.REPO},
           "event": "pull_request", "status": "completed", "conclusion": "success",
           "created_at": "2026-10-16T12:00:00Z", "head_sha": HEAD}
    pr = {"number": 5, "state": "open", "draft": False,
          "base": {"repo": {"full_name": ci.REPO}, "ref": "main", "sha": BASE},
          "head": {"repo": {"full_name": ci.REPO}, "sha": HEAD}, "merge_commit_sha": BUILD}
    commit = {"sha": BUILD, "parents": [{"sha": BASE}, {"sha": HEAD}]}
    return run, pr, commit


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.run, self.pr, self.commit = fixture()
        self.context = ci.validate_identity(self.run, self.pr, BASE, self.commit)

    def test_only_fresh_successful_same_repo_verification_is_accepted(self):
        ci.validate_run(self.run, 10, 101, 2, NOW)
        for change in ({"run_attempt": 3}, {"workflow_id": 11}, {"path": ".github/workflows/evil.yml"},
                       {"event": "push"}, {"conclusion": "failure"}, {"status": "in_progress"},
                       {"created_at": "2026-10-01T00:00:00Z"}, {"head_repository": {"full_name": "other/repo"}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                ci.validate_run({**self.run, **change}, 10, 101, 2, NOW)

    def test_stale_closed_draft_fork_wrong_base_and_non_merge_build_are_rejected(self):
        for field, value in (("state", "closed"), ("draft", True), ("merge_commit_sha", HEAD)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                ci.validate_identity(self.run, {**self.pr, field: value}, BASE, self.commit)
        for section, key, value in (("head", "sha", BASE), ("base", "sha", HEAD),
                                    ("base", "ref", "other"), ("head", "repo", {"full_name": "fork/repo"})):
            pr = copy.deepcopy(self.pr)
            pr[section][key] = value
            with self.subTest(section=section, key=key), self.assertRaises(ValueError):
                ci.validate_identity(self.run, pr, BASE, self.commit)
        with self.assertRaisesRegex(ValueError, "base/head merge"):
            ci.validate_identity(self.run, self.pr, BASE, {**self.commit, "parents": [{"sha": HEAD}]})

    def test_all_provenance_dimensions_and_artifact_attempt_must_match(self):
        metadata = {"expired": False, "workflow_run": {"id": 101, "head_sha": HEAD}, "name": f"site-{BUILD}-2"}
        version = {"ci": self.context, "source_commit": BUILD, "dirty": False}
        ci.validate_artifact(metadata, version, self.context)
        for key, wrong in (("run_id", 102), ("run_attempt", 1), ("pr", 6), ("head_sha", BASE),
                           ("base_sha", HEAD), ("build_sha", HEAD), ("repository", "other/repo")):
            altered = copy.deepcopy(version)
            altered["ci"][key] = wrong
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "provenance"):
                ci.validate_artifact(metadata, altered, self.context)
        for altered in ({**metadata, "expired": True}, {**metadata, "name": f"site-{BUILD}-1"},
                        {**metadata, "workflow_run": {"id": 102, "head_sha": HEAD}}):
            with self.assertRaises(ValueError):
                ci.validate_artifact(altered, version, self.context)

    def archive(self, replace=None, extra=None, symlink=False):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            for name in sorted(publish.FILES):
                item = zipfile.ZipInfo(replace if replace and name == "index.html" else name)
                if symlink and name == "index.html":
                    item.create_system = 3
                    item.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(item, "data")
            if extra:
                archive.writestr(extra, "data")
        return buffer.getvalue()

    def test_zip_rejects_paths_extra_files_links_and_duplicate_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            for kwargs in ({"replace": "../index.html"}, {"replace": "/index.html"},
                           {"extra": "package.json"}, {"symlink": True}, {"replace": "version.json"}):
                with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                    ci.unpack(self.archive(**kwargs), Path(temp) / "site")
            ci.unpack(self.archive(), Path(temp) / "site")
            self.assertEqual({p.name for p in (Path(temp) / "site").iterdir()}, publish.FILES)
            with self.assertRaisesRegex(ValueError, "empty"):
                ci.unpack(self.archive(), Path(temp) / "site")

    def test_archive_digest_is_checked_and_bearer_is_not_sent_to_blob(self):
        import hashlib
        from urllib.error import HTTPError
        from email.message import Message
        data = self.archive()
        headers = Message()
        headers["Location"] = "https://artifacts.blob.core.windows.net/container/signed"
        redirect = HTTPError("https://api.github.com", 302, "Found", headers, None)
        with patch.dict(os.environ, {"GH_TOKEN": "test-token"}), patch.object(ci, "build_opener") as opener, patch.object(ci, "urlopen") as fetch:
            opener.return_value.open.side_effect = redirect
            fetch.return_value.read.return_value = data
            ci.download({"id": 123, "digest": "sha256:" + hashlib.sha256(data).hexdigest()})
            self.assertNotIn("Authorization", fetch.call_args.args[0].headers)
            with self.assertRaisesRegex(ValueError, "digest"):
                ci.download({"id": 123, "digest": "sha256:wrong"})
            headers.replace_header("Location", "https://untrusted.example/download")
            with self.assertRaisesRegex(ValueError, "host"):
                ci.download({"id": 123, "digest": "sha256:wrong"})

    def test_urls_require_isolated_account_workers_dev_and_two_distinct_deployments(self):
        result = {"preview": {"name": "pr-5", "id": "preview-1", "urls": ["https://pr-5-model-observatory-preview.openai-proxy-local.workers.dev"]},
                  "deployment": {"id": "deployment-1", "urls": ["https://version-model-observatory-preview.openai-proxy-local.workers.dev"]}}
        self.assertIn("stable_url", ci.preview_urls(result, "pr-5"))
        for url in ("https://models.localgpt.net", "https://model-observatory.openai-proxy-local.workers.dev",
                    "https://other.workers.dev", "https://x.openai-proxy-local.workers.dev/path", "http://x.openai-proxy-local.workers.dev"):
            altered = copy.deepcopy(result)
            altered["preview"]["urls"] = [url]
            with self.subTest(url=url), self.assertRaises(ValueError):
                ci.preview_urls(altered, "pr-5")

    def test_upload_accepts_real_static_config_and_drops_github_credentials(self):
        from types import SimpleNamespace
        record = {"type": "preview", "version": 1, "worker_name": ci.WORKER,
                  "preview_name": "pr-5", "preview_id": "preview-1", "deployment_id": "deployment-1",
                  "preview_urls": ["https://pr-5-model-observatory-preview.openai-proxy-local.workers.dev"],
                  "deployment_urls": ["https://version-model-observatory-preview.openai-proxy-local.workers.dev"]}
        def fake_run(*args, **kwargs):
            Path(kwargs["env"]["WRANGLER_OUTPUT_FILE_PATH"]).write_text(json.dumps(record) + "\n")
            return SimpleNamespace(returncode=0, stdout="Asset upload progress\nnot pure JSON\n", stderr="")
        with patch.object(ci, "parent_exists"), patch.object(ci, "cf", return_value=None), \
                patch.dict(os.environ, {"GH_TOKEN": "unit-test", "GITHUB_TOKEN": "unit-test"}), \
                patch.object(ci.subprocess, "run", side_effect=fake_run) as run:
            published = ci.upload("pr-5", "config-regression", BUILD)
            self.assertEqual(published["deployment_id"], "deployment-1")
            env = run.call_args.kwargs["env"]
            self.assertNotIn("GH_TOKEN", env)
            self.assertNotIn("GITHUB_TOKEN", env)
            self.assertEqual(env["GITHUB_SHA"], BUILD)
            self.assertIn("preview", run.call_args.args[0])

    def test_upload_requires_one_matching_versioned_machine_record(self):
        from types import SimpleNamespace
        for records in (None, [], [{"type": "preview", "version": 2}],
                        [{"type": "preview", "version": 1}, {"type": "preview", "version": 1}],
                        [{"type": "preview", "version": 1, "worker_name": "other", "preview_name": "pr-5"}]):
            def fake_run(*args, **kwargs):
                if records is not None:
                    Path(kwargs["env"]["WRANGLER_OUTPUT_FILE_PATH"]).write_text(
                        "".join(json.dumps(record) + "\n" for record in records))
                return SimpleNamespace(returncode=0, stdout="untrusted progress", stderr="")
            with self.subTest(records=records), patch.object(ci, "parent_exists"), \
                    patch.object(ci, "cf", return_value=None), patch.object(ci.subprocess, "run", side_effect=fake_run):
                with self.assertRaises(ValueError):
                    ci.upload("pr-5", "output-contract")

    def test_upload_rejects_routes_bindings_and_non_release_asset_directory(self):
        config = json.loads((ci.ROOT / "wrangler.preview.json").read_text())
        for changed in ({**config, "routes": []}, {**config, "main": "worker.js"},
                        {**config, "previews": {"vars": {"UNEXPECTED": "binding"}}},
                        {**config, "assets": {**config["assets"], "directory": "./"}}):
            with self.subTest(config=changed), patch.object(ci, "parent_exists"), \
                    patch.object(Path, "read_text", return_value=json.dumps(changed)), \
                    patch.object(ci, "cf") as cf, patch.object(ci.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "static-only"):
                    ci.upload("pr-5", "config-regression")
                cf.assert_not_called()
                run.assert_not_called()

    def test_initialization_targets_only_dedicated_worker_with_checked_assets(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as temp, patch.object(ci, "RECORD", Path(temp) / "record.json"), \
                patch.object(ci, "parent_exists") as parent, patch.object(ci.publish, "check") as check, \
                patch.object(ci.publish, "git", return_value=BUILD), patch.object(ci.publish, "probe") as probe, \
                patch.object(ci.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
            ci.initialize()
            parent.assert_called_once()
            check.assert_called_once_with(ci.SITE, BUILD)
            self.assertEqual(run.call_args.args[0][-3:], ["deploy", "--config", "wrangler.preview.json"])
            probe.assert_called_once_with("https://model-observatory-preview.openai-proxy-local.workers.dev", ci.SITE)
            self.assertEqual(json.loads(ci.RECORD.read_text())["status"], "initialized")

    def test_cleanup_requires_closed_pr_and_never_deletes_parent(self):
        with patch.object(ci, "repo_api", return_value=self.pr), patch.object(ci, "delete_preview") as delete:
            with self.assertRaisesRegex(ValueError, "closed PR"):
                ci.cleanup(5)
            delete.assert_not_called()
        with patch.object(ci, "parent_exists"), patch.object(ci, "cf", side_effect=[{"id": "p"}, None, None]) as cf:
            self.assertEqual(ci.delete_preview("pr-5"), "deleted")
            self.assertEqual(cf.call_args_list[1].args, ("/previews/pr-5",))
            self.assertEqual(cf.call_args_list[1].kwargs, {"method": "DELETE"})
        with self.assertRaisesRegex(ValueError, "target"):
            ci.delete_preview(ci.WORKER)
        with patch.object(ci, "parent_exists"), patch.object(ci, "cf", side_effect=ValueError("HTTP 403")) as cf:
            with self.assertRaisesRegex(ValueError, "403"):
                ci.delete_preview("pr-5")
            self.assertEqual(cf.call_count, 1)

    def test_smoke_updates_probes_and_cleans_without_reusing_production(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(ci, "RECORD", Path(temp) / "record.json"), \
                patch.object(ci.publish, "check"), patch.object(ci.publish, "git", return_value=BUILD), \
                patch.object(ci.publish, "probe") as probe, patch.object(ci, "delete_preview", return_value="deleted") as delete, \
                patch.object(ci, "upload", side_effect=[
                    {"stable_url": "https://stable", "deployment_url": "https://first", "deployment_id": "one"},
                    {"stable_url": "https://stable", "deployment_url": "https://second", "deployment_id": "two"}]):
            ci.smoke()
            self.assertEqual(json.loads(ci.RECORD.read_text())["status"], "passed")
            self.assertEqual(probe.call_count, 5)
            self.assertEqual([c.args[0] for c in delete.call_args_list], ["permission-smoke", "permission-smoke"])

    def test_stale_after_upload_is_removed_and_never_reported_verified(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(ci, "CONTEXT", Path(temp) / "context.json"), \
                patch.object(ci, "RECORD", Path(temp) / "record.json"), patch.object(ci, "still_current", side_effect=[None, ValueError("advanced")]), \
                patch.object(ci.publish, "check"), patch.object(ci, "upload", return_value={}), \
                patch.object(ci, "delete_preview", return_value="deleted") as delete:
            ci.save(ci.CONTEXT, self.context)
            with self.assertRaisesRegex(ValueError, "advanced"):
                ci.deploy()
            self.assertEqual(json.loads(ci.RECORD.read_text())["status"], "stale-removed")
            delete.assert_called_once_with("pr-5")

    def test_build_records_ci_provenance_without_tokens(self):
        with tempfile.TemporaryDirectory() as temp:
            event = Path(temp) / "event.json"
            event.write_text(json.dumps({"number": 5, "pull_request": self.pr}))
            with patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "GITHUB_SHA": BUILD, "GITHUB_REPOSITORY": ci.REPO,
                                         "GITHUB_RUN_ID": "101", "GITHUB_RUN_ATTEMPT": "2", "GITHUB_EVENT_NAME": "pull_request",
                                         "GITHUB_EVENT_PATH": str(event)}, clear=True):
                self.assertEqual(publish.ci_context(BUILD), self.context)
                with self.assertRaisesRegex(ValueError, "Checkout"):
                    publish.ci_context(HEAD)


if __name__ == "__main__":
    unittest.main()
