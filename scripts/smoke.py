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
from sweet_spot import PRESETS, picks, profile_alternatives, profile_series, profile_pitfalls


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


def check_overview_ui(page, data):
    """Sweet-spot matrix matches the Python reference; data-driven quadrant; focus and page TOC."""
    page.locator('[data-panel="overview"]').click()
    expect(page.locator("#sweetMatrix tbody tr")).to_have_count(11)
    for preset, share in PRESETS.items():
        page.select_option("#sweetTolerance", preset)
        expected = picks(data, share)
        rendered = page.eval_on_selector_all("#sweetMatrix .ss-cell", "cells => cells.map(c => [c.dataset.ssModel, c.dataset.ssTask, c.querySelector('.ss-effort').textContent])")
        require(len(rendered) == len(expected), f"Sweet-spot matrix size changed: {preset}")
        for model, task, effort in rendered:
            require(expected[(model, task)] == effort, f"Sweet spot drifted from reference: {preset}/{model}/{task}")
    page.select_option("#sweetTolerance", "balanced")
    page.locator('[data-ss-model="claude-sonnet-5-5"][data-ss-task="ii"]').click()
    expect(page.locator("#sweetDetail tr.is-pick th")).to_have_text("high")
    expect(page.locator("#sweetDetail .ss-refs-detail")).to_be_visible()
    expect(page.locator("#taskQuadHint")).to_contain_text("中位数")
    page.locator('[data-task-pill="claude-fable-5-1"]').click()
    active = sum(any(v.get("taskScores") for v in r["variants"]) for r in data["aa_release_series"]["releases"])
    expect(page.locator("#taskEffortChart .release-series.is-dimmed")).to_have_count(active - 1)
    page.locator('[data-task-pill="claude-fable-5-1"]').click()
    expect(page.locator("#taskEffortChart .release-series.is-dimmed")).to_have_count(0)
    hash_before = page.evaluate("location.hash")
    require(page.locator("#pageToc button").count() >= 8, "Overview page TOC is missing sections")
    page.locator("#pageToc button").nth(3).click()
    require(page.evaluate("location.hash") == hash_before, "Page TOC changed the panel hash")


def check_profile_ui(page, data, output):
    """Model profile: every model x preset matches the Python reference; deep link and cross-links work."""
    page.locator('[data-panel="profiles"]').click()
    models = data["model_effort_profiles"]["models"]
    expect(page.locator("#profileModel option")).to_have_count(len(models))
    for preset, share in PRESETS.items():
        page.select_option("#profileTolerance", preset)
        for m in models:
            page.select_option("#profileModel", m["id"])
            expected = profile_series(data, m["id"], share)
            rendered = dict(page.eval_on_selector_all("#profileGrid tr[data-mp-series]", "rows => rows.filter(r => r.dataset.mpPick).map(r => [r.dataset.mpSeries, r.dataset.mpPick])"))
            require(rendered == expected, f"Profile drifted from reference: {preset}/{m['id']}: {rendered} != {expected}")
            require(page.locator("#profileCards .mp-card").count() == len(data["model_effort_profiles"]["taskAxis"]), "Profile task cards missing")
            require(page.locator('#profiles a[href=""]').count() == 0, "Empty source link in profile")
    page.select_option("#profileTolerance", "balanced")
    for m in models:
        page.select_option("#profileModel", m["id"])
        rendered = page.eval_on_selector_all("#profilePitfallList li[data-mp-pit-kind]:not([data-mp-pit-kind=evidence])",
            "items => items.map(li => [li.dataset.mpPitKind, li.dataset.key, li.dataset.effort, li.dataset.alt || null, li.dataset.altEffort || null])")
        got = {tuple(x for x in item if x is not None) for item in rendered}
        require(got == profile_pitfalls(data, m["id"]), f"Pitfalls drifted from reference: {m['id']}")
        require(len(rendered) == len(got), f"Duplicate pitfall rows: {m['id']}")
    for scope in ("vendor", "all"):
        page.select_option("#profileAltScope", scope)
        for m in models:
            page.select_option("#profileModel", m["id"])
            for effort in page.eval_on_selector_all("#profileAltEffort option", "os => os.map(o => o.value)"):
                page.select_option("#profileAltEffort", effort)
                rows = page.eval_on_selector_all("#profileAltTable tr[data-alt-series]",
                    "rs => rs.map(r => [r.dataset.altSeries, r.dataset.cheaper, r.dataset.stronger, r.dataset.unbounded])")
                pair = lambda v: tuple(v.split("|")) if v else None
                got = {k: (pair(c), pair(st), pair(ce)) for k, c, st, ce in rows}
                require(got == profile_alternatives(data, m["id"], effort, scope), f"Alternatives drifted: {scope}/{m['id']}/{effort}")
    # Every model shows the same benchmark rows, so coding always lists the AA row before Vulcan.
    page.select_option("#profileModel", "gpt-5.6-luna")
    coding = page.locator('#profileGrid tr[data-mp-task="coding"] .mp-bench')
    expect(coding).to_have_count(2)
    expect(coding.nth(0)).to_contain_text("Terminal-Bench")
    expect(coding.nth(1)).to_contain_text("通过率 %")
    expect(page.locator('#profileGrid tr[data-mp-task="coding"]').nth(0)).to_contain_text("未测")
    page.select_option("#profileAltScope", "vendor")
    # Community voices are shown as text next to the data, never inside the alternatives table.
    page.select_option("#profileModel", "gpt-6.1-sol")
    expect(page.locator("#profileHeader .mp-voice-box")).to_contain_text("社区主流声音")
    expect(page.locator("#profileAltCoverage")).to_contain_text("这张表看不到的")
    for m in models:
        if m["tier"] == "main":
            page.select_option("#profileModel", m["id"])
            require(page.locator("#profileAltCoverage .mp-voices li").count() >= 1, f"No community voice shown for {m['id']}")
    page.select_option("#profileModel", "gpt-6.1-sol")
    page.select_option("#profileAltEffort", "max")
    # Without a budget, near-ties go to the faster config: Astra xhigh, not the slower top-scoring Astra max.
    expect(page.locator('#profileAltTable tr[data-alt-series="aa-ii"]')).to_have_attribute("data-unbounded", "gpt-6-astra|xhigh")
    expect(page.locator("#profileScenarioList li")).to_have_count(len(data["community_consensus"]["maxEffortScenarios"]))
    expect(page.locator('#profileScenarioList li[data-scenario="interactive-wait"] .mp-scn-signal.hit')).to_contain_text("首字等待")
    expect(page.locator('#profileScenarioList li[data-scenario="tie-but-slower"] .mp-scn-signal.hit')).to_be_visible()
    # Work phases map generic tiers onto native efforts (Argon has no xhigh / max).
    phases = data["community_consensus"]["workPhases"]
    expect(page.locator("#profilePhaseTable tbody tr")).to_have_count(len(phases))
    page.select_option("#profileModel", "gemini-4-argon")
    expect(page.locator('#profilePhaseTable tr[data-phase="design"]')).to_have_attribute("data-mapped", "high")
    page.select_option("#profileModel", "claude-opus-5-5")
    expect(page.locator('#profilePhaseTable tr[data-phase="design"]')).to_have_attribute("data-mapped", "xhigh")
    page.select_option("#profileModel", "grok-4-7")
    expect(page.locator("#profileAltEffort")).to_have_value("high")
    page.locator('#profileGrid tr[data-mp-series="aa-ii"] td[data-mp-effort="xhigh"]').click()
    expect(page.locator("#profileAltEffort")).to_have_value("xhigh")
    page.select_option("#profileModel", "claude-sonnet-5-5")
    expect(page.locator('#profileGrid tr[data-mp-series="aa-ii"] td[data-mp-effort="max"] .mp-pit.k-cost')).to_have_count(1)
    expect(page.locator("#profileRule")).to_contain_text("边际收益拐点")
    expect(page.locator("#profileRule")).to_contain_text("省钱 20%、均衡 12%、性能优先 6%")
    page.locator("#profilePitfalls").uncheck()
    expect(page.locator("#profilePitfallsCard")).to_be_hidden()
    expect(page.locator("#profileGrid .mp-pit:visible")).to_have_count(0)
    page.locator("#profilePitfalls").check()
    page.select_option("#profileModel", "gpt-5.6-sol")
    expect(page.locator('#profilePitfallList li[data-mp-pit-kind="upgrade"][data-effort="max"]')).to_have_attribute("data-alt", "gpt-6.1-sol")
    page.select_option("#profileModel", "grok-4-7")
    expect(page.locator("#profileHeader")).to_contain_text("档位待核验")
    expect(page.locator("#profileGrid thead")).to_contain_text("待核验")
    require(page.evaluate("location.hash") == "#profiles?m=grok-4-7", "Profile deep link not written")
    page.select_option("#profileModel", "claude-opus-4-7")
    expect(page.locator("#profileHeader")).to_contain_text("不补造曲线")
    page.locator('[data-mp-quick="claude-opus-5-5"]').click()
    expect(page.locator('[data-mp-quick="claude-opus-5-5"]')).to_have_attribute("aria-pressed", "true")
    page.locator('#profileGrid tr[data-mp-series="vulcan"]').click()
    expect(page.locator("#profileCard-coding.selected")).to_have_count(1)
    page.locator("#profiles").screenshot(path=str(output / "model-profile-desktop.png"), style=".nav-shell{visibility:hidden!important}")
    page.locator('[data-mp-jump="overview"]').click()
    expect(page.locator("#overview")).to_be_visible()
    page.locator('[data-ss-model="gpt-6-1-sol"][data-ss-task="coding"]').click()
    page.locator("#sweetDetail [data-profile-open]").click()
    expect(page.locator("#profiles")).to_be_visible()
    expect(page.locator("#profileModel")).to_have_value("gpt-6.1-sol")
    expect(page.locator("#profileCard-coding.selected")).to_have_count(1)
    page.goto(page.url.split("#")[0] + "#profiles?m=gpt-5.6-luna")
    page.reload()
    expect(page.locator("#profileModel")).to_have_value("gpt-5.6-luna")


def check_market_ui(page, data, output):
    """Exercise fresh evidence, missing values, price boundaries, themes and touch."""
    expect(page.locator("#marketTable tbody tr")).to_have_count(8)
    # AA v5 is the default view: GPT-6 Astra ranks second under the new index.
    expect(page.locator('[data-board="aa5"]')).to_have_attribute("aria-pressed", "true")
    expect(page.locator("#marketTable tbody tr").nth(1)).to_contain_text("GPT-6 Astra")
    page.screenshot(path=str(output / "refresh-desktop.png"))
    page.locator('[data-board="livebench"]').click()
    page.fill("#marketSearch", "Grok")
    expect(page.locator("#marketTable")).to_contain_text("74.1")
    expect(page.locator("#marketTable")).to_contain_text("$2.69")
    with page.expect_download() as download:
        page.locator("#exportMarket").click()
    rows = list(csv.DictReader(io.StringIO(Path(download.value.path()).read_text(encoding="utf-8-sig"))))
    require(len(rows) == 1 and rows[0]["cost_usd"] == "2.687", "Market export lost source precision")
    require(rows[0]["source_updated_at"] == "2026-10-18" and rows[0]["checked_at"] == "2026-10-23", "Source and verification dates conflated")
    page.fill("#marketSearch", "no-such-model")
    expect(page.locator("#marketTable")).to_contain_text("没有匹配的模型")
    expect(page.locator("#exportMarket")).to_be_disabled()
    page.locator("#marketReset").click()
    page.locator('[data-board="scale"]').click()
    with page.expect_download() as download:
        page.locator("#exportMarket").click()
    rows = list(csv.DictReader(io.StringIO(Path(download.value.path()).read_text(encoding="utf-8-sig"))))
    require(all(r["cost_usd"] == "" and r["source_updated_at"] == "" for r in rows), "Unknown source values fabricated")
    page.locator('[data-board="openrouter"]').click()
    expect(page.locator("#boardNote")).to_contain_text("不能作为能力分")
    page.locator("#marketMore").click()
    expect(page.locator("#marketTable tbody tr")).to_have_count(10)
    page.locator('[data-board="aa5"]').click()
    expect(page.locator("#boardMethod")).to_be_visible()
    expect(page.locator("#marketTable tbody tr").first).to_contain_text("Claude Opus 5.5")
    expect(page.locator("#marketTable")).to_contain_text("+4 · 原 53")
    require(not page.locator("#marketSort option[value=cost]").evaluate("o => o.disabled"), "AA v5 cost sort disabled")
    page.select_option("#marketSort", "cost")
    expect(page.locator("#marketTable tbody tr").first).to_contain_text("GPT-6 Luna")
    page.select_option("#marketSort", "score")
    page.locator('[data-board="aa"]').click()
    expect(page.locator("#boardMethod")).to_be_hidden()
    page.select_option("#marketVendor", "OpenAI")
    expect(page.locator("#marketTable tbody tr")).to_have_count(4)
    page.locator("#marketReset").click()
    page.select_option("#marketSort", "cost")
    page.locator("#marketMore").click()
    expect(page.locator("#marketTable tbody tr").last).to_contain_text("Muse Wonder Full")
    page.locator("#marketReset").click()
    page.locator("#latestBenchmarks").scroll_into_view_if_needed()
    page.locator("#latestBenchmarks").screenshot(path=str(output / "refresh-leaderboards.png"))
    page.select_option("#themeSelect", "dark")
    page.evaluate("window.scrollTo(0,0)")
    page.screenshot(path=str(output / "refresh-dark.png"))
    page.reload(wait_until="networkidle")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    page.select_option("#themeSelect", "light")
    page.locator('[data-panel="specs"]').click()
    for control in ("answerTokens", "reasonTokens"):
        page.fill("#" + control, "0")
    page.fill("#cachePercent", "0")
    for tokens, expected in ((199999,.399998),(200000,.8),(200001,.800004)):
        page.fill("#inputTokens", str(tokens))
        actual = float(page.locator('[data-cost-model="grok-4-7"]').get_attribute("data-per"))
        require(abs(actual-expected) < 1e-9, f"Grok long-context boundary: {tokens}")
    # Reload restores the existing smoke suite's default calculator values.
    page.goto(page.url.split("#")[0], wait_until="networkidle")
    for width in (390, 320):
        context = page.context.browser.new_context(viewport={"width":width,"height":844}, has_touch=True, is_mobile=True)
        try:
            touch = context.new_page()
            touch.goto(page.url.split("#")[0], wait_until="networkidle")
            touch.locator('[data-scroll="latestBenchmarks"]').tap()
            touch.locator('[data-board="livebench"]').tap()
            touch.fill("#marketSearch", "Grok")
            expect(touch.locator("#marketTable")).to_contain_text("74.1")
            require(touch.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Market overflow: {width}")
            touch.locator("#marketReset").tap()
            touch.screenshot(path=str(output / f"refresh-market-{width}.png"))
            touch.evaluate("window.scrollTo(0,0)")
            touch.screenshot(path=str(output / f"refresh-hero-{width}.png"))
        finally:
            context.close()


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
            check_market_ui(page, data, output)
            expect(page.locator('[role="tab"]')).to_have_count(7)
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
            check_overview_ui(page, data)
            check_profile_ui(page, data, output)
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
                for panel in ("overview", "capabilities", "explorer", "specs", "reasoning", "profiles", "evidence"):
                    page.locator(f'[data-panel="{panel}"]').click()
                    fits = page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                    if not fits:
                        page.screenshot(path=str(output / f"overflow-{width}-{panel}.png"))
                        print(page.evaluate("""({viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,
                          elements:Array.from(document.querySelectorAll('body *')).filter(e => {
                            const r=e.getBoundingClientRect();
                            if (!r.width || r.right<=innerWidth) return false;
                            for(let p=e.parentElement;p;p=p.parentElement) {
                              if (/hidden|clip|auto|scroll/.test(getComputedStyle(p).overflowX)) return false;
                            }
                            return true;
                          }).slice(0,25).map(e=>({tag:e.tagName,id:e.id,
                            width:e.getBoundingClientRect().width,right:e.getBoundingClientRect().right,
                            text:e.textContent.slice(0,70)}))})"""))
                    require(fits, f"Page overflow: {width}px/{panel}")
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
              "checks": ["fresh five-source search, filters, missing-cost export, dates, theme persistence and touch", "Grok 200k inclusive price boundary", "task-specific best variants in seven dimensions", "dataset-backed knowledge narrative and Elo differences", "effort filters and scaling charts", "pinned vs temporary highlight, missing gaps and singleton", "separate Computer Use protocols and scope-limited raw-precision alternatives", "three verified workflow cards, source boundaries and native disclosures on keyboard/touch",
               "capability missingness, tie ranks, per-domain denominators and CSV consistency",
               "reasoning charts, effort selection, nonmonotonic scores and keyboard access", "seven panels", "Claude filter", "CSV missing values", "budget boundaries", "four Opus evidence views",
                         "28 version-specific task priors, unknown-version state, native keyboard and true touch", "AA terminology across seven panels and thirteen CSV downloads", "Arena preference, causal signals and factuality boundaries", "source index", "sweet-spot matrix equals the Python reference for three presets", "median quadrant, series focus and page TOC", "model profile sweet spots, pitfalls (incl. overthinking) and three better alternatives equal the Python reference for every model, effort, preset and scope; max-effort scenarios with measured signals; work-phase mainstream efforts mapped to native levels; community voices for every main model stay text-only; deep link and cross-links", "no page overflow", "no JS errors or external requests", "source paths return 404", "version and asset hashes"],
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
