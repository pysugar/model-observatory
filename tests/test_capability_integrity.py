"""Regress missingness, published precision, cohort and effort semantics offline."""
import json
import copy
from build_report import bind_panorama_capabilities
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CapabilityIntegrityTests(unittest.TestCase):
    def test_shared_chart_table_export_math(self):
        source = (ROOT / 'report.js').read_text()
        math = source.split('// BEGIN CAPABILITY_MATH', 1)[1].split('\n', 1)[1].split('// END CAPABILITY_MATH', 1)[0]
        script = 'const assert=require("node:assert/strict"); const finite=v=>typeof v==="number"&&Number.isFinite(v);\n' + math + r'''
const synthetic = [
 {slug:'missing',intelligenceIndex:99,capabilities:{}},
 {slug:'a',intelligenceIndex:10,capabilities:{legal:60.104}},
 {slug:'b',intelligenceIndex:20,capabilities:{legal:60.101}},
 {slug:'c',intelligenceIndex:80,capabilities:{legal:60.09}},
 {slug:'zero',intelligenceIndex:90,capabilities:{legal:0}},
];
assert.equal(capScore(synthetic[0],'legal'),null);
const rank=capRanking(synthetic,'legal');
assert.equal(rank.n,4);
assert.equal(rank.ranks.has('missing'),false);
assert.deepEqual(['a','b','c','zero'].map(s=>rank.ranks.get(s)),[1,1,3,4]);
const exported=capExportRows(synthetic,[{key:'legal',slug:'legal'}]);
assert.equal(exported[0].legal_score,null);
assert.equal(exported[0].legal_view_rank,null);
assert.equal(exported[0].legal_status,'missing');
assert(exported.every(e=>e.legal_valid_n===4 && e.comparison_n===5));
const data=JSON.parse(require('node:fs').readFileSync('report-data.json','utf8')).aa_capability_indexes;
const all=capScopeEntries(data.entries,'four_family_all');
assert.equal(all.length,57); // Never silently truncate the overview to 35.
const top=capScopeEntries(data.entries,'four_family_top');
assert.equal(top.length,16);
assert.equal(capRanking(top,'healthcareAndMedical').n,15);
const argon=top.find(e=>e.releaseSlug==='gemini-4-argon');
assert.equal(capScore(argon,'healthcareAndMedical'),null);
const fable=data.entries.filter(e=>e.releaseSlug==='claude-fable-5-1');
assert.equal(fable.find(e=>e.isTopVariant).effort,'max');
const fableRows=effortRows(fable,'legal',fable.find(e=>e.effort==='xhigh').slug);
assert.equal(fableRows.find(e=>e.best_for_metric).effort,'xhigh');
assert.equal(fableRows.find(e=>e.selected).effort,'xhigh');
assert(fableRows.find(e=>e.effort==='max').delta_score<0);
assert(fableRows.find(e=>e.effort==='max').representative_by_overall_ii);
const missingCost=effortRows([{slug:'low',effort:'low',intelligenceIndex:30,costPerTask:null},{slug:'high',effort:'high',intelligenceIndex:31,costPerTask:2}],'__ii__','high');
assert.equal(missingCost[0].cost_per_task_usd,null);
assert.equal(missingCost[1].delta_cost_usd,null);
const raw=[{slug:'low',effort:'low',intelligenceIndex:99,costPerTask:1,evalMetrics:{SciCode:0}},
 {slug:'high',effort:'high',intelligenceIndex:100,costPerTask:2,evalMetrics:{}}];
assert.equal(capScore(raw[0],'eval:SciCode'),0);
assert.equal(capScore(raw[1],'eval:SciCode'),null);
const rawRows=effortRows(raw,'eval:SciCode','low');
assert(rawRows.every(r=>r.cost_per_task_usd===null && r.delta_cost_usd===null));
assert.equal(rawRows[1].score_status,'missing');
assert.equal(exported[0].__ii___score,99);
assert.equal(exported[0].__ii___valid_n,5);
'''
        result = subprocess.run(['node', '-e', script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_domain_scores_preserved_and_method_labels(self):
        data = json.loads((ROOT / 'report-data.json').read_text())
        variants = {v['slug']: v for r in data['aa_release_series']['releases'] for v in r['variants']}
        for entry in data['aa_capability_indexes']['entries']:
            self.assertEqual(entry['capabilities'], variants[entry['slug']]['capabilities'])
        domains = {d['key']: d for d in data['aa_capability_indexes']['domains']}
        self.assertEqual(len(domains['financeAndAccounting']['coreEvals']), 7)
        self.assertIn('MLCR-AA', domains['healthcareAndMedical']['coreEvals'])
        self.assertFalse(any('SciCode' in e for e in domains['engineering']['coreEvals']))
        self.assertTrue(all(d['weightNote'] and d['methodologyUrl'] for d in domains.values()))

    def test_panorama_summary_follows_official_fields_and_rejects_ambiguous_join(self):
        original = json.loads((ROOT / 'research/2026-10-19/multi-benchmark-supplement.json').read_text())
        multi = copy.deepcopy(original)
        bind_panorama_capabilities(multi)
        rows = multi['external_leaderboards']['four_family_matrix']
        official = multi['aa_capability_indexes']
        for row in rows:
            entry = next(e for e in official['entries'] if e['slug'] == row['aa_cap_variant_slug'])
            self.assertEqual(row['aa_cap_source_url'], entry['sourceUrl'])
            self.assertEqual(row['aa_cap_release_slug'], entry['releaseSlug'])
            self.assertNotIn('#', row['aa_cap_highlights'])
            for domain in official['domains']:
                value = entry['capabilities'].get(domain['key'])
                expected = f"{value:.2f}" if value is not None else '无数据（不参排）'
                self.assertIn(domain['shortLabel'] + ' ' + expected, row['aa_cap_highlights'])
        opus = next(e for e in official['entries'] if e['slug'] == 'claude-opus-5-5')
        opus['capabilities']['economics'] = 42.25
        bind_panorama_capabilities(multi)
        opus_row = next(r for r in rows if r['aa_cap_variant_slug'] == opus['slug'])
        self.assertIn('经济学 42.25', opus_row['aa_cap_highlights'])
        self.assertNotIn('经济学 65.60', opus_row['aa_cap_highlights'])
        official['entries'].append(copy.deepcopy(opus))
        with self.assertRaisesRegex(ValueError, 'one official II representative'):
            bind_panorama_capabilities(multi)
        missing = copy.deepcopy(original)
        missing['external_leaderboards']['four_family_matrix'][0]['aa_cap_release_slug'] = 'unknown-release'
        with self.assertRaisesRegex(ValueError, 'one official II representative'):
            bind_panorama_capabilities(missing)
