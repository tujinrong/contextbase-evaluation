from pathlib import Path
import hashlib
base=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01\delivery')
old=base/'build_xlsx_v2_62_r02.mjs';new=base/'build_xlsx_v2_62_r03.mjs'
raw=old.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='b73991d39d017002512672838f4544309233629cd2c26dede6b22c80d6668b6d'
assert not new.exists()
s=raw.decode('utf-8').replace('\r\n','\n')
s=s.replace("import crypto from 'node:crypto';","import crypto from 'node:crypto';\nimport { execFileSync } from 'node:child_process';")
start=s.index('const modelPath=option(');stop=s.index('const literal=value')
setup=r'''// Guards cover this actor's explicit FS calls; package/runtime FS boundaries are unchanged.
const BUNDLED_NODE=String.raw`C:\Users\tujin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe`;
const BUNDLED_PYTHON=String.raw`C:\Users\tujin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`;
const OWN_TMP=String.raw`D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01`;
const HELPER=path.join(OWN_TMP,'delivery','fs_preflight_v2_62_r02.py');
const HELPER_SHA='4c03b060269ee36dbbb1b8368fbb6cde9a95a6f7e91849e376c40919b61c567c';
if(path.resolve(process.execPath)!==path.resolve(BUNDLED_NODE))throw new Error('Bundled Node executable required');
const BOOTSTRAP_PY=String.raw`import os,sys,stat,hashlib
from pathlib import Path
expected=Path(r"D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01\delivery\fs_preflight_v2_62_r02.py")
p=Path(os.path.abspath(sys.argv[1]))
if p!=expected or p.resolve(strict=False)!=p:raise ValueError("HOLD: bootstrap helper path")
for node in (p,*p.parents):
 try:st=node.lstat()
 except FileNotFoundError:continue
 if stat.S_ISLNK(st.st_mode) or getattr(st,"st_file_attributes",0)&0x400:raise ValueError("HOLD: linked bootstrap helper")
st=p.lstat()
if not stat.S_ISREG(st.st_mode) or st.st_size>262144:raise ValueError("HOLD: bootstrap helper metadata")
raw=p.read_bytes()
if hashlib.sha256(raw).hexdigest()!=sys.argv[2]:raise ValueError("HOLD: bootstrap helper SHA")
for node in (p,*p.parents):
 st=node.lstat()
 if stat.S_ISLNK(st.st_mode) or getattr(st,"st_file_attributes",0)&0x400:raise ValueError("HOLD: bootstrap helper changed path")
if p.resolve(strict=False)!=p:raise ValueError("HOLD: bootstrap helper changed resolution")
sys.argv=[str(p)]
exec(compile(raw,str(p),"exec"),{"__name__":"__main__","__file__":str(p),"__package__":None})
`;
const guardEnv={...process.env,PYTHONDONTWRITEBYTECODE:'1'};delete guardEnv.PYTHONPATH;delete guardEnv.PYTHONHOME;
const fsChecks=[];const ownedOutputHashes=new Map();let bindingDescriptor=null;
const preflight=request=>{
  const raw=execFileSync(BUNDLED_PYTHON,['-I','-B','-c',BOOTSTRAP_PY,HELPER,HELPER_SHA],
    {input:JSON.stringify({schema:'fs-preflight-v2-62/1',...request}),encoding:'utf8',env:guardEnv,cwd:OWN_TMP,timeout:30000,maxBuffer:1048576,windowsHide:true});
  const result=JSON.parse(raw);
  if(result.status!=='METADATA_AND_PINS_CHECKED'||result.raceFreeGuarantee!==false)throw new Error('Invalid FS preflight response');
  fsChecks.push(result);return result;
};
const canonicalRelative=value=>{
  if(typeof value!=='string'||!value||value.includes('..')||value.includes('\\')||value.includes(':')||/[\x00-\x1f\x7f]/.test(value)||path.isAbsolute(value)||value.split('/').some(part=>!part||part==='.')||!value.endsWith('.md'))throw new Error('Invalid canonical relative path');
  return value;
};
const rawModelPath=option('--model');const outputRoot=option('--output-root');const modelSha=option('--model-sha256');
if(!rawModelPath||!outputRoot||!modelSha||!argv.includes('--authoring-marker-completed'))throw new Error('Supply pinned --model/--model-sha256, fresh --output-root and acknowledged completed author marker.');
const modelPath=path.resolve(rawModelPath);const destination=path.resolve(outputRoot);
const readPinned=async(file,expectedSha,role)=>{
  file=path.resolve(file);
  const request={path:file,operation:'read',role,expectedSha256:expectedSha};
  if(!['model','binding'].includes(role))request.binding=bindingDescriptor;
  preflight(request);const bytes=await fs.readFile(file);
  if(hash(bytes)!==expectedSha.toLowerCase())throw new Error('Pinned file changed during read');
  preflight(request);return bytes;
};
const outputRequest=(file,operation,extra={})=>({path:path.resolve(file),role:'output',operation,outputRoot:destination,...extra});
const mkdirOutput=async(directory,fresh=false)=>{
  preflight(outputRequest(directory,'mkdir',{fresh}));await fs.mkdir(directory,{recursive:true});
  preflight(outputRequest(directory,'mkdir'));
};
const writeOutput=async(file,bytes)=>{
  file=path.resolve(file);const previous=ownedOutputHashes.get(file);
  preflight(outputRequest(file,previous?'write-owned':'write-fresh',previous?{ownedOutput:true,expectedSha256:previous}:{}));
  await fs.writeFile(file,bytes,{flag:previous?'w':'wx'});
  const sha=hash(bytes);preflight(outputRequest(file,'post-write',{ownedOutput:true,expectedSha256:sha}));ownedOutputHashes.set(file,sha);
};
const saveXlsxOutput=async(xlsx,file)=>{
  file=path.resolve(file);preflight(outputRequest(file,'save-fresh'));await xlsx.save(file);
  const result=preflight(outputRequest(file,'post-write',{ownedOutput:true}));ownedOutputHashes.set(file,result.sha256);
};
const readOwnedOutput=async(file)=>{
  file=path.resolve(file);const sha=ownedOutputHashes.get(file);if(!sha)throw new Error('Output not owned by this FS actor');
  const request=outputRequest(file,'read',{ownedOutput:true,expectedSha256:sha});preflight(request);
  const bytes=await fs.readFile(file);if(hash(bytes)!==sha)throw new Error('Owned output changed during read');preflight(request);return bytes;
};
const modelRaw=await readPinned(modelPath,modelSha,'model');const model=JSON.parse(modelRaw.toString('utf8'));
if(model.formatProfile?.id!=='v2-62-preserved-reference'||model.formatProfile.gridColumns!==62||model.formatProfile.coverPrintArea!=='O6:AU36'||model.formatProfile.itemListColumns!==10)throw new Error('V2-62 profile must match the preserved-reference interpretation');
if(model.schema!=='reverse-agent-delivery-model/1'||model.businessContentAuthored!==false)throw new Error('Invalid mechanical model');
const bindingRaw=await readPinned(model.binding,model.bindingSha256,'binding');const binding=JSON.parse(bindingRaw.toString('utf8'));
bindingDescriptor={path:path.resolve(model.binding),sha256:model.bindingSha256};
for(const origin of [binding.permittedMarkdownRoot,binding.permittedRenderRoot,modelPath,model.binding]){
  const resolved=path.resolve(origin);const a=path.relative(resolved,destination);const b=path.relative(destination,resolved);
  if(!a||(!a.startsWith('..')&&!path.isAbsolute(a))||(!b.startsWith('..')&&!path.isAbsolute(b)))throw new Error('Output must be disjoint from pinned inputs/model');
}
const provenance={schema:'reverse-agent-xlsx-delivery/1',modelSha256:hash(modelRaw),bindingSha256:model.bindingSha256,
  sourceSnapshotManifestSha256:model.sourceSnapshotManifestSha256,referenceMode:model.referenceMode,businessContentAuthored:false,applicationExecuted:false,
  formatInterpretation:'existing V2 reference preservation interpreted as V2-62',
  filesystemPreflight:{helperSha256:HELPER_SHA,bootstrap:'bundledPython-static-code-lstat-SHA-same-bytes-compile-exec',scope:'CALLER_FS_ACTOR_ONLY',raceFreeGuarantee:false,packageRuntimeFilesystemBoundaryChanged:false,checks:fsChecks},
  documents:[],status:'RUNNING',visualReview:'PENDING',authoringMarkerAcknowledged:true};
await mkdirOutput(destination,true);

'''
s=s[:start]+setup+s[stop:]
start=s.index('const boundInput=async(');stop=s.index('const splitRange=',start)
s=s[:start]+'''const boundInput=async(document)=>{
  await readPinned(document.markdown,document.markdownSha256,'markdown');
  await readPinned(path.join(document.renderDirectory,'render-pins.json'),document.renderPinsSha256,'render-pins');
  await readPinned(path.join(document.renderDirectory,'manifest.json'),document.renderManifestSha256,'render-manifest');
  for(const sheet of document.sheets)for(const image of sheet.images)await readPinned(image.path,image.sha256,'image');
};
'''+s[stop:]
s=s.replace('const canonical=document.canonicalDocumentPath;','const canonical=canonicalRelative(document.canonicalDocumentPath);')
oldlines=[line for line in s.splitlines(keepends=True) if line.lstrip().startswith("if(canonical.includes(")]
assert len(oldlines)==1
s=s.replace(oldlines[0],'')
changes=[
("const qaDir=path.join(destination,'qa',stem);await fs.mkdir(qaDir,{recursive:true});","const qaDir=path.join(destination,'qa',stem);await mkdirOutput(qaDir);"),
("const bytes=await fs.readFile(image.path);if(hash(bytes)!==image.sha256)throw new Error('Changed PNG');","const bytes=await readPinned(image.path,image.sha256,'image');"),
("await fs.writeFile(path.join(qaDir,'inspection.ndjson'),inspect.ndjson);","await writeOutput(path.join(qaDir,'inspection.ndjson'),inspect.ndjson);"),
("await fs.writeFile(path.join(qaDir,filename),bytes);","await writeOutput(path.join(qaDir,filename),bytes);"),
("const xlsx=await SpreadsheetFile.exportXlsx(workbook);","await boundInput(document);\n    const xlsx=await SpreadsheetFile.exportXlsx(workbook);"),
("const filename=path.join(destination,'Excel',stem+'.xlsx');await fs.mkdir(path.dirname(filename),{recursive:true});await xlsx.save(filename);","const filename=path.join(destination,'Excel',stem+'.xlsx');await mkdirOutput(path.dirname(filename));await saveXlsxOutput(xlsx,filename);"),
("xlsx:filename,xlsxSha256:hash(await fs.readFile(filename))","xlsx:filename,xlsxSha256:hash(await readOwnedOutput(filename))"),
("await fs.writeFile(path.join(destination,'delivery-manifest.json'),JSON.stringify(provenance,null,2)+'\\n');","await writeOutput(path.join(destination,'delivery-manifest.json'),JSON.stringify(provenance,null,2)+'\\n');"),
("if(hash(await fs.readFile(model.binding))!==model.bindingSha256||hash(await fs.readFile(modelPath))!==hash(modelRaw))throw new Error('Binding/model changed during authoring');","await readPinned(model.binding,model.bindingSha256,'binding');await readPinned(modelPath,hash(modelRaw),'model');")]
for before,after in changes:
    count=s.count(before);assert count==(2 if 'delivery-manifest.json' in before else 1),(before,count)
    s=s.replace(before,after)
assert "range.format.borders={top:{style:'thin',color:light}}" in s
with new.open('x',encoding='utf-8',newline='') as f:f.write(s)
assert old.read_bytes()==raw
print(str(new));print(hashlib.sha256(new.read_bytes()).hexdigest())

