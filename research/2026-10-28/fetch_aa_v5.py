"""Refresh the AA Intelligence Index v5 leaderboard rows from the public AA pages.

Reads the leaderboard's embedded model list (v5 scores, weighted cost per task, output
speed and the nine v5 evaluations) and rewrites only `board.rows` and `pages` in
aa-index-v5.json; the hand-written methodology notes stay as they are. No raw HTML is
committed: each page is recorded by URL and SHA-256.

Run from the repository root: python3 research/2026-10-28/fetch_aa_v5.py
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import hashlib
import json
import re
import sys
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "aa-index-v5.json"
OLD = ROOT / "research/2026-10-23/market-snapshot.json"
LEADERBOARD = "https://artificialanalysis.ai/leaderboards/models"
ARTICLE = "https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v5"

# Same selection as the 10-23 v4.3.2 board, plus configurations the v5 article names
# (Opus 5.5 low, Kimi K3.1 Pro, GPT-6.1 Terra) and Gemini 3.5 Flash-Lite. Opus 5.5 xhigh
# (56.99) is left out so the list reads as AA's model ranking: Opus 5.5 max, then GPT-6 Astra.
SELECTION = [
    "claude-opus-5-5", "claude-opus-5-5-high", "claude-opus-5-5-low",
    "gpt-6-astra", "gpt-6-1-sol", "gpt-6-1-sol-high", "claude-sonnet-5-5", "gpt-6-1-terra",
    "gemini-4-argon", "muse-wonder-full", "claude-fable-5-1", "kimi-k3-1-pro", "muse-wonder",
    "claude-haiku-5-5", "grok-4-7-high", "grok-4-7", "qwen3-8-max", "deepseek-v4-1-flash-1017",
    "glm-5-3", "gemini-3-8-flash", "mimo-v2-6-pro", "ling-3-1-flash-1019", "minimax-m3-1-flash",
    "step-5", "gpt-6-luna", "gemini-3-5-flash-lite",
]
# Not on the v5 leaderboard any more; listed in `pending` instead of guessed.
DROPPED = {"kimi-k3": "Kimi K3"}
# v4.3 scores the 10-23 board did not select, taken from AA's own launch article.
PREVIOUS_EXTRA = {
    "kimi-k3-1-pro": (55, "https://artificialanalysis.ai/articles/kimi-k3-1-pro-launch-benchmarks"),
}
EVALS = {
    "aa-briefcase": "AA-Briefcase (Elo)", "automationbench-aa": "AutomationBench-AA",
    "gdp-pdf": "GDP.pdf", "frontiercode-2-0": "FrontierCode 2.0",
    "terminalbench-4-0": "Terminal-Bench 4.0", "terminal-bench-science": "Terminal-Bench-Science",
    "critpt-v2-hard": "CritPt v2 hard", "omniscience-accuracy": "AA-Omniscience 准确率",
    "omniscience-non-hallucination": "AA-Omniscience 不幻觉率", "hle-diamond": "HLE-Diamond",
}
# AA counts it as open weights once published; the flag is not set yet.
UNRELEASED_WEIGHTS = {"kimi-k3-1-pro"}
VENDORS = {"Kimi": "Moonshot AI", "Z AI": "Z.AI", "SpaceXAI": "xAI"}
NAMES = {"Kimi K3.1 Pro": "Kimi K3.1 Pro"}


def fetch(url):
    request = Request(url, headers={"User-Agent": "model-observatory-research/1.0 (+https://github.com/pysugar/model-observatory)"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def flight_data(html):
    """Concatenate the Next.js flight chunks that carry the page's data."""
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, flags=re.S)
    return "".join(json.loads('"' + chunk + '"') for chunk in chunks)


def models(page):
    data = flight_data(page)
    start = data.index('"initialModels":') + len('"initialModels":')
    return json.JSONDecoder().raw_decode(data[start:])[0]


def display(value):
    """AA shows whole numbers rounded half up (34.5 → 35, as in the v5 article)."""
    return int(Decimal(str(round(value, 4))).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def split_name(name):
    match = re.match(r"(.*?) \((.*)\)$", name)
    if not match:
        return name, "页面未注明档位"
    base, inside = match.groups()
    parts = [p.strip() for p in inside.split(",")]
    effort = parts[0].lower()
    if not re.fullmatch(r"non-reasoning|low|medium|high|xhigh|max|\d{4}", effort):
        return name, "页面未注明档位"
    if effort.isdigit():  # e.g. "Qwen3.8 Max (0902)" is a snapshot date, not an effort
        return name, "页面未注明档位"
    label = effort + (" · 含回退" if any("Fallback" in p for p in parts[1:]) else "")
    return base, label


def change_label(score, previous):
    if previous is None:
        return "旧选录无此档"
    delta = score - previous
    return ("持平" if delta == 0 else f"{'+' if delta > 0 else '−'}{abs(delta)}") + f" · 原 {previous}"


def main():
    pages, bodies = [], {}
    for url in (LEADERBOARD, ARTICLE):
        body = fetch(url)
        bodies[url] = body.decode("utf-8", "replace")
        pages.append({"url": url, "sha256": hashlib.sha256(body).hexdigest()})
    by_slug = {m["slug"]: m for m in models(bodies[LEADERBOARD])}
    old = {(r["model"], r["configuration"]): r["score"]
           for r in json.loads(OLD.read_text())["boards"][0]["rows"]}
    rows, missing = [], []
    for slug in SELECTION:
        m = by_slug.get(slug)
        if not m or m.get("intelligenceIndex") is None:
            missing.append(slug)
            continue
        model, configuration = split_name(m["name"])
        model = NAMES.get(model, model)
        score = display(m["intelligenceIndex"])
        previous, previous_source = old.get((model, configuration)), None
        if previous is None and slug in PREVIOUS_EXTRA:
            previous, previous_source = PREVIOUS_EXTRA[slug]
        cost = m.get("intelligenceIndexCostPerTask")
        tps = m.get("medianOutputTokensPerSecond")
        row = {
            "slug": slug, "model": model,
            "vendor": VENDORS.get(m["modelCreatorName"], m["modelCreatorName"]),
            "configuration": configuration, "score": score,
            "score_exact": round(m["intelligenceIndex"], 2),
            "prev_score": previous, "change": change_label(score, previous),
            "cost_usd": round(cost, 2) if cost is not None else None,
            "output_tps": round(tps) if tps else None,
            "open_weights": bool(m.get("isOpenWeights")),
            "evals": {label: (round(m["scores"][key], 4) if key in m["scores"] else None)
                      for key, label in EVALS.items()},
        }
        if previous_source:
            row["prev_source"] = previous_source
        # Tag after matching, so the label never breaks the v4.3.2 lookup.
        if slug in UNRELEASED_WEIGHTS:
            row["configuration"] += " · 开放权重（尚未发布）"
        elif row["open_weights"]:
            row["configuration"] += " · 开放权重"
        rows.append(row)
    if missing:
        sys.exit(f"Selected configurations missing from the leaderboard: {missing}")
    rows.sort(key=lambda r: (-r["score_exact"], r["slug"]))
    for index, row in enumerate(rows, 1):
        row["id"] = f"r{index}"
    doc = json.loads(OUT.read_text())
    doc["board"]["rows"] = [{"id": r.pop("id"), **r} for r in rows]
    doc["pages"] = pages
    doc["fetched_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    doc["dropped_from_v5"] = DROPPED
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"rows": len(rows), "pages": [p["sha256"][:12] for p in pages]}))


if __name__ == "__main__":
    main()
