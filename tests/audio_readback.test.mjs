import test from 'node:test';
import assert from 'node:assert/strict';
import {numberPlan,planSpeech,AudioReadbackPlayer} from '../web/audio-readback.mjs';
import {SpeakerCheck} from '../web/speaker-check.mjs';
import {initial,reduce} from '../web/core.mjs';
import {VoiceAudit} from '../web/voice-audit.mjs';
const TEXT='This is Recount. If you can hear this voice, tap I heard it.';
const tick=()=>new Promise(r=>setImmediate(r));
function harness({loading=false,missing=false,badHash=false,decodeFails=false,blocked=false}={}){
 let release;const barrier=new Promise(r=>release=r);const sources=[],requests=[],timers=[];let resumed=false;
 class Buffer{constructor(length=10,sr=100){this.numberOfChannels=1;this.length=length;this.duration=length/sr;this.data=new Float32Array(length).fill(.1);}getChannelData(){return this.data;}}
 class Context{constructor(){this.state='suspended';this.sampleRate=100;this.destination={};}resume(){resumed=true;this.state=blocked?'suspended':'running';return Promise.resolve();}decodeAudioData(){if(decodeFails)return Promise.reject(Error());return Promise.resolve(new Buffer());}createBuffer(ch,n,sr){return new Buffer(n,sr);}createAnalyser(){return {connect(){},disconnect(){}};}createBufferSource(){const s={starts:0,stops:0,connect(){},disconnect(){},start(){this.starts++;},stop(){this.stops++;}};sources.push(s);return s;}}
 const fetcher=async url=>{requests.push(url);if(loading)await barrier;
  if(url.endsWith('manifest.json'))return {ok:true,json:async()=>({schema:'recount-bundled-voice-1',clips:{'speaker-test':{path:'/voice/v1/speaker-test.mp3',bytes:100,sha256:'01'.repeat(32)}}})};
  return {ok:!missing,arrayBuffer:async()=>new ArrayBuffer(100)};
 };
 const player=new AudioReadbackPlayer({Context,fetcher,crypto:{subtle:{digest:async()=>new Uint8Array(32).fill(badHash?0:1)}},setTimer:fn=>{timers.push(fn);return timers.length;},clearTimer:()=>{}});
 return {player,sources,requests,timers,release,get resumed(){return resumed;}};
}
test('all 10,000 supported whole numbers map to exactly their quantity',()=>{for(let n=0;n<=9999;n++)assert.equal(numberPlan(n).filter(s=>s!=='and').reduce((a,s)=>a+Number(s.slice(7)),0),n);});
test('invalid numbers cannot produce spoken count clips',()=>{for(const n of [-1,10000,.5,NaN,'13'])assert.throws(()=>numberPlan(n));});
test('real ledger readback repeats corrected quantity and unit, never the old value',()=>{let s=initial();for(const [i,text]of ['rice twelve bags','no','thirteen bags'].entries())s=reduce(s,{kind:'turn',id:'a'+i,text,source:'typed',confidence:1,final:true,revision:s.revision});const p=planSpeech(s.reply);assert.equal(p.filter(x=>x==='number-13').length,2);assert.ok(p.includes('bags'));assert.ok(!p.includes('number-12'));});
test('saved and unconfirmed count messages remain distinct',()=>{assert.equal(planSpeech('Saved Rice: 13 bags. What is the next item?')[0],'saved');assert.ok(!planSpeech('Rice: 13 bags. Say confirm 13, or correct the count.').includes('saved'));});
test('mismatch reads both numbers without pretending to save',()=>{const p=planSpeech('The confirmation said 12, but the read-back is 13. Nothing was saved. Say “confirm 13” or correct the count.');assert.ok(p.includes('number-12')&&p.includes('number-13')&&p.includes('nothing-saved'));assert.ok(!p.includes('saved'));});
test('unknown reply explicitly asks for screen review, without inventing content',()=>assert.deepEqual(planSpeech('unknown state'),['screen-review']));
test('unit and identity inconsistency cannot create false spoken summary',()=>assert.throws(()=>planSpeech('Rice: 13 bottles. Say confirm 13, or correct the count.')));
test('resume is invoked synchronously before network work',async()=>{const h=harness({loading:true});const p=h.player.speak(TEXT);assert.equal(h.resumed,true);h.player.cancel();assert.equal((await p).status,'cancelled');h.release();await tick();assert.equal(h.sources.length,0);});
test('playback completion waits for output end rather than successful download',async()=>{const h=harness();let settled=false;const p=h.player.speak(TEXT).then(r=>{settled=true;return r;});await tick();assert.equal(h.sources[0].starts,1);assert.equal(settled,false);h.sources[0].onended();assert.equal((await p).status,'completed');});
test('cancelled clip and stale end event cannot complete the newer reply',async()=>{const h=harness();const first=h.player.speak(TEXT);await tick();const old=h.sources[0];const next=h.player.speak(TEXT);assert.equal((await first).status,'cancelled');await tick();old.onended();assert.ok(h.player.current);h.sources[1].onended();assert.equal((await next).status,'completed');});
test('missing asset is an observable failure not a silent success',async()=>{await assert.rejects(harness({missing:true}).player.speak(TEXT),{code:'audio-load-failed'});});
test('wrong asset digest fails before playback',async()=>{const h=harness({badHash:true});await assert.rejects(h.player.speak(TEXT),{code:'audio-integrity'});assert.equal(h.sources.length,0);});
test('decode failure stays distinct from native speech failure',async()=>{await assert.rejects(harness({decodeFails:true}).player.speak(TEXT),{code:'audio-decode-failed'});});
test('blocked context never claims sound completion',async()=>{await assert.rejects(harness({blocked:true}).player.speak(TEXT),{code:'audio-blocked'});});
test('watchdog stops output and rejects rather than restarting capture',async()=>{const h=harness();const p=h.player.speak(TEXT);await tick();h.timers[0]();await assert.rejects(p,{code:'audio-timeout'});assert.ok(h.sources[0].stops>0);});
test('the same decoded clip is cached without another network fetch',async()=>{const h=harness();let p=h.player.speak(TEXT);await tick();h.sources[0].onended();await p;const n=h.requests.length;p=h.player.speak(TEXT);await tick();h.sources[1].onended();await p;assert.equal(h.requests.length,n);});
test('speaker still needs explicit human acknowledgement after audio end',async()=>{const h=harness(),s=new SpeakerCheck(h.player);const p=s.test();await tick();h.sources[0].onended();await p;assert.equal(s.ready(),false);assert.equal(s.state,'awaiting_confirmation');s.heard();assert.equal(s.ready(),true);});
test('audio engine label and error survive the local report allowlist',()=>{const a=new VoiceAudit();a.add({event:'speaker_test_started',backend:'bundled-neural-audio'});a.add({event:'speaker_test_failed',code:'audio-decode-failed'});assert.equal(a.events[0].playback_backend,'bundled-neural-audio');assert.equal(a.events[1].error_code,'audio-decode-failed');});
