"""Refresh the five vendors on AA v5, preserving the earlier dated snapshots.

Meta scope is deliberately limited to its mainstream closed-weight Muse models.
Run from the repository root: python3 research/2026-10-31/refresh_aa.py
"""

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VENDORS = {"Google", "Meta", "xAI", "SpaceXAI", "OpenAI", "Anthropic"}
META_MODELS = {"muse-wonder", "muse-wonder-full", "muse-spark-1-3", "muse-spark-1-3-xhigh"}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def add_single_point(doc, models):
    """Wonder Full has no release-page record; preserve the measured leaderboard point.

    No capability indices, timing, token usage or cost are inferred for this model.
    """
    m = next(m for m in models if m["slug"] == "muse-wonder-full")
    scores = m["scores"]
    mappings = {"AA-Briefcase v1.1": ("aa-briefcase",1), "AutomationBench-AA": ("automationbench-aa",100),
                "GDP.pdf": ("gdp-pdf",100), "FrontierCode 2.0": ("frontiercode-2-0",100),
                "Terminal-Bench 4.0": ("terminalbench-4-0",100), "Terminal-Bench-Science": ("terminal-bench-science",100),
                "CritPt v2 hard": ("critpt-v2-hard",100), "HLE-Diamond": ("hle-diamond",100)}
    metrics = {label:round(scores[key]*scale,2) for label,(key,scale) in mappings.items()}
    metrics.update({"Intelligence Index":round(m["intelligenceIndex"],2), "AA-Omniscience v1.1":m["omniscience"]})
    v = dict(slug=m["slug"],name=m["name"],shortName=m["shortName"],effort="max",effortOrder=6,
             intelligenceIndex=metrics["Intelligence Index"],intelligenceIndexRounded=int(m["intelligenceIndex"]+0.5),costPerTask=None,
             costBreakdown={},costTotalRun=None,timePerTaskSeconds=None,timePerTaskMinutes=None,
             outputTokensPerTask=None,outputTokensBreakdown={},outputSpeed=None,ttfaSeconds=None,
             capabilities={},hasFallback=False,fallbackLabel=None,isTopVariant=True)
    release = dict(releaseSlug=m["slug"],name="Muse Wonder Full",aaReleaseName="Muse Wonder Full",shortName="Wonder Full",
                   vendor="Meta",color="#0284c7",isFourFamily=False,isCurrent=True,isTrackedFamily=True,
                   releaseDate="2026-10-12",contextWindowTokens=m["contextWindowTokens"],modelCount=1,
                   maxIntelligenceIndex=v["intelligenceIndex"],minCostPerTask=None,maxCostPerTask=None,
                   strengthsGlobalRank={},sourceUrl="https://artificialanalysis.ai/leaderboards/models",
                   availabilityNote="仅 Muse Code；无公开 API 费用",variants=[v])
    doc["aa_release_series"]["releases"] = [r for r in doc["aa_release_series"]["releases"] if r["releaseSlug"] != m["slug"]] + [release]
    doc["aa_effort_evals"]["variants"][m["slug"]] = dict(slug=m["slug"],releaseSlug=m["slug"],model=release["name"],
        vendor="Meta",effort="max",effortOrder=6,source_url=release["sourceUrl"],metrics=metrics)
    doc["pages"].append({"url":release["sourceUrl"],"note":"Wonder Full single point and v5 subevaluations from the embedded leaderboard model list"})
    return doc


def add_spark_board_row(board, series, record):
    """Carry the measured release-page point through the board and cross-source table."""
    rel = next(r for r in series["aa_release_series"]["releases"] if r["releaseSlug"] == "muse-spark-1-3")
    v = next(v for v in rel["variants"] if v["slug"] == "muse-spark-1-3")
    raw = record["evaluationScores"]
    mapping = {"AA-Briefcase (Elo)":("briefcaseElo",1), "AutomationBench-AA":("automationBenchPartialScore",1),
               "GDP.pdf":("gdpPdfAllPass",1), "FrontierCode 2.0":("frontierCode20",1),
               "Terminal-Bench 4.0":("terminalBench40",1), "Terminal-Bench-Science":("terminalBenchScience",1),
               "CritPt v2 hard":("critptAgenticHard",1), "AA-Omniscience 准确率":("omniscienceAccuracy",1),
               "HLE-Diamond":("hleDiamond",1)}
    evals = {label:round(raw[key]*scale,4) for label,(key,scale) in mapping.items()}
    evals["AA-Omniscience 不幻觉率"] = round(1-raw["omniscienceHallucinationRate"],4)
    row = dict(slug=v["slug"],model=rel["name"],vendor="Meta",configuration="max · 发布页补充",
               score=v["intelligenceIndexRounded"],score_exact=v["intelligenceIndex"],prev_score=None,
               change="旧选录无此档",cost_usd=v["costPerTask"],output_tps=v["outputSpeed"],open_weights=False,
               evals=evals,source_url=rel["sourceUrl"])
    rows = [r for r in board["board"]["rows"] if r["slug"] != row["slug"]] + [row]
    rows.sort(key=lambda r:(-r["score_exact"],r["slug"]))
    for i,r in enumerate(rows,1):
        r["id"] = f"r{i}"
    board["board"]["rows"] = rows
    page = next(p for p in series["pages"] if p["url"] == rel["sourceUrl"])
    board["pages"] = [p for p in board["pages"] if p["url"] != page["url"]] + [page]
    board["board"]["selection"] += " Spark 1.3 max 以同版发布页补充，行内及CSV单独保留来源。"
    return board


def main():
    board = load("aa_board", "research/2026-10-28/fetch_aa_v5.py")
    series = load("aa_series", "research/2026-10-28/fetch_aa_v5_releases.py")
    # Keep other vendors' existing reference models; include every scored configuration
    # of the five tracked vendors, without bringing Meta's open-weight models into scope.
    body = board.fetch(board.LEADERBOARD)
    models = board.models(body.decode())
    # Scores, costs and the recorded hash must come from the very same response.
    fetch_board = board.fetch
    board.fetch = lambda url: body if url == board.LEADERBOARD else fetch_board(url)
    selected = {m["slug"] for m in models if m.get("intelligenceIndex") is not None
                and m["modelCreatorName"] in VENDORS
                and (m["modelCreatorName"] != "Meta" or m["slug"] in META_MODELS)}
    board.SELECTION = sorted(selected | set(board.SELECTION))
    board.OUT = HERE / "aa-index-v5.json"
    board.OUT.write_text((ROOT / "research/2026-10-28/aa-index-v5.json").read_text())
    board.main()
    doc = json.loads(board.OUT.read_text())
    current = {m["slug"]: m for m in models}
    for row in doc["board"]["rows"]:
        cost = current[row["slug"]].get("intelligenceIndexCostPerTask")
        row["cost_usd"] = round(cost, 4) if cost is not None else None
    doc["board"].update(
        checked_at="2026-10-31", source_updated_at=None,
        selection="选录五家厂商当前榜单全部已测 v5 配置，并保留其他厂商的既有参照；不是完整全球榜。"
                  "Meta 仅纳入 Muse Wonder / Wonder Full / Spark 1.3 闭源系列，未测不补值。"
                  "整数按 AA 显示，CSV 保留原值、费用、速度与子评测；较 v4.3.2 为口径变化，不是能力增减。",
        note="v5 约 60% 权重来自私有或答案不公开的评测，四类各 25%。新旧分数不能直接比较。"
             "Gemini 4 Carbon 目前仅限部分安全合作方；Wonder Full 仅在 Muse Code 提供，无公开 API 任务费用。"
             "Gemini 4 Argon 的 AA 费用采用 12-01 后 $4 / $20，11-30 前优惠价约一半。"
             "本期重读未发现既有配置分数变化；新增 Carbon 与此前遗漏的档位。",
    )
    doc["pending"] = [
        "Kimi K3 未在当前 v5 榜单选录；不从旧指数补值。",
        "Meta 仅监测主流闭源系列；Spark 1.3 的 v5 max 取自发布版本页，xhigh 未重测，不从旧版补值。",
        "Carbon 的公开 API 规格与正式开放时间尚未确认；榜单成绩不表示普遍可调用。",
    ]
    doc["change_note"] = {
        "title": "AA v5 刷新：Carbon 领先，五厂档位补齐",
        "body": "10-31 读取当前榜单：Carbon high 59.43，Opus 5.5 max 58.41，Astra max 56.85。"
                "新增此前遗漏的 Opus xhigh 与 Terra 全档位，Meta 仅保留主流闭源模型。"
                "Carbon 访问受限；新旧指数不能直接比较。",
    }
    board.OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")

    metadata = json.loads(series.V4.read_text())["aa_release_series"]["releases"]
    extra = [
        ("gemini-4-carbon", "Gemini 4 Carbon", "Carbon", "Google", "#2867c9", "2026-10-28", 1048576),
        ("gpt-6-1-terra", "GPT-6.1 Terra", "Terra 6.1", "OpenAI", "#0d9488", "2026-10-26", 1050000),
        ("muse-wonder-full", "Muse Wonder Full", "Wonder Full", "Meta", "#0284c7", "2026-10-12", 1048576),
    ]
    for slug, name, short, vendor, color, date, context in extra:
        metadata.append(dict(releaseSlug=slug, name=name, aaReleaseName=name, shortName=short,
                             vendor=vendor, color=color, isFourFamily=vendor != "Meta", isCurrent=True,
                             releaseDate=date, contextWindowTokens=context, variants=[]))
    series.OUT = HERE / "aa-v5-series.json"
    series.EVAL_RELEASES = [r["releaseSlug"] for r in metadata if r["vendor"] in VENDORS and r["isCurrent"]]
    cache = ROOT / "test-results/refresh-2026-10-31/aa-pages"
    cache.mkdir(parents=True, exist_ok=True)
    fetch = series.fetch

    def cached(url):
        path = cache / (url.rsplit("/", 1)[-1] + ".html")
        if not path.exists():
            path.write_bytes(fetch(url))
        return path.read_bytes()

    urls = [series.BASE + r["releaseSlug"] for r in metadata]
    # Bounded parallel reads; the existing parser and version separation stay unchanged.
    with ThreadPoolExecutor(max_workers=6) as executor:
        for url, _ in zip(urls, executor.map(cached, urls)):
            print("Cached " + url.rsplit("/", 1)[-1], flush=True)
    series.fetch = cached
    series.main(release_metadata=metadata, request_delay=0)
    doc = json.loads(series.OUT.read_text())
    for key in ("aa_release_series", "aa_capability_indexes"):
        items = doc[key]["releases" if key == "aa_release_series" else "entries"]
        for item in items:
            item["isTrackedFamily"] = item["vendor"] in VENDORS
            if item.get("releaseSlug") == "gemini-4-carbon":
                item["availabilityNote"] = "仅向部分安全合作方开放"
            elif item.get("releaseSlug") == "muse-wonder-full":
                item["availabilityNote"] = "仅 Muse Code；无公开 API 费用"
    doc = add_single_point(doc, models)
    doc["pages"][-1]["sha256"] = next(p["sha256"] for p in json.loads(board.OUT.read_text())["pages"] if p["url"] == board.LEADERBOARD)
    series.OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    spark = next(r for r in series.records(series.flight_data(cached(series.BASE + "muse-spark-1-3").decode()))
                 if r["slug"] == "muse-spark-1-3")
    board_doc = add_spark_board_row(json.loads(board.OUT.read_text()), doc, spark)
    board.OUT.write_text(json.dumps(board_doc, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
