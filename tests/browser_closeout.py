"""Actual browser and downloads; text commands only, no microphone or provider calls."""
import json, os, subprocess, sys, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.getenv('RECOUNT_CLOSEOUT_OUT', '/tmp/recount-closeout-browser'))
OUT.mkdir(parents=True, exist_ok=True)
BASE = 'http://127.0.0.1:8924'
env = {**os.environ, 'ALLOW_ASSEMBLYAI': 'false'}
env.pop('ASSEMBLYAI_API_KEY', None)
server = subprocess.Popen([sys.executable, 'server.py', '--port', '8924'], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
checks, errors = [], []

def save_download(page, selector, target):
    with page.expect_download() as event:
        page.locator(selector).click()
    event.value.save_as(target)

try:
    for _ in range(40):
        try:
            urllib.request.urlopen(BASE + '/api/config', timeout=1)
            break
        except Exception:
            time.sleep(.1)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=os.getenv('RECOUNT_BROWSER_PATH'))
        for width, height in [(1440, 1080), (390, 844)]:
            ctx = browser.new_context(viewport={'width': width, 'height': height}, accept_downloads=True)
            page = ctx.new_page()
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(BASE, wait_until='networkidle')
            def command(text):
                page.locator('#utterance').fill(text)
                page.locator('#textForm button').click()
            expect(page.locator('#closeoutBadge')).to_have_text('0 / 4 resolved')
            expect(page.locator('#completeCSV')).to_be_disabled()
            assert page.locator('.closeout-not_counted').count() == 4
            checks.append(f'{width}: uncounted is not silently interpreted as zero')
            command('beans 27 bags')
            command('oil')
            expect(page.locator('#reviewRows')).to_contain_text('Beans: 27 bags')
            command('16 bottles')
            command('confirm 15')
            expect(page.locator('#rows tr')).to_have_count(0)
            command('confirm 16')
            expect(page.locator('#rows tr')).to_have_count(1)
            expect(page.locator('#closeoutBadge')).to_have_text('1 / 4 resolved')
            checks.append(f'{width}: switching items preserves an unfinished count; mismatched confirmation does not save')
            command('soap zero bars')
            command('confirm zero')
            expect(page.locator('#rows tr')).to_have_count(2)
            assert '0 bars confirmed' in page.locator('#closeoutRows').inner_text()
            assert page.locator('.closeout-not_counted').count() == 1
            save_download(page, '#handoff', OUT / f'partial-handoff-{width}.json')
            partial = json.loads((OUT / f'partial-handoff-{width}.json').read_text())
            assert partial['totals'] == {'scope':4, 'confirmed':2, 'needs_review':1, 'not_counted':1}
            assert next(r for r in partial['rows'] if r['sku']=='rice')['confirmed_quantity'] is None
            assert next(r for r in partial['rows'] if r['sku']=='soap')['confirmed_quantity'] == 0
            assert partial['complete'] is False
            checks.append(f'{width}: downloaded handoff distinguishes confirmed, open and never-counted items')
            page.screenshot(path=str(OUT / f'partial-{width}.png'), full_page=True)
            save_download(page, '#session', OUT / f'session-{width}.json')
            page.reload(wait_until='networkidle')
            page.locator('#load').set_input_files(OUT / f'session-{width}.json')
            expect(page.locator('#closeoutBadge')).to_have_text('2 / 4 resolved')
            expect(page.locator('#reviewRows')).to_contain_text('Beans: 27 bags')
            page.locator('#reviewRows button').first.click()
            expect(page.locator('#rows tr')).to_have_count(2)
            page.locator('#confirm').click()
            expect(page.locator('#closeoutBadge')).to_have_text('3 / 4 resolved')
            expect(page.locator('#completeCSV')).to_be_disabled()
            checks.append(f'{width}: saved session recovers unfinished work and resume alone cannot confirm it')
            command('rice 41 bags')
            command('confirm 41')
            expect(page.locator('#completeCSV')).to_be_enabled()
            expect(page.locator('#closeoutBadge')).to_have_text('4 / 4 resolved')
            save_download(page, '#completeCSV', OUT / f'complete-{width}.csv')
            rows = (OUT / f'complete-{width}.csv').read_text().splitlines()
            assert rows[0] == 'item,quantity,unit'
            assert set(rows[1:]) == {'Cooking oil,16,bottles', 'Soap,0,bars', 'Beans,27,bags', 'Rice,41,bags'}
            save_download(page, '#handoff', OUT / f'complete-handoff-{width}.json')
            full = json.loads((OUT / f'complete-handoff-{width}.json').read_text())
            assert full['complete'] and full['totals']['confirmed'] == 4
            assert next(r for r in full['rows'] if r['sku']=='beans')['confirmation_method'] == 'on_screen'
            assert next(r for r in full['rows'] if r['sku']=='oil')['confirmation_method'] == 'typed'
            assert not any(k in (OUT / f'complete-handoff-{width}.json').read_text() for k in ['csrf','access_code','confirm 41'])
            checks.append(f'{width}: complete export is gated by all four scoped items; manual and typed confirmation stay distinct')
            page.screenshot(path=str(OUT / f'complete-{width}.png'), full_page=True)
            command('oil 17 bottles')
            expect(page.locator('#completeCSV')).to_be_disabled()
            expect(page.locator('#rows')).to_contain_text('16')
            page.locator('#discard').click()
            expect(page.locator('#completeCSV')).to_be_enabled()
            checks.append(f'{width}: a new unresolved draft reopens closeout without changing confirmed stock')
            assert not errors, errors
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            checks.append(f'{width}: no uncaught JavaScript errors or horizontal overflow')
            ctx.close()
        browser.close()
    receipt = {'status':'passed', 'check_count':len(checks), 'checks':checks,
               'provider_calls':0, 'human_audio_cases':0,
               'scope':'Actual Chromium, loopback application, typed multi-item workflow and real downloads; not live ASR or physical stock validation.'}
    (OUT / 'RECEIPT.json').write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt))
except Exception as exc:
    (OUT / 'FAILURE.json').write_text(json.dumps({'status':'failed','error':str(exc),'page_errors':errors,'completed_checks':checks}, indent=2))
    raise
finally:
    server.terminate()
    server.wait(timeout=5)
