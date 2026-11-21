"""Freeze the November 21 AA board and release pages using their explicit identities."""

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREVIOUS = HERE.with_name("2026-11-19")
CHECKED = HERE.name


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reader = load(PREVIOUS / "refresh_aa.py")
reader.CACHE = ROOT / "test-results" / f"refresh-{CHECKED}" / "aa-pages"
read, write, fetch = reader.read, reader.write, reader.fetch


def main():
    board = load(HERE.with_name("2026-10-28") / "fetch_aa_v5.py")
    series = load(HERE.with_name("2026-10-28") / "fetch_aa_v5_releases.py")
    previous = read(PREVIOUS / "aa-v5-series.json")
    releases = previous["aa_release_series"]["releases"]
    prior_board = read(PREVIOUS / "aa-index-v5.json")
    references = {r["model"] for r in prior_board["board"]["rows"]} | {"Qwen4 Max"}
    tracked = {r["releaseSlug"] for r in releases if r["isTrackedFamily"]}
    models = board.models(fetch(board.LEADERBOARD).decode())
    selected = [m for m in models if m.get("intelligenceIndex") is not None and
                (m["release"]["slug"] in tracked or board.split_name(m["name"])[0] in references)]
    release_slugs = {r["releaseSlug"] for r in releases}
    urls = sorted({series.BASE + slug for slug in release_slugs | {m["release"]["slug"] for m in selected}})
    with ThreadPoolExecutor(max_workers=5) as executor:
        bodies = dict(zip(urls, executor.map(fetch, urls)))
    identities = {}
    for body in bodies.values():
        for record in reader.records(series.flight_data(body.decode())):
            identities[record["id"]] = record
    normalized = []
    for model in selected:
        record = identities[model["id"]]
        if record["release"]["slug"] != model["release"]["slug"]:
            raise ValueError(f"Release mismatch for {model['name']}")
        normalized.append({**model, "slug": record["slug"], "medianOutputTokensPerSecond": model.get("outputSpeed")})

    series.fetch, series.records = fetch, reader.records
    series.EVAL_RELEASES = sorted(release_slugs)
    economics_evals, _ = series.DOMAINS_V5["economics"]
    series.DOMAINS_V5["economics"] = (economics_evals, "知识30% · 代理知识工作30% · 推理25% · 长上下文15%")
    series.OUT = HERE / "aa-v5-series.json"
    series.main(release_metadata=releases, request_delay=0)
    result = read(series.OUT)
    measured = {v["slug"] for r in result["aa_release_series"]["releases"] for v in r["variants"]}
    missing = {u["releaseSlug"]: u for u in result["unmeasured"]}
    for row in previous["unmeasured"]:
        remaining = sorted(set(row["variants"]) - measured)
        if remaining and row["releaseSlug"] not in missing:
            result["unmeasured"].append({**row, "variants": remaining})
    notes = {r["releaseSlug"]: r["availabilityNote"] for r in releases if r.get("availabilityNote")}
    for slug in ("gemini-4-argon", "gemini-4-carbon"):
        source = next(r for r in identities.values() if r["slug"] == slug)
        if (source["price1mInputTokens"], source["price1mOutputTokens"]) != (4, 20):
            raise ValueError(f"Recheck AA pricing for {slug}")
        notes[slug] = "已开放付费 API，AA 按 12-01 常规价 $4 / $20 计费，Google 官方优惠价 $2 / $10 适用至 11-30"
    for key, entries in (("aa_release_series", "releases"), ("aa_capability_indexes", "entries")):
        result[key]["snapshot"] = CHECKED
        for row in result[key][entries]:
            slug = row["releaseSlug"]
            row["isTrackedFamily"] = slug in tracked
            if slug in notes:
                row["availabilityNote"] = notes[slug]
    write(series.OUT, result)

    board.fetch = fetch
    board.models = lambda html: normalized
    board.SELECTION = [m["slug"] for m in normalized]
    board.UNRELEASED_WEIGHTS = set()  # Kimi K3.1 Pro weights are in Moonshot's official repository.
    board.OUT = HERE / "aa-index-v5.json"
    write(board.OUT, prior_board)
    board.main()
    doc = read(board.OUT)
    extra_urls = set(urls) - {series.BASE + slug for slug in release_slugs}
    doc["pages"].extend({"url": url, "sha256": sha256(bodies[url]).hexdigest()} for url in sorted(extra_urls))
    costs = {m["slug"]: m.get("intelligenceIndexCostPerTask") for m in normalized}
    for row in doc["board"]["rows"]:
        cost = costs[row["slug"]]
        row["cost_usd"] = round(cost, 4) if cost is not None else None
    doc.update(checked_at=CHECKED, method="按 AA 榜单 UUID 关联发布页档位。五家主力系列逐档读取，另选录跨厂参照；费用保留四位小数。")
    doc["methodology"]["reading"][1] = (
        "AA 在 10-27 发布 v5 时观察到开放权重模型与当时榜首的分差扩大。"
        "截至 11-21，Moonshot 已发布 Kimi K3.1 Pro 权重，该模型在本期 AA v5 得 46.45 分。"
    )
    doc["board"].update(
        checked_at=CHECKED, source_updated_at=None,
        selection="选录五厂已跟踪系列及跨厂参照（含 Qwen4 Max）。Meta 仅选闭源系列。",
        note="AA v5 的四类任务各占 25%。本期 Argon 与 Carbon 均按 $4 / $20 常规价计算任务费用，Google 官方优惠至 11-30，12-01 起执行常规价。Wonder Full 缺少公开 API 费用。",
    )
    if "muse-spark-1-3" not in costs:
        spark = next(r for r in identities.values() if r["slug"] == "muse-spark-1-3")
        doc = load(HERE.with_name("2026-10-31") / "refresh_aa.py").add_spark_board_row(doc, result, spark)
    doc["pending"] = [
        "旧型号只在有 v5 实测的发布页保留曲线；v4.3.2 可在页首单独查看。",
        "Gemini 4 Neon 已进入 LiveBench 和 Scale HSS。Scale HLE Diamond 及 ARC Prize 官方结果页尚未列出 Neon。",
    ]
    doc["change_note"] = {
        "title": "Gemini 4 Neon 登上 LiveBench 首位",
        "body": "11-06 题集补录 Neon 后，其综合得分为 87.4，每成功任务 $2.654。Fable 5.2 和 GPT-6.2 Astra 的显示分均为 84.9，每成功任务分别为 $9.850 和 $1.941。榜单未披露三者的推理档位。",
        "sources": [{"label": "LiveBench 2.0", "url": "https://livebench.ai/"}],
    }
    write(board.OUT, doc)


if __name__ == "__main__":
    main()
