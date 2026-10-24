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


# ---------- Model profile pitfalls (mirrors report.js mpPitfalls) ----------
COST_ASSASSIN_RATIO = 2.0      # a step that at least doubles the cost ...
COST_ASSASSIN_SHARE = PRESETS["balanced"]  # ... yet gains less than 12% of the benchmark's score spread


def _profile_points(data, model_id):
    """{series_key: (points, elo, spread)}; points are dicts with effort/score/cost in effort order."""
    profiles = data["model_effort_profiles"]
    entry = next(m for m in profiles["models"] if m["id"] == model_id)
    name = next(m["name"] for m in data["models"] if m["id"] == model_id)
    out = {}
    active = active_releases(data)
    release = next((r for r in data["aa_release_series"]["releases"] if r["releaseSlug"] == entry["aaRelease"]), None)
    order = lambda pts: sorted(pts, key=lambda p: EFFORT_ORDER.index(p["effort"]))
    if release:
        for key, get in TASKS.items():
            values = [get(v) for r in active for v in r["variants"] if _finite(get(v))]
            pts = [{"effort": _norm(v["effort"]), "score": get(v), "cost": v.get("costPerTask")} for v in release["variants"] if _finite(get(v))]
            if pts:
                out["aa-" + key] = (order(pts), key in ("agentic", "planning"), _spread(values))
    for bench, key in (("coding", "vulcan"), ("writing", "tonebench")):
        pool = [r for r in data["rows"] if r["benchmark"] == bench and _finite(r["score"])]
        mine = [r for r in pool if r["model"] == name and _norm(r["effort"]) in EFFORT_ORDER
                and r.get("variant") not in ("unverified", "ultra_harness")]
        if mine:
            out[key] = (order([{"effort": _norm(r["effort"]), "score": r["score"], "cost": r.get("cost_usd")} for r in mine]), False, _spread([r["score"] for r in pool]))
    sweep = data["computer_use_evidence"]["openaiSweep"]
    series = next((s for s in sweep["series"] if s["modelId"] in entry["cuIds"]), None)
    if series:
        pts = [{"effort": e, "score": sc, "cost": c} for e, sc, c in zip(sweep["efforts"], series["scores"], series["costUsdPerTask"])]
        out["cu-openai"] = (pts, False, _spread([x for s in sweep["series"] for x in s["scores"]]))
    return out


def _release_date(data, model_id):
    entry = next(m for m in data["model_effort_profiles"]["models"] if m["id"] == model_id)
    rel = next((r for r in data["aa_release_series"]["releases"] if r["releaseSlug"] == entry["aaRelease"]), None)
    return rel.get("releaseDate") if rel else None


def profile_pitfalls(data, model_id):
    """Set of (kind, series_key, effort[, alt_model_id, alt_effort]) flagged for one model."""
    vendor = {m["id"]: m["vendor"] for m in data["models"]}
    mine = _profile_points(data, model_id)
    flags = set()
    for key, (pts, elo, spread) in mine.items():
        tol = 10 if elo else 0.5
        for i, p in enumerate(pts):
            lower = pts[:i]
            if lower and p["score"] < max(x["score"] for x in lower) - tol:
                flags.add(("regress", key, p["effort"]))
            prev = pts[i - 1] if i else None
            if prev and _finite(p["cost"]) and _finite(prev["cost"]) and prev["cost"] > 0 \
                    and p["cost"] / prev["cost"] >= COST_ASSASSIN_RATIO and p["score"] - prev["score"] < COST_ASSASSIN_SHARE * spread:
                flags.add(("cost", key, p["effort"]))
    # Same-vendor comprehensive dominance: another active model's effort is at least as good and no more
    # expensive on every benchmark series both have measured with costs (strictly better on at least one).
    others = [m["id"] for m in data["model_effort_profiles"]["models"] if m["id"] != model_id and vendor[m["id"]] == vendor[model_id]]
    other_points = {o: _profile_points(data, o) for o in others}
    mine_date = _release_date(data, model_id)
    line = {m["id"]: m["line"] for m in data["model_effort_profiles"]["models"]}
    efforts = [e for e in EFFORT_ORDER if any(p["effort"] == e for pts, _e, _s in mine.values() for p in pts)]
    for effort in efforts:
        mine_at = {k: next(p for p in pts if p["effort"] == effort) for k, (pts, _e, _s) in mine.items()
                   if any(p["effort"] == effort and _finite(p["cost"]) for p in pts)}
        best = None
        for o, series in other_points.items():
            alt_efforts = {p["effort"] for pts, _e, _s in series.values() for p in pts}
            for f in [e for e in EFFORT_ORDER if e in alt_efforts]:
                shared = [k for k in mine_at if any(q["effort"] == f and _finite(q["cost"]) for q in series.get(k, ([], 0, 0))[0])]
                if not shared:
                    continue
                ok, strict = True, False
                for k in shared:
                    p = mine_at[k]
                    q = next(q for q in series[k][0] if q["effort"] == f)
                    if q["score"] < p["score"] or q["cost"] > p["cost"]:
                        ok = False
                        break
                    strict = strict or q["score"] > p["score"] or q["cost"] < p["cost"]
                if ok and strict:
                    first = shared[0]
                    q_first = next(q for q in series[first][0] if q["effort"] == f)
                    cand = (-len(shared), q_first["cost"], o, EFFORT_ORDER.index(f), f)
                    best = min(best, cand) if best else cand
        if best:
            alt = best[2]
            alt_date = _release_date(data, alt)
            newer_same_line = line[alt] == line[model_id] and mine_date and alt_date and alt_date > mine_date
            flags.add(("upgrade" if newer_same_line else "dominated", "config", effort, alt, best[4]))
    return flags


# ---------- Better alternatives for one model x effort (mirrors report.js mpAlternatives) ----------
def profile_alternatives(data, model_id, effort, scope="vendor"):
    """{series_key: (cheaper, stronger)}; each is (model_id, effort) or None.

    cheaper  = lowest-cost config scoring at least as high and costing strictly less;
    stronger = highest-scoring config costing no more and scoring strictly higher.
    Candidates are active profile models (same vendor, or all four vendors), own other efforts included.
    """
    vendor = {m["id"]: m["vendor"] for m in data["models"]}
    pool = [m["id"] for m in data["model_effort_profiles"]["models"] if scope == "all" or vendor[m["id"]] == vendor[model_id]]
    series = {o: _profile_points(data, o) for o in pool}
    out = {}
    for key, (pts, _elo, _spread) in series[model_id].items():
        p = next((x for x in pts if x["effort"] == effort), None)
        if not p or not _finite(p["cost"]):
            continue
        cands = [(o, q) for o in pool for q in series[o].get(key, ([], 0, 0))[0]
                 if _finite(q["cost"]) and not (o == model_id and q["effort"] == effort)]
        cheaper = sorted((c for c in cands if c[1]["score"] >= p["score"] and c[1]["cost"] < p["cost"]),
                         key=lambda c: (c[1]["cost"], -c[1]["score"], c[0], EFFORT_ORDER.index(c[1]["effort"])))
        stronger = sorted((c for c in cands if c[1]["cost"] <= p["cost"] and c[1]["score"] > p["score"]),
                          key=lambda c: (-c[1]["score"], c[1]["cost"], c[0], EFFORT_ORDER.index(c[1]["effort"])))
        pick = lambda lst: (lst[0][0], lst[0][1]["effort"]) if lst else None
        out[key] = (pick(cheaper), pick(stronger))
    return out
