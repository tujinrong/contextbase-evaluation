"""Generate a new safe critique solely from candidate and authorized raw inputs.

No evaluation checklist, selected row, score report, or expected cell is opened.
"""
from pathlib import Path
import datetime, hashlib, json
OUT=Path(__file__).resolve().parent
ROOT=OUT
while not (ROOT/'test-project1/srcs/CSharp_ASPNET').is_dir(): ROOT=ROOT.parent
CAP=ROOT/'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
GEN=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-05/spec/detail/student-search.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
seen={}
def ref(path,a,z=None):
    p=CAP/path; lines=p.read_text(encoding='utf-8-sig').splitlines(); z=a if z is None else z
    assert path.startswith(('sources/','reference-designs/'))
    assert 1<=a<=z<=len(lines)
    seen[path]={'path':path,'sha256':sha(p),'bytes':p.stat().st_size}
    return {'path':path,'startLine':a,'endLine':z,'sha256':sha(p)}
def gen(a,z=None):
    z=a if z is None else z
    assert 1<=a<=z<=len(GEN.read_text(encoding='utf-8-sig').splitlines())
    return {'path':GEN.relative_to(ROOT).as_posix(),'startLine':a,'endLine':z,'sha256':sha(GEN)}
def finding(fid,kind,observation,action,src,generated):
    return {'findingId':fid,'kind':kind,'observation':observation,'suggestedAction':action,
      'sourceEvidence':src,'generatedEvidence':generated}
def preserve(pid,behavior,src,generated):
    return {'preserveId':pid,'behavior':behavior,'sourceEvidence':src,'generatedEvidence':generated}
findings=[
 finding('S5-C01','source-design-layout-distinction',
  '第5稿は現行Razor/CSSの静的投影とViewer/操作権限を具体化し、許可参考HTMLとの出自を区別する。許可参考資料は独立した設計見本のHTML構造を持つが、現稿ではその一部の操作・結果領域は比較説明に留まり、参考設計の配置を読むには外部資料が必要になる。',
  '現行ソースを投影したレイアウトを保持したうえで、許可参考の設計見本を扱うなら、その配置と現行との差を別の明示した設計投影にする。参考設計の部品を現行実装と称して追加せず、ソース投影・参考設計・実機画面の出自を表示する。',
  [ref('reference-designs/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md',29,45),ref('sources/Views/Students/Search.cshtml',1,8),ref('sources/Views/Shared/_Layout.cshtml',1),ref('sources/wwwroot/css/site.css',1)],
  [gen(86,154),gen(1031,1043)]),
 finding('S5-C02','shared-candidate-contract-boundary',
  '候補表は検索用途を詳細に定義し、補足で登録候補の有効性・期間判定を登録側責務としている。実ソースのLookupAsyncとWebPresentation.Lookupsは検索/登録で人数集計と選択可能性が異なる。共有候補という呼び方と、検索専用契約および接続されていない登録向け候補APIの境界をもう少し明示できる。',
  '候補の共通取得データと検索画面の選択規則を分けて書き、登録側の規則を指す箇所には実際の呼出経路・用途・文書責務を添える。検索MVCが使っていないOptionsRequest/Coordinator.Options/Lookupsを接続済みとせず、関連文書の計画参照だけで画面内の候補契約を省略しない。',
  [ref('sources/Core/SqlServerStudentService.cs',196,216),ref('sources/Infrastructure/WebPresentation.cs',8,18),ref('sources/Infrastructure/WebStudentCoordinator.cs',16,17),ref('sources/Web/Controllers/StudentsController.cs',22,25)],
  [gen(182,194),gen(390,420),gen(1045,1057),gen(1078,1108)])
]
preserves=[
 preserve('S5-P01','入力名→DTO移送→サービス正規化→型付きSQLパラメータ→再表示の連鎖、rawと表示表記/照合キーおよび業務文字数とDB容量の区別を保持する。',
  [ref('sources/Web/Inputs/StudentSearchInput.cs',7,22),ref('sources/Core/SqlServerStudentService.cs',103,139),ref('sources/Core/StudentNormalizer.cs',20,61)],
  [gen(58,84),gen(156,181),gen(319,336),gen(982,998)]),
 preserve('S5-P02','状態のGet、Gate取得前の取消、取得後の再確認、Revision照合、成功後の状態更新と期限延長、finallyの解放を分ける。取消や拒否で一律SQL実行済みとしない。',
  [ref('sources/Infrastructure/SearchContextStore.cs',11,15),ref('sources/Infrastructure/WebStudentCoordinator.cs',7,15)],
  [gen(243,279),gen(484,554)]),
 preserve('S5-P03','サービスの検証失敗と状態所有/期限/版の失敗は別の状態となる。PageとSearchの局所WebFaultは元のe.Statusを保持し、後段の候補取得/変換/描画失敗と区別する。',
  [ref('sources/Core/SqlServerStudentService.cs',107,108),ref('sources/Core/SqlServerStudentService.cs',169,170),ref('sources/Infrastructure/WebStudentCoordinator.cs',20),ref('sources/Infrastructure/WebPresentation.cs',23),ref('sources/Web/Controllers/StudentsController.cs',13,19),ref('sources/Infrastructure/WebHostSetup.cs',21,24)],
  [gen(507,554),gen(629,678)]),
 preserve('S5-P04','PageはApplied条件を使い表示指定変更時に先頭から検索する。一度の補正再検索とResumeの保持ページ/SQLローカルページの差を区別する。',
  [ref('sources/Infrastructure/WebStudentCoordinator.cs',11,14),ref('sources/Core/SqlServerStudentService.cs',143,168)],
  [gen(607,678),gen(728,782),gen(1000,1008)]),
 preserve('S5-P05','OptionsはLastResultを維持し今回条件の未反映を伝え、未所属ONで上位条件を解除する。OFFで旧値を復元せず、検索状態のGate/revision更新と同一視しない。',
  [ref('sources/Web/Controllers/StudentsController.cs',22),ref('sources/wwwroot/js/site.js',1,9)],
  [gen(556,605),gen(784,826)]),
 preserve('S5-P06','編集入口では非空の復帰ContextをDB/候補取得後にも再確認してRevisionを取得する。検索リンクは復帰Contextを持ち、状態省略の直接編集は別責務である。',
  [ref('sources/Views/Students/Search.cshtml',8),ref('sources/Infrastructure/WebStudentCoordinator.cs',17),ref('sources/Web/Controllers/StudentsController.cs',23,25)],
  [gen(828,891)]),
 preserve('S5-P07','保存の非成功再表示は今回入力/元Snapshot/結果を使う一方、削除の非成功はLoadで再読込して新Snapshotを作る。削除の再読込で別の不在エラーになる可能性も保持する。',
  [ref('sources/Web/Controllers/StudentsController.cs',28,38)],
  [gen(893,980)]),
 preserve('S5-P08','確認Tokenは所有者・セッション・対象・版・入力内容・候補集合・期限とBusyを照合し、無効時は再確認結果にする。確認の成功だけをDB保存確定と扱わない。',
  [ref('sources/Core/SqlServerStudentService.cs',274,290),ref('sources/Core/SqlServerStudentService.cs',308,321)],
  [gen(893,980)]),
 preserve('S5-P09','確定保存/削除だけが復帰通知と303へ進む。通知Takeは所有者/セッション/状態単位の一回消費で、後段の候補/表示失敗まで含む配信確約ではない。',
  [ref('sources/Web/Controllers/StudentsController.cs',9,11),ref('sources/Web/Controllers/StudentsController.cs',31,38),ref('sources/Infrastructure/FlashMessageStore.cs',7,9)],
  [gen(728,782),gen(913,980)]),
 preserve('S5-P10','表示範囲、Busy、要求世代等の参考設計値は、型・長さ・初期/未設定・設定源を具体化し、ソースにないプロパティ/計算/画面表示は設計意図と区別する。共通契約と計画参照の責務を本書内で説明する。',
  [ref('reference-designs/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md',20,25),ref('reference-designs/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md',129,148),ref('sources/Infrastructure/WebStudentCoordinator.cs',21),ref('sources/Core/Contracts.cs',28,55)],
  [gen(37,56),gen(1010,1108)])
]
payload={'schema':'source-backed-writer-feedback/1','classification':'GENERATION_SAFE_SOURCE_BACKED_FEEDBACK',
 'reviewDocumentId':'SM-DET-STUDENT-SEARCH','reviewDocumentVersion':'5.0',
 'reviewDate':datetime.datetime.now(datetime.timezone.utc).isoformat(),'projectId':'test-project1',
 'profile':'CSharp_ASPNET','iteration':'20261013-focus-round-05',
 'builderInputPolicy':'This builder opens only the completed candidate and raw source/authorized reference-design files in the same permitted capsule. It does not open selected rows, evaluation checklists or scoring reports. Feedback content contains no protected expected cells or points.',
 'provenance':{'generatedPath':GEN.relative_to(ROOT).as_posix(),'generatedSha256':sha(GEN),
  'sourceInputRoot':CAP.relative_to(ROOT).as_posix(),'sourceInputs':list(seen.values()),
  'checks':{'everyEvidenceRangeWithinReferencedFile':True,'pointOrExpectedCellContentIncluded':False,
  'actualApplicationOrDbTestPerformed':False,'actualRenderedImageReviewClaimed':False}},
 'sourceBackedFindings':findings,'existingCorrectBehaviors':preserves,
 'limitations':['静的本文/原文照合の批評。構造/描画/実機/DB/全対話モードの合格を証明しない。',
  '許可参考資料の設計意図を現行ソースの実装済み事実へ変更しない。']}
destination=(OUT/'student-search-feedback.json').resolve()
assert destination.is_relative_to(OUT.resolve()) and destination!=OUT.resolve()
OUT.mkdir(parents=True,exist_ok=True)
with destination.open('xb') as stream:stream.write((json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps({'path':destination.relative_to(ROOT).as_posix(),'sha256':sha(destination),
 'findings':len(findings),'preserves':len(preserves),'sourceInputPins':len(seen)},ensure_ascii=False))
