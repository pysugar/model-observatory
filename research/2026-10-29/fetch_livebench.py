"""Rebuild the LiveBench 2.0 board from the release's static files.

LiveBench publishes each release as static files under livebench.ai/data/<release>/.
Overall and cost per successful task are computed in the browser, never stored, so this
script recomputes them with the page's own rules (read from its bundle on 2026-10-29):

- Overall = weighted mean of the suite scores; `_overall_weights` in categories.json,
  default weight 1.
- Cost per successful task = (sum of suite costs / sum of suite task counts) / Overall * 100.

Display names follow the leaderboard page. Raw files are recorded by URL and SHA-256.
Run from the repository root: python3 research/2026-10-29/fetch_livebench.py
"""

from datetime import datetime, timezone
from pathlib import Path
import csv
import hashlib
import io
import json
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
OUT = HERE / "livebench.json"
RELEASE = "2026-10-25"
BASE = f"https://livebench.ai/data/{RELEASE.replace('-', '')}/"
# Page display name, vendor and open-weights flag for each model id in this release.
NAMES = {
    "claude-fable-5.1": ("Claude Fable 5.1", "Anthropic", False),
    "gpt-6-astra": ("GPT-6 Astra", "OpenAI", False),
    "claude-opus-5.5": ("Claude Opus 5.5", "Anthropic", False),
    "gpt-6.1-sol": ("GPT-6.1 Sol", "OpenAI", False),
    "claude-sonnet-5.5": ("Claude Sonnet 5.5", "Anthropic", False),
    "gemini-4-argon": ("Gemini 4 Argon", "Google", False),
    "gpt-6.1-terra": ("GPT-6.1 Terra", "OpenAI", False),
    "muse-wonder-1.0": ("Muse Wonder 1.0", "Meta", False),
    "deepseek-v4.1-flash-1017": ("DeepSeek V4.1 Flash 1017", "DeepSeek", True),
    "kimi-k3.1-pro": ("Kimi K3.1 Pro", "Moonshot AI", False),
    "grok-4.7": ("Grok 4.7", "xAI", False),
    "claude-haiku-5.5": ("Claude Haiku 5.5", "Anthropic", False),
    "mimo-v2.6-pro": ("MiMo V2.6 Pro", "Xiaomi", True),
    "gpt-5.6-terra": ("GPT-5.6 Terra", "OpenAI", False),
    "grok-4.6": ("Grok 4.6", "xAI", False),
    "minimax-m3.1-flash": ("MiniMax M3.1 Flash", "MiniMax", True),
    "gpt-6-luna": ("GPT-6 Luna", "OpenAI", False),
    "kimi-k3": ("Kimi K3", "Moonshot AI", True),
    "muse-spark-1.3": ("Muse Spark 1.3", "Meta", False),
    "glm-5.3-flash": ("GLM-5.3 Flash", "Z.AI", True),
    "qwen3.8-max": ("Qwen3.8 Max", "Alibaba", True),
    "gemini-3.8-flash": ("Gemini 3.8 Flash", "Google", False),
}
# Values shown on the leaderboard page on 2026-10-29 (browser read), used as a spot check.
PAGE_CHECK = {"claude-fable-5.1": (85.7, 6.904), "gpt-6-astra": (85.6, 4.548), "claude-opus-5.5": (85.1, 4.291),
              "gpt-6.1-sol": (84.1, 0.761), "deepseek-v4.1-flash-1017": (74.0, 0.181), "grok-4.7": (70.1, 2.913),
              "gemini-3.8-flash": (59.2, 1.659)}
SUITES = ["long_agentic", "reasoning", "coding", "browser", "data_analysis", "research", "design"]


def get(name):
    url = BASE + name
    raw = urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
    return url, raw


def main():
    pages, files = [], {}
    for name in ("table.csv", "categories.json", "cost.csv"):
        url, raw = get(name)
        pages.append({"url": url, "sha256": hashlib.sha256(raw).hexdigest()})
        files[name] = raw.decode("utf-8")
    categories = json.loads(files["categories.json"])
    weights = categories.pop("_overall_weights", {})
    suite_weight = {cols[0]: float(weights.get(cat, 1)) for cat, cols in categories.items()}
    costs = {row["model"]: row for row in csv.DictReader(io.StringIO(files["cost.csv"]))}
    rows = []
    for row in csv.DictReader(io.StringIO(files["table.csv"])):
        scores = {s: float(row[s]) for s in SUITES if row.get(s) not in (None, "", "n/a")}
        overall = sum(scores[s] * suite_weight[s] for s in scores) / sum(suite_weight[s] for s in scores)
        cost = costs.get(row["model"])
        cpst = None
        if cost:
            total = sum(float(cost[s]) for s in SUITES if cost.get(s))
            tasks = sum(float(cost["nq_" + s]) for s in SUITES if cost.get(s))
            cpst = round(total / tasks / overall * 100, 3)
        rows.append({"slug": row["model"], "overall": round(overall, 1), "overall_exact": round(overall, 3),
                     "cost_per_successful_task": cpst, "suites": scores})
    rows.sort(key=lambda r: -r["overall_exact"])
    by_slug = {r["slug"]: r for r in rows}
    for slug, (overall, cpst) in PAGE_CHECK.items():
        row = by_slug[slug]
        # The page rounds a slightly different intermediate; allow one unit in the last place.
        assert row["overall"] == overall and abs(row["cost_per_successful_task"] - cpst) <= 0.0015, (slug, row)
    for rank, row in enumerate(rows, 1):
        row["source_order"] = rank
        name = NAMES.get(row["slug"])
        row["model"], row["vendor"], row["open_weights"] = name if name else (row["slug"], None, None)
    out = {"source": "https://livebench.ai/#/", "release": RELEASE, "pages": pages,
           "weights": suite_weight, "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "rows": rows}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"rows": len(rows), "top": [(r["model"], r["overall"], r["cost_per_successful_task"]) for r in rows[:5]]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
