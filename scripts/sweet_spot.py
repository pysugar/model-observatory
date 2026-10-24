"""Reference implementation of the overview effort sweet-spot rule (mirrors report.js sweetPick/kneeOf).

For each model x task, walk the upper hull of (log2 cost, score) from the cheapest measured effort and keep
stepping up while each step gains at least `share` of the task's score spread per doubling of cost.
"""

import math

TASKS = {
    "ii": lambda v: v.get("intelligenceIndex"),
    "coding": lambda v: (v.get("taskScores") or {}).get("coding"),
    "complex": lambda v: (v.get("taskScores") or {}).get("complex"),
    "automation": lambda v: (v.get("taskScores") or {}).get("automation"),
    "agentic": lambda v: (v.get("taskScores") or {}).get("agentic"),
    "planning": lambda v: (v.get("taskScores") or {}).get("planning"),
    "knowledge": lambda v: (v.get("taskScores") or {}).get("knowledge"),
}
PRESETS = {"thrifty": 0.20, "balanced": 0.12, "performance": 0.06}


def _finite(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def active_releases(data):
    return [r for r in data["aa_release_series"]["releases"] if any(v.get("taskScores") for v in r["variants"])]


def knee(items, threshold):
    """items: dicts with score/cost/effort. Returns the chosen item, or None without costs."""
    pts = sorted(((math.log2(x["cost"]), x) for x in items if _finite(x["cost"]) and x["cost"] > 0 and _finite(x["score"])),
                 key=lambda p: (p[0], -p[1]["score"]))
    hull = []
    for lx, x in pts:
        if hull and lx == hull[-1][0]:
            continue
        while len(hull) >= 2:
            (alx, a), (blx, b) = hull[-2], hull[-1]
            if (b["score"] - a["score"]) * (lx - alx) <= (x["score"] - a["score"]) * (blx - alx):
                hull.pop()
            else:
                break
        hull.append((lx, x))
    if not hull:
        return None
    cur = hull[0]
    for nxt in hull[1:]:
        if (nxt[1]["score"] - cur[1]["score"]) / (nxt[0] - cur[0]) < threshold:
            break
        cur = nxt
    return cur[1]


def picks(data, share):
    releases = active_releases(data)
    out = {}
    for key, get in TASKS.items():
        values = [get(v) for r in releases for v in r["variants"] if _finite(get(v))]
        threshold = share * (max(values) - min(values)) if values else 0
        for rel in releases:
            items = [{"effort": v["effort"], "order": v["effortOrder"], "score": get(v), "cost": v.get("costPerTask")}
                     for v in rel["variants"] if _finite(get(v))]
            if not items:
                continue
            chosen = knee(items, threshold)
            if chosen is None:  # no costs: fall back to the best score, lowest effort on ties
                chosen = sorted(items, key=lambda x: (-x["score"], x["order"]))[0]
            out[(rel["releaseSlug"], key)] = chosen["effort"]
    return out


# ---------- Model profile tab (mirrors report.js mpSeries / mpPick) ----------
EFFORT_ORDER = ["none", "minimal", "low", "medium", "high", "xhigh", "max"]


def _norm(effort):
    return "none" if effort == "non-reasoning" else effort


def _pick(items, threshold):
    if not items:
        return None
    chosen = knee(items, threshold)
    if chosen is None:
        chosen = sorted(items, key=lambda x: (-x["score"], EFFORT_ORDER.index(x["effort"])))[0]
    return chosen["effort"]


def _spread(values):
    values = [v for v in values if _finite(v)]
    return max(values) - min(values) if values else 0


def profile_series(data, model_id, share):
    """Return {series_key: picked effort} for one profile model, using the same inputs as the page."""
    profiles = data["model_effort_profiles"]
    entry = next(m for m in profiles["models"] if m["id"] == model_id)
    name = next(m["name"] for m in data["models"] if m["id"] == model_id)
    out = {}
    active = active_releases(data)
    release = next((r for r in data["aa_release_series"]["releases"] if r["releaseSlug"] == entry["aaRelease"]), None)
    if release:
        for key, get in TASKS.items():
            values = [get(v) for r in active for v in r["variants"] if _finite(get(v))]
            threshold = share * (max(values) - min(values)) if values else 0
            items = [{"effort": _norm(v["effort"]), "score": get(v), "cost": v.get("costPerTask")}
                     for v in release["variants"] if _finite(get(v))]
            if items:
                out["aa-" + key] = _pick(items, threshold)
    for bench, key in (("coding", "vulcan"), ("writing", "tonebench")):
        pool = [r for r in data["rows"] if r["benchmark"] == bench and _finite(r["score"])]
        mine = [r for r in pool if r["model"] == name and _norm(r["effort"]) in EFFORT_ORDER
                and r.get("variant") not in ("unverified", "ultra_harness")]
        if mine:
            items = [{"effort": _norm(r["effort"]), "score": r["score"], "cost": r.get("cost_usd")} for r in mine]
            out[key] = _pick(items, share * _spread([r["score"] for r in pool]))
    cu = data["computer_use_evidence"]
    sweep = cu["openaiSweep"]
    series = next((s for s in sweep["series"] if s["modelId"] in entry["cuIds"]), None)
    if series:
        pool = [x for s in sweep["series"] for x in s["scores"]]
        items = [{"effort": e, "score": sc, "cost": c} for e, sc, c in zip(sweep["efforts"], series["scores"], series["costUsdPerTask"])]
        out["cu-openai"] = _pick(items, share * _spread(pool))
    row = next((r for r in cu["anthropicMax"]["rows"] if r["modelId"] in entry["cuIds"]), None)
    if row:
        out["cu-anthropic"] = cu["anthropicMax"]["nativeEffort"]
    return out
