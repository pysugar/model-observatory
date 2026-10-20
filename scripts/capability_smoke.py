"""Browser regressions for capability and reasoning views, including exported evidence."""
import csv
import io
from pathlib import Path
from playwright.sync_api import expect


def csv_download(page, selector):
    with page.expect_download() as download:
        page.locator(selector).click()
    return list(csv.DictReader(io.StringIO(Path(download.value.path()).read_text(encoding='utf-8-sig'))))


def check_panorama(page, data):
    cap = data['aa_capability_indexes']
    # Panorama and its CSV must agree with the official representative, not stale prose.
    page.locator('[data-panel="overview"]').click()
    panorama_csv = {r['model']:r for r in csv_download(page, '#exportPanorama')}
    for row in data['external_leaderboards']['four_family_matrix']:
        entry = next(e for e in cap['entries'] if e['slug']==row['aa_cap_variant_slug'])
        summary = row['aa_cap_highlights']
        for domain in cap['domains']:
            score = entry['capabilities'].get(domain['key'])
            value = f'{score:.2f}' if score is not None else '无数据（不参排）'
            assert domain['shortLabel']+' '+value in summary
        expect(page.locator('#panoramaTable tbody tr').filter(has_text=row['model'])).to_contain_text(summary)
        assert panorama_csv[row['model']]['aa_cap_highlights']==summary
        assert panorama_csv[row['model']]['aa_cap_source_url']==entry['sourceUrl']


def check_capabilities(page, data, output):
    cap = data['aa_capability_indexes']
    check_panorama(page, data)
    page.locator('[data-panel="capabilities"]').click()
    for scope, entries in (
        ('four_family_top', [e for e in cap['entries'] if e['isTopVariant'] and e['isFourFamily'] and e['isCurrent']]),
        ('four_family_all', [e for e in cap['entries'] if e['isFourFamily'] and e['isCurrent']]),
        ('all_top', [e for e in cap['entries'] if e['isTopVariant']]),
    ):
        page.select_option('#capIndexScope', scope)
        page.locator('[data-cap-tab="all"]').click()
        expect(page.locator('#capModelPills button')).to_have_count(len(entries))
        exported = {r['model']:r for r in csv_download(page, '#exportCapIndexes')}
        assert len(exported) == len(entries)
        for domain in cap['domains']:
            key = domain['key']
            valid = [e for e in entries if isinstance(e['capabilities'].get(key), (int,float))]
            header = page.locator(f'.cap-denominator[data-domain="{key}"]')
            assert int(header.get_attribute('data-valid-n')) == len(valid)
            expect(page.locator(f'#capBumpChart .cap-node[data-domain="{key}"]')).to_have_count(len(valid))
            for entry in entries:
                row = exported[entry['name']]
                score = entry['capabilities'].get(key)
                assert int(row[key+'_valid_n']) == len(valid)
                assert int(row['comparison_n']) == len(entries)
                if score is None:
                    assert row[key+'_score'] == row[key+'_view_rank'] == ''
                    assert row[key+'_status'] == 'missing'
                    expect(page.locator(f'[data-cap-id="{entry["slug"]}"] .cap-node[data-domain="{key}"]')).to_have_count(0)
                else:
                    rank = 1 + sum(round(v['capabilities'][key],2)>round(score,2) for v in valid)
                    assert float(row[key+'_score']) == score
                    assert int(row[key+'_view_rank']) == rank
            page.locator(f'[data-cap-tab="{key}"]').click()
            expect(page.locator('#capBumpChart .cap-bar')).to_have_count(len(valid))
            for bar in page.locator('#capBumpChart .cap-bar').all():
                group = bar.locator('..')
                slug = group.get_attribute('data-cap-id')
                entry = next(e for e in valid if e['slug']==slug)
                assert float(bar.get_attribute('data-score')) == entry['capabilities'][key]
                assert bar.get_attribute('data-rank') == exported[entry['name']][key+'_view_rank']
            page.locator('[data-cap-tab="all"]').click()
    page.select_option('#capIndexScope','four_family_top')
    argon=page.locator('#capBumpChart [data-cap-id="gemini-4-argon"]')
    assert argon.locator('path').get_attribute('d').count('M')==2, 'Missing domain must break the path'
    argon.locator('.cap-node[data-domain="__ii__"]').focus(); page.keyboard.press('Enter')
    expect(page.locator('#capIndexDetail')).to_contain_text('无数据 · 不参排')
    expect(page.locator('#capIndexDetail')).to_contain_text('15 个有效配置')
    page.locator('#capModelPills [data-cap-model="claude-opus-5-5"]').click()
    expect(page.locator('#capIndexDetail tbody tr')).to_have_count(7)
    point=page.locator('#capBumpChart [data-cap-id="claude-opus-5-5"] .cap-node[data-domain="__ii__"]')
    point.focus()
    expect(page.locator('#capPointTip')).to_contain_text('AA 智能指数')
    expect(page.locator('#capPointTip')).to_contain_text('候选 16')
    page.keyboard.press('Enter')
    expect(page.locator('#capBumpChart [data-cap-id="claude-opus-5-5"] .cap-node[data-domain="__ii__"]')).to_be_focused()
    expect(page.locator('#capIndexDetail')).to_contain_text('完整 7 项指标')
    rows=csv_download(page,'#exportCapIndexes')
    opus=next(r for r in rows if r['model']=='Claude Opus 5.5 (max)')
    assert opus['__ii___score']==opus['intelligence_index']
    assert opus['__ii___valid_n']=='16'

    page.locator('#capBumpChart').screenshot(path=str(output/'capability-desktop.png'),style='.nav-shell{visibility:hidden!important}')
    page.locator('[data-panel="reasoning"]').click()
    page.select_option('#reasoningRelease','claude-fable-5-1')
    page.select_option('#reasoningMetric','legal')
    points=page.locator('#reasoningCurve .reasoning-dot')
    first=points.first
    chosen=first.get_attribute('data-variant')
    first.focus(); page.keyboard.press('Enter')
    expect(page.locator('#reasoningSelected')).to_have_value(chosen)
    expect(page.locator('#reasoningSelected')).to_be_focused()
    rows=csv_download(page,'#exportReasoningEvidence')
    assert sum(r['selected']=='true' for r in rows)==1
    assert next(r for r in rows if r['selected']=='true')['variant']==chosen
    assert next(r for r in rows if r['best_for_metric']=='true')['effort']=='xhigh'
    assert float(next(r for r in rows if r['effort']=='max')['delta_score'])<0
    for row in rows:
        table_row=page.locator(f'#reasoningEvidenceTable tr[data-variant="{row["variant"]}"]')
        expect(table_row).to_have_count(1)
        for selector in ('#reasoningCurve',):
            point=page.locator(f'{selector} [data-variant="{row["variant"]}"]')
            expect(point).to_have_count(1)
            assert float(point.get_attribute('data-score'))==float(row['score'])
    expect(page.locator('#reasoningCostPanel')).to_be_hidden()
    assert all(r['cost_per_task_usd']=='' for r in rows)
    for metric in ("Humanity's Last Exam",'CritPt','Terminal-Bench 4.0','SciCode'):
        page.select_option('#reasoningRelease','claude-opus-5-5')
        page.select_option('#reasoningMetric','eval:'+metric)
        rows=csv_download(page,'#exportReasoningEvidence')
        variants={v['slug']:v for r in data['aa_release_series']['releases'] for v in r['variants']}
        for row in rows:
            value=variants[row['variant']].get('evalMetrics',{}).get(metric)
            assert (float(row['score']) if row['score'] else None)==value
            assert row['cost_per_task_usd']==''
        expect(page.locator('#reasoningCostPanel')).to_be_hidden()
    expect(page.locator('#practicalEvidence')).to_contain_text('暂无直接可比公开成绩')
    page.select_option('#reasoningRelease','gemini-4-argon')
    page.select_option('#reasoningMetric','healthcareAndMedical')
    expect(page.locator('#reasoningCurve .reasoning-dot')).to_have_count(0)
    expect(page.locator('#reasoningCost .reasoning-dot')).to_have_count(0)
    page.select_option('#reasoningRelease','gemini-3-8-flash')
    page.select_option('#reasoningMetric','__ii__')
    expect(page.locator('#reasoningCurve [data-variant="gemini-3-8-flash-low"]')).to_have_count(1)
    expect(page.locator('#reasoningCost [data-variant="gemini-3-8-flash-low"]')).to_have_count(0)
    missing_cost_rows=csv_download(page,'#exportReasoningEvidence')
    assert next(r for r in missing_cost_rows if r['effort']=='low')['cost_per_task_usd']==''
    page.select_option('#reasoningRelease','claude-fable-5-1')
    page.select_option('#reasoningMetric','legal')
    page.locator('#reasoningCharts').screenshot(path=str(output/'reasoning-desktop.png'),style='.nav-shell{visibility:hidden!important}')
    for width in (390,320):
        page.set_viewport_size({'width':width,'height':844})
        page.locator('#reasoningCharts').screenshot(path=str(output/f'reasoning-mobile-{width}.png'),style='.nav-shell{visibility:hidden!important}')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Reasoning page overflow'
        page.locator('[data-panel="capabilities"]').click()
        page.locator('#capIndexCard').screenshot(path=str(output/f'capability-mobile-{width}.png'),style='.nav-shell{visibility:hidden!important}')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Capability page overflow'
        point=page.locator('#capBumpChart [data-cap-id="claude-opus-5-5"] .cap-node[data-domain="economics"]')
        point.dispatch_event('click')
        expect(page.locator('#capPointTip')).to_contain_text('经济学')
        page.locator('[data-panel="reasoning"]').click()
    page.set_viewport_size({'width':1440,'height':1000})

    touch=page.context.browser.new_page(viewport={'width':390,'height':844},has_touch=True)
    try:
        touch.goto(page.url)
        touch.locator('[data-panel="capabilities"]').tap()
        point=touch.locator('#capBumpChart [data-cap-id="claude-opus-5-5"] .cap-node[data-domain="economics"]')
        point.tap()
        expect(touch.locator('#capPointTip')).to_be_visible()
        expect(touch.locator('#capPointTip')).to_contain_text('经济学')
        touch.screenshot(path=str(output/'capability-touch-390.png'))
        touch.locator('[data-panel="reasoning"]').tap()
        touch.locator('#practicalEvidence').screenshot(path=str(output/'practical-evidence-390.png'))
    finally:
        touch.close()
    check_recovery(page, data, output)


def check_recovery(page, data, output):
    """Missing HLE evidence and non-nested point buttons on real report data."""
    old_release = next(r for r in data['aa_release_series']['releases'] if r['releaseSlug']=='claude-opus-5')
    assert old_release['variants'] and all(not v.get('evalMetrics') for v in old_release['variants'])
    page.locator('[data-panel="reasoning"]').click()
    page.select_option('#reasoningRelease', old_release['releaseSlug'])
    page.select_option('#reasoningMetric', "eval:Humanity's Last Exam")
    expect(page.locator('#reasoningCurve .reasoning-dot')).to_have_count(0)
    expect(page.locator('#reasoningEvidenceTable tbody tr')).to_have_count(len(old_release['variants']))
    expect(page.locator('#reasoningEvidenceTable a')).to_have_count(0)
    expect(page.locator('#reasoningEvidenceTable a[href=""]')).to_have_count(0)
    for row in page.locator('#reasoningEvidenceTable tbody tr').all():
        expect(row).to_contain_text('无该指标来源 · 无测量')
        expect(row).to_contain_text('无数据')
    rows=csv_download(page, '#exportReasoningEvidence')
    assert len(rows)==len(old_release['variants'])
    assert all(r['score']==r['source_url']=='' and r['score_status']=='missing' for r in rows)
    page.locator('#reasoningCharts').screenshot(path=str(output/'missing-hle-source.png'),style='.nav-shell{visibility:hidden!important}')
    # Known measurements must retain their real benchmark URLs.
    page.select_option('#reasoningRelease', 'claude-opus-5-5')
    rows=csv_download(page, '#exportReasoningEvidence')
    assert rows and all(r['score'] and r['source_url'].startswith('https://artificialanalysis.ai/models/comparisons/') for r in rows)
    assert page.locator('#reasoningEvidenceTable a').count()==len(rows)
    page.locator('[data-panel="capabilities"]').click()
    page.locator('[data-cap-tab="all"]').click()
    for scope in ('four_family_top','four_family_all','all_top'):
        page.select_option('#capIndexScope', scope)
        assert page.locator('#capBumpChart .cap-node').count()>0
        assert page.locator('#capBumpChart .cap-node').evaluate_all(
            "nodes => nodes.every(n => n.getAttribute('role') === 'button' && !n.parentElement.closest('button,[role=button]'))")
        expect(page.locator('#capBumpChart .bump-group[role="group"][aria-pressed]')).to_have_count(0)
    page.select_option('#capIndexScope','four_family_top')
    for key,slug in (('Enter','claude-opus-5-5'),('Space','gemini-4-argon')):
        point=page.locator(f'#capBumpChart [data-cap-id="{slug}"] .cap-node[data-domain="__ii__"]')
        point.focus(); page.keyboard.press(key)
        expect(point).to_be_focused()
        expect(page.locator('#capPointTip')).to_be_visible()
        expect(page.locator(f'#capModelPills [data-cap-model="{slug}"]')).to_have_attribute('aria-pressed','true')
    # Model path clicks still select a model without exposing another button.
    page.locator('#capBumpChart [data-cap-id="claude-opus-5-5"] .bump-path').dispatch_event('click')
    expect(page.locator('#capModelPills [data-cap-model="claude-opus-5-5"]')).to_have_attribute('aria-pressed','true')
    page.locator('[data-cap-tab="legal"]').click()
    for key,slug in (('Enter','gemini-4-argon'),('Space','claude-opus-5-5')):
        bar=page.locator(f'#capBumpChart .bump-group[data-cap-id="{slug}"]')
        expect(bar).to_have_attribute('role','button')
        bar.focus(); page.keyboard.press(key)
        expect(page.locator(f'#capModelPills [data-cap-model="{slug}"]')).to_have_attribute('aria-pressed','true')
    page.locator('[data-cap-tab="all"]').click()
    for width in (390,320):
        touch=page.context.browser.new_page(viewport={'width':width,'height':844},has_touch=True)
        try:
            touch.goto(page.url)
            touch.locator('[data-panel="capabilities"]').tap()
            point=touch.locator('#capBumpChart [data-cap-id="claude-opus-5-5"] .cap-node[data-domain="economics"]')
            point.tap()
            expect(point).to_be_focused()
            expect(touch.locator('#capPointTip')).to_be_visible()
            expect(touch.locator('#capPointTip')).to_contain_text('经济学')
            expect(touch.locator('#capModelPills [data-cap-model="claude-opus-5-5"]')).to_have_attribute('aria-pressed','true')
            assert touch.evaluate('document.documentElement.scrollWidth <= innerWidth')
            touch.screenshot(path=str(output/f'non-nested-touch-{width}.png'))
        finally:
            touch.close()
