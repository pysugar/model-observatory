"""Rebuild the November 28 market tables from the frozen source files."""

import re

from refresh_aa import CHECKED, HERE, PREVIOUS, load, read, write


def scale_rows(table):
    vendors = {"anthropic": "Anthropic", "openai": "OpenAI", "google": "Google", "meta": "Meta",
               "moonshot": "Moonshot AI", "xai": "xAI", "deepseek": "DeepSeek", "minimax": "MiniMax",
               "zai": "Z.AI", "thinkingmachines": "Thinking Machines", "alibaba": "Alibaba", "nvidia": "NVIDIA"}
    aliases = {"Muse Ember 1.0": "Muse Ember", "GLM 5.3": "GLM-5.3", "MiniMax M3.1 Flash": "MiniMax-M3.1-Flash"}
    rows = []
    for src in table["rows"]:
        name, agent, effort = re.fullmatch(r"(.+?)( \(one-pass-agent\))?(?: (low|medium|high|xhigh|max))?", src["model"]).groups()
        if src["company"] == "meta" and name not in {"Muse Ember 1.0", "Muse Wonder 1.0", "Muse Spark 1.3"}:
            continue
        model = aliases.get(name, name.replace("GPT ", "GPT-"))
        if src["version"] == "fireworks_ai/deepseek-v4p1-flash-1017":
            model = "DeepSeek V4.1 Flash 1017"
        configuration = (effort or "未注明档位") + (" · one-pass-agent" if agent else " · 未注明代理框架")
        rows.append(dict(id=f"r{len(rows)+1}", model=model, vendor=vendors[src["company"]], configuration=configuration,
                         score=src["score"], interval=src["confidenceInterval_upper"], calibration_error=src["calibrationError"],
                         source_rank=src["rank"], cost_usd=None))
    return rows


def cross_source(columns, focus, open_weights, boards):
    aliases = {alias: name for name, names in focus for alias in names}
    models = {name: dict(model=name, open_weights=name in open_weights, cells={}) for name, _ in focus}
    for col in columns:
        source = col["id"]
        best = {}
        for row in boards[source]["rows"]:
            name = aliases.get(row["model"])
            value = row["score_exact"] if source == "aa5" else row["score"]
            exact = row.get("score_raw", row.get("score_exact", value))
            if name and (name not in best or exact > best[name][0]):
                best[name] = (exact, value, row["configuration"])
        col["covered"] = len(best)
        previous = None
        for i, (name, (exact, value, config)) in enumerate(sorted(best.items(), key=lambda item: -item[1][0]), 1):
            if exact != previous:
                rank = i
            models[name]["cells"][source] = dict(rank=rank, value=value, config=config)
            previous = exact
    for row in models.values():
        ranks = [c["rank"] for source, c in row["cells"].items() if source != "openrouter"]
        row["spread"] = max(ranks) - min(ranks) if len(ranks) > 1 else None
    return dict(columns=columns, models=list(models.values()),
                note=f"名次只在这 {len(models)} 款型号内计算，每款取该来源最高分。按保留精度排序，同分并列。空格表示缺测，用量不计入名次跨度。")


def main():
    helpers = load(HERE.with_name("2026-10-29") / "build_snapshot.py")
    snapshot = read(PREVIOUS / "market-snapshot.json")
    arena, live, manual, aa, notes = (read(HERE / name) for name in
        ("arena.json", "livebench.json", "manual-boards.json", "aa-index-v5.json", "notes.json"))
    boards = {b["id"]: b for b in snapshot["boards"]}
    praise_board = arena["boards"]["agent_praise_complaint"]
    assert praise_board["published"] == arena["boards"]["agent"]["published"]
    praise = {r["raw_name"]: r["score"] for r in praise_board["rows"]}
    for bid, source in (("arena", "text_style_control"), ("arena_webdev", "webdev"), ("arena_agent", "agent")):
        table = arena["boards"][source]
        extra = (lambda r: {"sessions": r["sessions"], "praise": praise.get(r["raw_name"])}) if bid == "arena_agent" else (lambda r: {"votes": r["votes"]})
        boards[bid].update(rows=helpers.arena_rows(table, len(table["rows"]), extra), checked_at=CHECKED,
                           source_updated_at=table["published"], selection=f"来源全榜 {table['total']} 项，选录前 40 名及关注型号。保留来源名次。Arena 数据集 {arena['revision'][:7]}。")
    chosen = [r for r in live["rows"] if r["vendor"]]
    boards["livebench"].update(checked_at=CHECKED, source_updated_at=live["release"],
        selection=f"11-06 题集共 {len(live['rows'])} 项，选录 {len(chosen)} 款。按官方七个套件的权重与费用文件复算。",
        rows=[dict(id=f"r{i}", model=r["model"], vendor=r["vendor"], score=r["overall"], score_exact=r["overall_exact"], cost_usd=r["cost_per_successful_task"],
                   coding=r["suites"]["coding"], source_order=r["source_order"],
                   configuration="页面未注明档位" + (" · 开放权重" if r["open_weights"] else "")) for i, r in enumerate(chosen, 1)])
    hle = scale_rows(manual["scale"])
    boards["scale"].update(checked_at=CHECKED, rows=hle, version="Humanity's Last Exam · Diamond",
        selection=f"来源 {manual['scale']['page_total']} 项，选录 {len(hle)} 项。保留来源并列名次、95% 区间及逐行标注的档位和框架。")
    for i, key in enumerate(("hss", "scale", "swe_full", "swe_hard", "rli", "multichallenge")):
        table = manual[key]
        top = table["rows"][:4]
        hl = dict(source_url=table["source_url"], checked_at=CHECKED, source_ranks=[r["rank"] for r in top])
        for j, r in enumerate(top, 1):
            interval = r["confidenceInterval_upper"]
            score = f"{r['score']:.2f} ±{interval:.2f}" if interval else f"{r['score']:.2f}%"
            hl[f"top{j}"] = r["model"].replace(" (one-pass-agent)", "") + f" ({score})"
        snapshot["scale_highlight_updates"][str(i)] = hl
    usage = manual["openrouter"]
    usage_rows = []
    for i, row in enumerate(usage["rows"], 1):
        config = "免费路由" if "(free)" in row["model"] else "平台全部已统计档位"
        if row["byok_capped"]:
            config += " · BYOK 用量触及统计上限"
        usage_rows.append(dict(id=f"r{i}", **row, cost_usd=None, configuration=config))
    boards["openrouter"].update(checked_at=CHECKED, source_updated_at=usage["usage_through"], rows=usage_rows,
        version=f"Text · 截至 {usage['usage_through']} 的滚动 7 天",
        note="OpenRouter 按 token 用量排序，自带密钥（BYOK）的流量有统计上限。该指标不能作为能力分。")
    names = {name for name, _ in helpers.FOCUS}
    aliases = {"Muse Wonder": ["Muse Wonder 1.0"], "Muse Ember": ["Muse Ember 1.0"], "Qwen4-Max": ["Qwen4 Max"],
               "Tencent Hy4": ["Hy4"]}
    new_references = ["Tencent Hy4", "Hy4 flash", "Inkling 2 Small", "Inkling 2 Mini"]
    for name in [r["model"] for r in snapshot["cross_source"]["models"]] + new_references:
        if name not in names:
            helpers.FOCUS.append((name, [name, *aliases.get(name, [])]))
            names.add(name)
    helpers.OPEN_WEIGHTS.update(["Kimi K3.1 Pro", *new_references])
    cross = cross_source(snapshot["cross_source"]["columns"], helpers.FOCUS, helpers.OPEN_WEIGHTS, {**boards, "aa5": aa["board"]})
    snapshot.update(reviewed_at=CHECKED, cross_source=cross, changes=notes["changes"])
    for h in snapshot["highlights"]:
        if h["board_id"] == "arena":
            h["caption"] = "Text Arena · " + boards["arena"]["rows"][0]["configuration"] + " · " + boards["arena"]["source_updated_at"][5:]
    for row in snapshot["vendor_updates"]:
        row["note"] = notes["vendors"][row["vendor"]]
    for row in snapshot["official_sources"]:
        row.update(checked_at=CHECKED, note=notes["official"][row["vendor"]])
        if row["vendor"] == "xAI":
            row["url"] = "https://docs.x.ai/developers/pricing"
    write(HERE / "market-snapshot.json", snapshot)


if __name__ == "__main__":
    main()
