"""Serialize independently reviewed notes using only the current MD and source.

No scoring report, checklist, expectation cell, or evaluator snapshot is loaded.
The source pins and line ranges identify the facts reviewed for these notes.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[5]
CAPSULE = ROOT / 'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
GEN = ROOT / 'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-02/spec/detail/student-search.md'
OUT = Path(__file__).with_name('student-search-feedback.json')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

NAMES = [
    'Program.cs', 'Web/Controllers/StudentsController.cs', 'Web/Inputs/StudentSearchInput.cs',
    'Core/Contracts.cs', 'Core/SqlServerStudentService.cs', 'Core/StudentNormalizer.cs',
    'Core/JapaneseDateService.cs', 'Core/MasterMaintenanceService.cs',
    'Infrastructure/WebStudentCoordinator.cs', 'Infrastructure/WebPresentation.cs',
    'Infrastructure/SearchContextStore.cs', 'Infrastructure/WebHostSetup.cs',
    'Infrastructure/EditorSnapshotStore.cs', 'Infrastructure/FlashMessageStore.cs',
    'Views/Students/Search.cshtml', 'Views/Students/Edit.cshtml',
    'wwwroot/js/site.js', 'wwwroot/css/site.css', 'database/001_schema.sql',
]
sources = {}
pins = []
for name in NAMES:
    key = 'sources/' + name
    raw = (CAPSULE / key).read_bytes()
    sources[key] = (raw.decode('utf-8-sig').splitlines(), sha(raw))
    pins.append({'path': key, 'sha256': sha(raw), 'bytes': len(raw)})
raw = GEN.read_bytes()
gen_sha = sha(raw)
lines = raw.decode('utf-8-sig').splitlines()
meta_match = re.fullmatch(r'<!-- spec-meta: (.+) -->', lines[0])
assert meta_match
meta = json.loads(meta_match.group(1))
assert meta['documentId'] == 'SM-DET-STUDENT-SEARCH' and meta['version'] == '2.0'
count = 0

def s(name, first, last=None, *anchors):
    global count
    last = first if last is None else last
    key = 'sources/' + name
    text, digest = sources[key]
    assert 1 <= first <= last <= len(text), (key, first, last)
    fragment = '\n'.join(text[first-1:last])
    assert all(anchor in fragment for anchor in anchors), (key, first, last, anchors)
    count += 1
    return {'path': key, 'startLine': first, 'endLine': last, 'sha256': digest}

def g(first, last=None, *anchors):
    global count
    last = first if last is None else last
    assert 1 <= first <= last <= len(lines)
    fragment = '\n'.join(lines[first-1:last])
    assert all(anchor in fragment for anchor in anchors), (first, last, anchors)
    count += 1
    return {'path': GEN.relative_to(ROOT).as_posix(), 'startLine': first,
            'endLine': last, 'sha256': gen_sha}

findings = [
    {
        'findingId': 'page-diagram-webfault-status',
        'kind': 'source_and_document_contradiction',
        'observation': 'ページ処理図はApplied未設定、GateのWebFault、検索サービスの検証WebFaultを一つの「409・空一覧用データ」へ接続している。本文の「対応HTTP状態」とも一致しない。ソースはPageのcatchでe.Statusを維持し、SearchAsyncのArgumentExceptionをValidationFailed、EnsureSearchを経て422へ移す。',
        'suggestedAction': 'Applied未設定や状態版拒否と、サービスの入力検証失敗を区別する。共有する再表示先を示す場合もHTTP状態を一律409に固定せず、図と本文と実際の結果型の対応を照合する。',
        'sourceEvidence': [s('Web/Controllers/StudentsController.cs', 18, 19, 'Response.StatusCode=e.Status'), s('Core/SqlServerStudentService.cs', 103, 110, 'ArgumentException'), s('Core/SqlServerStudentService.cs', 169, 170, 'Outcome.ValidationFailed'), s('Infrastructure/WebStudentCoordinator.cs', 11, 12, 'WebFault(409'), s('Infrastructure/WebStudentCoordinator.cs', 20, 20, 'WebPresentation.Status'), s('Infrastructure/WebPresentation.cs', 23, 23, 'Outcome.ValidationFailed=>422')],
        'generatedEvidence': [g(541, 565, 'V[409・空一覧用データ]', '検証WebFault'), g(579, 579, '対応HTTP状態')],
    },
    {
        'findingId': 'admission-date-layer-boundary',
        'kind': 'clarify_contract_boundary',
        'observation': '検索日の項目はネイティブtype=date入力、バインド後の任意文字列、厳密ISO変換後のDateOnly、型付きSQL dateを説明する。ブラウザー部品の値形式だけでは、人が読む表示と受信値と内部比較の責務を十分に分けられない。',
        'suggestedAction': '開始日・終了日のフォーム値、片側指定、厳密変換、日付比較、SQL、再描画を担当層ごとに対応付ける。独立した表示契約を扱う場合は入力部品の観測と区別し、実装にないフォーマッターやロケール保証を推測で追加しない。',
        'sourceEvidence': [s('Views/Students/Search.cshtml', 5, 5, 'type="date"'), s('Web/Inputs/StudentSearchInput.cs', 17, 22, 'string? AdmissionFrom', 'AdmissionTo=AdmissionTo'), s('Core/JapaneseDateService.cs', 52, 59, 'TryParseExact'), s('Core/SqlServerStudentService.cs', 67, 72, 'DateOnly'), s('Core/SqlServerStudentService.cs', 118, 122, 'from', 'to')],
        'generatedEvidence': [g(136, 137, 'yyyy-MM-dd'), g(844, 866, 'DateOnly', '時差')],
    },
    {
        'findingId': 'source-projection-and-design-layout',
        'kind': 'clarify_design_and_artifact_boundary',
        'observation': '静的HTMLはソースに存在する操作だけを投影し、参考設計のメニュー、範囲、追加ページ操作は差分表に別記している。関連文書の計画上のパスも生成済み本文の確認とは区別されている。',
        'suggestedAction': 'ソース投影と参考設計の配置を比較できるよう、各表示物の目的と証拠を明示する。必要な設計用ビューを追加する場合は参考設計としてラベルを付け、現在のRazor画面へない動作を実装済みと扱わない。静的HTML、描画画像、実機取得画像の出自と検査状態を分ける。',
        'sourceEvidence': [s('Views/Students/Search.cshtml', 3, 8, '前へ', '次へ'), s('Infrastructure/WebStudentCoordinator.cs', 21, 21, 'totalCount=', 'page=c.Page'), s('wwwroot/css/site.css', 1, 1)],
        'generatedEvidence': [g(54, 118, '静的', 'HTML'), g(912, 915, 'メニュー', 'RangeFrom'), g(921, 945, '計画', '未生成')],
    },
    {
        'findingId': 'execution-test-responsibility',
        'kind': 'clarify_verification_responsibility',
        'observation': '関連文書の責務対応とソース解析はアプリ/DB実行試験の記録ではない。healthの応答はdatabase=not-testedであり、起動コードだけから業務入力やSQLの実行結果を証明できない。',
        'suggestedAction': '抽出、文書検査、描画確認、将来の入力→サービス→DB→再表示確認の範囲を区別する。Unicode長、日付境界、古い状態版、検索上限、候補取得失敗、読取単位、復帰と通知の分岐をソース根拠の確認候補として示し、実行証拠なしに合格を記載しない。',
        'sourceEvidence': [s('Program.cs', 2, 8, 'app.Run()'), s('Infrastructure/WebHostSetup.cs', 28, 28, 'database="not-tested"'), s('Core/SqlServerStudentService.cs', 103, 170, 'IsolationLevel.Snapshot', 'Outcome.ValidationFailed')],
        'generatedEvidence': [g(921, 947, '関連文書', '未生成')],
    },
]

correct = [
    {
        'behaviorId': 'raw-modelstate-normalized-bind-chain',
        'behavior': 'HTTPフォーム受信値、MVCバインド後DTO、ModelState、サービスの正規化値、型付きSQL条件、DDLを分けている。rawはNormalizerへ届く値を指し、HTTPから空白が同一のまま届く保証を追加していない。',
        'preserve': '空と不正と任意NULL、raw上限と正規化上限、検索キーと保存表記、SQLパラメーター容量とDB型/NULLを同一視しない。',
        'sourceEvidence': [s('Web/Controllers/StudentsController.cs', 13, 16), s('Web/Inputs/StudentSearchInput.cs', 7, 22), s('Core/StudentNormalizer.cs', 47, 57), s('Core/SqlServerStudentService.cs', 113, 150)],
        'generatedEvidence': [g(26, 34), g(126, 137), g(844, 850)],
    },
    {
        'behaviorId': 'business-length-and-joined-null',
        'behavior': '保守サービスの名称業務長、DDL容量とCHECK、LEFT JOIN後のnullable出力を別に説明している。検索用途の既存停止値と保存用途の有効性検査も分離する。',
        'preserve': '名称容量を業務上限と扱わず、基表NOT NULLからLEFT JOIN結果の非NULLを保証しない。コード分類と値の用途別結合、学生行の保持を維持する。',
        'sourceEvidence': [s('Core/MasterMaintenanceService.cs', 33, 33, '18,18'), s('Core/MasterMaintenanceService.cs', 82, 82, '12,12'), s('database/001_schema.sql', 63, 81), s('database/001_schema.sql', 113, 128), s('Core/SqlServerStudentService.cs', 151, 168)],
        'generatedEvidence': [g(152, 156), g(192, 198), g(304, 344), g(848, 848)],
    },
    {
        'behaviorId': 'applied-page-and-resume',
        'behavior': 'PageはAppliedを複製して表示指定だけを変更し、必要時は別SearchAsyncで一度補正する。Resumeは元Appliedの条件を変えず、SQLの取得ページ補正と画面のpage値を区別する。',
        'preserve': '二度の検索を一つのSNAPSHOTと説明せず、再補正ループを作らない。未実行のフォーム値、保存した学生、取得ページを理由に元検索条件を広げない。',
        'sourceEvidence': [s('Infrastructure/WebStudentCoordinator.cs', 11, 14), s('Core/SqlServerStudentService.cs', 159, 168), s('Infrastructure/WebStudentCoordinator.cs', 21, 21)],
        'generatedEvidence': [g(525, 579), g(629, 674)],
    },
    {
        'behaviorId': 'options-and-last-result',
        'behavior': 'Optionsは候補Lookupだけを行い学生検索を実行せず、Entry版/Gate/期限を更新しない。LastResultを再提示し、上位不適合のクラスを解除する。',
        'preserve': 'Search失敗の空一覧応答と保持済みLastResultの消去を同一視しない。後続Optionsで旧一覧が再表示され得る点と、JSの解除とサーバー再描画の活性を維持する。',
        'sourceEvidence': [s('Web/Controllers/StudentsController.cs', 14, 22), s('wwwroot/js/site.js', 7, 8), s('Core/SqlServerStudentService.cs', 202, 223)],
        'generatedEvidence': [g(476, 519), g(679, 718), g(874, 897)],
    },
    {
        'behaviorId': 'revision-gate-and-ui-generation',
        'behavior': 'Contextの所有者/認証セッション/期限、非空時のタブ照合、排他内の厳密期待Revisionを記述し、検索Revisionと学生期待版、画面応答世代を区別する。',
        'preserve': '省略期待版の最新版補完を追加しない。OptionsやIndex/Resumeの実際の検査範囲と、参考設計の応答順意図を別に保つ。',
        'sourceEvidence': [s('Infrastructure/SearchContextStore.cs', 9, 15), s('Web/Controllers/StudentsController.cs', 8, 22), s('wwwroot/js/site.js', 2, 9)],
        'generatedEvidence': [g(165, 181), g(908, 910), g(917, 919)],
    },
    {
        'behaviorId': 'save-delete-return-failure-boundaries',
        'behavior': '通常Saveの非成功は投稿Inputを使う一方、Deleteの非SavedはLoadで最新値と新Snapshotを取得する。Delete理由の投稿復元はせず、再Loadの404が先の結果に代わり得る。',
        'preserve': '登録側の失敗をすべて編集入力保持へまとめない。Saved/NoChange/Unknown、DB確定、303復帰、Resume成功、Flash消費を別境界として維持する。',
        'sourceEvidence': [s('Web/Controllers/StudentsController.cs', 29, 39), s('Infrastructure/WebStudentCoordinator.cs', 17, 20), s('Infrastructure/FlashMessageStore.cs', 6, 9), s('Core/SqlServerStudentService.cs', 313, 329)],
        'generatedEvidence': [g(781, 838)],
    },
    {
        'behaviorId': 'snapshot-search-and-result-categories',
        'behavior': '同じ確定条件でTOP10001件数とページを同一検索SNAPSHOTで読む。未検索、0件、正常、上限超過を分け、超過の10001を総件数として表示しない。',
        'preserve': '全順序の末尾学生ID昇順、LIKEエスケープ、許可列による並替え、型付きoffset/sizeを維持し、元設計の表示範囲を現行Presentの実装として補わない。',
        'sourceEvidence': [s('Core/SqlServerStudentService.cs', 103, 168), s('Infrastructure/WebStudentCoordinator.cs', 21, 21), s('Views/Students/Search.cshtml', 7, 8)],
        'generatedEvidence': [g(252, 312), g(854, 866), g(913, 914)],
    },
    {
        'behaviorId': 'plan-reference-and-memory-scope',
        'behavior': '文書計画のID/パス/責務を参照し、本文の生成済み確認とは分けている。検索・編集・通知は別メモリ辞書であり、DDLの状態表から永続化や暗号化を推定しない。',
        'preserve': '関連文書を参照することと検証済み成果物であることを区別し、登録の全DML詳細は対応文書の責務として扱う。',
        'sourceEvidence': [s('Infrastructure/SearchContextStore.cs', 9, 15), s('Infrastructure/EditorSnapshotStore.cs', 7, 11), s('Infrastructure/FlashMessageStore.cs', 6, 9)],
        'generatedEvidence': [g(921, 947)],
    },
]

data = {
    'schema': 'source-backed-writer-feedback/1', 'classification': 'WRITER_SAFE_SOURCE_ONLY',
    'reviewDocumentId': meta['documentId'], 'reviewDocumentVersion': meta['version'],
    'reviewDate': '2026-10-13', 'projectId': 'test-project1', 'profile': 'CSharp_ASPNET',
    'iteration': '20261013-focus-round-02',
    'builderInputPolicy': 'Only this generated search MD and explicit authorized source files are read as task inputs.',
    'provenance': {'generatedPath': GEN.relative_to(ROOT).as_posix(), 'generatedSha256': gen_sha,
        'sourceInputRoot': CAPSULE.relative_to(ROOT).as_posix(), 'sourceInputs': pins,
        'checks': {'inputSha256Recorded': True, 'evidenceLineRangesAndAnchorsChecked': True,
                   'sourceFilesChecked': len(pins), 'generatedFilesChecked': 1,
                   'evidenceRangesChecked': count}},
    'sourceBackedFindings': findings, 'existingCorrectBehaviors': correct,
    'validationScope': 'Source/document review. This feedback does not establish application/DB execution or rendered-image fidelity.',
}
OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'path': OUT.relative_to(ROOT).as_posix(), 'sha256': sha(OUT.read_bytes()),
                  'builderSha256': sha(Path(__file__).read_bytes()), 'generatedSha256': gen_sha,
                  'evidenceRangesChecked': count}, ensure_ascii=False))
