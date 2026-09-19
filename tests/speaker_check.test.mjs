import test from 'node:test';import assert from 'node:assert/strict';
import {ReadbackPlayer,speechErrorCode,speechErrorMessage} from '../web/readback.mjs';
import {SpeakerCheck} from '../web/speaker-check.mjs';
import {VoiceAudit} from '../web/voice-audit.mjs';
import {VoiceRuntime} from '../web/voice-runtime.mjs';
import {initial} from '../web/core.mjs';
function setup(voices=[]){
 const spoken=[],events=[],timers=new Map();let n=0;
 const synth={paused:false,getVoices:()=>voices,cancel(){events.push('cancel');},speak(u){spoken.push(u);events.push('speak');},resume(){events.push('resume');}};
 class U{constructor(text){this.text=text;}}
 const player=new ReadbackPlayer({synth,Utterance:U,setTimer:fn=>{timers.set(++n,fn);return n;},clearTimer:id=>timers.delete(id)});
 return {spoken,events,timers,player,synth};
}
test('speaker test invokes speech synchronously, before its async promise yields',async()=>{const f=setup(),s=new SpeakerCheck(f.player);const p=s.test();assert.equal(f.spoken.length,1);assert.equal(s.state,'testing');f.spoken[0].onend();await p;assert.equal(s.state,'awaiting_confirmation');});
test('playback completion never automatically asserts the user heard sound',async()=>{const f=setup(),s=new SpeakerCheck(f.player);const p=s.test();f.spoken[0].onend();await p;assert.equal(s.ready(),false);assert.equal(s.heard(),true);assert.equal(s.ready(),true);});
test('I heard it cannot be accepted before test completion',async()=>{const f=setup(),s=new SpeakerCheck(f.player);assert.equal(s.heard(),false);const p=s.test();assert.equal(s.heard(),false);f.spoken[0].onend();await p;s.heard();assert.equal(s.ready(),true);});
test('reported silence after completion keeps voice mode unready',async()=>{const f=setup(),s=new SpeakerCheck(f.player);const p=s.test();f.spoken[0].onend();await p;s.unheard();assert.equal(s.ready(),false);assert.match(s.message(),/no sound/);});
test('actual native synthesis-unavailable is retained, not a generic audio-gap',async()=>{const f=setup(),rows=[],s=new SpeakerCheck(f.player,{onTrace:e=>rows.push(e)});const p=s.test();f.spoken[0].onerror({error:'synthesis-unavailable'});await p;assert.equal(s.state,'failed');assert.equal(s.code,'synthesis-unavailable');assert.equal(rows.at(-1).code,'synthesis-unavailable');assert.equal(s.ready(),false);});
test('blocked playback has its own actionable not-allowed error',async()=>{const f=setup(),p=f.player.speak('Test');f.spoken[0].onerror({error:'not-allowed'});await assert.rejects(p,e=>e.code==='not-allowed'&&e.message.includes('Tap Test speaker'));});
test('unsupported speech API fails preflight without claiming a heard voice',async()=>{const s=new SpeakerCheck(new ReadbackPlayer({synth:null,Utterance:null}));await s.test();assert.equal(s.state,'failed');assert.equal(s.code,'speech-unavailable');});
test('known English voice is selected and utterance is strongly retained',async()=>{const en={lang:'en-GB',localService:true},f=setup([{lang:'fr-FR',default:true},en]),p=f.player.speak('Test');assert.equal(f.spoken[0].voice,en);assert.equal(f.spoken[0].lang,'en-GB');assert.equal(f.player.current.utterance,f.spoken[0]);assert.equal(f.spoken[0].volume,1);f.spoken[0].onend();await p;});
test('empty asynchronously-loaded voice list does not prematurely reject default engine',async()=>{const f=setup(),p=f.player.speak('Test');assert.equal(f.spoken[0].lang,'en-US');f.spoken[0].onend();assert.equal((await p).status,'completed');});
test('paused synthesis is resumed before dispatching speech',async()=>{const f=setup();f.synth.paused=true;const p=f.player.speak('Test');assert.deepEqual(f.events.slice(-2),['resume','speak']);f.spoken[0].onend();await p;});
test('start timeout and mid-speech timeout are distinct',async()=>{for(const started of [false,true]){const f=setup(),p=f.player.speak('Test');if(started)f.spoken[0].onstart();[...f.timers.values()][0]();await assert.rejects(p,e=>e.code===(started?'speech-timeout':'speech-start-timeout'));}});
test('reset invalidates a late speaker-test completion',async()=>{const f=setup(),s=new SpeakerCheck(f.player);const p=s.test();s.reset();f.spoken[0].onend();await p;assert.equal(s.state,'untested');assert.equal(s.ready(),false);});
test('failed speaker attempt can export evidence without any provider session',()=>{const a=new VoiceAudit();a.add({event:'speaker_test_started',supported:true,voice_count:0,english_voice_count:0});a.add({event:'speaker_test_failed',code:'synthesis-unavailable'});assert.equal(a.hasReport(),true);assert.equal(a.hasSession(),false);const r=a.snapshot(initial());assert.equal(r.summary.speaker_tests,1);assert.equal(r.summary.sessions_requested,0);assert.equal(r.summary.speech_output_errors,1);assert.equal(r.events[1].error_code,'synthesis-unavailable');});
test('speaker diagnostics preserve no arbitrary error text, device name or credential fields',()=>{const a=new VoiceAudit();a.add({event:'speaker_test_failed',code:'PRIVATE_SECRET',message:'PRIVATE_SECRET',voiceURI:'SECRET_URL',url:'https://x?token=PRIVATE_SECRET'});assert.doesNotMatch(JSON.stringify(a.snapshot(initial())),/PRIVATE_SECRET|SECRET_URL|https:\/\/x/);assert.equal(speechErrorCode('PRIVATE_SECRET'),'unknown');assert.doesNotMatch(speechErrorMessage('PRIVATE_SECRET'),/PRIVATE_SECRET/);});
test('native read-back error remains visible after the hold action clears previous errors',async()=>{
 let error='old',held=false,stops=0;const rows=[];
 const r=new VoiceRuntime({getRevision:()=>0,onTurn:()=>{},onHold:()=>{},onError:e=>{error=e;},onTrace:e=>rows.push(e),promptReply:async()=>{throw Object.assign(new Error('not for export'),{code:'not-allowed'});}});
 const v={finished:false,prompting:false,promptGeneration:0,input:{disconnect(){},connect(){}},node:{port:{postMessage(){}},disconnect(){}},stream:{getTracks:()=>[{stop(){stops++;}}]},gate:{phase:'listening',fail(){held=true;error='';}},ws:{close(){}}};r.current=v;
 await r.prompt(v);assert.equal(held,true);assert.equal(stops,1);assert.match(error,/not-allowed/);assert.equal(r.current,null);assert.equal(rows.find(x=>x.event==='readback_failed').code,'not-allowed');
});
