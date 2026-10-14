"""Independent code/pure-function audit. No production bindings or AI providers."""
from pathlib import Path
import ast
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
WORK = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
REPORT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
OUT = REPORT / 'independent-audit/writer-metadata-r05-independent-code-review-r01.json'
DRIVER = WORK / 'nenkin_writer_driver_r05.py'
BASE = WORK / 'nenkin_writer_driver_r04.py'
EXPECTED = '6b8e5456d96fabfda1bf43b6c17b6155167726492b10c0f9145473f243ee102c'
EXPECTED_BASE = 'ce836766e61f5abad0fc4d2abfe11b3c6e6588f4dc8b9d46f62f913f0cd8e664'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert not OUT.exists()
assert sha(DRIVER) == EXPECTED and sha(BASE) == EXPECTED_BASE
spec = importlib.util.spec_from_file_location('independent_metadata_r05_only', DRIVER)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
assert not any(name == 'contextbase' or name.startswith('contextbase.') for name in sys.modules)

checks = []
def check(name, callback, reject=False):
    try:
        callback()
        actual = 'ACCEPTED'
        detail = None
    except ValueError as exc:
        actual = 'REJECTED'
        detail = str(exc)
    expected = 'REJECTED' if reject else 'ACCEPTED'
    checks.append({'name': name, 'expected': expected, 'actual': actual,
                   'passed': expected == actual, 'detail': detail})

# Pure function checks use in-memory data; path checks only resolve owned/nonexistent toy paths.
plan = {'documents': [{'id': 'INDEX', 'kind': 'index', 'path': 'index.md'},
                      {'id': 'REPORT', 'kind': 'analysis-report', 'path': 'analysis/report.md'},
                      {'id': 'BASIC', 'kind': 'basic-design', 'path': 'basic/a.md'}]}
pin = {'snapshot': {'manifestSha256': 'a' * 64}, 'executionContextSha256': 'b' * 64,
       'planSha256': 'c' * 64, 'executionMetadata': {'documentIds': ['INDEX', 'REPORT'],
          'context': {'schema': 'synthetic-context-only/1', 'recordedState': 'IN_PROGRESS'}}}
identity = {'runId': '20261014-nenkin-high-01', 'projectId': 'nenkin',
    'capsuleManifestSha256': 'a' * 64, 'executionContextSha256': 'b' * 64, 'planSha256': 'c' * 64,
    'sourceOnly': True, 'businessEvidenceAuthority': False, 'originalAppExecuted': False,
    'originalSpecificationsAuthorized': False, 'evaluationExpectationsAuthorized': False,
    'newSourceReadPermissions': False}
check('exact synthetic same-run identity', lambda: m.metadata_identity(identity, pin))
for key, value in [('projectId', 'other'), ('runId', 'other'),
                   ('capsuleManifestSha256', 'd' * 64), ('executionContextSha256', 'd' * 64),
                   ('planSha256', 'd' * 64), ('sourceOnly', False),
                   ('businessEvidenceAuthority', True), ('newSourceReadPermissions', True),
                   ('originalAppExecuted', True)]:
    altered = {**identity, key: value}
    check('identity rejects ' + key, lambda altered=altered: m.metadata_identity(altered, pin), True)
check('reserved wave exact IDs', lambda: m.metadata_selection(pin, plan, ['REPORT', 'INDEX']))
check('reserved wave subset', lambda: m.metadata_selection(pin, plan, ['INDEX']), True)
check('reserved wave business document', lambda: m.metadata_selection(pin, plan, ['INDEX', 'REPORT', 'BASIC']), True)

for value in ('md/index.md', 'analysis/report.md'):
    check('normalized routing path ' + value, lambda value=value: m.metadata_relative_path(value))
for value in ('../index.md', '/index.md', 'md//index.md', 'md/./index.md',
              'D:/index.md', 'md\\index.md', 'md/index.md?x', 'md/index.md#x', 'md/%20.md'):
    check('unsafe routing path ' + repr(value), lambda value=value: m.metadata_relative_path(value), True)

original = {'schema': 'synthetic-original-only/1', 'nested': {'scope': ['a', 'b']}}
before = copy.deepcopy(original)
def unchanged_context():
    actual = m.metadata_revision_context(original, original, pin)
    assert actual['executionContext'] is original and original == before
    assert actual['sameRunExecutionMetadata'] == pin['executionMetadata']['context']
check('complete original execution context preserved', unchanged_context)
def unchanged_revision():
    prior = {'executionContext': original, 'previousCanonicalMarkdown': 'whole\r\nMarkdown\r\n',
             'preservedIndependentReviewRawResponse': '{\r\n  "approved": false\r\n}\r\n'}
    actual = m.metadata_revision_context(prior, original, pin)
    assert actual['previousCanonicalMarkdown'] == prior['previousCanonicalMarkdown']
    assert actual['preservedIndependentReviewRawResponse'] == prior['preservedIndependentReviewRawResponse']
    assert 'sameRunExecutionMetadata' not in prior
check('previous exact Markdown/raw review retained without mutation', unchanged_revision)
check('original context replacement rejected',
      lambda: m.metadata_revision_context({'executionContext': {}}, original, pin), True)
check('supplement overwrite rejected',
      lambda: m.metadata_revision_context({'executionContext': original, 'sameRunExecutionMetadata': {}}, original, pin), True)

owned = WORK / 'execution-metadata/independent-unused-supplement.json'
check('owned metadata JSON path', lambda: m.metadata_record_path(owned))
check('metadata JSON outside metadata roots', lambda: m.metadata_record_path(WORK / 'misc/independent-unused.json'), True)
check('metadata evidence outside run roots',
      lambda: m.metadata_evidence_path(REPORT.parent / 'independent-unused.json'), True)
check('metadata evidence cannot read capsule',
      lambda: m.metadata_evidence_path(WORK / 'snapshot-input-02/manifest.json'), True)

old_ast = ast.parse(BASE.read_text(encoding='utf-8'))
new_ast = ast.parse(DRIVER.read_text(encoding='utf-8'))
functions = lambda tree: {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, ast.FunctionDef)}
old_functions, new_functions = functions(old_ast), functions(new_ast)
changed = sorted(name for name in old_functions if old_functions[name] != new_functions[name])
critical = ['binding', 'bootstrap', 'fixed_grant', 'provider_evidence', 'module_pin', 'safe', 'inside', 'inventory']
assert all(old_functions[name] == new_functions[name] for name in critical)
assert changed == ['main', 'prepare', 'previous_revision', 'recheck', 'run', 'scoped_review', 'text_pin']
calls = [node for node in ast.walk(new_ast) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
         and isinstance(node.func.value, ast.Name) and node.func.value.id == 'workflow' and node.func.attr == 'document']
assert len(calls) == 1 and 'analysis_job' not in {x.arg for x in calls[0].keywords}
assert {'revision_context', 'deadline', 'timeout'} <= {x.arg for x in calls[0].keywords}

schemas = []
for name, (path, expected) in m.METADATA_SCHEMAS.items():
    assert sha(path) == expected
    value = json.loads(path.read_text(encoding='utf-8'))
    assert value['additionalProperties'] is False
    assert value['properties']['businessEvidenceAuthority']['const'] is False
    assert value['properties']['newSourceReadPermissions']['const'] is False
    if name != 'supplement':
        assert value['properties']['formalPercentage']['const'] is None
        assert value['properties']['published']['const'] is False
    schemas.append({'kind': name, 'path': str(path), 'sha256': expected})

prior_report = REPORT / 'independent-audit/writer-metadata-r05-bounded-probes-r02.json'
prior = json.loads(prior_report.read_text(encoding='utf-8'))
assert prior['driverSha256'] == EXPECTED and prior['passed'] == 40 and prior['probeCount'] == 40
prior_probe = next(x for x in prior['probes'] if x['name'] == 'routing record outside owned region refused')
assert prior_probe['detail']['type'] == 'FileNotFoundError'
revised_report = REPORT / 'independent-audit/writer-metadata-r05-bounded-probes-r03.json'
revised_sha = '635595f3269bf50e2b68ad05fb4bf7139fcb7f0d31a8053807ce06a1c38bcc23'
assert sha(revised_report) == revised_sha
revised = json.loads(revised_report.read_text(encoding='utf-8'))
assert revised['driverSha256'] == EXPECTED and revised['passed'] == 40 and revised['probeCount'] == 40
revised_probe = next(x for x in revised['probes'] if x['name'] == 'routing record outside owned region refused')
assert revised_probe['detail']['type'] == 'ValueError'

assert sha(DRIVER) == EXPECTED and sha(BASE) == EXPECTED_BASE
assert not any(name == 'contextbase' or name.startswith('contextbase.') for name in sys.modules)
report = {
    'schema': 'spec-agent-writer-metadata-independent-code-audit/1',
    'createdAt': datetime.now(timezone.utc).isoformat(),
    'reviewer': '/root/author_metadata_extension/metadata_r05_review',
    'status': 'APPROVED_CODE_SCOPE_WITH_EXPLICIT_LIMITATIONS',
    'driver': str(DRIVER), 'driverSha256': EXPECTED, 'base': str(BASE), 'baseSha256': EXPECTED_BASE,
    'readScope': 'candidate/base code, static schemas and metadata-only synthetic-probe report',
    'schemas': schemas,
    'changedExistingFunctions': changed,
    'unchangedBaseBindingFunctions': critical,
    'frozenWorkflowDocumentCalls': 1, 'analysisReusePassed': False,
    'independentPureChecks': {'count': len(checks), 'passed': sum(x['passed'] for x in checks), 'checks': checks},
    'authorBoundedProbeReportsInspected': [
        {'path': str(prior_report), 'sha256': sha(prior_report), 'scope': '40/40 reported but one containment test was FileNotFoundError'},
        {'path': str(revised_report), 'sha256': revised_sha, 'scope': '40/40 revised synthetic probes; correct outside-record guard rejection; author-run not independently rerun'}
    ],
    'blockingCandidateFindings': [],
    'limitations': [
        {'id': 'META-L01', 'location': 'with_execution_metadata completion-evidence loop',
         'description': 'Completion evidence is bounded and byte-pinned JSON, not parsed/validated for document identity, result schema or successful status. RECORDED is an audited record declaration rather than qualified completion.',
         'requiredExternalCheck': 'Root must validate each supplied evidence association/status; final collector/native/delivery gates remain authoritative.'},
        {'id': 'META-L02', 'location': 'with_execution_metadata routing-locations loop',
         'description': 'Routing scope, format and normalized relative path are checked, but target locations are not checked against the publisher layout or cross-document collisions.',
         'requiredExternalCheck': 'Root must supply audited current-run routing; final bundle manifest/link/collision validation is still required.'},
        {'id': 'META-L03', 'location': str(prior_report),
         'description': 'One existing negative probe changed routePath without updating the supplement reference and rejected on FileNotFoundError. That probe does not verify routing-record containment.',
         'independentCoverage': 'The pure path guard is exercised independently here; author r03 corrected the stale-reference fixture and reports a genuine ValueError containment rejection. No production supplemental binding behavior is claimed.'},
        {'id': 'META-L04', 'location': 'previous_execution_metadata / revision integration',
         'description': 'Previous metadata binding/review/raw artifact verification was inspected in code only; no production previous-provider or activation artifacts were read.'}
    ],
    'positiveReviewConclusions': [
        'Optional supplement reaches only exact selected index/analysis-report IDs and exact planned kind/path.',
        'Original execution context is retained in full and supplemental scope separately labelled.',
        'Fresh frozen workflow.document remains the only composite generator; no frozen code or prompts replaced.',
        'Scoped independent review receives separate metadata marker, exact current Markdown and complete original context.',
        'Raw current-run draft/review and previous metadata context are preserved for fresh revisions.',
        'Supplement/schema/record/evidence pins are carried through composite generation, scoped review, final pin and wave completion.',
        'The code explicitly declines internal-callback, atomic/race-free, formal percentage, native or application-runtime proof.'
    ],
    'actualActivationBindingVerified': False, 'actualPreviousProviderArtifactsVerified': False,
    'actualGenerationExecuted': False, 'actualIndependentReviewExecuted': False,
    'actualNativeOrFormalQualification': False, 'sourceOrOriginalSpecificationsRead': False,
    'oldOutputOrEvaluationExpectationsRead': False, 'frozenCoreOrLoadedPromptModified': False,
    'providerStarts': 0, 'candidateModified': False
}
assert all(x['passed'] for x in checks)
with OUT.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'report': str(OUT), 'sha256': sha(OUT), 'status': report['status'],
                  'pureChecks': len(checks), 'passed': len(checks), 'providerStarts': 0}, ensure_ascii=False))
