"""Keep current observations distinct from frozen experiments and unknown values."""

import json
from pathlib import Path
import subprocess
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class MarketSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "report-data.json").read_text())
        cls.snapshot = cls.data["market_snapshot"]

    def test_sources_dates_and_missing_costs_survive_build(self):
        raw = json.loads((ROOT / "research/2026-10-23/market-snapshot.json").read_text())
        self.assertEqual(self.snapshot, raw)
        self.assertEqual({b["id"] for b in raw["boards"]}, {"aa", "arena", "scale", "livebench", "openrouter"})
        self.assertEqual(sum(len(b["rows"]) for b in raw["boards"]), 87)
        for board in raw["boards"]:
            self.assertEqual(urlsplit(board["source_url"]).scheme, "https")
            self.assertTrue(board["selection"] and board["cost_basis"])
            self.assertEqual(len(board["rows"]), len({r["id"] for r in board["rows"]}))
            for row in board["rows"]:
                self.assertIsInstance(row["score"], (int, float))
                self.assertTrue(row["configuration"])
                self.assertTrue(row["cost_usd"] is None or row["cost_usd"] >= 0)
            if board["id"] in {"scale", "arena", "openrouter"}:
                self.assertTrue(all(r["cost_usd"] is None for r in board["rows"]))
        boards = {b["id"]:b for b in raw["boards"]}
        self.assertIsNone(boards["scale"]["source_updated_at"])
        self.assertEqual(boards["livebench"]["source_updated_at"], "2026-10-18")
        self.assertEqual(boards["livebench"]["checked_at"], "2026-10-23")

    def test_correct_model_costs_replace_old_panorama_estimates(self):
        rows = {r["model"]:r for r in self.data["external_leaderboards"]["four_family_matrix"]}
        self.assertIn("74.1 · $2.687/成功任务", rows["Grok 4.7"]["livebench_2"])
        self.assertIn("75.6 · $0.818/成功任务", rows["Claude Haiku 5.5"]["livebench_2"])
        self.assertIn("7.45T tokens", rows["Claude Opus 5.5"]["openrouter"])
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
assert.equal(marketExportRows(boards.livebench,boards.livebench.rows)[0].source_updated_at,'2026-10-18');
assert.equal(marketExportRows(boards.livebench,boards.livebench.rows)[0].checked_at,'2026-10-23');
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
