"""Release gates: evidence preservation, reproducibility, leaks and stale versions."""

import contextlib
import copy
import io
import json
import os
import shutil
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import publish


class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.temp.name) / "base"
        publish.build(cls.base)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.site = Path(self.work.name) / "site"
        shutil.copytree(self.base, self.site)

    def tearDown(self):
        self.work.cleanup()

    def test_release_is_reproducible_and_preserves_evidence(self):
        other = Path(self.work.name) / "second"
        publish.build(other)
        self.assertEqual({p.name: p.read_bytes() for p in self.base.iterdir()}, {p.name: p.read_bytes() for p in other.iterdir()})
        result = publish.check(other)
        self.assertEqual((result["rows"], result["models"]), (169, 29))

    def test_unknown_files_and_symlinks_are_rejected(self):
        (self.site / "secret.txt").write_text("not for publication")
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            publish.check(self.site)
        with self.assertRaisesRegex(ValueError, "non-release"):
            publish.build(self.site)
        (self.site / "secret.txt").unlink()
        (self.site / "report-data.csv").unlink()
        (self.site / "report-data.csv").symlink_to(self.base / "report-data.csv")
        with self.assertRaisesRegex(ValueError, "regular files"):
            publish.check(self.site)

    def test_tampered_artifact_and_wrong_commit_fail(self):
        with self.assertRaisesRegex(ValueError, "requested clean commit"):
            publish.check(self.site, "0" * 40)
        with (self.site / "index.html").open("a") as handle:
            handle.write("tampered")
        with self.assertRaisesRegex(ValueError, "checksum"):
            publish.check(self.site)

    def test_sensitive_material_is_rejected_without_echoing_value(self):
        for text in ("person@example.org", "/Users/person/private", "ghp_" + "x" * 30, "-----BEGIN PRIVATE KEY-----", 'api_token="' + "x" * 32 + '"'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as error:
                    publish.audit_text("test", text.encode())
                self.assertNotIn(text, str(error.exception))

    def test_model_identity_and_csv_mismatch_are_rejected(self):
        data = json.loads((self.site / "report-data.json").read_text())
        html = (self.site / "index.html").read_text()
        csv = (self.site / "report-data.csv").read_bytes()
        with self.assertRaisesRegex(ValueError, "CSV differs"):
            publish.validate_data(data, csv.replace(b"general", b"wrong", 1), html)
        changed = copy.deepcopy(data)
        changed["models"][1]["id"] = changed["models"][0]["id"]
        old_payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        new_payload = json.dumps(changed, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        with self.assertRaisesRegex(ValueError, "Duplicate model"):
            publish.validate_data(changed, csv, html.replace(old_payload, new_payload))

    def test_dirty_worktree_cannot_be_a_release(self):
        def fake_git(*args):
            return " M README.md" if args[0] == "status" else "a" * 40
        with patch.object(publish, "git", side_effect=fake_git):
            with self.assertRaisesRegex(ValueError, "clean committed"):
                publish.build(Path(self.work.name) / "dirty", require_clean=True)

    def test_live_probe_rejects_old_version(self):
        class Response(io.BytesIO):
            status = 200
            headers = {"X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"}
        old = json.loads((self.site / "version.json").read_text())
        old["source_commit"] = "0" * 40
        with patch.object(publish, "urlopen", return_value=Response(json.dumps(old).encode())):
            with self.assertRaisesRegex(ValueError, "does not match"):
                publish.probe("https://example.org", self.site, attempts=1)

    def test_live_probe_identifies_itself_and_verifies_all_public_assets(self):
        site, requested = self.site, []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                agent = self.headers.get("User-Agent", "")
                if not agent or agent.startswith("Python-urllib/"):
                    self.send_error(403, "Unidentified generic client")
                    return
                path = urlsplit(self.path).path
                requested.append(path)
                name = "index.html" if path == "/" else path.lstrip("/")
                self.send_response(200)
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write((site / name).read_bytes())

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            result = publish.probe(f"http://127.0.0.1:{server.server_port}", site, attempts=1)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(requested, ["/version.json", "/", "/report-data.json", "/report-data.csv"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_footer_escapes_refs_and_only_links_verified_commits(self):
        identity = {"environment": "preview", "branch": 'feature/<img src=x>&"',
                    "build_sha": "a" * 40, "head_sha": "b" * 40, "pr": 10,
                    "dirty": False, "tags": ["release/v1&2"]}
        html = publish.build_footer(identity)
        self.assertIn("feature/&lt;img src=x&gt;&amp;&quot;", html)
        self.assertNotIn("<img", html)
        self.assertIn("/tree/release%2Fv1%262", html)
        self.assertIn("/commit/" + "a" * 40, html)
        self.assertIn("/commit/" + "b" * 40, html)
        self.assertIn("源提交", html)
        self.assertIn("构建", html)
        with self.assertRaisesRegex(ValueError, "commit"):
            publish.build_footer({**identity, "build_sha": "not-a-commit"})

    def test_footer_identity_uses_actual_pr_and_main_build_context(self):
        event = Path(self.work.name) / "event.json"
        event.write_text(json.dumps({"pull_request": {"head": {"ref": "feature/footer"}}}))
        context = {"repository": "pysugar/model-observatory", "event": "pull_request", "pr": 10, "head_sha": "b" * 40}
        def fake_git(*args):
            return "v1.2.3" if args[0] == "tag" else ""
        with patch.dict(os.environ, {"GITHUB_EVENT_PATH": str(event), "GITHUB_REF": "refs/pull/10/merge"}, clear=True), patch.object(publish, "git", side_effect=fake_git):
            preview = publish.deployment_identity("a" * 40, False, context)
            self.assertEqual((preview["environment"], preview["branch"], preview["head_sha"], preview["build_sha"]),
                             ("preview", "feature/footer", "b" * 40, "a" * 40))
            self.assertEqual(preview["tags"], ["v1.2.3"])
            os.environ["GITHUB_REF"] = "refs/heads/main"
            release = publish.deployment_identity("c" * 40, False, {**context, "event": "push"})
            self.assertEqual((release["environment"], release["branch"]), ("release", "main"))
            self.assertNotIn("head_sha", release)

    def test_footer_must_match_version_metadata_even_if_hash_is_updated(self):
        version = json.loads((self.site / "version.json").read_text())
        html = (self.site / "index.html").read_text().replace('aria-label="构建版本"', 'aria-label="wrong"')
        (self.site / "index.html").write_text(html)
        version["assets"]["index.html"] = publish.sha256(html.encode())
        (self.site / "version.json").write_text(json.dumps(version))
        with self.assertRaisesRegex(ValueError, "Footer differs"):
            publish.check(self.site)

    def test_release_has_no_runtime_or_research_copies(self):
        config = json.loads((publish.ROOT / "wrangler.json").read_text())
        self.assertNotIn("main", config)
        self.assertNotIn("routes", config)
        self.assertEqual(config["assets"]["directory"], "./dist")
        self.assertEqual(config["assets"]["not_found_handling"], "none")
        self.assertEqual({p.name for p in self.site.iterdir()}, publish.FILES)


if __name__ == "__main__":
    unittest.main()
