import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {HOST_INJECTIONS,normalizedHostedHTML} from '../delivery/hosted-html.mjs';
const source=fs.readFileSync(new URL('../web/index.html',import.meta.url),'utf8');
const inject=()=>source.replace('<meta charset="utf-8">','<meta charset="utf-8">'+HOST_INJECTIONS[0])+HOST_INJECTIONS[1];
test('untouched HTML remains byte-identical',()=>assert.deepEqual(normalizedHostedHTML(source),{html:source,removed:[]}));
test('only exact observed Netlify metadata and HUD additions normalize',()=>{const r=normalizedHostedHTML(inject());assert.equal(r.html,source);assert.equal(r.removed.length,2);});
test('application modifications remain detectable',()=>assert.notEqual(normalizedHostedHTML(inject().replace('Counting desk','Modified desk')).html,source));
test('modified host script is not silently waived',()=>assert.notEqual(normalizedHostedHTML(inject().replace('/.netlify/scripts/hud?variant=public','https://example.invalid/script.js')).html,source));
test('duplicate host markup is not silently waived',()=>assert.notEqual(normalizedHostedHTML(inject()+HOST_INJECTIONS[1]).html,source));
