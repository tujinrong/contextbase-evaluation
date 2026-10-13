from pathlib import Path
import hashlib
import json

# Human source review supplies the statements. This builder binds identities,
# numbered references and byte hashes; it reads only the candidate and sources.
ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).parent
GENERATED = 'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-04/spec/detail/student-editor.md'
GEN_SHA = '071001104d8ce7b1174dfbdccb848e04980de1d021ddc7bcf1a724780d83235c'
SOURCE_BASE = 'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted/sources/'
PINS = {
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
 'database/002_seed.sql':'b4b6745e5c6e7d1ed3a22b07b2bb4607b5a6bf173ad08ba5bf32f0e4bb2322ee',
 'wwwroot/js/site.js':'74729845c175ed285ddf0b19140d8216e7a1df6141a8e2e11d3a39f87f5d27bd',
}

def sha(path):
 return hashlib.sha256(path.read_bytes()).hexdigest()

assert sha(ROOT/GENERATED) == GEN_SHA
for name, expected in PINS.items():
 assert sha(ROOT/SOURCE_BASE/name) == expected, name

def ref(path, a, z, digest):
 lines = (ROOT/path).read_text(encoding='utf-8-sig').splitlines()
 assert 1 <= a <= z <= len(lines), (path,a,z)
 return {'path':path,'startLine':a,'endLine':z,'sha256':digest}

def g(a,z=None):
 return ref(GENERATED,a,z or a,GEN_SHA)

def s(name,a,z=None):
 return ref(SOURCE_BASE+name,a,z or a,PINS[name])

findings = [
 {
  'findingId':'editor-context-success-merge',
  'severity':'major',
  'title':'非空復帰Contextの正常枝がNULL版の節点へ合流する',
  'observed':'新規・既存読込の図は、二度目Context.Getの成功枝をReturnRevision=NULLと記すSnapshot節点へ接続する。一方、同じ本文の手順は採取した版を保持すると正しく説明しており、図と手順が両立しない。これは学生の期待RowVersionではなく検索復帰用の版である。',
  'sourceBehavior':'LoadはContext省略時だけreturnRevisionをnullにする。非空時はawait Edit後のcontexts.Getから現在RevisionをInvariantCultureの十進文字列にし、モデルと独立したEditorSnapshotへ渡す。戻りリンクと保存後303はこの読込時版を使用する。',
  'suggestion':'NULL指定をContext省略枝に限定する。非空ContextのGet成功枝は採取版を保持する節点を経て、値を変更しない共通Snapshot作成へ合流させる。二度目Getの拒否、元Status保持、失敗時Snapshot未作成を維持する。再読込図と復帰版の移送も同じソースで確認する。',
  'generatedEvidence':[g(267,297),g(329,364),g(241,243)],
  'sourceEvidence':[s('Web/Controllers/StudentsController.cs',23,25),s('Infrastructure/EditorSnapshotStore.cs',7,9),s('Infrastructure/SearchContextStore.cs',13,14),s('Views/Students/Edit.cshtml',16),s('Web/Controllers/StudentsController.cs',38)],
 },
 {
  'findingId':'editor-rollback-table-delimiter',
  'severity':'major',
  'title':'確定判定表の縦棒がMarkdownセルを分裂させる',
  'observed':'Rollback・確定判定表のinline code内に未escapeの二つの縦棒がある。rawの式と結果はソースに一致するが、Markdown表の区切りとして扱われると式の後半と結果列を正しく表示できない。別段落のCommit試行後Unknown説明は正しい。',
  'sourceBehavior':'保存と削除は、書込開始後かつCommit試行済みまたはRollback未成功ならUnknown、それ以外ならSystemErrorとする。捕捉する例外型、Rollbackに使うCancellationToken.None、両結果のHTTP503を区別する。',
  'suggestion':'表セル内の縦棒を安全にescapeするか、同じ論理を区切り文字のない条件文で表す。最終HTMLと画像で式の両条件、Unknown/SystemErrorの対応、双方のHTTP状態が読めることを確認する。式、例外範囲、Commit時点、再送前の検索確認は変更しない。',
  'generatedEvidence':[g(1057,1069),g(590,603)],
  'sourceEvidence':[s('Core/SqlServerStudentService.cs',319,329),s('Core/SqlServerStudentService.cs',411,416),s('Infrastructure/WebPresentation.cs',23)],
 }
]

keep = [
 {
  'behaviorId':'typed-values-date-null-bind',
  'behavior':'フォーム原入力、19業務入力、生成値込み22保存値、typed SQL parameter、DTO nullableとDB NULL可否を別に説明する。緊急連絡先全消去の4列NULL、原入力と正規化後の値を保持する。日付は和暦4raw部品、内部DateOnly、DB date、画面表示の各層を分ける。元号IDはraw完全一致、数値部はNFKC後に桁数/ASCII正整数を検査する。通常日付エラーとNULL対象外例外、HTTP省略からNULLを保証できない境界を維持する。',
  'generatedEvidence':[g(176,205),g(211,214),g(974,1008),g(1043,1049)],
  'sourceEvidence':[s('Web/Inputs/StudentSaveInput.cs',9,60),s('Core/JapaneseDateService.cs',17,59),s('Core/StudentNormalizer.cs',37,57),s('Core/StudentNormalizer.cs',119,159),s('Core/SqlServerStudentService.cs',30,38),s('Core/SqlServerStudentService.cs',65,72),s('database/001_schema.sql',8,43)],
 },
 {
  'behaviorId':'independent-states-and-context-checks',
  'behavior':'SearchContextとEditorSnapshotは独立して乱数キーを発行し、主体/session/対象/期限を確認する。初回Context確認とasync DB読取後の二度目Getを分け、WebFaultの元Statusと非WebFault503を分ける。復帰版の正しい手順説明を維持し、今回指摘した図の合流だけを修正する。',
  'generatedEvidence':[g(239,245),g(257),g(267,274),g(329,336),g(387,389)],
  'sourceEvidence':[s('Infrastructure/SearchContextStore.cs',9,15),s('Infrastructure/EditorSnapshotStore.cs',7,11),s('Infrastructure/WebStudentCoordinator.cs',6,17),s('Web/Controllers/StudentsController.cs',25),s('Infrastructure/WebHostSetup.cs',23)],
 },
 {
  'behaviorId':'protected-code-and-selectable-options',
  'behavior':'保護コードの停止/期間短縮禁止と候補選択の可否を分ける。通常分類の既存同値保持、新規/変更時の有効期間、GRADE全値列挙と独立GRADE存在照会なしの現行を正確に保持する。',
  'generatedEvidence':[g(226,233),g(1025,1039),g(1115)],
  'sourceEvidence':[s('Core/MasterMaintenanceService.cs',105,115),s('Core/SqlServerStudentService.cs',196,216),s('Core/SqlServerStudentService.cs',344,383),s('Views/Students/Edit.cshtml',7,13),s('database/002_seed.sql',14,23)],
 },
 {
  'behaviorId':'save-failure-versus-delete-reload',
  'behavior':'保存非成功の投稿Input/旧Snapshotと、削除非成功後のLoadによる最新DB値/版/新Snapshotを別に説明する。削除理由/投稿業務値の復元を創作しない。再表示中のLookup/Load失敗が先の結果表示を妨げうること、WebFault状態保持を維持する。',
  'generatedEvidence':[g(590,609),g(762,764)],
  'sourceEvidence':[s('Web/Controllers/StudentsController.cs',28,38),s('Infrastructure/WebStudentCoordinator.cs',17,19),s('Infrastructure/WebHostSetup.cs',23)],
 },
 {
  'behaviorId':'confirmation-recheck-consumption',
  'behavior':'確認は19正規化入力と全候補ID/版に結び、画面には全件数と先頭20件の最小表示値だけを出す。再POSTで主体/session/対象/版/期限/hash/Busyと理由を再確認し、変更時キー失効、正常Commit後消費、Unknown無効化、非成功Busy解除を区別する。取消はブラウザー内だけで入力保持する。',
  'generatedEvidence':[g(619,679),g(244,245),g(401,445)],
  'sourceEvidence':[s('Core/SqlServerStudentService.cs',224,235),s('Core/SqlServerStudentService.cs',269,323),s('Views/Students/Edit.cshtml',14),s('wwwroot/js/site.js',3,6)],
 },
 {
  'behaviorId':'nochange-commit-unknown-delivery',
  'behavior':'最新DBとの22値比較によるNoChange、学生/監査の正常Commit、Unknown、Flash/303の作成と配信を別の境界として保つ。Commitの正常な戻り前にSavedを出さず、配信失敗で既確定保存を取り消したと説明しない。',
  'generatedEvidence':[g(582,586),g(590,609),g(1053,1075)],
  'sourceEvidence':[s('Core/SqlServerStudentService.cs',258,265),s('Core/SqlServerStudentService.cs',302,329),s('Core/SqlServerStudentService.cs',411,416),s('Web/Controllers/StudentsController.cs',31,38),s('Infrastructure/FlashMessageStore.cs',6,9)],
 },
 {
  'behaviorId':'reset-reload-formguard',
  'behavior':'ResetのFormGuard400を先行Authorize/CSRFと別段階に置き、ModelState.Clear後のOriginalコピーとLookupのみの処理を説明する。Reloadは最新業務値と期待版を一括取得する別操作で、版だけの自動差替えではない。未保存変更の取消/続行を維持する。',
  'generatedEvidence':[g(770,828),g(836,889),g(1096,1098)],
  'sourceEvidence':[s('Web/Controllers/StudentsController.cs',23,25),s('Web/Controllers/StudentsController.cs',35,41),s('Infrastructure/EditorSnapshotStore.cs',7,11),s('wwwroot/js/site.js',2,8),s('Infrastructure/WebHostSetup.cs',14,18)],
 },
 {
  'behaviorId':'page-resume-flash-order',
  'behavior':'検索復帰はApplied条件のResume再検索であり、結果の適用PageとContextのApplied.Pageへの書込を混同しない。読込時ReturnRevisionの照合、303の固定内部復帰先、Resume成功後のFlash消費と後段Lookup失敗を区別する。',
  'generatedEvidence':[g(897,968)],
  'sourceEvidence':[s('Web/Controllers/StudentsController.cs',8,11),s('Web/Controllers/StudentsController.cs',38),s('Infrastructure/WebStudentCoordinator.cs',14,21),s('Infrastructure/SearchContextStore.cs',13,15),s('Core/SqlServerStudentService.cs',156,170),s('Infrastructure/FlashMessageStore.cs',6,9)],
 }
]

feedback = {
 'schema':'source-backed-writer-feedback/1',
 'classification':'WRITER_SAFE_SOURCE_ONLY',
 'reviewDocumentId':'SM-DET-STUDENT-EDITOR',
 'generatedVersion':'4.0',
 'sourceBackedFindings':findings,
 'existingCorrectBehaviors':keep,
 'scope':'固定した第4稿Markdownと許可ソースの人手レビュー。本文訂正は生成側がソースで再確認する。',
 'notPerformed':['application_execution','database_execution','HTTP_model_binding_execution','native_visual_verification_by_this_reviewer'],
 'provenance':{
  'generated':{'path':GENERATED,'sha256':GEN_SHA},
  'sourcePins':[{'path':SOURCE_BASE+n,'sha256':h} for n,h in PINS.items()],
  'builder':{'path':Path(__file__).relative_to(ROOT).as_posix(),'sha256':sha(Path(__file__))},
  'lineAndShaChecksPassed':True,
  'semanticJudgementsHumanReviewed':True,
  'builderAssignsSemanticJudgements':False,
 },
}
payload=json.dumps(feedback,ensure_ascii=False,indent=2)+'\n'
for forbidden in ('evaluationId','originalPoints','awardedPoints','expectedCells','spec-eval','evaluator-only'):
 assert forbidden not in payload
target=OUT/'student-editor-feedback.json'
target.write_text(payload,encoding='utf-8')
print(json.dumps({'findings':len(findings),'preservedBehaviors':len(keep),'sourcePins':len(PINS),'feedbackSha256':sha(target),'builderSha256':sha(Path(__file__))},ensure_ascii=False))
