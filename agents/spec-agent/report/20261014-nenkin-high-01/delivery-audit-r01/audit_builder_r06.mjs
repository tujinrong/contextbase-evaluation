// Independent source/pure-function audit. Never execute the builder or import Artifact.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const D=String.raw`D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01\delivery`;
const O=String.raw`D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01`;
const source=path.join(D,'build_xlsx_v2_62_r06.mjs');
const old=path.join(D,'build_xlsx_v2_62_r02.mjs');
const hash=raw=>crypto.createHash('sha256').update(raw).digest('hex');
const raw=await fs.readFile(source);assert.equal(hash(raw),'33aa7166fbce79874576408ae682a471b52fbaa43269de1dcfe51f401dca0cfd');
const prior=await fs.readFile(old);assert.equal(hash(prior),'b73991d39d017002512672838f4544309233629cd2c26dede6b22c80d6668b6d');
const text=raw.toString('utf8').replaceAll('\r\n','\n');const donor=prior.toString('utf8').replaceAll('\r\n','\n');
const checks=[];
const check=(name,wanted,observed)=>{assert.deepEqual(observed,wanted,name);checks.push({name,pass:true});};
function segment(t,a,b){const start=t.indexOf(a);const end=t.indexOf(b,start);assert(start>=0&&end>start);return t.slice(start,end);}
const geometryStart='    for(const specification of document.sheets){';
const geometryEnd='    workbook.recalculate();';
const geometry=segment(text,geometryStart,geometryEnd);
const oldGeometry=segment(donor,geometryStart,geometryEnd);
const originalRead="const bytes=await fs.readFile(image.path);if(hash(bytes)!==image.sha256)throw new Error('Changed PNG');";
check('public Artifact geometry unchanged except guarded PNG read',oldGeometry.replace(originalRead,"const bytes=await readPinned(image.path,image.sha256,'image');"),geometry);
check('company band exactly top-thin setter retained',true,geometry.includes("range.format.borders={top:{style:'thin',color:light}}"));
check('format clearing and text number format retained',true,geometry.includes("region.clear({applyTo:'formats'})")&&geometry.includes("region.setNumberFormat('@')"));
check('all explicit Node FS calls limited to guarded wrappers',['mkdir','readFile','readFile','writeFile'],[...text.matchAll(/\bfs\.(\w+)\s*\(/g)].map(m=>m[1]).sort());
check('explicit XLSX save appears only guarded wrapper',1,[...text.matchAll(/\bxlsx\.save\(/g)].length);
for(const name of ['readPinned','mkdirOutput','writeOutput','saveXlsxOutput','readOwnedOutput']){
  const start=text.indexOf('const '+name+'=');const stop=text.indexOf('\n};',start)+4;
  const body=text.slice(start,stop);check(name+' wrapper preflight present',true,body.includes('preflight('));
}
check('fresh writes use exclusive wx flag',true,text.includes("flag:previous?'w':'wx'"));
check('binding/model root disjoint guard retained',true,text.includes('Output must be disjoint from pinned inputs/model'));
check('no static Artifact bare import',false,/^import .*@oai\/artifact-tool/m.test(text));
check('Artifact dynamic public fileURL import after marker argument guard',true,text.indexOf("await import(pathToFileURL(ARTIFACT_ENTRY).href)")>text.indexOf("argv.includes('--authoring-marker-completed')"));
check('explicit bundled entry and hash recorded',true,text.includes('node_modules\\\\@oai\\\\artifact-tool\\\\dist\\\\artifact_tool.mjs')&&text.includes('0900e6e29e518a03fa1a49008257ddf525b0557ad3c4a38be60bfa9085bb85d7'));
check('both isolated Python argv use utf8',2,[...text.matchAll(/\['-I','-B','-X','utf8','-c'/g)].length);
check('profile basis interpretation gate',true,text.includes("selectionBasis!=='INTERPRETATION_OF_REQUEST_TO_PRESERVE_EXISTING_V2_FORMAT'")&&text.includes('userExplicitlySpecified62!==false'));
const canonicalSource=segment(text,'const canonicalRelative=','const rawModelPath=');
const canonical=vm.runInNewContext(canonicalSource+'\ncanonicalRelative',{path});
for(const value of ['基本設計書/01_仕様.md','toy.md'])check('canonical valid '+value,value,canonical(value));
for(const value of ['a:stream.md','a\x00.md','a\x7f.md','../a.md','a\\b.md','a//b.md','/a.md']){
  let refused=false;try{canonical(value);}catch{refused=true;}check('canonical invalid '+JSON.stringify(value),true,refused);
}
const calls=[];const boundSource=segment(text,'const boundInput=','const splitRange=');
const bound=vm.runInNewContext(boundSource+'\nboundInput',{path,readPinned:async(file,sha,role)=>calls.push({file,sha,role})});
const document={markdown:'toy.md',markdownSha256:'1'.repeat(64),renderDirectory:'toy-render',renderPinsSha256:'2'.repeat(64),renderManifestSha256:'3'.repeat(64),sheets:[{images:[{path:'one.png',sha256:'4'.repeat(64)}]},{images:[{path:'two.png',sha256:'5'.repeat(64)}]}]};
await bound(document);check('boundInput rechecks every sheet PNG',['markdown','render-pins','render-manifest','image','image'],calls.map(c=>c.role));
check('boundInput PNG pins copied exactly',['4'.repeat(64),'5'.repeat(64)],calls.filter(c=>c.role==='image').map(c=>c.sha));
const exportAt=text.indexOf('const xlsx=await SpreadsheetFile.exportXlsx(workbook)');
check('all PNGs checked again immediately before export',true,text.lastIndexOf('await boundInput(document);',exportAt)>text.indexOf('workbook.recalculate();'));
check('all PNGs checked after export save',true,text.indexOf('await boundInput(document);',exportAt)>text.indexOf('await saveXlsxOutput',exportAt));
check('final model and binding pin reread',true,text.includes("await readPinned(model.binding,model.bindingSha256,'binding');await readPinned(modelPath,hash(modelRaw),'model')"));
check('source unchanged after audit',hash(raw),hash(await fs.readFile(source)));
const result={scope:'INDEPENDENT_SOURCE_AND_EXTRACTED_PURE_FUNCTIONS_ONLY',status:'PASS',candidate:{path:source,sha256:hash(raw)},donor:{path:old,sha256:hash(prior)},checks,count:checks.length,artifactImportExecuted:false,builderExecuted:false,authoringMarkerExecuted:0,actualXlsxCreated:0,productionBusinessReads:0,limits:['Source/pure tests do not qualify actual Artifact package import, export or native image appearance.','Filesystem gate is explicitly non-atomic; package-internal FS remains trusted bundled runtime scope.','--authoring-marker-completed is an acknowledgement; root must execute and bind the actual one-time marker after final plan count.']};
const out=path.join(O,'builder-r06-independent-code-audit.json');await fs.writeFile(out,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
process.stdout.write(JSON.stringify({path:out,sha256:hash(await fs.readFile(out)),checks:checks.length})+'\n');
