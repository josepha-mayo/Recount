/* Bounded half-duplex microphone transport. Final provider turns can trigger a
   local spoken read-back while microphone audio is disconnected from the
   streaming worklet, then listening resumes. Permanent provider keys never
   enter this module. */
import {CaptureGate} from './capture-gate.mjs';
import {streamingURL} from './streaming-request.mjs';
import {normalizeTranscript} from './core.mjs';
export class VoiceRuntime {
  constructor({getRevision,onTurn,onHold,onPartial=()=>{},onState=()=>{},onError=()=>{},promptReply=async()=>{},cancelPrompt=()=>{},onTrace=()=>{},deps={}}){
    Object.assign(this,{getRevision,onTurn,onHold,onPartial,onState,onError,promptReply,cancelPrompt,onTrace});
    this.d={mediaDevices:globalThis.navigator?.mediaDevices,AudioContext:globalThis.AudioContext,
      AudioWorkletNode:globalThis.AudioWorkletNode,WebSocket:globalThis.WebSocket,
      fetch:globalThis.fetch?.bind(globalThis),setTimeout:globalThis.setTimeout.bind(globalThis),clearTimeout:globalThis.clearTimeout.bind(globalThis),...deps};
    this.current=null;this.generation=0;
  }
  trace(event,details={}){try{this.onTrace({event,revision:this.getRevision(),...details});}catch{ /* Diagnostics cannot change the count path. */ }}
  active(){return this.current!==null;}
  phase(){return this.current?.prompting?'prompting':this.current?.gate.phase??'idle';}
  live(v){return this.current===v&&!v.finished;}
  timer(v,name,ms,fn){v[name]=this.d.setTimeout(()=>{if(this.live(v))fn();},ms);}
  clear(v,name){if(v[name]!==undefined)this.d.clearTimeout(v[name]);}
  stopPrompt(v){if(v?.prompting){v.promptGeneration++;v.prompting=false;try{this.cancelPrompt();}catch{}this.trace('readback_cancelled');}}
  finish(v){
    if(v.finished)return;v.finished=true;this.stopPrompt(v);
    for(const name of ['handshake','duration','drain','flush'])this.clear(v,name);
    v.stream?.getTracks().forEach(t=>t.stop());v.input?.disconnect();v.node?.disconnect();
    try{v.ws?.close();}catch{}
    try{Promise.resolve(v.ctx?.close()).catch(()=>{});}catch{}
    if(this.current===v){this.current=null;this.trace('session_closed');this.onState('idle');}
  }
  fail(v,reason){if(!this.live(v))return;this.trace('session_hold',{reason});try{v.gate.fail(reason);}finally{this.finish(v);}}
  async prompt(v){
    if(!this.live(v)||v.gate.phase!=='listening'||!v.input||!v.node||v.prompting)return;
    const generation=++v.promptGeneration;v.prompting=true;
    try{v.input.disconnect();}catch{this.fail(v,'audio_gap');return;}
    // Empty the pre-prompt sub-frame so samples before and after TTS are never
    // fused into one worklet packet. The normal port handler forwards the tail.
    try{v.node.port.postMessage({type:'drain'});}catch{this.fail(v,'audio_gap');return;}
    this.trace('readback_started',{generation});this.onState('prompting');
    let result;
    try{result=await this.promptReply();}catch{if(generation!==v.promptGeneration||!this.live(v))return;this.onError('Read-back failed or timed out. Audio stopped; review the held draft.');this.fail(v,'audio_gap');return;}
    if(generation!==v.promptGeneration||!this.live(v))return;
    if(result?.status==='unavailable'||result?.status==='cancelled'){this.onError('Read-back did not complete. Stop and review the draft.');this.fail(v,'audio_gap');return;}
    if(v.gate.phase!=='listening'){v.prompting=false;return;}
    this.trace('readback_finished',{generation,status:result?.status??'completed'});
    try{v.input.connect(v.node);}catch{this.fail(v,'audio_gap');return;}
    v.prompting=false;this.onState('listening');
  }
  async start(config,consent){
    if(this.active())throw Error('Microphone session already active');
    if(!config?.voice_enabled||consent!==true)throw Error('Configure the provider and explicitly permit audio transfer first.');
    const tokenBody={consent:true};
    if(config.requires_access_code){
      if(typeof config.access_code!=='string'||config.access_code.length<8||config.access_code.length>128)throw Error('A valid judge access code is required.');
      tokenBody.access_code=config.access_code;
    }
    const v={epoch:++this.generation,finished:false,prompting:false,promptGeneration:0};this.current=v;this.trace('session_requested',{epoch:v.epoch});
    v.gate=new CaptureGate({epoch:v.epoch,getRevision:this.getRevision,onTurn:this.onTurn,
      onHold:this.onHold,onPartial:this.onPartial,onPhase:p=>this.onState(p)});
    this.onState('connecting');this.timer(v,'handshake',20000,()=>this.fail(v,'stream_lost'));
    try{
      const stream=await this.d.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true}});
      if(!this.live(v)){stream.getTracks().forEach(t=>t.stop());return false;}v.stream=stream;
      v.ctx=new this.d.AudioContext({sampleRate:16000});await v.ctx.audioWorklet.addModule('/audio-worklet.js');
      if(!this.live(v))return false;
      const res=await this.d.fetch('/api/token',{method:'POST',headers:{'Content-Type':'application/json','X-Recount-Token':config.csrf},body:JSON.stringify(tokenBody)});
      const data=await res.json();
      if(!this.live(v))return false;
      if(!res.ok||typeof data.token!=='string'||!Number.isFinite(data.max_session_duration_seconds))throw Error(data?.error||'Provider token unavailable');
      const url=streamingURL({sampleRate:v.ctx.sampleRate,speechModel:data.speech_model,token:data.token});
      v.ws=new this.d.WebSocket(url);
      v.ws.onmessage=async e=>{
        if(!this.live(v))return;
        try{
          const message=JSON.parse(e.data);
          // A provider can deliver queued final turns while local speech is still
          // playing. That is not permission to confirm an unheard read-back.
          // Exact duplicate finals still go through CaptureGate's idempotency guard.
          if(v.prompting && message.type==='Turn' && message.end_of_turn===true &&
             Number.isSafeInteger(message.turn_order) && message.turn_order>v.gate.lastOrder){
            const text=normalizeTranscript(String(message.transcript??''));
            if(/^(?:confirm|confirmed|save|saved)(?:\s|$)/.test(text)){
              this.trace('premature_confirmation_rejected',{order:message.turn_order});
              this.onError('Confirmation arrived before read-back finished. Nothing new saved; review the draft.');
              this.fail(v,'stale_turn');return;
            }
            // A newer correction must replace the old spoken reply. Invalidating
            // its generation prevents the cancelled promise reopening capture.
            this.stopPrompt(v);this.trace('readback_superseded',{order:message.turn_order});
          }
          const outcome=v.gate.ingest(v.epoch,message);
          if(outcome==='final')this.trace('provider_final',{order:message.turn_order});
          if(outcome==='duplicate_final')this.trace('duplicate_final_ignored',{order:message.turn_order});
          if(outcome==='begin')this.trace('provider_begin');
          if(outcome==='terminated')this.trace('provider_terminated');
          if(v.gate.phase==='faulted'){this.finish(v);return;}
          if(outcome==='terminated'){this.finish(v);return;}
          if(outcome==='begin'){
            this.clear(v,'handshake');v.input=v.ctx.createMediaStreamSource(v.stream);
            v.node=new this.d.AudioWorkletNode(v.ctx,'recount-pcm16');
            v.node.port.onmessage=event=>{
              if(!this.live(v))return;
              if(event.data?.type==='drained')return;
              if(event.data?.type==='flushed'){
                if(v.gate.phase==='draining'){
                  this.clear(v,'flush');
                  if(v.ws.readyState!==this.d.WebSocket.OPEN){this.fail(v,'stream_lost');return;}
                  try{v.ws.send(JSON.stringify({type:'Terminate'}));}catch{this.fail(v,'stream_lost');}
                }return;
              }
              if(!(event.data instanceof ArrayBuffer)){this.fail(v,'invalid_event');return;}
              if(v.ws.readyState!==this.d.WebSocket.OPEN){this.fail(v,'stream_lost');return;}
              if(v.ws.bufferedAmount>256000){this.fail(v,'audio_gap');return;}
              try{v.ws.send(event.data);}catch{this.fail(v,'stream_lost');}
            };
            v.input.connect(v.node);v.node.connect(v.ctx.destination);await v.ctx.resume();
            if(this.live(v))this.timer(v,'duration',Math.min(data.max_session_duration_seconds,120)*1000,()=>this.stop());
          } else if(outcome==='final' && this.live(v) && v.gate.phase==='listening') {
            await this.prompt(v);
          }
        }catch{this.onError('Streaming data could not be verified. Review the held count.');this.fail(v,'invalid_event');}
      };
      v.ws.onerror=()=>{if(this.live(v)){this.onError('Connection failed. The count remains unconfirmed.');this.fail(v,'stream_lost');}};
      v.ws.onclose=()=>{if(this.live(v)){v.gate.transportClosed();this.finish(v);}};
      return true;
    }catch(e){
      if(this.live(v)){this.onError(e?.message==='Invalid judge access code.'?e.message:'Microphone or provider setup failed. No successful transcription is claimed.');this.fail(v,'stream_lost');}
      return false;
    }
  }
  stop(){
    const v=this.current;if(!v)return;this.trace('stop_requested');
    if(v.gate.phase==='draining')return;
    if(v.gate.phase!=='listening'||!v.node){this.fail(v,'stream_lost');return;}
    this.stopPrompt(v);v.gate.requestStop();this.clear(v,'duration');
    v.stream?.getTracks().forEach(t=>t.stop());v.input?.disconnect();
    this.timer(v,'drain',3500,()=>{v.gate.timeout();this.finish(v);});
    this.timer(v,'flush',500,()=>this.fail(v,'audio_gap'));
    v.node.port.postMessage({type:'flush'});
  }
  revoke(){const v=this.current;if(v){this.trace('consent_revoked');this.stopPrompt(v);try{v.gate.revokeConsent();}finally{this.finish(v);}}}
}
