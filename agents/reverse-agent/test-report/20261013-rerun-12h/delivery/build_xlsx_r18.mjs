// Artifact Tool is the sole workbook author. No prose, formulas, or business rules.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const argv=process.argv.slice(2);
const option=name => {const index=argv.indexOf(name);return index<0?null:argv[index+1];};
const modelPath=option('--model');const outputRoot=option('--output-root');
if(!modelPath||!outputRoot||!argv.includes('--authoring-marker-completed')) {
  throw new Error('Supply --model, --output-root and --authoring-marker-completed after the required successful skill marker.');
}
const modelRaw=await fs.readFile(modelPath);const model=JSON.parse(modelRaw.toString('utf8'));
if(model.schema!=='reverse-agent-delivery-model/1'||model.businessContentAuthored!==false)throw new Error('Invalid mechanical model');
const destination=path.resolve(outputRoot);
const bindingRaw=await fs.readFile(model.binding);
if(hash(bindingRaw)!==model.bindingSha256)throw new Error('Changed input binding');
const binding=JSON.parse(bindingRaw.toString('utf8'));
for(const origin of [binding.permittedMarkdownRoot,binding.permittedRenderRoot,modelPath,model.binding]){
  const resolved=path.resolve(origin);
  const a=path.relative(resolved,destination);const b=path.relative(destination,resolved);
  if(!a||(!a.startsWith('..')&&!path.isAbsolute(a))||(!b.startsWith('..')&&!path.isAbsolute(b)))throw new Error('Output must be disjoint from pinned inputs/model');
}
for(let ancestor=destination;;ancestor=path.dirname(ancestor)){
  try {if((await fs.lstat(ancestor)).isSymbolicLink())throw new Error('Linked output paths forbidden');}catch(error){if(error.code!=='ENOENT')throw error;}
  if(path.dirname(ancestor)===ancestor)break;
}
try {await fs.stat(destination);throw new Error('Fresh XLSX delivery root required');} catch(error){if(error.code!=='ENOENT')throw error;}
const provenance={schema:'reverse-agent-xlsx-delivery/1',modelSha256:hash(modelRaw),bindingSha256:model.bindingSha256,
  sourceSnapshotManifestSha256:model.sourceSnapshotManifestSha256,referenceMode:model.referenceMode,businessContentAuthored:false,applicationExecuted:false,
  documents:[],status:'RUNNING',visualReview:'PENDING',authoringMarkerAcknowledged:true};
await fs.mkdir(destination,{recursive:true});

const literal=value=>value.startsWith('=')||value.startsWith("'")?"'"+value:value;
const black='#000000';const light='#808080';
const outside=(range,style='thin',color=light)=>{range.format.borders={preset:'outside',style,color};};
const boundInput=async(document)=>{
  if(hash(await fs.readFile(document.markdown))!==document.markdownSha256)throw new Error('Changed Markdown');
  if(hash(await fs.readFile(path.join(document.renderDirectory,'render-pins.json')))!==document.renderPinsSha256)throw new Error('Changed render-pins');
  if(hash(await fs.readFile(path.join(document.renderDirectory,'manifest.json')))!==document.renderManifestSha256)throw new Error('Changed render manifest');
};
const splitRange=ref=>{const match=/^([A-Z]+)(\d+):([A-Z]+)(\d+)$/.exec(ref);if(!match)throw new Error('Rectangular operation required');return match;};
const col=number=>{let result='';while(number){const remainder=(number-1)%26;number=Math.floor((number-1)/26);result=String.fromCharCode(65+remainder)+result;}return result;};

try{
  for(const document of model.documents){
    await boundInput(document); console.log(JSON.stringify({stage:"bound-document", documentId:document.documentId, utc:new Date().toISOString()}));
    const canonical=document.canonicalDocumentPath;
    if(canonical.includes('..')||canonical.includes('\\')||path.isAbsolute(canonical)||!canonical.endsWith('.md'))throw new Error('Invalid canonical path');
    const stem=canonical.slice(0,-3);const workbook=Workbook.create();
    const qaDir=path.join(destination,'qa',stem);await fs.mkdir(qaDir,{recursive:true});
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
      region.format.columnWidth=specification.columns===120?2:specification.role==='cover'?3:18;
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
        const bytes=await fs.readFile(image.path);if(hash(bytes)!==image.sha256)throw new Error('Changed PNG');
        sheet.images.add({dataUrl:'data:image/png;base64,'+bytes.toString('base64'),anchor:{from:{row:image.row,col:image.col},extent:{widthPx:image.displayWidth,heightPx:image.displayHeight}}});
      }
    }
    workbook.recalculate();
    const inspect=await workbook.inspect({kind:'sheet',include:'id,name',maxChars:6000});
    await fs.writeFile(path.join(qaDir,'inspection.ndjson'),inspect.ndjson);
    for(const specification of document.sheets){
      for(let index=0;index<specification.previewTiles.length;index++){
        const tile=specification.previewTiles[index]; console.log(JSON.stringify({stage:"native-tile", documentId:document.documentId, sheet:specification.name, index, range:tile.range, utc:new Date().toISOString()}));
        const preview=await workbook.render({sheetName:specification.name,range:tile.range,scale:1,format:'png'});
        const bytes=new Uint8Array(await preview.arrayBuffer());
        const filename=`sheet-${document.sheets.indexOf(specification)+1}-${String(index+1).padStart(3,'0')}.png`;
        await fs.writeFile(path.join(qaDir,filename),bytes);previews.push({sheet:specification.name,range:tile.range,path:path.join(qaDir,filename),sha256:hash(bytes)});
      }
    }
    const xlsx=await SpreadsheetFile.exportXlsx(workbook);
    const filename=path.join(destination,'Excel',stem+'.xlsx');await fs.mkdir(path.dirname(filename),{recursive:true});await xlsx.save(filename);
    await boundInput(document); console.log(JSON.stringify({stage:"bound-document", documentId:document.documentId, utc:new Date().toISOString()}));
    provenance.documents.push({documentId:document.documentId,canonicalDocumentPath:canonical,markdownSha256:document.markdownSha256,
      xlsx:filename,xlsxSha256:hash(await fs.readFile(filename)),writtenCells:written,previews,
      requestedPrintAreas:document.sheets.map(s=>({sheet:s.name,area:s.printArea})),
      printSettings:'REQUIRES_PUBLIC_API_PROBE_OR_VERIFIED_OOXML_METADATA_CONNECTION',
      independentCellVerification:'PENDING',visualReview:'PENDING',semanticApproval:'NOT_ASSESSED'});
    await fs.writeFile(path.join(destination,'delivery-manifest.json'),JSON.stringify(provenance,null,2)+'\n');
  }
  provenance.status='EXPORTED_VERIFICATION_PENDING';
  if(hash(await fs.readFile(model.binding))!==model.bindingSha256||hash(await fs.readFile(modelPath))!==hash(modelRaw))throw new Error('Binding/model changed during authoring');
}catch(error){provenance.status='FAILED';provenance.error=String(error);provenance.published=false;throw error;}
finally{await fs.writeFile(path.join(destination,'delivery-manifest.json'),JSON.stringify(provenance,null,2)+'\n');}
console.log(JSON.stringify({documents:provenance.documents.length,status:provenance.status,visualReview:'PENDING'}));
