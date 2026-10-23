"""Join the dated market snapshot without rewriting historical benchmark runs."""


CATALOG_NAMES = {
    "GPT-6 Astra": "GPT 6 Astra", "GPT-6.1 Sol": "GPT 6.1 Sol",
    "GPT-6 Luna": "GPT 6 Luna", "GPT-6 Sol": "GPT 6 Sol",
    "GPT-5.6 Sol": "GPT 5.6 Sol",
}


def refresh_panorama(external, snapshot):
    """Refresh only observed fields; each source retains its own date and metric."""
    boards = {board["id"]: board for board in snapshot["boards"]}
    lookups = {
        key: {CATALOG_NAMES.get(row["model"], row["model"]): row for row in boards[key]["rows"]}
        for key in ("livebench", "openrouter")
    }
    for row in external["four_family_matrix"]:
        live = lookups["livebench"].get(row["model"])
        row["livebench_2"] = (
            f'Overall {live["score"]:.1f} · ${live["cost_usd"]:.3f}/成功任务'
            if live else "本次选录未收录；不代表来源未测"
        )
        row["livebench_snapshot"] = boards["livebench"]["source_updated_at"]
        row["arena"] = "Agent Code 历史快照 2026-10-14：" + row["arena"].split(" · Text")[0]
        # Text results are kept separate from historical Agent Code observations.
        text_rows = [r for r in boards["arena"]["rows"]
                     if CATALOG_NAMES.get(r["model"], r["model"]) == row["model"]]
        if text_rows:
            text = text_rows[0]
            row["arena"] = (f'Text {boards["arena"]["source_updated_at"]}：'
                            f'{text["score"]} ±{text["interval"]} Elo · {text["configuration"]}')
        elif "Agent Code" not in row["arena"].split("：", 1)[-1]:
            row["arena"] = "本次 Text 选录未收录；旧版近似 Elo 不再作为当前成绩"
        usage = lookups["openrouter"].get(row["model"])
        row["openrouter"] = (
            f'周用量 #{usage["source_rank"]} · {usage["score"]:g}T tokens · {usage["change"]}'
            if usage else "本次周用量前十选录未收录；不表示不可用或能力较低"
        )
        row["openrouter_snapshot"] = boards["openrouter"]["source_updated_at"]
        row["scale_snapshot"] = "2026-10-19 历史选录；新核验 HLE / HSS / MultiChallenge 见下方"
        # Old cross-board recommendations relied on stale or incomparable costs.
        row["sweet_spot"] = "先按任务与原生档位查看上方选档速查，再用同一评测的成绩与费用验证；各站指标独立参考。"
        if row["model"] == "Claude Haiku 5.5":
            row["scale_seal"] = "MultiChallenge 67.67 ±5.34（当前页面序号 #8）"
            row["scale_snapshot"] = "2026-10-23 核验"
        elif row["model"] == "Gemini 4 Argon":
            row["scale_seal"] = "HSS 55.40 ±4.20；HLE Diamond 53.20 ±3.07；MultiChallenge 78.70 ±5.30"
            row["scale_snapshot"] = "2026-10-23 核验"
        elif row["model"] == "Gemini 3.8 Flash":
            row["scale_seal"] = "HSS 41.60 ±3.70（当前页面序号 #6）"
            row["scale_snapshot"] = "2026-10-23 核验"
    updates = snapshot["scale_highlight_updates"]
    for index, update in updates.items():
        external["scale_highlights"][int(index)].update(update)
    for platform in external["platforms"]:
        board = boards[platform["id"]]
        platform["url"] = board["source_url"]
        platform["snapshot"] = (f'{board["version"]} · 来源更新 {board["source_updated_at"] or "未披露"}'
                                f' · 核验 {board["checked_at"]}')
        platform["focus"] = board["metric"] + "。" + board["note"]
        platform["cost_metric"] = board["cost_basis"]
    external["reviewed_at"] = snapshot["reviewed_at"]
