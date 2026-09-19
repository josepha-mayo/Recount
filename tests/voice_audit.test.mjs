import test from 'node:test';
import assert from 'node:assert/strict';
import {VoiceAudit} from '../web/voice-audit.mjs';
import {initial} from '../web/core.mjs';
test('report allowlists trace fields and never echoes credential-bearing URLs',()=>{
 const a=new VoiceAudit({now:()=>100});a.add({event:'provider_begin',token:'PRIVATE',access_code:'SECRET',url:'wss://x?token=PRIVATE',reason:'SECRET'});
 const r=a.snapshot(initial(),{origin:'https://example.test/?secret=PRIVATE',assetHashes:{'app.mjs':'a'.repeat(64),token:'SECRET'}});
 assert.equal(r.site,'https://example.test');assert.equal(r.asset_sha256['app.mjs'],'a'.repeat(64));assert.doesNotMatch(JSON.stringify(r),/PRIVATE|SECRET|wss:/);
});
test('reports are bounded and count truncation instead of growing forever',()=>{
 const a=new VoiceAudit({limit:2});for(let i=0;i<5;i++)a.add({event:'session_requested',epoch:i});assert.equal(a.events.length,2);assert.equal(a.dropped,3);
});
test('exported histories are copies and retain speech versus local action provenance',()=>{
 const a=new VoiceAudit();const s=initial();s.history=[{kind:'turn',source:'assemblyai',text:'rice twelve bags'},{kind:'confirm'}];
 const r=a.snapshot(s);r.ledger.history[0].text='changed';assert.equal(s.history[0].text,'rice twelve bags');assert.equal(r.ledger.history[1].kind,'confirm');
});
test('disabled audio is not counted as a completed spoken read-back',()=>{
 const a=new VoiceAudit();a.add({event:'readback_finished',status:'disabled'});const r=a.snapshot(initial());assert.equal(r.summary.completed_readbacks,0);assert.equal(r.summary.disabled_readbacks,1);
});
test('invalid events and unknown statuses are not trusted',()=>{
 const a=new VoiceAudit();a.add({event:'pass'});a.add({event:'readback_finished',status:'human_test_passed'});assert.equal(a.events.length,1);assert.equal(a.events[0].status,undefined);assert.equal(a.hasSession(),false);
});
test('startup diagnostics preserve safe stage and transport metadata only',()=>{
 const a=new VoiceAudit({now:()=>100});
 a.add({event:'setup_stage',stage:'token_response',httpStatus:403,token:'PRIVATE'});
 a.add({event:'setup_failed',stage:'token_response',errorName:'TypeError',message:'SECRET'});
 a.add({event:'socket_closed',closeCode:1008,wasClean:false,url:'wss://host?token=PRIVATE'});
 const r=a.snapshot(initial());
 assert.equal(r.summary.last_setup_stage,'token_response');assert.equal(r.summary.setup_failures,1);assert.equal(r.summary.socket_closes,1);
 assert.deepEqual(r.events[0],{event:'setup_stage',elapsed_ms:0,setup_stage:'token_response',http_status:403});
 assert.equal(r.events[1].error_name,'TypeError');assert.equal(r.events[2].close_code,1008);assert.equal(r.events[2].was_clean,false);
 assert.doesNotMatch(JSON.stringify(r),/PRIVATE|SECRET|wss:/);
});
