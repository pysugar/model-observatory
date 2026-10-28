"""Browser checks for the default AA Intelligence Index v5 view and the version switch.

The v4.3.2 checks in smoke.py run on `?aa=v4`; here the v5 view is compared with the same
Python reference implementation (scripts/sweet_spot.py) fed the v5 data, so nothing below
hard-codes a v5 number.
"""

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
