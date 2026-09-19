"""Real browser/app/worklet with generated silence and authored provider messages.
No physical microphone, AssemblyAI request, human audio, or ASR accuracy claim.
"""
import json,os,subprocess,sys,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.getenv('RECOUNT_VOICE_TEST_OUT',str(ROOT/'verification/voice-recovery')));OUT.mkdir(parents=True,exist_ok=True)
PORT=int(os.getenv('RECOUNT_VOICE_TEST_PORT','8881'));BASE=f'http://127.0.0.1:{PORT}'
env={**os.environ,'ALLOW_ASSEMBLYAI':'false'};env.pop('ASSEMBLYAI_API_KEY',None)
p=subprocess.Popen([sys.executable,'server.py','--port',str(PORT)],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
FIXTURE=r'''(() => {
 window.__fixture={speechMode:'complete',tts:[],sockets:[],cancelCount:0,contexts:[],outsideRequests:[]};
 const f=window.__fixture,origTimer=window.setTimeout.bind(window);
 window.setTimeout=(fn,ms,...args)=>origTimer(fn,ms===12000?75:ms,...args);
 Object.defineProperty(window,'speechSynthesis',{value:{speaking:false,cancel(){this.speaking=false;f.cancelCount++;},speak(u){this.speaking=true;f.tts.push(u.text);if(f.speechMode==='complete')origTimer(()=>{this.speaking=false;u.onend?.();},10);}}});
 navigator.mediaDevices.getUserMedia=async()=>{const ctx=new AudioContext();const dest=ctx.createMediaStreamDestination();f.contexts.push(ctx);f.stream=dest.stream;return dest.stream;};
 class Socket {
  static OPEN=1;constructor(url){this.url=url;this.readyState=1;this.bufferedAmount=0;this.sent=[];f.sockets.push(this);origTimer(()=>this.emit({type:'Begin',id:'fixture-browser-'+f.sockets.length}),0);}
  async emit(m){return this.onmessage?.({data:JSON.stringify(m)});}
  send(b){if(typeof b==='string'){const m=JSON.parse(b);this.sent.push(m.type);if(m.type==='Terminate')origTimer(()=>this.emit({type:'Termination',audio_duration_seconds:0,session_duration_seconds:0}),0);}else this.sent.push('synthetic-silence-packet');}
  close(){this.readyState=3;}
 }
 Object.defineProperty(window,'WebSocket',{value:Socket});
})();'''
checks=[];browser_errors=[]
def emit(page,text,order,low=None):
 words=[{'text':w,'confidence':(low if low is not None and w.strip('.,').isdigit() else .99),'start':i*30,'end':i*30+20}for i,w in enumerate(text.split())]
 page.evaluate('(m)=>window.__fixture.sockets.at(-1).emit(m)',{'type':'Turn','turn_order':order,'end_of_turn':True,'transcript':text,'words':words})
 expect(page.locator('#mode')).to_have_text('AUDIO LISTENING')

def context(browser,timeout=False):
 c=browser.new_context(viewport={'width':1360,'height':1050},accept_downloads=True)
 c.add_init_script(FIXTURE)
 def route(q):
  url=q.request.url
  if url.startswith(BASE+'/api/config'):q.fulfill(json={'voice_enabled':True,'requires_access_code':False,'csrf':'synthetic-fixture'})
  elif url.startswith(BASE+'/api/token'):q.fulfill(json={'token':'synthetic-token-not-valid','max_session_duration_seconds':90,'speech_model':'universal-3-5-pro'})
  elif url.startswith(BASE+'/'):q.continue_()
  else:raise AssertionError('Unexpected external HTTP request: '+url.split('?')[0])
 c.route('**/*',route)
 page=c.new_page();page.on('pageerror',lambda e:browser_errors.append(str(e)))
 page.goto(BASE+'/',wait_until='networkidle');page.locator('summary').click();page.locator('#consent').check();page.locator('#speak').check()
 page.locator('#speakerTest').click();page.locator('#speakerHeard').click()
 if timeout:page.evaluate("window.__fixture.speechMode='timeout'")
 page.locator('#listen').click();expect(page.locator('#mode')).to_have_text('AUDIO LISTENING')
 return c,page
try:
 for _ in range(40):
  try:urllib.request.urlopen(BASE+'/api/config',timeout=1);break
  except Exception:time.sleep(.1)
 with sync_playwright() as pw:
  b=pw.chromium.launch(headless=True,executable_path=os.getenv('RECOUNT_BROWSER_PATH'))
  c,page=context(b)
  emit(page,'Rice 11 bags.',0);expect(page.locator('#draft')).to_contain_text('11 bags')
  emit(page,'Confirm 11.',1,low=.60);expect(page.locator('#rows tr')).to_have_count(0);expect(page.locator('#draft')).to_contain_text('11 bags');checks.append('uncertain spoken confirmation preserves draft and writes nothing')
  emit(page,'No.',2);expect(page.locator('#draft')).to_contain_text('?');checks.append('standalone correction clears earlier quantity')
  emit(page,'12 bags.',3);expect(page.locator('#draft')).to_contain_text('12 bags')
  emit(page,'Confirm 11.',4);expect(page.locator('#rows tr')).to_have_count(0);checks.append('old quantity echo cannot confirm corrected draft')
  emit(page,'Confirm 12.',5);expect(page.locator('#rows')).to_contain_text('12');expect(page.locator('#rows tr')).to_have_count(1);checks.append('new clear quantity echo completes corrected count')
  emit(page,'Confirm 12.',5);expect(page.locator('#rows tr')).to_have_count(1);checks.append('duplicate final cannot create second save')
  q=page.evaluate("Object.fromEntries(new URL(window.__fixture.sockets[0].url).searchParams)")
  assert q['min_turn_silence']=='160' and q['max_turn_silence']=='400' and isinstance(json.loads(q['keyterms_prompt']),list);checks.append('actual browser request uses JSON vocabulary and selected development timing')
  page.locator('#listen').click();expect(page.locator('#mode')).to_have_text('TEXT / REVIEW MODE')
  assert page.evaluate('window.__fixture.stream.getTracks().every(t=>t.readyState===\'ended\')');checks.append('normal stop waits for finalization and ends generated capture tracks')
  with page.expect_download() as d:page.locator('#csv').click()
  d.value.save_as(OUT/'voice-retry-stock.csv');assert (OUT/'voice-retry-stock.csv').read_text()=='item,quantity,unit\nRice,12,bags\n';checks.append('actual downloaded CSV contains one corrected record')
  page.screenshot(path=str(OUT/'voice-retry-confirmed.png'),full_page=True);c.close()
  c,page=context(b)
  emit(page,'Beans 8 bags.',0);emit(page,'Confirm 8.',1,low=.60);emit(page,'Soap.',2);expect(page.locator('#reviewRows')).to_contain_text('Beans: 8 bags');checks.append('moving on parks unclear confirmation as a review, not confirmed stock')
  emit(page,'2 bars.',3);emit(page,'Confirm 2.',4);expect(page.locator('#rows tr')).to_have_count(1)
  page.locator('#listen').click();expect(page.locator('#mode')).to_have_text('TEXT / REVIEW MODE')
  page.locator('#reviewRows button').click();expect(page.locator('#draft')).to_contain_text('8 bags');page.locator('#confirm').click();expect(page.locator('#rows tr')).to_have_count(2);checks.append('operator can explicitly review and finish earlier draft after voice stops')
  with page.expect_download() as d:page.locator('#session').click()
  d.value.save_as(OUT/'completed-session.json');page.reload(wait_until='networkidle');page.locator('#load').set_input_files(OUT/'completed-session.json');expect(page.locator('#rows tr')).to_have_count(2);checks.append('mixed voice and explicit operator review replays from versioned history')
  page.screenshot(path=str(OUT/'operator-recovery-confirmed.png'),full_page=True);c.close()
  c,page=context(b,timeout=True)
  words=[{'text':x,'confidence':.99,'start':i*30,'end':i*30+20}for i,x in enumerate('Rice 19 bags.'.split())]
  page.evaluate('(m)=>window.__fixture.sockets.at(-1).emit(m)',{'type':'Turn','turn_order':0,'end_of_turn':True,'transcript':'Rice 19 bags.','words':words})
  expect(page.locator('#mode')).to_have_text('REVIEW REQUIRED');expect(page.locator('#rows tr')).to_have_count(0);expect(page.locator('#confirm')).to_be_disabled();checks.append('timed-out readback holds the draft instead of reopening microphone over TTS')
  assert page.evaluate('!speechSynthesis.speaking && window.__fixture.cancelCount>0 && window.__fixture.stream.getTracks().every(t=>t.readyState===\'ended\')');checks.append('readback timeout cancels speech and stops generated capture tracks')
  page.screenshot(path=str(OUT/'readback-timeout-held.png'),full_page=True);c.close()
  assert not browser_errors,browser_errors;b.close()
 report={'status':'passed','checks':checks,'check_count':len(checks),'provider_requests':0,'human_audio_cases':0,'physical_microphone_used':False,'input':'generated silence and authored final events at mocked provider boundary','speech_output':'mocked SpeechSynthesis callbacks; timeout accelerated to 75 ms for one test','scope':'Actual browser/app/worklet/CSV and recovery-control tests, not speech recognition or field usability.'}
 (OUT/'RECEIPT.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
finally:
 p.terminate();p.wait(timeout=5)
