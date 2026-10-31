"""Assemble the latest source-specific boards; never relabel an unread source as fresh."""

from pathlib import Path
import json

from refresh_aa import load

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CHECKED = "2026-10-31"
META = {"Muse Wonder", "Muse Wonder 1.0", "Muse Wonder Full", "Muse Spark 1.3"}


def read(path):
    return json.loads(path.read_text())


def main():
    previous = load("snapshot", "research/2026-10-29/build_snapshot.py")
    snap = read(ROOT / "research/2026-10-29/market-snapshot.json")
    arena, live, manual, aa = (read(HERE / name) for name in
                               ("arena.json", "livebench.json", "manual-boards.json", "aa-index-v5.json"))
    boards = {b["id"]: b for b in snap["boards"]}
    praise = {r["raw_name"]: r["score"] for r in arena["boards"]["agent_praise_complaint"]["rows"]}
    for bid, config in (("arena", "text_style_control"), ("arena_webdev", "webdev"), ("arena_agent", "agent")):
        src = arena["boards"][config]
        rows = previous.arena_rows(src, len(src["rows"]),
                                    (lambda r: {"praise": praise.get(r["raw_name"]), "sessions": r["sessions"]})
                                    if bid == "arena_agent" else (lambda r: {"votes": r["votes"]}))
        boards[bid].update(rows=rows, checked_at=CHECKED, source_updated_at=src["published"],
                           selection=f"选录前40名及关注型号，保留原始来源名次；来源全榜共 {src['total']} 项。"
                                     f"Arena 官方 Hugging Face 数据集固定版本 {arena['revision'][:7]}；Meta 仅闭源主流型号。")
    boards["livebench"].update(checked_at=CHECKED,
        selection="选录页面已识别的22款模型；题集仍为10-25版，成本文件于10-31重读。7款模型费用与当前网页核对。",
        rows=[dict(id=f"r{i}",model=r["model"],vendor=r["vendor"],score=r["overall"],
                   cost_usd=r["cost_per_successful_task"],coding=r["suites"]["coding"],source_order=r["source_order"],
                   configuration="页面未注明档位"+(" · 开放权重" if r["open_weights"] else ""))
              for i,r in enumerate((r for r in live["rows"] if r["vendor"]),1)])
    scale = manual["scale"]
    boards["scale"].update(checked_at=CHECKED,
        selection="来源全榜19项，选录18项；按监测范围排除Meta开放权重型号。未披露发布日期，保留来源名次。",
        rows=[dict(id=f"r{i}",model=name,vendor=vendor,configuration="页面未注明档位",score=score,
                   interval=ci,calibration_error=ce,cost_usd=None,source_rank=scale["source_ranks"][slug])
              for i,(slug,name,vendor,score,ci,ce) in enumerate(scale["rows"],1)])
    snap["reviewed_at"] = CHECKED
    snap["changes"] = [
        {"title":"Arena 三榜刷新至10-28", "body":"Carbon 新增至文本榜第一、WebDev第四、Agent Arena第二；Opus 5.5 仍领跑 WebDev 与 Agent Arena。区间重叠不代表显著领先；文本偏好、网页生成和真实会话分开看。"},
        {"title":"LiveBench 题集未变，费用已变", "body":"仍为10-25加权题集。Fable 5.1 85.7、Astra 85.6、Opus 5.5 85.1；当前每成功任务费用分别为 $7.406、$4.828、$4.820。Sol 6.1 为 $0.819、Terra 为 $0.665。旧版费用不可沿用。"},
        {"title":"五厂覆盖与访问限制", "body":"Meta 仅保留 Muse Wonder、Wonder Full、Spark 1.3 闭源系列。Wonder Full 仅 Muse Code 订阅，缺公开 API 费用；Carbon 仅限部分合作方。OpenRouter 周用量保留10-27旧快照，社区声音保留10-29复核，未冒充本期新数据。"},
    ]
    snap["highlights"][1].update(row_id="r1",caption="Text Arena · high · 10-28")
    snap["official_sources"].extend([
        {"vendor":"Meta", "url":"https://dev.meta.ai/docs/pricing-rate-limits", "checked_at":CHECKED,
         "note":"闭源Wonder / Spark 1.3 Standard；Full仅订阅；不纳入开放权重系列。"},
        {"vendor":"OpenAI · Terra", "url":"https://developers.openai.com/api/docs/models/gpt-6.1-terra", "checked_at":CHECKED,
         "note":"新增Terra Standard $1 / $0.05 / $5；长上下文阶梯单列。"},
    ])
    snap["vendor_updates"] = [
        {"vendor":"Google", "slugs":["gemini-4-carbon","gemini-4-argon","gemini-3-8-flash"],
         "note":"Carbon 成绩领先，仍仅限部分安全合作方。Argon 为公开可用参照；AA 费用采用优惠结束后的单价。", "url":"https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-carbon/"},
        {"vendor":"Meta", "slugs":["muse-wonder-full","muse-wonder","muse-spark-1-3"],
         "note":"仅监测主流闭源系列。Wonder Full 是独立型号，仅 Muse Code 指定订阅；不是 Wonder 的 max 档。Spark 1.3 以来源实际已测为准。", "url":"https://dev.meta.ai/docs/models"},
        {"vendor":"xAI", "slugs":["grok-4-7-high","grok-4-7"],
         "note":"Grok 4.7 的 high 指数略高于 xhigh、费用更低。官方支持 low / medium / high / xhigh；AA 未测 medium，不补曲线。", "url":"https://docs.x.ai/developers/models"},
        {"vendor":"OpenAI", "slugs":["gpt-6-astra","gpt-6-1-sol","gpt-6-1-terra"],
         "note":"新增 Terra 六个已测配置。none 不保证优于 low；任务、档位和费用一起比较。", "url":"https://developers.openai.com/api/docs/models"},
        {"vendor":"Anthropic", "slugs":["claude-opus-5-5","claude-opus-5-5-xhigh","claude-sonnet-5-5","claude-haiku-5-5"],
         "note":"补齐此前遗漏的 Opus xhigh。Opus / Sonnet / Fable 的 AA 配置含默认护栏回退，保留来源标记。", "url":"https://www.anthropic.com/news/models"},
    ]
    previous.FOCUS += [("Gemini 4 Carbon",["Gemini 4 Carbon"]),("GPT-6.1 Terra",["GPT-6.1 Terra"]),
                       ("Muse Wonder",["Muse Wonder","Muse Wonder 1.0"]),("Muse Wonder Full",["Muse Wonder Full"]),
                       ("Muse Spark 1.3",["Muse Spark 1.3"])]
    snap["cross_source"] = previous.cross_source(arena,live,manual,aa)
    snap["cross_source"]["note"] = snap["cross_source"]["note"].replace("14 款","19 款")
    (HERE / "market-snapshot.json").write_text(json.dumps(snap,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({b["id"]:len(b["rows"]) for b in snap["boards"]}))


if __name__ == "__main__":
    main()
