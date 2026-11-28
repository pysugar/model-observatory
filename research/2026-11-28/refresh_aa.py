"""Freeze AA v5.0.2, joining the leaderboard and release pages by variant UUID."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREVIOUS = HERE.with_name("2026-11-21")
CHECKED = HERE.name
VERSION = "v5.0.2"
METHOD = "https://artificialanalysis.ai/methodology/intelligence-benchmarking"


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reader = load(HERE.with_name("2026-11-19") / "refresh_aa.py")
reader.CACHE = ROOT / "test-results" / f"refresh-{CHECKED}" / "aa-pages"
read, write, fetch = reader.read, reader.write, reader.fetch


def main():
    board = load(HERE.with_name("2026-10-28") / "fetch_aa_v5.py")
    series = load(HERE.with_name("2026-10-28") / "fetch_aa_v5_releases.py")
    previous = read(PREVIOUS / "aa-v5-series.json")
    releases = previous["aa_release_series"]["releases"]
    prior_board = read(PREVIOUS / "aa-index-v5.json")
    references = {r["model"] for r in prior_board["board"]["rows"]} | {"Tencent Hy4", "Inkling 2 Small", "Inkling 2 Mini"}
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
    raw_series_scores = {r["slug"]: r.get("intelligenceIndex") for r in identities.values()}
    series.fetch, series.records = fetch, reader.records
    series.EVAL_RELEASES = sorted(release_slugs)
    series.EVALS = {("Terminal-Bench 4.1" if k == "Terminal-Bench 4.0" else k):
                    (("terminalBench41", 100) if k == "Terminal-Bench 4.0" else v) for k, v in series.EVALS.items()}
    series.OUT = HERE / "aa-v5-series.json"
    series.main(release_metadata=releases, request_delay=0)
    bundle = read(series.OUT)
    measured = {v["slug"] for r in bundle["aa_release_series"]["releases"] for v in r["variants"]}
    missing = {r["releaseSlug"]: r for r in bundle["unmeasured"]}
    for row in previous["unmeasured"]:
        absent = set(row["variants"]) - measured
        if absent:
            item = missing.setdefault(row["releaseSlug"], {**row, "variants": []})
            item["variants"] = sorted(absent | set(item["variants"]))
    bundle.update(unmeasured=list(missing.values()), version=VERSION, source="Artificial Analysis release pages · " + VERSION)
    bundle["aa_effort_evals"]["source"] = bundle["source"]
    notes = {r["releaseSlug"]: r["availabilityNote"] for r in releases if r.get("availabilityNote")}
    for key, entries in (("aa_release_series", "releases"), ("aa_capability_indexes", "entries")):
        bundle[key].update(snapshot=CHECKED, version=VERSION)
        for row in bundle[key][entries]:
            slug = row["releaseSlug"]
            row["isTrackedFamily"] = slug in tracked
            if slug in notes:
                row["availabilityNote"] = notes[slug]
    for release in bundle["aa_release_series"]["releases"]:
        for variant in release["variants"]:
            raw_score = raw_series_scores[variant["slug"]]
            variant["intelligenceIndexRaw"] = raw_score
            variant["intelligenceIndexRounded"] = int(Decimal(str(raw_score)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    for d, prior in zip(bundle["aa_capability_indexes"]["domains"], previous["aa_capability_indexes"]["domains"], strict=True):
        assert d["key"] == prior["key"]
        d.update(weightNote=prior["weightNote"], coreEvals=[v.replace("Terminal-Bench 4.0", "Terminal-Bench 4.1") for v in prior["coreEvals"]])
    write(series.OUT, bundle)

    board.fetch = fetch
    board.models = lambda html: normalized
    board.SELECTION = [m["slug"] for m in normalized]
    board.UNRELEASED_WEIGHTS = set()
    del board.EVALS["terminalbench-4-0"]
    board.EVALS["terminalbench-4-1"] = "Terminal-Bench 4.1"
    board.OUT = HERE / "aa-index-v5.json"
    write(board.OUT, prior_board)
    board.main()
    doc = read(board.OUT)
    doc["pages"].extend({"url": u, "sha256": sha256(fetch(u)).hexdigest()}
                        for u in sorted({METHOD, *urls} - {series.BASE + slug for slug in release_slugs}))
    by_slug = {m["slug"]: m for m in normalized}
    for row in doc["board"]["rows"]:
        cost = by_slug[row["slug"]].get("intelligenceIndexCostPerTask")
        row["cost_usd"] = round(cost, 4) if cost is not None else None
    doc.update(checked_at=CHECKED, method="榜单与发布页按模型 UUID 匹配。五家主力系列逐档读取，另选录跨厂参照。")
    doc["board"].update(checked_at=CHECKED, version="AA 智能指数 " + VERSION,
                        selection="选录五厂已跟踪系列及跨厂参照，包括腾讯 Hy4 和 Inkling 2 Small / Mini。Meta 选录闭源系列。")
    if "muse-spark-1-3" not in by_slug:
        spark = next(r for r in identities.values() if r["slug"] == "muse-spark-1-3")
        doc = load(HERE.with_name("2026-10-31") / "refresh_aa.py").add_spark_board_row(doc, bundle, spark)
        evals = next(r["evals"] for r in doc["board"]["rows"] if r["slug"] == spark["slug"])
        del evals["Terminal-Bench 4.0"]
        score = spark["evaluationScores"].get("terminalBench41")
        evals["Terminal-Bench 4.1"] = round(score, 4) if score is not None else None
    rows = doc["board"]["rows"]
    for row in rows:
        raw_score = by_slug[row["slug"]]["intelligenceIndex"] if row["slug"] in by_slug else raw_series_scores[row["slug"]]
        row["score_raw"] = raw_score
        row["score"] = int(Decimal(str(raw_score)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        row["change"] = board.change_label(row["score"], row["prev_score"])
    rows.sort(key=lambda r: (-r["score_raw"], r["slug"]))
    for i, row in enumerate(rows, 1):
        row["id"] = f"r{i}"
    method = doc["methodology"]
    method["version"] = VERSION
    method["categories"][1]["evals"][1][0] = "Terminal-Bench 4.1"
    method["reading"] = [
        "v5 系列于 10 月 27 日发布。11 月的 v5.0.2 在 66 道终端任务上采用新版验证器，并用更新的轨迹检查与评审流程重评 FrontierCode-AA 2.0。模型沿用原有作答轨迹。",
        "本期按发布版本分别取最高综合分。单个版本的不同推理档可以同时出现在总榜前列。",
        "v4.3.2 采用另一套题集与权重。历史视图可单独查看。",
    ]
    doc["pending"] = ["GLM-5.4 已于 11-23 发布，本期 AA 总榜未列出其综合分。", "旧型号保留各自有实测的指数版本。"]
    doc["change_note"] = {
        "title": "AA 更新编程评分，终端任务切换至 Terminal-Bench 4.1",
        "body": "v5.0.2 更换了 66 道终端任务的验证器，并对 FrontierCode-AA 2.0 的已有作答重新评分。分项图、编程均值和下载表均使用新成绩。对照上期时需考虑评分变化。",
        "sources": [{"label": "AA 评测方法与版本记录", "url": METHOD}],
    }
    write(board.OUT, doc)


if __name__ == "__main__":
    main()
