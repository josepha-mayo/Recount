from pathlib import Path
root=Path.cwd()
def replace(path,old,new):
 p=root/path;s=p.read_text();assert s.count(old)==1,(path,old[:90],s.count(old));p.write_text(s.replace(old,new))
p=root/'web/readback.mjs';s=p.read_text();s=s[:s.index('export class ReadbackPlayer')]+'''export const SPEECH_ERRORS = new Set(['canceled','interrupted','audio-busy','audio-hardware','network',
  'synthesis-unavailable','synthesis-failed','language-unavailable','voice-unavailable','text-too-long',
  'invalid-argument','not-allowed','speech-start-timeout','speech-timeout','speech-unavailable','unknown']);
export function speechErrorCode(value){return SPEECH_ERRORS.has(value)?value:'unknown';}
export function speechErrorMessage(code){
  const messages={
    'not-allowed':'The browser blocked spoken audio. Tap Test speaker directly to allow it.',
    'synthesis-unavailable':'This browser has no working speech engine. Voice replies cannot start here.',
    'synthesis-failed':'The device speech engine failed to produce audio.',
    'speech-unavailable':'Spoken audio is not supported by this browser.',
    'language-unavailable':'No usable English speech voice is available in this browser.',
    'voice-unavailable':'The selected speech voice is unavailable.',
    'audio-busy':'The browser could not access the audio output device.',
    'audio-hardware':'The browser could not find a working audio output device.',
    'network':'The device speech service could not complete its network request.',
    'speech-start-timeout':'The speech engine timed out before reporting that audio started.',
    'speech-timeout':'Spoken audio timed out before completing and was cancelled.',
    'canceled':'The speech engine cancelled the reply before it started.',
    'interrupted':'The speech engine interrupted the reply.',
  };
  return (messages[code]||'Spoken audio failed to complete.')+' ['+speechErrorCode(code)+']';
}
function failure(code,message){const e=new Error(message||speechErrorMessage(code));e.code=speechErrorCode(code);return e;}
export class ReadbackPlayer {
  constructor({synth=globalThis.speechSynthesis,Utterance=globalThis.SpeechSynthesisUtterance,
    setTimer=globalThis.setTimeout.bind(globalThis),clearTimer=globalThis.clearTimeout.bind(globalThis),timeoutMs=12000}={}){
    Object.assign(this,{synth,Utterance,setTimer,clearTimer,timeoutMs});this.current=null;
  }
  availableVoices(){try{return Array.from(this.synth?.getVoices?.()||[]);}catch{return [];}}
  capabilities(){const voices=this.availableVoices();return {supported:Boolean(this.synth&&this.Utterance),
    voice_count:voices.length,english_voice_count:voices.filter(v=>/^en(?:[-_]|$)/i.test(v.lang||'')).length};}
  cancel(){
    const v=this.current;
    if(v&&!v.done){v.done=true;this.current=null;this.clearTimer(v.timer);try{this.synth?.cancel();}catch{}v.resolve({status:'cancelled'});}
    else{try{this.synth?.cancel();}catch{}}
  }
  speak(text){
    this.cancel();
    if(!this.synth||!this.Utterance)return Promise.resolve({status:'unavailable',code:'speech-unavailable'});
    return new Promise((resolve,reject)=>{
      const v={done:false,started:false,resolve,reject,timer:null,utterance:null};this.current=v;
      const finish=(ok,code,message)=>{
        if(v.done)return;v.done=true;this.clearTimer(v.timer);if(this.current===v)this.current=null;
        if(!ok){try{this.synth.cancel();}catch{}reject(failure(code,message));}
        else resolve({status:'completed',start_event_observed:v.started});
      };
      try{
        const u=new this.Utterance(conciseReadback(text));v.utterance=u;
        const voices=this.availableVoices(),english=voices.filter(v=>/^en(?:[-_]|$)/i.test(v.lang||''));
        const selected=english.find(v=>v.default)||english.find(v=>v.localService)||english[0];
        if(selected)u.voice=selected;
        u.lang=selected?.lang||'en-US';u.rate=.88;u.pitch=1;u.volume=1;
        u.onstart=()=>{if(!v.done)v.started=true;};
        u.onend=()=>finish(true);
        u.onerror=event=>finish(false,speechErrorCode(event?.error));
        v.timer=this.setTimer(()=>finish(false,v.started?'speech-timeout':'speech-start-timeout'),this.timeoutMs);
        if(this.synth.paused)this.synth.resume?.();
        // Called synchronously from Test speaker's click handler. No preceding await.
        this.synth.speak(u);
      }catch(error){finish(false,speechErrorCode(error?.name==='NotAllowedError'?'not-allowed':error?.code),'Read-back audio could not start. ['+speechErrorCode(error?.name==='NotAllowedError'?'not-allowed':error?.code)+']');}
    });
  }
}
''';p.write_text(s)
replace('web/voice-runtime.mjs',"import {normalizeTranscript} from './core.mjs';", "import {normalizeTranscript} from './core.mjs';\nimport {speechErrorCode,speechErrorMessage} from './readback.mjs';")
replace('web/voice-runtime.mjs',"try{result=await this.promptReply();}catch{if(generation!==v.promptGeneration||!this.live(v))return;this.onError('Read-back failed or timed out. Audio stopped; review the held draft.');this.fail(v,'audio_gap');return;}","try{result=await this.promptReply();}catch(error){if(generation!==v.promptGeneration||!this.live(v))return;const code=speechErrorCode(error?.code);this.trace('readback_failed',{code});this.fail(v,'audio_gap');this.onError(speechErrorMessage(code)+' Microphone stopped; the draft is held for review.');return;}")
replace('web/voice-runtime.mjs',"if(result?.status==='unavailable'||result?.status==='cancelled'){this.onError('Read-back did not complete. Stop and review the draft.');this.fail(v,'audio_gap');return;}","if(result?.status==='unavailable'||result?.status==='cancelled'){const code=result.status==='unavailable'?'speech-unavailable':'canceled';this.trace('readback_failed',{code});this.fail(v,'audio_gap');this.onError(speechErrorMessage(code)+' Microphone stopped; review the draft.');return;}")
(root/'web/speaker-check.mjs').write_text('''import {speechErrorCode,speechErrorMessage} from './readback.mjs';
export const SPEAKER_TEST_TEXT='This is Recount. If you can hear this voice, tap I heard it.';
export class SpeakerCheck {
  constructor(player,{onChange=()=>{},onTrace=()=>{}}={}){Object.assign(this,{player,onChange,onTrace});this.generation=0;this.state='untested';this.code=null;}
  ready(){return this.state==='heard';}
  busy(){return this.state==='testing';}
  trace(event,extra={}){try{this.onTrace({event,...extra});}catch{}}
  changed(){this.onChange();}
  reset(){this.generation++;this.player.cancel();this.state='untested';this.code=null;this.changed();}
  async test(){
    const id=++this.generation;this.state='testing';this.code=null;
    const capabilities=this.player.capabilities();this.trace('speaker_test_started',capabilities);this.changed();
    try{
      // Start during the originating click, not after permission/network work.
      const result=await this.player.speak(SPEAKER_TEST_TEXT);
      if(id!==this.generation)return;
      if(result?.status!=='completed')throw Object.assign(new Error('Speaker unavailable'),{code:result?.code||'speech-unavailable'});
      this.state='awaiting_confirmation';this.trace('speaker_test_finished',{status:'completed'});
    }catch(error){if(id!==this.generation)return;this.code=speechErrorCode(error?.code);this.state='failed';this.trace('speaker_test_failed',{code:this.code});}
    this.changed();
  }
  heard(){if(this.state!=='awaiting_confirmation')return false;this.state='heard';this.trace('speaker_test_confirmed');this.changed();return true;}
  unheard(){if(!['awaiting_confirmation','heard'].includes(this.state))return false;this.state='unheard';this.trace('speaker_test_unheard');this.changed();return true;}
  message(){
    if(this.state==='testing')return 'Playing a short speaker test. The microphone is OFF.';
    if(this.state==='awaiting_confirmation')return 'The browser reported playback finished. Did you actually hear the voice?';
    if(this.state==='heard')return 'Speaker test confirmed by you. Voice mode is ready when access and consent are set.';
    if(this.state==='unheard')return 'You reported no sound. Voice mode stays off. Check the media volume/output device; the browser may report completion even without audible output.';
    if(this.state==='failed')return speechErrorMessage(this.code)+' Microphone and transcription have not started for this test.';
    return 'First tap Test speaker. It uses no microphone or AssemblyAI credit.';
  }
}
''')
replace('web/voice-audit.mjs',"/* Local-only, bounded interaction evidence. No audio, credentials or query URLs. */", "import {SPEECH_ERRORS} from './readback.mjs';\n/* Local-only, bounded interaction evidence. No audio, credentials or query URLs. */")
replace('web/voice-audit.mjs',"'capture_options','session_requested'","'speaker_test_started','speaker_test_finished','speaker_test_confirmed','speaker_test_unheard','speaker_test_failed','readback_failed','capture_options','session_requested'")
replace('web/voice-audit.mjs',"if(REASONS.has(row.reason))out.reason=row.reason;", "if(REASONS.has(row.reason))out.reason=row.reason;\n    if(SPEECH_ERRORS.has(row.code))out.error_code=row.code;\n    for(const k of ['voice_count','english_voice_count'])if(Number.isSafeInteger(row[k])&&row[k]>=0&&row[k]<=10000)out[k]=row[k];\n    if(typeof row.supported==='boolean')out.speech_api_available=row.supported;")
replace('web/voice-audit.mjs',"hasSession(){return this.events.some(e=>e.event==='session_requested');}","hasSession(){return this.events.some(e=>e.event==='session_requested');}\n  hasReport(){return this.hasSession()||this.events.some(e=>e.event==='speaker_test_started');}")
replace('web/voice-audit.mjs',"client_revision:'voice-setup-20260919'", "client_revision:'speaker-preflight-20260919'")
replace('web/voice-audit.mjs',"summary:{sessions_requested:","summary:{speaker_tests:this.events.filter(e=>e.event==='speaker_test_started').length,speaker_tests_confirmed_by_user:this.events.filter(e=>e.event==='speaker_test_confirmed').length,speech_output_errors:this.events.filter(e=>e.event==='speaker_test_failed'||e.event==='readback_failed').length,sessions_requested:")
for fname in ['web/voice-audit.mjs','web/app.mjs']:
 replace(fname,"'audio-worklet.js','streaming-request.mjs'","'audio-worklet.js','streaming-request.mjs','speaker-check.mjs'")
replace('web/app.mjs',"import {ReadbackPlayer} from './readback.mjs';","import {ReadbackPlayer} from './readback.mjs';\nimport {SpeakerCheck} from './speaker-check.mjs';")
replace('web/app.mjs',"function cancelSpeech(){readback.cancel();}","const speaker=new SpeakerCheck(readback,{onChange:()=>render(),onTrace:event=>audit.add(event)});\nfunction cancelSpeech(){readback.cancel();}")
replace('web/app.mjs',"locked=voice.active();","locked=voice.active()||speaker.busy();")
replace('web/app.mjs',"$('voiceReport').disabled=locked||!audit.hasSession();","$('voiceReport').disabled=locked||!audit.hasReport();")
replace('web/app.mjs',"$('listen').disabled=phase==='draining'||(!locked&&(!config?.voice_enabled||!$('consent').checked));","$('listen').disabled=speaker.busy()||phase==='draining'||(!voice.active()&&(!config?.voice_enabled||!$('consent').checked||($('speak').checked&&!speaker.ready())));\n  $('speakerTest').disabled=voice.active()||speaker.busy();\n  $('speakerHeard').hidden=speaker.state!=='awaiting_confirmation';$('speakerUnheard').hidden=speaker.state!=='awaiting_confirmation';\n  $('speakerTestStatus').textContent=speaker.message();")
replace('web/app.mjs',"if(!audit.hasSession())throw Error('Start a voice session first.');","if(!audit.hasReport())throw Error('Run Test speaker or start a voice session first.');")
replace('web/app.mjs',"if(voice.active()){cancelSpeech();return voice.stop();}\n  cancelSpeech();", "if(voice.active()){cancelSpeech();return voice.stop();}\n  if($('speak').checked&&!speaker.ready())throw Error('Tap Test speaker, then confirm you heard it before starting voice mode.');\n  cancelSpeech();")
replace('web/app.mjs',"$('speak').onchange=()=>{cancelSpeech();render();};", "$('speakerTest').onclick=()=>{if(!voice.active())void speaker.test();};\n$('speakerHeard').onclick=()=>speaker.heard();$('speakerUnheard').onclick=()=>speaker.unheard();\n$('speak').onchange=()=>{speaker.reset();render();};")
replace('web/app.mjs',"onState:()=>render(),onError:error,promptReply:","onState:()=>render(),onError:message=>{error(message);},promptReply:")
replace('web/app.mjs',"onTrace:event=>audit.add(event)});\nfunction typed", "onTrace:event=>{audit.add(event);if(event.event==='readback_failed'){speaker.state='failed';speaker.code=event.code;speaker.generation++;}}});\nfunction typed")
replace('web/index.html',"<button id=\"listen\"", "<div class=\"speaker-preflight\"><button id=\"speakerTest\" type=\"button\" class=\"secondary\">Test speaker</button> <button id=\"speakerHeard\" type=\"button\" hidden>I heard it</button> <button id=\"speakerUnheard\" type=\"button\" class=\"secondary\" hidden>No sound</button><p id=\"speakerTestStatus\" role=\"status\" aria-live=\"polite\"></p></div><button id=\"listen\"")
replace('web/index.html',"When finished, stop voice and download the report.","If the speaker test fails, download the voice report without starting the microphone. Otherwise, when finished, stop voice and download the report.")
with (root/'web/style.css').open('a') as f:f.write('\n.speaker-preflight{padding:14px;margin:14px 0;border:1px solid var(--line);border-radius:9px}.speaker-preflight button{margin:3px 0}.speaker-preflight p{font-size:13px;margin-bottom:0}button[hidden]{display:none}\n')
replace('server.py',"'/voice-audit.mjs':('voice-audit.mjs','text/javascript'),", "'/speaker-check.mjs':('speaker-check.mjs','text/javascript'),'/voice-audit.mjs':('voice-audit.mjs','text/javascript'),")
# Existing behavior assertions are unchanged; perform the new UI preflight first.
replace('tests/browser_readback_barrier.py',"page.locator('#speak').check();page.locator('#listen').click();", "page.locator('#speak').check();page.locator('#speakerTest').click();page.evaluate('window.__barrier.utterances.at(-1).onend()');page.locator('#speakerHeard').click();page.evaluate('window.__barrier.utterances=[]');page.locator('#listen').click();")
replace('tests/browser_readback_barrier.py',"len(r['asset_sha256'])==8", "len(r['asset_sha256'])==9")
replace('tests/browser_voice_recovery.py',"if timeout:page.evaluate(\"window.__fixture.speechMode='timeout'\")", "page.locator('#speakerTest').click();page.locator('#speakerHeard').click()\n if timeout:page.evaluate(\"window.__fixture.speechMode='timeout'\")")
