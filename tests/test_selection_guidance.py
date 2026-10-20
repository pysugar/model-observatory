"""Version-specific advice is a prior with provenance, not invented measurements."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'claude-opus-5-5': ['medium']*4,
    'claude-fable-5-1': ['high']*4,
    'claude-sonnet-5-5': ['high','medium','medium','high'],
    'gpt-6-1-sol': ['medium','medium','high','medium'],
    'gpt-6-astra': ['medium']*4,
    'gemini-4-argon': ['high','medium','medium','medium'],
    'grok-4-7': ['high']*4,
}


class SelectionGuidanceTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT/'research/2026-10-20/task-effort-guidance.json').read_text())

    def test_exact_version_task_mapping_and_native_support(self):
        tasks = ['complex','daily_code','repository_bug','design']
        self.assertEqual([t['id'] for t in self.data['tasks']], tasks)
        rows = self.data['recommendations']
        self.assertEqual(len(rows), 28)
        self.assertEqual(len({(r['modelId'],r['taskType']) for r in rows}), 28)
        models = {m['modelId']:m for m in self.data['models']}
        self.assertEqual(set(models), set(EXPECTED))
        for model, efforts in EXPECTED.items():
            actual = {r['taskType']:r for r in rows if r['modelId']==model}
            self.assertEqual([actual[t]['nativeEffort'] for t in tasks], efforts)
            for row in actual.values():
                self.assertIn(row['nativeEffort'], models[model]['supportedEfforts'])
        self.assertEqual(models['grok-4-7']['supportedEfforts'], ['low','medium','high','xhigh'])
        self.assertIsNone(models['gpt-6-astra']['officialDefault'])

    def test_evidence_scope_and_unknowns(self):
        for row in self.data['recommendations']:
            self.assertIn(row['evidenceType'], ['经验先验','社区实测'])
            self.assertTrue(row['sourceUrl'].startswith('https://'))
            self.assertEqual(row['checkedAt'], '2026-10-20')
            self.assertTrue(row['caveats'])
            self.assertIn('未建立任务最优结论', ''.join(row['caveats']))
            self.assertNotIn('score', row)
            self.assertNotIn('confidence', row)
            self.assertTrue(row['support'])
            for e in row['support']:
                self.assertIn(e['evidenceType'], ['官方建议','社区实测'])
                self.assertTrue(e['sourceUrl'].startswith('https://'))
                self.assertTrue(e['scope'])
            if row['modelId']=='gpt-6-1-sol' and row['taskType']=='repository_bug':
                self.assertEqual((row['evidenceType'],row['sampleSize'],row['harness']),('社区实测',23,'Codex CLI'))
            else:
                self.assertEqual(row['evidenceType'], '经验先验')
                self.assertIsNone(row['sampleSize'])
                self.assertIsNone(row['harness'])
            if row['taskType']=='design':
                self.assertIn('暂无直接可比公开架构设计成绩', ''.join(row['caveats']))
        self.assertTrue(all(r['evidenceType']=='经验先验' for r in self.data['rules']))
