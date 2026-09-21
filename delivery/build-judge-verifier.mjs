// Build-only credential handling. This emits a server verifier, never a raw code.
import fs from 'node:fs';
import {createHash} from 'node:crypto';
const code=process.env.RECOUNT_DEMO_PASS;
if(typeof code!=='string'||!/^recount-[A-Za-z0-9_-]{20,64}$/.test(code))throw Error('A generated high-entropy judge code is required in RECOUNT_DEMO_PASS');
const digest=createHash('sha256').update('Recount judge code v1\0').update(code).digest('hex');
const target=new URL('../netlify/lib/judge-verifier.mts',import.meta.url);
fs.writeFileSync(target,'// Deployment-generated one-way verifier; no plaintext credential.\nexport const JUDGE_CODE_SHA256 = '+JSON.stringify(digest)+';\n',{mode:0o600});
console.log('Server-only judge verifier generated. The judge code is unchanged.');
