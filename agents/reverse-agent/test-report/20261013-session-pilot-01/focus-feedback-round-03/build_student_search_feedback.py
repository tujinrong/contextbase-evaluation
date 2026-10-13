"""Serialize current-document source-only notes; no evaluation input is loaded."""
from pathlib import Path
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[5]
CAP=ROOT/'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
GEN=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-03/spec/detail/student-search.md'
EXPECTED_GEN='370fcc8b85803fe167d0b7148e5e612e657ee6a8c9fcefca77d63a89af6c6777'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(GEN)==EXPECTED_GEN
lines=GEN.read_text(encoding='utf-8-sig').splitlines()
meta=json.loads(re.fullmatch(r'<!-- spec-meta: (.+) -->',lines[0]).group(1))
assert meta['documentId']=='SM-DET-STUDENT-SEARCH' and meta['version']=='3.0'
names=['Program.cs','Web/Controllers/StudentsController.cs','Web/Inputs/StudentSearchInput.cs',
       'Core/Contracts.cs','Core/SqlServerStudentService.cs','Core/StudentNormalizer.cs',
       'Core/JapaneseDateService.cs','Core/MasterMaintenanceService.cs',
       'Infrastructure/WebStudentCoordinator.cs','Infrastructure/WebPresentation.cs',
       'Infrastructure/SearchContextStore.cs','Infrastructure/WebHostSetup.cs',
       'Infrastructure/EditorSnapshotStore.cs','Infrastructure/FlashMessageStore.cs',
       'Views/Students/Search.cshtml','Views/Students/Edit.cshtml','wwwroot/js/site.js',
       'wwwroot/css/site.css','database/001_schema.sql']
manifest=json.loads((CAP/'manifest.json').read_text(encoding='utf-8-sig'))
expected={x['path']:x['sha256'] for x in manifest['files']}
loaded={};pins=[];count=0
for n in names:
    p=CAP/'sources'/n
    assert sha(p)==expected[n]
    loaded[n]=p.read_text(encoding='utf-8-sig').splitlines()
    pins.append({'path':'sources/'+n,'sha256':sha(p),'bytes':p.stat().st_size})
def s(n,a,b=None,*anchors):
    global count
    b=a if b is None else b
    assert 1<=a<=b<=len(loaded[n])
    assert all(x in '\n'.join(loaded[n][a-1:b]) for x in anchors),(n,a,b,anchors)
    count+=1
    return {'path':'sources/'+n,'startLine':a,'endLine':b,'sha256':expected[n]}
def g(a,b=None,*anchors):
    global count
    b=a if b is None else b
    assert 1<=a<=b<=len(lines)
    assert all(x in '\n'.join(lines[a-1:b]) for x in anchors),(a,b,anchors)
    count+=1
    return {'path':GEN.relative_to(ROOT).as_posix(),'startLine':a,'endLine':b,'sha256':EXPECTED_GEN}

findings=[
    {'findingId':'self-contained-in-scope-comparison','kind':'clarify_document_responsibility',
     'observation':'参考設計との対比表は、追加表示・操作を短い主題名として示し、詳細を未生成の関連計画へ分担する。現行ソースのフォーム、描画値、遷移先、欠落機能は別々に追跡できるが、読者が本画面内の設計意図と現行責務を判断する説明は主題名だけでは薄い。',
     'suggestedAction':'本画面内の説明について、対象、条件、操作または表示、結果、担当層を保ち、未生成リンクを理由に省略しない。ソースの観測と許可参考資料の意図を明示して分け、実装にない条件・算式・遷移URLを観測済み動作へ追加しない。',
     'sourceEvidence':[s('Views/Students/Search.cshtml',4,8),s('Infrastructure/WebStudentCoordinator.cs',21,21),s('Web/Controllers/StudentsController.cs',21,25)],
     'generatedEvidence':[g(955,969,'追加表示・操作'),g(971,995,'未生成')]},
    {'findingId':'layout-and-artifact-origin','kind':'clarify_artifact_boundary',
     'observation':'概要のHTMLはViewer未検索の現行ソース投影で、ルート情報をdata属性に保持し送信を止めている。これは実機取得画像や参考設計の配置を表示したものではない。本文内の差分説明もその区別を明記している。',
     'suggestedAction':'静的ソース投影、参考設計の比較用配置、描画結果、実機画像の目的・出自・検査状態をそれぞれ説明する。関連描画成果物を示す場合は実在する成果物を参照し、未生成のリンクや静的投影を実機検証の証拠にしない。',
     'sourceEvidence':[s('Views/Students/Search.cshtml',3,8),s('wwwroot/css/site.css',1,1)],
     'generatedEvidence':[g(61,118,'静的投影','実画面撮影ではない'),g(969,969,'現行ソース')]},
    {'findingId':'verification-responsibility-and-future-checks','kind':'clarify_verification_responsibility',
     'observation':'関連文書の計画やソース分岐は実行結果を示さない。起動コードが存在しても業務入力やDB結果の往復確認を証明せず、healthもdatabase=not-testedを返す。',
     'suggestedAction':'ソース解析・文書検査・描画確認・アプリ/DB実行確認の責務と実施状態を分ける。将来の確認候補は本文の入力→DTO→変換→SQL→再表示に対応付け、境界値、拒否、後段例外、復帰と通知の確認範囲を明記する。実行証拠なしに合格を主張しない。',
     'sourceEvidence':[s('Program.cs',2,8,'app.Run()'),s('Infrastructure/WebHostSetup.cs',28,28,'database="not-tested"'),s('Core/SqlServerStudentService.cs',103,170),s('Web/Controllers/StudentsController.cs',8,22)],
     'generatedEvidence':[g(884,949),g(971,997,'計画')]},
]
correct=[
    {'behaviorId':'page-status-and-second-search','behavior':'Page図は所有403、状態409、サービス検証422を可変e.Statusの合流点へ接続し、本文と一致する。最終頁への一度の再検索は別接続・別SNAPSHOTである。',
     'preserve':'同じ再表示先でもHTTP状態を固定せず、返却後描画やcatch内再構築の例外を再捕捉した保証に変えない。',
     'sourceEvidence':[s('Web/Controllers/StudentsController.cs',18,19),s('Infrastructure/WebStudentCoordinator.cs',11,12),s('Infrastructure/WebStudentCoordinator.cs',20,20),s('Infrastructure/WebPresentation.cs',23,23)],
     'generatedEvidence':[g(538,613,'入力検証422','HTTP状態を固定しない')]},
    {'behaviorId':'date-reception-conversion-display','behavior':'日付のネイティブ入力、バインド後文字列、厳密ISO変換、DateOnly比較、型付きdate、再表示を分けている。参考設計の表示形式を実在フォーマッターと扱わない。',
     'preserve':'HTTP値と最終DTOの同一性、ブラウザー表示ロケール、独自整形の実装保証を追加せず、片側/包含/不正拒否を維持する。',
     'sourceEvidence':[s('Views/Students/Search.cshtml',5,5),s('Web/Inputs/StudentSearchInput.cs',17,22),s('Core/JapaneseDateService.cs',52,59),s('Core/SqlServerStudentService.cs',67,72),s('Core/SqlServerStudentService.cs',120,122)],
     'generatedEvidence':[g(134,135),g(884,900)]},
    {'behaviorId':'raw-and-null-boundaries','behavior':'非nullable注釈をNULL除外の実行保証にせず、Normalizerへ届いたraw、任意空、ModelState、正規化値を区別する。在籍配列NULLのサービス単体例外と、フォームキー省略時の空配列補正を分ける。',
     'preserve':'直接サービス引数のNULL経路をHTTPフォームで確認済みの動作に拡張せず、catchが受ける例外型の範囲を維持する。',
     'sourceEvidence':[s('Web/Controllers/StudentsController.cs',13,16),s('Infrastructure/WebHostSetup.cs',16,18),s('Core/SqlServerStudentService.cs',111,117),s('Core/SqlServerStudentService.cs',169,170),s('Core/StudentNormalizer.cs',47,57)],
     'generatedEvidence':[g(37,59),g(904,908)]},
    {'behaviorId':'business-length-db-capacity-and-join','behavior':'保守入力の業務上限、DDL容量/CHECK、SQL Size、LEFT JOIN後のnullableを分け、表示名称の保存側も追跡する。',
     'preserve':'CodeName12/ClassName18等を容量24/36へ拡張せず、基表NOT NULLをJOIN結果保証にしない。用途分類＋値の結合と行保持を維持する。',
     'sourceEvidence':[s('Core/MasterMaintenanceService.cs',33,33),s('Core/MasterMaintenanceService.cs',82,82),s('database/001_schema.sql',63,81),s('database/001_schema.sql',113,128),s('Core/SqlServerStudentService.cs',79,90)],
     'generatedEvidence':[g(190,196),g(904,914)]},
    {'behaviorId':'options-and-state-read-boundary','behavior':'Optionsは今回inputとLastResultで全候補から再描画し、学生検索、期待版照合、Gate、期限更新をしない。不適合クラスを解除し、未反映を通知する。',
     'preserve':'旧LastResultの再提示を今回条件の結果や一括保護読取りへ変えず、正規化しない候補比較とSearch整合検査を分ける。',
     'sourceEvidence':[s('Web/Controllers/StudentsController.cs',22,22),s('Infrastructure/SearchContextStore.cs',9,14),s('Core/SqlServerStudentService.cs',197,216)],
     'generatedEvidence':[g(485,530)]},
    {'behaviorId':'context-version-resume-and-flash','behavior':'所有/セッション/期限/非空Tab、厳密期待Revision、未検索復帰、元Applied再検索、SQL取得pageと提示page、Flash消費位置を分けている。',
     'preserve':'省略版を最新版へ補完せず、期限切れ自動初期化や保存行の特別追加を保証しない。DB確定と復帰HTMLの到達を分ける。',
     'sourceEvidence':[s('Infrastructure/SearchContextStore.cs',9,15),s('Infrastructure/WebStudentCoordinator.cs',14,14),s('Infrastructure/WebStudentCoordinator.cs',21,21),s('Web/Controllers/StudentsController.cs',8,11),s('Infrastructure/FlashMessageStore.cs',6,9)],
     'generatedEvidence':[g(163,178),g(665,711)]},
    {'behaviorId':'save-delete-and-commit-boundaries','behavior':'通常保存の非成功は投稿Input、削除非Savedは再Loadの最新値/新Snapshotであり、削除理由を明示復元しない。NoChange/UnknownをSavedにせず、commit後だけ303と確定通知へ進む。',
     'preserve':'削除再Loadで404等が元の結果に代わる可能性、確定後復帰失敗でDBを戻さないこと、Open/Beginが対象catch外であることを維持する。',
     'sourceEvidence':[s('Web/Controllers/StudentsController.cs',25,38),s('Infrastructure/WebStudentCoordinator.cs',17,17),s('Core/SqlServerStudentService.cs',240,243),s('Core/SqlServerStudentService.cs',313,329),s('Core/SqlServerStudentService.cs',409,416)],
     'generatedEvidence':[g(825,880)]},
    {'behaviorId':'inert-projection-and-unconnected-helpers','behavior':'静的HTMLの原ルートはdata属性、全buttonはtype=button、アプリ内リンクは解決する文書fragmentへ変えたと明示する。未接続Options helperを公開JSON APIと扱わず、三つの状態ストアを別辞書として扱う。',
     'preserve':'静的閲覧を業務送信へ接続せず、収録コードにない永続化/暗号化/プロセス間共有をDDL列から追加しない。',
     'sourceEvidence':[s('Views/Students/Search.cshtml',4,8),s('Web/Controllers/StudentsController.cs',22,22),s('Infrastructure/WebStudentCoordinator.cs',16,16),s('Infrastructure/SearchContextStore.cs',9,15),s('Infrastructure/EditorSnapshotStore.cs',7,11),s('Infrastructure/FlashMessageStore.cs',6,9)],
     'generatedEvidence':[g(67,116),g(759,759),g(997,997)]},
]
data={'schema':'source-backed-writer-feedback/1','classification':'WRITER_SAFE_SOURCE_ONLY',
      'reviewDocumentId':meta['documentId'],'reviewDocumentVersion':meta['version'],
      'reviewDate':'2026-10-13','projectId':'test-project1','profile':'CSharp_ASPNET','iteration':'20261013-focus-round-03',
      'builderInputPolicy':'Only this current generated MD, capsule manifest and explicit authorized sources are read as inputs.',
      'provenance':{'generatedPath':GEN.relative_to(ROOT).as_posix(),'generatedSha256':EXPECTED_GEN,
          'sourceInputRoot':CAP.relative_to(ROOT).as_posix(),'sourceInputs':pins,
          'checks':{'inputSha256Matches':True,'evidenceLineRangesAndAnchorsChecked':True,'sourceFilesChecked':len(pins),
                    'generatedFilesChecked':1,'evidenceRangesChecked':count}},
      'sourceBackedFindings':findings,'existingCorrectBehaviors':correct,
      'validationScope':'Source/document review only. This feedback does not prove rendered-image fidelity or application/DB execution.'}
out=Path(__file__).with_name('student-search-feedback.json')
assert not out.exists()
out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'output':out.relative_to(ROOT).as_posix(),'sha256':sha(out),'generatedSha256':EXPECTED_GEN,
                  'sourceFiles':len(pins),'evidenceRanges':count},ensure_ascii=False))
