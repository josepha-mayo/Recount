"""Actual Chromium/app/audio-worklet; generated silence and mocked ASR/TTS.
Tests asynchronous callback ordering and user-downloaded report bytes, not speech accuracy.
"""
import json,os,subprocess,sys,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.getenv('RECOUNT_BARRIER_OUT',str(ROOT/'verification/readback-barrier')));OUT.mkdir(parents=True,exist_ok=True)
BASE='http://127.0.0.1:8891'
env={**os.environ,'ALLOW_ASSEMBLYAI':'false'};env.pop('ASSEMBLYAI_API_KEY',None)
p=subprocess.Popen([sys.executable,'server.py','--port','8891'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
FIXTURE=r'''(()=>{
 const f=window.__barrier={utterances:[],sockets:[],cancellations:0};
 Object.defineProperty(window,'speechSynthesis',{value:{speak(u){f.utterances.push(u);},cancel(){f.cancellations++;}}});
 navigator.mediaDevices.getUserMedia=async()=>{f.audio=new AudioContext();const d=f.audio.createMediaStreamDestination();f.stream=d.stream;return d.stream;};
 class Socket{static OPEN=1;constructor(){this.readyState=1;this.bufferedAmount=0;f.sockets.push(this);setTimeout(()=>this.emit({type:'Begin',id:'authored-browser-session'}),0);}emit(m){return this.onmessage?.({data:JSON.stringify(m)});}close(){this.readyState=3;}send(m){if(typeof m==='string'&&JSON.parse(m).type==='Terminate')setTimeout(()=>this.emit({type:'Termination'}),0);}}
 Object.defineProperty(window,'WebSocket',{value:Socket});
})();'''
checks=[];errors=[]
def emit(page,text,order):
 msg={'type':'Turn','turn_order':order,'end_of_turn':True,'transcript':text,'words':[{'text':w,'confidence':.99,'start':i*50,'end':i*50+40}for i,w in enumerate(text.split())]}
 page.evaluate('(m)=>{void window.__barrier.sockets[0].emit(m);}',msg)
def open_session(browser,width):
 ctx=browser.new_context(viewport={'width':width,'height':1000},accept_downloads=True);ctx.add_init_script(FIXTURE)
 def route(q):
  if q.request.url==BASE+'/api/config':q.fulfill(json={'voice_enabled':True,'requires_access_code':False,'csrf':'PRIVATE_CSRF_SENTINEL'})
  elif q.request.url==BASE+'/api/token':q.fulfill(json={'token':'PRIVATE_PROVIDER_SENTINEL','max_session_duration_seconds':90,'speech_model':'universal-3-5-pro'})
  elif q.request.url.startswith(BASE+'/'):q.continue_()
  else:raise AssertionError('Unexpected external request')
 ctx.route('**/*',route);page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(BASE+'/',wait_until='networkidle');page.locator('summary').click();page.locator('#voiceEngine').select_option('native');page.locator('#consent').check();page.locator('#speak').check();page.locator('#speakerTest').click();page.evaluate('window.__barrier.utterances.at(-1).onend()');page.locator('#speakerHeard').click();page.evaluate('window.__barrier.utterances=[]');page.locator('#listen').click();expect(page.locator('#mode')).to_have_text('AUDIO LISTENING')
 return ctx,page
try:
 for _ in range(40):
  try:urllib.request.urlopen(BASE+'/api/config',timeout=1);break
  except Exception:time.sleep(.1)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path=os.getenv('RECOUNT_BROWSER_PATH'))
  for width in [1360,390]:
   ctx,page=open_session(browser,width)
   emit(page,'Rice 12 bags.',0);expect(page.locator('#mode')).to_have_text('AUDIO PROMPTING')
   emit(page,'Confirm 12.',1);expect(page.locator('#mode')).to_have_text('REVIEW REQUIRED');expect(page.locator('#rows tr')).to_have_count(0);checks.append(f'{width}:confirmation before spoken reply finishes cannot save')
   page.evaluate('window.__barrier.utterances[0].onend()');expect(page.locator('#mode')).to_have_text('REVIEW REQUIRED');expect(page.locator('#confirm')).to_be_disabled();checks.append(f'{width}:late old speech completion cannot release hold')
   expect(page.locator('#voiceReport')).to_be_enabled()
   with page.expect_download() as d:page.locator('#voiceReport').click()
   dest=OUT/f'premature-{width}.json';d.value.save_as(dest);raw=dest.read_text();r=json.loads(raw)
   assert r['summary']['premature_confirmations_rejected']==1 and r['ledger']['counts']=={} and r['ledger']['hold']=='stale_turn'
   expected_assets={'app.mjs','core.mjs','capture-gate.mjs','voice-runtime.mjs','readback.mjs','voice-audit.mjs','audio-worklet.js','streaming-request.mjs','speaker-check.mjs','audio-readback.mjs','startup-errors.mjs'}
   assert set(r['asset_sha256'])==expected_assets and 'PRIVATE_CSRF_SENTINEL' not in raw and 'PRIVATE_PROVIDER_SENTINEL' not in raw
   assert r['privacy']['audio_in_report'] is False;checks.append(f'{width}:download includes held ledger and hashes but no credentials or audio')
   page.screenshot(path=str(OUT/f'held-{width}.png'),full_page=True);ctx.close()
   ctx,page=open_session(browser,width)
   emit(page,'Rice 12 bags.',0);expect(page.locator('#mode')).to_have_text('AUDIO PROMPTING')
   emit(page,'No 13 bags.',1);expect(page.locator('#draft')).to_contain_text('13 bags');page.wait_for_function('window.__barrier.utterances.length===2')
   page.evaluate('window.__barrier.utterances[0].onend()');expect(page.locator('#mode')).to_have_text('AUDIO PROMPTING');checks.append(f'{width}:new correction replaces old read-back without premature resume')
   page.evaluate('window.__barrier.utterances[1].onend()');expect(page.locator('#mode')).to_have_text('AUDIO LISTENING')
   emit(page,'Confirm 13.',2);expect(page.locator('#rows tr')).to_have_count(1);expect(page.locator('#rows')).to_contain_text('13');page.wait_for_function('window.__barrier.utterances.length===3')
   page.evaluate('window.__barrier.utterances[2].onend()');expect(page.locator('#mode')).to_have_text('AUDIO LISTENING');checks.append(f'{width}:fresh echo after completed replacement reply saves exactly one corrected count')
   page.locator('#listen').click();expect(page.locator('#mode')).to_have_text('TEXT / REVIEW MODE')
   with page.expect_download() as d:page.locator('#voiceReport').click()
   dest=OUT/f'completed-{width}.json';d.value.save_as(dest);r=json.loads(dest.read_text())
   assert r['summary']['completed_readbacks']==2 and r['summary']['provider_begins']==1 and r['ledger']['counts']['rice']['quantity']==13
   assert r['summary']['final_events']==3;checks.append(f'{width}:report distinguishes final transcripts, cancelled reply and actual completed callbacks')
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(OUT/f'confirmed-{width}.png'),full_page=True);ctx.close()
  browser.close()
 assert not errors,errors
 report={'status':'passed','check_count':len(checks),'checks':checks,'provider_audio_requests':0,'human_speaker_cases':0,'input':'generated silence; mocked provider and speech callbacks','scope':'Actual browser/app/worklet, asynchronous delivery order and downloaded report checks; not live ASR or human validation.'}
 (OUT/'RECEIPT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
finally:p.terminate();p.wait(timeout=5)
