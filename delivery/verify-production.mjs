// Production smoke check. Secrets come only from the environment and are never exported.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {streamingURL} from '../web/streaming-request.mjs';
export const BASE='https://recount-voice.netlify.app';
const SAFE=new Set(['Invalid judge access code.','Refresh the page before starting voice mode.','Same-origin request required.','Voice mode is not configured on this deployment.','Judge deployment is not fully configured.','Provider token service rejected the request.','Provider token service is temporarily unavailable.']);
export async function authorize(code,fetcher=fetch){
  const result={config_http_status:null,token_http_status:null,token_present:false};
  try{
    const r=await fetcher(BASE+'/api/config',{cache:'no-store',redirect:'error',signal:AbortSignal.timeout(15000)});result.config_http_status=r.status;
    const c=await r.json();
    if(!r.ok||c.voice_enabled!==true||c.requires_access_code!==true||typeof c.csrf!=='string'){result.failure_stage='config';return {result};}
    const cookie=r.headers.getSetCookie().map(x=>x.split(';')[0]).find(x=>/^recount_nonce=[A-Za-z0-9_-]{20,64}$/.test(x));
    if(!cookie){result.failure_stage='cookie';return {result};}
    const t=await fetcher(BASE+'/api/token',{method:'POST',redirect:'error',headers:{'Content-Type':'application/json',Origin:BASE,Cookie:cookie,'X-Recount-Token':c.csrf},body:JSON.stringify({consent:true,access_code:code}),signal:AbortSignal.timeout(15000)});result.token_http_status=t.status;
    const data=await t.json();
    result.token_present=t.ok&&typeof data.token==='string'&&data.token.length>=10&&data.token.length<=4096&&data.speech_model==='universal-3-5-pro';
    if(!result.token_present){result.failure_stage='token';if(SAFE.has(data.error))result.error=data.error;return {result};}
    return {result,token:data.token,speechModel:data.speech_model};
  }catch{result.failure_stage=result.token_http_status===null?'config_or_token_network':'token_response';return {result};}
}
export async function probe(url,Socket=WebSocket,{intervalMs=100,timeoutMs=20000}={}){
  const r={begin:false,termination:false,audio_bytes:0};
  await new Promise(resolve=>{
    let ws,interval,timer,done=false;
    const finish=()=>{if(done)return;done=true;clearTimeout(timer);clearInterval(interval);try{ws?.close();}catch{}resolve();};
    try{ws=new Socket(url);}catch{r.failure_stage='socket_create';finish();return;}
    timer=setTimeout(()=>{r.failure_stage='socket_timeout';finish();},timeoutMs);
    ws.addEventListener('error',()=>{r.failure_stage='socket_error';finish();});
    ws.addEventListener('close',e=>{r.close_code=e.code;if(!r.termination)r.failure_stage='socket_closed';finish();});
    ws.addEventListener('message',e=>{
      if(done)return;
      try{
        const m=JSON.parse(String(e.data));
        if(m.type==='Begin'&&!r.begin){
          r.begin=true;let frames=0;
          interval=setInterval(()=>{
            try{if(ws.readyState!==Socket.OPEN)throw Error();
              if(frames++<5){ws.send(new Uint8Array(3200));r.audio_bytes+=3200;}
              else{clearInterval(interval);ws.send(JSON.stringify({type:'Terminate'}));}
            }catch{r.failure_stage='socket_send';finish();}
          },intervalMs);
        }else if(m.type==='Termination'){r.termination=true;finish();}
        else if(m.type==='Error'){r.failure_stage='provider_error';if(Number.isInteger(m.error_code))r.provider_error_code=m.error_code;finish();}
      }catch{r.failure_stage='invalid_event';finish();}
    });
  });
  r.status=r.begin&&r.termination&&r.audio_bytes===16000&&!r.failure_stage?'passed':'failed';return r;
}
export async function verify({code,root=fileURLToPath(new URL('../web/',import.meta.url)),fetcher=fetch,Socket=WebSocket,probeOptions}={}){
  const r={status:'failed',site:BASE,source_commit:process.env.GITHUB_SHA??null,checked_at:new Date().toISOString(),human_audio_cases:0,physical_microphone_tested:false,scope:'Production authorization, served source, and real provider transport with generated silence. Not human speech validation.'};
  if(typeof code!=='string'||code.length<8||code.length>128){r.failure_stage='missing_judge_secret';return r;}
  const names=['index.html','app.mjs','core.mjs','voice-runtime.mjs','capture-gate.mjs','voice-audit.mjs','startup-errors.mjs','streaming-request.mjs','audio-worklet.js','audio-readback.mjs','readback.mjs','speaker-check.mjs','style.css','voice/v1/manifest.json'];
  r.assets=[];
  for(const name of names){
    try{const res=await fetcher(BASE+(name==='index.html'?'/':'/'+name),{cache:'no-store',redirect:'error',signal:AbortSignal.timeout(15000)});const data=Buffer.from(await res.arrayBuffer());r.assets.push({path:name,matches:res.ok&&data.equals(fs.readFileSync(path.join(root,name))),sha256:createHash('sha256').update(data).digest('hex')});}
    catch{r.assets.push({path:name,matches:false});}
  }
  if(r.assets.some(x=>!x.matches)){r.failure_stage='served_source_mismatch';return r;}
  const invalid=code==='synthetic-invalid-control'?'synthetic-other-control':'synthetic-invalid-control';
  r.rejection_control=(await authorize(invalid,fetcher)).result;
  if(r.rejection_control.token_http_status!==403||r.rejection_control.error!=='Invalid judge access code.'){r.failure_stage='authorization_rejection_control';return r;}
  const auth=await authorize(code,fetcher);r.authorization=auth.result;
  if(!auth.result.token_present){r.failure_stage='production_authorization';return r;}
  r.provider=await probe(streamingURL({token:auth.token,sampleRate:16000,speechModel:auth.speechModel}),Socket,probeOptions);
  if(r.provider.status!=='passed'){r.failure_stage='provider_transport';return r;}
  r.status='passed';return r;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const report=await verify({code:process.env.RECOUNT_DEMO_PASS});
  const output=process.env.RECOUNT_RECEIPT??'Recount-Production-Receipt.json';
  fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({status:report.status,failure_stage:report.failure_stage??null,receipt:output}));
  if(report.status!=='passed')process.exitCode=1;
}
