"""One-time migration of four runtime files plus CI. No network or credentials.
Aborts unless outputs exactly match the locally tested source bytes.
"""
from pathlib import Path
import hashlib
p=Path(__file__).resolve().parents[1]
f=p/'web/voice-runtime.mjs';s=f.read_text()
s=s.replace("import {streamingURL} from './streaming-request.mjs';","import {streamingURL} from './streaming-request.mjs';\nimport {normalizeTranscript} from './core.mjs';")
s=s.replace('cancelPrompt=()=>{},deps={}})', 'cancelPrompt=()=>{},onTrace=()=>{},deps={}})')
s=s.replace('onError,promptReply,cancelPrompt});','onError,promptReply,cancelPrompt,onTrace});')
s=s.replace("  active(){", "  trace(event,details={}){try{this.onTrace({event,revision:this.getRevision(),...details});}catch{ /* Diagnostics cannot change the count path. */ }}\n  active(){")
s=s.replace("stopPrompt(v){if(v?.prompting){try{this.cancelPrompt();}catch{}v.prompting=false;}}", "stopPrompt(v){if(v?.prompting){v.promptGeneration++;v.prompting=false;try{this.cancelPrompt();}catch{}this.trace('readback_cancelled');}}")
s=s.replace("if(this.current===v){this.current=null;this.onState('idle');}","if(this.current===v){this.current=null;this.trace('session_closed');this.onState('idle');}")
s=s.replace("fail(v,reason){if(!this.live(v))return;try", "fail(v,reason){if(!this.live(v))return;this.trace('session_hold',{reason});try")
s=s.replace('    v.prompting=true;','    const generation=++v.promptGeneration;v.prompting=true;')
s=s.replace("    this.onState('prompting');\n    try{await this.promptReply();}catch{this.onError", "    this.trace('readback_started',{generation});this.onState('prompting');\n    let result;\n    try{result=await this.promptReply();}catch{if(generation!==v.promptGeneration||!this.live(v))return;this.onError")
s=s.replace("    if(!this.live(v)||v.gate.phase!=='listening'){v.prompting=false;return;}\n    try{v.input.connect", "    if(generation!==v.promptGeneration||!this.live(v))return;\n    if(result?.status==='unavailable'||result?.status==='cancelled'){this.onError('Read-back did not complete. Stop and review the draft.');this.fail(v,'audio_gap');return;}\n    if(v.gate.phase!=='listening'){v.prompting=false;return;}\n    this.trace('readback_finished',{generation,status:result?.status??'completed'});\n    try{v.input.connect")
s=s.replace("const v={epoch:++this.generation,finished:false,prompting:false};this.current=v;", "const v={epoch:++this.generation,finished:false,prompting:false,promptGeneration:0};this.current=v;this.trace('session_requested',{epoch:v.epoch});")
s=s.replace("const message=JSON.parse(e.data);const outcome=v.gate.ingest(v.epoch,message);", """const message=JSON.parse(e.data);
          // A provider can deliver queued final turns while local speech is still
          // playing. That is not permission to confirm an unheard read-back.
          // Exact duplicate finals still go through CaptureGate's idempotency guard.
          if(v.prompting && message.type==='Turn' && message.end_of_turn===true &&
             Number.isSafeInteger(message.turn_order) && message.turn_order>v.gate.lastOrder){
            const text=normalizeTranscript(String(message.transcript??''));
            if(/^(?:confirm|confirmed|save|saved)(?:\\s|$)/.test(text)){
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
          if(outcome==='terminated')this.trace('provider_terminated');""")
s=s.replace("stop(){\n    const v=this.current;if(!v)return;", "stop(){\n    const v=this.current;if(!v)return;this.trace('stop_requested');")
s=s.replace("revoke(){const v=this.current;if(v){", "revoke(){const v=this.current;if(v){this.trace('consent_revoked');")
f.write_text(s)
f=p/'web/app.mjs';s=f.read_text();s=s.replace("import {ReadbackPlayer} from './readback.mjs';", "import {ReadbackPlayer} from './readback.mjs';\nimport {VoiceAudit} from './voice-audit.mjs';\nconst audit=new VoiceAudit();")
s=s.replace("$('session').disabled=locked;", "$('session').disabled=locked;$('voiceReport').disabled=locked||!audit.hasSession();")
s=s.replace("cancelPrompt:cancelSpeech});", "cancelPrompt:cancelSpeech,onTrace:event=>audit.add(event)});")
s=s.replace("  await voice.start(runtimeConfig,$('consent').checked);", "  audit.add({event:'capture_options',spokenReadback:$('speak').checked});\n  await voice.start(runtimeConfig,$('consent').checked);")
needle="$('session').onclick=()=>{";pos=s.index(needle)
block="""$('voiceReport').onclick=async()=>{try{
  if(voice.active())throw Error('Stop voice and wait for finalization before exporting the report.');
  if(!audit.hasSession())throw Error('Start a voice session first.');
  const revision=state.revision,hashes={};
  for(const name of ['app.mjs','core.mjs','capture-gate.mjs','voice-runtime.mjs','readback.mjs','voice-audit.mjs','audio-worklet.js','streaming-request.mjs']){
    try{const r=await fetch('/'+name,{cache:'no-store'});if(!r.ok)continue;const digest=await crypto.subtle.digest('SHA-256',await r.arrayBuffer());hashes[name]=Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');}catch{}
  }
  if(voice.active()||state.revision!==revision)throw Error('The session changed during export. Finish it and try again.');
  download('Recount-Interaction-Report.json',JSON.stringify(audit.snapshot(state,{origin:location.origin,assetHashes:hashes}),null,2),'application/json');
}catch(e){error(e);}};
"""
s=s[:pos]+block+s[pos:];f.write_text(s)
f=p/'web/index.html';s=f.read_text();s=s.replace('<button id="listen" class="secondary" disabled>Start voice session</button>', '<button id="listen" class="secondary" disabled>Start voice session</button> <button id="voiceReport" class="secondary" disabled>Download voice report</button><p class="small">To check the real interaction, enable spoken read-back, speak one count, wait for the reply, then confirm or correct it. When finished, stop voice and download the report. It contains transcript text and timing events, not audio or access codes. Nothing is uploaded by the report button.</p>');f.write_text(s)
f=p/'server.py';s=f.read_text();needle="'/app.mjs':('app.mjs','text/javascript')";assert needle in s;s=s.replace(needle,needle+",'/voice-audit.mjs':('voice-audit.mjs','text/javascript')");f.write_text(s)
expected={
'web/voice-runtime.mjs':'8727c3a0d575444b221f9a409725ecd99c3eba5098a11d05f2b2bba29767e220',
'web/app.mjs':'9b4c1aba3914fd57a4e6cca14743dcf59d4188b38c465ce3251fce9e521f64b9',
'web/index.html':'215e0a1a8749c673d3e2f21fe721af20c2c3314b48c9d6492187ea193adcda7c',
'server.py':'524960f7632677b407ec7d95c0353c4b748b68d1f70787f0e175487f43409f16',
'web/voice-audit.mjs':'4539b1c5289dd43b96251d875f4b45a201fd01a4ea15bff834d18f045cac2696',
'tests/readback_barrier.test.mjs':'5526677db938fa6371700b442de6fabc79e5fabc5b170050e3fe9db39d2b8071',
'tests/voice_audit.test.mjs':'329ecb9f0d940a191ce3ee5ad665d4de76d412870c9ee3b978bd3c4e513ce3be',
'tests/browser_readback_barrier.py':'b278c4e7b0a982661265511d8a9a277f99209c66125774ecf52810d9efa5b48b'}
for name,want in expected.items():assert hashlib.sha256((p/name).read_bytes()).hexdigest()==want,name
# Preserve inherited suites and add the asynchronous browser suite to ordinary CI.
f=p/'.github/workflows/ci.yml';s=f.read_text()
needle='          cp verification/desktop-*.png /tmp/recount-ci/'
assert needle in s
s=s.replace(needle,"          RECOUNT_BARRIER_OUT=/tmp/recount-ci/readback-barrier python tests/browser_readback_barrier.py | tee /tmp/recount-ci/readback-barrier.log\n"+needle)
s=s.replace("v=json.loads((p/'voice-recovery/RECEIPT.json').read_text())", "v=json.loads((p/'voice-recovery/RECEIPT.json').read_text());g=json.loads((p/'readback-barrier/RECEIPT.json').read_text())")
s=s.replace("and v['status']=='passed'", "and v['status']=='passed' and g['status']=='passed'")
s=s.replace("'voice_recovery_browser_checks':v['check_count'],", "'voice_recovery_browser_checks':v['check_count'],'readback_barrier_browser_checks':g['check_count'],")
f.write_text(s)
print('Verified all eight patched/new files against local SHA-256 values; CI extended without removing inherited tests.')
