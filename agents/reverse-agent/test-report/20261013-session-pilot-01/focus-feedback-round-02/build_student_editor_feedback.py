"""Build writer-safe notes from the current editor MD and authorized source only.

All factual notes below were reviewed independently against these exact inputs.
This builder attaches identities, verifies SHA256 and line anchors, and serializes
the notes. It does not load evaluation reports, checklists, expected cells, or
reference designs, and it does not derive semantic findings from text matches.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SOURCE_ROOT = ROOT / 'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
GENERATED = ROOT / 'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-02/spec/detail/student-editor.md'
OUTPUT = Path(__file__).with_name('student-editor-feedback.json')
GENERATED_SHA = '657b3ff33fb8d07d37b7408245fc5c448020810efd77628e481e10d6edc70161'
SOURCE_PINS = {
    'sources/Program.cs': 'd45c2b1b96fa1354706b0f4a8dcd4830c1f78c175b091919b0c3af0d44eb6e49',
    'sources/Core/Contracts.cs': '0df616a1e6369675a0bc6997ea480726267070dcec8d31f4ec7eaf8395492916',
    'sources/Core/JapaneseDateService.cs': 'fe3ba2094f911da09b2fb0d5b2694006f347f2a2eb2e4944ac8f251cd265f847',
    'sources/Core/StudentNormalizer.cs': 'e2cad5e8b23fbbbe44ca03933432b371b4b3fe824432220b183cc922f838b71d',
    'sources/Core/SqlServerStudentService.cs': 'ae235c4a91ef2e1b7ed5fafb13b4f898e12cb38333e01b027c27b12d999b7560',
    'sources/Core/MasterMaintenanceService.cs': '271674d65ae5d3d1d8b5537e0d243b01ce730f7d5cba033c69cdf24b6c06d4ef',
    'sources/Views/Students/Edit.cshtml': '8a9f8ee01b5241be778f8f1b03819a62ab00502abba0b02e5e87a8035abf5b67',
    'sources/Web/Inputs/StudentSaveInput.cs': '607b30560672b7b548a6ece29f6f4a47a2cadf68786d1fe8d265a0452d03fbb8',
    'sources/Web/Controllers/StudentsController.cs': 'cbbf397456a0c95cd5a7e33a2faabb06826451e5f24ac48d571283c88e8e3e31',
    'sources/Infrastructure/SearchContextStore.cs': '7cc7e82c9a6bda7bf33ee374cad02348c1be2f40a6728aefe9b761dac0463bd2',
    'sources/Infrastructure/EditorSnapshotStore.cs': '887e02443c77d43d175105a3411e46676c54e64d4a44e6cf07f133bb5da3a027',
    'sources/Infrastructure/WebStudentCoordinator.cs': '358bc13a486d43b4e30404f12f32845060ea4e98d3979c64a03ed8cc11a7c962',
    'sources/Infrastructure/WebHostSetup.cs': '1a873e7427fcbc16d3593d2eaaed5c4180e79625bff8819ce979eada8e3f0649',
    'sources/Infrastructure/WebPresentation.cs': '3a78f67fca52749e10924cea48054055612404ae687f3dfac0817b6741ac7c26',
    'sources/Infrastructure/FlashMessageStore.cs': 'dc3a431e90dfb70b9055f7c47914a84182f6ca5f2db9d2156f60589fff7b5fd3',
    'sources/database/001_schema.sql': 'e6872d042fed6e1d795fde72e29adef5cecda6a0887348444ea905661de1178a',
    'sources/database/002_seed.sql': 'b4b6745e5c6e7d1ed3a22b07b2bb4607b5a6bf173ad08ba5bf32f0e4bb2322ee',
}

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

raw = GENERATED.read_bytes()
assert sha(raw) == GENERATED_SHA, 'Current generated editor differs from the reviewed candidate.'
generated_lines = raw.decode('utf-8-sig').splitlines()
match = re.fullmatch(r'<!-- spec-meta: (.+) -->', generated_lines[0])
assert match, 'Generated document metadata missing.'
meta = json.loads(match.group(1))
assert meta['documentId'] == 'SM-DET-STUDENT-EDITOR' and meta['version'] == '2.0'
loaded: dict[str, list[str]] = {}
source_inputs = []
for name, expected_sha in SOURCE_PINS.items():
    p = SOURCE_ROOT / name
    source_raw = p.read_bytes()
    assert sha(source_raw) == expected_sha, f'Authorized source changed: {name}'
    loaded[name] = source_raw.decode('utf-8-sig').splitlines()
    source_inputs.append({'path': name, 'sha256': expected_sha, 'bytes': len(source_raw)})

anchors_checked = 0

def source(name: str, start: int, end: int, *anchors: str) -> dict:
    global anchors_checked
    assert name in loaded
    lines = loaded[name]
    assert 1 <= start <= end <= len(lines), (name, start, end)
    fragment = '\n'.join(lines[start - 1:end])
    for anchor in anchors:
        assert anchor in fragment, (name, start, end, anchor)
    anchors_checked += 1
    return {'path': name, 'startLine': start, 'endLine': end, 'sha256': SOURCE_PINS[name]}

def generated(start: int, end: int, *anchors: str) -> dict:
    global anchors_checked
    assert 1 <= start <= end <= len(generated_lines), (start, end)
    fragment = '\n'.join(generated_lines[start - 1:end])
    for anchor in anchors:
        assert anchor in fragment, (start, end, anchor)
    anchors_checked += 1
    return {'path': GENERATED.relative_to(ROOT).as_posix(), 'startLine': start, 'endLine': end, 'sha256': GENERATED_SHA}

findings = [
    {
        'findingId': 'date-layer-responsibility',
        'kind': 'clarify_contract_boundary',
        'observation': '本文はtype=dateの入力部品、ISO文字列への既存値復元、内部DateOnlyとSQL dateを説明している。これらを一つの表示形式契約へまとめると、受信値、内部比較値、再表示値の責務が読み取りにくくなる。',
        'suggestedAction': '入学日・終了日について、フォーム値、厳密変換、内部日付、DB、再表示の担当層を対応付ける。独立した表示契約を説明する場合は、観測できる入力値の形式と区別し、ソースにない表示保証を推定しない。',
        'sourceEvidence': [
            source('sources/Views/Students/Edit.cshtml', 11, 11, 'type="date"'),
            source('sources/Core/SqlServerStudentService.cs', 188, 194, 'AdmissionDate=', 'EnrollmentEndDate='),
            source('sources/Core/JapaneseDateService.cs', 52, 59, 'ParseIso', 'TryParseExact'),
            source('sources/Core/SqlServerStudentService.cs', 67, 72, 'DateOnly', 'DBNull.Value'),
        ],
        'generatedEvidence': [generated(138, 140, 'type=date'), generated(176, 178, 'ParseIso'), generated(859, 859, 'date値に時差変換はなく')],
    },
    {
        'findingId': 'wareki-raw-versus-normalized-limits',
        'kind': 'clarify_contract_boundary',
        'observation': '和暦の元号IDは完全一致で照合し、数値部だけNFKC後に桁数・ASCII正整数を検査する。通常Textの正規化前rawスカラー検査とは異なる処理である。',
        'suggestedAction': '和暦4部品ごとにraw表現、変換後の制約、HTMLガード、サーバー検査を分けて記載する。数値部の変換後制約をraw上限の説明へ置き換えず、ソースで実施していないText型のraw検査を実施済みと書かない。',
        'sourceEvidence': [
            source('sources/Core/JapaneseDateService.cs', 17, 24, 'era.Id == input.Era', 'NormalizationForm.FormKC'),
            source('sources/Core/JapaneseDateService.cs', 35, 39, 'text.Length', 'value <= 0'),
            source('sources/Core/StudentNormalizer.cs', 47, 57, 'ScalarCount(raw)', 'value.Trim()'),
            source('sources/Views/Students/Edit.cshtml', 7, 7, 'BirthDateInput.Era', 'BirthDateInput.Year'),
        ],
        'generatedEvidence': [generated(130, 130, '4値とも空'), generated(168, 168, '数値部NFKC後'), generated(849, 849, 'Textのraw検査ではない')],
    },
    {
        'findingId': 'execution-and-verification-scope',
        'kind': 'clarify_verification_responsibility',
        'observation': '関連文書計画とソース観測は実行検証の記録ではない。起動コードはWebホストを組み立てて実行し、health応答にもDB試験を実施したという情報はない。',
        'suggestedAction': '仕様抽出、文書検査、画面描画確認、アプリ/DB実行試験の責務と実施状態を区別する。将来確認する入力→サービス→DB→再表示の流れや、保存分岐/競合/履歴失敗/確定結果不明の確認範囲を、ソースの分岐を根拠に示す。実行結果の証拠なしに合格を主張しない。',
        'sourceEvidence': [
            source('sources/Program.cs', 2, 8, 'WebApplication.CreateBuilder', 'app.Run()'),
            source('sources/Infrastructure/WebHostSetup.cs', 28, 28, 'database="not-tested"'),
            source('sources/Core/SqlServerStudentService.cs', 313, 323, 'CommitAsync', 'Outcome.Unknown'),
        ],
        'generatedEvidence': [generated(9, 10, 'ソースで観測した実装'), generated(922, 950, '関連文書', '未生成')],
    },
]

correct = [
    {
        'behaviorId': 'typed-bind-and-null-chain',
        'behavior': 'フォーム値からStudentSaveInput、StudentDraft、正規化Values、型付きSQL、DDL型/NULLへの移送を分け、任意空値、変換失敗、条件付き必須、物理容量を同一視しない。',
        'preserve': 'HTTP受信値・バインド後DTO・ModelState・サービス引数の区別と、19業務値/生成3値/補助値・管理値の分離を維持する。',
        'sourceEvidence': [source('sources/Web/Inputs/StudentSaveInput.cs', 34, 43, 'new StudentDraft', 'IdParser.Optional'), source('sources/Core/StudentNormalizer.cs', 119, 159, 'NormalizedStudent', 'relationship_category'), source('sources/Core/SqlServerStudentService.cs', 30, 37, 'SqlDbType'), source('sources/Core/SqlServerStudentService.cs', 67, 72, 'DBNull.Value'), source('sources/database/001_schema.sql', 8, 42, 'NULL', 'IDENTITY')],
        'generatedEvidence': [generated(21, 21, '業務19項目'), generated(44, 46, '同一視しない'), generated(165, 194, 'NOT NULL', 'NULL')],
    },
    {
        'behaviorId': 'independent-context-and-snapshot',
        'behavior': 'ContextとSnapshotは共通乱数関数を別々に呼んで独立発行し、別辞書へ保存する。検索版、学生期待版、所有/セッション/タブ/対象の照合範囲も異なる。',
        'preserve': '同じキー生成関数を使うことを同一キー・同一保持領域・同じ検査条件という意味へ変えない。',
        'sourceEvidence': [source('sources/Infrastructure/SearchContextStore.cs', 9, 14, 'Id {get;}=Token()', 'ContextRevision'), source('sources/Infrastructure/EditorSnapshotStore.cs', 7, 11, 'SearchContextStore.Token()', 'snapshots[token]')],
        'generatedEvidence': [generated(230, 232, '独立発行', '別キー・別辞書')],
    },
    {
        'behaviorId': 'protected-code-versus-selectability',
        'behavior': 'IsProtectedはLookupへ移送するが、学生画面のoption利用可否には使用しない。保護値の停止・期間短縮禁止はコード保守の責務であり、名称等の通常更新とは別である。',
        'preserve': '保護、現在の有効性/期間、既存同値保持、学生保存値を区別し、保護を全属性の変更禁止と説明しない。',
        'sourceEvidence': [source('sources/database/002_seed.sql', 14, 22, 'is_protected'), source('sources/Core/SqlServerStudentService.cs', 203, 212, 'is_protected'), source('sources/Core/MasterMaintenanceService.cs', 105, 115, '保護値の停止・期間短縮', 'code_name=@name'), source('sources/Views/Students/Edit.cshtml', 8, 13, 'selectable=')],
        'generatedEvidence': [generated(216, 218, 'IsProtected'), generated(837, 837, '保護はマスター保守の責務')],
    },
    {
        'behaviorId': 'save-versus-delete-failure',
        'behavior': '通常保存の非成功は投稿Inputを使って再表示する。削除の非Saved結果はLoadを再実行し、最新DB値/期待版/新Snapshotへ戻るため、編集投稿値と投稿削除理由を復元しない。',
        'preserve': '削除を通常保存と同じ入力保持経路としてまとめない。再Loadで対象不在の応答が元の結果状態に代わる可能性も維持する。',
        'sourceEvidence': [source('sources/Web/Controllers/StudentsController.cs', 29, 33, 'Input=input'), source('sources/Web/Controllers/StudentsController.cs', 37, 37, 'return await Load'), source('sources/Infrastructure/WebStudentCoordinator.cs', 17, 19, 'StudentSaveInput.From'), source('sources/Views/Students/Edit.cshtml', 17, 17, 'textarea name="Reason"')],
        'generatedEvidence': [generated(514, 514, '投稿Input'), generated(655, 655, '投稿削除理由は復元しない'), generated(916, 916, '削除非Saved')],
    },
    {
        'behaviorId': 'confirmation-full-payload-and-candidates',
        'behavior': '確認は生成値を除く業務19値と全候補ID/版のハッシュ、主体/セッション/対象/期待版/期限、原子的Busyを照合する。表示最大件数を比較対象へ流用しない。',
        'preserve': '入力操作のキー消去・確認取消、サーバーBusy取得/解除、成功後消費、Unknown時無効化を別の状態遷移として維持する。',
        'sourceEvidence': [source('sources/Core/SqlServerStudentService.cs', 224, 225, 'HashPayload', 'HashCandidates'), source('sources/Core/SqlServerStudentService.cs', 269, 290, 'while(await reader.ReadAsync(ct))', 'Interlocked.CompareExchange'), source('sources/Core/SqlServerStudentService.cs', 313, 335, 'TryRemove', 'Interlocked.Exchange')],
        'generatedEvidence': [generated(233, 239, '業務19値ハッシュ', '別'), generated(526, 585, '全候補', 'Commit正常終了後')],
    },
    {
        'behaviorId': 'nochange-commit-and-unknown',
        'behavior': 'NoChangeは書込単位内の最新DB値との比較で、版・時点・監査を増やさない。学生と監査の正常Commit後だけSavedとし、書込み/Commit/Rollbackの状態でUnknownを分類する。',
        'preserve': 'OUTPUTでIDを受け取ったことを確定成功と扱わず、Open/Beginの例外境界や特別な例外分岐の扱いを維持する。',
        'sourceEvidence': [source('sources/Core/SqlServerStudentService.cs', 240, 263, 'BeginTransactionAsync', 'Outcome.NoChange'), source('sources/Core/SqlServerStudentService.cs', 302, 329, 'Audit(', 'commitAttempted', 'unknown=writeStarted'), source('sources/Core/SqlServerStudentService.cs', 409, 416, 'Audit(', 'CommitAsync')],
        'generatedEvidence': [generated(204, 204, '差分なし'), generated(475, 475, 'Snapshot.Originalではなく'), generated(865, 871, 'writeStarted', 'Unknown')],
    },
    {
        'behaviorId': 'reset-versus-reload',
        'behavior': 'ResetはSnapshot.Originalの複製で入力を戻し、学生本体の最新取得は行わない。Reloadは通常既存GETで全業務値と期待版を取得し、新Snapshotへ置き換える。',
        'preserve': '取消と再読込の取得元・期待版・候補再取得を分け、期待版だけを最新版へ変更する操作にしない。',
        'sourceEvidence': [source('sources/Web/Controllers/StudentsController.cs', 23, 25, 'Load(id,returnContextId'), source('sources/Web/Controllers/StudentsController.cs', 35, 35, 'Copy(snapshot.Original)'), source('sources/Infrastructure/EditorSnapshotStore.cs', 9, 11, 'Copy(original)'), source('sources/Views/Students/Edit.cshtml', 16, 16, '最新情報を再読込')],
        'generatedEvidence': [generated(661, 699, 'メモリ', '期待版'), generated(705, 744, '最新業務値・最新期待版・新Snapshot')],
    },
    {
        'behaviorId': 'page-and-resume-return-boundaries',
        'behavior': '検索復帰は読込Context/検索版と固定内部303を使い、Applied条件でResumeする。Pageの補正書戻しとResumeの取得ページ/提示pageは異なる。DB確定、復帰検索成功、Flash消費も別境界である。',
        'preserve': 'Context未適用時の未検索、版相違による復帰失敗、Resume後Lookup前のFlash消費、人数なしLookupのゼロを実人数とみなさない点を維持する。',
        'sourceEvidence': [source('sources/Infrastructure/WebStudentCoordinator.cs', 11, 14, 'criteria.Page=', 'Resume'), source('sources/Infrastructure/WebStudentCoordinator.cs', 21, 21, 'page=c.Page'), source('sources/Web/Controllers/StudentsController.cs', 8, 11, 'coordinator.Resume', 'flash.Take'), source('sources/Web/Controllers/StudentsController.cs', 38, 39, 'Response.StatusCode=303', 'LookupAsync(false'), source('sources/Infrastructure/SearchContextStore.cs', 13, 14, 'ContextRevision'), source('sources/Infrastructure/FlashMessageStore.cs', 7, 9, 'TryRemove')],
        'generatedEvidence': [generated(754, 808, 'Applied', '取得ページと表示page')],
    },
]

data = {
    'schema': 'source-backed-writer-feedback/1',
    'classification': 'WRITER_SAFE_SOURCE_ONLY',
    'reviewDocumentId': meta['documentId'],
    'reviewDocumentVersion': meta['version'],
    'reviewDate': '2026-10-13',
    'projectId': 'test-project1',
    'profile': 'CSharp_ASPNET',
    'iteration': '20261013-focus-round-02',
    'builderInputPolicy': 'Only this generated editor MD and explicit authorized source files are read as task inputs.',
    'provenance': {
        'generatedPath': GENERATED.relative_to(ROOT).as_posix(),
        'generatedSha256': GENERATED_SHA,
        'sourceInputRoot': SOURCE_ROOT.relative_to(ROOT).as_posix(),
        'sourceInputs': source_inputs,
        'checks': {'inputSha256Matches': True, 'evidenceLineRangesAndAnchorsChecked': True,
                   'sourceFilesChecked': len(source_inputs), 'generatedFilesChecked': 1,
                   'evidenceRangesChecked': anchors_checked},
    },
    'sourceBackedFindings': findings,
    'existingCorrectBehaviors': correct,
    'validationScope': 'Source/document review. These notes do not establish application execution, DB testing, or rendered-image fidelity.',
}
assert len(findings) == 3 and len(correct) == 8
OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'output': OUTPUT.relative_to(ROOT).as_posix(), 'feedbackSha256': sha(OUTPUT.read_bytes()),
                  'builderSha256': sha(Path(__file__).read_bytes()), 'generatedSha256': GENERATED_SHA,
                  'sourceFilesChecked': len(source_inputs), 'evidenceRangesChecked': anchors_checked}, ensure_ascii=False))
