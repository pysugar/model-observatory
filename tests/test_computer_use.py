"""Frozen publisher Computer Use evidence and scope-limited observed alternatives."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]


class ComputerUseTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((ROOT/'research/2026-10-20/computer-use-evidence.json').read_text())

    def test_exact_fifteen_points_and_missing_protocol_metadata(self):
        s=self.data['openaiSweep']
        self.assertEqual((s['benchmark'],s['release'],s['subset'],s['metric'],s['scoreUnit']),('OSWorld 2.0','v2026.08.08','offline','partial reward','percent'))
        self.assertEqual(s['efforts'],['low','medium','high','xhigh','max'])
        self.assertEqual(s['missingEfforts'],['non-reasoning'])
        expected=[
            ([62.17,69.25,70.02,71.27,73.49],[2.7159,5.3594,6.9064,7.4944,9.4353]),
            ([58.96,66.84,69.56,69.38,71.42],[.4248,.7675,.9613,1.0466,1.2689]),
            ([43.9,54,58.29,60.54,64.43],[1.0117,1.3789,1.7096,2.3002,3.3695]),
        ]
        self.assertEqual(len(s['series']),3)
        for row,(scores,costs) in zip(s['series'],expected):
            self.assertEqual(row['scores'],scores)
            self.assertEqual(row['costUsdPerTask'],costs)
        for k in ['harness','maxSteps','runs','ci']: self.assertIsNone(s[k])
        self.assertEqual(s['provenance'],'provider-reported')

    def test_separate_anthropic_naming_protocol_and_gemini_statistic(self):
        a=self.data['anthropicMax']
        self.assertEqual([(r['partialRewardPct'],r['strictSuccessRatePct']) for r in a['rows']],[(81.8,48.7),(80.7,42.8),(80.1,43.5)])
        self.assertEqual((a['release'],a['tasks'],a['maxSteps'],a['runs'],a['nativeEffort']),('2026-09-10',108,500,5,'max'))
        self.assertEqual(a['resolution'],'1080p')
        self.assertEqual(a['grader'],'Claude Opus 4.8')
        self.assertEqual([r['originalBenchmarkName'] for r in a['sourceRefs']],['OSWorld 2.0','OSWorld 2.1'])
        self.assertEqual([r['pages'] for r in a['sourceRefs']],[[205,206,207],[129,130,131]])
        self.assertIsNone(a['costUsdPerTask']);self.assertIsNone(a['ci'])
        g=self.data['geminiReference']
        self.assertEqual((g['partialRewardPct'],g['statistic'],g['runs']),(69.2,'max over 3 runs',3))
        self.assertIsNone(g['nativeEffort']);self.assertIsNone(g['costUsdPerTask'])
        self.assertIsNone(self.data['grokReference']['score'])
        self.assertEqual(self.data['grokReference']['status'],'未发现公开可核实成绩')
        # Experience sources are separate from comparable benchmark measurements.
        self.assertEqual(self.data['pitfallExperience']['minimumIndependentOriginalSources'],2)
        for c in self.data['pitfallExperience']['cards']:
            self.assertGreaterEqual(len({s['sourceUrl'] for s in c['sources']}),2)

    def test_verified_workflow_cards_and_boundaries(self):
        cards=self.data['pitfallExperience']['cards']
        self.assertEqual([c['title'] for c in cards],['高档不一定靠少重试省钱','设计跑偏，先补上下文与验收标准','账单变大，别只怪模型和档位'])
        expected=[
            ['https://trilogyai.substack.com/p/astra-reasoning-effort-token-usage','https://arxiv.org/html/2608.01347v6#A14'],
            ['https://www.anthropic.com/engineering/harness-design-long-running-apps','https://cursor.com/blog/dynamic-context-discovery'],
            ['https://cursor.com/blog/dynamic-context-discovery','https://www.langchain.com/blog/deep-agents-v0-7'],
        ]
        for c,urls in zip(cards,expected):
            self.assertEqual(c['evidenceType'],'多源经验参考')
            self.assertEqual(c['checkedAt'],'2026-10-20')
            self.assertFalse(c['appliesToAllCurrentModels'])
            self.assertTrue(c['pitfall'] and c['alternativeAction'])
            self.assertTrue(c['modelScope'] and c['taskScope'] and c['versionScope'])
            self.assertTrue(c['caveats'])
            self.assertEqual([s['sourceUrl'] for s in c['sources']],urls)
            self.assertEqual(len({s['originalSourceId'] for s in c['sources']}),2)
            self.assertTrue(all(s['sourceType']=='独立原始来源' for s in c['sources']))
            self.assertNotIn('score',c)
            self.assertNotIn('savingsPct',c)
            self.assertNotRegex(json.dumps(c,ensure_ascii=False),r'\d+(?:\.\d+)?%')
        self.assertEqual((cards[0]['sources'][0]['sampleSize'],cards[0]['sources'][0]['runs']),(2,24))
        self.assertIn('没有盲测质量评估',cards[0]['sources'][0]['caveats'])
        self.assertIn('不是 5.5',cards[0]['sources'][1]['caveats'])
        self.assertIn('未经同行评审',cards[0]['sources'][1]['caveats'])
        self.assertIn('不是 max 与补上下文的受控对照实验',''.join(cards[1]['caveats']))
        self.assertIn('费用可能反而增加',''.join(cards[2]['caveats']))
        self.assertEqual(self.data['pitfallReminders']['cards'],[])

    def test_shared_paths_differences_raw_precision_and_alternatives(self):
        source=(ROOT/'report.js').read_text()
        math=source.split('// BEGIN SCALING_MATH',1)[1].split('// END SCALING_MATH',1)[0]
        script='const assert=require("node:assert/strict");const finite=v=>typeof v==="number"&&Number.isFinite(v);\n'+math+r'''
const data=JSON.parse(require('node:fs').readFileSync('research/2026-10-20/computer-use-evidence.json','utf8'));
const points=osworldSweepPoints(data.openaiSweep), get=id=>points.find(p=>p.id===id);
assert.equal(points.length,15);assert(!points.some(p=>p.effort==='non-reasoning'));
const x=get('gpt-6-1-sol:xhigh'),high=get('gpt-6-1-sol:high');
const r=scalingRows(points.filter(p=>p.modelId===x.modelId),data.openaiSweep.efforts).find(r=>r.effort==='xhigh');
assert.equal(r.deltaScore.toFixed(2),'-0.18');assert.equal(r.deltaCostPct.toFixed(2),'8.87');
assert.deepEqual(observedAlternatives(points,x).map(p=>p.id),[high.id]);
assert.equal(((x.cost-high.cost)/x.cost*100).toFixed(2),'8.15');
const old=get('gpt-6-sol:max'),medium=get('gpt-6-1-sol:medium');
assert.equal(observedAlternatives(points,old)[0].id,medium.id);
assert.equal((medium.score-old.score).toFixed(2),'2.41');
assert.equal(((old.cost-medium.cost)/old.cost*100).toFixed(2),'77.22');
const astra=get('gpt-6-astra:low');assert.equal(observedAlternatives(points,astra)[0].id,medium.id);
assert.equal((medium.score-astra.score).toFixed(2),'4.67');
assert.equal(((astra.cost-medium.cost)/astra.cost*100).toFixed(2),'71.74');
for(const p of points.filter(p=>p.modelId==='gpt-6-astra'))assert.equal(observedAlternatives(points,p).length>0,p.effort!=='max');
for(const p of points) {const a=observedAlternatives(points,p);assert(a.length<=2);assert.equal(new Set(a.map(a=>a.id)).size,a.length);}
const base={...x,id:'base',score:60,cost:2};
assert.deepEqual(observedAlternatives([{...base,id:'equal'}],base),[]); // At least one strict inequality.
assert.deepEqual(observedAlternatives([{...base,id:'missing',cost:null,score:99}],base),[]);
assert.deepEqual(observedAlternatives(points,{...base,cost:null}),[]);
for(const extra of [{release:'2026-09-10'},{metric:'strict success rate'},{subset:'full suite'},{costDefinition:'USD/success'},{harness:'other'},{sourceUrl:'https://example.test'}])
 assert.deepEqual(observedAlternatives([{...base,...extra,id:'different',score:99,cost:.01}],base),[]);
assert.deepEqual(observedAlternatives([{...base,id:'rounds-equal-but-lower',score:59.9999999,cost:1}],base),[]);
assert.equal(observedAlternatives([{...base,id:'tiny-strict-increase',score:60.0000001}],base).length,1);
const ties=['z','a'].map(id=>({...base,id,score:61,cost:1}));assert.deepEqual(observedAlternatives(ties,base).map(p=>p.id),['a']);
assert.deepEqual(observedAlternatives(points,{...base,protocolId:'other'}),[]);
const gap=[{effort:'low',score:0},{effort:'high',score:3}];
assert.equal(scalingPath(gap,['low','medium','high'],i=>i,v=>v),'M0,0 M2,3');
assert.equal(scalingRows(gap,['low','medium','high'])[2].deltaScore,null);
assert.equal(scalingRows(gap,['low','medium','high'])[1].score,null);
assert.equal(scalingPath([{effort:'high',score:3}],['low','medium','high'],i=>i,v=>v),'M2,3');
'''
        result=subprocess.run(['node','-e',script],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
