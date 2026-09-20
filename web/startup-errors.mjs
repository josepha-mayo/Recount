// Fixed public error classes only. Never return provider bodies or device labels.
const MESSAGES=new Map([
  ['Invalid judge access code.','invalid_access_code'],
  ['Refresh the page before starting voice mode.','session_expired'],
  ['Same-origin request required.','origin_rejected'],
  ['Provider token service is temporarily unavailable.','provider_unavailable'],
  ['Provider token service rejected the request.','provider_rejected'],
  ['Voice mode is not configured on this deployment.','voice_not_configured'],
]);
export const STARTUP_FAILURE_CODES=new Set([...MESSAGES.values(),'microphone_denied','microphone_missing','microphone_unreadable','startup_failed','startup_timeout']);
const STAGES=new Set(['microphone_request','microphone_ready','audio_context_ready','worklet_ready','token_request','token_response','token_ready','socket_created']);
export function startupFailure(error,stage){
  const code=MESSAGES.get(error?.message);
  if(code)return {code,message:error.message};
  if(stage==='microphone_request'){
    const device={NotAllowedError:['microphone_denied','Microphone permission was denied. Allow microphone access in your browser before starting voice.'],
      NotFoundError:['microphone_missing','No microphone was found. Connect one before starting voice.'],
      NotReadableError:['microphone_unreadable','The microphone could not be opened. Check whether another application is using it.']}[error?.name];
    if(device)return {code:device[0],message:device[1]};
  }
  const where=STAGES.has(stage)?stage.replaceAll('_',' '):'startup';
  return {code:'startup_failed',message:`Voice setup failed during ${where}. Nothing was saved. Download the voice report for details.`};
}
