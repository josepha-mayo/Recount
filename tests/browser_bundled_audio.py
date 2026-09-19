"""Actual Web Audio output and UI. Mock ASR/input only, never mock speech audio.
An analyser signal demonstrates decoded output, not a person hearing the device.
"""
import hashlib,json,os,subprocess,sys,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];OUT=Path(os.getenv('RECOUNT_AUDIO_OUT','/tmp/recount-audio'));OUT.mkdir(parents=True,exist_ok=True)
BASE=os.getenv('RECOUNT_AUDIO_BASE','http://127.0.0.1:8901');server=None
if BASE=='http://127.0.0.1:8901':
 server=subprocess.Popen([sys.executable,'server.py','--port','8901'],cwd=ROOT,env={**os.environ,'ALLOW_ASSEMBLYAI':'false'},stdout=subprocess.DEVNULL)
 for _ in range(40):
  try:urllib.request.urlopen(BASE+'/api/config',timeout=1);break
  except Exception:time.sleep(.1)
FIXTURE=r'''(()=>{
 const f=window.__audio={analyzers:[],sources:[],nativeCalls:0,microphoneCalls:0,sockets:[],maxRms:0};
 const Real=window.AudioContext;
 class Context extends Real{
  createAnalyser(){const a=super.createAnalyser();f.analyzers.push(a);return a;}
  createBufferSource(){const s=super.createBufferSource();f.sources.push(s);return s;}
 }
 window.AudioContext=Context;
 Object.defineProperty(window,'speechSynthesis',{value:{getVoices(){return [];},cancel(){},speak(){f.nativeCalls++;throw Error('Native synthesis deliberately disabled');}}});
 setInterval(()=>{for(const a of f.analyzers){try{const x=new Float32Array(a.fftSize);a.getFloatTimeDomainData(x);const rms=Math.sqrt(x.reduce((n,v)=>n+v*v,0)/x.length);f.maxRms=Math.max(f.maxRms,rms);}catch{}}},15);
 navigator.mediaDevices.getUserMedia=async()=>{f.microphoneCalls++;const c=new Real();await c.resume();return c.createMediaStreamDestination().stream;};
 class Socket{static OPEN=1;constructor(){this.readyState=1;this.bufferedAmount=0;f.sockets.push(this);setTimeout(()=>this.emit({type:'Begin',id:'audio-playback-browser'}),0);}emit(m){return this.onmessage?.({data:JSON.stringify(m)});}send(x){if(typeof x==='string'&&JSON.parse(x).type==='Terminate')setTimeout(()=>this.emit({type:'Termination'}),0);}close(){this.readyState=3;}}
 Object.defineProperty(window,'WebSocket',{value:Socket});
})();'''
checks=[];errors=[];token_attempts=[];signals=[]
def routes(c,allow_token=False):
 c.route('**/api/config',lambda q:q.fulfill(json={'voice_enabled':True,'requires_access_code':False,'csrf':'synthetic-test'}))
 def token(q):
  token_attempts.append(q.request.url)
  assert allow_token,'Speaker test must not request ASR token'
  q.fulfill(json={'token':'mock-provider-not-a-real-token','speech_model':'universal-3-5-pro','max_session_duration_seconds':90})
 c.route('**/api/token',token)
def msg(text,n):return {'type':'Turn','turn_order':n,'end_of_turn':True,'transcript':text,'words':[{'text':w,'confidence':.99,'start':i*90,'end':i*90+80} for i,w in enumerate(text.split())]}
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path=os.getenv('RECOUNT_BROWSER_PATH'))
  for width,height in [(1360,1000),(390,844)]:
   c=browser.new_context(viewport={'width':width,'height':height},accept_downloads=True);c.add_init_script(FIXTURE);routes(c,width==1360)
   p=c.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.goto(BASE+'/',wait_until='networkidle');p.locator('summary').click();p.locator('#consent').check()
   expect(p.locator('#voiceEngine')).to_have_value('audio');expect(p.locator('#listen')).to_be_disabled();checks.append(f'{width}:bundled audio is default and requires hearing acknowledgement')
   p.locator('#speakerTest').click();expect(p.locator('#speakerHeard')).to_be_visible(timeout=25000)
   signal=p.evaluate('__audio.maxRms');assert signal>.005,signal;signals.append({'viewport':width,'max_output_rms':signal})
   assert p.evaluate('__audio.nativeCalls===0 && __audio.microphoneCalls===0 && __audio.sockets.length===0');checks.append(f'{width}:actual neural MP3 creates nonzero Web Audio output without device speech or microphone')
   expect(p.locator('#listen')).to_be_disabled();checks.append(f'{width}:audio end does not claim user hearing')
   p.locator('#speakerUnheard').click();expect(p.locator('#listen')).to_be_disabled();checks.append(f'{width}:no-sound acknowledgement stays blocked')
   p.locator('#speakerTest').click();p.locator('#speakerHeard').click(timeout=25000);expect(p.locator('#listen')).to_be_enabled();checks.append(f'{width}:explicit hearing response enables consenting session')
   if width==1360:
    p.locator('#listen').click();expect(p.locator('#mode')).to_have_text('AUDIO LISTENING')
    expect(p.locator('#voiceEngine')).to_be_disabled();checks.append('runtime: reply backend cannot switch mid-session')
    for i,text in enumerate(['Rice 12 bags','No 13 bags','Confirm 13']):
     p.evaluate('(m)=>__audio.sockets[0].emit(m)',msg(text,i));expect(p.locator('#mode')).to_have_text('AUDIO PROMPTING')
     if i<2:expect(p.locator('#rows tr')).to_have_count(0)
     expect(p.locator('#mode')).to_have_text('AUDIO LISTENING',timeout=30000)
    expect(p.locator('#rows tr')).to_have_count(1);expect(p.locator('#rows')).to_contain_text('13');assert p.evaluate('__audio.nativeCalls===0');checks.append('runtime: real audio readbacks complete with mocked recognition and preserve corrected single count')
    p.locator('#listen').click();expect(p.locator('#mode')).to_have_text('TEXT / REVIEW MODE')
   with p.expect_download() as event:p.locator('#voiceReport').click()
   event.value.save_as(OUT/f'audio-{width}.json');report=json.loads((OUT/f'audio-{width}.json').read_text())
   assert any(e.get('playback_backend')=='bundled-neural-audio' for e in report['events']);checks.append(f'{width}:download identifies actual chosen audio backend')
   assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors;p.screenshot(path=str(OUT/f'audio-{width}.png'),full_page=True);checks.append(f'{width}:layout and JavaScript remain valid')
   c.close()
  # A missing clip blocks setup before microphone access and preserves the error.
  c=browser.new_context(accept_downloads=True);c.add_init_script(FIXTURE);routes(c)
  c.route('**/voice/v1/speaker-test.mp3',lambda q:q.fulfill(status=404,body='missing'))
  p=c.new_page();p.goto(BASE+'/',wait_until='networkidle');p.locator('summary').click();p.locator('#speakerTest').click()
  expect(p.locator('#speakerTestStatus')).to_contain_text('audio-load-failed',timeout=15000);expect(p.locator('#listen')).to_be_disabled();assert p.evaluate('__audio.microphoneCalls===0');checks.append('missing asset: error shown and microphone never starts')
  with p.expect_download() as event:p.locator('#voiceReport').click()
  event.value.save_as(OUT/'asset-failure.json');r=json.loads((OUT/'asset-failure.json').read_text());assert any(e.get('error_code')=='audio-load-failed' for e in r['events']);checks.append('missing asset: original error survives report export');c.close()
  browser.close()
 receipt={'status':'passed','checks':checks,'check_count':len(checks),'output_signals':signals,'native_speech_synthesis_calls':0,'real_provider_audio_calls':0,'mock_provider_token_attempts':len(token_attempts),'physical_microphone_used':False,'scope':'Real browser, actual generated MP3 decoding and Web Audio signal. Recognition/input are mocked. No human hearing or real ASR task success claimed.'}
 (OUT/'RECEIPT.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
finally:
 if server:server.terminate();server.wait(timeout=5)
