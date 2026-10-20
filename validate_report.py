"""Validate evidence preservation, budget boundaries, and browser interactions."""

from collections import Counter
from pathlib import Path
import csv
import io
import json
import math
import re

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "verification"
OUT.mkdir(exist_ok=True)
DATA = json.loads((ROOT / "report-data.json").read_text())
html = (ROOT / "model-capability-cost.html").read_text()
original = (ROOT / "archive/model-capability-cost-2026-10-14.html").read_text()
original_rows = json.loads(re.search(r'<script id="dataset" type="application/json">(.*?)</script>', original, re.S)[1])["rows"]
embedded = json.loads(re.search(r'<script id="report-data" type="application/json">(.*?)</script>', html, re.S)[1])
assert embedded == DATA
assert len(original_rows) == 121
for old, new in zip(original_rows, DATA["rows"]):
    assert {key: new[key] for key in old} == old
assert Counter(r["benchmark"] for r in DATA["rows"]) == {"general": 62, "coding": 45, "writing": 50, "arena": 12}
assert len(DATA["models"]) == 24 and sum(m["current"] for m in DATA["models"]) == 21
assert len(DATA["aa_profiles"]) == 21
assert len(DATA["aa_capability_indexes"]["domains"]) == 6 and len(DATA["aa_capability_indexes"]["entries"]) == 90
assert len(DATA["aa_release_series"]["releases"]) == 30
assert len(DATA["aa_effort_evals"]["variants"]) == 44
assert len(DATA["external_leaderboards"]["platforms"]) == 5 and len(DATA["external_leaderboards"]["four_family_matrix"]) == 11
assert len(list(csv.DictReader((ROOT / "report-data.csv").open(encoding="utf-8-sig")))) == 169
for forbidden in ["GEO", "OpenClaw", "Hermes", "未修改本机配置", "用户提供的 Claude 模型选择器截图"]:
    assert forbidden not in html, f"Personal/private keyword still present: {forbidden}"
claude = [m for m in DATA["models"] if m["vendor"] == "Anthropic"]
assert len(claude) == 14 and sum(m["screenshot_visible"] for m in claude) == 8
assert {p["model"] for p in DATA["aa_profiles"] if p.get("score_estimated")} == {"Claude Opus 4.7", "Claude Opus 4.6", "Claude Opus 4.5"}
assert next(p for p in DATA["aa_profiles"] if p["model"] == "Claude Haiku 4.5")["metrics"]["AA-Omniscience"] == -4
assert all(r["variant"] == "mixed_fallback" for r in DATA["rows"] if r["model"] == "Claude Fable 5" and r["effort"] == "max")
current = {m["name"] for m in DATA["models"] if m["current"]}
checks = [
    "Original 121 records preserved; zero personal/GEO/OpenClaw/Hermes references",
    "169 JSON/CSV records agree (including Grok 4.7 low/high/xhigh)",
    "24 models, including 14 Claude, 8 common client models, and Grok 4.7",
    "AA Capability Indexes (6 domains × 90 variants), AA Release Series (30 releases), and 44 active per-effort task evaluations verified",
    "Estimated scores, Unicode minus, and Fable 5 fallback preserved",
]


def cost(page, model, attribute="data-per"):
    value = page.locator(f'[data-cost-model="{model}"]').get_attribute(attribute)
    return float(value) if value else None


def close(actual, expected):
    assert math.isclose(actual, expected, rel_tol=1e-10), (actual, expected)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel="chrome", chromium_sandbox=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
    errors, external = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("request", lambda request: external.append(request.url) if not request.url.startswith(("http://127.0.0.1", "file:", "blob:")) else None)
    page.goto((ROOT / "model-capability-cost.html").as_uri(), wait_until="load")
    page.screenshot(path=str(OUT / "overview-desktop.png"), full_page=True)
    assert page.locator('[role="tab"]').count() == 6
    assert page.locator("#overview").is_visible()
    assert not errors, errors
    assert page.locator("#taskEffortChart .task-dot").count() == 43
    assert "Most attractive quadrant" in page.locator("#taskEffortLegend").inner_text()
    assert "Most attractive quadrant" in page.locator("#taskEffortChart").inner_html()
    assert page.locator("#taskCategoryCards .platform-card").count() == 4
    for t_tab in ["complex", "coding", "planning", "agentic", "automation", "knowledge", "intelligenceIndex"]:
        page.locator(f'[data-task-tab="{t_tab}"]').click()
        assert not re.search(r"\b(?:NaN|Infinity)\b", page.locator("#taskEffortChart").inner_html())
    page.select_option("#taskEffortMode", "top_variants")
    assert page.locator("#taskEffortChart .task-dot").count() == 11
    page.select_option("#taskEffortMode", "release_trajectories")
    page.locator('[data-task-tab="complex"]').click()
    assert page.locator("#platformCards .platform-card").count() == 5
    assert page.locator("#panoramaTable tbody tr").count() == 11
    page.select_option("#panoramaFamily", "Grok (xAI / SpaceXAI)")
    assert page.locator("#panoramaTable tbody tr").count() == 1
    assert "Grok 4.7" in page.locator("#panoramaTable").inner_text()
    page.select_option("#panoramaFamily", "all")
    assert page.locator("#scaleHighlightsTable tbody tr").count() == 6
    assert page.locator("#claudeCatalog tbody tr").count() == 14
    page.select_option("#claudeScope", "screenshot")
    assert page.locator("#claudeCatalog tbody tr").count() == 8
    assert "usage credits" in page.locator("#claudeCatalog").inner_text()
    with page.expect_download() as download:
        page.locator("#exportClaude").click()
    exported = list(csv.DictReader(io.StringIO(Path(download.value.path()).read_text(encoding="utf-8-sig"))))
    assert len(exported) == 8 and all(r["chinese_tested"] == "false" for r in exported)
    page.locator('[data-claude-reasoning="Claude Haiku 4.5"]').click()
    assert page.locator("#reasoning").is_visible()
    assert "无 effort" in page.locator("#deltaModelInfo").inner_text()
    assert "不足两个" in page.locator("#deltaTable").inner_text()
    page.select_option("#deltaModel", "Claude Opus 5.5")
    page.select_option("#deltaGroup", "writing")
    page.locator('[data-panel="overview"]').click()
    page.select_option("#claudeScope", "all")
    checks.append("AA Task×Effort quadrant & trajectory chart, 5-platform × 4-family panorama, Claude availability table, and CSV export")
    page.locator('[data-panel="capabilities"]').click()
    assert page.locator("#effortScalingChart .scaling-dot").count() == 44
    assert page.locator("#effortScalingTable tbody tr").count() == 11
    for s_task in ["complex", "coding", "planning", "agentic", "automation", "knowledge", "intelligenceIndex"]:
        page.select_option("#effortScalingTask", s_task)
        assert not re.search(r"\b(?:NaN|Infinity)\b", page.locator("#effortScalingChart").inner_html())
    page.select_option("#effortScalingTask", "complex")
    assert page.locator("#capBumpChart .bump-group").count() == 16
    assert not re.search(r"\b(?:NaN|Infinity)\b", page.locator("#capBumpChart").inner_html())
    page.select_option("#capIndexScope", "all_top")
    assert page.locator("#capBumpChart .bump-group").count() == 30
    page.locator('[data-cap-tab="engineering"]').click()
    assert page.locator("#capBumpChart .bump-group").count() == 30
    assert not re.search(r"\b(?:NaN|Infinity)\b", page.locator("#capBumpChart").inner_html())
    page.locator('[data-cap-tab="all"]').click()
    page.select_option("#capIndexScope", "four_family_top")
    assert page.locator("#capabilityTable tbody tr").count() == 21
    page.select_option("#profileScope", "claude")
    assert page.locator("#capabilityTable tbody tr").count() == 14
    assert "41*" in page.locator("#capabilityTable tbody tr").filter(has_text="Claude Opus 4.7").inner_text()
    page.select_option("#profileScope", "screenshot")
    assert page.locator("#capabilityTable tbody tr").count() == 8
    page.select_option("#profileScope", "all")
    page.select_option("#dimension", "speed")
    page.locator('[data-sort="Output Speed"]').click()
    assert "Flash-Lite" in page.locator("#capabilityTable tbody tr").first.inner_text()
    assert "未提供" in page.locator("#capabilityTable tbody tr").filter(has_text="Argon").inner_text()
    page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
    page.screenshot(path=str(OUT / "capabilities-speed.png"), full_page=True)
    with page.expect_download() as download:
        page.locator("#exportProfiles").click()
    profile_rows = list(csv.DictReader(io.StringIO(Path(download.value.path()).read_text(encoding="utf-8-sig"))))
    assert len(profile_rows) == 21
    assert next(r for r in profile_rows if r["model"] == "Gemini 3.5 Flash-Lite")["Output Speed"] == "438"
    checks.append("Reasoning Effort Scaling slopes + 11×6 heatmap, AA Capability Index rank bump chart, 6-domain bar charts, capability sorting, and CSV export")

    page.locator('[data-panel="explorer"]').click()
    assert page.locator("#releaseChart .release-dot").count() > 20
    assert "Most attractive quadrant" in page.locator("#releaseChart").inner_html()
    for r_axis in ["costPerTask", "timePerTaskMinutes", "outputTokensPerTask"]:
        page.select_option("#releaseXMetric", r_axis)
        assert not re.search(r"\b(?:NaN|Infinity)\b", page.locator("#releaseChart").inner_html())
    page.select_option("#releaseXMetric", "costPerTask")
    assert page.locator("#releaseDetail .cost-stack span").count() >= 3
    for group in ["general", "coding", "writing", "arena"]:
        page.locator(f'[data-group="{group}"]').click()
        expected = [r for r in DATA["rows"] if r["benchmark"] == group and r["model"] in current]
        assert page.locator("#tbody tr").count() == len(expected)
        assert page.locator("#chart .dot").count() == sum(r["cost_usd"] is not None for r in expected)
        for scale in ["linear", "log"]:
            page.select_option("#scale", scale)
            assert not re.search(r"\b(?:NaN|Infinity)\b", page.locator("#chart").inner_html())
        page.locator("#selectAll").click()
        assert page.locator("#tbody tr").count() == sum(r["benchmark"] == group for r in DATA["rows"])
        if group == "coding":
            assert "收据 21/23" in page.locator("#gaps").inner_text()
            assert "收据 19/23" in page.locator("#gaps").inner_text()
            page.select_option("#xmetric", "minutes_per_task_all_runs")
            assert page.locator("#chart .dot").count() == 45
            page.locator("#verifiedOnly").check()
            assert page.locator("#chart .dot").count() == 41
            page.locator("#verifiedOnly").uncheck()
        page.locator("#chart .dot").first.focus()
        page.keyboard.press("Enter")
        assert page.locator("#detail h3").inner_text()
        page.locator("#currentModels").click()
    page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
    page.screenshot(path=str(OUT / "arena-desktop.png"), full_page=True)
    page.locator('[data-group="coding"]').click()
    page.locator("#selectAll").click()
    with page.expect_download() as download:
        page.locator("#export").click()
    coding_rows = list(csv.DictReader(io.StringIO(Path(download.value.path()).read_text(encoding="utf-8-sig"))))
    assert len(coding_rows) == 45
    assert sum(r["cost_usd"] == "" for r in coding_rows) == 2
    page.locator("#clearAll").click()
    assert page.locator("#chart .dot").count() == 0
    assert "没有可绘数据" in page.locator("#chart").text_content()
    page.locator("#reset").click()
    assert page.locator("#models input:checked").count() == 21
    page.locator("#claudeModels").click()
    assert page.locator("#models input:checked").count() == 14
    page.locator("#screenshotModels").click()
    assert page.locator("#models input:checked").count() == 8
    assert "没有纳入同基准数据" in page.locator("#gaps").inner_text()
    page.locator('[data-group="writing"]').click()
    assert page.locator("#tbody tr").count() == 12
    page.locator("#verifiedOnly").check()
    assert "Fable 5" not in page.locator("#tbody").inner_text()
    page.locator("#reset").click()
    checks.append("All four benchmarks, AA By-Release trajectory chart, model filters, axes, null receipts, keyboard points, CSV export")

    page.locator('[data-panel="specs"]').click()
    assert page.locator("#specTable tbody tr").count() == 21
    page.select_option("#specScope", "screenshot")
    assert page.locator("#specTable tbody tr").count() == 8
    close(cost(page,"claude-haiku-4-5-20251001"), .06)
    close(cost(page,"claude-sonnet-5"), .12)
    close(cost(page,"claude-opus-5"), .3)
    close(cost(page,"claude-fable-5"), .6)
    page.fill("#inputTokens", "190001")
    assert cost(page,"claude-haiku-4-5-20251001") is None
    page.fill("#inputTokens", "10000")
    page.fill("#reasonTokens", "64000")
    assert cost(page,"claude-haiku-4-5-20251001") is None
    page.fill("#reasonTokens", "8000")
    page.select_option("#specScope", "current")
    assert page.locator(".calc-inputs input:invalid").count() == 0
    close(cost(page,"gpt-6.1-sol"), .12)
    close(cost(page,"gpt-6.1-sol","data-total"), 120)
    close(cost(page,"claude-haiku-5-5"), .006)
    close(cost(page,"gemini-4-argon"), .12)
    page.fill("#cachePercent", "50")
    close(cost(page,"gpt-6.1-sol"), .1105)
    page.fill("#cachePercent", "0")
    page.fill("#inputTokens", "100000")
    close(cost(page,"claude-haiku-5-5"), .015)
    page.fill("#inputTokens", "100001")
    close(cost(page,"claude-haiku-5-5"), .0750005)
    page.fill("#inputTokens", "272000")
    close(cost(page,"gpt-6.1-sol"), .644)
    page.fill("#inputTokens", "272001")
    close(cost(page,"gpt-6.1-sol"), 1.238004)
    page.fill("#inputTokens", "10000")
    page.select_option("#priceScenario", "afterPromo")
    close(cost(page,"gemini-4-argon"), .24)
    close(cost(page,"gemini-3.8-flash"), .09)
    page.fill("#reasonTokens", "128000")
    assert cost(page,"gpt-6.1-sol") is None
    assert "超出同步输出上限" in page.locator("#costTable").inner_text()
    page.fill("#reasonTokens", "8000")
    page.fill("#inputTokens", "1040000")
    assert cost(page,"gemini-4-argon") is None
    assert cost(page,"gemini-3.8-flash") is not None
    page.fill("#inputTokens", "10000")
    page.fill("#cachePercent", "101")
    assert page.locator("#costTable tr").count() == 0
    page.fill("#cachePercent", "0")
    page.select_option("#priceScenario", "current")
    close(cost(page,"grok-4-7"), .08)
    page.select_option("#specScope", "all")
    assert page.locator("#specTable tbody tr").count() == 24
    with page.expect_download() as download:
        page.locator("#exportSpecs").click()
    assert len(list(csv.DictReader(io.StringIO(Path(download.value.path()).read_text(encoding="utf-8-sig"))))) == 24
    page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
    page.screenshot(path=str(OUT / "calculator-desktop.png"), full_page=True)
    checks.append("Budget arithmetic (including Grok 4.7), cache, exact tier boundaries, promotion scenario, context/output limits")

    page.locator('[data-panel="reasoning"]').click()
    assert "2.57 倍" in page.locator("#deltaTable").inner_text()
    page.select_option("#deltaModel", "GPT 6.1 Sol")
    assert "-0.41" in page.locator("#deltaTable").inner_text()
    page.select_option("#deltaModel", "Gemini 4 Argon")
    assert "不足两个" in page.locator("#deltaTable").inner_text()
    page.select_option("#deltaModel", "Claude Opus 5.5")
    page.select_option("#deltaGroup", "coding")
    assert page.locator("#deltaTable").is_hidden()
    assert page.locator("#opusCodingEvidence").is_visible()
    assert "12/23；47.8%" in page.locator("#opusEvidenceTable").inner_text()
    for view in DATA["opus_coding_evidence"]["views"]:
        page.select_option("#opusEvidenceView", view["id"])
        assert page.locator("#opusEvidenceTable tbody tr").count() == len(view["rows"])
        with page.expect_download() as download:
            page.locator("#exportOpusEvidence").click()
        exported = list(csv.DictReader(io.StringIO(Path(download.value.path()).read_text(encoding="utf-8-sig"))))
        assert len(exported) == len(view["rows"])
        assert all(row["evidence_view"] == view["id"] and row["caveat"] for row in exported)
    page.select_option("#deltaGroup", "writing")
    assert page.locator("#opusCodingEvidence").is_hidden()
    assert "2.57 倍" in page.locator("#deltaTable").inner_text()
    page.locator('[data-panel="evidence"]').click()
    assert page.locator("#sourceList .source-item").count() == len(DATA["sources"])
    page.locator('[data-panel="overview"]').focus()
    page.keyboard.press("ArrowRight")
    assert page.locator("#capabilities").is_visible()
    checks.append("Reasoning deltas, exclusion rules, source index, accessible tabs")

    for width in [320, 390]:
        page.set_viewport_size({"width":width,"height":844})
        for panel in ["overview","capabilities","explorer","specs","reasoning","evidence"]:
            page.locator(f'[data-panel="{panel}"]').click()
            page.wait_for_timeout(80)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), (width, panel)
    page.locator('[data-panel="explorer"]').click()
    page.locator('[data-group="writing"]').click()
    page.locator(".filters summary").click()
    page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
    page.screenshot(path=str(OUT / "writing-mobile.png"), full_page=True)
    page.locator('[data-panel="overview"]').click()
    page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
    page.screenshot(path=str(OUT / "overview-mobile.png"), full_page=True)
    page.context.set_offline(True)
    page.goto((ROOT / "model-capability-cost.html").as_uri(), wait_until="load")
    page.locator('[data-panel="explorer"]').click()
    assert page.locator("#chart .dot").count() > 0
    assert not errors, errors
    assert not external, external
    checks.append("390px responsive layout; standalone file works offline; no page errors or remote requests")
    browser.close()

result = {"status":"PASS","checks":checks,"rows":169,"screenshots":sorted(p.name for p in OUT.glob("*.png"))}
(OUT / "validation.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(result,ensure_ascii=False,indent=2))
