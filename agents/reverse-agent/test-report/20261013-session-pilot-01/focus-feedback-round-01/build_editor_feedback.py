"""Source + candidate audit for writer input. No scoring files are read."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
OUT=Path(__file__).resolve().parent
ROOT=OUT
while not (ROOT/'test-project1/srcs/CSharp_ASPNET').is_dir():
    assert ROOT.parent!=ROOT
    ROOT=ROOT.parent
SRC=ROOT/'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted/sources'
GEN=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-01/spec/detail/student-editor.md'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def source(path,start,end):
    p=SRC/path
    assert 1<=start<=end<=len(p.read_text(encoding='utf-8-sig').splitlines())
    return dict(path='sources/'+path,sha256=sha(p),startLine=start,endLine=end)
def generated(start,end):
    assert 1<=start<=end<=len(GEN.read_text(encoding='utf-8-sig').splitlines())
    return dict(path=GEN.relative_to(ROOT).as_posix(),sha256=sha(GEN),startLine=start,endLine=end)
def item(key,title,description,spans,refs):
    return dict(findingId=key,title=title,description=description,generatedEvidence=[generated(*x) for x in spans],sourceEvidence=refs)
def preserve(key,description,spans,refs):
    return dict(behaviorId=key,description=description,generatedEvidence=[generated(*x) for x in spans],sourceEvidence=refs)

findings=[
 item('RETURN-KEY','復帰キーと編集Snapshotキーの発行経路を個別に記載する',
  'Snapshotには32バイト乱数/64桁小文字hexの説明があるが、ReturnContextIdは期限/所有/状態項目だけで発行経路を記していない。SearchContextStore.Entry.Id=Token()とTokenの32byte乱数→小文字hex、および編集Snapshotが同じToken helperを使うことを、それぞれの独立した辞書キーへ対応付ける。キーの同じ形式を辞書や照合対象の同一性に読み替えない。',
  [(198,205)],[source('Infrastructure/SearchContextStore.cs',9,12),source('Infrastructure/EditorSnapshotStore.cs',7,11)]),
 item('CODE-PROTECTION','候補可否と保護フラグの役割を分けて説明する',
  'コード候補は有効性/期間/既存保持を説明しているがis_protectedの役割がない。seedの保護指定、LookupのIsProtected移送、マスタ保守の保護値に対する停止/期間短縮拒否を追跡し、学生画面の選択可否とは別責務であることを明確にする。保護フラグを学生画面の新規業務入力や学生保存列として追加しない。',
  [(185,192),(788,796)],[source('database/002_seed.sql',15,22),source('Core/SqlServerStudentService.cs',203,212),source('Core/MasterMaintenanceService.cs',105,113)]),
 item('UI-INTERNAL-BOUNDARY','処理中UIと確認辞書Busyを同じ内部状態にしない',
  'dirty/leaving/aria-busyと押下ボタン以外のdisabledはブラウザー内の補助制御である。押下ボタン再入拒否や要求連番による旧応答破棄はない。Web確認辞書のBusyはサーバーでトークン利用を排他する別項目である。本文の正しい実装限界を内部状態表にも対応させ、UI再入保証や応答世代を推定しない。参考設計にある追加保証は設計意図と明示して分ける。',
  [(194,208),(325,330),(362,370)],[source('wwwroot/js/site.js',2,9),source('Core/SqlServerStudentService.cs',19,29),source('Core/SqlServerStudentService.cs',274,283)]),
 item('MASTER-NAME-LENGTHS','候補名称にも業務長と物理容量を揃えて書く',
  'C-01のマスタ型説明はcode_name:nvarchar(24)とclass_name:nvarchar(36)を記している。DDLは別途12/18スカラー相当のCHECKを持つ。学生入力項目で確立したraw/正規化/業務長/物理領域/NULLの区別を候補名称にも適用し、LEFT JOIN欠損と物理列NOT NULLを区別する。',
  [(788,796)],[source('database/001_schema.sql',63,81),source('database/001_schema.sql',113,128),source('Core/SqlServerStudentService.cs',203,214)]),
 item('COMMON-PLAN','実装契約の分冊参照を計画全体と対応させる',
  '登録文書が説明する検索復帰/共通状態/DDL/配備の責務を、次工程で受け取る計画全体のID/path/roleへ対応させる。実在するソースの登録関係と生成文書の参照責務を区別し、未知のパスや生成済み状態は補完しない。UIモック、MDの検査、実行試験は別の根拠として扱い、試験未実施を消さない。',
  [(834,858),(918,924)],[source('Infrastructure/WebHostSetup.cs',13,24),source('database/003_web_permissions.sql',12,24)]),
]
behaviors=[
 preserve('FIELD-CHAIN','今回追加したUI/DTO→正規化命令→実DB列/型/NULL→typed parameter/Sizeの対応を維持する。DTO nullableやSizeを保存列のNULL/容量と置換しない。',[(97,179)],[source('Web/Inputs/StudentSaveInput.cs',7,60),source('Core/StudentNormalizer.cs',119,149),source('Core/SqlServerStudentService.cs',30,37),source('database/001_schema.sql',8,59)]),
 preserve('SAVE-VS-DELETE','Saveの非Saved応答は投稿Inputと旧Snapshotを使う。Deleteの非Saved結果はLoadでDB最新値/新Snapshotへ戻り、編集中入力と投稿理由を復元しない。削除済み等でLoadが404なら元結果より共通404が表に出る場合がある。この分岐を一律の失敗時入力保持へ変えない。',[(487,491),(619,623)],[source('Web/Controllers/StudentsController.cs',29,38),source('Infrastructure/WebStudentCoordinator.cs',17,19),source('Views/Students/Edit.cshtml',17,17)]),
 preserve('CONFIRM-TOKEN','接続WebはwebTokens=trueの確認辞書を使う。主体/セッション/対象/期待版/期限/業務Payload/全候補ID版/Busyを確認し、入力変更/cancelのクライアントキー消去とサーバーレコード消費を区別する。Snapshot/Context/Tabは確認レコード自体の照合項目ではない。',[(203,203),(490,565),(918,922)],[source('Infrastructure/WebHostSetup.cs',19,19),source('Core/SqlServerStudentService.cs',19,29),source('Core/SqlServerStudentService.cs',224,225),source('Core/SqlServerStudentService.cs',274,342),source('wwwroot/js/site.js',3,3)]),
 preserve('NOCHANGE-COMMIT','同内容保存NoChangeはROLLBACKしDML/監査/版加算しない。Commit正常だけSavedと成功303。UnknownはwriteStartedとcommitAttempted/rollback成否の条件で分類し、Open/Beginの外側例外を含めてSavedと偽装しない。',[(440,491),(619,623),(842,858)],[source('Core/SqlServerStudentService.cs',227,323),source('Core/SqlServerStudentService.cs',392,416),source('Web/Controllers/StudentsController.cs',38,38)]),
 preserve('RESET-RELOAD','ResetはSnapshot.Originalへ戻し、DB最新再取得のReload/Loadと区別する。SnapshotはGetで延長/消費しない。',[(629,666)],[source('Web/Controllers/StudentsController.cs',25,35),source('Infrastructure/EditorSnapshotStore.cs',7,11)]),
 preserve('SEATS','席は非削除01/02だけ、容量NULL無制限で0は無制限にしない。新しい席を得る操作、既存席保持、03/04の最終所属と変更時期間重なりを分け、画面人数を予約としない。',[(798,832)],[source('Core/SqlServerStudentService.cs',235,237),source('Core/SqlServerStudentService.cs',357,383),source('database/001_schema.sql',201,201)]),
 preserve('DATES-POSTAL','和暦入力のNumberはNFKC後4/2/2桁でありHTML maxlengthやrawスカラー制限から別に扱う。郵便番号はraw10→正規化7で保存し、設計上の表示形式を現行formatterの存在へ読み替えない。',[(103,124),(798,811)],[source('Core/JapaneseDateService.cs',17,59),source('Core/StudentNormalizer.cs',94,98),source('Views/Students/Edit.cshtml',7,9)]),
 preserve('RETURN-PAGE','SavedのDB確定と検索復帰表示は別。戻り版は読込時版で最新補完しない。Resumeは元Applied条件で再検索するがSQL用ページだけ補正し、Applied.Pageを更新しない。FlashはResume後/Lookup前に消費する。',[(782,784),(914,916)],[source('Web/Controllers/StudentsController.cs',8,11),source('Web/Controllers/StudentsController.cs',25,38),source('Infrastructure/WebStudentCoordinator.cs',14,14),source('Infrastructure/FlashMessageStore.cs',6,9)]),
]
payload=dict(schema='source-backed-writer-feedback/1',classification='WRITER_SAFE_SOURCE_ONLY',
 reviewDocumentId='SM-DET-STUDENT-EDITOR',projectId='test-project1',profile='CSharp_ASPNET',iteration='20261013-focus-round-01',
 createdAt=datetime.now(timezone.utc).isoformat(),provenance=dict(generatedPath=GEN.relative_to(ROOT).as_posix(),generatedSha256=sha(GEN),
 sourceRoot=SRC.relative_to(ROOT).as_posix(),sourceExecutionPerformed=False,criteriaOrOriginalExpectedCellsUsedAsFeedback=False),
 sourceBackedFindings=findings,existingCorrectBehaviors=behaviors,
 limits=['ソース/DDL/生成本文の読取りによる指摘。実DB・実機・ビルド試験未実施。',
 '追加の設計意図は既に許可された参考snapshotから執筆側が確認する。このJSONに期待セルや採点条件を転記しない。'])
text=json.dumps(payload,ensure_ascii=False,indent=2)+'\n'
for prohibited in ('evaluationId','awardedPoints','expectedSpecification','spec-eval/','evaluator-only/','originalCells','confirmedAwardedPoints'):
    assert prohibited not in text,prohibited
(OUT/'student-editor-feedback.json').write_text(text,encoding='utf-8')
print(json.dumps(dict(file='student-editor-feedback.json',sha256=sha(OUT/'student-editor-feedback.json'),findings=len(findings),correctBehaviors=len(behaviors)),ensure_ascii=False))
