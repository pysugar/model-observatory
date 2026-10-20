"""Browser regressions for capability and reasoning views, including exported evidence."""
import csv
import io
from pathlib import Path
from playwright.sync_api import expect


def csv_download(page, selector):
    with page.expect_download() as download:
        page.locator(selector).click()
    return list(csv.DictReader(io.StringIO(Path(download.value.path()).read_text(encoding='utf-8-sig'))))


def check_capabilities(page, data, output):
    cap = data['aa_capability_indexes']
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
    argon.focus(); page.keyboard.press('Enter')
    expect(page.locator('#capIndexDetail')).to_contain_text('无数据 · 不参排')
    expect(page.locator('#capIndexDetail')).to_contain_text('15 个有效配置')
    page.locator('#capModelPills [data-cap-model="claude-opus-5-5"]').click()
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
        for selector in ('#reasoningCurve','#reasoningCost'):
            point=page.locator(f'{selector} [data-variant="{row["variant"]}"]')
            expect(point).to_have_count(1)
            assert float(point.get_attribute('data-score'))==float(row['score'])
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
        page.locator('[data-panel="reasoning"]').click()
    page.set_viewport_size({'width':1440,'height':1000})
