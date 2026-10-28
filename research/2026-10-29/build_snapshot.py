"""Assemble the 2026-10-29 market snapshot from the dated inputs in this folder.

Starts from research/2026-10-23/market-snapshot.json and replaces only boards with a
newer read. The frozen AA v4.3.2 board is kept as is; AA v5 is merged at build time from
research/2026-10-28/aa-index-v5.json. No value here is derived from another source.

Run from the repository root after the fetch scripts:
python3 research/2026-10-29/build_snapshot.py
"""

from pathlib import Path
import copy
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CHECKED = "2026-10-29"
EFFORT_LABEL = {"default": "未注明档位", "minimal": "minimal", "low": "low", "medium": "medium",
                "high": "high", "xhigh": "xhigh", "max": "max"}


def read(path):
    return json.loads(Path(path).read_text())


def arena_rows(board, limit, extra):
    rows = []
    for i, r in enumerate(board["rows"][:limit], 1):
        config = EFFORT_LABEL[r["effort"]] + (" · 开放权重" if r["open_weights"] else "")
        row = {"id": f"r{i}", "model": r["model"], "vendor": r["vendor"], "configuration": config,
               "score": r["score"], "interval": round((r["upper"] - r["lower"]) / 2, 4 if r["score"] < 5 else 1),
               "source_rank": r["source_rank"], "cost_usd": None}
        row.update(extra(r))
        rows.append(row)
    return rows


# Models compared across sources, with the names each source uses for them.
FOCUS = [
    ("GPT-6 Astra", ["GPT-6 Astra"]), ("GPT-6.1 Sol", ["GPT-6.1 Sol"]), ("GPT-6 Luna", ["GPT-6 Luna"]),
    ("Claude Opus 5.5", ["Claude Opus 5.5"]), ("Claude Fable 5.1", ["Claude Fable 5.1"]),
    ("Claude Sonnet 5.5", ["Claude Sonnet 5.5"]), ("Claude Haiku 5.5", ["Claude Haiku 5.5"]),
    ("Gemini 4 Argon", ["Gemini 4 Argon"]), ("Gemini 3.8 Flash", ["Gemini 3.8 Flash"]), ("Grok 4.7", ["Grok 4.7"]),
    ("DeepSeek V4.1 Flash 1017", ["DeepSeek V4.1 Flash 1017", "DeepSeek-V4.1-Flash-20261017"]),
    ("Kimi K3.1 Pro", ["Kimi K3.1 Pro"]), ("GLM-5.3", ["GLM-5.3", "GLM 5.3"]),
    ("MiMo V2.6 Pro", ["MiMo-V2.6-Pro", "MiMo V2.6 Pro"]),
]
OPEN_WEIGHTS = {"DeepSeek V4.1 Flash 1017", "GLM-5.3", "MiMo V2.6 Pro"}


def cross_source(arena, live, manual, aa5):
    """Rank the focus models within each source (best configuration per model)."""
    alias = {name: model for model, names in FOCUS for name in names}
    sources = [
        ("aa5", "AA v5", "能力", "智能指数", [(r["model"], r["score_exact"], r["configuration"]) for r in aa5["board"]["rows"]]),
        ("arena", "Arena 文本", "偏好", "Elo", [(r["model"], r["score"], r["effort"]) for r in arena["boards"]["text_style_control"]["rows"]]),
        ("arena_webdev", "Arena WebDev", "偏好", "分", [(r["model"], r["score"], r["effort"]) for r in arena["boards"]["webdev"]["rows"]]),
        ("arena_agent", "Agent Arena", "真实会话", "IPS", [(r["model"], r["score"], r["effort"]) for r in arena["boards"]["agent"]["rows"]]),
        ("livebench", "LiveBench", "能力", "分", [(r["model"], r["overall"], "") for r in live["rows"]]),
        ("scale", "HLE Diamond", "能力", "%", [(name, score, "") for _, name, _, score, _, _ in manual["scale"]["rows"]]),
        ("openrouter", "OpenRouter 用量", "热度", "T tokens", [(name, score, "") for name, _, score, _ in manual["openrouter"]["rows"]]),
    ]
    cells = {model: {} for model, _ in FOCUS}
    columns = []
    for sid, label, group, unit, rows in sources:
        best = {}
        for name, value, config in rows:
            model = alias.get(name)
            if model and (model not in best or value > best[model][0]):
                best[model] = (value, config)
        ranked = sorted(best, key=lambda m: -best[m][0])
        for i, model in enumerate(ranked, 1):
            value, config = best[model]
            cells[model][sid] = {"rank": i, "value": value, "config": config}
        columns.append({"id": sid, "label": label, "group": group, "unit": unit, "covered": len(ranked)})
    models = []
    for model, _ in FOCUS:
        ranks = [c["rank"] for sid, c in cells[model].items() if sid != "openrouter"]
        models.append({"model": model, "open_weights": model in OPEN_WEIGHTS, "cells": cells[model],
                       "spread": max(ranks) - min(ranks) if len(ranks) > 1 else None})
    return {"columns": columns, "models": models,
            "note": "名次只在这 14 款模型之间排列，每款取该来源最好的一个配置；“—”表示来源这次没有收录或没有上榜，不代表能力差。"
                    "跨度只看能力、偏好与真实会话来源，不含 OpenRouter 用量。各列口径不同，名次不能相加或平均。"}


def main():
    snap = read(ROOT / "research/2026-10-23/market-snapshot.json")
    arena, live, manual = read(HERE / "arena.json"), read(HERE / "livebench.json"), read(HERE / "manual-boards.json")
    boards = {b["id"]: b for b in snap["boards"]}

    text = boards["arena"]
    text.update(checked_at=CHECKED, selection=text["selection"] + " 10 月 29 日用 Arena 官方数据集（text_style_control）逐行核对，"
                "分数、区间与票数一致；来源本期没有新发布。")

    praise = {r["raw_name"]: r["score"] for r in arena["boards"]["agent_praise_complaint"]["rows"]}
    webdev_src, agent_src = arena["boards"]["webdev"], arena["boards"]["agent"]
    webdev = {
        "id": "arena_webdev", "name": "Arena", "short": "Arena WebDev", "kind": "网页开发偏好",
        "metric": "Code Arena (WebDev) 分数", "unit": "分", "precision": 0,
        "source_url": "https://arena.ai/leaderboard/webdev", "source_updated_at": webdev_src["published"],
        "version": "WebDev · Overall（HTML / React / 图生网页）", "cost_label": None,
        "cost_basis": "来源不报告费用。",
        "extra_key": "votes", "extra_label": "对战数", "extra_unit": "场",
        "selection": f"选录来源前 15 名（共 {webdev_src['total']} 项）。arena.ai 拦截自动读取，数据取自 Arena 官方 Hugging Face 数据集同一发布，版本固定在 {arena['revision'][:7]}。",
        "note": "用户对两个模型生成的网页做盲选，衡量前端与交互生成的偏好，不等于后端工程或代码审查能力。同一模型不同档位分列；区间重叠不说明显著领先。",
        "checked_at": CHECKED,
        "rows": arena_rows(webdev_src, 15, lambda r: {"votes": r["votes"]}),
    }
    agent = {
        "id": "arena_agent", "name": "Arena", "short": "Agent Arena", "kind": "真实代理会话",
        "metric": "Agent Arena 综合 IPS", "unit": "", "precision": 3, "fixed_precision": True,
        "source_url": "https://arena.ai/leaderboard/agent", "source_updated_at": agent_src["published"],
        "version": "Agent Arena · Overall（IPS 估计）", "cost_label": None, "cost_basis": "来源不报告费用。",
        "extra_key": "praise", "extra_label": "表扬 / 抱怨信号", "extra_unit": "",
        "selection": f"选录来源前 15 名（共 {agent_src['total']} 项）。数据取自 Arena 官方 Hugging Face 数据集，版本 {arena['revision'][:7]}；“表扬 / 抱怨信号”取同一发布的 agent_praise_complaint 分项。",
        "note": "来自真实代理会话里的多种信号（任务结果、可引导性、工具幻觉、bash 可靠性、用户表扬与抱怨），用 IPS 估计，越高越好；不是任务成功率。10 月 12 日起 bash 信号口径已改。方法原页拦截自动读取，本期未直接打开。",
        "checked_at": CHECKED,
        "rows": arena_rows(agent_src, 15, lambda r: {"praise": praise.get(r["raw_name"]), "sessions": r["sessions"]}),
    }

    lb = boards["livebench"]
    lb.update(source_updated_at=live["release"], checked_at=CHECKED,
              version=f"LiveBench 2.0 · release {live['release']}（长程代理 ×2、编程与设计 ×1.5 加权）",
              selection=f"选录页面列出名称的 {sum(1 for r in live['rows'] if r['vendor'])} 项（原始页面共 {len(live['rows'])} 项）。"
                        "Overall 与每成功任务成本按页面规则由发布静态文件重算，并与页面抽查值一致。",
              note="10-25 版起 Overall 改为加权均值（长程代理 ×2，编程、设计 ×1.5），与 10-14 版不能直接比较。主表未注明原生 effort，不可据此把成绩归给 high 或 max。",
              rows=[{"id": f"r{i}", "model": r["model"], "vendor": r["vendor"], "score": r["overall"],
                     "cost_usd": r["cost_per_successful_task"], "coding": r["suites"]["coding"],
                     "source_order": r["source_order"],
                     "configuration": "页面未注明档位" + (" · 开放权重" if r["open_weights"] else "")}
                    for i, r in enumerate((r for r in live["rows"] if r["vendor"]), 1)])

    sc, sm = boards["scale"], manual["scale"]
    sc.update(checked_at=CHECKED, selection=f"选录页面全部 {sm['page_total']} 项。核验日期不是评测日期；页面未明确更新日期，保留未知。",
              rows=[{"id": f"r{i}", "model": name, "vendor": vendor, "score": score, "interval": ci,
                     "calibration_error": ce, "configuration": "页面未注明档位", "cost_usd": None}
                    for i, (_, name, vendor, score, ci, ce) in enumerate(sm["rows"], 1)])

    orr, om = boards["openrouter"], manual["openrouter"]
    orr.update(checked_at=CHECKED, source_updated_at=om["usage_through"],
               version="Text · This Week · 截至 10 月 27 日的滚动 7 天",
               rows=[{"id": f"r{i}", "model": name, "vendor": vendor, "score": score, "change": change,
                      "source_rank": i, "cost_usd": None,
                      "configuration": "免费路由 · 与付费版分列" if "(free)" in name else "平台全部已统计档位"}
                     for i, (name, vendor, score, change) in enumerate(om["rows"], 1)])

    order = ["aa", "arena", "arena_webdev", "arena_agent", "livebench", "scale", "openrouter"]
    boards.update(arena_webdev=webdev, arena_agent=agent)
    out = copy.deepcopy(snap)
    out["boards"] = [boards[k] for k in order]
    out["reviewed_at"] = CHECKED
    out["changes"] = read(HERE / "notes.json")["changes"]
    for source in out["official_sources"]:
        if source["vendor"] == "Google":
            source.update(checked_at=CHECKED, note="Argon 优惠价 $2 / $10 仍至 2026-11-30；12-01 起 $4 / $20。AA v5 已按 12-01 后价格计 Argon 费用。")
    out["cross_source"] = cross_source(arena, live, manual, read(ROOT / "research/2026-10-28/aa-index-v5.json"))
    (HERE / "market-snapshot.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({b["id"]: len(b["rows"]) for b in out["boards"]}))


if __name__ == "__main__":
    main()
