"""Trusted-main bridge from a tested static artifact to native Worker Previews.

Never imports, checks out or executes PR code. No third-party Python dependencies.
"""

import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
import zipfile

import publish

REPO = "pysugar/model-observatory"
ACCOUNT = "cf37bfe5ee78022d9099c57673e50dbc"
WORKER = "model-observatory-preview"
WORKFLOW = ".github/workflows/verify.yml"
ROOT = publish.ROOT
SITE = ROOT / "dist"
EVIDENCE = ROOT / "test-results/preview"
CONTEXT = EVIDENCE / "context.json"
RECORD = EVIDENCE / "deployment.json"
MARKER = "<!-- model-observatory-native-preview -->"
MAX_ZIP = 25_000_000
require = publish.require


def positive(value):
    require(re.fullmatch(r"[1-9][0-9]{0,11}", str(value)) is not None, "Invalid numeric identifier")
    return int(value)


def sha(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None, "Invalid commit SHA")
    return value


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def output(**values):
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as handle:
            for key, value in values.items():
                require("\n" not in str(value), "Invalid workflow output")
                handle.write(f"{key}={value}\n")


def github(path, method="GET", data=None):
    require(path.startswith("/") and not path.startswith("//"), "Invalid GitHub path")
    token = os.environ["GH_TOKEN"]
    request = Request("https://api.github.com" + path, method=method,
                      data=json.dumps(data).encode() if data is not None else None,
                      headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                               "Content-Type": "application/json", "User-Agent": publish.PROBE_USER_AGENT,
                               "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        raise ValueError(f"GitHub {method} {path}: HTTP {error.code}") from None


def repo_api(path, **kwargs):
    return github(f"/repos/{REPO}{path}", **kwargs)


def pages(path):
    result = []
    for page in range(1, 32):
        items = repo_api(f"{path}{'&' if '?' in path else '?'}per_page=100&page={page}")
        require(isinstance(items, list), "Expected a paginated list")
        result.extend(items)
        if len(items) < 100:
            return result
    raise ValueError("Too many records; manual review required")


def validate_run(run, workflow_id, run_id, attempt, now=None):
    now = now or datetime.now(timezone.utc)
    require(run["id"] == positive(run_id) and run["run_attempt"] == positive(attempt), "Run attempt changed")
    require(run["workflow_id"] == workflow_id and run["path"] == WORKFLOW, "Unexpected verification workflow")
    require(run["repository"]["full_name"] == REPO and run["head_repository"]["full_name"] == REPO,
            "Only same-repository PR artifacts can be published")
    require(run["event"] == "pull_request" and run["status"] == "completed" and run["conclusion"] == "success",
            "Expected a successful completed PR verification")
    created = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
    require(timedelta(0) <= now - created <= timedelta(days=7), "Verification run is expired")
    sha(run["head_sha"])


def validate_identity(run, pr, main_sha, merge_commit):
    require(pr["state"] == "open" and not pr["draft"], "PR is closed or draft")
    require(pr["base"]["repo"]["full_name"] == REPO and pr["base"]["ref"] == "main", "Unexpected PR base")
    require(pr["head"]["repo"]["full_name"] == REPO, "External PRs receive build checks only")
    require(pr["head"]["sha"] == run["head_sha"], "PR head advanced; verify its current commit")
    require(pr["base"]["sha"] == main_sha, "PR base is stale")
    require(merge_commit["sha"] == pr["merge_commit_sha"], "PR merge build changed")
    require([p["sha"] for p in merge_commit["parents"]] == [main_sha, run["head_sha"]],
            "Build commit is not the current base/head merge")
    return {"repository": REPO, "run_id": run["id"], "run_attempt": run["run_attempt"],
            "event": "pull_request", "pr": positive(pr["number"]), "head_repository": REPO,
            "head_sha": sha(run["head_sha"]), "base_sha": sha(main_sha), "base_ref": "main",
            "build_sha": sha(merge_commit["sha"])}


def current_context(run_id, attempt, pr_number=None):
    workflow = repo_api("/actions/workflows/verify.yml")
    run = repo_api(f"/actions/runs/{positive(run_id)}")
    validate_run(run, workflow["id"], run_id, attempt)
    if pr_number is None:
        candidates = repo_api(f"/commits/{run['head_sha']}/pulls")
        candidates = [p for p in candidates if p["state"] == "open" and p["head"]["sha"] == run["head_sha"]
                      and p["base"]["ref"] == "main" and p["base"]["repo"]["full_name"] == REPO]
        require(len(candidates) == 1, "Cannot identify one current PR for this verification run")
        pr_number = candidates[0]["number"]
    pr = repo_api(f"/pulls/{positive(pr_number)}")
    main_sha = repo_api("/branches/main")["commit"]["sha"]
    merge_sha = sha(pr["merge_commit_sha"])
    commit = repo_api(f"/commits/{merge_sha}")
    return validate_identity(run, pr, main_sha, commit)


def resolve():
    require(os.environ.get("GITHUB_REPOSITORY") == REPO and os.environ.get("GITHUB_REF") == "refs/heads/main",
            "This entry point only runs from trusted main")
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    kind = os.environ["GITHUB_EVENT_NAME"]
    if kind == "workflow_run":
        run = event["workflow_run"]
        context = current_context(run["id"], run["run_attempt"])
        output(mode="deploy", pr=context["pr"], run_id=context["run_id"], attempt=context["run_attempt"])
    elif kind == "pull_request_target":
        require(event["action"] == "closed", "Unexpected PR target action")
        output(mode="cleanup", pr=positive(event["number"]))
    else:
        require(kind == "workflow_dispatch", "Unexpected workflow event")
        mode = event["inputs"]["operation"]
        require(mode in {"permission-smoke", "cleanup", "cleanup-smoke"}, "Unexpected manual operation")
        output(mode=mode, pr=positive(event["inputs"]["pr"]) if mode == "cleanup" else "smoke")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def download(artifact):
    """Do not forward the GitHub bearer token to the signed blob redirect."""
    request = Request(f"https://api.github.com/repos/{REPO}/actions/artifacts/{positive(artifact['id'])}/zip",
                      headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"],
                               "User-Agent": publish.PROBE_USER_AGENT})
    try:
        response = build_opener(NoRedirect()).open(request, timeout=30)
    except HTTPError as error:
        require(error.code == 302, f"Artifact download: HTTP {error.code}")
        location = error.headers["Location"]
        parts = urlsplit(location)
        require(parts.scheme == "https" and parts.username is None and parts.port is None and
                any((parts.hostname or "").endswith(suffix) for suffix in
                    (".blob.core.windows.net", ".actions.githubusercontent.com", ".githubusercontent.com")),
                "Unexpected artifact download host")
        response = urlopen(Request(location, headers={"User-Agent": publish.PROBE_USER_AGENT}), timeout=60)
    with response:
        data = response.read(MAX_ZIP + 1)
    require(len(data) <= MAX_ZIP, "Artifact archive too large")
    require(artifact.get("digest") == "sha256:" + hashlib.sha256(data).hexdigest(), "Artifact archive digest mismatch")
    return data


def unpack(data, destination):
    """Read exactly five bounded regular files; never extract arbitrary ZIP paths."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = archive.infolist()
        require(len(entries) == 5 and {i.filename for i in entries} == publish.FILES, "Expected exactly five public files")
        contents = {}
        for item in entries:
            mode = item.external_attr >> 16
            require(not item.is_dir() and stat.S_IFMT(mode) in {0, stat.S_IFREG}, "Archive entry is not a regular file")
            require(not item.flag_bits & 1 and 0 < item.file_size < 5_000_000, "Invalid archive entry size or encryption")
            require(item.compress_type in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}, "Unsupported archive compression")
            contents[item.filename] = archive.read(item)
    require(not destination.is_symlink() and (not destination.exists() or not any(destination.iterdir())),
            "Artifact destination must be empty")
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in contents.items():
        (destination / name).write_bytes(content)


def validate_artifact(metadata, version, context):
    require(not metadata["expired"], "Artifact has expired")
    require(metadata["workflow_run"]["id"] == context["run_id"] and
            metadata["workflow_run"]["head_sha"] == context["head_sha"], "Artifact run/head mismatch")
    require(metadata["name"] == f"site-{context['build_sha']}-{context['run_attempt']}", "Artifact name mismatch")
    require(version.get("ci") == context and version["source_commit"] == context["build_sha"] and
            version["dirty"] is False, "Artifact PR/run/head/base/build provenance mismatch")


def prepare(run_id, attempt, pr_number):
    context = current_context(run_id, attempt, pr_number)
    artifacts = repo_api(f"/actions/runs/{context['run_id']}/artifacts?per_page=100")["artifacts"]
    expected = f"site-{context['build_sha']}-{context['run_attempt']}"
    matches = [a for a in artifacts if a["name"] == expected]
    require(len(matches) == 1 and not matches[0]["expired"], "One unexpired artifact is required")
    artifact = matches[0]
    require(artifact["size_in_bytes"] <= MAX_ZIP, "Artifact archive too large")
    unpack(download(artifact), SITE)
    version = json.loads((SITE / "version.json").read_text())
    validate_artifact(artifact, version, context)
    counts = publish.check(SITE, context["build_sha"])
    changed = pages(f"/pulls/{context['pr']}/files")
    baseline = json.loads((ROOT / "report-data.json").read_text())
    data = json.loads((SITE / "report-data.json").read_text())
    old_models = {m["id"]: m for m in baseline["models"]}
    new_models = {m["id"]: m for m in data["models"]}
    changed_models = sum(old_models.get(key) != new_models.get(key) for key in old_models.keys() | new_models.keys())
    categories = set()
    for item in changed:
        name = item["filename"]
        if name.startswith("research/") or name == "report-content.json":
            categories.add("研究数据/说明")
        elif name in {"report.js", "report.css", "report.template.html"}:
            categories.add("页面")
        elif name.startswith(("scripts/", ".github/", "tests/", "wrangler")) or name in {"package.json", "package-lock.json", "build_report.py"}:
            categories.add("构建/发布")
        else:
            categories.add("文档/其他")
    context.update(artifact_id=artifact["id"], artifact_digest=artifact["digest"],
                   reviewed_at=date.fromisoformat(version["report_reviewed_at"]).isoformat(), counts={k: counts[k] for k in ("rows", "models", "sources")},
                   previous_counts={k: len(baseline[k]) for k in ("rows", "models", "sources")},
                   changed_files=len(changed), change_categories=sorted(categories), changed_model_records=changed_models, publisher_sha=publish.git("rev-parse", "HEAD"))
    save(CONTEXT, context)


def still_current(context):
    fresh = current_context(context["run_id"], context["run_attempt"], context["pr"])
    require(all(context[k] == value for k, value in fresh.items()), "PR or verification changed; refusing stale artifact")


def cf(path="", method="GET", missing_ok=False, missing_codes=(10025,)):
    require(os.environ.get("CLOUDFLARE_ACCOUNT_ID") == ACCOUNT, "Unexpected Cloudflare account")
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    require(bool(token), "Preview Environment token is missing")
    endpoint = f"/accounts/{ACCOUNT}/workers/workers/{WORKER}{path}"
    request = Request("https://api.cloudflare.com/client/v4" + endpoint, method=method,
                      headers={"Authorization": "Bearer " + token, "User-Agent": publish.PROBE_USER_AGENT})
    try:
        with urlopen(request, timeout=30) as response:
            data = json.load(response)
    except HTTPError as error:
        try:
            codes = [e.get("code") for e in json.load(error).get("errors", [])]
        except (ValueError, AttributeError):
            codes = []
        if missing_ok and error.code == 404 and any(code in codes for code in missing_codes):
            return None
        raise ValueError(f"Cloudflare {method} {endpoint}: HTTP {error.code}, codes {codes}; do not expand token scope automatically") from None
    require(data.get("success") is True, f"Cloudflare {method} {endpoint} did not confirm success")
    return data.get("result")


def parent_exists():
    require(cf()["name"] == WORKER, "Dedicated preview Worker must already exist")


def delete_preview(name):
    require(re.fullmatch(r"pr-[1-9][0-9]{0,11}|permission-smoke", name) is not None, "Unexpected cleanup target")
    parent_exists()
    path = f"/previews/{name}"
    if cf(path, missing_ok=True) is None:
        return "already-absent"
    cf(path, method="DELETE")
    require(cf(path, missing_ok=True) is None, "Preview deletion is not confirmed")
    return "deleted"


def preview_urls(result, name):
    require(result["preview"]["name"] == name, "Unexpected returned Preview name")
    urls = []
    for item in (result["preview"], result["deployment"]):
        candidates = item.get("urls", [])
        require(len(candidates) == 1, "Expected one workers.dev URL; no custom Preview domains")
        url = candidates[0]
        parts = urlsplit(url)
        require(parts.scheme == "https" and parts.username is None and parts.port is None and
                (parts.hostname or "").endswith(f"-{WORKER}.openai-proxy-local.workers.dev") and
                parts.path in {"", "/"} and not parts.query and not parts.fragment and
                parts.hostname != "model-observatory.openai-proxy-local.workers.dev", "Unexpected Preview URL")
        require(re.fullmatch(r"[A-Za-z0-9_-]{1,128}", item["id"]) is not None, "Invalid Cloudflare identifier")
        urls.append(url.rstrip("/"))
    require(urls[0] != urls[1], "Stable and unique deployment URLs must differ")
    return {"stable_url": urls[0], "deployment_url": urls[1], "preview_id": result["preview"]["id"],
            "deployment_id": result["deployment"]["id"]}


def upload(name, tag, build_sha=None):
    parent_exists()  # Prevent Wrangler's parent auto-provision fallback.
    config = json.loads((ROOT / "wrangler.preview.json").read_text())
    require(config["name"] == WORKER and config["previews"] == {} and config["preview_urls"] is True and config["workers_dev"] is True and
            config["assets"] == {"directory": "./dist", "html_handling": "auto-trailing-slash", "not_found_handling": "none"} and
            set(config) == {"$schema", "name", "compatibility_date", "workers_dev", "preview_urls", "assets"},
            "Preview configuration must remain static-only without bindings or routes")
    existing = cf(f"/previews/{name}", missing_ok=True)
    if existing is not None:
        latest = cf(f"/previews/{name}/deployments/latest", missing_ok=True, missing_codes=(10025, 10222))
        require(latest is None or not latest.get("env"), "Existing Preview has bindings/secrets; review it before publishing")
    # Only trusted-main dependencies/config run here; no PR source, .env, cache or package hooks.
    child_env = {key: value for key, value in os.environ.items() if key not in {"GH_TOKEN", "GITHUB_TOKEN"}}
    if build_sha:
        child_env["GITHUB_SHA"] = sha(build_sha)  # Artifact identity; checkout remains trusted main.
    result = subprocess.run(["node", "node_modules/wrangler/bin/wrangler.js", "preview", "--config", "wrangler.preview.json",
                             "--name", name, "--ignore-base-config", "--tag", tag, "--message", tag, "--json"],
                            cwd=ROOT, text=True, capture_output=True, timeout=240, env=child_env)
    if result.returncode != 0:
        diagnostic = result.stdout + result.stderr
        codes = sorted(set(re.findall(r"(?:code|status):\s*(\d+)", diagnostic)))
        endpoints = sorted(set(re.findall(r"/accounts/" + ACCOUNT + r"/workers/[a-zA-Z0-9_/-]+", diagnostic)))
        raise ValueError(f"Wrangler preview {WORKER}/{name} failed; codes {codes}, endpoints {endpoints}. "
                         "Remote outcome may be uncertain; inspect this Preview before retrying. Token scope was not changed.")
    try:
        value = json.loads(result.stdout)
    except ValueError:
        raise ValueError("Wrangler did not return expected JSON; upload outcome is uncertain") from None
    return preview_urls(value, name)


def deploy():
    context = json.loads(CONTEXT.read_text())
    still_current(context)
    publish.check(SITE, context["build_sha"])
    name = f"pr-{positive(context['pr'])}"
    record = {**context, "worker": WORKER, "preview_name": name, "status": "upload-started",
              "recorded_at": datetime.now(timezone.utc).isoformat()}
    save(RECORD, record)
    record.update(upload(name, f"pr-{context['pr']}-{context['head_sha'][:12]}-run-{context['run_id']}-{context['run_attempt']}", context["build_sha"]), status="uploaded")
    save(RECORD, record)
    try:
        still_current(context)
    except ValueError:
        record.update(status="stale-removed", cleanup=delete_preview(name))
        save(RECORD, record)
        raise
    for url in (record["stable_url"], record["deployment_url"]):
        publish.probe(url, SITE)
    try:
        still_current(context)
    except ValueError:
        record.update(status="stale-removed", cleanup=delete_preview(name))
        save(RECORD, record)
        raise
    record["status"] = "verified"
    save(RECORD, record)
    output(url=record["stable_url"])


def cleanup(pr_number):
    number = positive(pr_number)
    pr = repo_api(f"/pulls/{number}")
    require(pr["state"] == "closed" and pr["base"]["repo"]["full_name"] == REPO, "Cleanup requires a closed PR in this repository")
    name = f"pr-{number}"
    record = {"pr": number, "worker": WORKER, "preview_name": name, "status": "cleanup-started"}
    save(RECORD, record)
    record.update(status="closed", cleanup=delete_preview(name))
    save(RECORD, record)


def smoke():
    publish.check(SITE, publish.git("rev-parse", "HEAD"))
    record = {"worker": WORKER, "preview_name": "permission-smoke", "checks": [], "status": "started"}
    save(RECORD, record)
    record["initial_cleanup"] = delete_preview("permission-smoke")
    try:
        first = upload("permission-smoke", "permission-create")
        record["checks"].append({"action": "create", **first})
        save(RECORD, record)
        for url in (first["stable_url"], first["deployment_url"]):
            publish.probe(url, SITE)
        second = upload("permission-smoke", "permission-update")
        require(first["stable_url"] == second["stable_url"] and first["deployment_id"] != second["deployment_id"],
                "Preview update did not produce a new deployment with the same stable URL")
        record["checks"].append({"action": "update", **second})
        save(RECORD, record)
        for url in (first["deployment_url"], second["stable_url"], second["deployment_url"]):
            publish.probe(url, SITE)
        record["status"] = "create-update-verified"
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        record.update(status="create-update-failed", error=str(error))
        raise
    finally:
        try:
            record["cleanup"] = delete_preview("permission-smoke")
            if record["status"] == "create-update-verified":
                record["status"] = "passed"
        except (ValueError, OSError) as error:
            record["cleanup_error"] = str(error)
            record["status"] = "cleanup-failed"
            raise
        finally:
            save(RECORD, record)


def comment(pr_number):
    number = positive(pr_number)
    record = json.loads(RECORD.read_text())
    require(record.get("pr") == number and record["status"] in {"verified", "closed"}, "No confirmed deployment/cleanup to announce")
    if record["status"] == "closed":
        body = f"{MARKER}\n此 PR 的临时预览已清理，稳定地址与此前的 Unique Deployment URLs 均已失效。"
    else:
        still_current(record)
        counts = " / ".join(f"{label} {record['previous_counts'][key]} → {record['counts'][key]}" for key, label in
                            (("models", "模型"), ("rows", "数据行"), ("sources", "来源")))
        body = (f"{MARKER}\n[最新预览]({record['stable_url']}) · [本次固定部署]({record['deployment_url']})\n\n"
                f"Head `{record['head_sha']}` · Base `{record['base_sha']}`\n\n"
                f"Build `{record['build_sha']}` · [验证 run {record['run_id']} / attempt {record['run_attempt']}]"
                f"(https://github.com/{REPO}/actions/runs/{record['run_id']})\n\n"
                f"变更 {record['changed_files']} 个文件（{'、'.join(record['change_categories'])}）；{counts}。"
                f"新增/修改/删除模型记录 {record['changed_model_records']} 条。内容日期：{record['reviewed_at']}。\n\n"
                f"Cloudflare deployment `{record['deployment_id']}`；发布记录见本工作流的 `preview-record` artifact。"
                "固定地址对应本次部署，但可能因历史配额或 PR 关闭清理而失效。CI 不代表研究结论已复核。")
    comments = pages(f"/issues/{number}/comments")
    matches = [c for c in comments if c["user"]["login"] == "github-actions[bot]" and c["body"].startswith(MARKER)]
    if matches:
        repo_api(f"/issues/comments/{positive(matches[0]['id'])}", method="PATCH", data={"body": body})
    else:
        repo_api(f"/issues/{number}/comments", method="POST", data={"body": body})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["resolve", "prepare", "deploy", "cleanup", "smoke", "cleanup-smoke", "comment"])
    parser.add_argument("--run-id")
    parser.add_argument("--attempt")
    parser.add_argument("--pr")
    args = parser.parse_args()
    try:
        if args.command == "resolve":
            resolve()
        elif args.command == "prepare":
            prepare(args.run_id, args.attempt, args.pr)
        elif args.command == "deploy":
            deploy()
        elif args.command == "cleanup":
            cleanup(args.pr)
        elif args.command == "smoke":
            smoke()
        elif args.command == "cleanup-smoke":
            save(RECORD, {"worker": WORKER, "preview_name": "permission-smoke", "status": delete_preview("permission-smoke")})
        else:
            comment(args.pr)
    except (ValueError, KeyError, OSError, zipfile.BadZipFile, subprocess.TimeoutExpired) as error:
        # No token, raw Cloudflare response, signed URL, PR code or Wrangler log is printed.
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        (EVIDENCE / "failure.txt").write_text(f"{args.command}: {error}\n")
        parser.exit(1, f"{args.command}: {error}\n")


if __name__ == "__main__":
    main()
