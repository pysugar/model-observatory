"""Assemble the market tables from the frozen November 21 inputs without network access."""

from refresh_aa import CHECKED, HERE, PREVIOUS, load, read, write


def scale_rows(raw):
    vendors = {"anthropic": "Anthropic", "openai": "OpenAI", "google": "Google", "meta": "Meta",
               "moonshot": "Moonshot AI", "xai": "xAI", "deepseek": "DeepSeek", "minimax": "MiniMax",
               "zai": "Z.AI", "thinkingmachines": "Thinking Machines"}
    aliases = {"Muse Ember 1.0": "Muse Ember", "GLM 5.3": "GLM-5.3", "MiniMax M3.1 Flash": "MiniMax-M3.1-Flash"}
    result = []
    for row in raw["rows"]:
        name, effort = row["model"].split(" (one-pass-agent)", 1)
        if row["company"] == "meta" and name not in {"Muse Ember 1.0", "Muse Wonder 1.0", "Muse Spark 1.3"}:
            continue
        model = aliases.get(name, name.replace("GPT ", "GPT-"))
        if row["version"] == "fireworks_ai/deepseek-v4p1-flash-1017":
            model = "DeepSeek V4.1 Flash 1017"
        result.append(dict(id=f"r{len(result)+1}", model=model, vendor=vendors[row["company"]],
                           configuration=(effort.strip() or "未注明档位") + " · one-pass-agent",
                           score=row["score"], interval=row["confidenceInterval_upper"],
                           calibration_error=row["calibrationError"], cost_usd=None, source_rank=row["rank"]))
    return result


def main():
    helpers = load(HERE.with_name("2026-10-29") / "build_snapshot.py")
    snap = read(PREVIOUS / "market-snapshot.json")
    arena, live, manual, aa = (read(HERE / name) for name in
                               ("arena.json", "livebench.json", "manual-boards.json", "aa-index-v5.json"))
    boards = {b["id"]: b for b in snap["boards"]}
    praise = {r["raw_name"]: r["score"] for r in arena["boards"]["agent_praise_complaint"]["rows"]}
    for bid, config in (("arena", "text_style_control"), ("arena_webdev", "webdev"), ("arena_agent", "agent")):
        source = arena["boards"][config]
        extra = (lambda r: {"sessions": r["sessions"], "praise": praise.get(r["raw_name"])}) if bid == "arena_agent" else (lambda r: {"votes": r["votes"]})
        boards[bid].update(
            rows=helpers.arena_rows(source, len(source["rows"]), extra), source_updated_at=source["published"],
            checked_at=CHECKED, selection=f"来源全榜 {source['total']} 项，选录前 40 名及关注型号。保留来源名次，Meta 仅闭源系列。Arena 数据集 {arena['revision'][:7]}。",
        )
    live_rows = [r for r in live["rows"] if r["vendor"]]
    boards["livebench"].update(
        checked_at=CHECKED, source_updated_at=live["release"],
        selection=f"11-06 题集共 {len(live['rows'])} 项，选录 {len(live_rows)} 款。新增 Gemini 4 Neon 成绩，另补列 Qwen4-Max 参照。按官方套件权重与费用文件复算。",
        rows=[dict(id=f"r{i}", model=r["model"], vendor=r["vendor"], score=r["overall"],
                   cost_usd=r["cost_per_successful_task"], coding=r["suites"]["coding"], source_order=r["source_order"],
                   configuration="页面未注明档位" + (" · 开放权重" if r["open_weights"] else "")) for i, r in enumerate(live_rows, 1)],
    )
    scale = manual["scale"]
    hle = scale_rows(scale)
    boards["scale"].update(
        checked_at=CHECKED, source_updated_at=None, rows=hle, version="Humanity's Last Exam · Diamond · one-pass-agent",
        selection=f"来源 {scale['page_total']} 行，选录 {len(hle)} 行。保留来源名次、置信区间和明示档位。全榜发布日期未披露。",
        note="读取 Performance Comparison 动态榜。主指标为 1,000 道专家题的正确率，校准误差单独列出。AA 的 HLE 子项使用其自身评测协议。",
    )
    usage = manual["openrouter"]
    boards["openrouter"].update(
        checked_at=CHECKED, source_updated_at=usage["usage_through"],
        version=f"Text · This Week · 截至 {usage['usage_through']} 的滚动 7 天",
        rows=[dict(id=f"r{i}", **r, cost_usd=None, configuration="免费路由" if "(free)" in r["model"] else "平台全部已统计档位")
              for i, r in enumerate(usage["rows"], 1)],
    )
    for idx, key in enumerate(("hss", "scale", "swe_full", "swe_hard", "rli", "multichallenge")):
        table = manual[key]
        first_four = table["rows"][:4]
        highlight = {"source_url": table["source_url"], "checked_at": CHECKED,
                     "source_ranks": [row["rank"] for row in first_four]}
        for position, row in enumerate(first_four, 1):
            name = row["model"].replace(" (one-pass-agent)", "")
            interval = row["confidenceInterval_upper"]
            value = f"{row['score']:.2f} ±{interval:.2f}" if interval else f"{row['score']:.2f}%"
            highlight[f"top{position}"] = f"{name} ({value})"
        snap["scale_highlight_updates"][str(idx)] = highlight

    names = {name for name, _ in helpers.FOCUS}
    aliases = {"Muse Wonder": ["Muse Wonder 1.0"], "Muse Ember": ["Muse Ember 1.0"], "Qwen4-Max": ["Qwen4 Max"]}
    for name in [r["model"] for r in snap["cross_source"]["models"]] + ["Qwen4-Max"]:
        if name not in names:
            helpers.FOCUS.append((name, [name, *aliases.get(name, [])]))
    helpers.OPEN_WEIGHTS.add("Kimi K3.1 Pro")
    comparable = {
        "scale": {"rows": [(None, r["model"], r["vendor"], r["score"], r["interval"], r["calibration_error"]) for r in hle]},
        "openrouter": {"rows": [(r["model"], r["vendor"], r["score"], r["change"]) for r in usage["rows"]]},
    }
    cross = helpers.cross_source(arena, live, comparable, aa)
    cross["note"] = f"每列只在这 {len(cross['models'])} 款型号中排序，取该来源的最高分配置。空格表示该榜缺测。跨度覆盖能力、偏好与真实会话；用量单列。"
    scale_config = {r["model"]: r["configuration"] for r in hle}
    for row in cross["models"]:
        if "scale" in row["cells"]:
            model = "Muse Wonder 1.0" if row["model"] == "Muse Wonder" else row["model"]
            row["cells"]["scale"]["config"] = scale_config[model]
    snap.update(reviewed_at=CHECKED, cross_source=cross)
    for h in snap["highlights"]:
        if h["board_id"] == "arena":
            h["caption"] = "Text Arena · high · " + boards["arena"]["source_updated_at"][5:]

    notes = read(HERE / "notes.json")
    snap["changes"] = notes["changes"]
    for row in snap["vendor_updates"]:
        row["note"] = notes["vendors"][row["vendor"]]
    for row in snap["official_sources"]:
        row.update(checked_at=CHECKED, note=notes["official"][row["vendor"]])
    write(HERE / "market-snapshot.json", snap)


if __name__ == "__main__":
    main()
