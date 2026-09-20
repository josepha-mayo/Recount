"""Real browser with mocked authorization, capture and ASR. No human audio."""
import json,os,subprocess,sys,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];OUT=Path(os.getenv('RECOUNT_STARTUP_OUT','/tmp/recount-startup-browser'));OUT.mkdir(parents=True,exist_ok=True);BASE='http://127.0.0.1:8913'
server=subprocess.Popen([sys.executable,'server.py','--port','8913'],cwd=ROOT,env={**os.environ,'ALLOW_ASSEMBLYAI':'false'},stdout=subprocess.DEVNULL)
FIXTURE=r'''(()=>{const f=window.__startup={sockets:[],streams:[],contexts:[]};navigator.mediaDevices.getUserMedia=async()=>{const c=new AudioContext(),d=c.createMediaStreamDestination();f.contexts.push(c);f.streams.push(d.stream);return d.stream;};class Socket{static OPEN=1;constructor(){this.readyState=1;this.bufferedAmount=0;f.sockets.push(this);setTimeout(()=>this.emit({type:'Begin',id:'synthetic-session'}),0);}async emit(m){await this.onmessage?.({data:JSON.stringify(m)});}send(m){if(typeof m==='string'&&JSON.parse(m).type==='Terminate')setTimeout(()=>this.emit({type:'Termination'}),0);}close(){this.readyState=3;}}Object.defineProperty(window,'WebSocket',{value:Socket});})();'''
checks=[];errors=[];p=None
try:
 for _ in range(40):
  try:urllib.request.urlopen(BASE+'/api/config',timeout=1);break
  except Exception:time.sleep(.1)
 with urllib.request.urlopen(BASE+'/startup-errors.mjs',timeout=2) as r:assert r.status==200 and 'javascript' in r.headers['Content-Type']
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path=os.getenv('RECOUNT_BROWSER_PATH'))
  for width,height in [(1360,1000),(390,844)]:
   c=browser.new_context(viewport={'width':width,'height':height},accept_downloads=True);c.add_init_script(FIXTURE);allowed={'value':False}
   c.route('**/api/config',lambda q:q.fulfill(json={'voice_enabled':True,'requires_access_code':True,'csrf':'synthetic-csrf'}))
   def token(q):
    assert q.request.post_data_json['access_code']=='synthetic-private-code'
    if not allowed['value']:q.fulfill(status=403,json={'error':'Invalid judge access code.'})
    else:q.fulfill(json={'token':'synthetic-provider-token','max_session_duration_seconds':90,'speech_model':'universal-3-5-pro'})
   c.route('**/api/token',token);p=c.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.goto(BASE,wait_until='networkidle');assert not errors,errors;p.locator('summary').click();p.locator('#speak').uncheck();p.locator('#consent').check();p.locator('#accessCode').fill('synthetic-private-code');p.locator('#listen').click()
   expect(p.locator('#error')).to_have_text('Invalid judge access code.');expect(p.locator('#mode')).to_have_text('REVIEW REQUIRED');assert p.evaluate('__startup.sockets.length===0 && __startup.streams.every(s=>s.getTracks().every(t=>t.readyState==="ended"))');checks.append(f'{width}:error persists after hold and capture cleanup; no socket opened');p.screenshot(path=str(OUT/f'authorization-error-{width}.png'),full_page=True)
   with p.expect_download() as event:p.locator('#voiceReport').click()
   event.value.save_as(OUT/f'authorization-error-{width}.json');data=(OUT/f'authorization-error-{width}.json').read_text();r=json.loads(data);assert any(e.get('failure_code')=='invalid_access_code' for e in r['events']);assert 'synthetic-private-code' not in data and 'synthetic-csrf' not in data;checks.append(f'{width}:report includes failure class without credentials')
   allowed['value']=True;p.locator('#listen').click();expect(p.locator('#mode')).to_have_text('AUDIO LISTENING')
   for n,text in enumerate(['Rice 12 bags','No 13 bags','Confirm 13']):
    m={'type':'Turn','turn_order':n,'end_of_turn':True,'transcript':text,'words':[{'text':w,'confidence':.99}for w in text.split()]};p.evaluate('(m)=>__startup.sockets.at(-1).emit(m)',m);expect(p.locator('#mode')).to_have_text('AUDIO LISTENING')
   expect(p.locator('#rows tr')).to_have_count(1);expect(p.locator('#rows')).to_contain_text('13');p.locator('#listen').click();expect(p.locator('#mode')).to_have_text('TEXT / REVIEW MODE')
   with p.expect_download() as event:p.locator('#csv').click()
   event.value.save_as(OUT/f'retry-{width}.csv');assert (OUT/f'retry-{width}.csv').read_text()=='item,quantity,unit\nRice,13,bags\n';checks.append(f'{width}:accepted mocked retry exports exactly one Rice 13 row');p.screenshot(path=str(OUT/f'retry-success-{width}.png'),full_page=True);assert not errors;assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');checks.append(f'{width}:no JavaScript errors or horizontal overflow');c.close()
  browser.close()
 receipt={'status':'passed','check_count':len(checks),'checks':checks,'provider_requests':0,'human_audio_cases':0,'physical_microphone_used':False,'scope':'Real browser/app/downloads; authorization, microphone and ASR mocked. Not live authorization or human speech proof.'};(OUT/'RECEIPT.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
except Exception as e:
 (OUT/'FAILURE.json').write_text(json.dumps({'status':'failed','error':str(e),'page_errors':errors,'completed_checks':checks},indent=2));raise
finally:server.terminate();server.wait(timeout=5)
