"""Publish new evidence summary, never overwrite any old report."""
from pathlib import Path
import json,hashlib,datetime,os,re,shutil
from evidence import compiled_inputs,binary_hashes
ROOT=Path(__file__).resolve().parents[1]
REPORT=Path(os.environ.get('COBOL_TEST_REPORT_DIR',ROOT/'test-report')).resolve()
name='20261012-build-04-cobol-27-report'
target=REPORT/(name+'.json')
if target.exists():raise SystemExit('Existing report is preserved')
def read(name):return json.loads((REPORT/name).read_text(encoding='utf-8'))
static='20261012-build-04-cobol-26-static';build='20261012-build-04-cobol-24-host-build';tests='20261012-build-04-cobol-25-host-tests'
s=read(static+'.json');b=read(build+'.json');t=read(tests+'.json')
assert b['succeeded'] and all(x['exitCode']==0 for x in b['results'])
assert b['compiledInputs']==compiled_inputs() and b['binaryHashes']==binary_hashes()
assert t['passed']==t['total']==86 and s['passed']==s['total']==12
assert not re.search(r'warning:|error:',(REPORT/(build+'.raw.log')).read_text(encoding='utf-8'),re.I)
files=[p for folder in ['cobol','copy','bridge','sql','assets','database','tools','deploy'] for p in sorted((ROOT/folder).rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
files += [ROOT/'Makefile',ROOT/'README.md',ROOT/'IMPLEMENTATION.md',ROOT/'dependencies.lock.json',ROOT/'build/input-manifest.json']
data={'runId':'20261012-build-04','project':'COBOL','recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inputVersion':'8.0','inputCount':46,'inputManifest':'build/input-manifest.json','inputManifestSha256':t['inputManifestSha256'],'outputs':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'productionPrograms':25,'copybooks':len(list((ROOT/'copy').glob('*.cpy'))),'fixedSQLCommands':38,'logicalRawFields':19,'logicalSearchFields':12,'logicalListFields':11,'records':{'static':static+'.json','build':build+'.json','tests':tests+'.json'},'hostBuild':{'succeeded':True,'warnings':0,'errors':0,'COBOLFiles':28,'productionPrograms':25,'profile':'Windows x64 GnuCOBOL3.2.0 + Zig0.14.1 + ICU78.3 + OpenSSL3.6.5; not Linux deployment'},'hostTests':{'passed':86,'total':86,'categories':{'ABI':1,'date':26,'integer':6,'unicode':12,'LIKE':2,'hex':3,'HTTP':11,'CGI':2,'registrationValidation':23}},'staticChecks':{'passed':12,'total':12},'unresolvedReferences':[],'notExecuted':['Linux compilation/link/runtime','Linux exact dependency package lock','SQLServer DDL/seed/CRUD/master maintenance/effective privileges','CGI database-state recovery across process restart','two-connection concurrency/capacity','audit failure rollback','commit-response-loss','real browser UI'], 'excludedHistoricalEvidence':['01..22 are preserved historical/debugging records; 18 failed build and 19 ran stale binaries, so 19 is excluded as current-source evidence'],'structuralSpecificationFindings':[]}
target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=f'''# COBOL 独立生成・ホスト試験報告

2026-10-12／runId 20261012-build-04。現行入力はCOBOL/spec版8.0、46ファイル。入力SHA256は `{data['inputManifestSha256']}`。旧版の合格を現行検査として流用していません。

生成済みは25 production PROGRAM-ID、11 COPY、38固定SQL、2業務画面、保守CLI、SQLServer業務5表89列＋技術2表、5分類70初期値、Makefile、依存記録、配備・ABI資料です。方式内のspec/source/database/tools/toolchainで完結します。生成は実業務分岐を持つCOBOL/Cで、未解決CALL/COPY/command参照・未生成参照先は0です。

| 検査 | 結果 | 新規証拠 |
| --- | --- | --- |
| 入力・CALL/COPY/SQL・ABI・状態・隔離静的検査 | 12/12 PASS | [{static}.json]({static}.json) / [生ログ]({static}.raw.log) |
| GnuCOBOL3.2.0構文/C変換＋Zig0.14.1リンク | production25＋probe3、警告0/エラー0 | [{build}.json]({build}.json) / [生ログ]({build}.raw.log) |
| 実バイナリーの境界・入力検証 | 86/86 PASS | [{tests}.json]({tests}.json) / [生ログ]({tests}.raw.log) |

実行対象はWindows x64ホストです。ICU78.3-4/OpenSSL3.6.5-1を含むMSYS2配布物の版・取得先・SHA256とローカルZigを固定しています。手書きCはWall/Wextra/Werror、GnuCOBOL生成Cだけ旧形式プロトタイプ警告を抑制しています。ABI1、暦26、整数6、Unicode12、LIKE2、hex3、HTTP11、CGI400/401の2、登録検証23件を実行しました。COPY本体を用いたAPP整列・pointer/int32/int64/NULL、raw上限と正規化後上限、4バイト文字、全角hint、必須・状態・終了日・連絡先を含みます。

ビルド時の全コンパイル入力とexeハッシュを記録し、試験前に現在のソース・バイナリーと一致することを検査します。18番のビルド失敗と19番の旧バイナリー試験は保存しましたが、現行合格根拠から除外しました。最終証拠は24/25/26番だけです。

19raw（生年月日は元号/年/月/日4入力）、12検索条件、11一覧項目を実装し、一覧の技術ID・複合列を分けるためSQL取得は13物理列です。仕様ID/ファイル対応は方式内IMPLEMENTATION.mdです。EV-SRC-001～006、EV-REG-001～007、共通01～17、SQLServer定義の対応を記録しています。

入力中条件と実行済み条件を分離し、検索/ページ/クリア/復帰/保存/確認/削除等でContext revisionを検査します。登録後は再取得、候補検索では人数集計を実行せず登録候補のみ参考人数を取得します。続柄分類と値のNULLを揃え、定員・候補・版をゲート取得後に再判定し、全候補ID/版をハッシュ・20件だけ表示します。理由未入力は確認情報を保持し、取消では消費します。保守監査はCREATE/UPDATE/DISABLE/ENABLE、学生削除はDELETEです。描画時のDB失敗をヘッダーへ反映できるよう、描画完了までHTTPヘッダーを送信しません。

未生成の参照先や業務TODO骨組みはありません。ただしLinux版依存物の正確なパッケージlock、Linuxコンパイル/リンク/CGI、実SQLServerのDDL/seed/CRUD/保守/有効権限、プロセス再起動状態復帰、2接続競合/定員、監査失敗、COMMIT後応答喪失、ブラウザー画面は未実施です。共通認証済みWebサーバー、DBサービス主体、秘密管理は配備前提で、実稼働設定はまだありません。この報告は実DB/配備の合格を意味しません。

構造的な仕様矛盾は今回の担当範囲で確定していません。旧中断報告は保存し、今回の報告で上書きしていません。入力/生成物ハッシュの全一覧は [{name}.json]({name}.json) です。
'''
(REPORT/(name+'.md')).write_text(md,encoding='utf-8',newline='\n')
local=ROOT/'test-report';local.mkdir(exist_ok=True)
for base in [static,build,tests,name]:
 for p in REPORT.glob(base+'.*'):
  destination=local/p.name
  if destination.resolve()==p.resolve():continue
  if destination.exists():raise SystemExit('Existing local report preserved: '+str(destination))
  shutil.copy2(p,destination)
print(str(target.with_suffix('.md')))
