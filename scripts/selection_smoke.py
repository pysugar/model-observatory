"""Rendered terminology, downloads, and prior guidance; included in release smoke."""
import json
import re
from playwright.sync_api import expect
from capability_smoke import csv_download

STALE = re.compile(r'\bII\b|综合智力指数|综合指数|Intelligence Index')


def audit_panel(page, panel):
    # Original English evidence is intentionally retained in raw methods and glossary.
    texts=page.locator('#'+panel).evaluate('''root => {
      const out=[], walk=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
      while(walk.nextNode()) {
        const n=walk.currentNode;
        if(!n.parentElement.closest('#aaGlossary,#rawmethod,script,style')) out.push(n.textContent);
      }
      for(const n of root.querySelectorAll('[aria-label],[title]')) {
        if(!n.closest('#rawmethod')) out.push(n.getAttribute('aria-label')||'',n.getAttribute('title')||'');
      }
      return out;
    }''')
    leftovers=[t for t in texts if STALE.search(t)]
    assert not leftovers, (panel,leftovers[:8])


def check_selection(page, data, output):
    page.locator('[data-panel="reasoning"]').click()
    expect(page.locator('#adviceMatrix button')).to_have_count(28)
    assert not page.locator('#taskEffortAdvice svg').count(), 'Priors must not become measured curves'
    guidance=data['task_effort_guidance']
    for row in guidance['recommendations']:
        button=page.locator(f'#adviceMatrix [data-advice-model="{row["modelId"]}"][data-advice-task="{row["taskType"]}"]')
        button.click()
        expect(button).to_be_focused()
        expect(button).to_have_attribute('aria-pressed','true')
        expect(page.locator('#adviceModel')).to_have_value(row['modelId'])
        expect(page.locator('#adviceTask')).to_have_value(row['taskType'])
        expect(page.locator('#adviceDetail')).to_contain_text(row['nativeEffort'])
        expect(page.locator('#adviceDetail')).to_contain_text(row['evidenceType'])
        expect(page.locator('#adviceDetail')).to_contain_text('未建立任务最优结论')
        expect(page.locator('#adviceDetail a').first).to_have_attribute('href',row['sourceUrl'])
        assert page.locator('#adviceDetail a[href=""]').count()==0
        if row['modelId']=='grok-4-7':
            assert 'max' not in page.locator('#adviceDetail').inner_text()
    for key,model,task in [('Enter','gpt-6-1-sol','repository_bug'),('Space','claude-fable-5-1','daily_code')]:
        button=page.locator(f'#adviceMatrix [data-advice-model="{model}"][data-advice-task="{task}"]')
        button.focus();page.keyboard.press(key)
        expect(button).to_be_focused()
        expect(button).to_have_attribute('aria-pressed','true')
    page.select_option('#adviceModel','gpt-6-astra')
    expect(page.locator('#adviceDetail')).to_contain_text('未核验官方默认或最佳档位')
    page.select_option('#adviceModel','claude-opus-5')
    expect(page.locator('#adviceDetail')).to_contain_text('暂无版本级建议')
    expect(page.locator('#adviceDetail a')).to_have_count(0)
    expect(page.locator('#adviceMatrix [aria-pressed="true"]')).to_have_count(0)
    page.select_option('#adviceModel','gpt-6-1-sol')
    page.select_option('#adviceTask','repository_bug')
    expect(page.locator('#adviceDetail')).to_contain_text('23 个旧程序重建/修复任务')
    expect(page.locator('#adviceDetail')).to_contain_text('不是代表性真实仓库样本')
    page.locator('#taskEffortAdvice').screenshot(path=str(output/'task-advice-desktop.png'),style='.nav-shell{visibility:hidden!important}')
    page.locator('[data-panel="evidence"]').click()
    guide=page.locator('#benchmarkGuide')
    for text in ('回答是否合意','任务是否省心','结果是否正确','成本是否值得','净改善','原始百分比','用户纠偏负担','未回应不算确认','Bash Reliability','2026-10-12','不从排名推断 effort'):
        expect(guide).to_contain_text(text)
    expect(guide.locator('a')).to_have_count(5)
    guide.screenshot(path=str(output/'benchmark-guide-desktop.png'),style='.nav-shell{visibility:hidden!important}')
    exports={
        'overview':['exportTaskEffort','exportPanorama','exportClaude'],
        'capabilities':['exportEffortScaling','exportCapIndexes','exportProfiles'],
        'explorer':['exportReleases','export'],
        'specs':['exportSpecs'],
        'reasoning':['exportAdvice','exportReasoningEvidence','exportOpusEvidence'],
        'evidence':[],
    }
    downloaded={}
    for panel,buttons in exports.items():
        page.locator(f'[data-panel="{panel}"]').click()
        if panel=='reasoning':
            page.select_option('#reasoningRelease','claude-opus-5-5')
            page.select_option('#reasoningMetric','__ii__')
            page.select_option('#deltaModel','Claude Opus 5.5')
            page.select_option('#deltaGroup','coding')
        audit_panel(page,panel)
        for name in buttons:
            rows=csv_download(page,'#'+name)
            assert rows, name
            headers=list(rows[0])
            assert len(headers)==len(set(headers)), (name,'duplicate headers')
            assert not any(STALE.search(h) or re.search(r'(^|_)ii(_|$)',h) for h in headers), (name,headers)
            downloaded[name]=headers
            if name=='exportAdvice':
                assert len(rows)==28
                assert all(r['sourceUrl'] and r['checkedAt']=='2026-10-20' for r in rows)
                assert json.loads(next(r for r in rows if r['modelId']=='gpt-6-1-sol' and r['taskType']=='repository_bug')['support'])[-1]['sampleSize']==23
    # Dynamic chart states, legends, point descriptions and empty states also stay clear.
    page.locator('[data-panel="overview"]').click()
    page.locator('[data-task-tab="intelligenceIndex"]').click()
    audit_panel(page,'overview')
    page.locator('[data-panel="capabilities"]').click()
    page.select_option('#effortScalingTask','intelligenceIndex')
    audit_panel(page,'capabilities')
    page.locator('[data-panel="explorer"]').click()
    page.locator('[data-group="general"]').click()
    audit_panel(page,'explorer')
    page.locator('#clearAll').click()
    audit_panel(page,'explorer')
    page.locator('#reset').click()
    for width in (390,320):
        touch=page.context.browser.new_page(viewport={'width':width,'height':844},has_touch=True)
        try:
            touch.goto(page.url)
            touch.locator('[data-panel="reasoning"]').tap()
            for row in guidance['recommendations']:
                b=touch.locator(f'#adviceMatrix [data-advice-model="{row["modelId"]}"][data-advice-task="{row["taskType"]}"]')
                b.tap()
                expect(b).to_have_attribute('aria-pressed','true')
                expect(touch.locator('#adviceDetail')).to_contain_text(row['evidenceType'])
            touch.locator('#taskEffortAdvice').screenshot(path=str(output/f'task-advice-touch-{width}.png'),style='.nav-shell{visibility:hidden!important}')
            assert touch.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Advice overflow'
            touch.locator('[data-panel="evidence"]').tap()
            touch.locator('#benchmarkGuide').screenshot(path=str(output/f'benchmark-guide-{width}.png'),style='.nav-shell{visibility:hidden!important}')
            assert touch.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Guide overflow'
        finally:
            touch.close()
    (output/'selection-downloads.json').write_text(json.dumps(downloaded,ensure_ascii=False,indent=2)+'\n')
