// Read-only public API discovery. Does not populate, export or save a workbook.
import { Workbook } from '@oai/artifact-tool';
const workbook=Workbook.create();
console.log(workbook.help('worksheet.pageLayout', {include:'index,examples,notes',maxChars:6500}).ndjson);
