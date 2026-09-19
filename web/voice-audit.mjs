// Redact known access-code patterns and explicitly supplied secrets in export copies.
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

import {SPEECH_ERRORS} from './readback.mjs';
/* Local-only, bounded interaction evidence. No audio, credentials or query URLs. */
const EVENTS=new Set(['speaker_test_started','speaker_test_finished','speaker_test_confirmed','speaker_test_unheard','speaker_test_failed','readback_failed','capture_options','session_requested','setup_stage','setup_failed','socket_open','socket_error','socket_closed','provider_begin','provider_final','duplicate_final_ignored','readback_started','readback_finished','readback_cancelled','readback_superseded','premature_confirmation_rejected','session_hold','session_closed','stop_requested','consent_revoked']);
const REASONS=new Set(['stream_lost','unfinished_speech','transcript_conflict','stale_turn','invalid_event','audio_gap','consent_revoked']);
const SETUP_STAGES=new Set(['microphone_request','microphone_ready','audio_context_ready','worklet_ready','token_request','token_response','token_ready','socket_created']);
const ERROR_NAMES=new Set(['Error','TypeError','NotAllowedError','NotFoundError','NotReadableError','NotSupportedError','SecurityError','AbortError','InvalidStateError']);
export class VoiceAudit {
  constructor({now=()=>performance.now(),limit=512}={}){
    if(!Number.isInteger(limit)||limit<1||limit>2048)throw Error('Invalid audit limit');
    this.now=now;this.limit=limit;this.events=[];this.dropped=0;this.started=now();
  }
  add(row){
    if(!row||!EVENTS.has(row.event))return;
    if(this.events.length>=this.limit){this.dropped++;return;}
    const out={event:row.event,elapsed_ms:Math.max(0,Math.round(this.now()-this.started))};
    for(const k of ['revision','order','epoch','generation'])if(Number.isSafeInteger(row[k])&&row[k]>=0)out[k]=row[k];
    if(REASONS.has(row.reason))out.reason=row.reason;
    if(SETUP_STAGES.has(row.stage))out.setup_stage=row.stage;
    if(ERROR_NAMES.has(row.errorName))out.error_name=row.errorName;
    if(Number.isInteger(row.httpStatus)&&row.httpStatus>=100&&row.httpStatus<=599)out.http_status=row.httpStatus;
    if(Number.isInteger(row.sampleRate)&&row.sampleRate>=8000&&row.sampleRate<=192000)out.sample_rate=row.sampleRate;
    if(Number.isInteger(row.closeCode)&&row.closeCode>=0&&row.closeCode<=4999)out.close_code=row.closeCode;
    if(typeof row.wasClean==='boolean')out.was_clean=row.wasClean;
    if(SPEECH_ERRORS.has(row.code))out.error_code=row.code;
    for(const k of ['voice_count','english_voice_count'])if(Number.isSafeInteger(row[k])&&row[k]>=0&&row[k]<=10000)out[k]=row[k];
    if(['bundled-neural-audio','native-speech'].includes(row.backend))out.playback_backend=row.backend;
    if(typeof row.supported==='boolean')out.speech_api_available=row.supported;
    if(['completed','disabled','cancelled','unavailable'].includes(row.status))out.status=row.status;
    if(typeof row.spokenReadback==='boolean')out.spoken_readback_requested=row.spokenReadback;
    this.events.push(out);
  }
  hasSession(){return this.events.some(e=>e.event==='session_requested');}
  hasReport(){return this.hasSession()||this.events.some(e=>e.event==='speaker_test_started');}
  snapshot(state,{origin='',assetHashes={},secrets=[]}={}){
    let site='';try{site=new URL(origin).origin;}catch{}
    const hashes={};
    for(const name of ['app.mjs','core.mjs','capture-gate.mjs','voice-runtime.mjs','readback.mjs','voice-audit.mjs','audio-worklet.js','streaming-request.mjs','speaker-check.mjs','audio-readback.mjs']){
      const hash=assetHashes[name];if(typeof hash==='string'&&/^[a-f0-9]{64}$/.test(hash))hashes[name]=hash;
    }
    const safe=redactForExport({schema:'recount-session-2',revision:state.revision,counts:state.counts,pending:state.pending,review:state.review,hold:state.hold,history:state.history},secrets);
    return {
      schema:'recount-interaction-report-1',client_revision:'bundled-neural-audio-startup-diagnostics-20260919',site,
      classification:'Client-collected interaction evidence; no automatic pass, human-speaker, physical-count or ASR-accuracy claim.',
      privacy:{audio_recorded:false,audio_in_report:false,configured_credentials_included:false,known_credential_redactions:safe.redactions,review_before_sharing:true,contains_transcript_text:true,upload_performed:false},
      events:structuredClone(this.events),events_dropped:this.dropped,asset_sha256:hashes,
      summary:{speaker_tests:this.events.filter(e=>e.event==='speaker_test_started').length,speaker_tests_confirmed_by_user:this.events.filter(e=>e.event==='speaker_test_confirmed').length,speech_output_errors:this.events.filter(e=>e.event==='speaker_test_failed'||e.event==='readback_failed').length,sessions_requested:this.events.filter(e=>e.event==='session_requested').length,provider_begins:this.events.filter(e=>e.event==='provider_begin').length,final_events:this.events.filter(e=>e.event==='provider_final').length,
        completed_readbacks:this.events.filter(e=>e.event==='readback_finished'&&e.status==='completed').length,disabled_readbacks:this.events.filter(e=>e.event==='readback_finished'&&e.status==='disabled').length,
        setup_failures:this.events.filter(e=>e.event==='setup_failed').length,socket_opens:this.events.filter(e=>e.event==='socket_open').length,socket_errors:this.events.filter(e=>e.event==='socket_error').length,socket_closes:this.events.filter(e=>e.event==='socket_closed').length,
        last_setup_stage:[...this.events].reverse().find(e=>e.event==='setup_stage')?.setup_stage??null,
        premature_confirmations_rejected:this.events.filter(e=>e.event==='premature_confirmation_rejected').length,holds:this.events.filter(e=>e.event==='session_hold').length},
      ledger:safe.value
    };
  }
}
