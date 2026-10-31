"""Browser checks for the default AA Intelligence Index v5 view and the version switch.

The v4.3.2 checks in smoke.py run on `?aa=v4`; here the v5 view is compared with the same
Python reference implementation (scripts/sweet_spot.py) fed the v5 data, so nothing below
hard-codes a v5 number.
"""

import csv
import io
from pathlib import Path

from playwright.sync_api import expect
from publish import require
from sweet_spot import PRESETS, picks, profile_pitfalls, profile_series


def v5_view(data):
    """The data the page uses when v5 is loaded."""
    v5 = data["aa_v5"]
    return {**data, "aa_release_series": v5["aa_release_series"],
            "aa_capability_indexes": v5["aa_capability_indexes"], "aa_effort_evals": v5["aa_effort_evals"]}


def check_v5_views(page, data, origin, output):
    view = v5_view(data)
    page.goto(origin + "/?aa=v5", wait_until="networkidle")
    require(page.evaluate("document.documentElement.dataset.aa") == "v5", "v5 view did not load")
    expect(page.locator("#aaVersionSelect")).to_have_value("v5")
    # Version-specific prose: only the v5 blocks are visible.
    expect(page.locator('.pitfall-list[data-aa-version="v5"]')).to_be_visible()
    expect(page.locator('.pitfall-list[data-aa-version="v4"]')).to_be_hidden()
    require("{{" not in page.content(), "Unresolved narrative placeholder")

    # Current and historical AA charts remain explicit; low v5 scores stay inside the plot.
    page.locator('[data-panel="explorer"]').click()
    expect(page.locator("#explorerIntro")).to_contain_text("20 个发布版本、58 个配置")
    expect(page.locator("#charttitle")).to_contain_text("AA v4.3.2（历史）")
    current = [r for r in view["aa_release_series"]["releases"] if r["isTrackedFamily"] and r["isCurrent"]]
    selected = sum(len(r["variants"]) for r in current)
    for axis, label in (("costPerTask","加权单任务成本"), ("timePerTaskMinutes","每任务耗时"),
                        ("outputTokensPerTask","每任务输出 Token 数")):
        page.select_option("#releaseXMetric", axis)
        expect(page.locator("#releaseChartTitle")).to_contain_text("AA v5")
        expect(page.locator("#releaseChartTitle")).to_contain_text(label)
        plotted = sum(v.get(axis) is not None and v[axis] > 0 for r in current for v in r["variants"])
        expect(page.locator("#releaseCount")).to_contain_text(f"已选 {selected} 个配置 · 可绘 {plotted} 个 · 未绘 {selected-plotted} 个")
        expect(page.locator("#releaseMissing")).to_contain_text("Wonder Full max")
        expect(page.locator("#releaseChart .release-dot")).to_have_count(plotted)
        require(page.eval_on_selector("#releaseChart", "svg => [...svg.querySelectorAll('.release-dot circle')].every(c => Number(c.getAttribute('cy')) >= 34 && Number(c.getAttribute('cy')) <= svg.viewBox.baseVal.height - 62)"), "v5 score outside the plotted y range")
        require("未提供m" not in page.locator("#releaseChart").text_content(), "Missing time received a unit")
    page.select_option("#releaseXMetric", "costPerTask")
    for release, text in (("gemini-4-carbon","安全合作方"), ("muse-wonder-full","Muse Code")):
        page.locator(f'[data-rel-pill="{release}"]').click()
        expect(page.locator("#releaseDetail .release-availability")).to_contain_text(text)
        expect(page.locator("#releaseDetail")).to_contain_text("不是官方 token 单价或订阅扣额")
    with page.expect_download() as download:
        page.locator("#exportReleases").click()
    rows = list(csv.DictReader(io.StringIO(Path(download.value.path()).read_text(encoding="utf-8-sig"))))
    require(all(r["aa_version"] == "v5.0" and r["aa_snapshot"] == "2026-10-31" and r["source_url"].startswith("https://") for r in rows), "Release export lost version, date or source")
    full = next(r for r in rows if r["variant_id"] == "muse-wonder-full")
    require(full["cost_per_task_usd"] == "" and "Muse Code" in full["availability_note"], "Missing-cost release export lost availability")
    page.locator('[data-panel="specs"]').click()
    expect(page.locator('#specScope option[value="all"]')).to_contain_text(str(len(data["models"])))
    page.locator('[data-panel="overview"]').click()

    # Sweet-spot matrix equals the reference on v5 data for every preset.
    page.locator('[data-panel="overview"]').click()
    expect(page.locator("#sweetMatrix thead")).to_contain_text("FrontierCode")
    for preset, share in PRESETS.items():
        page.select_option("#sweetTolerance", preset)
        expected = picks(view, share)
        rendered = page.eval_on_selector_all("#sweetMatrix .ss-cell", "cells => cells.map(c => [c.dataset.ssModel, c.dataset.ssTask, c.querySelector('.ss-effort').textContent])")
        require(len(rendered) == len(expected), f"v5 sweet-spot matrix size changed: {preset}")
        for model, task, effort in rendered:
            require(expected[(model, task)] == effort, f"v5 sweet spot drifted: {preset}/{model}/{task}")
    page.select_option("#sweetTolerance", "balanced")

    # Missing-cost single points remain observations, not computed sweet spots.
    page.locator('[data-panel="profiles"]').click()
    page.select_option("#profileModel", "claude-opus-5-5")
    page.select_option("#profileModel", "muse-wonder-full")
    expect(page.locator("#profileGrid .mp-mark.pick")).to_have_count(0)
    expect(page.locator("#profileGrid")).to_contain_text("仅测单点")
    expect(page.locator("#profileAltCoverage .mp-voices")).to_have_count(0)
    page.locator('[data-panel="specs"]').click()
    for model in ("muse-wonder-full", "gemini-4-carbon"):
        expect(page.locator(f'[data-cost-model="{model}"]')).to_have_attribute("data-per", "")
        expect(page.locator(f'[data-cost-model="{model}"]')).to_contain_text("暂不提供公开 API 预算")
    page.locator('[data-panel="overview"]').click()
    expect(page.locator("#vendorCoverage .vendor-card")).to_have_count(5)
    page.select_option("#marketVendor", "Meta")
    expect(page.locator("#marketTable tbody tr")).to_have_count(3)
    expect(page.locator("#marketTable")).to_contain_text("Muse Spark 1.3")
    expect(page.locator('#marketTable a[href*="muse-spark-1-3"]')).to_have_count(1)
    page.locator("#marketReset").click()

    # Task chart: one dot per measured variant, with v5 task labels.
    page.locator('[data-task-tab="agentic"]').click()
    expect(page.locator('[data-task-tab="agentic"]')).to_contain_text("Terminal-Bench-Science")
    require("NaN" not in page.locator("#taskEffortChart").inner_html(), "Invalid v5 task chart coordinate")

    # Capability bump chart and its column header follow v5.
    page.locator('[data-panel="capabilities"]').click()
    expect(page.locator("#capBumpChart")).to_contain_text("AA 智能指数 v5.0")
    n_measured = sum(len(r["variants"]) for r in view["aa_release_series"]["releases"] if any(v.get("taskScores") for v in r["variants"]))
    expect(page.locator("#effortScalingChart .scaling-dot")).to_have_count(n_measured)

    # Model profiles: AA rows equal the reference; models without v5 data show no AA picks.
    page.locator('[data-panel="profiles"]').click()
    for preset, share in PRESETS.items():
        page.select_option("#profileTolerance", preset)
        for m in data["model_effort_profiles"]["models"]:
            page.select_option("#profileModel", m["id"])
            expected = profile_series(view, m["id"], share)
            rendered = dict(page.eval_on_selector_all("#profileGrid tr[data-mp-series]", "rows => rows.filter(r => r.dataset.mpPick).map(r => [r.dataset.mpSeries, r.dataset.mpPick])"))
            require(rendered == expected, f"v5 profile drifted: {preset}/{m['id']}: {rendered} != {expected}")
    page.select_option("#profileTolerance", "balanced")
    for m in data["model_effort_profiles"]["models"]:
        page.select_option("#profileModel", m["id"])
        rendered = page.eval_on_selector_all("#profilePitfallList li[data-mp-pit-kind]:not([data-mp-pit-kind=evidence])",
            "items => items.map(li => [li.dataset.mpPitKind, li.dataset.key, li.dataset.effort, li.dataset.alt || null, li.dataset.altEffort || null])")
        got = {tuple(x for x in item if x is not None) for item in rendered}
        require(got == profile_pitfalls(view, m["id"]), f"v5 pitfalls drifted: {m['id']}")

    for width in (390, 320):
        page.set_viewport_size({"width": width, "height": 844})
        for panel in ("overview", "capabilities", "explorer", "reasoning", "profiles", "evidence"):
            page.locator(f'[data-panel="{panel}"]').click()
            require(page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"v5 page overflow: {width}px/{panel}")
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.locator('[data-panel="overview"]').click()
    page.screenshot(path=str(output / "v5-overview.png"))

    # The header switch reloads into the other version and keeps it in the URL.
    with page.expect_navigation(wait_until="networkidle"):
        page.select_option("#aaVersionSelect", "v4")
    require(page.evaluate("document.documentElement.dataset.aa") == "v4", "Version switch did not load v4.3.2")
    require("aa=v4" in page.url, "Version switch is not reflected in the URL")
    expect(page.locator('.pitfall-list[data-aa-version="v4"]')).to_be_visible()
