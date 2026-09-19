/* Generated neural clips played by Web Audio. No speechSynthesis or inference API. */
import {conciseReadback} from './readback.mjs';
const ITEMS={Rice:'rice',Beans:'beans','Cooking oil':'oil',Soap:'soap'};
const UNITS={rice:'bags',beans:'bags',oil:'bottles',soap:'bars'};
export function numberPlan(n){
  if(!Number.isSafeInteger(n)||n<0||n>9999)throw Error('Unsupported quantity');
  if(n<100)return ['number-'+n];
  const scale=n>=1000?1000:100,head=Math.floor(n/scale)*scale,rest=n%scale;
  return ['number-'+head,...(rest?(rest<100?['and']:[]).concat(numberPlan(rest)):[])];
}
function countParts(item,n,unit){
  const id=ITEMS[item];if(!id||UNITS[id]!==unit)throw Error('Invalid count identity');
  return [id,...numberPlan(Number(n)),unit];
}
export function planSpeech(input){
  const text=conciseReadback(input);let m;
  if(text==='This is Recount. If you can hear this voice, tap I heard it.')return ['speaker-test'];
  if(text.startsWith('Review restored. '))return ['review-restored',...planSpeech(text.slice(17))];
  if((m=text.match(/^(Rice|Beans|Cooking oil|Soap): (\d+) (bags|bottles|bars)\. Say confirm (\d+), or correct the count\./))){
    if(m[2]!==m[4])throw Error('Mismatched speech quantity');
    return [...countParts(m[1],m[2],m[3]),'say-confirm',...numberPlan(+m[2]),'or-correct',...(text.includes('carefully')?['check-item-unit']:[])];
  }
  if((m=text.match(/^Saved (Rice|Beans|Cooking oil|Soap): (\d+) (bags|bottles|bars)\. What is the next item\?/)))return ['saved',...countParts(m[1],m[2],m[3]),'next-item'];
  if((m=text.match(/^How many (bags|bottles|bars) of (Rice|Beans|Cooking oil|Soap)\?/))){
    if(UNITS[ITEMS[m[2]]]!==m[1])throw Error('Invalid unit question');
    return ['how-many-'+m[1],ITEMS[m[2]],...(text.includes('Earlier drafts')?['reviews-parked']:[])];
  }
  if((m=text.match(/^(\d+) (Rice|Beans|Cooking oil|Soap): which unit\? Say (bags|bottles|bars)\./)))return [...numberPlan(+m[1]),ITEMS[m[2]],'which-unit','say-'+m[3]];
  if((m=text.match(/^Correcting (Rice|Beans|Cooking oil|Soap)\. Say the new number and unit/)))return ['correcting',ITEMS[m[1]],'new-number-unit'];
  if((m=text.match(/^The confirmation said (\d+), but the read-back is (\d+)\. Nothing was saved\./)))return ['confirmation-said',...numberPlan(+m[1]),'readback-is',...numberPlan(+m[2]),'nothing-saved','say-confirm',...numberPlan(+m[2]),'or-correct'];
  const starts=[
    ['Confirmation unclear.','confirm-unclear'],['The confirmation number or command was not clear enough','confirm-unclear'],
    ['Nothing complete is ready to save','no-complete-count'],['Nothing complete to save yet','no-complete-count'],
    ['That count was unclear.','count-unclear'],['The task-critical part','count-unclear'],
    ['Audio needs review.','audio-hold'],['Audio or transcript integrity','audio-hold'],
    ['Draft discarded.','discarded'],['Cancellation was unclear.','discard-unclear'],
    ['Count one catalogue item','one-item'],['The earlier count is uncertain','uncertain-full-count'],
    ['The latest instruction needs clarification','uncertain-full-count'],['Repeat the entire uncertain count','uncertain-full-count'],
    ['Which item?','which-item'],['Name one item','start-count'],['No count is waiting','start-count'],
    ['A newer count was confirmed','newer-count'],['Confirm by repeating only the number','confirm-number-only'],
    ['The correction was unfinished','incomplete-correction'],['I need one unambiguous','unambiguous-number'],
    ['Confirm or discard the current item','different-item'],['The unit changed','unit-changed'],
    ['The item name was uncertain','item-unclear'],['The correction marker was uncertain','correction-unclear'],
  ];
  for(const [prefix,key] of starts)if(text.startsWith(prefix))return [key];
  if(text.includes('not guess pack conversions'))return ['wrong-unit'];
  // Never invent or approximate an unrecognized reply. The screen remains authoritative.
  return ['screen-review'];
}
function failure(code){return Object.assign(Error({
  'audio-unavailable':'Audio playback is unavailable in this browser.',
  'audio-load-failed':'The bundled voice could not load. Check the connection and tap Test speaker again.',
  'audio-integrity':'The downloaded voice file failed its integrity check.',
  'audio-decode-failed':'This browser could not decode the bundled audio.',
  'audio-blocked':'Audio playback is paused or blocked. Tap Test speaker directly.',
  'audio-timeout':'Audio did not complete in time. The microphone remains held.',
  'audio-plan-failed':'The reply could not be represented safely as audio. Review the screen.',
  'audio-playback-failed':'Audio playback failed. The microphone remains held.'
}[code]||'Audio playback failed.'),{code});}
export class AudioReadbackPlayer{
  constructor({Context=globalThis.AudioContext||globalThis.webkitAudioContext,fetcher=globalThis.fetch?.bind(globalThis),
    crypto=globalThis.crypto,setTimer=globalThis.setTimeout.bind(globalThis),clearTimer=globalThis.clearTimeout.bind(globalThis),timeoutMs=30000}={}){
    Object.assign(this,{Context,fetcher,crypto,setTimer,clearTimer,timeoutMs});
    this.ctx=null;this.current=null;this.manifest=null;this.cache=new Map();this.lastOutput=null;
  }
  capabilities(){return {supported:Boolean(this.Context),voice_count:1,english_voice_count:1,backend:'bundled-neural-audio'};}
  cancel(){const v=this.current;if(!v||v.done)return;v.done=true;this.current=null;this.clearTimer(v.timer);
    try{v.source?.stop();}catch{}try{v.source?.disconnect();}catch{}v.resolve({status:'cancelled',backend:'bundled-neural-audio'});}
  async jsonManifest(){
    if(this.manifest)return this.manifest;
    const r=await this.fetcher('/voice/v1/manifest.json',{credentials:'omit',signal:AbortSignal.timeout(10000)});
    if(!r.ok)throw failure('audio-load-failed');const m=await r.json();
    if(m.schema!=='recount-bundled-voice-1'||!m.clips||Object.keys(m.clips).length>300)throw failure('audio-integrity');
    this.manifest=m;return m;
  }
  async load(id){
    if(!/^[a-z0-9-]+$/.test(id))throw failure('audio-plan-failed');
    if(this.cache.has(id))return this.cache.get(id);
    const p=(async()=>{
      const m=await this.jsonManifest(),clip=m.clips[id];
      if(!clip||clip.path!='/voice/v1/'+id+'.mp3'||!Number.isInteger(clip.bytes)||clip.bytes<100||clip.bytes>300000||!/^[a-f0-9]{64}$/.test(clip.sha256))throw failure('audio-integrity');
      const r=await this.fetcher(clip.path,{credentials:'omit',signal:AbortSignal.timeout(10000)});
      if(!r.ok)throw failure('audio-load-failed');const data=await r.arrayBuffer();
      if(data.byteLength!==clip.bytes)throw failure('audio-integrity');
      const hash=Array.from(new Uint8Array(await this.crypto.subtle.digest('SHA-256',data)),b=>b.toString(16).padStart(2,'0')).join('');
      if(hash!==clip.sha256)throw failure('audio-integrity');
      let audio;try{audio=await this.ctx.decodeAudioData(data);}catch{throw failure('audio-decode-failed');}
      if(audio.numberOfChannels!==1||audio.duration<=.05||audio.duration>25)throw failure('audio-integrity');
      return audio;
    })();
    this.cache.set(id,p);try{return await p;}catch(e){this.cache.delete(id);throw e;}
  }
  speak(text){
    this.cancel();
    if(!this.Context)return Promise.resolve({status:'unavailable',code:'audio-unavailable'});
    let ids,resume;
    try{
      ids=planSpeech(text);if(ids.length>24)throw failure('audio-plan-failed');
      if(!this.ctx||this.ctx.state==='closed')this.ctx=new this.Context({latencyHint:'interactive'});
      // Resume is invoked synchronously in the speaker-test click, before any fetch/await.
      resume=this.ctx.resume();
    }catch(e){return Promise.reject(e.code?e:failure('audio-playback-failed'));}
    return new Promise((resolve,reject)=>{
      const v={done:false,resolve,reject,source:null,timer:null};this.current=v;
      const finish=(ok,code)=>{
        if(v.done)return;v.done=true;this.clearTimer(v.timer);if(this.current===v)this.current=null;
        try{v.source?.disconnect();}catch{}
        if(ok)resolve({status:'completed',backend:'bundled-neural-audio',start_event_observed:true,clips:ids.length});
        else{try{v.source?.stop();}catch{}reject(failure(code));}
      };
      v.timer=this.setTimer(()=>finish(false,'audio-timeout'),this.timeoutMs);
      (async()=>{
        try{
          await resume;if(v.done)return;if(this.ctx.state!=='running')throw failure('audio-blocked');
          const clips=await Promise.all(ids.map(id=>this.load(id)));if(v.done)return;
          const sr=this.ctx.sampleRate,gap=Math.round(.045*sr);
          const length=clips.reduce((n,b)=>n+b.length,0)+gap*(clips.length-1);
          if(length/sr>28)throw failure('audio-plan-failed');
          const combined=this.ctx.createBuffer(1,length,sr),out=combined.getChannelData(0);let offset=0;
          for(const b of clips){out.set(b.getChannelData(0),offset);offset+=b.length+gap;}
          const source=this.ctx.createBufferSource();v.source=source;source.buffer=combined;
          const analyser=this.ctx.createAnalyser();analyser.fftSize=2048;
          source.connect(analyser);analyser.connect(this.ctx.destination);
          this.lastOutput={analyser,seconds:combined.duration,backend:'bundled-neural-audio'};
          source.onended=()=>{try{analyser.disconnect();}catch{}finish(true);};
          if(this.ctx.state!=='running')throw failure('audio-blocked');source.start();
        }catch(e){finish(false,e.code||'audio-load-failed');}
      })();
    });
  }
}
