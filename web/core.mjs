/* Recount: explicit single-item counting dialogue. No free-form LLM decisions. */
export const CATALOG = Object.freeze({
  rice: {label:'Rice', unit:'bags'}, beans:{label:'Beans',unit:'bags'},
  oil: {label:'Cooking oil',unit:'bottles'}, soap:{label:'Soap',unit:'bars'}
});
const SMALL = Object.fromEntries('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split(' ').map((s,i)=>[s,i]));
const TENS = {twenty:20,thirty:30,forty:40,fifty:50,sixty:60,seventy:70,eighty:80,ninety:90};
const NUMBER = new Set([...Object.keys(SMALL),...Object.keys(TENS),'hundred']);
const UNITS = {bag:'bags',bags:'bags',bottle:'bottles',bottles:'bottles',bar:'bars',bars:'bars',carton:'cartons',cartons:'cartons',piece:'pieces',pieces:'pieces'};
const FILLER = new Set('count counted have i we there are is of the a total set to stock cooking please now'.split(' '));
export const HOLD_REASONS = new Set(['stream_lost','unfinished_speech','transcript_conflict','stale_turn','invalid_event','audio_gap','consent_revoked']);
const TASK_CONFIDENCE_FLOOR=.75; // development heuristic; must be recalibrated on human speech before production use.
const VOICE_CONFIRM_FLOOR=.90; // stricter because this utterance commits the count.
export function initial(){return {revision:0,pending:null,hold:null,counts:{},review:[],seen:{},history:[],reply:'Name one item, its count, and its unit. For example: rice twelve bags.'};}
export function normalizeTranscript(s){return s.toLowerCase().replace(/[.,!?;:]/g,' ').replace(/(?<=[a-z])-(?=[a-z])/g,' ').replace(/\s+/g,' ').trim();}
function cleanToken(s){return String(s??'').toLowerCase().replace(/^[^a-z0-9]+|[^a-z0-9]+$/g,'');}
function num(words){
  if(words.length===1 && /^\d+$/.test(words[0])){const n=Number(words[0]);return Number.isSafeInteger(n)&&n<=9999?n:null;}
  if(words.some(w=>/^\d+$/.test(w)))return null;
  let w=[...words],n=0;
  if(w.length>=2 && SMALL[w[0]]>0 && SMALL[w[0]]<10 && w[1]==='hundred'){
    n=SMALL[w[0]]*100;w=w.slice(2);if(w[0]==='and')w.shift();if(!w.length)return n;
  }
  if(w.length===1 && SMALL[w[0]]!==undefined)return n+SMALL[w[0]];
  if((w.length===1||w.length===2)&&TENS[w[0]]){
    if(w.length===1)return n+TENS[w[0]];
    if(SMALL[w[1]]>0&&SMALL[w[1]]<10)return n+TENS[w[0]]+SMALL[w[1]];
  }
  return null;
}
function parts(text){
  const words=text?text.split(' '):[],skus=[...new Set(words.filter(w=>Object.hasOwn(CATALOG,w)))];
  const units=[...new Set(words.filter(w=>Object.hasOwn(UNITS,w)).map(w=>UNITS[w]))];
  const nums=words.filter(w=>NUMBER.has(w)||/^\d+$/.test(w)||w==='and');
  const unknown=words.filter(w=>!Object.hasOwn(CATALOG,w)&&!Object.hasOwn(UNITS,w)&&!NUMBER.has(w)&&!/^\d+$/.test(w)&&w!=='and'&&!FILLER.has(w));
  if(unknown.length||skus.length>1||units.length>1)return {error:'Count one catalogue item at a time, using a whole number and its unit.'};
  const quantity=nums.length?num(nums):null;
  if(nums.length&&quantity===null)return {error:'I need one unambiguous whole-number count. Please repeat the complete item and count.'};
  return {sku:skus[0]??null,unit:units[0]??null,quantity};
}
function confirmationNumber(t){
  const m=t.match(/^(?:confirm|confirmed|save|saved)\s+(.+)$/);if(!m)return null;
  const words=m[1].split(' ');
  if(!words.length||words.some(w=>!(NUMBER.has(w)||/^\d+$/.test(w)||w==='and')))return {error:'Confirm by repeating only the number, for example: confirm thirteen.'};
  const value=num(words);return value===null?{error:'I could not verify that confirmation number.'}:{confirmEcho:value};
}
export function parse(text,previous=null){
  const t=normalizeTranscript(text);
  if(['cancel','discard','discard count','cancel count'].includes(t))return {cancel:true};
  if(['confirm','confirmed','save','saved','save count','confirm count','confirmed count'].includes(t))return {confirmRequested:true};
  const confirmation=confirmationNumber(t);if(confirmation)return confirmation;
  if(['read back','read it back','repeat'].includes(t))return {repeat:true};
  const clauses=t.split(/\b(?:no|actually|sorry|make that|correction)\b/).map(s=>s.trim());
  if(clauses.length>1 && clauses.slice(1).some(x=>!x))return {error:'The correction was unfinished. Repeat the complete item, number and unit.'};
  const chunks=clauses.filter(Boolean);
  const correcting=/\b(?:no|actually|sorry|make that|correction)\b/.test(t);
  if(!chunks.length)return {error:'Repeat the item and the corrected count.'};
  let p=previous?{...previous,blocked:false}:{sku:null,quantity:null,unit:null,blocked:false};
  if(previous?.blocked){
    const repair=parts(chunks.at(-1));
    if(repair.error||!repair.sku||repair.quantity===null||!repair.unit)return {error:'The earlier count is uncertain. Repeat the complete item, number and unit, or discard it.'};
  }
  for(const chunk of chunks){
    const q=parts(chunk);if(q.error)return q;
    if(q.sku&&p.sku&&q.sku!==p.sku)return {error:'Confirm or discard the current item before starting a different item.'};
    if(q.unit&&p.unit&&q.unit!==p.unit&&!correcting)return {error:'The unit changed. Say the corrected unit explicitly or discard this draft.'};
    if(q.sku)p.sku=q.sku;if(q.quantity!==null)p.quantity=q.quantity;if(q.unit)p.unit=q.unit;
  }
  if(!p.sku)return {error:'Which item? This prototype knows rice, beans, cooking oil and soap.'};
  if(p.unit&&p.unit!==CATALOG[p.sku].unit)return {error:`Use ${CATALOG[p.sku].unit} for ${CATALOG[p.sku].label}. I will not guess pack conversions.`};
  if(previous?.identityUncertain){const restated=parts(chunks.at(-1));if(restated.sku&&restated.quantity!==null&&restated.unit)p.identityUncertain=false;}
  return {pending:p};
}
export function ready(p){return Boolean(p&&!p.blocked&&CATALOG[p.sku]&&Number.isSafeInteger(p.quantity)&&p.quantity>=0&&p.quantity<=9999&&p.unit===CATALOG[p.sku].unit);}
function describe(p){
  if(!p)return 'No count is waiting. Name one catalogue item and its count.';
  if(p.blocked)return 'The latest instruction needs clarification. Repeat the complete count before confirming.';
  if(p.quantity===null)return `How many ${CATALOG[p.sku].unit} of ${CATALOG[p.sku].label}?`;
  if(!p.unit)return `${p.quantity} ${CATALOG[p.sku].label}: which unit? Say ${CATALOG[p.sku].unit}.`;
  const warning=p.speechEvidence?.min_word_confidence<TASK_CONFIDENCE_FLOOR?' One non-number word was low-confidence, so verify this read-back carefully.':'';
  return `${CATALOG[p.sku].label}: ${p.quantity} ${p.unit}. To save hands-free, say “confirm ${p.quantity}”, or press Confirm count. This replaces its count, not adds to it.${warning}`;
}
function itemFocus(text){
  const t=normalizeTranscript(text);
  if(Object.hasOwn(CATALOG,t))return t;
  return t==='cooking oil'?'oil':null;
}
function parkPending(s,reason){
  if(!s.pending)return;
  if(s.review.length>=100)throw Error('Review queue is full; resolve an earlier draft first');
  s.review.push({id:`review:${s.revision}`,parkedAt:s.revision,reason,draft:structuredClone(s.pending)});
  s.pending=null;
}
function commandConfidence(action){
  return action.source==='assemblyai'?(action.recognition?.command_confidence??0):action.confidence;
}
function validKey(x){return typeof x==='string'&&/^[a-zA-Z0-9:_-]{1,140}$/.test(x);}
function savePending(s){s.counts[s.pending.sku]={quantity:s.pending.quantity,unit:s.pending.unit,revision:s.revision};s.reply=`Saved ${CATALOG[s.pending.sku].label}: ${s.pending.quantity} ${s.pending.unit}. What is the next item?`;s.pending=null;s.hold=null;}
export function reduce(before,action){
  if(!action||!['turn','confirm','discard','hold','resume'].includes(action.kind))throw Error('Unknown action');
  if(action.kind==='turn'&&action.final===false)return before;
  if(action.kind==='turn'){
    if(!validKey(action.id)||typeof action.text!=='string'||!action.text.trim()||action.text.length>500)throw Error('Invalid turn');
    if(!['typed','assemblyai','fixture'].includes(action.source)||action.final!==true)throw Error('Invalid turn provenance');
    if(!Number.isFinite(action.confidence)||action.confidence<0||action.confidence>1)throw Error('Invalid recognition confidence');
    if(Object.hasOwn(before.seen,action.id)){
      const prior=before.seen[action.id];
      if(prior.text===normalizeTranscript(action.text) && prior.confidence===action.confidence && prior.source===action.source && prior.commandConfidence===commandConfidence(action))return before;
      throw Error('Conflicting transcript for an existing turn; repeat as a new turn');
    }
  }
  if(action.kind==='hold'&&!HOLD_REASONS.has(action.reason))throw Error('Unknown hold reason');
  if(action.revision!==before.revision)throw Error('Draft changed; review the latest read-back');
  if(before.history.length>=1000)throw Error('Session limit reached; export and start a new session');
  const s=structuredClone(before);s.revision++;s.history.push(structuredClone(action));
  if(action.kind==='hold'){
    s.hold=action.reason;if(s.pending)s.pending.blocked=true;
    s.reply='Audio or transcript integrity needs review. Repeat the complete item, number and unit, or explicitly discard this uncertain input.';return s;
  }
  if(action.kind==='resume'){
    if(s.hold)throw Error('Resolve the audio integrity hold before resuming a review');
    const index=s.review.findIndex(r=>r.id===action.reviewId);
    if(index<0)throw Error('Review draft is no longer available');
    const [entry]=s.review.splice(index,1);
    parkPending(s,'operator_switched_review');s.pending=entry.draft;
    if((s.counts[s.pending.sku]?.revision??0)>entry.parkedAt){s.pending.blocked=true;s.pending.identityUncertain=true;s.reply='A newer count was confirmed after this review was parked. Restate the complete count before saving it.';}
    else s.reply='Review restored. '+describe(s.pending);return s;
  }
  if(action.kind==='discard'){s.hold=null;s.pending=null;s.reply='Draft discarded. Confirmed counts are unchanged.';return s;}
  if(action.kind==='confirm'){
    if(s.hold || !ready(s.pending))throw Error('A complete, clarified draft is required');
    savePending(s);return s;
  }
  s.seen[action.id]={text:normalizeTranscript(action.text),confidence:action.confidence,source:action.source,commandConfidence:commandConfidence(action)};
  const text=normalizeTranscript(action.text);
  const isDiscard=['cancel','discard','discard count','cancel count'].includes(text);
  if(isDiscard){
    // Cancellation never writes a stock row. Judge the action word, not its filler noun.
    if(commandConfidence(action)<TASK_CONFIDENCE_FLOOR){
      s.reply='Cancellation was unclear. Say discard again, or stop audio and use Discard draft.';return s;
    }
    s.hold=null;s.pending=null;s.reply='Draft discarded. Confirmed counts and other reviews are unchanged.';return s;
  }
  const echo=confirmationNumber(text);
  if(echo?.confirmEcho!==undefined){
    // Uncertainty in a confirmation does not make the earlier count itself uncertain.
    // Neither threshold is lowered; no confirmation supplies a missing draft quantity.
    if(s.hold||!ready(s.pending))s.reply='Nothing complete is ready to save. Repeat the full item, number and unit first.';
    else if(echo.confirmEcho!==s.pending.quantity)s.reply=`The confirmation said ${echo.confirmEcho}, but the read-back is ${s.pending.quantity}. Nothing was saved. Say “confirm ${s.pending.quantity}” or correct the count.`;
    else if(action.source==='assemblyai' && (commandConfidence(action)<TASK_CONFIDENCE_FLOOR || (action.recognition?.quantity_confidence??0)<VOICE_CONFIRM_FLOOR))
      s.reply='The confirmation number or command was not clear enough to commit. The draft is preserved. Repeat the confirmation number, or stop audio and review it on screen.';
    else if(action.confidence<TASK_CONFIDENCE_FLOOR)s.reply='The confirmation was uncertain. The draft is preserved; nothing was saved.';
    else savePending(s);
    return s;
  }
  if(['no','actually','sorry','make that','correction'].includes(text) && s.pending && !s.hold && !s.pending.identityUncertain){
    if(commandConfidence(action)<TASK_CONFIDENCE_FLOOR){s.pending.blocked=true;s.reply='The correction marker was uncertain. Repeat the full count.';return s;}
    // A fresh correction invalidates the old number; a unit-only fragment cannot restore it.
    s.pending={sku:s.pending.sku,quantity:null,unit:null,blocked:false,awaitingCorrection:true};
    s.reply=`Correcting ${CATALOG[s.pending.sku].label}. Say the new number and unit. Nothing is ready to save.`;return s;
  }
  const focus=itemFocus(action.text);
  if(focus && !s.hold){
    const confidence=action.source==='assemblyai'?(action.recognition?.item_confidence??0):action.confidence;
    if(confidence<TASK_CONFIDENCE_FLOOR){s.reply='The item name was uncertain. Repeat it; the current draft is unchanged.';return s;}
    if(s.pending?.sku!==focus){
      parkPending(s,'explicit_item_focus');
      s.pending={sku:focus,quantity:null,unit:null,blocked:false};
      if(action.recognition)s.pending.speechEvidence=structuredClone(action.recognition);
    }
    s.reply=describe(s.pending)+(s.review.length?' Earlier drafts are saved in Needs review, not confirmed stock.':'');return s;
  }
  if(action.confidence<TASK_CONFIDENCE_FLOOR){if(s.pending)s.pending.blocked=true;s.reply='The task-critical part of that transcript is uncertain. Please repeat the full item, number and unit.';return s;}
  let result=parse(action.text,s.pending);
  if(s.hold && result.pending){
    const restatement=parse(action.text);
    if(!restatement.pending || !ready(restatement.pending))result={error:'Repeat the entire uncertain count, including item and unit, or discard it.'};
  }
  if(result.error){
    if(s.pending){s.pending.blocked=true;const named=normalizeTranscript(action.text).split(' ').filter(w=>Object.hasOwn(CATALOG,w));if(named.some(w=>w!==s.pending.sku))s.pending.identityUncertain=true;}
    s.reply=result.error;
  }
  else if(result.cancel){s.hold=null;s.pending=null;s.reply='Draft discarded. Confirmed counts are unchanged.';}
  else if(result.confirmRequested){s.reply=ready(s.pending)?describe(s.pending):'Nothing complete to save yet. '+describe(s.pending);}
  else if(result.confirmEcho!==undefined){
    if(s.hold||!ready(s.pending)){s.reply='Nothing complete is ready to save. Repeat the full item, number and unit first.';}
    else if(result.confirmEcho!==s.pending.quantity){s.reply=`The confirmation said ${result.confirmEcho}, but the read-back is ${s.pending.quantity}. Nothing was saved. Say “confirm ${s.pending.quantity}” or correct the count.`;}
    else if(action.source==='assemblyai' && (action.recognition?.quantity_confidence??0)<VOICE_CONFIRM_FLOOR){s.reply='The confirmation number was not clear enough to commit. Repeat the confirmation number.';}
    else savePending(s);
  }
  else if(result.repeat)s.reply=describe(s.pending);
  else{
    s.hold=null;s.pending=result.pending;
    if(action.source==='assemblyai'&&action.recognition)s.pending.speechEvidence=structuredClone(action.recognition);
    s.reply=describe(s.pending);
  }
  return s;
}
export function fromAssembly(message,session,revision){
  if(!message||message.type!=='Turn'||message.end_of_turn!==true)return null;
  if(!validKey(session)||!Number.isSafeInteger(message.turn_order)||message.turn_order<0)throw Error('Invalid provider turn identity');
  if(!Array.isArray(message.words)||!message.words.length)throw Error('Word-confidence evidence missing');
  const rows=message.words.map(w=>({token:cleanToken(w.text),confidence:w.confidence}));
  if(rows.some(x=>!Number.isFinite(x.confidence)||x.confidence<0||x.confidence>1))throw Error('Invalid word confidence');
  const nums=rows.filter(x=>NUMBER.has(x.token)||/^\d+$/.test(x.token));
  const units=rows.filter(x=>Object.hasOwn(UNITS,x.token));
  const items=rows.filter(x=>Object.hasOwn(CATALOG,x.token));
  const commands=rows.filter(x=>['confirm','confirmed','save','saved','discard','cancel','no','actually','sorry','make','that','correction'].includes(x.token));
  const semantic=[...nums,...units,...items];
  const taskRows=nums.length?nums:(semantic.length?semantic:rows);
  const recognition={policy:'quantity-first-v1',command_confidence:commands.length?Math.min(...commands.map(x=>x.confidence)):null,min_word_confidence:Math.min(...rows.map(x=>x.confidence)),quantity_confidence:nums.length?Math.min(...nums.map(x=>x.confidence)):null,unit_confidence:units.length?Math.min(...units.map(x=>x.confidence)):null,item_confidence:items.length?Math.min(...items.map(x=>x.confidence)):null,task_confidence:Math.min(...taskRows.map(x=>x.confidence)),development_floor:TASK_CONFIDENCE_FLOOR,voice_confirm_floor:VOICE_CONFIRM_FLOOR};
  return {kind:'turn',id:`${session}:${message.turn_order}`,text:message.transcript,confidence:recognition.task_confidence,recognition,source:'assemblyai',final:true,revision};
}
export function replay(log){
  if(!Array.isArray(log)||log.length>1000)throw Error('Invalid session history');
  return log.reduce((s,a)=>reduce(s,a),initial());
}
export function exportCSV(s){if(s.hold)throw Error('Resolve or discard the uncertain input before exporting');return 'item,quantity,unit\r\n'+Object.entries(s.counts).map(([sku,r])=>`${CATALOG[sku].label},${r.quantity},${r.unit}\r\n`).join('');}
