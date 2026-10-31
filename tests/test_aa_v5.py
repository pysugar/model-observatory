"""AA Intelligence Index v5 bundle: v5-only task views, no v4.3.2 fill-ins, both versions kept apart."""

from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import unittest

from build_report import v5_task_scores
from scripts.report_claims import render_claims

ROOT = Path(__file__).resolve().parents[1]


class AaV5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "report-data.json").read_text())
        cls.v5 = cls.data["aa_v5"]
        cls.raw = json.loads((ROOT / "research/2026-10-31/aa-v5-series.json").read_text())

    def test_versions_stay_separate(self):
        # v4.3.2 stays in the top-level keys; v5 lives in its own bundle and the page loads one of them.
        self.assertEqual(self.data["aa_release_series"]["version"], "v4.3.2")
        self.assertEqual(len(self.data["aa_release_series"]["releases"]), 30)
        self.assertEqual(self.v5["aa_release_series"]["version"], "v5.0")
        self.assertEqual(len(self.v5["aa_release_series"]["releases"]), 20)

    def test_unmeasured_models_are_listed_not_filled(self):
        unmeasured = {u["releaseSlug"] for u in self.v5["unmeasured"]}
        self.assertTrue({"claude-opus-5", "gpt-5-6-sol", "claude-sonnet-4-6", "grok-4-6"} <= unmeasured)
        for rel in self.v5["aa_release_series"]["releases"]:
            self.assertTrue(rel["variants"])
            for v in rel["variants"]:
                self.assertIsInstance(v["intelligenceIndex"], float)
        listed = {s for u in self.v5["unmeasured"] for s in u["variants"]}
        present = {v["slug"] for r in self.v5["aa_release_series"]["releases"] for v in r["variants"]}
        self.assertFalse(listed & present)

    def test_five_families_have_every_v5_evaluation(self):
        current = [r for r in self.v5["aa_release_series"]["releases"] if r["isTrackedFamily"] and r["isCurrent"]]
        self.assertEqual(len(current), 16)
        variants = [v for r in current for v in r["variants"]]
        self.assertEqual(len(variants), 54)
        for v in variants:
            self.assertEqual(set(v["evalMetrics"]), set(self.raw["aa_effort_evals"]["evals"]))
            self.assertEqual(v["taskScores"], v5_task_scores(v["evalMetrics"]))
            self.assertNotIn("SciCode", v["evalMetrics"])
            self.assertNotIn("GDPval-AA v2.1", v["evalMetrics"])

    def test_task_view_formulas(self):
        m = {"HLE-Diamond": 60, "CritPt v2 hard": 40, "Terminal-Bench 4.0": 50, "FrontierCode 2.0": 30,
             "AA-Briefcase v1.1": 1500, "Terminal-Bench-Science": 45, "AutomationBench-AA": 70,
             "GDP.pdf": 30, "AA-Omniscience v1.1": -10}
        self.assertEqual(v5_task_scores(m), {"complex": 50.0, "coding": 40.0, "planning": 1500,
                                             "agentic": 45, "automation": 70, "knowledge": 6.0})

    def test_partial_measurement_and_closed_meta_scope(self):
        m = {"HLE-Diamond":None,"CritPt v2 hard":40,"Terminal-Bench 4.0":50,"FrontierCode 2.0":30,
             "AA-Briefcase v1.1":1500,"Terminal-Bench-Science":45,"AutomationBench-AA":70,
             "GDP.pdf":30,"AA-Omniscience v1.1":None}
        self.assertIsNone(v5_task_scores(m)["complex"])
        self.assertIsNone(v5_task_scores(m)["knowledge"])
        self.assertEqual(v5_task_scores(m)["coding"],40)
        meta = [r for r in self.v5["aa_release_series"]["releases"] if r["vendor"] == "Meta"]
        self.assertEqual({r["releaseSlug"] for r in meta}, {"muse-wonder","muse-wonder-full","muse-spark-1-3"})
        full = next(r for r in meta if r["releaseSlug"] == "muse-wonder-full")["variants"][0]
        self.assertIsNone(full["costPerTask"])
        self.assertEqual(full["capabilities"], {})
        spark = next(r for r in meta if r["releaseSlug"] == "muse-spark-1-3")
        self.assertEqual([v["effort"] for v in spark["variants"]],["max"])

    def test_rounding_capabilities_and_top_variant(self):
        variants = {v["slug"]: v for r in self.v5["aa_release_series"]["releases"] for v in r["variants"]}
        for v in variants.values():
            expected = int(Decimal(str(v["intelligenceIndex"])).quantize(Decimal("1"), ROUND_HALF_UP))
            self.assertEqual(v["intelligenceIndexRounded"], expected)
        self.assertEqual(variants["claude-opus-5-5-low"]["intelligenceIndexRounded"], 35)
        for rel in self.v5["aa_release_series"]["releases"]:
            top = [v for v in rel["variants"] if v["isTopVariant"]]
            self.assertEqual(len(top), 1)
            self.assertEqual(top[0]["intelligenceIndex"], max(v["intelligenceIndex"] for v in rel["variants"]))
        for entry in self.v5["aa_capability_indexes"]["entries"]:
            self.assertEqual(entry["intelligenceIndex"], variants[entry["slug"]]["intelligenceIndex"])
            self.assertEqual(entry["capabilities"], variants[entry["slug"]]["capabilities"])

    def test_leaderboard_and_release_pages_agree(self):
        variants = {v["slug"]: v for r in self.v5["aa_release_series"]["releases"] for v in r["variants"]}
        board = next(b for b in self.data["market_snapshot"]["boards"] if b["id"] == "aa5")
        for row in board["rows"]:
            if row["slug"] in variants:
                self.assertAlmostEqual(row["score_exact"], variants[row["slug"]]["intelligenceIndex"], places=2)

    def test_v5_narrative_references(self):
        self.assertEqual(render_claims("{{aa5:claude-opus-5-5:max:intelligenceIndex:1}}", self.data), "58.4")
        self.assertEqual(render_claims("{{aa:claude-opus-5-5:max:intelligenceIndex:1}}", self.data), "57.6")
        with self.assertRaises(ValueError):
            render_claims("{{aa5:claude-opus-5:max:intelligenceIndex:1}}", self.data)


if __name__ == "__main__":
    unittest.main()
