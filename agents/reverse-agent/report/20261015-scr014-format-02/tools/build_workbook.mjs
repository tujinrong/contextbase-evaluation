// Generic format projection only. Business text is taken literally from the AI Markdown model.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';
const W=String.raw`D:\開発\contextbase-evaluation\agents\reverse-agent\.tmp\20261015-scr014-format-02`;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const raw=await fs.readFile(path.join(W,'view-model.json'));const model=JSON.parse(raw);
const hierarchy=JSON.parse(await fs.readFile(path.join(W,'hierarchy.json'),'utf8'));
const parentLabels=new Set(hierarchy.groups.flatMap(s=>s.groups.map((g,i)=>`${i+1}. ${g.title}`)));
if(model.schema!=='scr014-pilot-view-model/1'||model.documentId!=='SCR-014'||model.businessContentAuthored!==false)throw Error('Unexpected model');
if(!process.argv.includes('--marker-completed'))throw Error('Author marker must precede first authoring');
if(sha(await fs.readFile(model.markdown))!==model.markdownSha256)throw Error('Markdown changed');
const wb=Workbook.create(),out=path.join(W,'staged'),qa=path.join(W,'workbook-preview');
await fs.mkdir(out,{recursive:true});await fs.mkdir(qa,{recursive:true});
const col=n=>{let s='';while(n){let m=(n-1)%26;s=String.fromCharCode(65+m)+s;n=Math.floor((n-1)/26);}return s;};
const outside=(r,style='thin',color='#808080')=>{r.format.borders={preset:'outside',style,color};};
const written=[];
for(const spec of model.sheets){
 const s=wb.worksheets.add(spec.name);s.showGridLines=false;
 const region=s.getRange(`A1:${col(spec.columns)}${spec.lastRow}`);
 region.clear({applyTo:'formats'});region.setNumberFormat('@');
 region.format.font={name:'Meiryo',size:10,color:'#404040'};
 region.format.verticalAlignment='top';region.format.wrapText=true;
 region.format.columnWidth=spec.role==='normal'||spec.role==='cover'?3:18;
 if(spec.columnWidths)for(let i=0;i<spec.columnWidths.length;i++)s.getRange(`${col(i+1)}1:${col(i+1)}${spec.lastRow}`).format.columnWidth=spec.columnWidths[i];
 for(const [row,height] of Object.entries(spec.rowHeights))s.getRange(`A${row}:${col(spec.columns)}${row}`).format.rowHeight=height;
 for(const op of spec.operations){
  const [a,b]=op.range.split(':');const r=s.getRange(op.range);if(a!==b)r.merge();
  const text=op.value; s.getRange(a).values=[[/^[=']/.test(text)?"'"+text:text]];
  if(parentLabels.has(text)&&op.style==='body')r.format.font={name:'Meiryo',size:10,bold:true,color:'#202020'};
  if(['title','heading','table-header','cover-title'].includes(op.style))r.format.font={name:'Meiryo',size:op.style==='cover-title'?24:op.style==='title'?14:10,bold:true,color:'#202020'};
  if(op.style==='code')r.format.font={name:'Consolas',size:10,color:'#404040'};
  if(op.style==='table-header'){r.format.fill='#D9D9D9';r.format.horizontalAlignment='center';outside(r);}
  else if(op.style==='table-cell'||op.style==='cover-cell')outside(r);
  else if(op.style==='cover-title')outside(r,'double','#595959');
  else if(op.style==='cover-company-band')r.format.borders={top:{style:'thin',color:'#808080'}};
  if(spec.role==='cover'){
   r.format.verticalAlignment='center';r.format.horizontalAlignment='center';
   if(/^O(?:12|15|18):/.test(op.range)||/^O23:|^Z23:|^AK23:/.test(op.range))r.format.fill='#D9D9D9';
  }
  written.push({sheet:spec.name,cell:a,range:op.range,value:text,sourceLines:op.sourceLines});
 }
 if(spec.role==='normal'){
  outside(region,'medium','#000000');
  s.getRange(`A1:${col(spec.columns)}1`).format.borders={top:{style:'medium',color:'#000000'},left:{style:'medium',color:'#000000'},right:{style:'medium',color:'#000000'},bottom:{style:'double',color:'#595959'}};
 }
 if(spec.role==='list')for(const t of spec.tables){
  s.freezePanes.freezeRows(t.headerRow);
  for(const c of ['A','E'])s.getRange(`${c}${t.headerRow+1}:${c}${spec.lastRow}`).format.horizontalAlignment='center';
  s.getRange(`A${t.headerRow}:J${t.headerRow}`).format.borders={top:{style:'medium',color:'#000000'},left:{style:'medium',color:'#000000'},right:{style:'medium',color:'#000000'},bottom:{style:'thin',color:'#808080'},insideVertical:{style:'thin',color:'#808080'}};
 }
 for(const im of spec.images){
  const b=await fs.readFile(im.path);if(sha(b)!==im.sha256)throw Error('Image drift');
  s.images.add({dataUrl:'data:image/png;base64,'+b.toString('base64'),anchor:{from:{row:im.row,col:im.col},extent:{widthPx:im.displayWidth,heightPx:im.displayHeight}}});
 }
 console.log(JSON.stringify({stage:'sheet-created',name:spec.name,rows:spec.lastRow,utc:new Date().toISOString()}));
}
wb.recalculate();
// Literal values only; independently compare every projected source cell before export.
for(const c of written){const v=wb.worksheets.getItem(c.sheet).getRange(c.cell).values[0][0];if(String(v)!==c.value&&String(v)!=="'"+c.value)throw Error('Cell mismatch '+c.sheet+'!'+c.cell);}
await fs.writeFile(path.join(qa,'inspection.ndjson'),(await wb.inspect({kind:'sheet',include:'id,name',maxChars:4000})).ndjson);
const previews=[];
for(let si=0;si<model.sheets.length;si++){
 const spec=model.sheets[si];
 for(let ti=0;ti<spec.previewTiles.length;ti++){
  const tile=spec.previewTiles[ti],file=path.join(qa,`sheet-${si+1}-${String(ti+1).padStart(3,'0')}.png`);
  const blob=await wb.render({sheetName:spec.name,range:tile.range,scale:1,format:'png'});
  await fs.writeFile(file,new Uint8Array(await blob.arrayBuffer()));previews.push({sheet:spec.name,range:tile.range,path:file,sha256:sha(await fs.readFile(file))});
  console.log(JSON.stringify({stage:'sheet-rendered',sheet:spec.name,tile:ti+1,utc:new Date().toISOString()}));
 }
}
if(sha(await fs.readFile(model.markdown))!==model.markdownSha256)throw Error('Source drift');
const dest=path.join(out,path.basename(model.canonicalDocumentPath,'.md')+'.xlsx');
await (await SpreadsheetFile.exportXlsx(wb)).save(dest);
await fs.writeFile(path.join(W,'workbook-build.json'),JSON.stringify({schema:'scr014-workbook-build/1',modelSha256:sha(raw),markdownSha256:model.markdownSha256,workbook:dest,workbookSha256:sha(await fs.readFile(dest)),writtenCells:written,previews,recalculated:true,literalCellComparison:true,visualReview:'PENDING',nativeFileVerification:'PENDING',businessTextAuthored:false},null,2));
console.log(JSON.stringify({stage:'exported',workbook:dest}));
