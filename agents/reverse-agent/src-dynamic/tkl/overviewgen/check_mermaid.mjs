import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
const modules = process.env.OVERVIEW_NODE_MODULES;
if (!modules) throw new Error('OVERVIEW_NODE_MODULES is required');
const require = createRequire(path.join(modules, 'package.json'));
const { JSDOM } = require('jsdom');
const dom = new JSDOM('<html><body></body></html>');
globalThis.window = dom.window;
globalThis.document = dom.window.document;
const { default: mermaid } = await import(pathToFileURL(path.join(modules, 'node_modules/mermaid/dist/mermaid.esm.mjs')));
mermaid.initialize({ startOnLoad: false, securityLevel: 'strict' });
const errors = [];
let checked = 0;
for (const name of fs.readdirSync('output').sort()) {
  if (!name.endsWith('.md')) continue;
  const text = fs.readFileSync(path.join('output', name), 'utf8');
  let index = 0;
  for (const match of text.matchAll(/```mermaid\r?\n([\s\S]*?)```/g)) {
    index++; checked++;
    try { await mermaid.parse(match[1]); }
    catch (err) { errors.push({ file: name, diagram: index, error: String(err) }); }
  }
}
fs.mkdirSync('report/overview', { recursive: true });
fs.writeFileSync('report/overview/mermaid-validation.json', JSON.stringify({ checked, errors, engine: 'mermaid@11.12.0', scope: 'syntax only; not visual layout review' }, null, 2) + '\n');
const file = 'report/overview/evaluation.json';
if (fs.existsSync(file)) {
  const result = JSON.parse(fs.readFileSync(file, 'utf8'));
  result.mermaid_syntax = errors.length ? 'failed' : 'passed';
  result.mermaid_syntax_checked = checked;
  fs.writeFileSync(file, JSON.stringify(result, null, 2) + '\n');
  const md = 'report/overview/独立評価.md';
  if (fs.existsSync(md)) fs.writeFileSync(md, fs.readFileSync(md, 'utf8').replace('| mermaid_syntax | not_yet_checked |', `| mermaid_syntax | ${errors.length ? 'failed' : 'passed'} (${checked} diagrams) |`));
}
console.log(JSON.stringify({ checked, errors }, null, 2));
if (errors.length) process.exitCode = 1;
