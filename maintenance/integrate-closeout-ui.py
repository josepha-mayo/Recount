"""One-time integration of the closeout UI into the exact reviewed frontend.
This script has no network access or credentials. Recognition/auth/core files are unchanged.
"""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
EXPECTED={
 'web/app.mjs':'48690448c047abf41c8781e089386650f8c2e702',
 'web/index.html':'78fb634b319ebf188cb850a4d472ce2a18bdff66',
 'web/style.css':'10a38375f8a65a24d25f21d5bfdf15edbc46dbcf',
 'web/voice-audit.mjs':'f89dbce0eb6d000fb1f51649cdc6f24ce1b19b2f',
 'server.py':'3186bf9c3ae08b08a356f9e95933f171c8ededa7',
 'tests/browser.py':'1deb7566d3e7256ddf12e8c1648a2baf453385f8',
 'tests/browser_readback_barrier.py':'cec67587583156bd9dc6a4d401003621913a8d1a'}
for name,expected in EXPECTED.items():
 data=(ROOT/name).read_bytes()
 assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==expected, 'Source changed: '+name

def once(s,old,new):
 assert s.count(old)==1, 'Unexpected integration context: '+old[:80]
 return s.replace(old,new)

p=ROOT/'web/app.mjs';s=p.read_text()
s="import {buildCloseout,exportCompleteCSV} from './closeout.mjs';\n"+s
block="""  const closeout=buildCloseout(state);
  $('closeoutBadge').textContent=`${closeout.totals.confirmed} / ${closeout.totals.scope} resolved`;
  $('closeoutStatus').textContent=closeout.complete?'Every scoped item is confirmed. No open drafts remain.':`${closeout.totals.needs_review} items need review. ${closeout.totals.not_counted} items have not been counted.${closeout.hold?' Resolve the audio hold before closing.':''}`;
  $('handoff').disabled=locked;$('completeCSV').disabled=locked||!closeout.complete;
  const closure=$('closeoutRows');closure.replaceChildren();
  for(const row of closeout.rows){
    const line=document.createElement('div');line.className='closeout-row';
    const name=document.createElement('strong');name.textContent=row.item;
    const status=document.createElement('span');status.className='closeout-'+row.status;
    status.textContent=row.status==='confirmed'?`${row.confirmed_quantity} ${row.unit} confirmed`:row.status==='needs_review'?`${row.open_drafts} open draft${row.open_drafts===1?'':'s'}`:'Not counted';
    line.append(name,status);closure.append(line);
  }
"""
s=once(s,"  const last=state.history.at(-1);",block+"  const last=state.history.at(-1);")
handlers="""$('handoff').onclick=()=>{try{if(voice.active())throw Error('Stop voice before exporting a handoff.');download('recount-review-handoff.json',JSON.stringify(buildCloseout(state),null,2),'application/json');}catch(e){error(e);}};
$('completeCSV').onclick=()=>{try{if(voice.active())throw Error('Stop voice before closing the stocktake.');download('recount-complete-stocktake.csv',exportCompleteCSV(state),'text/csv');}catch(e){error(e);}};
"""
s=once(s,"$('session').onclick=",handlers+"$('session').onclick=")
s=once(s,"'startup-errors.mjs']","'startup-errors.mjs','closeout.mjs']");p.write_text(s)

p=ROOT/'web/index.html';s=p.read_text()
s=once(s,'Recount | Count it. Correct it. Confirm it.','Recount | Voice Stocktakes Without Lost Work')
s=once(s,'ONE COUNT. EVEN WHEN YOU CHANGE YOUR MIND.','KEEP COUNTING. KEEP UNFINISHED WORK VISIBLE.')
s=once(s,'Count it.<br>Correct it. <em>Confirm it.</em>','Walk the stockroom.<br><em>Finish the stocktake.</em>')
s=once(s,'Turn a spoken count into a checked stock sheet without letting corrections, retries or vague confirmations silently duplicate inventory.','Count by voice, park unfinished items, and return to the exceptions. Hand over confirmed counts with a clear view of what still needs attention.')
s=once(s,'<span>spoken quantity echo</span><span>duplicate-final guard</span><span>hold-on-failure recovery</span>','<span>unfinished-work recovery</span><span>explicit confirmation</span><span>review-ready handoff</span>')
s=once(s,'placeholder="rice twelve bags"','placeholder="beans 27 bags"')
start=s.index('<div class="examples">');end=s.index('</div>',start)+len('</div>')
s=s[:start]+'''<div class="examples"><button class="chip" data-example="beans 27 bags">Count beans</button><button class="chip" data-example="oil">Park draft / move to oil</button><button class="chip" data-example="16 bottles">Count oil</button><button class="chip" data-example="confirm 16">Confirm current oil count</button></div><p class="small">Examples send real text commands, not a simulated success. Confirm the number currently shown. Say the next item name alone to park an unfinished draft.</p>'''+s[end:]
section='''<section id="closeoutPanel" class="closeout-panel"><div class="heading"><h3>Stocktake closeout</h3><span class="badge" id="closeoutBadge">0 / 4 resolved</span></div><p id="closeoutStatus" role="status" aria-live="polite"></p><div id="closeoutRows"></div><div class="actions"><button id="handoff" class="secondary">Download review handoff</button><button id="completeCSV" disabled>Export complete stocktake</button></div><p class="small">Scope: four prototype items. Not counted is never treated as zero. The regular CSV contains confirmed rows only and may be partial. The handoff lists omissions and unresolved work without transcript text or audio.</p></section>'''
s=once(s,'<h3 class="history-title">',section+'<h3 class="history-title">');p.write_text(s)

p=ROOT/'web/style.css';s=p.read_text();s+='\n.closeout-panel{border-top:1px solid #344339;margin-top:1.4rem;padding-top:1rem}.closeout-row{display:flex;justify-content:space-between;gap:1rem;padding:.65rem 0;border-bottom:1px solid #2d3a32}.closeout-row span{text-align:right}.closeout-needs_review{color:#e2c084}.closeout-not_counted{color:#b8c3bc}.closeout-confirmed{color:#c6e091}#closeoutStatus{line-height:1.5}#closeoutPanel .actions{flex-wrap:wrap}\n';p.write_text(s)
p=ROOT/'web/voice-audit.mjs';s=p.read_text();s=once(s,"'startup-errors.mjs']","'startup-errors.mjs','closeout.mjs']");s=once(s,'persistent-startup-errors-20260920','stocktake-closeout-20260922');p.write_text(s)
p=ROOT/'server.py';s=p.read_text();s=once(s,"paths={'/startup-errors.mjs'","paths={'/closeout.mjs':('closeout.mjs','text/javascript'),'/startup-errors.mjs'");p.write_text(s)
p=ROOT/'tests/browser.py';s=p.read_text()
for value in ['rice twelve','bags','no thirteen']:
 s=once(s,"page.locator('[data-example=\""+value+"\"]').click();","page.locator('#utterance').fill('"+value+"');page.locator('#textForm button').click();")
p.write_text(s)
p=ROOT/'tests/browser_readback_barrier.py';s=p.read_text();s=once(s,"'startup-errors.mjs'}","'startup-errors.mjs','closeout.mjs'}");p.write_text(s)
print('Integrated read-only closeout UI. Core ledger, recognition, runtime and hosted authorization unchanged.')
