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
from scripts.market_snapshot import merge_aa_v5  # noqa: E402


class MarketSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "report-data.json").read_text())
        cls.snapshot = cls.data["market_snapshot"]

    def test_sources_dates_and_missing_costs_survive_build(self):
        raw = json.loads((ROOT / "research/2026-10-29/market-snapshot.json").read_text())
        v5 = json.loads((ROOT / "research/2026-10-28/aa-index-v5.json").read_text())
        self.assertEqual(self.snapshot, merge_aa_v5(raw, v5))
        self.assertEqual([b["id"] for b in raw["boards"]],
                         ["aa", "arena", "arena_webdev", "arena_agent", "livebench", "scale", "openrouter"])
        self.assertEqual(sum(len(b["rows"]) for b in raw["boards"]), 119)
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
        self.assertEqual(boards["livebench"]["source_updated_at"], "2026-10-25")
        self.assertEqual(boards["livebench"]["checked_at"], "2026-10-29")
        self.assertEqual(boards["aa"]["checked_at"], "2026-10-23")  # the frozen v4.3.2 board keeps its date

    def test_new_sources_match_their_raw_files(self):
        folder = ROOT / "research/2026-10-29"
        raw = json.loads((folder / "market-snapshot.json").read_text())
        boards = {b["id"]: b for b in raw["boards"]}
        arena = json.loads((folder / "arena.json").read_text())
        self.assertTrue(all(len(p["sha256"]) == 64 for p in arena["pages"]))
        # The text board read on 10-23 agrees with Arena's own dataset row by row.
        text = {r["source_rank"]: r for r in arena["boards"]["text_style_control"]["rows"]}
        for row in boards["arena"]["rows"]:
            src = text[row["source_rank"]]
            self.assertEqual(round(src["score"]), row["score"], row["model"])
            self.assertEqual(src["votes"], row["votes"], row["model"])
        agent = boards["arena_agent"]
        self.assertEqual(agent["source_updated_at"], "2026-10-23")
        self.assertEqual(agent["rows"][0]["model"], "Claude Opus 5.5")
        self.assertAlmostEqual(agent["rows"][0]["praise"], 0.4532, places=4)
        self.assertTrue(agent["fixed_precision"])  # small IPS values keep three decimals on screen
        self.assertEqual(boards["arena_webdev"]["source_updated_at"], "2026-10-27")
        # LiveBench Overall: long agentic x2, coding and design x1.5, the rest x1.
        live = json.loads((folder / "livebench.json").read_text())
        fable = next(r for r in live["rows"] if r["slug"] == "claude-fable-5.1")
        w = live["weights"]
        overall = sum(v * w[k] for k, v in fable["suites"].items()) / sum(w[k] for k in fable["suites"])
        self.assertEqual(round(overall, 1), 85.7)
        self.assertEqual(boards["livebench"]["rows"][0]["cost_usd"], 6.904)
        self.assertEqual(len(boards["scale"]["rows"]), 17)
        self.assertEqual(boards["openrouter"]["source_updated_at"], "2026-10-27")

    def test_cross_source_ranks_stay_within_each_source(self):
        cs = self.snapshot["cross_source"]
        board_ids = {b["id"] for b in self.snapshot["boards"]}
        self.assertTrue({c["id"] for c in cs["columns"]} <= board_ids)
        self.assertEqual(len(cs["models"]), 14)
        for col in cs["columns"]:
            ranks = sorted(m["cells"][col["id"]]["rank"] for m in cs["models"] if col["id"] in m["cells"])
            self.assertEqual(ranks, list(range(1, col["covered"] + 1)), col["id"])
        by = {m["model"]: m for m in cs["models"]}
        self.assertEqual(by["Claude Opus 5.5"]["cells"]["arena_agent"]["rank"], 1)
        self.assertEqual(by["GPT-6 Astra"]["cells"]["scale"]["rank"], 1)
        self.assertEqual(by["DeepSeek V4.1 Flash 1017"]["cells"]["openrouter"]["rank"], 1)
        self.assertNotIn("arena_agent", by["Kimi K3.1 Pro"]["cells"])  # absent, not ranked last
        for m in cs["models"]:
            ranks = [c["rank"] for k, c in m["cells"].items() if k != "openrouter"]
            self.assertEqual(m["spread"], max(ranks) - min(ranks) if len(ranks) > 1 else None)

    def test_aa_v5_board_is_separate_and_traceable(self):
        boards = {b["id"]: b for b in self.snapshot["boards"]}
        self.assertEqual([b["id"] for b in self.snapshot["boards"]][:2], ["aa5", "aa"])
        raw = json.loads((ROOT / "research/2026-10-29/market-snapshot.json").read_text())
        self.assertEqual({**boards["aa"], "short": raw["boards"][0]["short"]}, raw["boards"][0])  # only the tab label changes
        self.assertEqual(boards["aa"]["short"], "AA v4.3.2（旧）")
        ranked = sorted(boards["aa5"]["rows"], key=lambda r: -r["score"])
        self.assertEqual([r["model"] for r in ranked[:2]], ["Claude Opus 5.5", "GPT-6 Astra"])
        v5 = boards["aa5"]
        self.assertEqual(v5["checked_at"], "2026-10-29")
        argon = next(r for r in v5["rows"] if r["model"] == "Gemini 4 Argon")
        self.assertEqual(argon["cost_usd"], 7.68)  # AA now prices Argon at the post-promotion $4 / $20
        self.assertIn("12-01", v5["note"])
        self.assertEqual(v5["source_updated_at"], "2026-10-27")
        self.assertEqual(sum(c["weight"] for c in v5["methodology"]["categories"]), 100)
        for cat in v5["methodology"]["categories"]:
            self.assertEqual(sum(w for _, w in cat["evals"]), cat["weight"])
        raw_v5 = json.loads((ROOT / "research/2026-10-28/aa-index-v5.json").read_text())
        self.assertTrue(all(len(p["sha256"]) == 64 for p in raw_v5["pages"]))
        old = {(r["model"], r["configuration"]): r["score"] for r in boards["aa"]["rows"]}
        rows = {(r["model"], r["configuration"].split(" · 开放权重")[0]): r for r in v5["rows"]}
        for row in v5["rows"]:
            # Displayed whole numbers round half up from the source's exact value.
            self.assertEqual(row["score"], int(Decimal(str(row["score_exact"])).quantize(Decimal("1"), ROUND_HALF_UP)))
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
        self.assertEqual(rows[("Muse Wonder", "max")]["score"], 43)
        self.assertEqual(rows[("MiMo-V2.6-Pro", "页面未注明档位")]["score"], 30)
        self.assertEqual(rows[("Claude Opus 5.5", "max · 含回退")]["cost_usd"], 10.04)
        self.assertIsNone(rows[("Muse Wonder Full", "max")]["cost_usd"])
        self.assertEqual(self.snapshot["highlights"][0]["board_id"], "aa5")
        self.assertEqual(self.snapshot["changes"][0]["title"], "AA 智能指数升级到 v5")

    def test_correct_model_costs_replace_old_panorama_estimates(self):
        rows = {r["model"]:r for r in self.data["external_leaderboards"]["four_family_matrix"]}
        self.assertIn("70.1 · $2.913/成功任务", rows["Grok 4.7"]["livebench_2"])
        self.assertIn("69.8 · $0.905/成功任务", rows["Claude Haiku 5.5"]["livebench_2"])
        self.assertIn("8.07T tokens", rows["Claude Opus 5.5"]["openrouter"])
        self.assertIn("1517 ±7", rows["Gemini 4 Argon"]["arena"])
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
assert.equal(marketExportRows(boards.livebench,boards.livebench.rows)[0].source_updated_at,'2026-10-25');
assert.equal(marketExportRows(boards.livebench,boards.livebench.rows)[0].checked_at,'2026-10-29');
assert.equal(marketExportRows(boards.livebench,boards.livebench.rows)[0].configuration,'页面未注明档位');
const grok=data.models.find(m=>m.id==='grok-4-7'),haiku=data.models.find(m=>m.id==='claude-haiku-5-5');
assert(!usesLongContextPrice(grok,199999));
assert(usesLongContextPrice(grok,200000));
assert(usesLongContextPrice(grok,200001));
assert(!usesLongContextPrice(haiku,100000));
assert(usesLongContextPrice(haiku,100001));
assert(!usesLongContextPrice({},999999));
'''
        result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
