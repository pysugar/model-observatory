"""Assemble source-specific November observations without rewriting old evidence."""

from refresh_aa import HERE, ROOT, PREVIOUS, CHECKED, load, read, write


def main():
    helpers = load("snapshot_helpers", "research/2026-10-29/build_snapshot.py")
    snap = read(PREVIOUS / "market-snapshot.json")
    arena, live, manual, aa = (read(HERE / name) for name in
                               ("arena.json", "livebench.json", "manual-boards.json", "aa-index-v5.json"))
    boards = {b["id"]: b for b in snap["boards"]}
    praise = {r["raw_name"]:r["score"] for r in arena["boards"]["agent_praise_complaint"]["rows"]}
    for bid, config in (("arena","text_style_control"),("arena_webdev","webdev"),("arena_agent","agent")):
        src = arena["boards"][config]
        rows = helpers.arena_rows(src,len(src["rows"]),
            (lambda r:{"praise":praise.get(r["raw_name"]),"sessions":r["sessions"]}) if bid == "arena_agent"
            else (lambda r:{"votes":r["votes"]}))
        boards[bid].update(rows=rows,checked_at=CHECKED,source_updated_at=src["published"],
            selection=f"选录前40名及关注型号，来源全榜{src['total']}项；保留来源名次。Arena官方数据集固定版本{arena['revision'][:7]}，Meta仅闭源系列。")
    boards["livebench"].update(checked_at=CHECKED,source_updated_at=live["release"],
        version=f"LiveBench 2.0 · release {live['release']}（长程代理×2、编程与设计×1.5）",
        selection=f"35项原始记录中选录{sum(bool(r['vendor']) for r in live['rows'])}款已识别型号。按来源静态文件与页面公式复算，成绩与费用保留本期快照。",
        note="11-06题集；与10-25题集不同，不能把两期分数之差当作能力变化。Overall为加权均值；来源没有注明原生effort，不归给high或max。",
        rows=[dict(id=f"r{i}",model=r["model"],vendor=r["vendor"],score=r["overall"],
            cost_usd=r["cost_per_successful_task"],coding=r["suites"]["coding"],source_order=r["source_order"],
            configuration="页面未注明档位"+(" · 开放权重" if r["open_weights"] else ""))
            for i,r in enumerate((r for r in live["rows"] if r["vendor"]),1)])
    scale = manual["scale"]
    boards["scale"].update(checked_at=CHECKED,source_updated_at=None,
        selection=f"来源全榜{scale['page_total']}项，选录{len(scale['rows'])}项，排除Meta开放权重型号；发布日期未披露，保留来源名次。",
        rows=[dict(id=f"r{i}",model=name,vendor=vendor,configuration="页面未注明档位",score=score,
            interval=ci,calibration_error=ce,cost_usd=None,source_rank=scale["source_ranks"][slug])
            for i,(slug,name,vendor,score,ci,ce) in enumerate(scale["rows"],1)])
    usage = manual["openrouter"]
    boards["openrouter"].update(checked_at=CHECKED,source_updated_at=usage["usage_through"],
        version=f"Text · This Week · 截至{usage['usage_through']}的滚动7天",
        selection="来源页面Weekly usage前十；token用量不等于用户数、收入或能力排名。",
        rows=[dict(id=f"r{i}",model=name,vendor=vendor,configuration="平台全部已统计档位",score=score,
            change=change,source_rank=i,cost_usd=None) for i,(name,vendor,score,change) in enumerate(usage["rows"],1)])
    snap["reviewed_at"] = CHECKED
    snap["changes"] = [
        {"title":"Arena与Scale新增Fable 5.2", "body":"Arena 11-11发布：Carbon high领先文本榜，Fable 5.2 xhigh / max分别领先WebDev / Agent Arena。Scale HLE Diamond新增Fable 5.2 72.4±2.8%；各协议独立，不与AA的同名子评测混用。"},
        {"title":"LiveBench升级为11-06题集", "body":"Fable 5.2 84.9 / $9.850、Astra 84.4 / $5.318、Carbon 83.5 / $2.023；费用为每成功任务。新题集与10-25不同，不直接计算涨跌。"},
        {"title":"价格与访问状态同步", "body":"Carbon已开放；Carbon / Argon优惠均至11-30，12-01单价翻倍。Fable 5.2 Standard降至$8 / $40；Ember低价但>200k输入整次三倍计价。Mythos 5.2仍需机构验证。"},
        {"title":"热度与社区分别保留日期", "body":"OpenRouter周用量更新至11-13；社区声音仍为10-29核对，不借用旧型号观点说明新型号。OpenAI / xAI通用主力未发现新代际，专用安全、生命科学及生成模型不纳入通用排名。"},
    ]
    snap["highlights"][1].update(row_id="r1",caption="Text Arena · high · 11-11")
    snap["official_sources"] = [
        dict(vendor="Google",url="https://aistudio.google.com/docs/pricing",checked_at=CHECKED,note="Carbon / Argon当前优惠与12-01常规价；Hydrogen全窗口Standard价。"),
        dict(vendor="Anthropic",url="https://platform.claude.com/docs/en/about-claude/pricing",checked_at=CHECKED,note="Fable 5.2与当前主力Standard价；Fast另列；Mythos需验证机构。"),
        dict(vendor="OpenAI",url="https://developers.openai.com/api/docs/pricing",checked_at=CHECKED,note="Astra / Sol 6.1 / Terra 6.1 / Luna Standard价；不混入Fast和领域受限型号。"),
        dict(vendor="Meta",url="https://dev.meta.ai/docs/pricing-rate-limits",checked_at=CHECKED,note="闭源Wonder / Spark / Ember Standard；Ember长上下文阈值单列。"),
        dict(vendor="xAI",url="https://docs.x.ai/developers/release-notes",checked_at=CHECKED,note="通用主力仍为Grok 4.7；现有单价保留逐模型核对日期。"),
    ]
    snap["vendor_updates"] = [
        dict(vendor="OpenAI",slugs=["gpt-6-astra","gpt-6-1-sol","gpt-6-1-terra","gpt-6-luna"],note="通用主力系列保持；重新读取成绩与任务费用。Terra视觉执行、Sol综合任务与Astra难题各按任务比较。",url="https://developers.openai.com/api/docs/models"),
        dict(vendor="Anthropic",slugs=["claude-fable-5-2","claude-fable-5-2-high","claude-opus-5-5","claude-sonnet-5-5"],note="Fable 5.2新增五档，API默认high、应用默认medium；max分数最高但费用显著更高。保留AA默认回退标记；Mythos独立受限。",url="https://www.anthropic.com/claude-fable-and-mythos-5-2"),
        dict(vendor="Google",slugs=["gemini-4-carbon","gemini-4-carbon-medium","gemini-4-hydrogen","gemini-4-hydrogen-high"],note="Carbon已公开，默认medium；Hydrogen默认high、最高xhigh。AA任务费用采用当前优惠价，12-01预算要另看。",url="https://aistudio.google.com/docs/models"),
        dict(vendor="xAI",slugs=["grok-4-7-high","grok-4-7"],note="Grok 4.7本期xhigh指数已略高于high，同时更贵；旧版high领先的结论不沿用。medium仍缺AA同协议成绩。",url="https://docs.x.ai/developers/models"),
        dict(vendor="Meta",slugs=["muse-wonder-full","muse-wonder","muse-spark-1-3","muse-ember","muse-ember-xhigh"],note="新增闭源Ember，默认max、目前只测xhigh / max；>200k整次三倍价。Wonder Full仍仅Muse Code，无API费用。",url="https://dev.meta.ai/docs/models"),
    ]
    helpers.FOCUS += [("Gemini 4 Carbon",["Gemini 4 Carbon"]),("GPT-6.1 Terra",["GPT-6.1 Terra"]),
        ("Muse Wonder",["Muse Wonder","Muse Wonder 1.0"]),("Muse Wonder Full",["Muse Wonder Full"]),
        ("Muse Spark 1.3",["Muse Spark 1.3"]),("Claude Fable 5.2",["Claude Fable 5.2"]),
        ("Gemini 4 Hydrogen",["Gemini 4 Hydrogen"]),("Muse Ember",["Muse Ember","Muse Ember 1.0"])]
    snap["cross_source"] = helpers.cross_source(arena,live,manual,aa)
    snap["cross_source"]["note"] = snap["cross_source"]["note"].replace("14 款",str(len(helpers.FOCUS))+" 款")
    write(HERE / "market-snapshot.json",snap)
    print({b["id"]:len(b["rows"]) for b in snap["boards"]})


if __name__ == "__main__":
    main()
