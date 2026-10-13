"""Writer-safe feedback from completed candidate, source, authorized reference.

No protected checklist, selected-row, expectation or scoring report is read.
"""
from pathlib import Path
import hashlib,json,datetime
OUT=Path(__file__).resolve().parent
ROOT=OUT
while not (ROOT/'test-project1/srcs/CSharp_ASPNET').is_dir():ROOT=ROOT.parent
F=ROOT/'agents/reverse-agent/test-report/20261013-session-pilot-01/evaluator-only/focus-round-04/frozen'
GEN=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-04/spec/detail/student-search.md'
CAP=ROOT/'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={}
def ref(path,a,b=None):
    b=a if b is None else b;p=F/path
    assert path.startswith(('sources/','reference-designs/'))
    assert 1<=a<=b<=len(p.read_text(encoding='utf-8-sig').splitlines())
    cap=CAP/path;assert sha(cap)==sha(p)
    pins[path]={'path':path,'sha256':sha(p),'bytes':p.stat().st_size}
    return {'path':path,'startLine':a,'endLine':b,'sha256':sha(p)}
def gen(a,b=None):
    b=a if b is None else b
    assert 1<=a<=b<=len(GEN.read_text(encoding='utf-8-sig').splitlines())
    return {'path':GEN.relative_to(ROOT).as_posix(),'startLine':a,'endLine':b,'sha256':sha(GEN)}
def finding(key,kind,observation,action,source,generated):
    return {'findingId':key,'kind':kind,'observation':observation,'suggestedAction':action,'sourceEvidence':source,'generatedEvidence':generated}
def preserve(key,behavior,action,source,generated):
    return {'behaviorId':key,'behavior':behavior,'preserve':action,'sourceEvidence':source,'generatedEvidence':generated}
findings=[
 finding('S4-C01','in-scope-document-responsibility',
  '本文は接続されたController・Coordinator・Serviceの役割を具体的に記述しているが、関連文書表では共通契約の引数・結果や文書の正本責務が計画IDの列挙に寄っている。許可参考資料は、本画面の具体契約と共通実装・DB定義・規約の責務を分けて説明している。',
  '計画参照が未生成でも、本画面で使う契約の責務、受け渡す引数と結果、文書の役割を本書内に残す。参考資料の設計責務と実際に接続されたソース名を分け、資料で確認できない契約を補作しない。',
  [ref('sources/Web/Controllers/StudentsController.cs',13,22),ref('sources/Infrastructure/WebStudentCoordinator.cs',7,21),ref('reference-designs/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md',20,25),ref('reference-designs/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md',76,78),ref('reference-designs/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md',586,598)],
  [gen(18,35),gen(931,981)]),
 finding('S4-C02','declared-design-value-contract',
  '件数はSearchResultとPresentまで型・設定元を追える。一方、表示範囲等の設計名は設計意図と現行不在の対比が中心で、本文内の状態・出力契約への対応が薄い。現行Presentに存在しない値を実装済みとしていない点は正しい。',
  '設計側にだけ存在する状態や表示値は、許可資料で確認できる型・設定元・初期／成功／失敗時の扱いを設計契約として整理し、現行ソースの宣言・計算・移送の有無とは別に対応させる。資料が不足する属性や算式は未確認と明示する。',
  [ref('sources/Core/Contracts.cs',57,58),ref('sources/Infrastructure/WebStudentCoordinator.cs',21),ref('sources/Views/Students/Search.cshtml',2,8),ref('reference-designs/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md',100,101),ref('reference-designs/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md',135,147)],
  [gen(190),gen(217,218),gen(923,929),gen(945)]),
 finding('S4-C03','verification-responsibility-description',
  '文書・実装・配信の成功境界は詳しいが、実装工程で確認する観点と担当責務の説明は簡略な一般列挙に留まる。現在の文書検査や描画からアプリ／DBの試験合格を導いていない点は維持できる。',
  '既に記述した受信→正規化→DB→再表示、状態更新とHTML到達の境界に対して、許可参考資料が求める確認観点と実装工程の責務を具体的に対応させる。文書検査、静的投影、今後の実装試験を分け、未実施の検証は未実施のまま表示する。',
  [ref('sources/Infrastructure/SearchContextStore.cs',14),ref('sources/Infrastructure/WebStudentCoordinator.cs',9,15),ref('sources/Web/Controllers/StudentsController.cs',39),ref('reference-designs/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md',546,550),ref('reference-designs/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md',586,598)],
  [gen(905,953),gen(955,981)])
]
correct=[
 preserve('S4-P01','フォーム／入力DTO／サービス条件／正規化ローカル／SqlDbTypeとSize／DB列／一覧DTOのつながりを分離して追跡している。','フィールドごとの実型、nullable境界、業務スカラー長・HTML長・DB容量・SQLパラメータ領域を維持する。非nullable注釈だけで受信NULL排除を保証しない。',[ref('sources/Web/Inputs/StudentSearchInput.cs',7,22),ref('sources/Core/StudentNormalizer.cs',37,93),ref('sources/Core/SqlServerStudentService.cs',103,168),ref('sources/Infrastructure/WebHostSetup.cs',16,18)],[gen(39,61),gen(140,154),gen(905,919)]),
 preserve('S4-P02','表示名称も保守側の業務上限と型付き保存まで追い、基表NOT NULLとLEFT JOIN後NULLを分けている。','名称をDB容量だけの長さで説明せず、算出住所、本人電話、非表示の住所2・緊急電話・照合キーを維持する。',[ref('sources/Core/MasterMaintenanceService.cs',32,34),ref('sources/Core/MasterMaintenanceService.cs',73,74),ref('sources/Core/MasterMaintenanceService.cs',82),ref('sources/Core/MasterMaintenanceService.cs',113,115),ref('sources/Core/SqlServerStudentService.cs',79,90),ref('sources/Infrastructure/WebPresentation.cs',20)],[gen(202,217),gen(917,919),gen(947)]),
 preserve('S4-P03','UseはGate待機前後のGetと期待版照合を行い、取得前の取消をSQLやGate解放へ進めない。','Gate取得前・取得後finally・operation正常終了の期限延長を別の条件として保ち、DB await後の再Getや自動rollbackを追加しない。',[ref('sources/Infrastructure/SearchContextStore.cs',13,14),ref('sources/Infrastructure/WebStudentCoordinator.cs',7,15)],[gen(228,244),gen(456,488),gen(927,929)]),
 preserve('S4-P04','Pageの図と本文はWebFaultの元状態を保持し、サービス検証、所有状態拒否、SQL取消、後段再構築を別経路にしている。','合流点を一つのHTTP状態へ固定しない。一回の検索SNAPSHOTと一度だけの補正再検索、Resumeの保持Page維持も区別する。',[ref('sources/Web/Controllers/StudentsController.cs',18,19),ref('sources/Core/SqlServerStudentService.cs',107,108),ref('sources/Core/SqlServerStudentService.cs',160,170),ref('sources/Infrastructure/WebStudentCoordinator.cs',12,14),ref('sources/Infrastructure/WebPresentation.cs',23)],[gen(557,626),gen(727)]),
 preserve('S4-P05','Optionsは今回inputとLastResultを使い、期待版・Gate・期限延長・学生再検索を行わず、宣言済み別helperを公開JSON応答へ読み替えない。','不適合クラス解除、未所属の3値解除、通常フォーム全体HTML、未実行条件と成功済み条件を混同しない説明を維持する。',[ref('sources/Web/Controllers/StudentsController.cs',22),ref('sources/Infrastructure/WebStudentCoordinator.cs',16),ref('sources/Infrastructure/WebPresentation.cs',8,18),ref('sources/wwwroot/js/site.js',7,8)],[gen(506,555),gen(729,771),gen(983)]),
 preserve('S4-P06','ソース投影、参考設計モック、実画面撮影・外部HTML画像を別の出自として扱い、静的HTMLを実アプリ送信先へ接続していない。','source routeは説明用データに留め、fragmentの状態と権限を明示する。参考図や資料中リンクを、本書で新しく生成または検証した成果物にしない。',[ref('sources/Views/Students/Search.cshtml',4,8),ref('sources/Views/Shared/_Layout.cshtml',1),ref('sources/wwwroot/css/site.css',1),ref('reference-designs/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md',27,45)],[gen(63,134)]),
 preserve('S4-P07','保存非Savedと削除非Savedを分け、前者の今回input・旧Snapshotと後者のLoad再実行を区別している。','削除の再Loadへ投稿編集値・削除理由・元Resultが必ず保持されるとは書かない。Load内の後続状態確認と404による元Unknown案内の消失可能性を維持する。',[ref('sources/Web/Controllers/StudentsController.cs',25),ref('sources/Web/Controllers/StudentsController.cs',29,38),ref('sources/Core/SqlServerStudentService.cs',176,179)],[gen(773,833),gen(835,901)]),
 preserve('S4-P08','Savedだけが成功通知・303へ進み、DB確定、復帰GET、Flash Take、後段候補／描画／配信の成功を分けている。','編集開始時のReturnRevisionを最新へ補完せず、Unknown等を再送可能成功にしない。Take後の画面失敗で通知が表示されない可能性と、確定書込みの非復元を維持する。',[ref('sources/Web/Controllers/StudentsController.cs',8,11),ref('sources/Web/Controllers/StudentsController.cs',31,38),ref('sources/Infrastructure/FlashMessageStore.cs',6,9),ref('sources/Core/SqlServerStudentService.cs',319,329)],[gen(675,727),gen(835,901)])
]
assert sha(GEN)==sha(F/'generated/spec/detail/student-search.md')
result={'schema':'source-backed-writer-feedback/1','classification':'GENERATION_SAFE_SOURCE_BACKED_FEEDBACK',
 'reviewDocumentId':'SM-DET-STUDENT-SEARCH','reviewDocumentVersion':'4.0',
 'reviewDate':datetime.datetime.now(datetime.timezone.utc).isoformat(),'projectId':'test-project1',
 'profile':'CSharp_ASPNET','iteration':'20261013-focus-round-04',
 'builderInputPolicy':'Completed candidate, raw source and the same authorized training reference snapshot only. No protected selected rows, checklist, expected cells or scoring report read.',
 'provenance':{'generatedPath':GEN.relative_to(ROOT).as_posix(),'generatedSha256':sha(GEN),
  'sourceInputRoot':CAP.relative_to(ROOT).as_posix(),'sourceInputs':list(pins.values()),
  'checks':{'publishedEqualsFrozen':True,'everyReferencedSourceEqualsAuthorizedCapsule':True,
            'pointOrExpectedCellContentIncluded':False,'actualApplicationOrDbTestPerformed':False}},
 'sourceBackedFindings':findings,'existingCorrectBehaviors':correct,
 'validationScope':'Source/candidate/reference hashes and ranges only. Rendering and application/DB tests are separate; no semantic score or formal acceptance included.'}
p=OUT/'student-search-feedback.json';assert not p.exists()
p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'findings':len(findings),'preserve':len(correct),'sourcePins':len(pins),'sha256':sha(p)},ensure_ascii=False))
