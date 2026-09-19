/* One bounded local utterance. Failed read-backs reject before capture resumes. */
export function conciseReadback(text){
  const s=String(text);
  const m=s.match(/^(Rice|Beans|Cooking oil|Soap): (\d+) (bags|bottles|bars)\. To save hands-free, say “confirm (\d+)”/);
  if(m && m[2]===m[4])return `${m[1]}: ${m[2]} ${m[3]}. Say confirm ${m[2]}, or correct the count.`+(s.includes('low-confidence')?' Check the item and unit carefully.':'');
  if(s.startsWith('The confirmation number or command was not clear enough'))return 'Confirmation unclear. Nothing saved. Repeat the confirmation number, or review it on screen.';
  if(s.startsWith('Audio or transcript integrity needs review.'))return 'Audio needs review. Restate the full item, number and unit, or discard the uncertain draft.';
  if(s.startsWith('The task-critical part of that transcript is uncertain.'))return 'That count was unclear. Please repeat the full item, number and unit.';
  return s;
}
export const SPEECH_ERRORS = new Set(['canceled','interrupted','audio-busy','audio-hardware','network',
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
