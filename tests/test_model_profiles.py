"""Model profile tab: one model, every task x native effort, joined from frozen evidence."""
import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sweet_spot import PRESETS, picks, profile_alternatives, profile_pitfalls, profile_series  # noqa: E402


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

    def test_pitfalls_flag_the_known_traps(self):
        pits = {m["id"]: profile_pitfalls(self.data, m["id"]) for m in self.doc["models"]}
        # Cost trap: Sonnet 5.5 xhigh -> max costs 2.7x for about 4 AA points.
        self.assertIn(("cost", "aa-ii", "max"), pits["claude-sonnet-5-5"])
        self.assertNotIn(("cost", "aa-ii", "xhigh"), pits["claude-sonnet-5-5"])
        # Grok 4.7: low -> high (the default) more than doubles the cost for about 4 points.
        self.assertIn(("cost", "aa-ii", "high"), pits["grok-4-7"])
        # Regression: Opus 5.5 Vulcan max scores below its own medium.
        self.assertIn(("regress", "vulcan", "max"), pits["claude-opus-5-5"])
        # Upgrade and step down: newer same-line models at a lower effort cover the old top effort.
        self.assertIn(("upgrade", "config", "max", "claude-opus-5-5", "medium"), pits["claude-opus-5"])
        self.assertIn(("upgrade", "config", "max", "gpt-6.1-sol", "medium"), pits["gpt-5.6-sol"])
        # Other same-vendor model: every Fable 5.1 effort is covered by an Opus 5.5 effort.
        self.assertTrue(all(x[3] == "claude-opus-5-5" for x in pits["claude-fable-5-1"] if x[0] == "dominated"))
        # Models without curves get no invented pitfalls.
        for model_id in ("claude-opus-4-7", "gemini-4-argon", "gemini-3.5-flash-lite"):
            self.assertEqual(pits[model_id], set(), model_id)

    def test_better_alternatives_for_a_specific_effort(self):
        grok = profile_alternatives(self.data, "grok-4-7", "high", "all")
        self.assertEqual(grok["aa-ii"][:2], (("gpt-6.1-sol", "medium"), ("claude-opus-5-5", "high")))
        # xAI has no other active model, so the same-vendor scope finds nothing better than Grok's own efforts.
        self.assertEqual(profile_alternatives(self.data, "grok-4-7", "high", "vendor")["aa-ii"][:2], (None, None))
        sonnet = profile_alternatives(self.data, "claude-sonnet-5-5", "max", "vendor")
        self.assertEqual(sonnet["vulcan"][0], ("claude-opus-5-5", "medium"))
        for model in self.doc["models"]:
            for scope in ("vendor", "all"):
                for effort in ("low", "medium", "high", "xhigh", "max"):
                    for key, picks_ in profile_alternatives(self.data, model["id"], effort, scope).items():
                        # The unbounded pick may be the current config ("当前就是"); the other two never are.
                        for alt in picks_[:2]:
                            self.assertNotEqual(alt, (model["id"], effort), key)
                        self.assertIsNotNone(picks_[2], key)

    def test_unbounded_pick_prefers_the_faster_near_tie(self):
        sol = profile_alternatives(self.data, "gpt-6.1-sol", "max", "vendor")
        # Astra max tops the overall index, but Astra xhigh is within a tie and about 1.4x faster.
        self.assertEqual(sol["aa-ii"][2], ("gpt-6-astra", "xhigh"))
        self.assertIsNone(sol["aa-ii"][1])  # nothing stronger within Sol max's budget
        # Without timing data (OSWorld), the tie-break falls back to cost.
        self.assertEqual(sol["cu-openai"][2], ("gpt-6-astra", "max"))

    def test_overthinking_is_flagged(self):
        pits = profile_pitfalls(self.data, "gpt-6.1-sol")
        # xhigh -> max: about 2x the time per task for +0.8 AA points.
        self.assertIn(("overthink", "aa-ii", "max"), pits)
        self.assertNotIn(("overthink", "aa-ii", "max"), profile_pitfalls(self.data, "claude-sonnet-5-5"))

    def test_max_effort_scenarios_are_sourced(self):
        scenarios = self.data["community_consensus"]["maxEffortScenarios"]
        self.assertGreaterEqual(len(scenarios), 8)
        self.assertEqual({s["measure"] for s in scenarios if s["measure"]}, {"overthink", "regress", "ttfa"})
        for sc in scenarios:
            self.assertTrue(sc["sources"] and all(x["url"].startswith("https://") for x in sc["sources"]), sc["id"])

    def test_community_voices_are_sourced_text_only(self):
        doc = self.data["community_consensus"]
        ids = {m["id"] for m in self.doc["models"]}
        self.assertTrue(doc["uncoveredDimensions"])
        for item in doc["items"]:
            self.assertTrue(set(item["modelIds"]) <= ids, item["id"])
            self.assertTrue(item["sources"] and all(s["url"].startswith("https://") for s in item["sources"]), item["id"])
            self.assertEqual(item["verification"], "search-summary")
            self.assertNotIn("efforts", item)  # community voices never feed the calculations

    def test_every_profile_model_has_a_product_line(self):
        for m in self.doc["models"]:
            self.assertTrue(m["line"], m["id"])

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
