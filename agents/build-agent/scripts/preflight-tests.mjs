// Test stop/overwrite/input-scope behavior in a disposable fixture under this agent.
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';import {spawnSync} from 'node:child_process';
const here=path.dirname(fileURLToPath(import.meta.url));
const base=path.resolve(here,'.test-work');fs.mkdirSync(base,{recursive:true});
const fixture=fs.mkdtempSync(path.join(base,'preflight-'));const root=path.join(fixture,'repo');let passed=0;
const files=['AGENTS.md','agents/README.md','agents/spec-agent/AGENT.md','agents/build-agent/AGENT.md','agents/reverse-agent/AGENT.md','docs/リポジトリ構成.md','docs/開発規約.md','docs/仕様書作成ルール.md','docs/評価規約.md','docs/MD構造・Excel変換規約.md','docs/テーブル仕様書記述規約.md','test-project1/README.md','test-project1/プロジェクト情報.md','test-project1/docs/開発規約.md'];
function write(file,text) {const target=path.join(root,file);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,text);}
function document(file,id) {return `<!-- spec-meta: ${JSON.stringify({schema:'spec-md/1.0',documentId:id,version:'1.0',path:file,sheets:[{heading:'定義',kind:'LIST',sheet:'01_定義',key:['ID']}]})} -->\n# fixture\n\n## 定義\n\n| ID | 内容 |\n| --- | --- |\n| A | fixture |\n`;}
function run(id,expected) {const result=spawnSync(process.execPath,[path.join(root,'agents/build-agent/scripts/preflight.mjs'),'--project','test-project1','--run-id',id],{encoding:'utf8'});if(result.status!==expected) throw new Error(`Expected ${expected}; got ${result.status}: ${result.stderr}${result.stdout}`);passed++;return JSON.parse(fs.readFileSync(path.join(root,`test-project1/report/${id}-structure.json`),'utf8'));}
try {
 files.forEach((file,i)=>write(file,document(file,file==='agents/build-agent/AGENT.md'?'AG-BUILD':`FIX-${i}`)));
 fs.mkdirSync(path.join(root,'test-project1/docs/開発規約'),{recursive:true});
 fs.mkdirSync(path.join(root,'test-project1/spec'),{recursive:true});
 write('agents/build-agent/scripts/preflight.mjs',fs.readFileSync(path.join(here,'preflight.mjs'),'utf8'));
 write('test-project1/spec-eval/poison.md','This deliberately has no valid metadata. It must never be an input.');
 run('positive',0);
 const inputs=JSON.parse(fs.readFileSync(path.join(root,'test-project1/report/positive-inputs.json'),'utf8'));
 if(inputs.files.some(file=>file.file.includes('spec-eval'))) throw new Error('Evaluation leaked into inputs');passed++;
 const original=fs.readFileSync(path.join(root,'test-project1/report/positive-inputs.json'));
 const duplicate=spawnSync(process.execPath,[path.join(root,'agents/build-agent/scripts/preflight.mjs'),'--project','test-project1','--run-id','positive'],{encoding:'utf8'});
 if(duplicate.status!==1||!original.equals(fs.readFileSync(path.join(root,'test-project1/report/positive-inputs.json')))) throw new Error('Existing report overwritten');passed++;
 const file='test-project1/spec/unit.md';const valid=document(file,'UNIT');
 write(file,valid+'| A | duplicate |\n');if(!run('duplicate-key',2).findings.some(f=>f.code==='TABLE_KEY')) throw new Error('Duplicate key not reported');passed++;
 write(file,valid.replace('## 定義','## 別の章'));if(!run('chapter',2).findings.some(f=>f.code==='CHAPTER_MAPPING')) throw new Error('Chapter mismatch not reported');passed++;
 write(file,valid.replace('| A | fixture |','| A | [missing](missing.md) |'));if(!run('missing-reference',2).findings.some(f=>f.code==='LINK_MISSING')) throw new Error('Missing reference not reported');passed++;
 console.log(`PASS ${passed} preflight assertions: structural stop, input exclusion, fresh reports; fixture only.`);
} finally {
 const resolved=path.resolve(fixture);if(!resolved.startsWith(base+path.sep)) throw new Error('Cleanup target outside agent fixture area');
 fs.rmSync(resolved,{recursive:true,force:true});
}
