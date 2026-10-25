// RETIRED one-time migration resource; current indexes must not be overwritten.
throw new Error('Retired migration: maintain current project/spec/<profile> indexes through the current specification contract. This historical writer cannot be rerun.');
// Control indexes contain routing only. All business specifications live in each package.
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const profiles=[['VB.NET_WinForms','VB.NET / WinForms','SQL Server 2022'],['CSharp_WPF','C# / WPF','SQL Server 2022'],['CSharp_ASPNET','C# / ASP.NET Core MVC','SQL Server 2022'],['Vue_CSharpAPI','Vue / TypeScript + C# API','SQL Server 2022'],['COBOL','GnuCOBOL / C / CGI','SQL Server 2022'],['AS400_RPG','ILE RPG / DDS / CL','Db2 for i'],['Access','VBA / DAO / Access forms','ACE']];
function document(file,id,title,sections){const meta={schema:'spec-md/1.0',documentId:id,version:'8.0',path:file,sheets:sections.map(([heading,,kind='GRID'],i)=>({heading,kind,sheet:String(i+1).padStart(2,'0')+'_'+heading,...(kind==='LIST'?{key:['方式ID']}: {})}))};write(file,'<!-- spec-meta: '+JSON.stringify(meta)+' -->\n# '+title+'\n\n版8.0／2026-10-12。現行の独立配置。各実行結果は試験報告の範囲で判定する。\n\n'+sections.map(([h,c])=>'## '+h+'\n\n'+c+'\n').join('\n'));}
function write(file,text){fs.mkdirSync(path.dirname(path.join(root,file)),{recursive:true});fs.writeFileSync(path.join(root,file),text);}
const index=(prefix,spec=false)=>'| 方式ID | 言語 | DB | 独立入口 |\n| --- | --- | --- | --- |\n'+profiles.map(([p,l,d])=>`| ${p} | ${l} | ${d} | [${spec?'専用仕様':'ソース・手順'}](${prefix}${p}/${spec?'spec/':''}README.md) |`).join('\n');
document('test-project1/README.md','PROJECT-README','test-project1 学生管理',[
 ['対象','仕様書解析Agent検証用の7つの独立プロジェクト。検索と登録・編集・参照・論理削除、およびクラス・コード保守を題材とする。各方式の原仕様、ソース、DB資源、生成器、ビルド、試験を当該方式内に置く。'],
 ['方式一覧',index('srcs/'),'LIST'],
 ['入力と報告','[プロジェクト情報](プロジェクト情報.md)／[仕様索引](spec/README.md)／[試験結果](test-report/README.md)。入力版・入力SHA-256・構造検査・出力SHA-256はreportの現行実行IDのJSONを参照する。過去の中断報告や試験合格を現行版へ流用しない。'],
 ['隔離境界','各方式は他方式のコード、仕様、DB定義、生成器を引用しない。原仕様は各方式内のspecだけを正本とする。旧横断仕様と共有ソースは[履歴](report/archive/20261012-pre-isolation/README.md)へ退避した。逆生成の入力はagent-inputの当該方式のソース用ZIPだけとし、元のspec、spec-eval、履歴、入力manifestは渡さない。全体docsや他Agent契約は変更していない。'],
]);
document('test-project1/プロジェクト情報.md','PROJECT-TEST1','test-project1 プロジェクト情報',[
 ['対象','顧客IT部門向けの業務基本設計と、経験5年程度のPG向け詳細から、方式ごとに独立実装を作成する。成績・出欠・年度所属履歴は対象外。実クラスと学生を初期値へ作らない。'],
 ['方式一覧',index('srcs/',true),'LIST'],
 ['独立配置','各srcs/方式/specに基本・詳細・規則・DB定義を完備し、方式内でのみ共通処理を使用する。SQL Server採用方式もそれぞれ独自のdatabaseを持つ。VB.NETはVB.NETで業務層を持ち、WPFはXAML/ViewModel、MVCはRazor、VueはComposition API、COBOLはCGI、RPGは5250/DDS/CL、Accessは内包フォーム/VBAを採用する。'],
 ['Access成果','Access/StudentManagement.accdbを1個の配布成果とする。フォーム、VBA、業務表、初期コード、評価用主体定義を内包する。外部リンク表や別バックエンドファイルは要求しない。試験fixtureは配布ファイルと区別する。'],
 ['評価入力','agent-input/方式-source.zipは当該方式のプログラム、DB資源、ビルド資料のみ。specと採点基準を含めない。spec-evalは本工程で未読・未変更。逆生成・照合・採点は未実施。全体ルーティング契約の隔離ZIP利用更新は別Agentの対象として報告する。'],
 ['検査範囲','[test-report](test-report/README.md)にビルド、実行試験、fake/ホスト環境、未実施、失敗と再試験の根拠を残す。SQL Server実機、IBM i処理系、Linux CGI配備、実認証結合等の未確認を静的検査やホスト試験で代替しない。']
]);
document('test-project1/spec/README.md','PROJECT-SPEC-INDEX','独立仕様書への入口',[
 ['正本','この索引は配置情報だけを持つ。業務仕様を横断して共有する文書は置かない。各方式の仕様セットはその方式のsrcs/方式/spec内だけで閉じる。'],
 ['方式一覧',index('../srcs/',true),'LIST'],
 ['旧版','改訂前の横断仕様はreport/archive/20261012-pre-isolation/specに履歴として保存する。現行生成入力へ含めず、方式別の現行仕様へ変更を自動伝播しない。']
]);
document('test-project1/docs/開発規約.md','DOC-BADE67AD5324','独立プロジェクトの工程境界',[
 ['対象','選択方式のsrcs/方式内だけで仕様確認、生成、ビルド、試験を行う。各方式専用の規則もその方式のspec内に収容する。'],
 ['引用境界','ProjectReference、Compile Link、SQL include、生成器の入力、ローカル文書リンクを他方式へ出さない。ビルド・試験ツールの既定出力も当該方式内に置く。build-agentの工程制御が全方式の検査結果を集約する際だけ、test-reportへの出力先を明示指定する。'],
 ['検証境界','逆生成には当該方式のソースZIPを渡す。原仕様、spec-eval、入力manifest、他方式、過去報告は含めない。実行済み・未実施・静的検査・fake使用・実機を区別し、入力と出力の版とハッシュを記録する。'],
 ['変更範囲','利用者指定により変更可能なのはagents/build-agentとtest-project1。全体docs、他Agent、他projectへの修正を行わない。必要なルーティング更新はreportへ報告する。構造問題を検出した場合はreportへ保存して中断する。']
]);
write('test-project1/report/archive/20261012-pre-isolation/README.md','# 独立化前の履歴\n\n2026-10-12、利用者の方式別完全隔離指示により退避した原仕様、題材規約、共有ソース。生成・ビルド・逆生成の現行入力には使用しない。旧報告の元パスは、このフォルダー内の同名spec/docs/srcsへ対応する。文書内の版・パス・リンクは当時の証拠として保存した。\n');
write('test-project1/srcs/README.md','# 独立プログラム\n\n2026-10-12。各方式のフォルダーを単独で扱う。コード、仕様(spec)、DB(database)、生成器、試験は当該フォルダー内で完結し、他方式を参照しない。\n\n'+index('')+'\n\nAccessの配布成果はAccess/StudentManagement.accdb 1個。実行結果と未実施は[test-report](../test-report/README.md)を参照。仕様書解析には[ソース専用パッケージ](../agent-input/README.md)を使い、原仕様を入力に含めない。\n');
console.log('Updated independent project control indexes.');
