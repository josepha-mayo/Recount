// Mirrors app.mjs clearing the error display in its hold reducer.
import test from 'node:test';
import assert from 'node:assert/strict';
import {VoiceRuntime} from '../web/voice-runtime.mjs';
import {VoiceAudit} from '../web/voice-audit.mjs';
import {initial,reduce} from '../web/core.mjs';
function fixture({httpStatus=200,message,mediaError}={}) {
  let state=initial(),visible='',stops=0,seq=0;
  const timers=new Map(),sockets=[],traces=[];
  class Socket {static OPEN=1;constructor(){this.readyState=1;this.bufferedAmount=0;sockets.push(this);}close(){this.readyState=3;}send(){}async emit(data){await this.onmessage({data:JSON.stringify(data)});}}
  class Context {constructor(){this.sampleRate=16000;this.audioWorklet={addModule:async()=>{}};this.destination={};}createMediaStreamSource(){return {connect(){},disconnect(){}};}resume(){return Promise.resolve();}close(){return Promise.resolve();}}
  class Worklet{constructor(){this.port={postMessage(){}};}connect(){}disconnect(){}}
  const runtime=new VoiceRuntime({getRevision:()=>state.revision,onTurn:a=>{visible='';state=reduce(state,a);},onHold:reason=>{visible='';state=reduce(state,{kind:'hold',reason,revision:state.revision});},onError:m=>{visible=m;},onTrace:e=>traces.push(e),deps:{WebSocket:Socket,AudioContext:Context,AudioWorkletNode:Worklet,mediaDevices:{getUserMedia:async()=>{if(mediaError)throw mediaError;return {getTracks:()=>[{stop(){stops++;}}]};}},fetch:async()=>({ok:httpStatus===200,status:httpStatus,json:async()=>httpStatus===200?{token:'synthetic-only-token',max_session_duration_seconds:90,speech_model:'universal-3-5-pro'}:{error:message}}),setTimeout:(fn,ms)=>{const id=++seq;timers.set(id,{fn,ms});return id;},clearTimeout:id=>timers.delete(id)}});
  return {runtime,sockets,traces,timers,get visible(){return visible;},get state(){return state;},get stops(){return stops;},start:()=>runtime.start({voice_enabled:true,csrf:'synthetic-csrf'},true),fire:ms=>{const t=[...timers.values()].find(x=>x.ms===ms);assert.ok(t);t.fn();}};
}
for(const [status,message] of [[403,'Invalid judge access code.'],[403,'Refresh the page before starting voice mode.'],[403,'Same-origin request required.'],[502,'Provider token service rejected the request.']])test(`startup ${status} remains visible: ${message}`,async()=>{const f=fixture({httpStatus:status,message});await f.start();assert.equal(f.visible,message);assert.equal(f.runtime.active(),false);assert.equal(f.sockets.length,0);assert.ok(f.stops);assert.equal(f.state.hold,'stream_lost');});
test('unknown provider body never reaches display or trace',async()=>{const f=fixture({httpStatus:502,message:'secret-token-example=do-not-include'});await f.start();assert.ok(f.visible);assert.doesNotMatch(f.visible,/secret-token/);assert.doesNotMatch(JSON.stringify(f.traces),/secret-token/);});
test('handshake timeout stays visible after capture is released',async()=>{const f=fixture();await f.start();f.fire(20000);assert.match(f.visible,/timed out/i);assert.ok(f.stops);assert.equal(f.runtime.active(),false);});
test('socket error survives later close and hold',async()=>{const f=fixture();await f.start();f.sockets[0].onerror();f.sockets[0].onclose({code:1006,wasClean:false});assert.match(f.visible,/connection/i);assert.equal(f.runtime.active(),false);});
test('socket error survives timeout without close',async()=>{const f=fixture();await f.start();f.sockets[0].onerror();f.fire(750);assert.match(f.visible,/connection/i);assert.equal(f.runtime.active(),false);});
test('malformed stream error survives hold',async()=>{const f=fixture();await f.start();await f.sockets[0].onmessage({data:'not JSON'});assert.match(f.visible,/streaming data/i);assert.equal(f.runtime.active(),false);});
test('microphone denial stays visible without private device labels',async()=>{const f=fixture({mediaError:Object.assign(Error('private device label'),{name:'NotAllowedError'})});await f.start();assert.ok(f.visible);assert.doesNotMatch(f.visible,/private device label/);assert.equal(f.runtime.active(),false);});
test('report contains safe authorization failure class',async()=>{const f=fixture({httpStatus:403,message:'Invalid judge access code.'});await f.start();const a=new VoiceAudit();for(const e of f.traces)a.add(e);assert.equal(a.snapshot(f.state).events.find(e=>e.event==='setup_failed').failure_code,'invalid_access_code');});
