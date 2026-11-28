"""Browser checks for the default AA Intelligence Index v5 view and the version switch.

The v4.3.2 checks in smoke.py run on `?aa=v4`; here the v5 view is compared with the same
Python reference implementation (scripts/sweet_spot.py) fed the v5 data, so nothing below
hard-codes a v5 number.
"""

import csv
import io
from pathlib import Path

from playwright.sync_api import expect
from capability_smoke import csv_download
from publish import require
from sweet_spot import PRESETS, picks, profile_pitfalls, profile_series


def v5_view(data):
    """The data the page uses when v5 is loaded."""
    v5 = data["aa_v5"]
    return {**data, "aa_release_series": v5["aa_release_series"],
            "aa_capability_indexes": v5["aa_capability_indexes"], "aa_effort_evals": v5["aa_effort_evals"]}


def check_plot_y_bounds(page, selector, top, bottom):
    coords = page.eval_on_selector(selector, "svg => ({height:svg.viewBox.baseVal.height, ys:[...svg.querySelectorAll('circle[cy]')].map(c=>Number(c.getAttribute('cy')))})")
    require(bool(coords["ys"]), f"No plotted points: {selector}")
    require(all(top <= y <= coords["height"]-bottom for y in coords["ys"]),
            f"Measured score outside plot: {selector}")


def check_cap_benchmarks(page, view):
    scope = page.locator("#capIndexScope")
    scope.select_option("all_top")
    selected = "gpt-6-2-astra"
    page.locator(f'[data-cap-model="{selected}"]').click()
    page.get_by_role("button", name="基础测试 · 科学与编程").click()
    entries = [e for e in view["aa_capability_indexes"]["entries"] if e["isTopVariant"]]
    measured = view["aa_effort_evals"]["variants"]
    weights = {"Terminal-Bench-Science": 15, "CritPt v2 hard": 10, "FrontierCode 2.0": 15, "Terminal-Bench 4.1": 10}
    config = next(e for e in entries if e["slug"] == selected)
    chart = page.locator("#capBumpChart")
    expect(chart.locator(".cap-denominator")).to_have_count(5)
    exported = next(row for row in csv_download(page, "#exportCapIndexes") if row["model"] == config["name"])
    for metric, weight in weights.items():
        key = "eval:" + metric
        scores = [measured[e["slug"]]["metrics"][metric] for e in entries]
        score = measured[selected]["metrics"][metric]
        rank = 1 + sum(s > score for s in scores if s is not None)
        valid = sum(s is not None for s in scores)
        node = chart.locator(f'[data-cap-id="{selected}"] [data-domain="{key}"]')
        expect(node).to_have_attribute("data-rank", str(rank))
        expect(node).to_have_attribute("data-valid-n", str(valid))
        assert float(node.get_attribute("data-score")) == float(exported[key+"_score"]) == score
        assert int(exported[key+"_view_rank"]) == rank
        assert int(exported[key+"_weight_pct"]) == weight and exported[key+"_unit"] == "%"
        assert abs(float(exported[key+"_contribution_points"]) - score*weight/100) < 0.0001
    subtotal = sum(measured[selected]["metrics"][metric]*weight/100 for metric, weight in weights.items())
    expect(page.locator("#capIndexDetail")).to_contain_text(f"{subtotal:.2f} / 50 分")
    expect(page.locator("#capIndexDetail tbody tr")).to_have_count(5)
    page.locator("#capShowII").uncheck()
    expect(chart.locator(".cap-denominator")).to_have_count(4)
    page.locator('[data-cap-tab="eval:Terminal-Bench-Science"]').click()
    expect(chart.locator(".cap-bar")).to_have_count(len(entries))
    expect(chart).to_contain_text("100%")
    page.get_by_role("button", name="六个行业指数").click()
    expect(chart.locator(".cap-denominator")).to_have_count(6)
    expect(page.locator(f'[data-cap-model="{selected}"]')).to_have_attribute("aria-pressed","true")
    expect(page.locator("#capIndexDetail tbody tr")).to_have_count(7)
    page.locator("#capShowII").check()
    scope.select_option("four_family_top")


def check_v5_views(page, data, origin, output):
    view = v5_view(data)
    page.goto(origin + "/?aa=v5", wait_until="networkidle")
    require(page.evaluate("document.documentElement.dataset.aa") == "v5", "v5 view did not load")
    expect(page.locator("#aaVersionSelect")).to_have_value("v5")
    expect(page.locator('#marketUpdates a[href*="arcprize.org/results/google-gemini-4-neon"]')).to_have_count(1)
    full_suite = page.locator("#scaleHighlightsTable tr").filter(has=page.locator('a[href$="tab=full"]'))
    expect(full_suite.locator("td strong")).to_have_text(["#1", "#2", "#2", "#3"])
    # Version-specific prose: only the v5 blocks are visible, and page TOC has no duplicates.
    expect(page.locator('.pitfall-list[data-aa-version="v5"]')).to_be_visible()
    expect(page.locator('.pitfall-list[data-aa-version="v4"]')).to_be_hidden()
    expect(page.locator("#engineering-guide-v5")).to_be_visible()
    expect(page.locator("#engineering-guide")).to_be_hidden()
    toc_labels = page.eval_on_selector_all("#pageToc button", "bs => bs.map(b => b.textContent.trim())")
    require(len(toc_labels) == len(set(toc_labels)), f"Duplicate v5 page TOC entries: {toc_labels}")
    require("{{" not in page.content(), "Unresolved narrative placeholder")

    # Current and historical AA charts remain explicit; low v5 scores stay inside the plot.
    page.locator('[data-panel="explorer"]').click()
    expect(page.locator("#explorerIntro")).to_contain_text("26 个发布版本、87 个配置")
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
        missing_label = "Flash 3.8 low" if axis == "outputTokensPerTask" else "Wonder Full max"
        expect(page.locator("#releaseMissing")).to_contain_text(missing_label)
        expect(page.locator("#releaseChart .release-dot")).to_have_count(plotted)
        require(page.eval_on_selector("#releaseChart", "svg => [...svg.querySelectorAll('.release-dot circle')].every(c => Number(c.getAttribute('cy')) >= 34 && Number(c.getAttribute('cy')) <= svg.viewBox.baseVal.height - 62)"), "v5 score outside the plotted y range")
        require("未提供m" not in page.locator("#releaseChart").text_content(), "Missing time received a unit")
    page.select_option("#releaseXMetric", "costPerTask")
    for release, text in (("gemini-4-carbon","已开放付费 API"), ("muse-wonder-full","Muse Code")):
        page.locator(f'[data-rel-pill="{release}"]').click()
        expect(page.locator("#releaseDetail .release-availability")).to_contain_text(text)
        expect(page.locator("#releaseDetail")).to_contain_text("不是官方 token 单价或订阅扣额")
    with page.expect_download() as download:
        page.locator("#exportReleases").click()
    rows = list(csv.DictReader(io.StringIO(Path(download.value.path()).read_text(encoding="utf-8-sig"))))
    require(all(r["aa_version"] == data["aa_v5"]["version"] and r["aa_snapshot"] == view["aa_release_series"]["snapshot"] and r["source_url"].startswith("https://") for r in rows), "Release export lost version, date or source")
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

    # Missing-cost single points remain observations, not computed sweet spots; voices follow the selected model.
    page.locator('[data-panel="profiles"]').click()
    page.select_option("#profileModel", "claude-opus-5-5")
    page.select_option("#profileModel", "muse-wonder-full")
    expect(page.locator("#profileGrid .mp-mark.pick")).to_have_count(0)
    expect(page.locator("#profileGrid")).to_contain_text("仅测单点")
    expect(page.locator("#profileAltCoverage .mp-voices")).to_contain_text("Meta 闭源旗舰")
    page.select_option("#profileModel", "gemini-4-neon")
    expect(page.locator("#profileAltCoverage .mp-voices li").first).to_be_visible()
    page.select_option("#profileModel", "claude-opus-4-7")
    expect(page.locator("#profileAltCoverage .mp-voices")).to_have_count(0)
    page.locator('[data-panel="specs"]').click()
    for model in ("muse-wonder-full",):
        expect(page.locator(f'[data-cost-model="{model}"]')).to_have_attribute("data-per", "")
        expect(page.locator(f'[data-cost-model="{model}"]')).to_contain_text("暂不提供公开 API 预算")
    # Public Carbon pricing and Ember's strict >200k boundary include cached input.
    fields = ("inputTokens", "cachePercent", "answerTokens", "reasonTokens", "requestCount")
    saved = {key: page.input_value("#"+key) for key in fields}
    scenario = page.input_value("#priceScenario")
    scope = page.input_value("#specScope")
    page.select_option("#specScope", "all")
    for key, value in zip(fields, (10000, 0, 1000, 0, 1)):
        page.fill("#"+key, str(value))
    carbon = page.locator('[data-cost-model="gemini-4-carbon"]')
    page.select_option("#priceScenario", "current")
    require(abs(float(carbon.get_attribute("data-per"))-.03) < 1e-10, "Carbon public API budget missing")
    neon = page.locator('[data-cost-model="gemini-4-neon"]')
    require(abs(float(neon.get_attribute("data-per"))-.045) < 1e-10, "Neon flat API budget missing")
    sol56 = page.locator('[data-cost-model="gpt-5.6-sol"]')
    require(abs(float(sol56.get_attribute("data-per"))-.06) < 1e-10, "Sol promo price missing")
    page.select_option("#priceScenario", "afterPromo")
    require(abs(float(carbon.get_attribute("data-per"))-.06) < 1e-10, "Carbon post-promotion price missing")
    require(abs(float(neon.get_attribute("data-per"))-.045) < 1e-10, "Neon flat price should not change after promo")
    expect(sol56).to_have_attribute("data-per", "")
    page.fill("#inputTokens", "300000")
    expect(sol56).to_have_attribute("data-per", "")
    page.select_option("#priceScenario", "current")
    page.fill("#inputTokens", "1000000")
    page.fill("#answerTokens", "0")
    require(abs(float(neon.get_attribute("data-per"))-3.0) < 1e-10, "Neon 1M flat input pricing drifted")
    page.fill("#answerTokens", "1000")
    page.fill("#cachePercent", "100")
    ember = page.locator('[data-cost-model="muse-ember-1.0"]')
    for tokens, expected in ((200000, .0013), (200001, .003900012)):
        page.fill("#inputTokens", str(tokens))
        require(abs(float(ember.get_attribute("data-per"))-expected) < 1e-10,
                f"Ember cached-input tier boundary drifted at {tokens}")
    for key, value in saved.items():
        page.fill("#"+key, value)
    page.select_option("#priceScenario", scenario)
    page.select_option("#specScope", scope)
    page.locator('[data-panel="overview"]').click()
    expect(page.locator("#vendorCoverage .vendor-card")).to_have_count(5)
    # Footer and hero dates both follow the snapshot review date, so neither goes stale on refresh.
    expect(page.locator("#footerDate")).to_have_text(data["market_snapshot"]["reviewed_at"])
    factbook = "https://www.modelfactbook.com/"
    referral = "?utm_source=model-observatory&utm_medium=referral&utm_content="
    for selector, path in (("#crossSource", "model-family-checkpoint-version/" + referral + "cross-source"),
                           ("#evidence", "how-to-read-a-model-card/" + referral + "evidence"), ("footer", "")):
        link = page.locator(selector).locator(f'a[href="{factbook}{path}"]')
        expect(link).to_have_count(1)
        expect(link).to_have_attribute("target", "_blank")
    page.locator("#heroNews").click()
    expect(page.locator("#editionUpdates")).to_be_in_viewport()
    page.select_option("#marketVendor", "Meta")
    expect(page.locator("#marketTable tbody tr")).to_have_count(6)
    expect(page.locator("#marketTable")).to_contain_text("Muse Spark 1.3")
    expect(page.locator('#marketTable a[href*="muse-spark-1-3"]')).to_have_count(1)
    page.locator("#marketReset").click()

    # Task chart: one dot per measured variant, with v5 task labels.
    page.locator('[data-task-tab="agentic"]').click()
    expect(page.locator('[data-task-tab="agentic"]')).to_contain_text("Terminal-Bench-Science")
    require("NaN" not in page.locator("#taskEffortChart").inner_html(), "Invalid v5 task chart coordinate")
    tasks = ("complex", "coding", "planning", "agentic", "automation", "knowledge", "intelligenceIndex")
    for task in tasks:
        page.locator(f'[data-task-tab="{task}"]').click()
        for focus in ("all", "low"):
            page.select_option("#taskEffortFocus", focus)
            check_plot_y_bounds(page, "#taskEffortChart", 36, 62)
        expect(page.locator("#taskEffortChart .axis-label").last).to_contain_text("AA v5 单任务加权成本")
    page.select_option("#taskEffortFocus", "all")
    page.locator('[data-task-tab="complex"]').click()
    fable = next(r for r in view["aa_release_series"]["releases"] if r["releaseSlug"] == "claude-fable-5-2")
    max_score = next(v for v in fable["variants"] if v["effort"] == "max")["taskScores"]["complex"]
    display_score = page.evaluate("v=>v.toLocaleString('en-US',{maximumFractionDigits:1})", max_score)
    expect(page.locator("#taskEffortSubnote")).to_contain_text(f"Fable 5.2 max {display_score}%")
    expect(page.locator("#taskEffortLegend")).to_contain_text("Meta")
    page.locator('[data-task-pill="muse-wonder-full"]').click()
    expect(page.locator("#taskEffortDetail")).to_contain_text("未提供耗时")
    require("—m" not in page.locator("#taskEffortDetail").inner_text(), "Missing task time received a unit")
    page.locator('[data-task-pill="muse-wonder-full"]').click()
    page.locator("#taskEffortCard").screenshot(path=str(output / "v5-task-chart.png"))

    # Capability bump chart and its column header follow v5.
    page.locator('[data-panel="capabilities"]').click()
    expect(page.locator("#capBumpChart")).to_contain_text("AA 智能指数 " + data["aa_v5"]["version"])
    check_cap_benchmarks(page, view)
    n_measured = sum(len(r["variants"]) for r in view["aa_release_series"]["releases"] if any(v.get("taskScores") for v in r["variants"]))
    expect(page.locator("#effortScalingChart .scaling-dot")).to_have_count(n_measured)
    for task in tasks:
        page.select_option("#effortScalingTask", task)
        check_plot_y_bounds(page, "#effortScalingChart", 40, 60)
    page.select_option("#effortScalingTask", "complex")
    page.locator("#effortScalingChart").screenshot(path=str(output / "v5-effort-chart.png"))

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

    page.select_option("#profileModel", "claude-opus-5-5")
    # 305px also covers a 320px window with a traditional 15px scrollbar.
    for width in (390, 320, 305):
        page.set_viewport_size({"width": width, "height": 844})
        for panel in ("overview", "capabilities", "explorer", "reasoning", "profiles", "evidence"):
            page.locator(f'[data-panel="{panel}"]').click()
            require(page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth"), f"v5 page overflow: {width}px/{panel}")
            if panel == "profiles":
                require(page.locator("#profilePitfallList").evaluate("el => [...el.children].every(c=>c.getBoundingClientRect().right <= el.getBoundingClientRect().right + 1)"), "Profile pitfalls exceed their grid")
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.locator('[data-panel="overview"]').click()
    page.screenshot(path=str(output / "v5-overview.png"))

    # The header switch reloads into the other version and keeps it in the URL.
    with page.expect_navigation(wait_until="networkidle"):
        page.select_option("#aaVersionSelect", "v4")
    require(page.evaluate("document.documentElement.dataset.aa") == "v4", "Version switch did not load v4.3.2")
    require("aa=v4" in page.url, "Version switch is not reflected in the URL")
    expect(page.locator('.pitfall-list[data-aa-version="v4"]')).to_be_visible()
    expect(page.locator("#engineering-guide")).to_be_visible()
    expect(page.locator("#engineering-guide-v5")).to_be_hidden()
    v4_toc = page.eval_on_selector_all("#pageToc button", "bs => bs.map(b => b.textContent.trim())")
    require(len(v4_toc) == len(set(v4_toc)), f"Duplicate v4 page TOC entries: {v4_toc}")
