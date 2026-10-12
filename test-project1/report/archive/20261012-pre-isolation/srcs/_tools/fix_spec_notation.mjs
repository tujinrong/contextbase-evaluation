// Local typographical corrections only; never reads spec-eval or changes requirements.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const project=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const report=path.join(project,'report/20261012-build-06-local-fixes.json');
if(fs.existsSync(report))throw new Error('Correction record already exists.');
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const files=[];
function walk(dir){for(const entry of fs.readdirSync(dir,{withFileTypes:true})){const file=path.join(dir,entry.name);if(entry.isDirectory())walk(file);else if(entry.name.endsWith('.md'))files.push(file);}}
walk(path.join(project,'spec'));
const records=[];
for(const file of files){
 const before=fs.readFileSync(file);let text=before.toString('utf8');const reasons=[];
 if(/CCSID(1200|1208)\b/.test(text)){text=text.replace(/CCSID(1200|1208)\b/g,'CCSID $1');reasons.push('Db2 CCSID clause spacing; encoding/type/capacity unchanged');}
 if(file.endsWith(path.join('AS400_RPG','02_学生登録画面.md'))&&text.includes('F8=次の入力ページ')){text=text.replaceAll('F7=前の入力ページ　F8=次の入力ページ　F12=取消','F7=前の入力ページ　F8=Unicode入力　F9=次の入力ページ　F12=取消');reasons.push('RPG mock function keys aligned with Unicode input contract');}
 if(!reasons.length)continue;
 const meta=JSON.parse(text.match(/^<!-- spec-meta: (.*?) -->/)[1]);const oldVersion=meta.version;const parts=oldVersion.split('.');const newVersion=`${parts[0]}.${Number(parts[1])+1}`;
 text=text.replace(`"version":"${oldVersion}"`,`"version":"${newVersion}"`).replaceAll(`${oldVersion}／2026-10-11`,`${newVersion}／2026-10-12`).replaceAll(`${oldVersion}／2026-10-12`,`${newVersion}／2026-10-12`);
 fs.writeFileSync(file,text);records.push({file:path.relative(project,file).split(path.sep).join('/'),beforeVersion:oldVersion,afterVersion:newVersion,beforeSha256:hash(before),afterSha256:hash(text),reasons});
}
const html=path.join(project,'spec/詳細仕様書/AS400_RPG/assets/学生登録.html');const before=fs.readFileSync(html);const after=before.toString('utf8').replaceAll('F7=前の入力ページ　F8=次の入力ページ　F12=取消','F7=前の入力ページ　F8=Unicode入力　F9=次の入力ページ　F12=取消');
if(hash(before)!==hash(after)){fs.writeFileSync(html,after);records.push({file:path.relative(project,html).split(path.sep).join('/'),beforeSha256:hash(before),afterSha256:hash(after),reasons:['Standalone RPG mock matches embedded HTML']});}
fs.writeFileSync(report,JSON.stringify({recordedAt:new Date().toISOString(),scope:'local syntax/display corrections; no business contract changes',records},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({documents:records.filter(x=>x.beforeVersion).length,assets:records.filter(x=>!x.beforeVersion).length,report:path.relative(project,report)}));
