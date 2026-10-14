"""Record manually judged helper review; no provider/render/application execution."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
helper = ROOT / 'agents/reverse-agent/test-report/20261013-rerun-12h/source-pilot/prepare_state_projection.py'
expected_helper = '2d3380b3a6e886381ecf8d7826f0b636088f88eb285e1e9468b4245fbd319c11'
assert hashlib.sha256(helper.read_bytes()).hexdigest() == expected_helper
drafts = [
    ('search-basic-05', 'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts/search-basic-05/基本設計書/01_学生検索画面.md', '1f307707bebcb621f7c0e7f895cec8e2a5c386c98c96aa5821c7e9619f0f6778'),
    ('search-detail-04', 'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts/search-detail-04/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md', '658617eb1367817031128eef12fbd51d50b758e04dff14f01997f14eacb1c785'),
]
for _, path, sha in drafts:
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha
probe01 = HERE / 'state-projection-gate-probe-01.json'
probe02 = HERE / 'state-projection-gate-probe-02.json'
latest = json.loads(probe02.read_text(encoding='utf8'))
assert latest['helper']['sha256'] == expected_helper
assert not latest['findings']
assert all(case['matchesExpected'] for case in latest['htmlGateCases'])
lines = helper.read_text(encoding='utf8').splitlines()


def evidence(start, end):
    return {'path': helper.relative_to(ROOT).as_posix(), 'sha256': expected_helper,
            'startLine': start, 'endLine': end, 'quote': '\n'.join(lines[start-1:end])}


def reference(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


review = {
    'schema': 'reverse-source-projection-helper-review/1',
    'recordedAtUtc': datetime.now(timezone.utc).isoformat(),
    'reviewRole': 'SOURCE_ONLY_INDEPENDENT_TECHNICAL_GATE',
    'helper': reference(helper),
    'boundPreviouslyAuditedDrafts': [{'id': key, 'path': path, 'sha256': sha} for key, path, sha in drafts],
    'scopeBoundary': {
        'originalSpecificationRead': False, 'specEvalRead': False,
        'trainingAssistedRead': False, 'scoresCreated': False,
        'helperOrCanonicalDraftEdited': False, 'aiProviderInvoked': False,
        'applicationDbSqlDeploymentExecuted': False,
        'browserRendererNetworkExecuted': False,
        'executedHelperDefinitionsOnly': latest['scope']['functionDefinitionsOnly'],
        'topLevelJobPipeline': 'READ_STATICALLY_NOT_INVOKED',
    },
    'judgment': {
        'testedCases': 'PASS_20_HTML_3_PATH_5_CANONICAL_LOCATION',
        'priorTwoNegativeCases': 'RESOLVED_ON_THIS_EXACT_HELPER_SHA',
        'newImportantTechnicalDefectFound': False,
        'readyForParentControlledAiProjectionRequest': True,
        'projectionMeaningVerified': False, 'fullInertnessProven': False,
        'nativeVisualFidelityVerified': False, 'applicationRuntimeVerified': False,
        'formalOriginalRubricPass': False,
    },
    'dynamicEvidence': {
        'priorProbe': reference(probe01), 'latestProbe': reference(probe02),
        'htmlCases': len(latest['htmlGateCases']), 'pathCases': len(latest['pathCases']),
        'canonicalLocationCases': len(latest['canonicalLocationCases']),
        'runtimeReceipt': latest['runtimeReceipt'],
        'unexpectedResults': latest['findings'],
    },
    'resolvedFindings': [
        {'id': 'PG01', 'problem': 'Old helper accepted an image-set() string URL.',
         'resolution': 'Reference functions including escaped image-set and -webkit-image-set are rejected recursively in parsed CSS.',
         'evidence': evidence(17, 32),
         'testedLabels': ['css-image-set-string-resource', 'css-image-set-escaped', 'css-webkit-image-set', 'css-webkit-image-set-escaped', 'inline-css-image-set']},
        {'id': 'PG02', 'problem': 'Old helper accepted duplicate meta http-equiv refresh because dict(attrs) retained the later value.',
         'resolution': 'Case-insensitive duplicate attributes are rejected for all HTML tags before dict(attrs) construction.',
         'evidence': evidence(46, 51),
         'testedLabels': ['meta-refresh-duplicate-attribute', 'duplicate-case-insensitive-safe-attribute', 'meta-refresh-entity-value']},
    ],
    'staticReview': [
        {'area': 'input roles and exact pins',
         'observation': 'Approved snapshot, source-only mode/no reference files, receipt04/05, fresh disjoint job root, two unique approved manuscript paths, explicit caller SHA, complete runtime hash map, and runtime import location are checked before dispatch.'},
        {'area': 'state answer bindings',
         'observation': 'Answer schema binds the exact manifest/draft SHA set. Every exact draft must be bound; state IDs must be unique; references are validated. Renderable states require source references and exact heading/line locations.'},
        {'area': 'canonical omission handling',
         'observation': 'When requiresCanonicalRevision is true, auxiliary HTML must be empty. The AI task explicitly returns canonical gaps for canonical AI revision; Python does not assemble semantic body/HTML.'},
        {'area': 'immutability and handoff',
         'observation': 'Draft SHA, sealed snapshot, original source hashes and frozen runtime hashes are rechecked after the AI answer. Handoff declares independent semantic review, strict renderer sanitizer, no complete inertness proof, no visual/runtime/original-rubric pass.'},
    ],
    'limitationsForIndependentReview': [
        {'id': 'PL01', 'severity': 'review-required',
         'detail': 'A correct heading/line binding proves position only, not that the cited text supports a state or its projected controls. Independent source/canonical meaning review remains required.'},
        {'id': 'PL02', 'severity': 'review-required',
         'detail': 'states minItems=1 and distinct IDs do not mechanically prove coverage of initial/normal/empty/tooMany/Viewer or other applicable source states. State completeness must be judged independently.'},
        {'id': 'PL03', 'severity': 'known-mechanical-limit',
         'detail': 'The canonical path gate permits both allowed suffixes under either search-basic-* or search-detail-* folder prefix, and the top-level pair check does not require exactly one basic and one detail kind. The tested caller pair contains the requested distinct basic05/detail04 files; this weakness did not affect the current review.'},
        {'id': 'PL04', 'severity': 'review-required',
         'detail': 'Twenty HTML cases are a finite rejection suite, not exhaustive browser inertness proof. Parent-controlled strict renderer sanitization and native visual review remain prerequisites to interpreting rendered evidence.'},
    ],
    'relatedBusinessAudit': reference(HERE / 'document-comparison-03.json'),
}
target = HERE / 'state-projection-helper-review-01.json'
assert not target.exists()
target.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf8', newline='\n')
summary = HERE / 'state-projection-helper-review-01.summary.md'
assert not summary.exists()
summary.write_text('''# source-only 投影helper 技術レビュー

対象は `prepare_state_projection.py` SHA `2d3380b3a6e886381ecf8d7826f0b636088f88eb285e1e9468b4245fbd319c11`。原仕様・spec-eval・training-assisted・採点は未読。helper、原稿、原ソースを変更していない。

旧SHAで通過したCSS `image-set()`文字列URLと重複meta refresh属性は、新SHAではともに拒否された。エスケープ、webkit、inline CSS、大小文字属性等を含む20 HTMLケース、3パスケース、5原稿位置ケースが期待通り。source04 runtimeの124ファイルは固定receiptと一致した。新たな重要技術欠陥は見つからなかった。

実行したのはASTで取り出した6関数・クラス定義だけ。トップレベルのAI発注、ソース不変gate等は静的読取りで確認した。provider、ブラウザ、通信、renderer、原App、DB、SQL、配置は未実行。

パス検査は現在の基本05・詳細04を許可し、role外パスを拒否する。見出し・行・SHA照合は架空見出し、誤行、誤SHA、節外範囲を拒否する。一方、位置の実在だけでは意味の一致を証明しない。状態配列のminItems=1は全状態の網羅を証明しない。許可suffixと基本/詳細folder prefixの組み合わせ、基本1件・詳細1件の組を機械的には限定していないが、今回の呼出対象は指定された別種2稿である。

この結果は親Agent管理下でAI投影を発注するための技術検査として扱える。HTMLの完全な非実行性、正本との意味一致、状態網羅、native画像合格、原アプリの動作合格、原評価表の合格は未確認。厳格renderer処理と独立したsource/canonical/画像レビューが必要。

詳細証跡: `state-projection-gate-probe-01.json`（旧不具合）、`state-projection-gate-probe-02.json`（新SHA再検証）、`state-projection-helper-review-01.json`（AI判断）。業務本文・図の独立比較は `document-comparison-03.json` に保存済み。
''', encoding='utf8', newline='\n')
print(json.dumps({'review': reference(target), 'summary': reference(summary)}, ensure_ascii=False))
