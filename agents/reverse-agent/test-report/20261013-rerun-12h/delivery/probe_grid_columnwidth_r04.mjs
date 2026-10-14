// Public Artifact API, unchanged literal and merge copied mechanically.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const arg=k=>{const n=process.argv.indexOf(k);return n<0?null:process.argv[n+1];};
const cp=arg('--config'),out=arg('--output');
if(!cp||!out||!process.argv.includes('--authoring-marker-completed'))throw Error('Configuration, fresh output, existing marker acknowledgement required');
const cr=await fs.readFile(cp),config=JSON.parse(cr),pins={[path.resolve(cp)]:hash(cr)};
try{await fs.stat(out);throw Error('Fresh output required');}catch(e){if(e.code!=='ENOENT')throw e;}
await fs.mkdir(out,{recursive:false});
const book=Workbook.create(),cells=[],previews=[],fixtures=[];
for(const [ordinal,f] of config.fixtures.entries()){
 const raw=await fs.readFile(f.model);if(hash(raw)!==f.modelSha256)throw Error('Model drift');pins[path.resolve(f.model)]=hash(raw);
 const model=JSON.parse(raw),doc=model.documents.find(d=>d.documentId===f.documentId);
 if(!doc||doc.markdownSha256!==f.markdownSha256)throw Error('Document pin mismatch');
 const spec=doc.sheets.find(s=>s.name===f.sheet),op=spec.operations.find(o=>o.range===f.range);
 if(!op||spec.columns!==120||!['body','table-cell'].includes(op.style))throw Error('Only pinned GRID body operations supported');
 const m=/^([A-Z]+)(\d+):([A-Z]+)(\d+)$/.exec(op.range);if(!m||m[2]!==m[4])throw Error('Single-row merged body required');
 const height=spec.rowHeights[m[2]];if(!Number.isFinite(height))throw Error('Height missing');
 for(const width of f.widths){
  if(!Number.isFinite(width)||width<2||width>255)throw Error('Invalid public column width');
  const name=`F${ordinal+1}_W${width}`,s=book.worksheets.add(name);s.showGridLines=false;
  const r=s.getRange(`A${m[2]}:DP${m[2]}`);r.clear({applyTo:'formats'});
  r.setNumberFormat('@');r.format.font={name:'Meiryo',size:10,color:'#404040'};
  r.format.verticalAlignment='top';r.format.wrapText=true;r.format.columnWidth=2;r.format.rowHeight=height;
  const target=s.getRange(op.range);target.merge();if(op.style==='table-cell')target.format.borders={preset:'outside',style:'thin',color:'#808080'};s.getRange(m[1]+m[2]).values=[[op.value.startsWith('=')||op.value.startsWith("'")?"'"+op.value:op.value]];
  s.getRange(`${f.column}${m[2]}:${f.column}${m[2]}`).format.columnWidth=width;
  cells.push({sheet:name,cell:m[1]+m[2],value:op.value});previews.push({sheet:name,range:op.range});
  fixtures.push({sheet:name,sourceModel:f.model,sourceSheet:f.sheet,sourceRange:op.range,sourceLines:op.sourceLines,sourceColumn:f.column,columnWidthBefore:2,columnWidthAfter:width,rowHeight:height,literalUnchanged:true});
 }
}
const filename=path.join(out,'probe.xlsx');await(await SpreadsheetFile.exportXlsx(book)).save(filename);
const plan={workbook:path.resolve(filename),workbookSha256:hash(await fs.readFile(filename)),manifest:path.resolve(path.join(out,'manifest.json')),sheets:fixtures.map(f=>f.sheet),cells,previews,documentId:'GEOMETRY_ONLY_PINNED_GRID_FIXTURES',canonicalDocumentPath:'synthetic-fixed-literal-probe',markdownSha256:null,readOnly:true,save:false};
const pp=path.join(out,'plan.json');await fs.writeFile(pp,JSON.stringify(plan,null,2)+'\n');
for(const [p,h]of Object.entries(pins))if(hash(await fs.readFile(p))!==h)throw Error('Input drift');
const receipt={schema:'grid-column-width-only-probe/1',scope:'UNCHANGED_LITERAL_GEOMETRY_ONLY',createdUtc:new Date().toISOString(),beforeAfterPins:pins,fixtures,xlsx:plan.workbook,xlsxSha256:plan.workbookSha256,plan:path.resolve(pp),planSha256:hash(await fs.readFile(pp)),markerReexecuted:false,businessContentAuthored:false,originalApplicationExecuted:false,visualApproval:'PENDING'};
await fs.writeFile(path.join(out,'manifest.json'),JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({fixtures:fixtures.length,output:out,status:'PUBLIC_API_EXPORTED_VISUAL_REVIEW_PENDING',xlsxSha256:receipt.xlsxSha256}));
