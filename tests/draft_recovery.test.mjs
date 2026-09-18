import test from 'node:test';
import assert from 'node:assert/strict';
import {initial,reduce,fromAssembly,ready,replay,exportCSV} from '../web/core.mjs';
let serial=0;
const typed=(s,text,extra={})=>reduce(s,{kind:'turn',id:`fixture:${serial++}`,source:'fixture',text,confidence:1,final:true,revision:s.revision,...extra});
const control=(s,kind,extra={})=>reduce(s,{kind,revision:s.revision,...extra});
function heard(s,text,scores={},id=null){
  const words=text.split(' ').map(w=>({text:w,confidence:scores[w]??.99,start:0,end:1}));
  const m={type:'Turn',turn_order:id??serial++,end_of_turn:true,transcript:text,words};
  return reduce(s,fromAssembly(m,'authored-fixture',s.revision));
}

test('standalone correction invalidates quantity and then accepts a quantity/unit fragment',()=>{
  let s=typed(initial(),'rice 42 bags');s=typed(s,'actually');
  assert.equal(s.pending.quantity,null);assert.equal(s.pending.unit,null);assert.ok(!ready(s.pending));
  assert.throws(()=>control(s,'confirm'));s=typed(s,'43 bags');assert.ok(ready(s.pending));
  s=typed(s,'confirm 43');assert.equal(s.counts.rice.quantity,43);
});
test('units alone after a correction cannot revive the earlier quantity',()=>{
  let s=typed(initial(),'soap 17 bars');s=typed(s,'no');s=typed(s,'bars');
  assert.equal(s.pending.quantity,null);assert.ok(!ready(s.pending));s=typed(s,'confirm 17');assert.deepEqual(s.counts,{});
});
test('uncertain fragment plus explicit correction keeps item identity without guessing missing quantity',()=>{
  let s=typed(initial(),'oil');s=typed(s,'unclear bottles');assert.ok(s.pending.blocked);
  s=typed(s,'sorry');s=typed(s,'12 bottles');assert.ok(ready(s.pending));assert.equal(s.pending.sku,'oil');
});
test('low-confidence correction keyword cannot clear a blocked draft',()=>{
  let s=typed(initial(),'soap 17 bars');s=typed(s,'unclear');s=heard(s,'No',{'No':.2});
  assert.ok(s.pending.blocked);assert.equal(s.pending.quantity,17);assert.throws(()=>control(s,'confirm'));
});
test('transport hold cannot be cleared by fragment correction or item focus',()=>{
  let s=control(typed(initial(),'beans 42 bags'),'hold',{reason:'stream_lost'});
  for(const text of ['no','43 bags','rice']){s=typed(s,text);assert.equal(s.hold,'stream_lost');assert.throws(()=>control(s,'confirm'));}
});
test('ambiguous change of identity still needs full restatement rather than number-only recovery',()=>{
  let s=typed(initial(),'rice 42 bags');s=typed(s,'beans 17 bags');assert.ok(s.pending.identityUncertain);
  s=typed(s,'no');s=typed(s,'18 bags');assert.ok(s.pending.blocked);assert.throws(()=>control(s,'confirm'));
});
test('standalone item focus parks a draft rather than dropping or confirming it',()=>{
  let s=typed(initial(),'rice 42 bags');s=typed(s,'soap');
  assert.equal(s.pending.sku,'soap');assert.equal(s.review.length,1);assert.equal(s.review[0].draft.quantity,42);
  assert.equal(s.review[0].draft.sku,'rice');assert.deepEqual(s.counts,{});
});
test('same-item focus does not clear a blocked draft or create duplicate reviews',()=>{
  let s=typed(initial(),'beans 11 bags');s=typed(s,'unclear');s=typed(s,'beans');assert.ok(s.pending.blocked);assert.equal(s.review.length,0);
});
test('uncertain item focus does not switch or archive the active count',()=>{
  let s=typed(initial(),'beans 11 bags');s=heard(s,'Rice',{'Rice':.3});assert.equal(s.pending.sku,'beans');assert.equal(s.review.length,0);
});
test('merged count and confirm is not split into hidden actions or auto-saved',()=>{
  let s=typed(initial(),'rice');s=typed(s,'42 bags confirm 42');assert.deepEqual(s.counts,{});assert.ok(!ready(s.pending));
});
test('compound different-item instruction remains rejected, unlike documented item-name focus',()=>{
  let s=typed(initial(),'rice 42 bags');s=typed(s,'soap 4 bars');assert.equal(s.pending.sku,'rice');assert.ok(s.pending.blocked);assert.equal(s.review.length,0);
});
test('unclear echoed confirmation preserves an otherwise trusted draft for review',()=>{
  let s=typed(initial(),'beans 42 bags');s=heard(s,'Confirm 42',{'42':.61});
  assert.ok(ready(s.pending));assert.equal(s.pending.quantity,42);assert.deepEqual(s.counts,{});assert.match(s.reply,/draft is preserved/i);
});
test('voice confirmation floor stays at 0.90, even for a matching quantity',()=>{
  let s=typed(initial(),'beans 42 bags');s=heard(s,'Confirm 42',{'42':.8999});assert.deepEqual(s.counts,{});
  s=heard(s,'Confirm 42',{'42':.90});assert.equal(s.counts.beans.quantity,42);
});
test('high-confidence number cannot rescue a low-confidence confirmation action word',()=>{
  let s=typed(initial(),'beans 42 bags');s=heard(s,'Confirm 42',{'Confirm':.2,'42':.99});assert.deepEqual(s.counts,{});assert.ok(ready(s.pending));
});
test('number staging floor remains 0.75 and zero is not invented from its confirmation',()=>{
  let s=heard(typed(initial(),'soap'),'0 bars',{'0':.5});s=heard(s,'Confirm zero');
  assert.deepEqual(s.counts,{});assert.ok(!ready(s.pending));
});
test('strong discard action ignores a weak filler noun, clearing only the active draft',()=>{
  let s=control(typed(initial(),'rice 42 bags'),'confirm');s=typed(s,'soap 12 bars');s=typed(s,'oil');
  s=heard(s,'Discard count',{'Discard':.98,'count':.1});assert.equal(s.pending,null);
  assert.equal(s.review.length,1);assert.equal(s.counts.rice.quantity,42);
});
test('a low-confidence discard action still does not discard',()=>{
  let s=typed(initial(),'soap 12 bars');s=heard(s,'Discard count',{'Discard':.2,'count':.99});assert.equal(s.pending.quantity,12);
});
test('discard action can release transport hold without changing any confirmed row',()=>{
  let s=control(typed(initial(),'rice 42 bags'),'confirm');s=control(s,'hold',{reason:'audio_gap'});
  s=heard(s,'Discard count',{'Discard':.98,'count':.1});assert.equal(s.hold,null);assert.equal(s.counts.rice.quantity,42);
});
test('review resume swaps drafts, retains their status, and never writes a count',()=>{
  let s=typed(initial(),'rice 42 bags');s=typed(s,'soap');s=typed(s,'17 bars');const id=s.review[0].id;
  s=control(s,'resume',{reviewId:id});assert.equal(s.pending.sku,'rice');assert.equal(s.review[0].draft.sku,'soap');assert.deepEqual(s.counts,{});
});
test('stale or absent review IDs cannot resume arbitrary data',()=>{
  let s=typed(typed(initial(),'rice 42 bags'),'soap');
  assert.throws(()=>control(s,'resume',{reviewId:'missing'}));
  assert.throws(()=>reduce(s,{kind:'resume',reviewId:s.review[0].id,revision:s.revision-1}));
});
test('review resume cannot escape an audio hold',()=>{
  let s=typed(typed(initial(),'rice 42 bags'),'soap');s=control(s,'hold',{reason:'stream_lost'});
  assert.throws(()=>control(s,'resume',{reviewId:s.review[0].id}));
});
test('older queued count cannot silently overwrite a newer confirmed value',()=>{
  let s=typed(typed(initial(),'rice 42 bags'),'soap');const id=s.review[0].id;
  s=control(s,'discard');s=control(typed(s,'rice 51 bags'),'confirm');s=control(s,'resume',{reviewId:id});
  assert.ok(s.pending.blocked);assert.throws(()=>control(s,'confirm'));assert.equal(s.counts.rice.quantity,51);
  s=typed(s,'no');s=typed(s,'42 bags');assert.throws(()=>control(s,'confirm'));
});
test('full explicit restatement is required to intentionally replace a newer confirmed value',()=>{
  let s=typed(typed(initial(),'rice 42 bags'),'soap');const id=s.review[0].id;
  s=control(s,'discard');s=control(typed(s,'rice 51 bags'),'confirm');s=control(s,'resume',{reviewId:id});
  s=typed(s,'rice 42 bags');s=control(s,'confirm');assert.equal(s.counts.rice.quantity,42);
});
test('draft queue and confirmation are deterministic across saved action replay',()=>{
  let s=typed(initial(),'rice 42 bags');s=heard(s,'Confirm 42',{'42':.5});s=typed(s,'soap');
  s=control(s,'resume',{reviewId:s.review[0].id});s=control(s,'confirm');assert.deepEqual(replay(s.history),s);
});
test('CSV contains no queued drafts and only actual confirmed counts',()=>{
  let s=control(typed(initial(),'oil 10 bottles'),'confirm');s=typed(s,'rice 42 bags');s=typed(s,'soap');
  assert.equal(exportCSV(s),'item,quantity,unit\r\nCooking oil,10,bottles\r\n');
});
test('correction for a previously blocked quantity never reuses its stale value',()=>{
  let s=typed(initial(),'rice 42 bags');s=typed(s,'no 43',{confidence:.3});s=typed(s,'actually');s=typed(s,'bags');
  assert.equal(s.pending.quantity,null);assert.throws(()=>control(s,'confirm'));
});
test('partial provider results cannot focus items, discard, or release corrections',()=>{
  const s=typed(initial(),'rice 42 bags');for(const text of ['soap','discard','no'])assert.equal(typed(s,text,{final:false}),s);
});
test('same provider turn with changed command confidence is a conflict, not an ignored update',()=>{
  let s=typed(initial(),'rice 42 bags');s=heard(s,'Confirm 42',{'Confirm':.4,'42':.99},70000);
  assert.throws(()=>heard(s,'Confirm 42',{'Confirm':.99,'42':.99},70000),/Conflicting/);
});
test('review limit fails without mutating or dropping the original active draft',()=>{
  let s=initial();for(let i=0;i<101;i++)s=typed(s,i%2?'soap':'rice');
  assert.equal(s.review.length,100);const copy=structuredClone(s);
  assert.throws(()=>typed(s,'soap'),/queue is full/);assert.deepEqual(s,copy);
});
