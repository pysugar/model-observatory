"""Keep current observations distinct from frozen experiments and unknown values."""

import json
from pathlib import Path
import subprocess
import unittest
from urllib.parse import urlsplit
import sys
from decimal import Decimal, ROUND_HALF_UP

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build_report import CURRENT_RESEARCH
from scripts.market_snapshot import merge_aa_v5  # noqa: E402


class MarketSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "report-data.json").read_text())
        cls.snapshot = cls.data["market_snapshot"]

    def test_sources_dates_and_missing_costs_survive_build(self):
        raw = json.loads((CURRENT_RESEARCH / "market-snapshot.json").read_text())
        v5 = json.loads((CURRENT_RESEARCH / "aa-index-v5.json").read_text())
        self.assertEqual(self.snapshot, merge_aa_v5(raw, v5))
        self.assertEqual([b["id"] for b in raw["boards"]],
                         ["aa", "arena", "arena_webdev", "arena_agent", "livebench", "scale", "openrouter"])
        self.assertEqual(sum(len(b["rows"]) for b in raw["boards"]), 233)
        for board in raw["boards"]:
            self.assertEqual(urlsplit(board["source_url"]).scheme, "https")
            self.assertTrue(board["selection"] and board["cost_basis"])
            self.assertEqual(len(board["rows"]), len({r["id"] for r in board["rows"]}))
            for row in board["rows"]:
                self.assertIsInstance(row["score"], (int, float))
                self.assertTrue(row["configuration"])
                self.assertTrue(row["cost_usd"] is None or row["cost_usd"] >= 0)
            if board["id"] in {"scale", "arena", "arena_webdev", "arena_agent", "openrouter"}:
                self.assertTrue(all(r["cost_usd"] is None for r in board["rows"]))
        boards = {b["id"]:b for b in raw["boards"]}
        self.assertIsNone(boards["scale"]["source_updated_at"])
        self.assertEqual(boards["livebench"]["source_updated_at"], "2026-11-06")
        self.assertEqual(boards["livebench"]["checked_at"], CURRENT_RESEARCH.name)
        self.assertEqual(raw["reviewed_at"], CURRENT_RESEARCH.name)
        self.assertEqual(boards["aa"]["checked_at"], "2026-10-23")  # the frozen v4.3.2 board keeps its date

    def test_new_sources_match_their_raw_files(self):
        folder = CURRENT_RESEARCH
        raw = json.loads((CURRENT_RESEARCH / "market-snapshot.json").read_text())
        boards = {b["id"]: b for b in raw["boards"]}
        arena = json.loads((folder / "arena.json").read_text())
        self.assertTrue(all(len(p["sha256"]) == 64 for p in arena["pages"]))
        # The current text board agrees with Arena's own dataset row by row.
        text = {r["source_rank"]: r for r in arena["boards"]["text_style_control"]["rows"]}
        for row in boards["arena"]["rows"]:
            src = text[row["source_rank"]]
            self.assertEqual(src["score"], row["score"], row["model"])
            self.assertEqual(src["votes"], row["votes"], row["model"])
        agent = boards["arena_agent"]
        self.assertEqual(agent["source_updated_at"], "2026-11-22")
        self.assertEqual(agent["rows"][0]["model"], "Claude Fable 5.2")
        self.assertAlmostEqual(agent["rows"][0]["praise"], 0.6866, places=4)
        self.assertTrue(agent["fixed_precision"])  # small IPS values keep three decimals on screen
        self.assertEqual(boards["arena_webdev"]["source_updated_at"], "2026-11-23")
        self.assertEqual(boards["arena"]["source_updated_at"], "2026-11-22")
        # LiveBench Overall: long agentic x2, coding and design x1.5, the rest x1.
        live = json.loads((folder / "livebench.json").read_text())
        fable = next(r for r in live["rows"] if r["slug"] == "claude-fable-5.1")
        w = live["weights"]
        overall = sum(v * w[k] for k, v in fable["suites"].items()) / sum(w[k] for k in fable["suites"])
        self.assertEqual(round(overall, 1), 84.0)
        neon = boards["livebench"]["rows"][0]
        self.assertEqual((neon["model"], neon["score"], neon["cost_usd"]), ("Gemini 4 Neon", 87.4, 2.654))
        self.assertEqual(len(boards["scale"]["rows"]), 32)
        manual = json.loads((folder / "manual-boards.json").read_text())
        in_scope = [r for r in manual["scale"]["rows"] if not r["model"].startswith("Muse Spark Open ")]
        for row, source in zip(boards["scale"]["rows"], in_scope, strict=True):
            self.assertEqual(row["source_rank"], source["rank"])
            self.assertEqual((row["score"], row["interval"], row["calibration_error"]),
                             (source["score"], source["confidenceInterval_upper"], source["calibrationError"]))
            effort = source["model"].rsplit(" ", 1)[-1]
            framework = "one-pass-agent" if "(one-pass-agent)" in source["model"] else "未注明代理框架"
            self.assertEqual(row["configuration"], f"{effort} · {framework}")
        self.assertEqual(raw["scale_highlight_updates"]["0"]["top1"], "Gemini 4 Neon xhigh (75.86 ±3.40)")
        full = raw["scale_highlight_updates"]["2"]
        self.assertEqual(full["source_ranks"], [1, 2, 2, 3])
        self.assertIn("Claude Fable 5.1 (Claude Code) high", full["top3"])
        self.assertEqual(raw["scale_highlight_updates"]["3"]["top1"], "Claude Opus 5 (Claude Code) xhigh (98.00%)")
        self.assertEqual(boards["openrouter"]["source_updated_at"], "2026-11-27")

    def test_cross_source_ranks_stay_within_each_source(self):
        cs = self.snapshot["cross_source"]
        board_ids = {b["id"] for b in self.snapshot["boards"]}
        self.assertTrue({c["id"] for c in cs["columns"]} <= board_ids)
        self.assertEqual(len(cs["models"]), 30)
        for col in cs["columns"]:
            ranks = sorted(m["cells"][col["id"]]["rank"] for m in cs["models"] if col["id"] in m["cells"])
            self.assertEqual(len(ranks), col["covered"])
            for i, rank in enumerate(ranks, 1):
                if i == 1 or rank != ranks[i-2]:
                    self.assertEqual(rank, i, col["id"])
        by = {m["model"]: m for m in cs["models"]}
        for name in ("Claude Opus 5.5", "Gemini 4 Argon", "Gemini 4 Hydrogen"):
            self.assertEqual(by[name]["cells"]["scale"]["rank"], 8)
        self.assertEqual(by["Claude Fable 5.1"]["cells"]["scale"]["rank"], 11)
        self.assertEqual([by[m]["cells"]["livebench"]["rank"] for m in ("Claude Fable 5.2", "GPT-6.2 Astra")], [2, 3])
        self.assertNotIn("openrouter", by["Tencent Hy4"]["cells"])
        self.assertEqual(set(by["Hy4 flash"]["cells"]), {"openrouter"})
        self.assertEqual(by["Claude Fable 5.2"]["cells"]["arena_agent"]["rank"], 1)
        self.assertEqual(by["Claude Fable 5.2"]["cells"]["scale"]["rank"], 1)
        self.assertEqual(by["DeepSeek V4.1 Flash 1017"]["cells"]["openrouter"]["rank"], 1)
        self.assertNotIn("scale", by["Muse Wonder Full"]["cells"])  # absent, not ranked last
        self.assertEqual(set(by["GPT-6.2 Astra"]["cells"]), {"aa5", "arena", "arena_webdev", "arena_agent", "livebench", "scale"})
        self.assertEqual(set(by["Gemini 4 Neon"]["cells"]), {"aa5", "arena", "arena_webdev", "arena_agent", "livebench", "scale"})
        self.assertEqual(by["Gemini 4 Neon"]["cells"]["livebench"]["rank"], 1)
        self.assertEqual(set(by["Qwen4-Max"]["cells"]), {"aa5", "arena_webdev", "arena_agent", "livebench"})
        self.assertTrue(by["Kimi K3.1 Pro"]["open_weights"])
        self.assertEqual(by["GPT-6.2 Sol"]["cells"]["livebench"]["value"], 80.3)
        self.assertNotIn("aa5", by["GPT-6 Astra"]["cells"])  # left the current AA board
        for m in cs["models"]:
            ranks = [c["rank"] for k, c in m["cells"].items() if k != "openrouter"]
            self.assertEqual(m["spread"], max(ranks) - min(ranks) if len(ranks) > 1 else None)

    def test_aa_v5_board_is_separate_and_traceable(self):
        boards = {b["id"]: b for b in self.snapshot["boards"]}
        self.assertEqual([b["id"] for b in self.snapshot["boards"]][:2], ["aa5", "aa"])
        raw = json.loads((CURRENT_RESEARCH / "market-snapshot.json").read_text())
        self.assertEqual({**boards["aa"], "short": raw["boards"][0]["short"]}, raw["boards"][0])  # only the tab label changes
        self.assertEqual(boards["aa"]["short"], "AA v4.3.2（旧）")
        ranked = sorted(boards["aa5"]["rows"], key=lambda r: -r["score"])
        self.assertEqual([r["model"] for r in ranked[:2]], ["Claude Fable 5.2", "Claude Fable 5.2"])
        v5 = boards["aa5"]
        self.assertEqual(v5["checked_at"], CURRENT_RESEARCH.name)
        argon = next(r for r in v5["rows"] if r["model"] == "Gemini 4 Argon")
        self.assertEqual(argon["cost_usd"], 7.0616)  # AA uses the December list price.
        retail = next(m for m in self.data["models"] if m["id"] == "gemini-4-argon")
        self.assertEqual((retail["input"], retail["output"], retail["promo_end"]), (2, 10, "2026-11-30"))
        self.assertIn("12-01", v5["note"])
        self.assertIsNone(v5["source_updated_at"])
        self.assertEqual(sum(c["weight"] for c in v5["methodology"]["categories"]), 100)
        for cat in v5["methodology"]["categories"]:
            self.assertEqual(sum(w for _, w in cat["evals"]), cat["weight"])
        raw_v5 = json.loads((CURRENT_RESEARCH / "aa-index-v5.json").read_text())
        self.assertTrue(all(len(p["sha256"]) == 64 for p in raw_v5["pages"]))
        old = {(r["model"], r["configuration"]): r["score"] for r in boards["aa"]["rows"]}
        rows = {(r["model"], r["configuration"].split(" · 开放权重")[0]): r for r in v5["rows"]}
        for row in v5["rows"]:
            # Displayed whole numbers round half up from the source's exact value.
            self.assertEqual(row["score"], int(Decimal(str(row["score_raw"])).quantize(Decimal("1"), ROUND_HALF_UP)))
            self.assertTrue(row["cost_usd"] is None or row["cost_usd"] > 0)
            self.assertEqual(len(row["evals"]), 10)
            key = (row["model"], row["configuration"].split(" · 开放权重")[0])
            if key in old:
                self.assertEqual(row["prev_score"], old[key])
            if row["prev_score"] is None:
                self.assertEqual(row["change"], "旧选录无此档")
            else:
                delta = row["score"] - row["prev_score"]
                label = "持平" if delta == 0 else f"{'+' if delta > 0 else '−'}{abs(delta)}"
                self.assertEqual(row["change"], f"{label} · 原 {row['prev_score']}")
        # Values first gathered from search snippets, now read from the AA page.
        self.assertEqual(rows[("Claude Opus 5.5", "low · 含回退")]["score"], 35)
        self.assertEqual(rows[("Muse Wonder", "max")]["score"], 44)
        self.assertEqual(rows[("MiMo-V2.6-Pro", "页面未注明档位")]["score"], 30)
        self.assertEqual(rows[("Claude Opus 5.5", "max · 含回退")]["cost_usd"], 10.0364)
        self.assertIsNone(rows[("Muse Wonder Full", "max")]["cost_usd"])
        self.assertEqual(self.snapshot["highlights"][0]["board_id"], "aa5")
        self.assertEqual(self.snapshot["changes"][0]["title"], "AA 更新编程评分，终端任务切换至 Terminal-Bench 4.1")
        titles = [c["title"] for c in self.snapshot["changes"]]
        self.assertEqual(len(titles), len(set(titles)))  # the AA note must not repeat a snapshot change

    def test_correct_model_costs_replace_old_panorama_estimates(self):
        rows = {r["model"]:r for r in self.data["external_leaderboards"]["four_family_matrix"]}
        self.assertIn("RLI #2 21.25%", rows["Claude Opus 5.5"]["scale_seal"])
        self.assertIn("MultiChallenge #15 high (67.67 ±5.34)%", rows["Claude Haiku 5.5"]["scale_seal"])
        self.assertIn("HLE Diamond #24 high · 未注明代理框架", rows["Grok 4.7"]["scale_seal"])
        self.assertIn("未列出", rows["Gemini 3.5 Flash-Lite"]["scale_seal"])
        self.assertEqual({r["scale_snapshot"] for r in rows.values()}, {CURRENT_RESEARCH.name + " 核验"})
        self.assertIn("67.9 · $4.175/成功任务", rows["Grok 4.7"]["livebench_2"])
        self.assertIn("68.9 · $1.264/成功任务", rows["Claude Haiku 5.5"]["livebench_2"])
        self.assertIn("6.36T tokens", rows["Claude Opus 5.5"]["openrouter"])
        self.assertIn("1519.8 ±5.0", rows["Gemini 4 Argon"]["arena"])
        self.assertEqual(len(self.data["rows"]), 169)
        self.assertEqual(self.data["aa_effort_evals"]["fetched_at"],
                         json.loads((ROOT / "research/2026-10-20/aa-effort-evals.json").read_text())["fetched_at"])

    def test_filter_export_missingness_and_long_context_thresholds(self):
        source = (ROOT / "report.js").read_text()
        math = source.split("// BEGIN MARKET_MATH",1)[1].split("// END MARKET_MATH",1)[0]
        script = 'const assert=require("node:assert/strict");const finite=v=>typeof v==="number"&&Number.isFinite(v);\n' + math + r'''
const data=JSON.parse(require('node:fs').readFileSync('report-data.json','utf8'));
const boards=Object.fromEntries(data.market_snapshot.boards.map(b=>[b.id,b]));
assert.equal(marketRows(boards.aa,'  DEEPSEEK ','all','score')[0].model,'DeepSeek V4.1 Flash 1017');
assert.equal(marketRows(boards.aa,'不存在','all','score').length,0);
assert(marketRows(boards.aa,'','OpenAI','score').every(r=>r.vendor==='OpenAI'));
const byCost=marketRows(boards.aa,'','all','cost');
assert.equal(byCost[0].model,'GPT-6 Luna');
assert.equal(byCost.at(-1).cost_usd,null);
const zero={...boards.aa,rows:[{model:'A',vendor:'X',configuration:'low',score:0,cost_usd:0},{model:'B',vendor:'X',configuration:'high',score:null,cost_usd:null}]};
assert.equal(marketRows(zero,'','all','score')[0].score,0);
assert.equal(marketExportRows(boards.scale,boards.scale.rows)[0].cost_usd,null);
assert.equal(marketExportRows(boards.scale,boards.scale.rows)[0].source_updated_at,null);
assert.equal(marketExportRows(boards.livebench,boards.livebench.rows)[0].source_updated_at,'2026-11-06');
assert.equal(marketExportRows(boards.livebench,boards.livebench.rows)[0].checked_at,data.market_snapshot.reviewed_at);
assert.equal(marketExportRows(boards.livebench,boards.livebench.rows)[0].configuration,'页面未注明档位');
const grok=data.models.find(m=>m.id==='grok-4-7'),haiku=data.models.find(m=>m.id==='claude-haiku-5-5');
assert(!usesLongContextPrice(grok,199999));
assert(usesLongContextPrice(grok,200000));
assert(usesLongContextPrice(grok,200001));
assert(!usesLongContextPrice(haiku,100000));
assert(usesLongContextPrice(haiku,100001));
const ember=data.models.find(m=>m.id==='muse-ember-1.0');
assert(!usesLongContextPrice(ember,200000));
assert(usesLongContextPrice(ember,200001));
const neon=data.models.find(m=>m.id==='gemini-4-neon');
assert(!usesLongContextPrice(neon,1000000));
assert(!usesLongContextPrice({},999999));
'''
        result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
