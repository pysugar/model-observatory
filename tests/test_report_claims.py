"""Keep numerical prose tied to frozen records and explicit task definitions."""

import copy
import json
from pathlib import Path
import subprocess
import unittest

from scripts.report_claims import render_claims


ROOT = Path(__file__).resolve().parents[1]


class NarrativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "report-data.json").read_text())
        cls.sources = (ROOT / "report.template.html").read_text() + (ROOT / "report.js").read_text()

    def test_all_numerical_references_resolve_and_follow_changed_records(self):
        rendered = render_claims(self.sources, self.data)
        self.assertNotIn("{{aa:", rendered)
        self.assertNotIn("{{row:", rendered)
        self.assertIn("high 44.83 分", rendered)
        self.assertIn("84.61 分 / $0.328", rendered)
        changed = copy.deepcopy(self.data)
        sol = next(r for r in changed["aa_release_series"]["releases"] if r["releaseSlug"] == "gpt-6-1-sol")
        next(v for v in sol["variants"] if v["effort"] == "high")["taskScores"]["knowledge"] = 40.25
        self.assertIn("high 40.25 分", render_claims(self.sources, changed))
        self.assertNotIn("high 44.83 分", render_claims(self.sources, changed))

    def test_missing_and_ambiguous_claims_fail_instead_of_inventing_values(self):
        with self.assertRaises(ValueError):
            render_claims("{{aa:gemini-3-8-flash:low:costPerTask:2}}", self.data)
        with self.assertRaises(ValueError):
            render_claims("{{aa:unknown:high:coding:1}}", self.data)
        changed = copy.deepcopy(self.data)
        changed["rows"].append(next(r for r in changed["rows"] if
                                   (r["benchmark"], r["model"], r["effort"]) == ("writing", "Claude Opus 5.5", "high")))
        with self.assertRaises(ValueError):
            render_claims("{{row:writing:Claude Opus 5.5:high:score:2}}", changed)

    def test_display_rounding_matches_browser_for_halfway_values(self):
        samples = [[value, digits] for value in (78.35, 69.05, 2.675, 0.005, 46.5, -1.25)
                   for digits in range(5)]
        result = subprocess.run(["node", "-e",
            "const a=JSON.parse(require('fs').readFileSync(0,'utf8'));"
            "process.stdout.write(JSON.stringify(a.map(([v,d])=>v.toLocaleString('en-US',"
            "{useGrouping:false,minimumFractionDigits:d,maximumFractionDigits:d}))));"],
            input=json.dumps(samples), capture_output=True, text=True, check=True)
        for (value, digits), expected in zip(samples, json.loads(result.stdout)):
            data = {"aa_release_series": {"releases": [{"releaseSlug": "test",
                    "variants": [{"effort": "max", "intelligenceIndex": value}]}]}}
            self.assertEqual(render_claims("{{aa:test:max:intelligenceIndex:"+str(digits)+"}}", data), expected)

    def test_task_formulas_match_raw_evaluations_for_every_variant(self):
        evidence = json.loads((ROOT / "research/2026-10-20/aa-effort-evals.json").read_text())["variants"]
        checked = set()
        for release in self.data["aa_release_series"]["releases"]:
            for variant in release["variants"]:
                if variant["slug"] not in evidence:
                    continue
                m = evidence[variant["slug"]]["metrics"]
                self.assertEqual(variant["evalMetrics"], m)
                self.assertEqual(variant["taskScores"], {
                    "complex": round((m["Humanity's Last Exam"] + m["CritPt"]) / 2, 2),
                    "coding": round((m["Terminal-Bench 4.0"] + m["SciCode"]) / 2, 2),
                    "planning": m["AA-Briefcase v1.1"],
                    "agentic": m["GDPval-AA v2.1"],
                    "automation": m["AutomationBench-AA"],
                    "knowledge": round((m["AA-LCR v1.1"] + 2 * m["GDP.pdf"] + 3 * m["AA-Omniscience"]) / 6, 2),
                })
                checked.add(variant["slug"])
        self.assertEqual(checked, set(evidence))


if __name__ == "__main__":
    unittest.main()
