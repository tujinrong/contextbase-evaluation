from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[5]
SAFE_ROOT=Path(__file__).resolve().parent
GEN='test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-05/spec/detail/student-editor.md'
GEN_SHA='5cec039f58141cbac0318ca8b937336fcc9234179b066f72a77083b71e6d81a7'
CAPSULE='agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted/'
# Only current candidate, whitelisted raw sources, and the already-authorized
# design inputs are read. Statements were independently reviewed by a human.
SOURCE_PINS={
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
 'Infrastructure/RequestIdentity.cs':'f70582b3ca8d46663514dd7bdfd46d99a1ce83d53b2ae2d7e295ab76817bf62b',
 'database/001_schema.sql':'e6872d042fed6e1d795fde72e29adef5cecda6a0887348444ea905661de1178a',
 'database/002_seed.sql':'b4b6745e5c6e7d1ed3a22b07b2bb4607b5a6bf173ad08ba5bf32f0e4bb2322ee',
 'wwwroot/js/site.js':'74729845c175ed285ddf0b19140d8216e7a1df6141a8e2e11d3a39f87f5d27bd',
}
DESIGN_PINS={
 '詳細仕様書/CSharp_ASPNET/02_学生登録画面.md':'ebf7afb72d8664b951853176859ffb6df99e797047a80bb837cd0c3782e2609e',
 '基本設計書/02_学生登録画面.md':'ec2cb1e42fd22637d43cd13c52fc1da4ab2a0bf7cb18246aef10a5aec6f39c0d',
}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(ROOT/GEN)==GEN_SHA
for n,h in SOURCE_PINS.items():assert sha(ROOT/CAPSULE/'sources'/n)==h,n
for n,h in DESIGN_PINS.items():assert sha(ROOT/CAPSULE/'reference-designs'/n)==h,n

def ref(path,a,z,h):
 assert 1<=a<=z<=len((ROOT/path).read_text(encoding='utf-8-sig').splitlines())
 return {'path':path,'startLine':a,'endLine':z,'sha256':h}
def g(a,z=None):return ref(GEN,a,z or a,GEN_SHA)
def s(n,a,z=None):return ref(CAPSULE+'sources/'+n,a,z or a,SOURCE_PINS[n])
def design(a,z=None,n='詳細仕様書/CSharp_ASPNET/02_学生登録画面.md'):
 return ref(CAPSULE+'reference-designs/'+n,a,z or a,DESIGN_PINS[n])

findings=[
 {
  'findingId':'editor-document-display-intent',
  'findingKind':'source-design-documentation',
  'severity':'major',
  'title':'表示意図の具体定義を現行加工の説明と分ける',
  'observed':'新稿は郵便の保存値復元、在籍日付のISO移送とネイティブ入力を正確に示す。一方、設計上の表示形式を現行加工へ置き換えないという一般文だけでは、本書を読む開発者が許可設計資料の具体的な表示意図を確認できない。実装加工がないという否定説明と、採用する設計上の表示定義は異なる。',
  'suggestion':'許可設計資料を直接読み、対象項目ごとに入力表現・内部値・保存値・設計表示を並べる。設計意図を再掲するときも、現行Viewがその表示を保証しているとは書かない。仕様の採用判断と実装差を明確に残す。',
  'generatedEvidence':[g(185),g(191,193),g(1053,1064),g(1204)],
  'sourceEvidence':[s('Core/SqlServerStudentService.cs',183,194),s('Views/Students/Edit.cshtml',9,11),s('Core/JapaneseDateService.cs',52,59)],
  'authorizedDesignEvidence':[design(93),design(99,101)],
 },
 {
  'findingId':'editor-document-boundaries-responsibility',
  'findingKind':'source-design-documentation',
  'severity':'major',
  'title':'画面の入出力境界と文書責務を自己完結させる',
  'observed':'Controller・Coordinator・サービスの説明と未生成文書計画はあるが、業務入出力の境界と、実装時に本書・共通契約・DB定義・規約が担当する具体内容を一緒に確認できる説明が不足する。文書計画に名前があることと、当該画面の契約が本書に定義されていることを分ける必要がある。',
  'suggestion':'実際の画面要求/表示、学生の読書き、マスター参照、監査、一時ストアについて方向と責務をまとめる。許可設計資料の対象範囲も直接確認し、本書が定義する項目・イベントと共通文書へ委ねる契約を区別する。別文書が未生成でも必要な本画面説明を具体化する。',
  'generatedEvidence':[g(15,50),g(1206,1233)],
  'sourceEvidence':[s('Web/Controllers/StudentsController.cs',23,38),s('Core/SqlServerStudentService.cs',196,216),s('Core/SqlServerStudentService.cs',227,324),s('Infrastructure/EditorSnapshotStore.cs',7,11)],
  'authorizedDesignEvidence':[design(16,25),design(47,81),design(789,795),design(14,24,'基本設計書/02_学生登録画面.md')],
 },
 {
  'findingId':'editor-document-verification-responsibility',
  'findingKind':'source-design-documentation',
  'severity':'major',
  'title':'契約の読取りと実装工程の検証責務を分けて記載する',
  'observed':'受信・日付・排他・Commit・配信の境界は詳述するが、許可設計資料が実装工程へ要求する確認と、今回実行していない範囲を読者が対応付けられる責務説明がない。未生成報告への分担や実行結果へ読み替えない注意だけでは、誰が何を確認するかが具体化されない。',
  'suggestion':'許可設計資料から実装工程の確認責務を直接整理し、入力/内部値/DB/再表示の往復と、ソース上の異常段階を対応付ける。受信バインド、サービスNULL経路、取消/確定判定、保存後通知について、今後の実行確認と現在の未実施状態を明確に区別する。未実行の成功を追加しない。',
  'generatedEvidence':[g(263),g(1064),g(1115,1151),g(1180),g(1190),g(1208)],
  'sourceEvidence':[s('Web/Controllers/StudentsController.cs',29,38),s('Core/JapaneseDateService.cs',19,39),s('Core/SqlServerStudentService.cs',302,329),s('Infrastructure/WebHostSetup.cs',16,28)],
  'authorizedDesignEvidence':[design(743,753),design(791,793)],
 }
]

keep=[
 {'behaviorId':'typed-raw-date-null-bind','behavior':'19業務入力と生成値込み保存値、typed SQL parameters、raw Unicodeスカラー/物理容量、DTO nullable/DB NULLを分ける。和暦4rawと内部date/表示の層、元号完全一致と数値部NFKC後形式、通常FieldErrorと数値部NULLの一般例外を保持する。','generatedEvidence':[g(44,48),g(180,209),g(1030,1066),g(1101,1107)],'sourceEvidence':[s('Web/Inputs/StudentSaveInput.cs',9,60),s('Core/JapaneseDateService.cs',17,59),s('Core/StudentNormalizer.cs',37,57),s('Core/StudentNormalizer.cs',119,159),s('Core/SqlServerStudentService.cs',30,38),s('Core/SqlServerStudentService.cs',67,72),s('database/001_schema.sql',8,43)]},
 {'behaviorId':'independent-keys-return-revision','behavior':'ContextとSnapshotの独立乱数キー、所有/session/期限/対象照合を保持する。前後Context.Getを分け、省略時NULLと採取成功版の保持を新規/既存/Reloadの図でも分離する。NULL SnapshotIdがストアへ到達した場合と非NULL不在の拒否を分け、HTTP省略から具体値を保証しない。','generatedEvidence':[g(245,247),g(261,263),g(273,303),g(335,370),g(879,901)],'sourceEvidence':[s('Infrastructure/SearchContextStore.cs',9,15),s('Infrastructure/EditorSnapshotStore.cs',7,11),s('Infrastructure/WebStudentCoordinator.cs',6,17),s('Web/Controllers/StudentsController.cs',25,37),s('Infrastructure/WebHostSetup.cs',23)]},
 {'behaviorId':'protected-versus-selectable','behavior':'保護コードの停止/期間短縮拒否と候補選択の可否を分ける。既存同値保持と新規/変更時の期間、GRADE全値列挙/disabledなし/独立存在照会なしの現行を正確に保持し、設計意図へ混ぜない。','generatedEvidence':[g(230,237),g(585,600),g(1083,1097),g(1196)],'sourceEvidence':[s('Core/MasterMaintenanceService.cs',105,115),s('Views/Students/Edit.cshtml',7,13),s('Core/SqlServerStudentService.cs',196,216),s('Core/SqlServerStudentService.cs',344,383),s('database/002_seed.sql',14,84)]},
 {'behaviorId':'save-failure-delete-reload','behavior':'保存非成功の投稿Input/旧Snapshotと、削除非Saved後LoadのDB最新値/期待版/新Snapshotを区別する。後段Lookup/Load失敗が結果表示を妨げうること、入口例外は再表示/再Load前に止まることを保持する。','generatedEvidence':[g(610,629),g(710,719),g(790,792),g(1200)],'sourceEvidence':[s('Web/Controllers/StudentsController.cs',28,38),s('Infrastructure/WebStudentCoordinator.cs',17,19),s('Infrastructure/WebHostSetup.cs',23)]},
 {'behaviorId':'confirmation-full-recheck','behavior':'確認を19正規化入力と全候補ID/版に結び、画面全件数と先頭20最小項目を区別する。要求開始時点で期限/所有/session/対象/期待版/hash/Busyと理由を再照合し、変更時キー消去、正常Commit消費、Unknown無効化、未完了Busy解除、取消要求なしを保持する。','generatedEvidence':[g(248,249),g(639,700),g(407,454)],'sourceEvidence':[s('Core/SqlServerStudentService.cs',19,29),s('Core/SqlServerStudentService.cs',224,335),s('Views/Students/Edit.cshtml',14),s('wwwroot/js/site.js',3,6)]},
 {'behaviorId':'nochange-commit-unknown','behavior':'最新DBの保存値比較によるNoChangeと理由のみ変更、学生/監査の正常Commit、先行422/409catchと一般catchのUnknown条件を分ける。Rollbackが成功してもCommit試行後の一般catchはUnknown。表は縦棒のない条件文を保ち、Flash/303配信と既確定保存を混同しない。','generatedEvidence':[g(602,629),g(1115,1157)],'sourceEvidence':[s('Core/SqlServerStudentService.cs',258,265),s('Core/SqlServerStudentService.cs',302,329),s('Core/SqlServerStudentService.cs',411,416),s('Web/Controllers/StudentsController.cs',31,38),s('Infrastructure/FlashMessageStore.cs',6,9)]},
 {'behaviorId':'reset-reload-guard','behavior':'Resetは先行filter後のFormGuard400、ID/ストア照合、ModelState.Clear、Original複製、Lookupだけの処理を保持する。Reloadは最新業務値/期待版を一括取得し、復帰版成功保持とNULL Snapshot例外の別段階を明記する。','generatedEvidence':[g(802,857),g(869,921),g(1178,1180)],'sourceEvidence':[s('Web/Controllers/StudentsController.cs',23,25),s('Web/Controllers/StudentsController.cs',35,41),s('Infrastructure/EditorSnapshotStore.cs',7,11),s('wwwroot/js/site.js',2,8)]},
 {'behaviorId':'resume-page-flash-boundary','behavior':'復帰はApplied条件のResume再検索であり、SQL取得Pageの補正をApplied.Pageへ書き戻さない。読込時ReturnRevisionの照合、固定内部303、Resume後のFlash消費と後段Lookupの順序を保持する。','generatedEvidence':[g(929,1024)],'sourceEvidence':[s('Web/Controllers/StudentsController.cs',8,11),s('Web/Controllers/StudentsController.cs',38,39),s('Infrastructure/WebStudentCoordinator.cs',14,21),s('Infrastructure/SearchContextStore.cs',13,15),s('Core/SqlServerStudentService.cs',156,170),s('Infrastructure/FlashMessageStore.cs',6,9)]},
]

feedback={
 'schema':'source-backed-writer-feedback/1',
 'classification':'WRITER_SAFE_SOURCE_AND_AUTHORIZED_DESIGN_DOCUMENTATION',
 'reviewDocumentId':'SM-DET-STUDENT-EDITOR',
 'generatedVersion':'5.0',
 'functionalContradictionsFound':0,
 'sourceBackedFindings':findings,
 'existingCorrectBehaviors':keep,
 'scope':'新稿と許可ソースを新規レビュー。文書契約の批評は既に許可された設計入力のみを直接再読した。実装矛盾と設計説明不足を分離する。',
 'notPerformed':['application_execution','database_execution','HTTP_model_binding_execution','native_visual_verification_by_this_reviewer'],
 'provenance':{'generated':{'path':GEN,'sha256':GEN_SHA},'sourcePins':[{'path':CAPSULE+'sources/'+n,'sha256':h} for n,h in SOURCE_PINS.items()],'authorizedDesignPins':[{'path':CAPSULE+'reference-designs/'+n,'sha256':h} for n,h in DESIGN_PINS.items()],'builder':{'path':Path(__file__).relative_to(ROOT).as_posix(),'sha256':sha(Path(__file__))},'lineAndShaChecksPassed':True,'statementsHumanReviewed':True,'builderAssignsSemanticJudgements':False},
}
raw=(json.dumps(feedback,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
for bad in ('evaluationId','originalPoints','awardedPoints','expectedCells','spec-eval','evaluator-only'):
 assert bad not in raw.decode('utf-8')
target=(SAFE_ROOT/'student-editor-feedback.json').resolve()
assert target.is_relative_to(SAFE_ROOT) and target!=SAFE_ROOT
with target.open('xb') as out:out.write(raw)
print(json.dumps({'feedbackSha256':sha(target),'builderSha256':sha(Path(__file__)),'documentationFindings':len(findings),'functionalContradictions':0,'preservedBehaviors':len(keep),'sourcePins':len(SOURCE_PINS),'authorizedDesignPins':len(DESIGN_PINS)},ensure_ascii=False))
