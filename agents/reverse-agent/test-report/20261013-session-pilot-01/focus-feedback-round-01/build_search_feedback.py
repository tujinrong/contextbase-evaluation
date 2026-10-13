"""Writer-safe source audit. Reads source + candidate only, no grading criteria."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

OUT=Path(__file__).resolve().parent
ROOT=OUT
while not (ROOT/'test-project1/srcs/CSharp_ASPNET').is_dir():
    assert ROOT.parent!=ROOT
    ROOT=ROOT.parent
SRC=ROOT/'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted/sources'
GENERATED=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-01/spec/detail/student-search.md'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(path,start,end):
    p=SRC/path
    n=len(p.read_text(encoding='utf-8-sig').splitlines())
    assert 1<=start<=end<=n
    return dict(path='sources/'+path,sha256=sha(p),startLine=start,endLine=end)
def generated(start,end):
    assert 1<=start<=end<=len(GENERATED.read_text(encoding='utf-8-sig').splitlines())
    return dict(path=GENERATED.relative_to(ROOT).as_posix(),sha256=sha(GENERATED),startLine=start,endLine=end)
def finding(key,title,detail,spans,refs):
    return dict(findingId=key,title=title,description=detail,generatedEvidence=[generated(*v) for v in spans],sourceEvidence=refs)
def correct(key,detail,spans,refs):
    return dict(behaviorId=key,description=detail,generatedEvidence=[generated(*v) for v in spans],sourceEvidence=refs)

findings=[
 finding('SOURCE-LENGTHS','名称の業務上限と物理容量の対応が途中で省略される',
  '氏名/カナは両方を記載しているが、学年/在籍/都道府県の名称はcode_name:nvarchar(24)、クラス名称はclass_name:nvarchar(36)の容量に留まる。提示DDLはそれぞれ別のスカラー長CHECK（12と18）を持つ。同一の項目移送表で、業務長・UTF-16容量・NOT NULL・LEFT JOIN結果nullableを区別して全名称へ適用する。SQLパラメーターSizeやDTO nullableで代替しない。',
  [(158,165),(824,830)], [ref('database/001_schema.sql',63,81),ref('database/001_schema.sql',113,128),ref('Core/SqlServerStudentService.cs',74,91)]),
 finding('INTENT-DETAIL','設計意図の一部が差分表の短い名詞だけになる',
  '操作/欠損表示の意図欄が話題の列挙に留まり、操作後の遷移、表示値の算出、状態変化との対応が読み取れない。現行Search.cshtmlとPresentにはこれらの専用制御/位置算出がなく、現行動作として追加してはいけない。同じ利用者承認済み参考資料の設計意図を読み直し、意図・ソースで実装された挙動・未実装差を別々に具体化する。画面HTMLもどの層を描いているか明記する。',
  [(49,90),(170,172),(877,890)], [ref('Views/Students/Search.cshtml',2,8),ref('Infrastructure/WebStudentCoordinator.cs',21,21)]),
 finding('RESPONSE-BOUNDARY','状態更新の保護と画面応答の制御を明示的に分ける',
  '現行フォームが通常HTML送信で、fetch/AbortController/要求連番の旧応答破棄を持たない説明は正しい。GateとRevisionはEntryの状態更新を保護する。一方、設計意図の応答順説明は候補に限られており、検索HTML、ページHTML、候補HTMLの応答制御をどう区別しているか曖昧に残る。各経路の実装範囲を整理し、追加制御は承認済み参考設計の意図として限定する。',
  [(184,194),(249,258),(552,558),(882,890)], [ref('wwwroot/js/site.js',2,9),ref('Infrastructure/SearchContextStore.cs',13,15),ref('Web/Controllers/StudentsController.cs',13,22)]),
 finding('RESPONSIBILITY-LINKS','分冊間の責務を供給された計画と対応させる',
  '本文は登録画面/共通契約/DB定義を別冊の責務として扱うが、その参照文書との対応が未提示のままである。計画全体のID/path/roleを受け取った次の工程で既知の分冊へ対応させる。存在しないID/pathや文書生成済み状態を創作しない。根拠ソースとDDLは読取りに基づく仕様であり、実DBや実装試験の合格を示さない。',
  [(20,22),(892,896)], [ref('Infrastructure/WebHostSetup.cs',15,24),ref('database/001_schema.sql',187,200)]),
]
preserve=[
 correct('CRITERIA-LAYERS','rawの現在入力、成功済みApplied、SQLローカル正規化値を分ける。成功Search/PageだけAppliedを深い複製で置換し、ResumeはAppliedを置換しない。',[(26,47),(135,145),(186,194)],[ref('Infrastructure/WebStudentCoordinator.cs',7,15),ref('Core/SqlServerStudentService.cs',113,154)]),
 correct('OPTIONS-STATE','Optionsは学生検索/状態更新をせずLastResultを表示する。Gate、Revision照合、期限延長がない。既存成功一覧が再表示され得ることを保持する。',[(314,358)],[ref('Web/Controllers/StudentsController.cs',22,22),ref('Infrastructure/SearchContextStore.cs',13,14)]),
 correct('PAGE-RESUME','PageはApplied由来で件数/ソート変更時1ページ、最終有効ページを保持条件まで補正する。Resumeは元条件で再検索するがSQL用ページだけ補正しApplied.Pageを変えない。',[(362,419),(469,514)],[ref('Infrastructure/WebStudentCoordinator.cs',11,14),ref('Core/SqlServerStudentService.cs',160,164)]),
 correct('STATE-ID-VERSION','ID64hex、主体/セッション/期限、非空Tabのみ、Gate内期待版を区別する。省略版を最新版で補完しない。Index/ResumeのTab不渡しを消さない。',[(135,141),(178,194),(887,890)],[ref('Infrastructure/SearchContextStore.cs',9,15),ref('Web/Controllers/StudentsController.cs',8,22)]),
 correct('QUERY-AND-NULL','非削除必須、任意条件AND、電話二列OR、空在籍配列は条件なし、未所属だけIS NULL。COUNTとPAGEに同値typed bind、TOP10001は上限検出値である。',[(685,818)],[ref('Core/SqlServerStudentService.cs',103,170)]),
 correct('FAILURE-PHASES','局所失敗は空一覧用応答であってApplied/LastResult削除ではない。Get/SQL/候補/描画の失敗と状態確定後の応答失敗を分け、成功応答配信を保証しない。',[(306,308),(354,358),(854,873)],[ref('Web/Controllers/StudentsController.cs',13,22),ref('Infrastructure/WebStudentCoordinator.cs',7,15),ref('Infrastructure/WebHostSetup.cs',23,23)]),
 correct('SAVE-DELETE-BOUNDARY','Save失敗とDelete失敗を同じ入力保持にしない。Deleteは非SavedならLoadでDB最新版/新Snapshotへ戻り、入力した削除理由を復元しない。',[(665,673)],[ref('Web/Controllers/StudentsController.cs',29,38),ref('Views/Students/Edit.cshtml',17,17)]),
 correct('COMMIT-UNKNOWN','Saved確定だけ自動復帰と成功通知へ進む。NoChange/確認要求/Conflict/UnknownはSavedに読み替えない。UnknownのwriteStarted/commitAttempted/rollback失敗条件とDB処理外のOpen/Beginを保持する。',[(613,673)],[ref('Core/SqlServerStudentService.cs',227,323),ref('Core/SqlServerStudentService.cs',392,416),ref('Web/Controllers/StudentsController.cs',38,38)]),
]
payload=dict(schema='source-backed-writer-feedback/1',classification='WRITER_SAFE_SOURCE_ONLY',
 reviewDocumentId='SM-DET-STUDENT-SEARCH',createdAt=datetime.now(timezone.utc).isoformat(),
 projectId='test-project1',profile='CSharp_ASPNET',iteration='20261013-focus-round-01',
 provenance=dict(generatedPath=GENERATED.relative_to(ROOT).as_posix(),generatedSha256=sha(GENERATED),
  sourceRoot=SRC.relative_to(ROOT).as_posix(),sourceExecutionPerformed=False,criteriaOrOriginalExpectedCellsUsedAsFeedback=False),
 sourceBackedFindings=findings,existingCorrectBehaviors=preserve,
 limits=['本文/ソースの読み取りによる指摘。実DB・実機・ビルド試験未実施。',
  '設計意図は既に許可された参考snapshotから執筆側が読み直す。ここに正解セルや採点条件を転記しない。'])
text=json.dumps(payload,ensure_ascii=False,indent=2)+'\n'
for prohibited in ('evaluationId','awardedPoints','expectedSpecification','spec-eval/','evaluator-only/','originalCells','confirmedAwardedPoints'):
    assert prohibited not in text,prohibited
(OUT/'student-search-feedback.json').write_text(text,encoding='utf-8')
print(json.dumps(dict(file='student-search-feedback.json',sha256=sha(OUT/'student-search-feedback.json'),findings=len(findings),correctBehaviors=len(preserve)),ensure_ascii=False))
