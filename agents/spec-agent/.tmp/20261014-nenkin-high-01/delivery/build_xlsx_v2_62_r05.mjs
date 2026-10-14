// Artifact Tool is the sole workbook author. No prose, formulas, or business rules.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const argv=process.argv.slice(2);
const option=name => {const index=argv.indexOf(name);return index<0?null:argv[index+1];};
// Guards cover this actor's explicit FS calls; package/runtime FS boundaries are unchanged.
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
  const raw=execFileSync(BUNDLED_PYTHON,['-I','-B','-X','utf8','-c',BOOTSTRAP_PY,HELPER,HELPER_SHA],
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
const ARTIFACT_ENTRY="C:\\Users\\tujin\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\node\\node_modules\\@oai\\artifact-tool\\dist\\artifact_tool.mjs";
const PACKAGE_BOOTSTRAP_PY="import os,sys,stat,hashlib,json\nfrom pathlib import Path\nexpected=[(Path(r\"C:\\Users\\tujin\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\node\\node_modules\\@oai\\artifact-tool\\dist\\artifact_tool.mjs\"),\"0900e6e29e518a03fa1a49008257ddf525b0557ad3c4a38be60bfa9085bb85d7\"),(Path(r\"C:\\Users\\tujin\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\node\\node_modules\\@oai\\artifact-tool\\package.json\"),\"4c6ba2c3f71d8d8b8b24c3aca3627b860de5a3d95da3824191d93fed7f447a86\")]\nchecked=[]\nfor p,sha in expected:\n if p.resolve(strict=False)!=p:raise ValueError(\"HOLD: bundled package entry resolution\")\n for node in (p,*p.parents):\n  st=node.lstat()\n  if stat.S_ISLNK(st.st_mode) or getattr(st,\"st_file_attributes\",0)&0x400:raise ValueError(\"HOLD: linked bundled package entry\")\n st=p.lstat()\n if not stat.S_ISREG(st.st_mode) or st.st_size>32000000:raise ValueError(\"HOLD: bundled package metadata\")\n if hashlib.sha256(p.read_bytes()).hexdigest()!=sha:raise ValueError(\"HOLD: bundled public package SHA\")\n checked.append({\"path\":str(p),\"sha256\":sha})\nprint(json.dumps({\"checked\":checked,\"importExecuted\":False,\"raceFreeGuarantee\":False}))\n";
const packageEntryPin=JSON.parse(execFileSync(BUNDLED_PYTHON,['-I','-B','-X','utf8','-c',PACKAGE_BOOTSTRAP_PY],{encoding:'utf8',env:guardEnv,cwd:OWN_TMP,timeout:30000,maxBuffer:1048576,windowsHide:true}));
const { Workbook, SpreadsheetFile }=await import(pathToFileURL(ARTIFACT_ENTRY).href);

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
  filesystemPreflight:{helperSha256:HELPER_SHA,bootstrap:'bundledPython-static-code-lstat-SHA-same-bytes-compile-exec',scope:'CALLER_FS_ACTOR_ONLY',raceFreeGuarantee:false,packageRuntimeFilesystemBoundaryChanged:false,publicBundledPackageEntry:packageEntryPin,checks:fsChecks},
  documents:[],status:'RUNNING',visualReview:'PENDING',authoringMarkerAcknowledged:true};
await mkdirOutput(destination,true);

const literal=value=>value.startsWith('=')||value.startsWith("'")?"'"+value:value;
const black='#000000';const light='#808080';
const outside=(range,style='thin',color=light)=>{range.format.borders={preset:'outside',style,color};};
const boundInput=async(document)=>{
  await readPinned(document.markdown,document.markdownSha256,'markdown');
  await readPinned(path.join(document.renderDirectory,'render-pins.json'),document.renderPinsSha256,'render-pins');
  await readPinned(path.join(document.renderDirectory,'manifest.json'),document.renderManifestSha256,'render-manifest');
  for(const sheet of document.sheets)for(const image of sheet.images)await readPinned(image.path,image.sha256,'image');
};
const splitRange=ref=>{const match=/^([A-Z]+)(\d+):([A-Z]+)(\d+)$/.exec(ref);if(!match)throw new Error('Rectangular operation required');return match;};
const col=number=>{let result='';while(number){const remainder=(number-1)%26;number=Math.floor((number-1)/26);result=String.fromCharCode(65+remainder)+result;}return result;};

try{
  for(const document of model.documents){
    await boundInput(document); console.log(JSON.stringify({stage:"bound-document", documentId:document.documentId, utc:new Date().toISOString()}));
    const canonical=canonicalRelative(document.canonicalDocumentPath);
    const stem=canonical.slice(0,-3);const workbook=Workbook.create();
    const qaDir=path.join(destination,'qa',stem);await mkdirOutput(qaDir);
    const written=[];const previews=[];
    for(const specification of document.sheets){
      const sheet=workbook.worksheets.add(specification.name);
      sheet.showGridLines=false;
      const region=sheet.getRange(`A1:${col(specification.columns)}${specification.lastRow}`);
      // preset:none serializes style="none" edges which this native renderer
      // paints black. A fresh, cleared format has neutral borderId=0 instead.
      region.clear({applyTo:'formats'});
      region.format.font={name:'Meiryo',size:10,color:'#404040'};
      region.format.verticalAlignment='top';region.format.wrapText=true;region.setNumberFormat('@');
      if(specification.role==='normal'&&(specification.columns!==62||specification.gridColumnWidth!==3))throw new Error('V2-62 normal sheet mismatch');
      region.format.columnWidth=specification.role==='normal'?specification.gridColumnWidth:specification.role==='cover'?3:18;
      if(specification.columnWidths){
        if(specification.columnWidths.length!==specification.columns)throw new Error('Column geometry mismatch');
        for(let index=0;index<specification.columnWidths.length;index++)sheet.getRange(`${col(index+1)}1:${col(index+1)}${specification.lastRow}`).format.columnWidth=specification.columnWidths[index];
      }
      for(const [row,height] of Object.entries(specification.rowHeights))sheet.getRange(`A${row}:${col(specification.columns)}${row}`).format.rowHeight=height;
      for(const operation of specification.operations){
        const [_,left,top,right,bottom]=splitRange(operation.range);
        const range=sheet.getRange(operation.range);
        if(left!==right||top!==bottom)range.merge();
        sheet.getRange(left+top).values=[[literal(operation.value)]];
        if(['title','heading','table-header','cover-title'].includes(operation.style))range.format.font={name:'Meiryo',size:operation.style==='cover-title'?16:operation.style==='title'?14:10,bold:true,color:'#404040'};
        if(operation.style==='code')range.format.font={name:'Consolas',size:10,color:'#404040'};
        if(operation.style==='table-header'){range.format.fill='#D9D9D9';range.format.horizontalAlignment='center';outside(range);}
        else if(operation.style==='table-cell'||operation.style==='cover-cell')outside(range);
        else if(operation.style==='cover-title')outside(range,'double','#595959');
        else if(operation.style==='cover-company-band')range.format.borders={top:{style:'thin',color:light}};
        written.push({sheet:specification.name,cell:left+top,value:operation.value,range:operation.range,sourceLines:operation.sourceLines});
      }
      for(const tableSpec of specification.tables){
        if(!tableSpec.grid){
          const table=sheet.tables.add(tableSpec.range,true,`Rows${provenance.documents.length}_${document.sheets.indexOf(specification)}_${specification.tables.indexOf(tableSpec)}`);
          table.showFilterButton=true;
          sheet.freezePanes.freezeRows(tableSpec.headerRow);
        }
        if(specification.role==='list'||specification.role==='table'){
          const header=sheet.getRange(`A${tableSpec.headerRow}:${col(tableSpec.header.length)}${tableSpec.headerRow}`);
          header.format.borders={top:{style:'medium',color:black},left:{style:'medium',color:black},right:{style:'medium',color:black},bottom:{style:'thin',color:light},insideVertical:{style:'thin',color:light}};
        }
      }
      if(specification.role==='normal'){
        outside(region,'medium',black);
        sheet.getRange(`A1:${col(specification.columns)}1`).format.borders={bottom:{style:'double',color:'#595959'},top:{style:'medium',color:black},left:{style:'medium',color:black},right:{style:'medium',color:black}};
      }
      for(const image of specification.images){
        const bytes=await readPinned(image.path,image.sha256,'image');
        sheet.images.add({dataUrl:'data:image/png;base64,'+bytes.toString('base64'),anchor:{from:{row:image.row,col:image.col},extent:{widthPx:image.displayWidth,heightPx:image.displayHeight}}});
      }
    }
    workbook.recalculate();
    const inspect=await workbook.inspect({kind:'sheet',include:'id,name',maxChars:6000});
    await writeOutput(path.join(qaDir,'inspection.ndjson'),inspect.ndjson);
    for(const specification of document.sheets){
      for(let index=0;index<specification.previewTiles.length;index++){
        const tile=specification.previewTiles[index]; console.log(JSON.stringify({stage:"native-tile", documentId:document.documentId, sheet:specification.name, index, range:tile.range, utc:new Date().toISOString()}));
        const preview=await workbook.render({sheetName:specification.name,range:tile.range,scale:1,format:'png'});
        const bytes=new Uint8Array(await preview.arrayBuffer());
        const filename=`sheet-${document.sheets.indexOf(specification)+1}-${String(index+1).padStart(3,'0')}.png`;
        await writeOutput(path.join(qaDir,filename),bytes);previews.push({sheet:specification.name,range:tile.range,path:path.join(qaDir,filename),sha256:hash(bytes)});
      }
    }
    await boundInput(document);
    const xlsx=await SpreadsheetFile.exportXlsx(workbook);
    const filename=path.join(destination,'Excel',stem+'.xlsx');await mkdirOutput(path.dirname(filename));await saveXlsxOutput(xlsx,filename);
    await boundInput(document); console.log(JSON.stringify({stage:"bound-document", documentId:document.documentId, utc:new Date().toISOString()}));
    provenance.documents.push({documentId:document.documentId,canonicalDocumentPath:canonical,markdownSha256:document.markdownSha256,
      xlsx:filename,xlsxSha256:hash(await readOwnedOutput(filename)),writtenCells:written,previews,
      requestedPrintAreas:document.sheets.map(s=>({sheet:s.name,area:s.printArea})),
      printSettings:'REQUIRES_PUBLIC_API_PROBE_OR_VERIFIED_OOXML_METADATA_CONNECTION',
      independentCellVerification:'PENDING',visualReview:'PENDING',semanticApproval:'NOT_ASSESSED'});
    await writeOutput(path.join(destination,'delivery-manifest.json'),JSON.stringify(provenance,null,2)+'\n');
  }
  provenance.status='EXPORTED_VERIFICATION_PENDING';
  await readPinned(model.binding,model.bindingSha256,'binding');await readPinned(modelPath,hash(modelRaw),'model');
}catch(error){provenance.status='FAILED';provenance.error=String(error);provenance.published=false;throw error;}
finally{await writeOutput(path.join(destination,'delivery-manifest.json'),JSON.stringify(provenance,null,2)+'\n');}
console.log(JSON.stringify({documents:provenance.documents.length,status:provenance.status,visualReview:'PENDING'}));
