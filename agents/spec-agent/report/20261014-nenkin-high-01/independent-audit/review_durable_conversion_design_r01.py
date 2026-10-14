"""Metadata-only independent review; no converter imports, execution or source reads."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

WORK = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
REPORT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
CANDIDATE = WORK / 'durable-candidate/conversion-scope-r01'
OUT = REPORT / 'independent-audit/durable-conversion-independent-design-review-r01.json'
HANDOFF = REPORT / 'durable-conversion-candidate-preparation-r02.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path):
    def pairs(values):
        answer = {}
        for key, value in values:
            assert key not in answer, 'Duplicate JSON metadata member'
            answer[key] = value
        return answer
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))

assert not OUT.exists()
pins = {
    CANDIDATE / 'package-plan-r01.json': '969c4b34bdaa7780cd2b91b53a55f3ad20bbb626df18ea76512c9e88ee77fac0',
    CANDIDATE / 'execution-config.schema-r01.json': '28af2edca6dabeec45843fb9a14c641fdb17c4126f3bccdd6014d30729aa55f4',
    CANDIDATE / 'format-v2-preserved-r01.json': 'e50b385e911267f587e931128597ca44b26a9974bb2aa7b4c9dff66614c6ac6f',
    CANDIDATE / 'baseline-code-pins-r01.json': '3889ff8c62a9ff53d312d98cc538c9f7a6598ca4d2a46c13868cb6e33b0e786c',
    HANDOFF: '27069f37817f25a8507bd6659dab8c693b0112145bb246d6262cc33ec5c609fd'
}
assert all(sha(path) == expected for path, expected in pins.items())
plan = load(CANDIDATE / 'package-plan-r01.json')
config = load(CANDIDATE / 'execution-config.schema-r01.json')
profile = load(CANDIDATE / 'format-v2-preserved-r01.json')
baseline = load(CANDIDATE / 'baseline-code-pins-r01.json')
handoff = load(HANDOFF)
baseline_profile = Path(baseline['profileDataSource']['path'])
assert baseline_profile == WORK / 'delivery/format-profile-v2-62-r04.json'
assert sha(baseline_profile) == baseline['profileDataSource']['sha256']
original_profile = load(baseline_profile)
preserved_keys = ['cover', 'normal', 'itemList', 'tableException', 'generalList', 'preamble',
    'formulaAuthoring', 'literalStringStorage', 'businessContentAuthored', 'artifactToolPublicApiOnly',
    'selectionBasis', 'userExplicitlySpecified62']
assert all(profile[key] == original_profile[key] for key in preserved_keys)
assert profile['cover']['expectedMergedRegions'] == 14 and profile['cover']['printArea'] == 'O6:AU36'
assert profile['normal']['columns'] == 62 and profile['normal']['columnWidth'] == 3
assert profile['itemList']['columns'] == 10 and profile['tableException']['columns'] == 9
assert profile['userExplicitlySpecified62'] is False and profile['businessContentAuthored'] is False

# Current converter files are hashed only; no executable component is imported or called.
components = {}
for name, pin in baseline['components'].items():
    path = Path(pin['path'])
    assert path.parent == WORK / 'delivery' and sha(path) == pin['sha256']
    components[name] = pin
assert len(components) == 8
for pin in plan['references'].values():
    assert Path(pin['path']).parent == CANDIDATE and sha(Path(pin['path'])) == pin['sha256']
for key in ('candidate', 'baseline', 'configSchema', 'pureProfile'):
    assert sha(Path(handoff[key]['path'])) == handoff[key]['sha256']
assert plan['status'] == 'DESIGN_ONLY_REAL_OUTPUT_QA_REQUIRED'
assert handoff['status'] == 'DESIGN_AND_CONFIG_SCHEMA_ONLY'
assert config['additionalProperties'] is False
assert config['properties']['referenceMode']['const'] == 'source-only'
assert config['properties']['profile']['properties']['sha256']['const'] == sha(CANDIDATE / 'format-v2-preserved-r01.json')
assert plan['configurationGuardImplemented'] is False and handoff['runtimeRootGuardImplemented'] is False
assert plan['candidateExecutablePrepared'] is False and plan['nativeQualified'] is False
assert plan['durablyPromoted'] is False and handoff['durablyPromoted'] is False
assert handoff['nativeOrEqualityReplayExecuted'] is False
assert 'arbitrary configured counts' in plan['runtimeBridgeBoundary']['laterParameterization']
assert 'TABLE9' in plan['branchCoverageLimit'] and 'native-unqualified' in plan['branchCoverageLimit']
assert 'separate parameterized-code audit' in plan['adoptionGate'] and 'same-input replay' in plan['adoptionGate']

previous_attempt = Path(handoff['priorPreparationFailure']['path'])
assert previous_attempt == REPORT / 'durable-conversion-candidate-attempt-r01.json'
assert sha(previous_attempt) == handoff['priorPreparationFailure']['sha256']
previous = load(previous_attempt)
assert previous['errorType'] == 'KeyError' and previous['error'] == 'table'
assert previous['activeComponentsModified'] is False
assert all(sha(path) == expected for path, expected in pins.items())
assert all(sha(Path(pin['path'])) == pin['sha256'] for pin in components.values())

report = {
    'schema': 'spec-agent-durable-conversion-independent-design-audit/1',
    'createdAt': datetime.now(timezone.utc).isoformat(),
    'reviewer': '/root/author_metadata_extension/metadata_r05_review',
    'status': 'APPROVED_DESIGN_SCOPE_ONLY_NOT_EXECUTION_OR_QUALIFICATION',
    'metadataPins': [{'path': str(path), 'sha256': expected} for path, expected in pins.items()],
    'reviewScope': 'Candidate metadata, static structural schema, baseline/pure format metadata; active component bytes hash-only',
    'activeComponentCount': len(components), 'activeComponentHashesBeforeAfterUnchanged': True,
    'pureProfileFieldsExactlyPreserved': preserved_keys,
    'blockingDesignFindings': [],
    'conclusions': [
        'The immediate package remains conversion-only; AI engine, collection/render, review bridge and publication are outside its scope.',
        'Upstream source13 full128-file/13-import/7-critical binding remains immutable; future bridge parameterization requires full accepted receipt equality, not arbitrary configured counts.',
        'Cover14, NORMAL62 width3, item LIST10 and TABLE9 format definitions remain literal copies of the baseline profile.',
        'Pure verification and PDF projection are planned to remain unchanged; path/identity guard changes require a separate executable audit.',
        'Original first-two real equality/native/print/PDF qualification and parameterized same-input replay are separate mandatory gates.',
        'TABLE9 and other LIST-width branches remain explicitly native-unqualified until actual reviewed current-run documents exercise them.',
        'The profile records62 as preserved-format interpretation rather than explicit numerical user instruction.',
        'The failed table lookup attempt remains recorded; r02 fixes only the metadata field lookup.'
    ],
    'implementationRequirementsStillOpen': [
        'The structural config schema does not constrain resolved roots, reparse ownership, runtime origin, public Artifact entry, current binding identity, deadline, or marker association; future run_contract must enforce them against accepted receipts.',
        'Future timeout values must be checked against the inherited run deadline and accepted per-stage bounds, in addition to structural ranges.',
        'If config schema is loaded externally by the executable package, include it in the immutable package manifest and enforce its actual origin/SHA before and after use.',
        'Only targeted changed-boundary rejection tests are needed; unchanged pure behavior still requires actual branch qualification rather than mirrored synthetic suites.'
    ],
    'candidateExecutableReviewed': False, 'runtimeRootGuardImplemented': False,
    'schemaMetaValidationIndependentlyExecuted': False,
    'actualOutputOrReplayExecuted': False, 'nativeQualificationVerified': False,
    'applicationOrDatabaseExecuted': False, 'authoringMarkersExecuted': False,
    'converterImportsOrCallsExecuted': False, 'AIProvidersExecuted': False,
    'sourceOrExpectedOrOldOutputRead': False, 'activeFilesModified': False,
    'durablyPromoted': False, 'formalQualityOr95PercentClaimed': False
}
with OUT.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'report': str(OUT), 'sha256': sha(OUT), 'status': report['status'],
                  'activeComponentHashChecks': len(components), 'providerStarts': 0}, ensure_ascii=False))
