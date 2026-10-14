// Public documented API only. Probe artifacts are retained, never delivered.
import fs from 'node:fs/promises';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';
const root=process.argv[2];
await fs.mkdir(root,{recursive:false});
const workbook=Workbook.create();
for(const method of ['untouched','none','cleared','outside']){
 const sheet=workbook.worksheets.add(method); const range=sheet.getRange('A1:F8');
 range.format.font={name:'Meiryo',size:10}; range.setNumberFormat('@');
 if(method==='none')range.format.borders={preset:'none'};
 if(method==='cleared'){range.format.borders={preset:'none'};range.clear({applyTo:'formats'});range.format.font={name:'Meiryo',size:10};range.setNumberFormat('@');}
 if(method==='outside')sheet.getRange('B2:E6').format.borders={preset:'outside',style:'thin',color:'#808080'};
 sheet.getRange('B2:E6').merge();sheet.getRange('B2').values=[['border probe']];
 const png=await workbook.render({sheetName:method,range:'A1:F8',scale:1,format:'png'});
 await fs.writeFile(`${root}/${method}.png`,new Uint8Array(await png.arrayBuffer()));
}
await (await SpreadsheetFile.exportXlsx(workbook)).save(`${root}/probe.xlsx`);
