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
