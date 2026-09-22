// Logic coverage, not ASR accuracy: no provider calls or recognition events are injected.
import test from 'node:test';
import assert from 'node:assert/strict';
import {CATALOG, initial, reduce} from '../web/core.mjs';
import {buildCloseout, exportCompleteCSV} from '../web/closeout.mjs';
const quantities=[0,1,2,7,27,41,99,101,999,1000,9999];
function typed(state,text,id){return reduce(state,{kind:'turn',id,text,final:true,source:'typed',confidence:1,revision:state.revision});}
for(const [sku,item] of Object.entries(CATALOG))test(`${sku}: varied quantities are data, not a rehearsed scenario`,()=>{
 for(const q of quantities){
  let s=typed(initial(),`${sku} ${q} ${item.unit}`,'count');
  assert.equal(s.pending.quantity,q);assert.deepEqual(s.counts,{});
  s=typed(s,`confirm ${q===9999?9998:q+1}`,'wrong');
  assert.deepEqual(s.counts,{});assert.equal(s.pending.quantity,q);
  s=typed(s,`confirm ${q}`,'right');
  assert.equal(s.counts[sku].quantity,q);assert.equal(s.pending,null);
  const c=buildCloseout(s);assert.equal(c.totals.confirmed,1);assert.equal(c.complete,false);
  assert.equal(c.rows.find(r=>r.sku===sku).confirmation_method,'typed');
  assert.throws(()=>exportCompleteCSV(s));
 }
});
