"""Build the offline report from immutable evidence and readable UI sources."""

from pathlib import Path
import csv
import hashlib
import json
import math
import re
import argparse
from scripts.report_claims import render_claims
from scripts.market_snapshot import merge_aa_v5, refresh_panorama

ROOT = Path(__file__).resolve().parent
RESEARCH = ROOT / "research" / "2026-10-15"
ORIGINAL = ROOT / "archive" / "model-capability-cost-2026-10-14.html"
NUMERIC_METRICS = {
    "Intelligence Index", "AA-Briefcase v1.1", "GDPval-AA v2.1", "AutomationBench-AA",
    "Terminal-Bench 4.0", "SciCode", "Humanity's Last Exam", "GDP.pdf", "CritPt",
    "AA-Omniscience", "AA-LCR v1.1", "Cost per Task", "Cost to Run Intelligence Index",
    "Output Speed", "Time to First Token", "Time to First Answer Token",
    "End-to-End Response Time", "Time per Task",
}


def read_json(path):
    return json.loads(path.read_text())


def number(value):
    match = re.search(r"-?\d[\d,]*(?:\.\d+)?", value)
    return float(match[0].replace(",", "")) if match else None



def bind_panorama_capabilities(multi):
    """Derive panorama prose/CSV from the same official representative as the chart."""
    cap = multi["aa_capability_indexes"]
    for row in multi["external_leaderboards"]["four_family_matrix"]:
        variants = [e for e in cap["entries"] if e["releaseSlug"] == row["aa_cap_release_slug"]]
        representatives = [e for e in variants if e["isTopVariant"]]
        if len(representatives) != 1:
            raise ValueError("Panorama requires one official II representative per release")
        entry = representatives[0]
        if entry["intelligenceIndex"] != max(v["intelligenceIndex"] for v in variants):
            raise ValueError("Panorama representative must have the highest overall II")
        scores = []
        for domain in cap["domains"]:
            value = entry["capabilities"].get(domain["key"])
            observed = isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
            scores.append(domain["shortLabel"] + " " + (f"{value:.2f}" if observed else "无数据（不参排）"))
        configuration = entry["effort"] + (" · " + entry["fallbackLabel"] if entry.get("fallbackLabel") else "")
        row["aa_cap_highlights"] = configuration + " · " + " · ".join(scores)
        row["aa_cap_variant_slug"] = entry["slug"]
        row["aa_cap_source_url"] = entry["sourceUrl"]


def check_model_profiles(doc, catalog, multi):
    """The profile tab joins catalog, AA releases and guidance by id; every link must resolve."""
    catalog_ids = {m["id"] for m in catalog["models"]}
    releases = {r["releaseSlug"] for r in multi["aa_release_series"]["releases"]}
    guidance = {m["modelId"] for m in read_json(ROOT / "research/2026-10-20/task-effort-guidance.json")["models"]}
    profile_ids = [m["id"] for m in doc["models"]]
    if len(set(profile_ids)) != len(profile_ids) or not set(profile_ids) <= catalog_ids:
        raise ValueError("Profile models must be unique catalog ids")
    tasks = {t["id"] for t in doc["taskAxis"]}
    for m in doc["models"]:
        if m["aaRelease"] and m["aaRelease"] not in releases:
            raise ValueError(f"Unknown AA release {m['aaRelease']}")
        if not m.get("line"):
            raise ValueError(f"Profile model {m['id']} needs a product line")
        if m["guidanceId"] and m["guidanceId"] not in guidance:
            raise ValueError(f"Unknown guidance id {m['guidanceId']}")
    for ev in doc["evidence"]:
        if not set(ev["modelIds"]) <= set(profile_ids) or not set(ev["tasks"]) <= tasks | {"all"}:
            raise ValueError(f"Evidence {ev['id']} points at unknown model or task")
        if not ev.get("url", "").startswith("https://") or not ev.get("checkedAt"):
            raise ValueError(f"Evidence {ev['id']} needs a source URL and check date")


def check_community(doc, profiles_doc):
    """Community voices are text-only; each needs known models/tasks and at least one https source."""
    ids = {m["id"] for m in profiles_doc["models"]}
    tasks = {t["id"] for t in profiles_doc["taskAxis"]} | {"all"}
    for item in doc["items"]:
        if not set(item["modelIds"]) <= ids or not set(item["tasks"]) <= tasks:
            raise ValueError(f"Community item {item['id']} points at unknown model or task")
        if not item["sources"] or not all(s["url"].startswith("https://") for s in item["sources"]):
            raise ValueError(f"Community item {item['id']} needs https sources")
    for sc in doc.get("maxEffortScenarios", []):
        if not sc["sources"] or not all(s["url"].startswith("https://") for s in sc["sources"]):
            raise ValueError(f"Scenario {sc['id']} needs https sources")
        if sc.get("measure") not in (None, "overthink", "regress", "ttfa"):
            raise ValueError(f"Scenario {sc['id']} has an unknown measure")
    tiers = ["low", "medium", "high", "xhigh", "max"]
    for ph in doc.get("workPhases", []):
        if ph["tier"] not in tiers or not all(t in tiers for t in ph["range"]) or not ph["sources"]:
            raise ValueError(f"Work phase {ph['id']} needs a valid tier, range and sources")


def build(output_dir=ROOT):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    original = ORIGINAL.read_text()
    base = json.loads(re.search(r'<script id="dataset" type="application/json">(.*?)</script>', original, re.S)[1])
    methods = json.loads(re.search(r'<script id="method-data" type="application/json">(.*?)</script>', original, re.S)[1])
    if isinstance(methods.get("general"), str):
        methods["general"] = methods["general"].replace(" or GEO outcomes", "")
    rows = base["rows"]
    catalog = read_json(ROOT / "report-content.json")
    model_names = [m["name"] for m in catalog["models"]]
    profiles = []
    for path in sorted(RESEARCH.glob("aa-pair-*.json")):
        evidence = read_json(path)
        table = evidence["tables"][0]
        for column in (1, 2):
            header = table[0][column]
            canonical_header = header.replace("GPT-", "GPT ")
            name = next(m for m in model_names if m in canonical_header)
            effort = "max" if "(Max" in header else "high" if "(High" in header else "unspecified"
            metrics = {row[0]: row[column] for row in table[1:] if len(row) > column}
            profile = {
                "model": name, "effort": effort, "source_label": header,
                "snapshot": "2026-10-15", "version": "4.3.2", "source_url": evidence["url"],
                "metrics": {key: number(value) for key, value in metrics.items() if key in NUMERIC_METRICS},
                "raw_metrics": metrics,
                "fallback": "Default Fallback" in header,
            }
            profiles.append(profile)
            existing = next((r for r in rows if r["benchmark"] == "general" and r["model"] == name and r["effort"] == effort), None)
            if existing:
                assert existing["score"] == profile["metrics"]["Intelligence Index"]
                assert existing["cost_usd"] == profile["metrics"]["Cost to Run Intelligence Index"]
            else:
                explicit = effort != "unspecified"
                rows.append({
                    "benchmark": "general", "model": name, "effort": effort,
                    "version": "4.3.2", "snapshot": "2026-10-15",
                    "score": profile["metrics"]["Intelligence Index"],
                    "cost_usd": profile["metrics"]["Cost to Run Intelligence Index"],
                    "weighted_cost_per_task_usd": profile["metrics"]["Cost per Task"],
                    "score_name": "AA Intelligence Index", "n": None,
                    "source_url": evidence["url"],
                    "cost_basis": "AA 整套指数估算 USD，不含重复测试；加权单任务费用为独立字段。",
                    "fallback": "Default Fallback（比例未披露）" if profile["fallback"] else "页面未标回退",
                    "notes": "同版 v4.3.2，10 月 15 日补充。公开取整值，不证明统计显著优胜。" + ("来源没有明确 effort，按未注明配置保留。" if not explicit else ""),
                    "variant": "standard_effort" if explicit else "unspecified",
                    "frontier_eligible": explicit, "connect": explicit, "plot": True,
                })

    tone_path = RESEARCH / "tonebench-leaderboard.json"
    tone = read_json(tone_path)
    tone_hash = hashlib.sha256(tone_path.read_bytes()).hexdigest()
    original_tone = read_json(ROOT / "九模型图表数据与来源" / "tonebench.json")
    assert tone_hash == original_tone["source_sha256"]
    additions = {
        "claude-fable-5-1": "Claude Fable 5.1",
        "gemini-4-argon": "Gemini 4 Argon",
        "gemini-3.8-flash": "Gemini 3.8 Flash",
        "gemini-3.5-flash-lite": "Gemini 3.5 Flash-Lite",
    }
    for source in tone["models"]:
        provenance = source["provenance"]
        if provenance["model_id"] not in additions:
            continue
        explicit = bool(provenance["reasoning_effort"])
        reported = provenance["reasoning_effort"] or provenance["thinking"]
        mismatch = reported == "no thinking"
        effort = reported.replace(" thinking", "") if not mismatch else "unverified"
        row = {
            "benchmark": "writing", "model": additions[provenance["model_id"]],
            "model_id": provenance["model_id"], "display": source["display"],
            "effort": effort, "source_effort_label": reported, "effort_explicit": explicit,
            "variant": "unverified" if mismatch else "standard_effort" if explicit else "provider_default",
            "score": source["overall"], "cost_usd": source["cost_usd"],
            "time_s": source["avg_latency_s"], "overall_std": source["overall_std"],
            "n": len(source["tasks"]) * source["n_runs"], "tasks_n": len(source["tasks"]),
            "drafts_per_task": source["n_runs"], "snapshot": tone["generated_at"],
            "version": tone["provenance"]["judge_rev"] + " / " + tone["provenance"]["generation_rev"],
            "score_name": "Writing Score (0–100)",
            "source_url": "https://benchmark.towardsai.com/data/leaderboard.json",
            "scorecard_url": "https://benchmark.towardsai.com/models/" + source["slug"] + ".html",
            "provider_route": provenance["provider"], "generation_first_run": provenance["first_run"],
            "generation_last_run": provenance["last_run"], "time_includes_retries": True,
            "cost_includes_all_retries": None,
            "cost_basis": "含思考输出与固定 prompt 的每篇 API 等价费用；完整失败重试费用覆盖未确认。",
            "notes": "10 个英文 AI 教育脚本 brief × 5 稿，不能外推为中文写作排名。" +
                     ("来源标为 no thinking，但官方仅支持 low/medium/high；实际请求设置待核验。" if mismatch else ""),
            "connect": explicit, "frontier_eligible": explicit, "plot": True,
        }
        assert row["n"] == 50
        rows.append(row)

    arena = read_json(RESEARCH / "arena-web-extract.json")
    for source_line in arena["rows"]:
        cells = [cell.strip() for cell in source_line.split("|")]
        name = next(m for m in model_names if m in cells[1])
        effort = re.search(r"\((Max|High|xHigh)\)", cells[1])[1].lower()
        score, interval = (number(v) for v in cells[2].split("±"))
        rows.append({
            "benchmark": "arena", "model": name, "effort": effort,
            "score": score, "ci95_halfwidth": interval, "cost_usd": number(cells[9]),
            "n": int(cells[8].replace(",", "")), "snapshot": "2026-10-14",
            "version": "Agent Arena Code / signals 2026-10-12", "source_url": arena["source"],
            "score_name": "Net Improvement（相对随机基线，百分点）",
            "cost_basis": "Arena 平台报告 Cost/Task P50；部分标价与官方 Standard 不一致，不代表同价重跑。",
            "notes": "随机路由的真实用户会话，95% CI；相对基线变化不是绝对通过率。任务、人群和工具链与其他基准不同。",
            "variant": "platform_harness", "frontier_eligible": True, "connect": False, "plot": True,
            "signals_source_display": dict(zip(["confirmed_success", "praise_complaint", "steerability", "bash_reliability", "tool_hallucination"], cells[3:8])),
        })

    claude = read_json(RESEARCH.parent / "2026-10-16" / "claude-catalog" / "claude-supplement.json")
    assert claude["tonebench_sha256"] == tone_hash
    rows.extend(claude["rows"])
    profiles.extend(claude["aa_profiles"])

    multi = read_json(RESEARCH.parent / "2026-10-19" / "multi-benchmark-supplement.json")
    assert multi["tonebench_sha256"] == tone_hash
    bind_panorama_capabilities(multi)
    rows.extend(multi["grok_rows"])
    profiles.append(multi["grok_aa_profile"])

    effort_evals = read_json(RESEARCH.parent / "2026-10-20" / "aa-effort-evals.json")
    eval_variants = effort_evals["variants"]
    for rel in multi["aa_release_series"]["releases"]:
        for var in rel["variants"]:
            ev = eval_variants.get(var["slug"])
            if ev:
                m = ev["metrics"]
                var["evalMetrics"] = m
                var["evalSourceUrl"] = ev["source_url"]
                var["taskScores"] = {
                    "complex": round(0.5 * m["Humanity's Last Exam"] + 0.5 * m["CritPt"], 2),
                    "coding": round(0.5 * m["Terminal-Bench 4.0"] + 0.5 * m["SciCode"], 2),
                    "planning": m["AA-Briefcase v1.1"],
                    "agentic": m["GDPval-AA v2.1"],
                    "automation": m["AutomationBench-AA"],
                    "knowledge": round((m["AA-LCR v1.1"] + 2.0 * m["GDP.pdf"] + 3.0 * m["AA-Omniscience"]) / 6.0, 2),
                }

    profiles_doc = read_json(ROOT / "research/2026-10-24/model-effort-profiles.json")
    check_model_profiles(profiles_doc, catalog, multi)
    community_doc = read_json(ROOT / "research/2026-10-25/community-consensus.json")
    check_community(community_doc, profiles_doc)
    market = read_json(ROOT / "research/2026-10-23/market-snapshot.json")
    refresh_panorama(multi["external_leaderboards"], market)
    # v5 is a separate, newer board; the panorama keeps its v4.3.2 references.
    market = merge_aa_v5(market, read_json(ROOT / "research/2026-10-28/aa-index-v5.json"))
    for index, row in enumerate(rows):
        row["id"] = index
    data = {
        **catalog, "rows": rows, "aa_profiles": profiles, "raw_methods": methods,
        "opus_coding_evidence": read_json(RESEARCH.parent / "2026-10-16" / "opus55-coding-supplement.json"),
        "computer_use_evidence": read_json(ROOT / "research/2026-10-20/computer-use-evidence.json"),
        "task_effort_guidance": read_json(ROOT / "research/2026-10-20/task-effort-guidance.json"),
        "practical_evidence": read_json(ROOT / "research/2026-10-20/practical-evidence.json"),
        "model_effort_profiles": profiles_doc,
        "community_consensus": community_doc,
        "aa_capability_indexes": multi["aa_capability_indexes"],
        "aa_release_series": multi["aa_release_series"],
        "aa_effort_evals": {
            "fetched_at": effort_evals["fetched_at"],
            "source": effort_evals["source"],
            "evals": effort_evals["evals"],
            "variants": eval_variants,
        },
        "external_leaderboards": multi["external_leaderboards"],
        "market_snapshot": market,
        "meta": {"reviewed_at": market["reviewed_at"], "original_rows": 121,
                 "tonebench_sha256": tone_hash, "tonebench_fingerprint": tone["provenance"],
                 "not_run": "未做新的模型调用或中文任务实验；使用公开基准与官方证据。"},
    }
    (output_dir / "report-data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with (output_dir / "report-data.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value for key, value in row.items()})
    html = (ROOT / "report.template.html").read_text()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = html.replace("/* REPORT_CSS */", (ROOT / "report.css").read_text())
    html = html.replace("/* REPORT_JS */", (ROOT / "report.js").read_text())
    html = render_claims(html, data)
    html = html.replace("REPORT_DATA_JSON", payload)
    (output_dir / "model-capability-cost.html").write_text(html, encoding="utf-8")
    print(json.dumps({"rows": len(rows), "original_rows": 121, "aa_profiles": len(profiles),
                      "models": len(model_names), "groups": {g: sum(r["benchmark"] == g for r in rows) for g in ["general", "coding", "writing", "arena"]},
                      "html_bytes": len(html.encode())}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    build(parser.parse_args().output_dir)
