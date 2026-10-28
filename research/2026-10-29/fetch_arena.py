"""Read Arena boards from Arena's own Hugging Face dataset (lmarena-ai/leaderboard-dataset).

arena.ai blocks scripted and automated browser reads (Cloudflare), so this uses the
dataset Arena publishes with every leaderboard update. Files are pinned to one dataset
revision and recorded by URL and SHA-256. Needs pyarrow (the shared research venv).

- text_style_control / overall: the default view of arena.ai/leaderboard/chat/text.
- webdev / overall: Code Arena (WebDev), Bradley-Terry scores.
- agent / overall and agent_praise_complaint / overall: Agent Arena IPS scores from real
  agent sessions; praise/complaint is the share of explicit user praise versus complaints.

Run from the repository root: python3 research/2026-10-29/fetch_arena.py
"""

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import io
import json
import re
from urllib.request import Request, urlopen

import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
OUT = HERE / "arena.json"
DATASET = "lmarena-ai/leaderboard-dataset"
REVISION = "6852ae7aa7c105ff8cf86bb1551d1b1fd52f9dd3"
CONFIGS = ["text_style_control", "webdev", "agent", "agent_praise_complaint"]
VENDORS = {"anthropic": "Anthropic", "openai": "OpenAI", "google": "Google", "xai": "xAI", "meta": "Meta",
           "deepseek": "DeepSeek", "moonshot": "Moonshot AI", "zai": "Z.AI", "alibaba": "Alibaba",
           "xiaomi": "Xiaomi", "minimax": "MiniMax", "tencent": "Tencent", "stepfun": "StepFun", "nvidia": "NVIDIA",
           "mistral": "Mistral AI", "amazon": "Amazon", "thinking machines": "Thinking Machines"}
TOP = 40  # rows kept per board; `total` records the full count
# Lower-ranked rows are also kept for models the site tracks, so a missing cell means "not on the board".
TRACKED = ("GPT-6 Astra", "GPT-6.1 Sol", "GPT-6 Luna", "Claude Opus 5.5", "Claude Fable 5.1", "Claude Sonnet 5.5",
           "Claude Haiku 5.5", "Gemini 4 Argon", "Gemini 3.8 Flash", "Gemini 3.5 Flash-Lite", "Grok 4.7",
           "DeepSeek-V4.1-Flash-20261017", "Kimi K3.1 Pro", "GLM-5.3", "MiMo-V2.6-Pro")


def split_name(raw):
    """'Claude Opus 5.5 (Max)' -> ('Claude Opus 5.5', 'max'); unnamed effort stays 'default'."""
    m = re.fullmatch(r"(.+?) \(([^()]+)\)", raw)
    if not m:
        return raw, "default"
    effort = m[2].lower()
    return (m[1], effort) if effort in {"low", "medium", "high", "xhigh", "max", "minimal"} else (raw, "default")


def main():
    pages, boards = [], {}
    for config in CONFIGS:
        url = f"https://huggingface.co/datasets/{DATASET}/resolve/{REVISION}/{config}/latest-00000-of-00001.parquet"
        raw = urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
        pages.append({"url": url, "sha256": hashlib.sha256(raw).hexdigest()})
        table = pq.read_table(io.BytesIO(raw)).to_pylist()
        rows = sorted((r for r in table if r["category"] == "overall"), key=lambda r: r["rank"])
        out = []
        for r in rows:
            model, effort = split_name(r["model_name"])
            row = {"source_rank": int(r["rank"]), "raw_name": r["model_name"], "model": model, "effort": effort,
                   "vendor": VENDORS.get(r["organization"].lower(), r["organization"]),
                   "open_weights": r["license"] not in ("Proprietary", None)}
            if "rating" in r:
                row.update(score=round(r["rating"], 1), lower=round(r["rating_lower"], 1),
                           upper=round(r["rating_upper"], 1), votes=int(r["vote_count"]))
            else:
                row.update(score=round(r["score"], 4), lower=round(r["score_ci_lower"], 4),
                           upper=round(r["score_ci_upper"], 4), observations=int(r["observation_count"]),
                           sessions=None if r["session_count"] != r["session_count"] or r["session_count"] is None
                           else int(r["session_count"]))
            out.append(row)
        boards[config] = {"published": rows[0]["leaderboard_publish_date"], "total": len(rows),
                          "rows": [r for r in out if r["source_rank"] <= TOP or r["model"] in TRACKED]}
    result = {"dataset": f"https://huggingface.co/datasets/{DATASET}", "revision": REVISION, "pages": pages,
              "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "boards": boards}
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: [b["published"], b["total"], b["rows"][0]["raw_name"]] for k, b in boards.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
