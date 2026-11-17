"""Add the GPT-6.2 launch to the 11-15 observations without rewriting other sources.

Only AA has measured GPT-6.2 so far. Arena, LiveBench, Scale and OpenRouter keep their
11-15 snapshots and verification dates; the cross-source table is recomputed with the
11-18 AA board.
"""

from refresh_aa import HERE, ROOT, PREVIOUS, CHECKED, load, read, write


def main():
    helpers = load("snapshot_helpers", "research/2026-10-29/build_snapshot.py")
    snap = read(PREVIOUS / "market-snapshot.json")
    arena, live, manual = (read(PREVIOUS / name) for name in ("arena.json", "livebench.json", "manual-boards.json"))
    aa = read(HERE / "aa-index-v5.json")
    snap["reviewed_at"] = CHECKED
    snap["changes"] = [
        {"title": "GPT-6.2 Astra / Sol 上线", "body": "11-17发布，AA已测low至max五档：Astra 6.2 max 62.1分、$4.00/任务，xhigh 61.6分、$2.52；Sol 6.2 max 57.3分、$1.01。Sol其余四档AA暂未公布费用，不推算。"},
        {"title": "OpenAI 单价与上一代", "body": "Astra 6.2 Standard降至$8 / $40（缓存$0.40），Sol 6.2沿用$2 / $10；>272k输入整次加价规则不变。GPT-6 Astra与6.1 Sol仍可调用，已离开AA当前榜单，曲线保留在档案。"},
        {"title": "其他来源尚未收录", "body": "Arena 11-11、LiveBench 11-06题集、Scale HLE Diamond与OpenRouter 11-13均无GPT-6.2，跨榜对照只在AA列出现，不推算其他来源名次。"},
        {"title": "价格日期提醒不变", "body": "Carbon / Argon优惠仍至11-30，12-01单价翻倍；Ember >200k输入整次三倍计价。其余厂商本期无新通用主力。"},
    ]
    for source in snap["official_sources"]:
        if source["vendor"] == "OpenAI":
            source.update(checked_at=CHECKED, note="GPT-6.2 Astra / Sol Standard、>272k整次加价、Batch与Fast倍率；GPT-6 Astra / 6.1 Sol仍列价，未见弃用。")
    for update in snap["vendor_updates"]:
        if update["vendor"] == "OpenAI":
            update.update(slugs=["gpt-6-2-astra", "gpt-6-2-astra-xhigh", "gpt-6-2-sol", "gpt-6-1-terra", "gpt-6-luna"],
                          note="GPT-6.2 Astra / Sol 11-17上线：Astra 6.2降价20%、max指数62.1；Sol 6.2沿用旧价，仅max有AA任务费用。官方迁移指南建议从medium起步。",
                          url="https://developers.openai.com/api/docs/models")
    helpers.FOCUS += [("Gemini 4 Carbon", ["Gemini 4 Carbon"]), ("GPT-6.1 Terra", ["GPT-6.1 Terra"]),
        ("Muse Wonder", ["Muse Wonder", "Muse Wonder 1.0"]), ("Muse Wonder Full", ["Muse Wonder Full"]),
        ("Muse Spark 1.3", ["Muse Spark 1.3"]), ("Claude Fable 5.2", ["Claude Fable 5.2"]),
        ("Gemini 4 Hydrogen", ["Gemini 4 Hydrogen"]), ("Muse Ember", ["Muse Ember", "Muse Ember 1.0"]),
        ("GPT-6.2 Astra", ["GPT-6.2 Astra"]), ("GPT-6.2 Sol", ["GPT-6.2 Sol"])]
    snap["cross_source"] = helpers.cross_source(arena, live, manual, aa)
    snap["cross_source"]["note"] = snap["cross_source"]["note"].replace("14 款", str(len(helpers.FOCUS)) + " 款")
    write(HERE / "market-snapshot.json", snap)
    print({b["id"]: len(b["rows"]) for b in snap["boards"]}, len(snap["cross_source"]["models"]))


if __name__ == "__main__":
    main()
