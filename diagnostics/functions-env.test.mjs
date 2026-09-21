import test from 'node:test';
import assert from 'node:assert/strict';
import configHandler from '../netlify/functions/config.mts';
import tokenHandler from '../netlify/functions/token.mts';
const values={RECOUNT_SIGNING_SECRET:'synthetic-signing-secret-long-enough',RECOUNT_DEMO_PASS:'synthetic-judge-code',ASSEMBLYAI_API_KEY:'synthetic-provider-key-long-enough',RECOUNT_ALLOWED_ORIGIN:'https://recount-voice.netlify.app'};
async function setup(mode,fn){const old=Object.fromEntries(Object.keys(values).map(k=>[k,process.env[k]])),api=globalThis.Netlify,fetcher=globalThis.fetch;try{for(const k of Object.keys(values))delete process.env[k];delete globalThis.Netlify;if(mode==='process')Object.assign(process.env,values);if(mode==='accessor')globalThis.Netlify={env:{get:k=>values[k]}};await fn();}finally{for(const k of Object.keys(values)){if(old[k]===undefined)delete process.env[k];else process.env[k]=old[k];}if(api===undefined)delete globalThis.Netlify;else globalThis.Netlify=api;globalThis.fetch=fetcher;}}
for(const mode of ['process','accessor'])test(mode+' runtime performs real config/cookie/CSRF/code validation',async()=>setup(mode,async()=>{
 const response=await configHandler(new Request(values.RECOUNT_ALLOWED_ORIGIN+'/api/config'));assert.equal(response.status,200);const data=await response.json();const cookie=response.headers.get('set-cookie').split(';')[0];assert.equal(data.voice_enabled,true);
 let calls=0;globalThis.fetch=async(url,options)=>{calls++;assert.equal(options.headers.Authorization,values.ASSEMBLYAI_API_KEY);return Response.json({token:'synthetic-temporary-provider-token'});};
 const request=code=>new Request(values.RECOUNT_ALLOWED_ORIGIN+'/api/token',{method:'POST',headers:{'content-type':'application/json',origin:values.RECOUNT_ALLOWED_ORIGIN,cookie,'x-recount-token':data.csrf},body:JSON.stringify({consent:true,access_code:code})});
 const invalid=await tokenHandler(request('synthetic-incorrect-code'));assert.equal(invalid.status,403);assert.equal(calls,0);
 const valid=await tokenHandler(request(values.RECOUNT_DEMO_PASS));assert.equal(valid.status,200);assert.equal(calls,1);const payload=await valid.json();assert.equal(payload.token,'synthetic-temporary-provider-token');assert.equal(payload.speech_model,'universal-3-5-pro');
 const text=JSON.stringify(data)+JSON.stringify(payload);for(const key of ['RECOUNT_DEMO_PASS','RECOUNT_SIGNING_SECRET','ASSEMBLYAI_API_KEY'])assert.ok(!text.includes(values[key]));
}));
test('missing configuration still refuses safely',async()=>setup('missing',async()=>{assert.equal((await configHandler(new Request(values.RECOUNT_ALLOWED_ORIGIN+'/api/config'))).status,503);}));
