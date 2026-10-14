// Public Artifact API, copying one unchanged canonical literal into geometry fixtures.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const H=path.dirname(fileURLToPath(import.meta.url));
const P=path.join(H,'registration-columnwidth-probe-r01');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
if(!process.argv.includes('--authoring-marker-completed'))throw Error('Existing marker acknowledgment required, never rerun marker');
const mp=path.join(H,'model-assisted-screens-r18-r02.json');const raw=await fs.readFile(mp);
if(hash(raw)!=='08bc77b7d6a2005f9f39f27d663f5a9373bafa615618f677383f3959d459fa2a')throw Error('Model drift');
const model=JSON.parse(raw);const doc=model.documents.find(d=>d.documentId==='CSHARP_ASPNET-BAS-STU-02');
const spec=doc.sheets.find(s=>s.name==='学生登録_項目');const op=spec.operations.find(o=>o.range==='J41:J41');
if(!op||spec.columnWidths[9]!==44)throw Error('Focal fixture mismatch');
await fs.mkdir(P,{recursive:false});const book=Workbook.create();const cells=[],previews=[],pins=[];
for(const width of [44,60,80,100]){
 const name='Width'+width;const sheet=book.worksheets.add(name);sheet.showGridLines=false;
 const r=sheet.getRange('J41:J41');r.clear({applyTo:'formats'});r.setNumberFormat('@');r.values=[[op.value]];
 r.format.font={name:'Meiryo',size:10,color:'#404040'};r.format.verticalAlignment='top';r.format.wrapText=true;
 r.format.columnWidth=width;r.format.rowHeight=spec.rowHeights['41'];r.format.borders={preset:'outside',style:'thin',color:'#808080'};
 cells.push({sheet:name,cell:'J41',value:op.value});previews.push({sheet:name,range:'J41:J41'});
 const image=await book.render({sheetName:name,range:'J41:J41',scale:1,format:'png'});const b=new Uint8Array(await image.arrayBuffer());
 const png=path.join(P,'artifact-'+width+'.png');await fs.writeFile(png,b);pins.push({width,png,sha256:hash(b)});
}
const xlsx=path.join(P,'probe.xlsx');await(await SpreadsheetFile.exportXlsx(book)).save(xlsx);
const plan={workbook:xlsx,workbookSha256:hash(await fs.readFile(xlsx)),manifest:path.join(P,'manifest.json'),sheets:[44,60,80,100].map(w=>'Width'+w),cells,previews,
 documentId:doc.documentId,canonicalDocumentPath:doc.canonicalDocumentPath,markdownSha256:doc.markdownSha256};
await fs.writeFile(path.join(P,'plan.json'),JSON.stringify(plan,null,2)+'\n');
const receipt={scope:'ONE_UNCHANGED_LITERAL_COLUMN_WIDTH_ONLY_GEOMETRY_PROBE',sourceModel:mp,sourceModelSha256:hash(raw),sourceCell:'学生登録_項目!J41',
 xlsx,xlsxSha256:plan.workbookSha256,pngs:pins,planSha256:hash(await fs.readFile(path.join(P,'plan.json'))),literalUnchanged:true,
 columnWidths:[44,60,80,100],businessContentAuthored:false,markerReexecuted:false,sourceModelAfterSha256:hash(await fs.readFile(mp)),visualReview:'PENDING'};
await fs.writeFile(path.join(P,'manifest.json'),JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
