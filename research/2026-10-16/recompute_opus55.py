"""Recompute the scoped Opus evidence from saved public sources, without network calls."""

from pathlib import Path
from statistics import mean, stdev
import csv
import json
import math
import re

ROOT = Path(__file__).resolve().parent
EFFORTS = ["low", "medium", "high", "xhigh", "max"]
FRONTIER = "https://vulcanbench.com/benchmarks/swe-v4-opus55-v315.html"
RUNS = "https://vulcanbench.com/assets/data/swe-v4-opus55-v315/runs.csv"
ROUTINE = "https://vulcanbench.com/leaderboard.html#routine-v1-board"
OFFICIAL = "https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence"


def read_csv(name):
    with (ROOT / name).open(newline="") as source:
        return list(csv.DictReader(source))


def effort(value):
    return value.replace("extra-high", "xhigh").split()[0]


def aggregate(rows):
    judged = [float(r["combined_33"]) for r in rows if r["combined_33"]]
    return {
        "n": len(rows),
        "passed": sum(float(r["functional_pct"]) == 100 for r in rows),
        "combined": mean(judged),
        "combined_se": stdev(judged) / math.sqrt(len(judged)),
        "judged_n": len(judged),
        "cost_usd": mean(float(r["estimated_usd"]) for r in rows),
        "time_s": mean(float(r["duration_s"]) for r in rows),
        "fallback_runs": sum(r["solver_fallback"] == "True" for r in rows),
        "fallback_reply_pct": 100 * sum(int(r["opus48_replies"]) for r in rows) / sum(int(r["all_replies"]) for r in rows),
    }


def dollar(value):
    return f"${value:.4f}" if value < 1 else f"${value:.2f}"


def build():
    runs = read_csv("frontier-runs.csv")
    assert len(runs) == 115
    assert len({(r["effort"], r["task"]) for r in runs}) == 115
    assert all(r["model"] == "opus55" for r in runs)
    assert all((r["solver_fallback"] == "True") == (int(r["opus48_replies"]) > 0) for r in runs)
    groups = {e: [r for r in runs if effort(r["effort"]) == e] for e in EFFORTS}
    assert all(len(rs) == 23 for rs in groups.values())
    task_sets = [{r["task"] for r in rs} for rs in groups.values()]
    assert all(tasks == task_sets[0] for tasks in task_sets)
    all_rows = [{"effort": e, **aggregate(rs)} for e, rs in groups.items()]

    # Check the new download against the report's existing immutable observations.
    report = json.loads((ROOT.parents[1] / "report-data.json").read_text())
    existing = {r["effort"]: r for r in report["rows"] if r["benchmark"] == "coding" and r["model"] == "Claude Opus 5.5"}
    for row in all_rows:
        old = existing[row["effort"]]
        assert row["passed"] == old["passes"]
        assert row["fallback_runs"] == old["solver_fallback_runs"]
        assert math.isclose(row["cost_usd"], old["cost_usd"], abs_tol=1e-10)
        assert math.isclose(row["time_s"] / 60, old["minutes_per_task_all_runs"], abs_tol=1e-10)
        assert math.isclose(row["combined"], old["combined_score_judged"], abs_tol=1e-4)

    clean_sets = [{r["task"] for r in rs if r["solver_fallback"] == "False"} for rs in groups.values()]
    common_tasks = set.intersection(*clean_sets)
    assert len(common_tasks) == 6
    common_rows = [{"effort": e, **aggregate([r for r in rs if r["task"] in common_tasks])} for e, rs in groups.items()]
    assert all(r["fallback_runs"] == 0 and r["n"] == 6 for r in common_rows)

    routine_rows = [{
        "effort": effort(r["effort"]), "n": int(r["n"]), "passed": int(r["passed"]),
        "combined": float(r["combined_33"]), "combined_se": float(r["combined_33_se"]),
        "cost_usd": float(r["mean_usd"]), "time_s": float(r["mean_seconds"]),
        "solver_fallback": None, "protocol": r["protocol"],
    } for r in read_csv("routine-v1-board.csv") if r["model"] == "Opus 5.5"]
    assert [r["effort"] for r in routine_rows] == EFFORTS
    assert all(r["n"] == r["passed"] == 12 for r in routine_rows)

    table = json.loads((ROOT / "claude-effort-table.json").read_text())["table"]
    official_rows = [{
        "effort": effort(r[2]), "score_pct": float(re.search(r"[\d.]+", r[3])[0]),
        "cost_usd": float(re.search(r"[\d.]+", r[4])[0]), "n_tasks": 478,
        "repeats": 1 if "single run" in r[3] else 2, "time_s": None,
        "run_dates": "2026-09-19/20", "per_turn_token_cap": 16384,
    } for r in table[1:] if r[1] == "Claude Opus 5.5" and r[0].startswith("SWE-bench Pro")]
    assert [r["effort"] for r in official_rows] == EFFORTS[:4]

    views = [
        {
            "id": "frontier-observed", "title": "Frontier v4 · 完整配置（含回退）",
            "scope": "2026-09-22 至 24；Claude Code 2.1.280；23 道二进制重建题 × 5 档，各一次。所有失败均保留在通过率、费用和耗时中。",
            "columns": ["档位", "完整通过 / 23", "综合分 ± SE（评审 n）", "均费 / 题", "分钟 / 题", "回退任务；4.8 回复占比"],
            "display_rows": [[r["effort"], f'{r["passed"]}/23（{100*r["passed"]/23:.1f}%）', f'{r["combined"]:.2f} ± {r["combined_se"]:.2f}（n={r["judged_n"]}）', dollar(r["cost_usd"]), f'{r["time_s"]/60:.1f}', f'{r["fallback_runs"]}/23；{r["fallback_reply_pct"]:.1f}%'] for r in all_rows],
            "rows": all_rows,
            "takeaway": "这批实际配置中，medium 已 23/23 通过；max 更贵且少通过两题。可用于评估当时的默认回退工作流，不能归因为纯 Opus 5.5 的升档效果。",
            "caveat": "medium 及以上包含 Opus 4.8。high 有一个安全停止产生空补丁：完整通过为 22/23，综合分只评审 22 份。SE 是任务间标准误，不是档位差分的置信区间；费用为含回退的 CLI API 等价总价。",
            "sources": [[FRONTIER, "Vulcan 原报告"], [RUNS, "115 条原始运行 CSV"]],
        },
        {
            "id": "frontier-common", "title": "Frontier v4 · 共同无回退 6 题（探索性）",
            "scope": "由同一份 115 条运行记录复算，仅保留五档都没有 Opus 4.8 回复的共同题目；每档 6 题，均为同题配对。",
            "columns": ["档位", "完整通过 / 6", "均费 / 题", "分钟 / 题", "回退"],
            "display_rows": [[r["effort"], f'{r["passed"]}/6', dollar(r["cost_usd"]), f'{r["time_s"]/60:.1f}', "0"] for r in common_rows],
            "rows": common_rows, "common_tasks": sorted(common_tasks),
            "takeaway": "在这 6 题中 medium 起均全部通过；high 的均费和耗时比 medium 低。样本太小且经事后筛选，不能据此宣布 high 或 medium 是普遍甜蜜点。",
            "caveat": "这是按运行后的回退事件筛出的子集，排除了 17/23 题，仍有选择偏差。不能代表整套 23 题，也不是关闭回退后重跑的实验。各档分别删回退会留下 23/20/16/15/11 道不同题，更不能直接比较。未新跑模型，未做显著性检验。",
            "sources": [[RUNS, "共同题目筛选所用的原始 CSV"]],
        },
        {
            "id": "routine", "title": "Routine v1 · 日常小修小改（独立题集）",
            "scope": "12 道私有小型 Python 工单 × 5 档，各一次；涵盖局部 BUG、小功能、输入校验与日期、金额、文本边界。来源按“最低档容易完成”筛题。",
            "columns": ["档位", "完整通过 / 12", "综合分 ± SE", "均费 / 题", "秒 / 题"],
            "display_rows": [[r["effort"], f'{r["passed"]}/12', f'{r["combined"]:.2f} ± {r["combined_se"]:.2f}', dollar(r["cost_usd"]), f'{r["time_s"]:.1f}'] for r in routine_rows],
            "rows": routine_rows,
            "takeaway": "这类简单工单可从 low 试起；五档通过数相同。max 的均费约为 low 的 15.6 倍，耗时约 10.7 倍，没有增加完整通过数。",
            "caveat": "仅公开聚合数据，未披露 solver 回退分布，不能标成经逐条身份核验的纯模型。协议为 v3.14；Routine 综合分与 Frontier v4 不可跨表比较。题集小、难度预先筛选、无重复运行；low 的来源推荐还使用了“距最佳综合分不超过 3 分”的规则。",
            "sources": [[ROUTINE, "Vulcan Routine v1 榜单与方法"], ["https://vulcanbench.com/assets/data/routine-v1-board.csv", "Routine 聚合 CSV"]],
        },
        {
            "id": "official", "title": "官方 SWE-bench Pro 子集（独立实验）",
            "scope": "Anthropic 自测，2026-09-19 至 20；经评测环境筛选后 478 题。low/medium/high 各两轮，xhigh 一轮；每次响应上限 16,384 token。",
            "columns": ["档位", "解决率", "均费 / 尝试", "每题轮数", "耗时"],
            "display_rows": [[r["effort"], f'{r["score_pct"]:.1f}%', f'${r["cost_usd"]:.2f}', str(r["repeats"]), "未公布"] for r in official_rows],
            "rows": official_rows,
            "takeaway": "medium→high 多解决 2.5 个百分点；high→xhigh 再增 1.4 个百分点，费用约为 high 的 2.5 倍。对较长编码任务，medium 可作成本起点，high 用于优先提高完成率。",
            "caveat": "厂商实验不是独立复现；不可与 Vulcan、公榜或 system card 混算。费用是含失败的每次尝试成本，非每个成功任务成本；数字已取整。xhigh 两次尝试被输出上限截断；此实验未公布 max、耗时及逐题回退身份明细。",
            "sources": [[OFFICIAL + "#tune-effort", "官方档位表"], [OFFICIAL + "#refs", "官方方法与脚注 3"]],
        },
    ]
    result = {"reviewed_at": "2026-10-16", "model": "Claude Opus 5.5", "views": views,
              "not_run": "仅复算公开数据，没有新的模型调用或付费实验。"}
    (ROOT / "opus55-coding-supplement.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "original_runs": len(runs), "common_tasks": len(common_tasks),
                      "view_rows": {v["id"]: len(v["rows"]) for v in views}}, ensure_ascii=False))


if __name__ == "__main__":
    build()
