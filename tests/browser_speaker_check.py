"""Browser/controller evidence with synthetic speech callbacks, not a hearing test."""
from pathlib import Path
import json,subprocess,os,sys,time,urllib.request
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];OUT=Path(os.getenv('RECOUNT_SPEAKER_OUT','/tmp/recount-speaker'));OUT.mkdir(parents=True,exist_ok=True)
BASE=os.getenv('RECOUNT_SPEAKER_BASE','http://127.0.0.1:8898')
server=None
if BASE=='http://127.0.0.1:8898':
 server=subprocess.Popen([sys.executable,'server.py','--port','8898'],cwd=ROOT,env={**os.environ,'ALLOW_ASSEMBLYAI':'false'},stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 for _ in range(40):
  try:urllib.request.urlopen(BASE+'/api/config',timeout=1);break
  except Exception:time.sleep(.1)
FIXTURE=r'''(()=>{
 const f=window.__speaker={mode:'fail',error:'synthesis-unavailable',sockets:[],utterances:[],tokenRequests:0,microphoneRequests:0,gestures:[]};
 Object.defineProperty(window,'speechSynthesis',{value:{getVoices(){return [];},cancel(){},speak(u){f.utterances.push(u);f.gestures.push(navigator.userActivation.isActive);setTimeout(()=>{if(f.mode==='fail')u.onerror?.({error:f.error});else{u.onstart?.();u.onend?.();}},10);}}});
 navigator.mediaDevices.getUserMedia=async()=>{f.microphoneRequests++;f.ctx=new AudioContext();return f.ctx.createMediaStreamDestination().stream;};
 class Socket{static OPEN=1;constructor(){this.readyState=1;this.bufferedAmount=0;f.sockets.push(this);setTimeout(()=>this.emit({type:'Begin',id:'authored-speaker-test'}),0);}emit(m){return this.onmessage?.({data:JSON.stringify(m)});}send(m){if(typeof m==='string'&&JSON.parse(m).type==='Terminate')setTimeout(()=>this.emit({type:'Termination'}),0);}close(){this.readyState=3;}}
 Object.defineProperty(window,'WebSocket',{value:Socket});
})();'''
checks=[];errors=[]
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(headless=True,executable_path=os.getenv('RECOUNT_BROWSER_PATH'))
  for width,height in [(1360,1000),(390,844)]:
   c=b.new_context(viewport={'width':width,'height':height},accept_downloads=True);c.add_init_script(FIXTURE)
   c.route('**/api/config',lambda r:r.fulfill(json={'voice_enabled':True,'requires_access_code':False,'csrf':'fixture-csrf'}))
   def token(r):
    raise AssertionError('No token should be requested during speaker test')
   c.route('**/api/token',token)
   p=c.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.goto(BASE+'/',wait_until='networkidle');p.locator('summary').click();p.locator('#consent').check()
   expect(p.locator('#listen')).to_be_disabled();checks.append(f'{width}:voice waits for audible-output acknowledgement')
   p.locator('#speakerTest').click();expect(p.locator('#speakerTestStatus')).to_contain_text('synthesis-unavailable');expect(p.locator('#listen')).to_be_disabled()
   assert p.evaluate('__speaker.microphoneRequests===0 && __speaker.sockets.length===0');checks.append(f'{width}:failed speech engine blocks capture before provider access')
   assert p.evaluate('__speaker.gestures[0]===true');checks.append(f'{width}:speaker begins inside user click activation')
   with p.expect_download() as d:p.locator('#voiceReport').click()
   d.value.save_as(OUT/f'failed-{width}.json');r=json.loads((OUT/f'failed-{width}.json').read_text());assert r['summary']['sessions_requested']==0 and r['summary']['speech_output_errors']==1 and r['ledger']['history']==[]
   assert r['events'][-1]['error_code']=='synthesis-unavailable';checks.append(f'{width}:download preserves specific speech failure without count mutations')
   p.evaluate("__speaker.mode='success'");p.locator('#speakerTest').click();expect(p.locator('#speakerHeard')).to_be_visible();expect(p.locator('#listen')).to_be_disabled();checks.append(f'{width}:engine-end callback does not automatically mean user heard it')
   p.locator('#speakerUnheard').click();expect(p.locator('#speakerTestStatus')).to_contain_text('no sound');expect(p.locator('#listen')).to_be_disabled();checks.append(f'{width}:no-sound answer remains a failure not a pass')
   p.locator('#speakerTest').click();p.locator('#speakerHeard').click();expect(p.locator('#listen')).to_be_enabled();checks.append(f'{width}:explicit hearing acknowledgement enables configured consenting voice mode')
   assert p.evaluate('__speaker.microphoneRequests===0 && __speaker.sockets.length===0');checks.append(f'{width}:three output checks made zero microphone/provider attempts')
   p.locator('#speak').uncheck();expect(p.locator('#voiceSetupStatus')).to_contain_text('SILENT REVIEW MODE');p.locator('#speak').check();expect(p.locator('#listen')).to_be_disabled();checks.append(f'{width}:changing reply mode requires a fresh output check')
   assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors;checks.append(f'{width}:mobile and desktop render without overflow or JavaScript error')
   p.screenshot(path=str(OUT/f'speaker-{width}.png'),full_page=True);c.close()
  c=b.new_context(accept_downloads=True);c.add_init_script(FIXTURE);p=c.new_page();p.on('pageerror',lambda e:errors.append(str(e)))
  c.route('**/api/config',lambda r:r.fulfill(json={'voice_enabled':True,'requires_access_code':False,'csrf':'fixture'}))
  c.route('**/api/token',lambda r:r.fulfill(json={'token':'fixture-only','max_session_duration_seconds':90,'speech_model':'universal-3-5-pro'}))
  p.goto(BASE+'/',wait_until='networkidle');p.locator('summary').click();p.evaluate("__speaker.mode='success'");p.locator('#speakerTest').click();p.locator('#speakerHeard').click();p.locator('#consent').check();p.locator('#listen').click();expect(p.locator('#mode')).to_have_text('AUDIO LISTENING')
  p.evaluate("__speaker.mode='fail';__speaker.error='not-allowed'")
  msg={'type':'Turn','turn_order':0,'end_of_turn':True,'transcript':'Rice 12 bags','words':[{'text':x,'confidence':.99,'start':i*60,'end':i*60+50} for i,x in enumerate('Rice 12 bags'.split())]}
  p.evaluate('(m)=>__speaker.sockets[0].emit(m)',msg);expect(p.locator('#mode')).to_have_text('REVIEW REQUIRED');expect(p.locator('#error')).to_contain_text('not-allowed');expect(p.locator('#rows tr')).to_have_count(0);expect(p.locator('#listen')).to_be_disabled();checks.append('runtime: read-back rejection text survives holding the draft and prevents blind restart')
  with p.expect_download() as d:p.locator('#voiceReport').click()
  d.value.save_as(OUT/'runtime-failure.json');r=json.loads((OUT/'runtime-failure.json').read_text());assert any(e['event']=='readback_failed' and e['error_code']=='not-allowed' for e in r['events']);assert r['ledger']['counts']=={} and r['ledger']['hold']=='audio_gap';checks.append('runtime: actual exported report distinguishes speech failure from its generic ledger hold')
  c.close();b.close()
 assert not errors,errors
 r={'status':'passed','checks':checks,'check_count':len(checks),'provider_audio_requests':0,'physical_microphone_used':False,'speaker_output':'synthetic native-speech callbacks including success, unavailable and blocked playback','hearing_claim':False,'scope':'Real app, click handlers, gating, generated silence, browser downloads and mocked speech/provider boundaries. Not the users device or human hearing.'}
 (OUT/'RECEIPT.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
finally:
 if server:server.terminate();server.wait(timeout=5)
