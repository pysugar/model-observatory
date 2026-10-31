"""Fetch Intelligence Index v5 per-effort data for the releases the report tracks.

Each AA release page embeds one record per effort configuration: the v5 score, the six
domain (capability) indexes, cost / token / time per task and every evaluation score.
This writes aa-v5-series.json in the same shape as the 2026-10-19 v4.3.2 snapshot
(`aa_release_series`, `aa_capability_indexes`) plus the per-effort v5 evaluations
(`aa_effort_evals`). Configurations AA has not scored on v5 are listed under
`unmeasured`, never filled from v4.3.2. No raw HTML is committed: pages are recorded by
URL and SHA-256.

Run from the repository root: python3 research/2026-10-28/fetch_aa_v5_releases.py
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import hashlib
import json
import re
import sys
import time
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V4 = ROOT / "research/2026-10-19/multi-benchmark-supplement.json"
OUT = HERE / "aa-v5-series.json"
BASE = "https://artificialanalysis.ai/zh/models/releases/"
# Releases with per-effort evaluations (the four families' current models), as in 2026-10-20.
EVAL_RELEASES = [
    "grok-4-7", "gpt-6-1-sol", "gpt-6-astra", "gpt-6-luna",
    "gemini-4-argon", "gemini-3-8-flash", "gemini-3-5-flash-lite",
    "claude-opus-5-5", "claude-sonnet-5-5", "claude-fable-5-1", "claude-haiku-5-5",
]
EFFORT_ORDER = {"non-reasoning": 0, "low": 2, "medium": 3, "unspecified": 3, "high": 4, "xhigh": 5, "max": 6}
# v5 evaluation name -> (evaluationScores key, scale to percent)
EVALS = {
    "Intelligence Index": ("intelligenceIndex", 1),
    "AA-Briefcase v1.1": ("briefcaseElo", 1),
    "AutomationBench-AA": ("automationBenchPartialScore", 100),
    "GDP.pdf": ("gdpPdfAllPass", 100),
    "FrontierCode 2.0": ("frontierCode20", 100),
    "Terminal-Bench 4.0": ("terminalBench40", 100),
    "Terminal-Bench-Science": ("terminalBenchScience", 100),
    "CritPt v2 hard": ("critptAgenticHard", 100),
    "AA-Omniscience v1.1": ("omniscience", 1),
    "HLE-Diamond": ("hleDiamond", 100),
}


# Capability index components and weights under v5, from
# https://artificialanalysis.ai/methodology/capability-indices (read 2026-10-28).
DOMAINS_V5 = {
    "financeAndAccounting": (["AA-Briefcase v1.1", "AA-Omniscience v1.1（商业知识 / 非幻觉）", "HLE-Diamond", "AutomationBench-AA", "GDP.pdf"],
                             "代理知识工作30% · 知识25% · 推理15% · 非幻觉15% · 工具10% · 长上下文5%"),
    "strategyAndOps": (["AutomationBench-AA", "AA-Briefcase v1.1", "AA-Omniscience v1.1（商业知识 / 非幻觉）", "GDP.pdf"],
                       "工具35% · 代理知识工作30% · 知识25% · 长上下文5% · 非幻觉5%"),
    "legal": (["AA-Omniscience v1.1（法律知识 / 非幻觉）", "AA-Briefcase v1.1", "HLE-Diamond", "GDP.pdf", "AutomationBench-AA"],
              "知识30% · 代理知识工作25% · 推理15% · 非幻觉15% · 长上下文10% · 工具5%"),
    "healthcareAndMedical": (["AA-Omniscience v1.1（医疗知识 / 非幻觉）", "AA-Briefcase v1.1", "MLCR-AA", "AutomationBench-AA", "HLE-Diamond"],
                             "知识25% · 代理知识工作25% · 长上下文15% · 工具15% · 非幻觉10% · 推理10%"),
    "engineering": (["AA-Omniscience v1.1（工程知识）", "CritPt v2 hard / Terminal-Bench-Science", "HLE-Diamond", "Terminal-Bench 4.0 / FrontierCode 2.0", "AA-Briefcase v1.1"],
                    "知识30% · 科学20% · 推理20% · 代理编程15% · 代理知识工作15%"),
    "economics": (["AA-Briefcase v1.1", "AA-Omniscience v1.1（经济学知识）", "HLE-Diamond", "GDP.pdf"],
                  "代理知识工作35% · 知识30% · 推理25% · 长上下文10%"),
}


def fetch(url):
    request = Request(url, headers={"User-Agent": "model-observatory-research/1.0 (+https://github.com/pysugar/model-observatory)"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def flight_data(html):
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, flags=re.S)
    return "".join(json.loads('"' + chunk + '"') for chunk in chunks)


def records(data):
    """Every embedded model record (the objects that carry capabilityScores), first copy wins."""
    found = {}
    for match in re.finditer(r'"capabilityScores"', data):
        depth = 0
        for start in range(match.start(), 0, -1):
            char = data[start]
            if char == "}":
                depth += 1
            elif char == "{":
                if depth == 0:
                    break
                depth -= 1
        record = json.JSONDecoder().raw_decode(data[start:])[0]
        if record.get("slug") and record.get("release"):
            found.setdefault(record["slug"], record)
    return list(found.values())


def effort_of(name):
    match = re.search(r"\(([^)]*)\)$", name)
    if not match:
        return "unspecified"
    first = match[1].split(",")[0].strip().lower()
    return first if first in EFFORT_ORDER else "unspecified"


def r(value, digits):
    return None if value is None else round(value, digits)


def variant(record, known_efforts):
    cost = (record.get("intelligenceIndexCostPerTask") or {}).get("cost") or {}
    tokens = record.get("intelligenceIndexOutputTokensPerTask") or {}
    seconds = record.get("intelligenceIndexTimePerTask")
    ttfa = (record.get("timeToFirstAnswerToken") or {}).get("total")
    effort = effort_of(record["name"])
    if effort == "unspecified":
        # Same configuration identity as the v4.3.2 snapshot (e.g. Gemini 3.5 Flash-Lite is high).
        effort = known_efforts.get(record["slug"], effort)
    fallback = "Default Fallback" if "Fallback" in record["name"] else None
    return {
        "slug": record["slug"], "name": record["name"], "shortName": record.get("shortName"),
        "effort": effort, "effortOrder": EFFORT_ORDER[effort],
        "intelligenceIndex": r(record["intelligenceIndex"], 2),
        # AA displays whole numbers rounded half up (34.5 → 35).
        "intelligenceIndexRounded": int(Decimal(str(round(record["intelligenceIndex"], 4))).quantize(Decimal("1"), ROUND_HALF_UP)),
        "costPerTask": r(cost.get("total"), 4),
        "costBreakdown": {k: r(cost.get(k), 4) for k in
                          ("total", "input", "nonCacheInput", "cacheRead", "cacheWrite", "output", "reasoning", "answer")},
        "costTotalRun": None,
        "timePerTaskSeconds": r(seconds, 1),
        "timePerTaskMinutes": r(seconds / 60, 2) if seconds else None,
        "outputTokensPerTask": round(tokens["output"]) if tokens.get("output") else None,
        "outputTokensBreakdown": {k: round(tokens[k]) if tokens.get(k) else None for k in ("output", "reasoning", "answer")},
        "outputSpeed": r(record.get("medianOutputSpeed"), 1),
        "ttfaSeconds": r(ttfa, 2),
        "capabilities": {k: r(v, 2) for k, v in (record.get("capabilityScores") or {}).items() if v is not None},
        "hasFallback": bool(fallback), "fallbackLabel": fallback,
    }


def eval_metrics(record):
    scores = record.get("evaluationScores") or {}
    return {name: (None if scores.get(key) is None else round(scores[key] * scale, 2))
            for name, (key, scale) in EVALS.items()}


def main(release_metadata=None, request_delay=1.0):
    v4 = json.loads(V4.read_text())
    v4_releases = release_metadata if release_metadata is not None else v4["aa_release_series"]["releases"]
    known_efforts = {v["slug"]: v["effort"] for r in v4_releases for v in r["variants"]}
    pages, releases, entries, evals, unmeasured = [], [], [], {}, []
    # Single-configuration releases have no working release page; every page also embeds
    # full records for the models it compares against, so pool records across pages.
    pool = {}
    for meta in v4_releases:
        url = BASE + meta["releaseSlug"]
        print("Fetch " + meta["releaseSlug"], file=sys.stderr, flush=True)
        body = fetch(url)
        page = {"url": url, "sha256": hashlib.sha256(body).hexdigest()}
        found = records(flight_data(body.decode("utf-8", "replace")))
        if not found:
            page["note"] = "no embedded records (AA error page for single-configuration releases)"
        pages.append(page)
        for x in found:
            pool.setdefault(x["slug"], x)
        time.sleep(request_delay)
    for meta in v4_releases:
        slug = meta["releaseSlug"]
        url = BASE + slug
        found = [x for x in pool.values() if x["release"]["slug"] == slug]
        scored = [x for x in found if x.get("intelligenceIndex") is not None]
        missing = sorted(x["slug"] for x in found if x.get("intelligenceIndex") is None)
        expected = sorted(v["slug"] for v in meta["variants"])
        absent = sorted(set(expected) - {x["slug"] for x in found})
        if missing or absent:
            unmeasured.append({"releaseSlug": slug, "name": meta["name"], "variants": sorted(set(missing) | set(absent))})
        print(("OK " if scored else "-- ") + slug, len(scored), "/", len(found), file=sys.stderr)
        if not scored:
            continue
        variants = sorted((variant(x, known_efforts) for x in scored), key=lambda v: (v["effortOrder"], v["slug"]))
        top = max(variants, key=lambda v: v["intelligenceIndex"])
        for v in variants:
            v["isTopVariant"] = v is top
        costs = [v["costPerTask"] for v in variants if v["costPerTask"] is not None]
        release = {k: meta[k] for k in ("releaseSlug", "name", "aaReleaseName", "shortName", "vendor",
                                        "color", "isFourFamily", "isCurrent", "releaseDate", "contextWindowTokens")}
        release.update({
            "modelCount": len(variants),
            "maxIntelligenceIndex": top["intelligenceIndex"],
            "minCostPerTask": min(costs) if costs else None,
            "maxCostPerTask": max(costs) if costs else None,
            "strengthsGlobalRank": {},
            "sourceUrl": url,
            "variants": variants,
        })
        releases.append(release)
        for v in variants:
            if not v["capabilities"]:
                continue
            entries.append({
                "slug": v["slug"], "releaseSlug": slug, "releaseName": meta["name"],
                "releaseShort": meta["shortName"], "name": f'{meta["name"]} ({v["effort"]})',
                "shortLabel": meta["shortName"] if v["isTopVariant"] else f'{meta["shortName"]} ({v["effort"]})',
                "variantLabel": f'{meta["shortName"]} · {v["effort"]}', "vendor": meta["vendor"],
                "color": meta["color"], "effort": v["effort"], "isTopVariant": v["isTopVariant"],
                "isFourFamily": meta["isFourFamily"], "isCurrent": meta["isCurrent"],
                "hasFallback": v["hasFallback"], "fallbackLabel": v["fallbackLabel"],
                "intelligenceIndex": v["intelligenceIndex"], "costPerTask": v["costPerTask"],
                "timePerTaskMinutes": v["timePerTaskMinutes"], "outputTokensPerTask": v["outputTokensPerTask"],
                "capabilities": v["capabilities"], "strengthsGlobalRank": {}, "sourceUrl": url,
            })
        if slug in EVAL_RELEASES:
            for x in scored:
                v = next(v for v in variants if v["slug"] == x["slug"])
                evals[x["slug"]] = {
                    "slug": x["slug"], "releaseSlug": slug, "model": meta["name"], "vendor": meta["vendor"],
                    "effort": v["effort"], "effortOrder": v["effortOrder"], "source_url": url,
                    "metrics": eval_metrics(x),
                }
    domains = [{**d, "coreEvals": DOMAINS_V5[d["key"]][0], "weightNote": DOMAINS_V5[d["key"]][1]}
               for d in v4["aa_capability_indexes"]["domains"]]
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    OUT.write_text(json.dumps({
        "fetched_at": stamp, "version": "v5.0",
        "source": "Artificial Analysis public release pages (Intelligence Index v5.0)",
        "pages": pages, "unmeasured": unmeasured,
        "aa_release_series": {"snapshot": stamp[:10], "version": "v5.0",
                              "source_url": "https://artificialanalysis.ai/zh/models/releases", "releases": releases},
        "aa_capability_indexes": {"snapshot": stamp[:10], "version": "v5.0",
                                  "source_url": "https://artificialanalysis.ai/zh/indexes",
                                  "domains": domains, "entries": entries},
        "aa_effort_evals": {"fetched_at": stamp, "source": "Artificial Analysis release pages (Intelligence Index v5.0)",
                            "evals": list(EVALS), "variants": evals},
    }, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"releases": len(releases), "variants": sum(len(x["variants"]) for x in releases),
                      "capability_entries": len(entries), "eval_variants": len(evals),
                      "unmeasured_releases": [u["releaseSlug"] for u in unmeasured]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
