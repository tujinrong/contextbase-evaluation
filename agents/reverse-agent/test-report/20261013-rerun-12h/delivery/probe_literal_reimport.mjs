// Read-only public API re-import of actual XLSX, preserving all stored strings.
import fs from 'node:fs/promises';
import path from 'node:path';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const [xlsx,sheetName,range,output]=process.argv.slice(2);
if(!xlsx||!sheetName||!range||!output) throw new Error('xlsx sheetName range freshOutput required');
await fs.mkdir(output,{recursive:false});
const input=await FileBlob.load(xlsx);
const wb=await SpreadsheetFile.importXlsx(input);
const sheet=wb.worksheets.getItem(sheetName);
const values=sheet.getRange(range).values;
await fs.writeFile(path.join(output,'values.json'),JSON.stringify({xlsx,sheetName,range,values},null,2));
const png=await wb.render({sheetName,range,scale:1,format:'png'});
await fs.writeFile(path.join(output,'reimport.png'),new Uint8Array(await png.arrayBuffer()));
