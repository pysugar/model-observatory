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
from capability_smoke import check_capabilities
from selection_smoke import check_selection
from scaling_smoke import check_scaling


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
            # Exercise task-specific representatives, including declining scores at higher effort.
            active = [r for r in data["aa_release_series"]["releases"] if any(v.get("taskScores") for v in r["variants"])]
            expect(page.locator("#taskEffortChart .task-dot")).to_have_count(43)
            page.select_option("#taskEffortMode", "top_variants")
            for task in ("complex", "coding", "planning", "agentic", "automation", "knowledge", "intelligenceIndex"):
                page.locator(f'[data-task-tab="{task}"]').click()
                expect(page.locator("#taskEffortChart .task-dot")).to_have_count(len(active))
                if task == "knowledge":
                    sol = next(r for r in active if r["releaseSlug"] == "gpt-6-1-sol")
                    high = next(v for v in sol["variants"] if v["effort"] == "high")
                    expect(page.locator("#taskEffortSubnote")).to_contain_text(f'high {high["taskScores"]["knowledge"]:.2f} 分')
                    expect(page.locator("#taskEffortSubnote")).to_contain_text("本报告自定义合成分")
                if task in ("planning", "agentic"):
                    expect(page.locator("#taskCategoryCards .platform-card").nth(1)).to_contain_text("与最高分相差")
                    expect(page.locator("#taskCategoryCards .platform-card").nth(1)).to_contain_text("Elo")
                for release in active:
                    def score(variant):
                        return variant["intelligenceIndex"] if task == "intelligenceIndex" else variant["taskScores"][task]
                    candidates = [v for v in release["variants"] if v.get("costPerTask") is not None and v["costPerTask"] > 0]
                    best = min(candidates, key=lambda v: (-score(v), v["costPerTask"]))
                    dot = page.locator(f'#taskEffortChart .task-dot[data-task-rel="{release["releaseSlug"]}"]')
                    expect(dot).to_have_attribute("data-task-var", best["slug"])
                require("NaN" not in page.locator("#taskEffortChart").inner_html(), "Invalid task chart coordinate")
            page.select_option("#taskEffortMode", "release_trajectories")
            page.locator('[data-task-tab="complex"]').click()
            page.select_option("#taskEffortFocus", "high")
            high_count = sum(any(v["effort"] == "high" and v.get("costPerTask") is not None for v in r["variants"]) for r in active)
            expect(page.locator("#taskEffortChart .task-dot")).to_have_count(high_count)
            page.select_option("#taskEffortFocus", "all")
            page.locator('[data-panel="capabilities"]').click()
            expect(page.locator("#effortScalingChart .scaling-dot")).to_have_count(44)
            for task in ("complex", "coding", "planning", "agentic", "automation", "knowledge", "intelligenceIndex"):
                page.select_option("#effortScalingTask", task)
                require("NaN" not in page.locator("#effortScalingChart").inner_html(), "Invalid scaling chart coordinate")
            page.select_option("#effortScalingTask", "complex")
            check_capabilities(page, data, output)
            check_scaling(page, data, output)
            check_selection(page, data, output)
            page.locator('[data-panel="overview"]').click()
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
            footer = page.locator("#build-info")
            expect(footer).to_have_count(1)
            expect(footer).to_contain_text(json.loads((site / "version.json").read_text())["deployment"]["build_sha"][:7])
            footer.scroll_into_view_if_needed()
            footer.screenshot(path=str(output / "build-footer-desktop.png"))
            for width in (390, 320):
                page.set_viewport_size({"width": width, "height": 844})
                for panel in ("overview", "capabilities", "explorer", "specs", "reasoning", "evidence"):
                    page.locator(f'[data-panel="{panel}"]').click()
                    require(page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Page overflow: {width}px/{panel}")
                page.locator('[data-panel="overview"]').click()
                page.screenshot(path=str(output / f"mobile-{width}.png"), full_page=True)
                footer.scroll_into_view_if_needed()
                footer.screenshot(path=str(output / f"build-footer-{width}.png"))
            for path in ("/.git/config", "/README.md", "/research/2026-10-16/RESEARCH-NOTES.txt", "/report.template.html"):
                require(page.request.get(origin + path).status == 404, f"Private source path was served: {path}")
            require(not errors, "Browser errors: " + "; ".join(errors))
            require(not remote, "Page attempted external network requests")
        finally:
            browser.close()
    probe(origin, site, attempts=1, require_headers=cloudflare)
    result = {"status": "PASS", "browser_version": browser_version, "browser_channel": channel or "bundled-chromium",
              "viewports": [1440, 390, 320], "rows": len(data["rows"]),
              "checks": ["task-specific best variants in seven dimensions", "dataset-backed knowledge narrative and Elo differences", "effort filters and scaling charts", "pinned vs temporary highlight, missing gaps and singleton", "separate Computer Use protocols and scope-limited raw-precision alternatives", "three verified workflow cards, source boundaries and native disclosures on keyboard/touch",
               "capability missingness, tie ranks, per-domain denominators and CSV consistency",
               "reasoning charts, effort selection, nonmonotonic scores and keyboard access", "six panels", "Claude filter", "CSV missing values", "budget boundaries", "four Opus evidence views",
                         "28 version-specific task priors, unknown-version state, native keyboard and true touch", "AA terminology across six panels and twelve CSV downloads", "Arena preference, causal signals and factuality boundaries", "source index", "no page overflow", "no JS errors or external requests", "source paths return 404", "version and asset hashes"],
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
