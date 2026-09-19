"""Bounded UI/privacy patch. Count parser, thresholds and prior results stay unchanged."""
from pathlib import Path
import hashlib,json

def change(path,old,new):
    p=Path(path);s=p.read_text();assert s.count(old)==1,(path,old[:80],s.count(old));p.write_text(s.replace(old,new))

core_hash=hashlib.sha256(Path('web/core.mjs').read_bytes()).hexdigest()
assert core_hash=='4f1694bef7c978e92effbce2dc5ac6c1ec3874ab62d08b2e288d6704faa42854'

p=Path('web/voice-audit.mjs');s=p.read_text()
helper=r'''// Redact known access-code patterns and explicitly supplied secrets in export copies.
// Arbitrary sensitive speech cannot be identified perfectly; users must review reports.
export function redactForExport(value,secrets=[]){
  const known=[...new Set(secrets.filter(s=>typeof s==='string'&&s.length>=8))];
  let redactions=0;
  function visit(v){
    if(typeof v==='string'){
      let out=v;
      for(const secret of known){if(out.includes(secret)){redactions+=out.split(secret).length-1;out=out.split(secret).join('[REDACTED_ACCESS_CODE]');}}
      return out.replace(/\brecount-[A-Za-z0-9_-]{12,128}\b/gi,()=>{redactions++;return '[REDACTED_ACCESS_CODE]';});
    }
    if(Array.isArray(v))return v.map(visit);
    if(v&&typeof v==='object')return Object.fromEntries(Object.entries(v).map(([k,x])=>[k,visit(x)]));
    return v;
  }
  return {value:visit(value),redactions};
}
export function hasCredentialText(text,secrets=[]){return redactForExport(text,secrets).redactions>0;}
'''
s=helper+'\n'+s
assert s.count("snapshot(state,{origin='',assetHashes={}}={}){")==1
s=s.replace("snapshot(state,{origin='',assetHashes={}}={}){","snapshot(state,{origin='',assetHashes={},secrets=[]}={}){")
old="    return {\n      schema:'recount-interaction-report-1',client_revision:'readback-barrier-20260919',site,"
new="    const safe=redactForExport({schema:'recount-session-2',revision:state.revision,counts:state.counts,pending:state.pending,review:state.review,hold:state.hold,history:state.history},secrets);\n    return {\n      schema:'recount-interaction-report-1',client_revision:'voice-setup-20260919',site,"
assert s.count(old)==1;s=s.replace(old,new)
old="privacy:{audio_recorded:false,audio_in_report:false,credentials_in_report:false,contains_transcript_text:true,upload_performed:false},"
new="privacy:{audio_recorded:false,audio_in_report:false,configured_credentials_included:false,known_credential_redactions:safe.redactions,review_before_sharing:true,contains_transcript_text:true,upload_performed:false},"
assert s.count(old)==1;s=s.replace(old,new)
old="ledger:structuredClone({schema:'recount-session-2',revision:state.revision,counts:state.counts,pending:state.pending,review:state.review,hold:state.hold,history:state.history})"
assert s.count(old)==1;s=s.replace(old,"ledger:safe.value")
p.write_text(s)

change('web/app.mjs',"import {VoiceAudit} from './voice-audit.mjs';","import {VoiceAudit,redactForExport,hasCredentialText} from './voice-audit.mjs';")
change('web/app.mjs',"function speak(){if(!voice.active())void say(state.reply).catch(e=>error(e));}","function speak(){if(!voice.active()&&state.history.at(-1)?.source==='assemblyai')void say(state.reply).catch(e=>error(e));}")
change('web/app.mjs',"  $('accessCode').disabled=locked||!config?.requires_access_code;","  $('accessCode').disabled=locked||!config?.requires_access_code;\n  $('speak').disabled=locked;\n  $('voiceSetupStatus').textContent=$('speak').checked?'Voice replies ON. Wait for the reply to finish before speaking again.':'SILENT REVIEW MODE: no spoken replies. Read the on-screen response before continuing.';")
change('web/app.mjs',"function typed(text){userAction({kind:'turn',id:crypto.randomUUID(),text,source:'typed',confidence:1,final:true});}","function typed(text){\n  if(hasCredentialText(text,[$('accessCode').value.trim()])){\n    $('voiceSetup').open=true;\n    if(/^recount-[A-Za-z0-9_-]{12,128}$/.test(text.trim()))$('accessCode').value=text.trim();\n    $('accessCode').focus();error('Access code detected. Use the Judge access code field, not the stock transcript. Nothing was added to the count history.');return;\n  }\n  userAction({kind:'turn',id:crypto.randomUUID(),text,source:'typed',confidence:1,final:true});\n}")
change('web/app.mjs',"audit.snapshot(state,{origin:location.origin,assetHashes:hashes})","audit.snapshot(state,{origin:location.origin,assetHashes:hashes,secrets:[$('accessCode').value.trim()]})")
change('web/app.mjs',"$('session').onclick=()=>{if(voice.active())return error('Finish the voice session before saving.');download(","$('session').onclick=()=>{if(voice.active())return error('Finish the voice session before saving.');if(redactForExport(state.history,[$('accessCode').value.trim()]).redactions)return error('This session contains an access code in its transcript. Use the redacted voice report instead; the original history was not altered.');download(")
change('web/app.mjs',"$('consent').onchange=()=>", "$('speak').onchange=()=>{cancelSpeech();render();};\n$('consent').onchange=()=>")

old_toggle='<label class="check"><input type="checkbox" id="speak"> Speak each read-back using the browser voice</label>'
change('web/index.html',old_toggle,'')
change('web/index.html','<details><summary>Live AssemblyAI voice path</summary>','<details id="voiceSetup"><summary>Live AssemblyAI voice path</summary>')
change('web/index.html','<label class="check"><input type="checkbox" id="consent">','<label class="check"><input type="checkbox" id="speak" checked> Speak voice replies aloud</label><p id="voiceSetupStatus" class="status" role="status">Voice replies ON. Wait for the reply to finish before speaking again.</p><label class="check"><input type="checkbox" id="consent">')
change('web/index.html','No audio or speech recognition in text mode','Stock commands only. Put access codes in the Judge access code field below.')
change('web/index.html','It is never written to the stock/session log.','Do not enter this code in the stock transcript. Known code patterns are blocked there.')
change('web/index.html','It contains transcript text and timing events, not audio or access codes.','It contains transcript text and timing events, not audio. Known access-code patterns are redacted; review before sharing.')

# Update present-day instructions only; historical receipts keep their original origins.
for name in ['README.md','SUBMISSION_DRAFT.md','.env.example']:
    p=Path(name)
    if p.exists():p.write_text(p.read_text().replace('recount-voice-joseph','recount-voice'))
assert hashlib.sha256(Path('web/core.mjs').read_bytes()).hexdigest()==core_hash
Path('/tmp/voice-setup-patch.json').write_text(json.dumps({'count_policy_unchanged':True,'core_sha256':core_hash,'new_site':'https://recount-voice.netlify.app','changes':['Voice reply setting visible at microphone controls, enabled by default','Known access-code input excluded from new stock history','Known credentials redacted from report copies; contaminated session exports blocked without rewriting history'],'provider_calls':0},indent=2))
