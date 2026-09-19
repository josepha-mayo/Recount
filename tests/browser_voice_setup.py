"""Authored UI inputs only. No microphone, provider calls or actual secrets."""
from pathlib import Path
import json,subprocess,sys,time,urllib.request,os
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1];out=Path(os.getenv('RECOUNT_SETUP_OUT','/tmp/recount-setup-browser'));out.mkdir(parents=True,exist_ok=True)
p=subprocess.Popen([sys.executable,'server.py','--port','8896'],cwd=root,env={**os.environ,'ALLOW_ASSEMBLYAI':'false'},stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
checks=[];errors=[];sockets=[]
try:
 for _ in range(40):
  try:urllib.request.urlopen('http://127.0.0.1:8896/api/config',timeout=1);break
  except Exception:time.sleep(.15)
 with sync_playwright() as pw:
  b=pw.chromium.launch(headless=True)
  for width,height in [(1360,1000),(390,844)]:
   ctx=b.new_context(viewport={'width':width,'height':height},accept_downloads=True);page=ctx.new_page()
   page.on('pageerror',lambda e:errors.append(str(e)));page.on('websocket',lambda w:sockets.append(w.url.split('?')[0]))
   page.route('**/api/config',lambda route:route.fulfill(json={'voice_enabled':False,'requires_access_code':True,'csrf':'fixture-only'}))
   page.goto('http://127.0.0.1:8896/',wait_until='networkidle');page.locator('summary').click()
   expect(page.locator('#speak')).to_be_checked();expect(page.locator('#voiceSetup #speak')).to_have_count(1);expect(page.locator('#voiceSetupStatus')).to_contain_text('Voice replies ON');checks.append(f'{width}:spoken replies enabled beside voice controls')
   page.locator('#speak').uncheck();expect(page.locator('#voiceSetupStatus')).to_contain_text('SILENT REVIEW MODE');checks.append(f'{width}:silent mode is explicitly visible')
   page.locator('#speak').check();dummy='recount-FIXTURE-NOT-A-SECRET-123';page.locator('#utterance').fill(dummy);page.locator('#textForm button').click()
   expect(page.locator('#accessCode')).to_have_value(dummy);expect(page.locator('#accessCode')).to_have_attribute('type','password');expect(page.locator('#last')).to_contain_text('Waiting for a count.');expect(page.locator('#error')).to_contain_text('Nothing was added');checks.append(f'{width}:misplaced access code goes to password control, not ledger')
   with page.expect_download() as d:page.locator('#session').click()
   d.value.save_as(out/f'empty-{width}.json');empty=json.loads((out/f'empty-{width}.json').read_text());assert empty['history']==[];assert dummy not in json.dumps(empty);checks.append(f'{width}:saved history excludes mistakenly pasted fixture code')
   for text in ['rice thirteen bags','confirm thirteen']:
    page.locator('#utterance').fill(text);page.locator('#textForm button').click()
   expect(page.locator('#rows tr')).to_have_count(1)
   with page.expect_download() as d:page.locator('#csv').click()
   d.value.save_as(out/f'count-{width}.csv');assert (out/f'count-{width}.csv').read_text()=='item,quantity,unit\nRice,13,bags\n';checks.append(f'{width}:ordinary count and CSV unchanged')
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors and not sockets;checks.append(f'{width}:no overflow, uncaught errors or provider connection')
   page.locator('#accessCode').fill('');page.screenshot(path=str(out/f'setup-{width}.png'),full_page=True);ctx.close()
  b.close()
 (out/'RECEIPT.json').write_text(json.dumps({'status':'passed','checks':checks,'count':len(checks),'provider_audio_calls':0,'scope':'Actual Chromium with authored text inputs and mocked configuration only. No human speech validation.'},indent=2));print(json.dumps({'status':'passed','checks':len(checks)}))
finally:p.terminate();p.wait(timeout=5)
