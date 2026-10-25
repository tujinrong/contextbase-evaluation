// LEGACY one-time migration resource. Current generation uses build/ and .tmp/.
// One-time materialization of seven independent specification packages.
// Every link in each result resolves within that package. No spec-eval input.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const project=path.join(root,'test-project1');
const source=path.join(project,'spec');
const profiles={'VB.NET_WinForms':'SQLServer',CSharp_WPF:'SQLServer',CSharp_ASPNET:'SQLServer',Vue_CSharpAPI:'SQLServer',COBOL:'SQLServer',AS400_RPG:'Db2_for_i',Access:'Access'};
const slash=s=>s.split(path.sep).join('/');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function list(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?list(path.join(dir,e.name)):[path.join(dir,e.name)]);}
const record=[];
for(const [profile,db] of Object.entries(profiles)){
 const dest=path.join(project,'srcs',profile,'spec');
 if(fs.existsSync(dest))throw new Error('Package already exists: '+dest);
 const map=new Map();
 const addTree=(from,to)=>{for(const f of list(from))map.set(f,path.join(dest,to,path.relative(from,f)));};
 for(const f of fs.readdirSync(path.join(source,'共通')).filter(f=>f.endsWith('.md')))map.set(path.join(source,'共通',f),path.join(dest,'共通',f));
 addTree(path.join(source,'基本設計書'),'基本設計書');
 addTree(path.join(source,'共通/方式別',profile),path.join('共通/方式別',profile));
 addTree(path.join(source,'詳細仕様書',profile),path.join('詳細仕様書',profile));
 addTree(path.join(source,'DB定義',db),path.join('DB定義',db));
 for(const f of list(path.join(root,'docs')))if(f.endsWith('.md'))map.set(f,path.join(dest,'規約/全体',path.relative(path.join(root,'docs'),f)));
 map.set(path.join(project,'docs/開発規約.md'),path.join(dest,'規約/開発規約.md'));
 map.set(path.join(project,'docs/開発規約',profile+'.md'),path.join(dest,'規約',profile+'.md'));
 const infoSource=path.join(project,'プロジェクト情報.md'),infoDest=path.join(dest,'プロジェクト情報.md');map.set(infoSource,infoDest);
 const resolve=(href,f)=>path.resolve(path.dirname(f),decodeURIComponent(href.split('#')[0]));
 for(const [from,to] of map){
  const input=fs.readFileSync(from);let output=input;
  if(from.endsWith('.md')||from.endsWith('.html')){
   let text=input.toString('utf8');
   // Exclude index rows for unselected physical/profile documents, preserving invariants.
   text=text.split(/\r?\n/).filter(line=>{
    if(!/^\|/.test(line))return true;
    const first=line.split('|')[1]?.trim();if(Object.keys(profiles).includes(first)&&first!==profile)return false;
    if(['SQLServer','Db2_for_i','Access'].includes(first)&&first!==db&&first!==profile)return false;
    const links=[...line.matchAll(/!?\[[^\]]*\]\(([^\s)]+)\)/g)];
    return !links.some(m=>{if(/^[a-z][a-z\d+.-]*:/i.test(m[1])||m[1].startsWith('#'))return false;const target=resolve(m[1],from);return target.startsWith(source+path.sep)&&!map.has(target);});
   }).join('\n');
   text=text.replace(/(!?)\[([^\]]*)\]\(([^\s)]+)(?:\s+"[^"]*")?\)/g,(whole,img,label,href)=>{
    if(/^[a-z][a-z\d+.-]*:/i.test(href)||href.startsWith('#'))return whole;
    const target=resolve(href,from),mapped=map.get(target);
    if(!mapped)return label; // External workflow/evaluation indexes are not specification dependencies.
    const fragment=href.includes('#')?'#'+href.split('#').slice(1).join('#'):'';
    return `${img}[${label}](${slash(path.relative(path.dirname(to),mapped))}${fragment})`;
   });
   text=text.replaceAll('5方式で共用するSQL Server物理定義','本プロジェクト専用のSQL Server物理定義')
    .replaceAll('全7方式','本方式').replaceAll('全方式','本方式').replaceAll('方式間で共通','本プロジェクト内で共通');
   if(from.endsWith('.md')){
    const matched=text.match(/^<!-- spec-meta: (.*?) -->/);if(!matched)throw new Error('Metadata missing: '+from);
    const meta=JSON.parse(matched[1]);const originalVersion=meta.version;
    meta.documentId=profile.toUpperCase()+'-'+meta.documentId;meta.path=slash(path.relative(root,to));meta.version='8.0';meta.isolationProfile=profile;
    text=text.replace(matched[0],'<!-- spec-meta: '+JSON.stringify(meta)+' -->')
     .replaceAll(originalVersion+'／2026-10-11','8.0／2026-10-12').replaceAll(originalVersion+'／2026-10-12','8.0／2026-10-12');
    // IDs used by business rules remain stable; only document identity is package-specific.
    record.push({profile,file:slash(path.relative(root,to)),sourceSha256:hash(input),sourceVersion:originalVersion,version:'8.0',sha256:hash(text)});
   }else record.push({profile,file:slash(path.relative(root,to)),sourceSha256:hash(input),sha256:hash(text)});
   output=Buffer.from(text);
  }else record.push({profile,file:slash(path.relative(root,to)),sourceSha256:hash(input),sha256:hash(input)});
  fs.mkdirSync(path.dirname(to),{recursive:true});fs.writeFileSync(to,output,{flag:'wx'});
 }
 // This package-level profile is explicit and contains no other project references.
 const meta={schema:'spec-md/1.0',documentId:profile.toUpperCase()+'-PROJECT',version:'8.0',path:slash(path.relative(root,infoDest)),sheets:[{heading:'対象',kind:'GRID',sheet:'01_対象'},{heading:'入力と境界',kind:'GRID',sheet:'02_入力と境界'}]};
 fs.writeFileSync(infoDest,`<!-- spec-meta: ${JSON.stringify(meta)} -->\n# ${profile} プロジェクト仕様\n\n版8.0／2026-10-12。独立した仕様入力。\n\n## 対象\n\n学生の検索・登録・編集・参照・論理削除、クラス・コード保守。方式は ${profile}、DB は ${db}。成績・出欠・年度所属履歴は対象外。\n\n## 入力と境界\n\nこの spec 配下の基本設計・方式内業務規則・詳細・DB定義・規約だけを使用する。他プロジェクトの仕様やコードを参照しない。重複した仕様は本プロジェクト専用の正本として維持する。仕様解析の検証では、この spec と評価資料を解析Agentのコード入力から除外する。\n`);
 const indexMeta={schema:'spec-md/1.0',documentId:profile.toUpperCase()+'-SPEC-INDEX',version:'8.0',path:slash(path.relative(root,path.join(dest,'README.md'))),sheets:[{heading:'対象',kind:'GRID',sheet:'01_対象'},{heading:'入口',kind:'LIST',sheet:'02_入口',key:['区分']},{heading:'隔離',kind:'GRID',sheet:'03_隔離'}]};
 fs.writeFileSync(path.join(dest,'README.md'),`<!-- spec-meta: ${JSON.stringify(indexMeta)} -->\n# ${profile} 仕様書\n\n版8.0／2026-10-12。\n\n## 対象\n\n本プロジェクトだけの実装・DB・画面仕様。\n\n## 入口\n\n| 区分 | 文書 |\n| --- | --- |\n| 対象 | [プロジェクト仕様](プロジェクト情報.md) |\n| 業務 | [仕様索引](共通/00_設計書一覧.md) |\n| 検索 | [詳細](詳細仕様書/${profile}/01_学生検索画面.md) |\n| 登録 | [詳細](詳細仕様書/${profile}/02_学生登録画面.md) |\n| 方式 | [方式内実装仕様](共通/方式別/${profile}/01_共通実装仕様.md) |\n| DB | [物理定義](DB定義/${db}/01_DB定義書.md) |\n| 規約 | [実装規約](規約/${profile}.md) |\n\n## 隔離\n\nすべての仕様参照はこのフォルダー内で閉じる。業務項目・規則IDは維持し、文書IDは本方式専用とした。他プロジェクトと共通の仕様ファイル、symlink、外部への相互引用は使用しない。\n`);
 console.log(JSON.stringify({profile,files:map.size+1,destination:slash(path.relative(root,dest))}));
}
fs.writeFileSync(path.join(project,'report/20261012-isolation-spec-materialization.json'),JSON.stringify({recordedAt:new Date().toISOString(),sourceInputManifest:'20261012-build-06-inputs.json',packageVersion:'8.0',scope:'independent specifications; evaluation input excluded',files:record},null,2)+'\n',{flag:'wx'});
