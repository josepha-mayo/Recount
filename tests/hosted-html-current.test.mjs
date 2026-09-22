import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {HOST_INJECTIONS, normalizedHostedHTML} from '../delivery/hosted-html.mjs';
const source=fs.readFileSync(new URL('../web/index.html',import.meta.url),'utf8');
const comment=HOST_INJECTIONS[2];
const injected=source.replace('<meta charset="utf-8">','<meta charset="utf-8">'+comment)+HOST_INJECTIONS[1];
test('September 22 exact site-specific hosting comment normalizes',()=>{
 const r=normalizedHostedHTML(injected);assert.equal(r.html,source);assert.deepEqual(r.removed,['netlify-public-hud','netlify-hosting-comment-20260922']);
});
test('altered host comment is not ignored',()=>assert.notEqual(normalizedHostedHTML(injected.replace('utm_campaign=loops','utm_campaign=unexpected')).html,source));
test('extra occurrence of a host comment is not ignored',()=>assert.notEqual(normalizedHostedHTML(injected+comment).html,source));
test('unrelated comment and script stay detectable',()=>assert.notEqual(normalizedHostedHTML(injected+'<!-- unrelated --><script>alert(1)</script>').html,source));
test('changed application copy remains detectable with new comment',()=>assert.notEqual(normalizedHostedHTML(injected.replace('Confirmed stock','Altered stock')).html,source));
