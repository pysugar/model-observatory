"""Assemble the 2026-11-19 observations: Gemini 4 Neon launch and full multi-source refresh.

Arena, LiveBench, Scale SEAL and OpenRouter come from this folder's raw files; earlier
snapshots stay untouched. Each source keeps its own publish date and verification date.
"""

from refresh_aa import HERE, ROOT, CHECKED, load, read, write


def main():
    helpers = load("snapshot_helpers", "research/2026-10-29/build_snapshot.py")
    snap = read(ROOT / "research/2026-11-18-pm/market-snapshot.json")
    arena, live, manual, aa = (read(HERE / name) for name in
                               ("arena.json", "livebench.json", "manual-boards.json", "aa-index-v5.json"))
    boards = {b["id"]: b for b in snap["boards"]}
    praise = {r["raw_name"]: r["score"] for r in arena["boards"]["agent_praise_complaint"]["rows"]}
    for bid, config in (("arena", "text_style_control"), ("arena_webdev", "webdev"), ("arena_agent", "agent")):
        src = arena["boards"][config]
        rows = helpers.arena_rows(
            src, len(src["rows"]),
            (lambda r: {"praise": praise.get(r["raw_name"]), "sessions": r["sessions"]}) if bid == "arena_agent"
            else (lambda r: {"votes": r["votes"]}),
        )
        boards[bid].update(
            rows=rows, checked_at=CHECKED, source_updated_at=src["published"],
            selection=f"选录前40名及关注型号，来源全榜{src['total']}项；保留来源名次。Arena官方数据集固定版本{arena['revision'][:7]}，Meta仅闭源系列。",
        )
    boards["livebench"].update(
        checked_at=CHECKED, source_updated_at=live["release"],
        version=f"LiveBench 2.0 · release {live['release']}（长程代理×2、编程与设计×1.5）",
        selection=f"{len(live['rows'])}项原始记录中选录{sum(bool(r['vendor']) for r in live['rows'])}款已识别型号。11-06题集包含GPT-6.2 Astra / Sol，尚无Gemini 4 Neon；按来源静态文件与页面公式复算。",
        note="11-06题集；与10-25题集不同，不能把两期分数之差当作能力变化。Overall为加权均值；来源没有注明原生effort，不归给high或max。",
        rows=[dict(
            id=f"r{i}", model=r["model"], vendor=r["vendor"], score=r["overall"],
            cost_usd=r["cost_per_successful_task"], coding=r["suites"]["coding"], source_order=r["source_order"],
            configuration="页面未注明档位" + (" · 开放权重" if r["open_weights"] else ""),
        ) for i, r in enumerate((r for r in live["rows"] if r["vendor"]), 1)],
    )
    scale = manual["scale"]
    boards["scale"].update(
        checked_at=CHECKED, source_updated_at=None,
        selection=f"来源全榜{scale['page_total']}项，选录{len(scale['rows'])}项，排除Meta开放权重型号；发布日期未披露，保留来源名次。",
        rows=[dict(
            id=f"r{i}", model=name, vendor=vendor, configuration="页面未注明档位", score=score,
            interval=ci, calibration_error=ce, cost_usd=None, source_rank=scale["source_ranks"][slug],
        ) for i, (slug, name, vendor, score, ci, ce) in enumerate(scale["rows"], 1)],
    )
    usage = manual["openrouter"]
    boards["openrouter"].update(
        checked_at=CHECKED, source_updated_at=usage["usage_through"],
        version=f"Text · This Week · 截至{usage['usage_through']}的滚动7天",
        selection="来源页面Weekly usage前十；token用量不等于用户数、收入或能力排名。",
        rows=[dict(
            id=f"r{i}", model=name, vendor=vendor, configuration="平台全部已统计档位", score=score,
            change=change, source_rank=i, cost_usd=None,
        ) for i, (name, vendor, score, change) in enumerate(usage["rows"], 1)],
    )
    # Refresh Scale SEAL highlights (indices 0=HSS, 1=HLE Diamond, 4=RLI, 5=MultiChallenge).
    extra = manual.get("scale_extra", {})
    fmt_top = lambda items: {f"top{i}": f"{r['model']} ({r['score']})" for i, r in enumerate(items[:4], 1)}
    hle_top4 = [
        {"model": name, "score": f"{score:.2f} ±{ci:.2f}"}
        for _slug, name, _vendor, score, ci, _ce in scale["rows"][:4]
    ]
    snap["scale_highlight_updates"] = {
        "0": {**fmt_top(extra["hss"]["top10"]), "source_url": extra["hss"]["source_url"], "checked_at": CHECKED},
        "1": {**fmt_top(hle_top4), "source_url": scale["source_url"], "checked_at": CHECKED},
        "4": {**fmt_top(extra["rli"]["top10"]), "source_url": extra["rli"]["source_url"], "checked_at": CHECKED},
        "5": {**fmt_top(extra["multichallenge"]["top10"]), "source_url": extra["multichallenge"]["source_url"], "checked_at": CHECKED},
    }
    for h in snap["highlights"]:
        if h["board_id"] == "arena":
            h["caption"] = f"Text Arena · high · {boards['arena']['source_updated_at'][5:]}"
    snap["reviewed_at"] = CHECKED
    snap["changes"] = [
        {
            "title": "Arena 三榜 11-18 全面刷新",
            "body": "Text 榜 Carbon 升至 #1（1525.9）、Neon 首秀 #3（1518.5），Google 包揽前三；WebDev 榜 Fable 5.2 #1、GPT-6.2 Astra 空降 #3（1780.6）、Neon #6、Sol 6.2 #8；Agent 榜 Fable 5.2 #1（0.274）、Neon #3（0.184，紧咬 Opus 5.5 max）、Astra 6.2 #6。",
        },
        {
            "title": "Vals Index 与 Scale SEAL 专项对照",
            "body": "Vals Index v2.2（GDP 行业加权，11-18）：Fable 5.2 #1（71.31%）、Neon #2（70.87%）、Astra 6.2 67.66%。Scale Remote Labor Index 上 Fable 5.2 达 41.25%（近第二名两倍）；HSS 榜 Carbon high 71.10 居首；MultiChallenge 中 GPT-6.2（73.20 / 72.00）低于 6.1 Sol（81.95）。",
        },
        {
            "title": "社区最佳实践与 API 变更",
            "body": "GPT-6.2 Responses API 改为将顶层 instructions 附在 input 之后，可复用系统提示须放首条 developer 消息以保缓存，且中途改前缀会丢弃缓存推理项；Kernel.dev 追踪显示 Carbon 慢主因是长轨迹过度盘查，每 5 轮插入检查点可明显提速。",
        },
        {
            "title": "OpenRouter 热度与价格日历",
            "body": "OpenRouter 周用量截至 11-18：DeepSeek V4.1 Flash 1017 居首（62.1T），腾讯 Hy4 Flash 升至 46.6T，MiniMax-M3.1-Flash 进前十。GPT-5.6 Sol 优惠确认延至 11-30，Carbon / Argon 12-01 单价翻倍、Sonnet 4.5 11-30 退役。",
        },
    ]
    snap["vendor_updates"] = [dict(u) for u in snap["vendor_updates"]]
    for source in snap["official_sources"]:
        source["checked_at"] = CHECKED
        if source["vendor"] == "Google":
            source["note"] = "11-18 新增 Neon（$3/$0.15/$15，无免费层）；Carbon / Argon 优惠仍至 11-30、12-01 起 $4/$20；Hydrogen 全窗口 $1.50/$7.50。"
        elif source["vendor"] == "OpenAI":
            source["note"] = "GPT-6.2 Standard $8/$40 与 $2/$10，不支持 Flex、改推 2h/8h 后台折扣；GPT-5.6 Sol 优惠确认延至 11-30。"
        elif source["vendor"] == "Anthropic":
            source["note"] = "Fable 5.2 与 5.5 系列单价不变；Sonnet 4.5 计划 11-30 退役；Mythos 5.2 仍限机构验证。"
        elif source["vendor"] == "Meta":
            source["note"] = "闭源 Wonder / Spark 1.3 / Ember Standard 价不变；Ember >200k 全量 ×3。"
        elif source["vendor"] == "xAI":
            source["note"] = "公开 API 主力仍为 Grok 4.7（$2/$0.50/$6，≥200k ×2）；Grok 4.8 尚未开放正式 API。"
    for update in snap["vendor_updates"]:
        if update["vendor"] == "OpenAI":
            update.update(
                slugs=["gpt-6-2-astra", "gpt-6-2-astra-xhigh", "gpt-6-2-sol", "gpt-6-2-sol-high", "gpt-6-1-terra", "gpt-6-luna"],
                note="GPT-6.2 已进 Arena WebDev（Astra #3 / Sol #8）与 Agent（#6 / #11），但 MultiChallenge 低于 6.1 Sol。直接调 Responses API 须把可复用提示放首条 developer 消息、避免中途改前缀，并显式要求报告阻碍与持续执行。",
            )
        elif update["vendor"] == "Anthropic":
            update.update(
                slugs=["claude-fable-5-2", "claude-fable-5-2-high", "claude-opus-5-5", "claude-sonnet-5-5"],
                note="Fable 5.2 在 AA v5、Arena WebDev / Agent、Scale HLE / RLI（41.25%）与 Vals Index（71.31%）全面领跑，但高档输出量与账单昂贵（max $26.54/任务）；社区普遍保留 Opus 5.5 作日常主力，Fable 5.2 留给规划与疑难升级。",
            )
        elif update["vendor"] == "Google":
            update.update(
                slugs=["gemini-4-neon", "gemini-4-neon-high", "gemini-4-carbon", "gemini-4-hydrogen", "gemini-4-hydrogen-high"],
                note="新增 Gemini 4 Neon（默认 high，支持 xhigh，$3/$15）：high 60 分 / $3.74 逼近 Carbon high（60 分 / $7.76）且快约四成，Arena Agent #3、Vals Index #2；12-01 Carbon/Argon 涨价后，多数工程任务优先 Neon + Hydrogen 分工。",
            )
        elif update["vendor"] == "xAI":
            update.update(
                slugs=["grok-4-7-high", "grok-4-7"],
                note="公开 API 仍为 Grok 4.7（xhigh 略高于 high 但更贵，medium 仍缺 AA 同协议成绩）；Grok 4.8 仅在消费端小范围灰度，暂无正式 API 文档或独立第三方评测。",
            )
        elif update["vendor"] == "Meta":
            update.update(
                slugs=["muse-wonder-full", "muse-wonder", "muse-spark-1-3", "muse-ember", "muse-ember-xhigh"],
                note="Muse Ember（max 36 分 / $0.14，~466 tok/s）居 AA 轻量效率前沿，但 FrontierCode 2.0 弱于 Haiku 且 >200k 整次 ×3；Wonder Full 仍仅限 Muse Code 订阅、无公开 API 定价。",
            )
    helpers.FOCUS += [
        ("Gemini 4 Carbon", ["Gemini 4 Carbon"]),
        ("GPT-6.1 Terra", ["GPT-6.1 Terra"]),
        ("Muse Wonder", ["Muse Wonder", "Muse Wonder 1.0"]),
        ("Muse Wonder Full", ["Muse Wonder Full"]),
        ("Muse Spark 1.3", ["Muse Spark 1.3"]),
        ("Claude Fable 5.2", ["Claude Fable 5.2"]),
        ("Gemini 4 Hydrogen", ["Gemini 4 Hydrogen"]),
        ("Gemini 4 Neon", ["Gemini 4 Neon"]),
        ("Muse Ember", ["Muse Ember", "Muse Ember 1.0"]),
        ("GPT-6.2 Astra", ["GPT-6.2 Astra"]),
        ("GPT-6.2 Sol", ["GPT-6.2 Sol"]),
    ]
    snap["cross_source"] = helpers.cross_source(arena, live, manual, aa)
    snap["cross_source"]["note"] = snap["cross_source"]["note"].replace("14 款", str(len(helpers.FOCUS)) + " 款")
    write(HERE / "market-snapshot.json", snap)
    print(
        {b["id"]: len(b["rows"]) for b in snap["boards"]},
        "cross_models=", len(snap["cross_source"]["models"]),
        "neon_cells=", next(m["cells"] for m in snap["cross_source"]["models"] if m["model"] == "Gemini 4 Neon"),
        "astra62_cells=", next(m["cells"] for m in snap["cross_source"]["models"] if m["model"] == "GPT-6.2 Astra"),
    )


if __name__ == "__main__":
    main()
