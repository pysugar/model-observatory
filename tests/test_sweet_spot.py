"""The overview sweet spot is a marginal-gain knee, not the near-ceiling effort."""
import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sweet_spot import PRESETS, knee, picks  # noqa: E402


class SweetSpotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "report-data.json").read_text())
        cls.balanced = picks(cls.data, PRESETS["balanced"])

    def test_steady_climb_stops_before_poor_value_max(self):
        # Sonnet 5.5 keeps rising to max, but xhigh -> max is +4 points for 2.7x cost.
        self.assertEqual(self.balanced[("claude-sonnet-5-5", "ii")], "high")
        self.assertEqual(self.balanced[("claude-opus-5-5", "ii")], "high")
        self.assertEqual(self.balanced[("gpt-6-1-sol", "ii")], "medium")
        self.assertEqual(self.balanced[("gpt-6-1-sol", "coding")], "high")

    def test_presets_are_ordered_by_appetite(self):
        order = ["non-reasoning", "minimal", "low", "medium", "high", "xhigh", "max"]
        thrifty, performance = picks(self.data, PRESETS["thrifty"]), picks(self.data, PRESETS["performance"])
        for cell, effort in self.balanced.items():
            self.assertLessEqual(order.index(thrifty[cell]), order.index(effort), cell)
            self.assertLessEqual(order.index(effort), order.index(performance[cell]), cell)

    def test_full_matrix_and_single_effort_models(self):
        self.assertEqual(len(self.balanced), 11 * 7)
        for task in ("ii", "coding", "knowledge"):
            self.assertEqual(self.balanced[("gemini-4-argon", task)], "high")

    def test_knee_skips_dominated_points(self):
        items = [{"effort": "low", "score": 10, "cost": 1}, {"effort": "medium", "score": 9, "cost": 2},
                 {"effort": "high", "score": 20, "cost": 4}]
        self.assertEqual(knee(items, 1)["effort"], "high")
        self.assertEqual(knee(items, 6)["effort"], "low")
        self.assertIsNone(knee([{"effort": "low", "score": 1, "cost": None}], 1))


if __name__ == "__main__":
    unittest.main()
