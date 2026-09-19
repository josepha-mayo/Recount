import test from 'node:test';
import assert from 'node:assert/strict';
import {VoiceRuntime} from '../web/voice-runtime.mjs';
import {initial,reduce} from '../web/core.mjs';
function fixture(){
  let state=initial();const prompts=[],traces=[],sockets=[],sources=[],nodes=[];
  class Socket{static OPEN=1;constructor(){this.readyState=1;this.bufferedAmount=0;sockets.push(this);}send(){}close(){this.readyState=3;}emit(m){return this.onmessage({data:JSON.stringify(m)});}}
  class Source{constructor(){this.connects=0;sources.push(this);}connect(){this.connects++;}disconnect(){}}
  class Context{constructor(){this.sampleRate=16000;this.audioWorklet={addModule:async()=>{}};}createMediaStreamSource(){return new Source();}resume(){return Promise.resolve();}close(){return Promise.resolve();}}
  class Worklet{constructor(){this.port={postMessage(){}};nodes.push(this);}connect(){}disconnect(){}}
  const runtime=new VoiceRuntime({getRevision:()=>state.revision,onTurn:a=>{state=reduce(state,a);},
    onHold:reason=>{state=reduce(state,{kind:'hold',reason,revision:state.revision});},
    onTrace:e=>traces.push(e),promptReply:()=>new Promise((resolve,reject)=>prompts.push({resolve,reject,revision:state.revision})),
    cancelPrompt:()=>{},deps:{mediaDevices:{getUserMedia:async()=>({getTracks:()=>[{stop(){}}]})},AudioContext:Context,AudioWorkletNode:Worklet,WebSocket:Socket,
    fetch:async()=>({ok:true,json:async()=>({token:'fixture-temporary',max_session_duration_seconds:90,speech_model:'universal-3-5-pro'})}),setTimeout:()=>1,clearTimeout:()=>{}}});
  const message=(text,order)=>({type:'Turn',turn_order:order,end_of_turn:true,transcript:text,words:text.split(' ').map(text=>({text,confidence:.99,start:0,end:30}))});
  return {runtime,prompts,traces,sources,get state(){return state;},async begin(){await runtime.start({voice_enabled:true,csrf:'fixture'},true);await sockets[0].emit({type:'Begin',id:'session'});},emit:(text,order)=>sockets[0].emit(message(text,order))};
}
test('a new confirmation cannot commit while its read-back is still playing',async()=>{
  const f=fixture();await f.begin();const first=f.emit('Rice 12 bags.',0);
  assert.equal(f.runtime.phase(),'prompting');await f.emit('Confirm 12.',1);
  assert.deepEqual(f.state.counts,{});assert.equal(f.state.hold,'stale_turn');
  f.prompts[0].resolve({status:'completed'});await first;assert.equal(f.runtime.active(),false);
});
test('a correction during read-back starts a new reply and old completion cannot reopen capture',async()=>{
  const f=fixture();await f.begin();const first=f.emit('Rice 12 bags.',0),second=f.emit('No 13 bags.',1);
  assert.equal(f.prompts.length,2);assert.equal(f.state.pending.quantity,13);
  f.prompts[0].resolve({status:'completed'});await first;
  assert.equal(f.runtime.phase(),'prompting');assert.equal(f.sources[0].connects,1);
  f.prompts[1].resolve({status:'completed'});await second;
  assert.equal(f.runtime.phase(),'listening');assert.equal(f.sources[0].connects,2);f.runtime.revoke();
});
test('late rejection of cancelled reply cannot stop the newer reply',async()=>{
  const f=fixture();await f.begin();const first=f.emit('Rice 12 bags.',0),second=f.emit('No 13 bags.',1);
  f.prompts[0].reject(Error('cancelled old speech'));await first;
  assert.equal(f.runtime.phase(),'prompting');assert.equal(f.state.hold,null);
  f.prompts[1].resolve({status:'completed'});await second;assert.equal(f.runtime.phase(),'listening');f.runtime.revoke();
});
test('an exact duplicate final during read-back does not restart it or create a hold',async()=>{
  const f=fixture();await f.begin();const first=f.emit('Rice 12 bags.',0);await f.emit('Rice 12 bags.',0);
  assert.equal(f.prompts.length,1);assert.equal(f.state.hold,null);
  f.prompts[0].resolve({status:'completed'});await first;f.runtime.revoke();
});
test('unavailable read-back is not reported as completed speech',async()=>{
  const f=fixture();await f.begin();const first=f.emit('Rice 12 bags.',0);f.prompts[0].resolve({status:'unavailable'});await first;
  assert.equal(f.runtime.active(),false);assert.equal(f.state.hold,'audio_gap');assert.deepEqual(f.state.counts,{});
});
test('deliberately disabled audio still permits the existing visual workflow',async()=>{
  const f=fixture();await f.begin();const first=f.emit('Rice 12 bags.',0);f.prompts[0].resolve({status:'disabled'});await first;
  assert.equal(f.runtime.phase(),'listening');assert.equal(f.state.hold,null);f.runtime.revoke();
});
test('a confirmation after completed read-back retains exact-quantity rules',async()=>{
  const f=fixture();await f.begin();const first=f.emit('Rice 12 bags.',0);f.prompts[0].resolve({status:'completed'});await first;
  const second=f.emit('Confirm 12.',1);assert.equal(f.state.counts.rice.quantity,12);
  f.prompts[1].resolve({status:'completed'});await second;f.runtime.revoke();
});
test('trace callback failures cannot alter count state transitions',async()=>{
  const f=fixture();f.runtime.onTrace=()=>{throw Error('observer failed');};await f.begin();const first=f.emit('Rice 12 bags.',0);
  f.prompts[0].resolve({status:'completed'});await first;assert.equal(f.state.pending.quantity,12);assert.equal(f.runtime.phase(),'listening');f.runtime.revoke();
});
