"""Build, audit and probe the static release; no deployment or credentials here."""

import argparse
import base64
import csv
import hashlib
import io
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ASSETS = {"index.html", "report-data.json", "report-data.csv", "_headers"}
FILES = ASSETS | {"version.json"}
PROBE_USER_AGENT = "model-observatory-release-probe/1.0 (+https://github.com/pysugar/model-observatory)"
SENSITIVE = {
    "private key": r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----",
    "access token": r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16})\b",
    "credential assignment": r"(?i)(?:api[_-]?key|api[_-]?token|client[_-]?secret|password)\s*[\"']?\s*[:=]\s*[\"'][A-Za-z0-9_+/=-]{16,}[\"']",
    "personal email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "local filesystem path": r"(?:/Users/|/home/|/opt/foundry/|file:///|[A-Z]:\\Users\\)",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def audit_text(name, content):
    text = content.decode("utf-8-sig")
    for label, pattern in SENSITIVE.items():
        require(not re.search(pattern, text), f"Public artifact {name}: possible {label}; inspect locally (value withheld)")


class Resources(HTMLParser):
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        require(tag not in {"iframe", "object", "embed", "form"}, f"Unexpected active element: {tag}")
        require(not any(k.startswith("on") for k in attrs), "Inline event handler needs review")
        if tag in {"script", "img", "link", "video", "audio", "source"}:
            require(not attrs.get("src") and not attrs.get("href"), "Report must have no external loaded resources")


def validate_data(data, csv_bytes, html):
    embedded = re.search(r'<script id="report-data" type="application/json">(.*?)</script>', html, re.S)
    require(embedded is not None and json.loads(embedded[1]) == data, "HTML embedded data differs from JSON")
    rows = data["rows"]
    models = data["models"]
    names = {m["name"] for m in models}
    require(len(names) == len(models) == len({m["id"] for m in models}), "Duplicate model identity")
    require([r["id"] for r in rows] == list(range(len(rows))), "Row IDs must be unique and sequential")
    require(all(r["model"] in names for r in rows), "Unknown row model")
    require(all(p["model"] in names for p in data["aa_profiles"]), "Unknown profile model")
    for row in rows:
        require(row["benchmark"] in {"general", "coding", "writing", "arena"}, "Unknown benchmark; review comparability")
        for key in ("score", "cost_usd"):
            value = row.get(key)
            require(value is None or (isinstance(value, (int, float)) and math.isfinite(value)), f"Invalid numeric {key}")
        require(row.get("cost_usd") is None or row["cost_usd"] >= 0, "Negative task cost")
    fields = list(dict.fromkeys(key for row in rows for key in row))
    expected = io.StringIO(newline="")
    writer = csv.DictWriter(expected, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()})
    require(csv_bytes == expected.getvalue().encode("utf-8-sig"), "CSV differs from JSON (including missing values)")
    Resources().feed(html)
    return {"rows": len(rows), "models": len(models), "sources": len(data["sources"])}


def validate_sources(data, html):
    original = (ROOT / "archive/model-capability-cost-2026-10-14.html").read_text(encoding="utf-8")
    original_rows = json.loads(re.search(r'<script id="dataset" type="application/json">(.*?)</script>', original, re.S)[1])["rows"]
    require(len(data["rows"]) >= len(original_rows), "Original evidence was removed")
    for old, new in zip(original_rows, data["rows"]):
        require({key: new.get(key) for key in old} == old, "Original evidence changed")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    expected = (ROOT / "report.template.html").read_text(encoding="utf-8")
    expected = expected.replace("/* REPORT_CSS */", (ROOT / "report.css").read_text(encoding="utf-8"))
    expected = expected.replace("REPORT_DATA_JSON", payload)
    expected = expected.replace("/* REPORT_JS */", (ROOT / "report.js").read_text(encoding="utf-8"))
    require(html == expected, "Published HTML differs from current sources")


def headers_for(html):
    scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, re.S)
    hashes = " ".join("'sha256-" + base64.b64encode(hashlib.sha256(s.encode()).digest()).decode() + "'" for s in scripts)
    return (
        "/*\n"
        "  Cache-Control: public, max-age=0, must-revalidate, no-transform\n"
        "  X-Content-Type-Options: nosniff\n"
        "  X-Frame-Options: DENY\n"
        "  Referrer-Policy: no-referrer\n"
        f"  Content-Security-Policy: default-src 'none'; script-src {hashes}; style-src 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'\n"
        "/version.json\n  Cache-Control: no-store\n"
    ).encode()


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", *args], cwd=ROOT, text=True).strip()


def ci_context(commit):
    """Record public build identity; the publisher verifies it against GitHub."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return None
    require(os.environ["GITHUB_SHA"] == commit, "Checkout differs from CI build SHA")
    context = {"repository": os.environ["GITHUB_REPOSITORY"],
               "run_id": int(os.environ["GITHUB_RUN_ID"]),
               "run_attempt": int(os.environ["GITHUB_RUN_ATTEMPT"]),
               "event": os.environ["GITHUB_EVENT_NAME"], "build_sha": commit}
    if context["event"] == "pull_request":
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
        pr = event["pull_request"]
        context.update(pr=event["number"], head_sha=pr["head"]["sha"],
                       base_sha=pr["base"]["sha"], base_ref=pr["base"]["ref"],
                       head_repository=pr["head"]["repo"]["full_name"])
    return context


def deployment_identity(commit, dirty, context):
    """Public identity from the checked-out Git tree and the actual CI event."""
    branch = git("branch", "--show-current")
    environment = "local"
    identity = {"environment": environment, "branch": branch or None,
                "build_sha": commit, "dirty": dirty,
                "tags": git("tag", "--points-at", commit).splitlines()}
    if context:
        require(context["repository"] == "pysugar/model-observatory", "Unexpected build repository")
        if context["event"] == "pull_request":
            event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
            identity.update(environment="preview", branch=event["pull_request"]["head"]["ref"],
                            pr=context["pr"], head_sha=context["head_sha"])
        elif os.environ.get("GITHUB_REF") == "refs/heads/main" and context["event"] in {"push", "workflow_dispatch"}:
            identity.update(environment="release", branch="main")
        else:
            identity.update(environment="ci", branch=os.environ.get("GITHUB_REF_NAME") or None)
    return identity


def build_footer(identity):
    """Render escaped, static metadata so the footer also works without JS."""
    require(identity["environment"] in {"local", "ci", "preview", "release"}, "Invalid build environment")
    require(re.fullmatch(r"[0-9a-f]{40}", identity["build_sha"]), "Invalid build commit")
    repo = "https://github.com/pysugar/model-observatory"
    def commit_link(sha, label):
        require(re.fullmatch(r"[0-9a-f]{40}", sha), "Invalid source commit")
        return f'<span>{label} <a href="{repo}/commit/{sha}" target="_blank" rel="noopener"><code>{sha[:7]}</code></a></span>'
    parts = [f'<span>{identity["environment"]}</span>']
    if identity.get("pr"):
        require(isinstance(identity["pr"], int) and identity["pr"] > 0, "Invalid PR")
        parts.append(f'<span><a href="{repo}/pull/{identity["pr"]}" target="_blank" rel="noopener">PR #{identity["pr"]}</a></span>')
    if identity.get("branch"):
        parts.append(f'<span>分支 <code>{escape(identity["branch"])}</code></span>')
    if identity.get("head_sha"):
        parts.append(commit_link(identity["head_sha"], "源提交"))
    parts.append(commit_link(identity["build_sha"], "构建" if identity.get("head_sha") else "commit"))
    for tag in identity["tags"]:
        parts.append(f'<span>tag <a href="{repo}/tree/{quote(tag, safe="")}" target="_blank" rel="noopener"><code>{escape(tag)}</code></a></span>')
    if identity["dirty"]:
        parts.append('<span>含未提交改动</span>')
    return '<p id="build-info" class="build-info" aria-label="构建版本">' + ' · '.join(parts) + '</p>'


def build(output, require_clean=False):
    output = Path(output)
    require(not output.is_symlink() and output.resolve() != ROOT, "Unsafe output directory")
    if output.exists():
        require(all(p.name in FILES and p.is_file() and not p.is_symlink() for p in output.iterdir()), "Output contains non-release files; refusing to overwrite")
    commit = git("rev-parse", "HEAD")
    dirty = bool(git("status", "--porcelain", "--untracked-files=normal"))
    require(not require_clean or not dirty, "Release build requires a clean committed worktree")
    with tempfile.TemporaryDirectory(prefix="model-observatory-build-") as temp:
        subprocess.run([sys.executable, str(ROOT / "build_report.py"), "--output-dir", temp], check=True, cwd=ROOT)
        generated = Path(temp)
        files = {"index.html": (generated / "model-capability-cost.html").read_bytes()}
        for name in ("report-data.json", "report-data.csv"):
            files[name] = (generated / name).read_bytes()
    data = json.loads(files["report-data.json"])
    html = files["index.html"].decode()
    validate_data(data, files["report-data.csv"], html)
    validate_sources(data, html)
    context = ci_context(commit)
    identity = deployment_identity(commit, dirty, context)
    require(html.count("<!-- BUILD_INFO -->") == 1, "Missing unique build footer slot")
    html = html.replace("<!-- BUILD_INFO -->", build_footer(identity))
    files["index.html"] = html.encode()
    files["_headers"] = headers_for(html)
    version = {"schema_version": 1, "deployment": identity, "source_commit": commit, "source_time": git("show", "-s", "--format=%cI", "HEAD"),
               "report_reviewed_at": data["meta"]["reviewed_at"], "dirty": dirty,
               "assets": {name: sha256(content) for name, content in sorted(files.items())}}
    if context:
        version["ci"] = context
    files["version.json"] = (json.dumps(version, ensure_ascii=False, indent=2) + "\n").encode()
    for name, content in files.items():
        audit_text(name, content)
    output.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (output / name).write_bytes(content)
    return check(output)


def check(output, expected_commit=None):
    output = Path(output)
    require(not output.is_symlink(), "Release directory cannot be a symlink")
    require({p.name for p in output.iterdir()} == FILES, "Unexpected or missing public artifact")
    contents = {}
    for path in output.iterdir():
        require(path.is_file() and not path.is_symlink(), "Public artifacts must be regular files")
        require(path.stat().st_size < 5_000_000, "Unexpectedly large public artifact")
        contents[path.name] = path.read_bytes()
        audit_text(path.name, contents[path.name])
    version = json.loads(contents["version.json"])
    require(version["schema_version"] == 1 and set(version["assets"]) == ASSETS, "Invalid release manifest")
    require(re.fullmatch(r"[0-9a-f]{40}", version["source_commit"]) is not None, "Invalid source commit")
    if expected_commit:
        require(version["source_commit"] == expected_commit and version["dirty"] is False, "Artifact is not the requested clean commit")
    for name in ASSETS:
        require(sha256(contents[name]) == version["assets"][name], f"Artifact checksum mismatch: {name}")
    html = contents["index.html"].decode()
    require(contents["_headers"] == headers_for(html), "Headers differ from reviewed policy")
    if "deployment" in version:
        identity = version["deployment"]
        require(identity["build_sha"] == version["source_commit"] and identity["dirty"] == version["dirty"], "Footer identity differs from release")
        require(html.count('id="build-info"') == 1 and build_footer(identity) in html, "Footer differs from version metadata")
    counts = validate_data(json.loads(contents["report-data.json"]), contents["report-data.csv"], html)
    return {"status": "PASS", "commit": version["source_commit"], "dirty": version["dirty"], **counts,
            "files": {name: len(content) for name, content in sorted(contents.items())}}


def probe(url, output, attempts=6, delay=5, require_headers=True):
    check(output)
    expected = json.loads((Path(output) / "version.json").read_text())
    parts = urlsplit(url)
    local = parts.hostname in {"localhost", "127.0.0.1", "::1"}
    require((parts.scheme == "https" or (parts.scheme == "http" and local)) and not parts.username and not parts.password
            and parts.path in {"", "/"} and not parts.query and not parts.fragment, "Use a bare HTTPS site origin")
    origin = url.rstrip("/")
    last_error = None
    for attempt in range(attempts):
        try:
            for name in ("version.json", "index.html", "report-data.json", "report-data.csv"):
                path = "/" if name == "index.html" else "/" + name
                request = Request(origin + path + "?release=" + expected["source_commit"],
                                  headers={"Cache-Control": "no-cache", "User-Agent": PROBE_USER_AGENT})
                with urlopen(request, timeout=15) as response:
                    content = response.read(5_000_001)
                    require(response.status == 200, f"Unexpected HTTP status for {path}")
                    if require_headers:
                        require(response.headers.get("X-Content-Type-Options") == "nosniff", "Missing security headers")
                        if name == "version.json":
                            require("no-store" in response.headers.get("Cache-Control", ""), "Version probe must not be cached")
                if name == "version.json":
                    require(json.loads(content) == expected, "Live version does not match tested artifact")
                else:
                    require(sha256(content) == expected["assets"][name], f"Live content differs: {path}")
            return {"status": "PASS", "url": origin, "commit": expected["source_commit"]}
        except (HTTPError, URLError, TimeoutError, ValueError) as error:
            last_error = ValueError(f"HTTP {error.code} for {urlsplit(error.url).path}") if isinstance(error, HTTPError) else error
            if attempt + 1 < attempts:
                time.sleep(delay)
    raise ValueError(f"Deployment probe failed: {last_error}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("build", "check", "probe"):
        command = sub.add_parser(name)
        command.add_argument("--site-dir", type=Path, default=ROOT / "dist")
        if name == "build":
            command.add_argument("--require-clean", action="store_true")
        if name == "check":
            command.add_argument("--expected-commit")
        if name == "probe":
            command.add_argument("--url", required=True)
    args = parser.parse_args()
    try:
        if args.command == "build":
            result = build(args.site_dir, args.require_clean)
        elif args.command == "check":
            result = check(args.site_dir, args.expected_commit)
        else:
            result = probe(args.url, args.site_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    main()
