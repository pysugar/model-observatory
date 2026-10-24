"""Model profile tab: one model, every task x native effort, joined from frozen evidence."""
import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sweet_spot import PRESETS, picks, profile_series  # noqa: E402


class ModelProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "report-data.json").read_text())
        cls.doc = cls.data["model_effort_profiles"]
        cls.source = json.loads((ROOT / "research/2026-10-24/model-effort-profiles.json").read_text())

    def test_build_embeds_the_frozen_research_file(self):
        self.assertEqual(self.doc, self.source)

    def test_every_active_catalog_model_has_a_profile(self):
        catalog = {m["id"]: m for m in self.data["models"]}
        ids = [m["id"] for m in self.doc["models"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), set(catalog))
        for vendor in ("Anthropic", "OpenAI", "Google", "xAI"):
            self.assertTrue(any(catalog[m["id"]]["vendor"] == vendor and m["tier"] == "main" for m in self.doc["models"]), vendor)
        # The user asked for the GPT-5.6 generation as well.
        self.assertTrue({"gpt-5.6-sol", "gpt-5.6-luna"} <= set(ids))

    def test_profile_knees_match_the_overview_matrix(self):
        for preset, share in PRESETS.items():
            overview = picks(self.data, share)
            for m in self.doc["models"]:
                series = profile_series(self.data, m["id"], share)
                for (release, task), effort in overview.items():
                    if release == m["aaRelease"]:
                        self.assertEqual(series["aa-" + task], effort, (preset, m["id"], task))

    def test_known_profile_picks(self):
        balanced = {m["id"]: profile_series(self.data, m["id"], PRESETS["balanced"]) for m in self.doc["models"]}
        self.assertEqual(balanced["claude-opus-5-5"]["vulcan"], "medium")
        self.assertEqual(balanced["gpt-6.1-sol"]["cu-openai"], "max")
        self.assertEqual(balanced["claude-opus-5-5"]["cu-anthropic"], "max")
        # GPT 5.6 Sol only has an overall AA curve plus coding/writing rows; no invented task scores.
        self.assertEqual(set(balanced["gpt-5.6-sol"]), {"aa-ii", "vulcan", "tonebench"})
        # Legacy models without measurements stay empty rather than borrowing a sibling's curve.
        self.assertEqual(balanced["claude-opus-4-7"], {})

    def test_evidence_is_sourced_and_flagged(self):
        tasks = {t["id"] for t in self.doc["taskAxis"]} | {"all"}
        ids = {m["id"] for m in self.doc["models"]}
        for ev in self.doc["evidence"]:
            self.assertTrue(ev["url"].startswith("https://"), ev["id"])
            self.assertEqual(ev["checkedAt"], "2026-10-24")
            self.assertEqual(ev["verification"], "search-summary")
            self.assertTrue(set(ev["tasks"]) <= tasks and set(ev["modelIds"]) <= ids, ev["id"])
            for effort in (ev.get("efforts") or {}).values():
                self.assertIn(effort, ["none", "minimal", "low", "medium", "high", "xhigh", "max"])

    def test_grok_medium_stays_pending_without_rewriting_the_catalog(self):
        grok = next(m for m in self.data["models"] if m["id"] == "grok-4-7")
        self.assertEqual(grok["efforts"], "low / high / xhigh")
        entry = next(m for m in self.doc["models"] if m["id"] == "grok-4-7")
        self.assertEqual(entry["effortDiscrepancy"]["extraEfforts"], ["medium"])

    def test_guidance_tasks_map_onto_the_axis(self):
        guide = {t["id"] for t in self.data["task_effort_guidance"]["tasks"]}
        mapped = {g for t in self.doc["taskAxis"] for g in t["guideTasks"]}
        self.assertEqual(mapped, guide)


if __name__ == "__main__":
    unittest.main()
