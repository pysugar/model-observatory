"""Assemble the 11-18 evening observations: every board re-read after the GPT-6.2 launch.

Arena, LiveBench, Scale and OpenRouter come from this folder's raw files; earlier
snapshots stay untouched. Each source keeps its own publish date and verification date.
"""

from refresh_aa import HERE, ROOT, CHECKED, load, read, write


def main():
    helpers = load("snapshot_helpers", "research/2026-10-29/build_snapshot.py")
    snap = read(ROOT / "research/2026-11-18/market-snapshot.json")
    arena, live, manual, aa = (read(HERE / name) for name in
                               ("arena.json", "livebench.json", "manual-boards.json", "aa-index-v5.json"))
    boards = {b["id"]: b for b in snap["boards"]}
    praise = {r["raw_name"]: r["score"] for r in arena["boards"]["agent_praise_complaint"]["rows"]}
    for bid, config in (("arena", "text_style_control"), ("arena_webdev", "webdev"), ("arena_agent", "agent")):
        src = arena["boards"][config]
        rows = helpers.arena_rows(src, len(src["rows"]),
            (lambda r: {"praise": praise.get(r["raw_name"]), "sessions": r["sessions"]}) if bid == "arena_agent"
            else (lambda r: {"votes": r["votes"]}))
        boards[bid].update(rows=rows, checked_at=CHECKED, source_updated_at=src["published"],
            selection=f"选录前40名及关注型号，来源全榜{src['total']}项；保留来源名次。Arena官方数据集固定版本{arena['revision'][:7]}，Meta仅闭源系列。")
    boards["livebench"].update(checked_at=CHECKED, source_updated_at=live["release"],
        version=f"LiveBench 2.0 · release {live['release']}（长程代理×2、编程与设计×1.5）",
        selection=f"{len(live['rows'])}项原始记录中选录{sum(bool(r['vendor']) for r in live['rows'])}款已识别型号。11-06题集在11-15后追加GPT-6.2 Astra / Sol；按来源静态文件与页面公式复算。",
        note="11-06题集；与10-25题集不同，不能把两期分数之差当作能力变化。Overall为加权均值；来源没有注明原生effort，不归给high或max。",
        rows=[dict(id=f"r{i}", model=r["model"], vendor=r["vendor"], score=r["overall"],
            cost_usd=r["cost_per_successful_task"], coding=r["suites"]["coding"], source_order=r["source_order"],
            configuration="页面未注明档位" + (" · 开放权重" if r["open_weights"] else ""))
            for i, r in enumerate((r for r in live["rows"] if r["vendor"]), 1)])
    scale = manual["scale"]
    boards["scale"].update(checked_at=CHECKED, source_updated_at=None,
        selection=f"来源全榜{scale['page_total']}项，选录{len(scale['rows'])}项，排除Meta开放权重型号；发布日期未披露，保留来源名次。",
        rows=[dict(id=f"r{i}", model=name, vendor=vendor, configuration="页面未注明档位", score=score,
            interval=ci, calibration_error=ce, cost_usd=None, source_rank=scale["source_ranks"][slug])
            for i, (slug, name, vendor, score, ci, ce) in enumerate(scale["rows"], 1)])
    usage = manual["openrouter"]
    boards["openrouter"].update(checked_at=CHECKED, source_updated_at=usage["usage_through"],
        version=f"Text · This Week · 截至{usage['usage_through']}的滚动7天",
        selection="来源页面Weekly usage前十；token用量不等于用户数、收入或能力排名。",
        rows=[dict(id=f"r{i}", model=name, vendor=vendor, configuration="平台全部已统计档位", score=score,
            change=change, source_rank=i, cost_usd=None) for i, (name, vendor, score, change) in enumerate(usage["rows"], 1)])
    snap["reviewed_at"] = CHECKED
    snap["changes"] = [
        {"title": "早期测试者与系统卡", "body": "多位早期测试者认为Astra 6.2难以引导、端到端任务常提前停止，正面反馈集中在3D、动效与computer use；系统卡显示其省略已知阻碍的比例约为上一代两倍，Codex提示可缓解但不用于直接API。Sol 6.2在LiveBench（80.3）与AA Coding Agent Index上略低于6.1 Sol。"},
        {"title": "Carbon 费用改按常规价", "body": "AA晚间改按12-01常规价$4 / $20计算Carbon任务费用，high升至$7.76，分数与用量不变；官方优惠仍至11-30，Argon仍按优惠价，两者不可直接比费用。"},
        {"title": "Arena 与 Scale 新快照", "body": "Arena WebDev / Agent更新至11-15，Fable 5.2仍居两榜第一，文本榜仍为11-11；均未收录GPT-6.2。Scale HLE Diamond新增Muse Ember，尚无GPT-6.2。"},
        {"title": "热度更新至 11-17", "body": "OpenRouter周用量截至11-17：DeepSeek V4.1 Flash 1017居首，腾讯Hy4 Flash新上榜第二；GPT-6.2未进前十。token用量只代表平台调用热度。"},
    ]
    snap["vendor_updates"] = [dict(u) for u in snap["vendor_updates"]]
    for source in snap["official_sources"]:
        if source["vendor"] == "Google":
            source.update(checked_at=CHECKED, note="Carbon / Argon优惠仍至11-30、12-01起$4 / $20；Hydrogen全窗口Standard价。")
    for update in snap["vendor_updates"]:
        if update["vendor"] == "OpenAI":
            update.update(slugs=["gpt-6-2-astra", "gpt-6-2-astra-xhigh", "gpt-6-2-sol", "gpt-6-2-sol-high", "gpt-6-1-terra", "gpt-6-luna"],
                          note="GPT-6.2 首日风评偏负面：早期测试者反映Astra难以引导、端到端任务常提前停止；系统卡显示其省略已知阻碍的比例约为上一代两倍，直接调API需自行要求报告阻碍。AA与LiveBench成绩及单任务费用都优于上一代。")
        elif update["vendor"] == "Google":
            update.update(note="Carbon默认medium；Hydrogen默认high、最高xhigh。AA晚间起按12-01常规价计算Carbon任务费用，Argon仍按11-30前优惠价，两者不可直接比费用。")
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
