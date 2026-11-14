"""Refresh AA v5 from public pages, adapting the November embedded-data schema.

Raw responses stay in the ignored task cache. Published snapshots record URLs and
SHA-256 hashes; historical research inputs are never overwritten.
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import importlib.util
import json
import re
from urllib.request import Request, urlopen
from urllib.error import URLError

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREVIOUS = ROOT / "research/2026-10-31"
CHECKED = "2026-11-15"
CACHE = ROOT / "test-results/refresh-2026-11-15/aa-pages"
VENDORS = {"Google", "Meta", "xAI", "SpaceXAI", "OpenAI", "Anthropic"}
META_RELEASES = {"muse-wonder", "muse-wonder-full", "muse-spark-1-3", "muse-ember"}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def fetch(url):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest() + ".html")
    if not path.exists():
        request = Request(url, headers={"User-Agent": "model-observatory-research/1.0 (+https://github.com/pysugar/model-observatory)"})
        for attempt in range(2):
            try:
                with urlopen(request, timeout=45) as response:
                    path.write_bytes(response.read())
                break
            except (URLError, TimeoutError) as error:
                if attempt:
                    raise RuntimeError(f"Could not read {url}: {error}") from error
        print("Cached " + url, flush=True)
    return path.read_bytes()


def records(data):
    """Read explicit model identities; never derive a variant slug from its label."""
    found = {}
    for match in re.finditer(r'"initialModels":', data):
        models = json.JSONDecoder().raw_decode(data[match.end():].lstrip())[0]
        for model in models:
            if not model.get("slug"):
                continue
            item = dict(model)
            item["capabilityScores"] = model.get("capabilities", {})
            item["evaluationScores"] = {**model, "briefcaseElo":
                ((model.get("briefcaseBreakdown") or {}).get("overall") or {}).get("elo")}
            item["medianOutputSpeed"] = (model.get("headline") or {}).get("outputSpeed")
            item["timeToFirstAnswerToken"] = {"total": (model.get("headline") or {}).get("timeToFirstAnswerToken")}
            found.setdefault(item["slug"], item)
    return list(found.values())


def main():
    board = load("aa_board", "research/2026-10-28/fetch_aa_v5.py")
    series = load("aa_series", "research/2026-10-28/fetch_aa_v5_releases.py")
    old = load("aa_previous", "research/2026-10-31/refresh_aa.py")
    previous = read(PREVIOUS / "aa-v5-series.json")
    metadata = previous["aa_release_series"]["releases"]
    for slug, name, short, vendor, color, date, context in [
        ("claude-fable-5-2", "Claude Fable 5.2", "Fable 5.2", "Anthropic", "#793919", "2026-11-09", 1000000),
        ("gemini-4-hydrogen", "Gemini 4 Hydrogen", "Hydrogen", "Google", "#2867c9", "2026-11-12", 1048576),
        ("muse-ember", "Muse Ember", "Ember", "Meta", "#0284c7", None, 1048576),
    ]:
        metadata.append(dict(releaseSlug=slug, name=name, aaReleaseName=name, shortName=short,
                             vendor=vendor, color=color, isFourFamily=vendor != "Meta", isCurrent=True,
                             releaseDate=date, contextWindowTokens=context, variants=[]))
    urls = [series.BASE + r["releaseSlug"] for r in metadata]
    with ThreadPoolExecutor(max_workers=5) as executor:
        bodies = list(executor.map(fetch, urls))
    pool = {}
    for body in bodies:
        for record in records(series.flight_data(body.decode())):
            pool.setdefault(record["id"], record)
    for meta in metadata:
        observed = next((r for r in pool.values() if r["release"]["slug"] == meta["releaseSlug"]), None)
        if observed and meta["releaseDate"] is None:
            meta["releaseDate"] = observed["releaseDate"]
    series.fetch, series.records = fetch, records
    series.OUT = HERE / "aa-v5-series.json"
    series.EVAL_RELEASES = [r["releaseSlug"] for r in metadata if r["vendor"] in VENDORS]
    series.main(release_metadata=metadata, request_delay=0)

    body = fetch(board.LEADERBOARD)
    models = board.models(body.decode())
    previous_board = read(PREVIOUS / "aa-index-v5.json")["board"]["rows"]
    reference_names = {r["model"] for r in previous_board}
    identity_urls = sorted({series.BASE + m["release"]["slug"] for m in models
        if m["id"] not in pool and board.split_name(m["name"])[0] in reference_names})
    for url in identity_urls:
        for record in records(series.flight_data(fetch(url).decode())):
            pool.setdefault(record["id"], record)
    normalized = []
    missing = []
    reference = {r["slug"] for r in read(PREVIOUS / "aa-index-v5.json")["board"]["rows"]}
    tracked_releases = {r["releaseSlug"] for r in metadata if r["vendor"] in VENDORS}
    for model in models:
        identity = pool.get(model["id"])
        tracked = model["release"]["slug"] in tracked_releases
        if identity:
            normalized.append({**model, "slug": identity["slug"], "medianOutputTokensPerSecond": model.get("outputSpeed")})
        elif tracked and model.get("intelligenceIndex") is not None:
            missing.append(model["name"])
    if missing:
        raise ValueError(f"Missing explicit AA identities: {missing}")
    selected = {m["slug"] for m in normalized if m.get("intelligenceIndex") is not None and
                (m["release"]["slug"] in tracked_releases or m["slug"] in reference or
                 board.split_name(m["name"])[0] in reference_names)}
    board.models = lambda html: normalized
    board.fetch = fetch
    board.SELECTION = sorted(selected)
    board.OUT = HERE / "aa-index-v5.json"
    write(board.OUT, read(PREVIOUS / "aa-index-v5.json"))
    board.main()
    doc = read(board.OUT)
    doc["pages"].extend({"url":url,"sha256":hashlib.sha256(fetch(url)).hexdigest(),
                         "note":"Explicit variant identity for a retained reference model"} for url in identity_urls)
    by_slug = {m["slug"]: m for m in normalized}
    for row in doc["board"]["rows"]:
        model = by_slug[row["slug"]]
        cost = model.get("intelligenceIndexCostPerTask")
        row["cost_usd"] = round(cost, 4) if cost is not None else None
    doc.update(checked_at=CHECKED)
    doc["method"] = "11-15从AA公开榜单与发布版本页内嵌数据重建；通过显式UUID关联变体slug，适配11月capabilities与根级子评测字段。当前榜单缺少的Spark 1.3 max仅用本期发布页补入。原始响应保留URL和SHA-256；未测不从历史v4.3.2补值。"
    doc["board"].update(checked_at=CHECKED, source_updated_at=None,
        selection="选录五家厂商当前榜单的已测 v5 配置，并保留既有其他厂商参照；不是完整全球榜。Meta 仅主流闭源系列。整数按 AA 显示，CSV 保留原值、费用、速度与子评测。",
        note="v5 四类各占25%，约60%权重来自私有或答案不公开的评测。新旧指数不能直接比较。Carbon 已开放付费 API；Carbon / Argon 本期 AA 费用按当前优惠价 $2 / $10，12-01 起官方单价翻倍。Wonder Full 仍无公开 API 费用。")
    doc["pending"] = ["未重测的旧型号和档位不从 v4.3.2 补值。Fable 5.1已不在当前榜单，已测曲线仍保留在发布版本与档案。", "Mythos 5.2 访问受限且无本期独立 AA 成绩；不复制 Fable 成绩。", "社区观点保留10-29核对日期，不延用到新型号。"]
    doc["change_note"] = {"title":"11月模型刷新：Fable 5.2、Hydrogen 与 Ember",
        "body":"新增三款模型的已测档位；Carbon 从受限观察转为公开 API 候选，并补齐 low / medium / high。AA 成绩和任务费用均重新读取；不同档位的收益与费用请结合任务查看。"}
    series_doc = read(series.OUT)
    current_slugs = {v["slug"] for r in series_doc["aa_release_series"]["releases"] for v in r["variants"]}
    for item in previous["unmeasured"]:
        remaining = [slug for slug in item["variants"] if slug not in current_slugs]
        if remaining and not any(u["releaseSlug"] == item["releaseSlug"] for u in series_doc["unmeasured"]):
            series_doc["unmeasured"].append({**item, "variants":remaining, "last_checked_at":"2026-10-31"})
    for key, items in (("aa_release_series", "releases"), ("aa_capability_indexes", "entries")):
        series_doc[key]["snapshot"] = CHECKED
        for item in series_doc[key][items]:
            item["isTrackedFamily"] = item["vendor"] in VENDORS
            if item["releaseSlug"] == "gemini-4-carbon":
                item["availabilityNote"] = "已开放付费 API；11-30 前优惠价，12-01 起恢复常规价"
            elif item["releaseSlug"] == "muse-wonder-full":
                item["availabilityNote"] = "仅 Muse Code；无公开 API 费用"
    if not any(r["releaseSlug"] == "muse-wonder-full" for r in series_doc["aa_release_series"]["releases"]):
        series_doc = old.add_single_point(series_doc, normalized)
        series_doc["pages"][-1]["sha256"] = hashlib.sha256(body).hexdigest()
    # A missing board point may be supplemented only by the current release page.
    if "muse-spark-1-3" not in selected:
        spark = next(r for r in pool.values() if r["slug"] == "muse-spark-1-3")
        doc = old.add_spark_board_row(doc, series_doc, spark)
    write(series.OUT, series_doc)
    write(board.OUT, doc)
    print(json.dumps({"board":len(doc["board"]["rows"]), "releases":len(series_doc["aa_release_series"]["releases"])}))


if __name__ == "__main__":
    main()
