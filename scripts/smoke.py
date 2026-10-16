"""Portable Playwright smoke test for the exact static release directory."""

import argparse
import csv
import functools
import io
import json
import os
import socket
import subprocess
import threading
import time
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen

from playwright.sync_api import sync_playwright, expect
from publish import ROOT, check, probe, require


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


@contextmanager
def local_server(directory):
    server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(directory)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@contextmanager
def wrangler_server(directory, output):
    require(directory.resolve() == (ROOT / "dist").resolve(), "Wrangler uses the repository dist directory")
    output.mkdir(parents=True, exist_ok=True)
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    origin = f"http://127.0.0.1:{port}"
    with (output / "wrangler-dev.log").open("w") as log:
        process = subprocess.Popen(["node", str(ROOT / "node_modules/wrangler/bin/wrangler.js"), "dev", "--local", "--ip", "127.0.0.1", "--port", str(port)],
                                   cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                   env={**os.environ, "WRANGLER_SEND_METRICS": "false"})
        try:
            deadline = time.monotonic() + 30
            ready = False
            while time.monotonic() < deadline:
                require(process.poll() is None, "Wrangler exited; see test-results/wrangler-dev.log")
                try:
                    with urlopen(origin + "/version.json", timeout=1) as response:
                        ready = response.status == 200
                    if ready:
                        break
                except OSError:
                    time.sleep(.2)
            require(ready, "Wrangler startup timed out; see test-results/wrangler-dev.log")
            yield origin
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def smoke(site, origin, output, channel=None, cloudflare=False):
    check(site)
    data = json.loads((site / "report-data.json").read_text())
    output.mkdir(parents=True, exist_ok=True)
    errors, remote = [], []
    with sync_playwright() as p:
        options = {"headless": True, "chromium_sandbox": True}
        if channel:
            options["channel"] = channel
        browser = p.chromium.launch(**options)
        browser_version = browser.version
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
            page.on("pageerror", lambda error: errors.append(str(error)))
            def route(request_route):
                request = request_route.request
                if urlsplit(request.url).netloc != urlsplit(origin).netloc and not request.url.startswith(("blob:", "data:")):
                    remote.append(request.url)
                    request_route.abort()
                else:
                    request_route.continue_()
            page.route("**/*", route)
            page.goto(origin + "/", wait_until="networkidle")
            expect(page.locator('[role="tab"]')).to_have_count(6)
            expect(page.locator("#claudeCatalog tbody tr")).to_have_count(14)
            page.select_option("#claudeScope", "screenshot")
            expect(page.locator("#claudeCatalog tbody tr")).to_have_count(8)
            require("中文未实测" in page.locator("#overview").inner_text(), "Chinese limitation missing")
            page.select_option("#claudeScope", "all")
            page.screenshot(path=str(output / "desktop.png"), full_page=True)
            page.locator('[data-panel="explorer"]').click()
            page.locator('[data-group="coding"]').click()
            page.locator("#selectAll").click()
            expect(page.locator("#tbody tr")).to_have_count(45)
            with page.expect_download() as download:
                page.locator("#export").click()
            rows = list(csv.DictReader(io.StringIO(Path(download.value.path()).read_text(encoding="utf-8-sig"))))
            require(len(rows) == 45 and sum(r["cost_usd"] == "" for r in rows) == 2, "CSV export lost missing-cost evidence")
            page.locator('[data-panel="specs"]').click()
            value = float(page.locator('[data-cost-model="gpt-6.1-sol"]').get_attribute("data-per"))
            require(abs(value - .12) < 1e-9, "Default budget calculation changed")
            page.fill("#cachePercent", "101")
            expect(page.locator("#costTable tr")).to_have_count(0)
            page.fill("#cachePercent", "0")
            page.locator('[data-panel="reasoning"]').click()
            page.select_option("#deltaModel", "Claude Opus 5.5")
            page.select_option("#deltaGroup", "coding")
            for view in data["opus_coding_evidence"]["views"]:
                page.select_option("#opusEvidenceView", view["id"])
                expect(page.locator("#opusEvidenceTable tbody tr")).to_have_count(len(view["rows"]))
            page.locator('[data-panel="evidence"]').click()
            expect(page.locator("#sourceList .source-item")).to_have_count(len(data["sources"]))
            for width in (390, 320):
                page.set_viewport_size({"width": width, "height": 844})
                for panel in ("overview", "capabilities", "explorer", "specs", "reasoning", "evidence"):
                    page.locator(f'[data-panel="{panel}"]').click()
                    require(page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Page overflow: {width}px/{panel}")
                page.locator('[data-panel="overview"]').click()
                page.screenshot(path=str(output / f"mobile-{width}.png"), full_page=True)
            for path in ("/.git/config", "/README.md", "/research/2026-10-16/RESEARCH-NOTES.txt", "/report.template.html"):
                require(page.request.get(origin + path).status == 404, f"Private source path was served: {path}")
            require(not errors, "Browser errors: " + "; ".join(errors))
            require(not remote, "Page attempted external network requests")
        finally:
            browser.close()
    probe(origin, site, attempts=1, require_headers=cloudflare)
    result = {"status": "PASS", "browser_version": browser_version, "browser_channel": channel or "bundled-chromium",
              "viewports": [1440, 390, 320], "rows": len(data["rows"]),
              "checks": ["six panels", "Claude filter", "CSV missing values", "budget boundaries", "four Opus evidence views",
                         "source index", "no page overflow", "no JS errors or external requests", "source paths return 404", "version and asset hashes"],
              "cloudflare_headers_checked": cloudflare}
    (output / "smoke.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "test-results")
    server = parser.add_mutually_exclusive_group()
    server.add_argument("--base-url")
    server.add_argument("--wrangler", action="store_true", help="Start and stop the actual local Workers static server")
    parser.add_argument("--browser-channel", choices=["chrome", "chromium", "msedge"])
    parser.add_argument("--cloudflare", action="store_true", help="Require deployed Workers security/cache headers")
    args = parser.parse_args()
    if args.wrangler:
        with wrangler_server(args.site_dir, args.output_dir) as origin:
            smoke(args.site_dir, origin, args.output_dir, args.browser_channel, True)
    elif args.base_url:
        smoke(args.site_dir, args.base_url.rstrip("/"), args.output_dir, args.browser_channel, args.cloudflare)
    else:
        require(not args.cloudflare, "Use --base-url for a Wrangler/Workers server")
        with local_server(args.site_dir) as origin:
            smoke(args.site_dir, origin, args.output_dir, args.browser_channel)
