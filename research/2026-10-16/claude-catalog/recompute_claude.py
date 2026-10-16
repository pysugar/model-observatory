"""Recompute the added Claude rows from frozen official and benchmark evidence."""

from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build_report import NUMERIC_METRICS


def read(path):
    return json.loads(path.read_text())


def number(value):
    match = re.search(r"-?\d[\d,]*(?:\.\d+)?", value.replace("−", "-"))
    return float(match[0].replace(",", "")) if match else None


def main():
    catalog = read(ROOT / "report-content.json")
    models = [m for m in catalog["models"] if m.get("added_in") == "claude-catalog-2026-10-16"]
    names = sorted((m["name"] for m in models), key=len, reverse=True)
    profiles, rows = [], []
    manifest = read(HERE / "aa-manifest.json")
    for entry in manifest:
        path = HERE / entry["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
        source = read(path)
        assert source["version"] == "4.3.2"
        table = source["tables"][0]
        for column in (1, 2):
            header = table[0][column]
            canonical = header.replace("Claude 4.5 Haiku", "Claude Haiku 4.5").replace("Claude 4.5 Sonnet", "Claude Sonnet 4.5")
            name = next(name for name in names if name + " (" in canonical)
            raw = {r[0]: r[column] for r in table[1:] if len(r) > column}
            metrics = {k: number(v) for k, v in raw.items() if k in NUMERIC_METRICS}
            effort = "max" if "(Max" in header else "unspecified"
            estimated = "*" in raw["Intelligence Index"]
            fallback = "Fallback" in header
            variant = "mixed_fallback" if fallback else "estimated" if estimated else "unspecified" if effort == "unspecified" else "standard_effort"
            profile = dict(model=name, effort=effort, source_label=header, snapshot="2026-10-16", version=source["version"],
                source_url=source["url"], metrics=metrics, raw_metrics=raw, fallback=fallback, score_estimated=estimated,
                configuration_note="extended thinking；预算 / effort 未披露" if effort == "unspecified" else "Opus 4.8 回退" if fallback else "")
            profiles.append(profile)
            rows.append(dict(benchmark="general",model=name,effort=effort,source_effort_label=profile["configuration_note"],
                version=source["version"],snapshot=source["snapshot"],score=metrics["Intelligence Index"],score_estimated=estimated,
                cost_usd=metrics.get("Cost to Run Intelligence Index"),weighted_cost_per_task_usd=metrics.get("Cost per Task"),
                score_name="AA Intelligence Index",n=None,source_url=source["url"],source_label=header,
                cost_basis="AA 整套指数估算 USD，不含重复测试；加权单任务费用为独立字段。",
                fallback="Opus 4.8 Fallback（比例未披露）" if fallback else "页面未标回退",
                notes="同版 v4.3.2，10 月 16 日读取；已取整，缺测留空。" + ("综合分为来源估计值，不能当作完整独立实测。" if estimated else "") + ("thinking 配置不能等同新版 effort。" if effort == "unspecified" else ""),
                variant=variant,frontier_eligible=variant=="standard_effort",connect=False,plot=True))
    assert len(profiles) == 10

    tone_path = ROOT / "research/2026-10-15/tonebench-leaderboard.json"
    tone = read(tone_path)
    tone_hash = hashlib.sha256(tone_path.read_bytes()).hexdigest()
    assert tone_hash == read(ROOT / "九模型图表数据与来源/tonebench.json")["source_sha256"]
    tone_names = {m["tone_id"]: m["name"] for m in models}
    for source in tone["models"]:
        provenance = source["provenance"]
        if provenance["model_id"] not in tone_names:
            continue
        explicit = bool(provenance["reasoning_effort"])
        reported = provenance["reasoning_effort"] or provenance["thinking"]
        fallback = "fallback" in source["display"].lower()
        variant = "mixed_fallback" if fallback else "standard_effort" if explicit else "provider_default"
        rows.append(dict(benchmark="writing",model=tone_names[provenance["model_id"]],model_id=provenance["model_id"],display=source["display"],
            effort=reported if explicit else "unspecified",source_effort_label=reported,effort_explicit=explicit,variant=variant,
            score=source["overall"],cost_usd=source["cost_usd"],time_s=source["avg_latency_s"],overall_std=source["overall_std"],
            n=len(source["tasks"])*source["n_runs"],tasks_n=len(source["tasks"]),drafts_per_task=source["n_runs"],
            snapshot=tone["generated_at"],version=tone["provenance"]["judge_rev"]+" / "+tone["provenance"]["generation_rev"],
            score_name="Writing Score (0–100)",source_url="https://benchmark.towardsai.com/data/leaderboard.json",
            scorecard_url="https://benchmark.towardsai.com/models/"+source["slug"]+".html",provider_route=provenance["provider"],
            generation_first_run=provenance["first_run"],generation_last_run=provenance["last_run"],time_includes_retries=True,cost_includes_all_retries=None,
            cost_basis="含思考输出与固定 prompt 的每篇 API 等价费用；完整失败重试费用覆盖未确认。",
            notes="10 个英文 AI 教育脚本 brief × 5 稿，不能外推为中文写作排名。"+("含 Opus 4.8 回退；比例未披露，不视为纯 Fable 5。" if fallback else ""),
            fallback="Opus 4.8；比例未披露" if fallback else None,
            connect=False,frontier_eligible=variant=="standard_effort",plot=True))
    assert len(rows) == 22
    assert all(r["n"] == 50 for r in rows if r["benchmark"] == "writing")
    result=dict(reviewed_at="2026-10-16",aa_profiles=profiles,rows=rows,tonebench_sha256=tone_hash,
        method="追加 10 个 AA 同版代表配置与同快照 12 个 ToneBench 配置；不混入旧版 Vulcan。估计值、回退、默认 thinking 与缺费分别保留。")
    (HERE / "claude-supplement.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"aa_profiles":len(profiles),"rows":len(rows),"estimated":[p["model"] for p in profiles if p["score_estimated"]]},ensure_ascii=False))


if __name__ == "__main__":
    main()
