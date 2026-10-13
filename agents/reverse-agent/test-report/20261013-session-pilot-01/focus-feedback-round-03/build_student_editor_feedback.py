"""Writer-safe notes, manually reviewed against only current MD and authorized source.

This builder reads neither scores nor checklists nor design reference documents.
It validates immutable source/document hashes and numbered evidence anchors.
It does not infer semantic findings from keywords or generate specification text.
"""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).with_name('student-editor-feedback.json')
GENERATED='test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-03/spec/detail/student-editor.md'
GENERATED_SHA='ae0961d287d2cea643605a2a83b9ad7d5f65683f214b55f001197d02149ca979'
SOURCE='agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted/sources'
PINS={
 'Program.cs':'d45c2b1b96fa1354706b0f4a8dcd4830c1f78c175b091919b0c3af0d44eb6e49',
 'Core/Contracts.cs':'0df616a1e6369675a0bc6997ea480726267070dcec8d31f4ec7eaf8395492916',
 'Core/JapaneseDateService.cs':'fe3ba2094f911da09b2fb0d5b2694006f347f2a2eb2e4944ac8f251cd265f847',
 'Core/StudentNormalizer.cs':'e2cad5e8b23fbbbe44ca03933432b371b4b3fe824432220b183cc922f838b71d',
 'Core/SqlServerStudentService.cs':'ae235c4a91ef2e1b7ed5fafb13b4f898e12cb38333e01b027c27b12d999b7560',
 'Core/MasterMaintenanceService.cs':'271674d65ae5d3d1d8b5537e0d243b01ce730f7d5cba033c69cdf24b6c06d4ef',
 'Views/Students/Edit.cshtml':'8a9f8ee01b5241be778f8f1b03819a62ab00502abba0b02e5e87a8035abf5b67',
 'Web/Inputs/StudentSaveInput.cs':'607b30560672b7b548a6ece29f6f4a47a2cadf68786d1fe8d265a0452d03fbb8',
 'Web/Controllers/StudentsController.cs':'cbbf397456a0c95cd5a7e33a2faabb06826451e5f24ac48d571283c88e8e3e31',
 'Infrastructure/SearchContextStore.cs':'7cc7e82c9a6bda7bf33ee374cad02348c1be2f40a6728aefe9b761dac0463bd2',
 'Infrastructure/EditorSnapshotStore.cs':'887e02443c77d43d175105a3411e46676c54e64d4a44e6cf07f133bb5da3a027',
 'Infrastructure/WebStudentCoordinator.cs':'358bc13a486d43b4e30404f12f32845060ea4e98d3979c64a03ed8cc11a7c962',
 'Infrastructure/WebHostSetup.cs':'1a873e7427fcbc16d3593d2eaaed5c4180e79625bff8819ce979eada8e3f0649',
 'Infrastructure/WebPresentation.cs':'3a78f67fca52749e10924cea48054055612404ae687f3dfac0817b6741ac7c26',
 'Infrastructure/FlashMessageStore.cs':'dc3a431e90dfb70b9055f7c47914a84182f6ca5f2db9d2156f60589fff7b5fd3',
 'database/001_schema.sql':'e6872d042fed6e1d795fde72e29adef5cecda6a0887348444ea905661de1178a',
 'database/002_seed.sql':'b4b6745e5c6e7d1ed3a22b07b2bb4607b5a6bf173ad08ba5bf32f0e4bb2322ee'
}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
loaded={}
for name,pin in PINS.items():
 path=ROOT/SOURCE/name
 assert sha(path)==pin,(name,'source SHA changed')
 loaded[name]=path.read_text(encoding='utf-8-sig').splitlines()
assert sha(ROOT/GENERATED)==GENERATED_SHA,'current generated SHA changed'
generated=(ROOT/GENERATED).read_text(encoding='utf-8-sig').splitlines()
checked=[]
def evidence(name,start,end,anchor):
 lines=generated if name is None else loaded[name]
 assert 1<=start<=end<=len(lines),(name,start,end)
 assert anchor in '\n'.join(lines[start-1:end]),(name,start,end,anchor)
 result={'path':GENERATED if name is None else SOURCE+'/'+name,'startLine':start,'endLine':end,'sha256':GENERATED_SHA if name is None else PINS[name]}
 checked.append(result)
 return result
g=lambda a,z,t:evidence(None,a,z,t)
s=lambda n,a,z,t:evidence(n,a,z,t)

findings=[
 {'findingId':'EDITOR-SOURCE-03-A','type':'source_behavior_documentation','title':'DB読取後の復帰Context再確認を別段階で示す',
  'description':'Loadはasync Coordinator.Editの完了後に復帰Contextをもう一度Getして検索版を読み、新Snapshotを作る。二度目の確認で拒否が発生した場合も、共通middlewareはWebFault.Statusを保持する。初回の認証・Context検査だけで後段の成否を保証せず、既存表示図の後段例外を503だけに固定しない。',
  'suggestedClarification':'初回Context確認、DB読取/Lookup、二度目Context.Get、Snapshot作成を図と結果説明で分ける。二度目のContext拒否はそのStatus、その他の対象外例外は共通応答という分岐を明記する。',
  'generatedEvidence':[g(262,266,'現在Revision'),g(315,319,'復帰検索版'),g(326,339,'未捕捉例外'),g(1011,1011,'WebFaultのStatus')],
  'sourceEvidence':[s('Web/Controllers/StudentsController.cs',25,25,'contexts.Get(context'),s('Infrastructure/WebStudentCoordinator.cs',17,17,'await service.GetAsync'),s('Infrastructure/SearchContextStore.cs',13,14,'WebFault(409'),s('Infrastructure/WebHostSetup.cs',23,23,'fault?.Status??503')]},
 {'findingId':'EDITOR-SOURCE-03-B','type':'clarify_cross_section_exception_path','title':'Resetのフォーム拒否経路を図からも参照できるようにする',
  'description':'Reset手順はFormGuardを呼び、共通説明は許可外・不正メタ情報・同名複数値の400拒否を記述している。Reset図の拒否状態列には400がないため、その図だけではフォーム拒否とID/Snapshot拒否の段階差が読めない。原入力復元やDB再読込の動作は変更しない。',
  'suggestedClarification':'Reset図にFormGuardを入口段階として置くか、400拒否は共通フォーム検査の説明へ従うと明示して、認証・ID・Snapshotの拒否と区別する。',
  'generatedEvidence':[g(722,726,'FormGuard'),g(732,742,'401・422・403・409'),g(1007,1007,'400で拒否')],
  'sourceEvidence':[s('Web/Controllers/StudentsController.cs',35,35,'await FormGuard'),s('Web/Controllers/StudentsController.cs',41,41,'WebFault(400'),s('Infrastructure/WebHostSetup.cs',23,23,'fault?.Status??503')]},
 {'findingId':'EDITOR-SOURCE-03-C','type':'verification_scope','title':'静的観測と受信・DBの実行確認の状態を明記する',
  'description':'新版はサービス引数NULLの例外とMVC受信の未確定部分を正確に分けている。起動入口やhealth応答だけではHTTPバインドやDB保存試験の完了を証明できない。文書末尾に、ソースから確定した処理、受信層で未確認の部分、実行証跡の有無を区別すると検証範囲が明確になる。',
  'suggestedClarification':'本文の欠落・空文字・空白・NULLの扱いは層別契約のまま保ち、HTTP/DB実行を確認済みとする場合は別の実行証跡を示す。証跡がない項目は未確認として記録し、ソース読解を実行合格へ読み替えない。',
  'generatedEvidence':[g(564,564,'MVC'),g(883,919,'NULL部品'),g(1023,1049,'未生成')],
  'sourceEvidence':[s('Program.cs',2,8,'app.Run'),s('Infrastructure/WebHostSetup.cs',16,18,'SuppressImplicitRequiredAttribute'),s('Infrastructure/WebHostSetup.cs',28,28,'not-tested'),s('Core/JapaneseDateService.cs',19,39,'input.Year.Normalize'),s('Core/JapaneseDateService.cs',52,59,'raw.Normalize'),s('Core/StudentNormalizer.cs',123,143,'catch (ArgumentException')]}
]

correct=[
 {'behaviorId':'EDITOR-PRESERVE-03-A','description':'業務19入力のDTO→Draft→正規化値→typed parameter→DB→再表示を保つ。任意NULL、条件付き必須、DB NULL可否、業務スカラー長と物理容量を分ける。',
  'generatedEvidence':[g(42,44,'19項目'),g(176,205,'DateOnly')],
  'sourceEvidence':[s('Web/Inputs/StudentSaveInput.cs',34,43,'new StudentDraft'),s('Core/StudentNormalizer.cs',119,159,'relationship_category'),s('Core/SqlServerStudentService.cs',30,38,'SqlDbType'),s('Core/SqlServerStudentService.cs',67,72,'DBNull.Value'),s('database/001_schema.sql',8,42,'date NULL')]},
 {'behaviorId':'EDITOR-PRESERVE-03-B','description':'日付のtype=date/DTO文字列、NFKC後ISO厳密変換、内部DateOnly、SQL date、再表示ISOを保つ。和暦Era完全一致と数値部NFKC後桁数を通常Text raw検査と区別し、NULL対象外例外を422へまとめない。',
  'generatedEvidence':[g(883,919,'NFKC後'),g(449,452,'日付NULL等')],
  'sourceEvidence':[s('Views/Students/Edit.cshtml',7,11,'type="date"'),s('Core/JapaneseDateService.cs',17,39,'era.Id == input.Era'),s('Core/JapaneseDateService.cs',52,59,'yyyy-MM-dd'),s('Core/StudentNormalizer.cs',47,57,'ScalarCount(raw)'),s('Core/SqlServerStudentService.cs',183,194,'yyyy-MM-dd')]},
 {'behaviorId':'EDITOR-PRESERVE-03-C','description':'ContextとSnapshotは同じ乱数関数を別に呼び、別キー/別辞書/別保有項目で保持する。検索版・学生期待版・確認キー・読込時Originalを分離する。',
  'generatedEvidence':[g(240,243,'別キー')],
  'sourceEvidence':[s('Infrastructure/SearchContextStore.cs',9,15,'Token()'),s('Infrastructure/EditorSnapshotStore.cs',7,11,'SearchContextStore.Token()'),s('Web/Controllers/StudentsController.cs',25,25,'ReturnRevision=returnRevision')]},
 {'behaviorId':'EDITOR-PRESERVE-03-D','description':'保護コードの停止/期間短縮拒否と、画面での新規選択可否/既存同値保持は別の判定である。名称・表示順・備考まで一律変更禁止にしない。学年候補には画面の例外がある。',
  'generatedEvidence':[g(225,232,'IsProtected'),g(950,950,'期間短縮')],
  'sourceEvidence':[s('Views/Students/Edit.cshtml',8,13,'c.CategoryId=="GRADE"'),s('database/002_seed.sql',14,22,'is_protected'),s('Core/MasterMaintenanceService.cs',105,115,'保護値の停止・期間短縮')]},
 {'behaviorId':'EDITOR-PRESERVE-03-E','description':'保存非成功の投稿Input/旧Snapshotによる再表示と、削除非SavedのLoadによる最新業務値/版/新Snapshot表示を分ける。削除は投稿編集値/削除理由を復元する保証を持たず、対象消失では後段404となり得る。',
  'generatedEvidence':[g(550,564,'投稿Input'),g(708,712,'投稿削除理由')],
  'sourceEvidence':[s('Web/Controllers/StudentsController.cs',28,37,'return await Load'),s('Infrastructure/WebStudentCoordinator.cs',17,19,'WebFault(404'),s('Core/SqlServerStudentService.cs',392,416,'Unknown')]},
 {'behaviorId':'EDITOR-PRESERVE-03-F','description':'確認は主体/セッション/対象/版/期限/業務19値/全候補IDと版/Busyへ結び、表示20件と照合全件を区別する。正常Commit後消費・Unknown無効化・未完了Busy解除と、ブラウザーキー消去を別にする。',
  'generatedEvidence':[g(243,244,'全候補'),g(574,606,'21件目以降'),g(626,632,'Role、Tab')],
  'sourceEvidence':[s('Core/SqlServerStudentService.cs',224,225,'HashCandidates'),s('Core/SqlServerStudentService.cs',274,290,'CompareExchange'),s('Core/SqlServerStudentService.cs',313,335,'WebConfirmations.TryRemove'),s('Infrastructure/WebHostSetup.cs',19,19,'webTokens:true'),s('Web/Controllers/StudentsController.cs',32,33,'Input.DuplicateToken')]},
 {'behaviorId':'EDITOR-PRESERVE-03-G','description':'NoChangeは最新DBとの正規化22値比較/明示Rollbackであり、学生DML・監査・版加算なし。Savedは正常Commit後だけ、Unknownは確定を断定せず検索確認を案内する。',
  'generatedEvidence':[g(211,218,'NoChange'),g(970,980,'commitAttempted')],
  'sourceEvidence':[s('Core/SqlServerStudentService.cs',260,263,'Outcome.NoChange'),s('Core/SqlServerStudentService.cs',292,323,'commitAttempted=true'),s('Core/SqlServerStudentService.cs',411,416,'unknown=writeStarted')]},
 {'behaviorId':'EDITOR-PRESERVE-03-H','description':'ResetはメモリOriginal複製、ReloadはDB全業務値/版/新Snapshotであり、復帰はApplied条件のResumeと読込時検索版を使う。ResumeはApplied.Pageを書き戻さず、FlashはResume後/Lookup前に消費する。',
  'generatedEvidence':[g(718,757,'Original'),g(765,805,'最新業務値'),g(813,879,'Applied.Page')],
  'sourceEvidence':[s('Web/Controllers/StudentsController.cs',35,35,'Copy(snapshot.Original)'),s('Web/Controllers/StudentsController.cs',24,25,'snapshots.Create'),s('Web/Controllers/StudentsController.cs',8,11,'flash.Take'),s('Infrastructure/WebStudentCoordinator.cs',11,14,'entry.Applied=SearchContextStore.Copy'),s('Infrastructure/SearchContextStore.cs',14,14,'request.ContextRevision'),s('Infrastructure/FlashMessageStore.cs',6,9,'TryRemove')]}
]
payload={'schema':'source-backed-writer-feedback/1','classification':'WRITER_SAFE_SOURCE_ONLY','reviewDocumentId':'SM-DET-STUDENT-EDITOR','generatedVersion':'3.0','reviewedAt':'2026-10-13','iteration':'20261013-focus-round-03','sourceBackedFindings':findings,'existingCorrectBehaviors':correct,'provenance':{'generatedPath':GENERATED,'generatedSha256':GENERATED_SHA,'sourceRoot':SOURCE,'sourcePins':[{'path':SOURCE+'/'+n,'sha256':v} for n,v in PINS.items()],'builderSha256':sha(Path(__file__)),'sourceAndCurrentGeneratedOnly':True,'numberedEvidenceChecks':len(checked),'priorJudgementsReused':False},'limitations':['静的ソース/本文の人手レビュー。HTTP受信/DB実行/実画面の承認を証明する資料ではない。','提案は記述の明確化であり、未接続APIや未観測のDB保証を追加しない。']}
serialized=json.dumps(payload,ensure_ascii=False,indent=2)+'\n'
for forbidden in ('evaluationId','originalPoints','awardedPoints','expectedCells','spec-eval','evaluator-only'):
 assert forbidden not in serialized,forbidden
OUT.write_text(serialized,encoding='utf-8')
print(json.dumps({'output':str(OUT),'sha256':sha(OUT),'builderSha256':sha(Path(__file__)),'findings':len(findings),'correctBehaviors':len(correct),'checkedEvidenceRanges':len(checked)},ensure_ascii=False))
