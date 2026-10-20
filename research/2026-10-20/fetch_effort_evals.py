"""Fetch Artificial Analysis per-effort evaluation tables for the four families' current models.

Each public comparison page lists the ten Intelligence Index v4.3.x evaluations for two
variants. We only keep parsed tables plus the page SHA-256 (no raw HTML is committed).
Run: uv run -- python research/2026-10-20/fetch_effort_evals.py
"""

from datetime import datetime, timezone
from html import unescape
from pathlib import Path
import hashlib
import json
import re
import ssl
import sys
import time
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
SUPPLEMENT = HERE.parent / "2026-10-19" / "multi-benchmark-supplement.json"
OUT = HERE / "aa-effort-evals.json"
BASE = "https://artificialanalysis.ai/models/comparisons/"
RELEASES = [
    "grok-4-7",
    "gpt-6-1-sol", "gpt-6-astra", "gpt-6-luna",
    "gemini-4-argon", "gemini-3-8-flash", "gemini-3-5-flash-lite",
    "claude-opus-5-5", "claude-sonnet-5-5", "claude-fable-5-1", "claude-haiku-5-5",
]
EVALS = [
    "Intelligence Index", "AA-Briefcase v1.1", "GDPval-AA v2.1", "AutomationBench-AA",
    "Terminal-Bench 4.0", "SciCode", "Humanity's Last Exam", "GDP.pdf", "CritPt",
    "AA-Omniscience", "AA-LCR v1.1",
]
EFFORT_LABEL = {"non-reasoning": "Non-reasoning", "low": "Low", "medium": "Medium",
                "high": "High", "xhigh": "Xhigh", "max": "Max"}


def text(fragment):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def parse(html):
    header = re.search(r"<thead[^>]*>(.*?)</thead>", html, re.S)
    names = [text(c) for c in re.findall(r"<th[^>]*>(.*?)</th>", header[1], re.S)] if header else []
    rows = {}
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        label = re.search(r"<th[^>]*>(.*?)</th>", row, re.S)
        if not label:
            continue
        cells = [text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        name = text(label[1])
        if name in EVALS and len(cells) >= 2 and name not in rows:
            rows[name] = cells[:2]
    return names, rows


def number(value):
    match = re.search(r"-?\d[\d,]*(?:\.\d+)?", value or "")
    return float(match[0].replace(",", "")) if match else None


def fetch(url):
    try:
        import certifi
        context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        context = ssl.create_default_context()
    request = Request(url, headers={"User-Agent": "model-observatory-research/1.0 (+https://github.com/pysugar/model-observatory)"})
    with urlopen(request, timeout=45, context=context) as response:
        return response.read()


def matches_col(rel, var, col_header):
    h = (col_header or "").lower().replace("gpt-", "gpt ")
    rname = rel["name"].lower().replace("gpt-", "gpt ")
    if rname not in h:
        return False
    eff = EFFORT_LABEL[var["effort"]].lower()
    return True if "(" not in h else f"({eff}" in h


def main():
    supplement = json.loads(SUPPLEMENT.read_text())
    releases = {r["releaseSlug"]: r for r in supplement["aa_release_series"]["releases"]}
    variants = [(slug, v) for slug in RELEASES for v in releases[slug]["variants"]]
    pairs, pending = [], [v for _, v in variants]
    while pending:
        first = pending.pop(0)
        second = pending.pop(0) if pending else next(v for _, v in variants if v["slug"] != first["slug"])
        pairs.append((first, second))
    pages, results = [], {}
    for first, second in pairs:
        url = f"{BASE}{first['slug']}-vs-{second['slug']}"
        try:
            body = fetch(url)
        except Exception as error:  # keep failures visible in the evidence file
            pages.append({"url": url, "error": f"{type(error).__name__}: {error}"})
            print("FAIL", url, error, file=sys.stderr)
            continue
        names, rows = parse(body.decode("utf-8", "replace"))
        pages.append({"url": url, "sha256": hashlib.sha256(body).hexdigest(), "header": names,
                      "rows": rows})
        for col_idx, col_label in enumerate(names[1:3]):
            for rslug, variant in variants:
                rel = releases[rslug]
                if matches_col(rel, variant, col_label) and variant["slug"] not in results and rows:
                    results[variant["slug"]] = {
                        "slug": variant["slug"], "releaseSlug": rslug, "model": rel["name"],
                        "vendor": rel["vendor"], "effort": variant["effort"],
                        "effortOrder": variant["effortOrder"], "source_url": url,
                        "column_label": col_label, "label_matches_effort": True,
                        "raw": {k: v[col_idx] for k, v in rows.items()},
                        "metrics": {k: number(v[col_idx]) for k, v in rows.items()},
                    }
        print("OK", url, len(rows))
        time.sleep(1.2)
    OUT.write_text(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Artificial Analysis public model comparison pages (Intelligence Index v4.3.2)",
        "evals": EVALS, "pages": pages, "variants": results,
    }, ensure_ascii=False, indent=2) + "\n")
    missing = [slug for _, v in variants for slug in [v["slug"]] if slug not in results]
    print(json.dumps({"variants": len(results), "expected": len(variants), "missing": missing}))


if __name__ == "__main__":
    main()
