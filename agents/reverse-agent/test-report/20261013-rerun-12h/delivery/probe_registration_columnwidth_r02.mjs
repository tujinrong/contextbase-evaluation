// Public Artifact API. Copy unchanged literals into width-only geometry fixtures.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const H=path.dirname(fileURLToPath(import.meta.url));
const P=path.join(H,'registration-columnwidth-probe-r02');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
if(!process.argv.includes('--authoring-marker-completed'))throw Error('Existing marker acknowledgment required; never rerun marker');
const mp=path.join(H,'model-assisted-screens-r18-r02.json'),raw=await fs.readFile(mp);
if(hash(raw)!=='08bc77b7d6a2005f9f39f27d663f5a9373bafa615618f677383f3959d459fa2a')throw Error('Model drift');
const model=JSON.parse(raw),doc=model.documents.find(d=>d.documentId==='CSHARP_ASPNET-BAS-STU-02');
const spec=doc.sheets.find(s=>s.name==='学生登録_項目');
const rows=[41,44,45,46,47], widths=[60,100,160,255];
await fs.mkdir(P,{recursive:false});const book=Workbook.create(),cells=[],previews=[];
for(const width of widths){
 const name='Width'+width,sheet=book.worksheets.add(name);sheet.showGridLines=false;
 for(const row of rows){
  const address='J'+row,op=spec.operations.find(o=>o.range===address+':'+address);if(!op)throw Error('Missing focal literal');
  const r=sheet.getRange(address+':'+address);r.clear({applyTo:'formats'});r.setNumberFormat('@');r.values=[[op.value]];
  r.format.font={name:'Meiryo',size:10,color:'#404040'};r.format.verticalAlignment='top';r.format.wrapText=true;
  r.format.columnWidth=width;r.format.rowHeight=spec.rowHeights[String(row)];r.format.borders={preset:'outside',style:'thin',color:'#808080'};
  cells.push({sheet:name,cell:address,value:op.value});previews.push({sheet:name,range:address+':'+address});
 }
}
const xlsx=path.join(P,'probe.xlsx');await(await SpreadsheetFile.exportXlsx(book)).save(xlsx);
const plan={workbook:xlsx,workbookSha256:hash(await fs.readFile(xlsx)),manifest:path.join(P,'manifest.json'),sheets:widths.map(w=>'Width'+w),cells,previews,documentId:doc.documentId,canonicalDocumentPath:doc.canonicalDocumentPath,markdownSha256:doc.markdownSha256};
await fs.writeFile(path.join(P,'plan.json'),JSON.stringify(plan,null,2)+'\n');
const receipt={scope:'UNCHANGED_LITERAL_MULTI_CELL_COLUMN_WIDTH_ONLY_GEOMETRY_PROBE',sourceModel:mp,sourceModelSha256:hash(raw),sourceCells:rows.map(r=>'学生登録_項目!J'+r),xlsx,xlsxSha256:plan.workbookSha256,planSha256:hash(await fs.readFile(path.join(P,'plan.json'))),columnWidths:widths,literalUnchanged:true,businessContentAuthored:false,markerReexecuted:false,sourceModelAfterSha256:hash(await fs.readFile(mp)),visualReview:'PENDING'};
await fs.writeFile(path.join(P,'manifest.json'),JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
