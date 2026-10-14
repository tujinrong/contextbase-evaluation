"""Create only actual plan-derived routing metadata; never claim artifact completion."""
import ast
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

WORK = Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01')
REPORT = Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01')
PINS = {
    WORK / 'jobs/plan-04/plan-verified.json': 'e14b5e5acd96aed44c800209efbe452d094cb595f7d57da097b8c9a4a7bc9ee3',
    WORK / 'jobs/plan-04/plan-handoff.json': '2815a418a728f5ba8e71ec8a8d0cf7308b1920ecdf283b6ec9288e0831b68660',
    WORK / 'snapshot-input-02/manifest.json': 'f074529043ff1c25ea53be34c16ae3a4788f137a1e3afb33c6214de7bf4c7445',
    WORK / 'execution-context-input-02.json': '8966757e00954241029817027efa85bafeb859beee5105b05c7c939c84470605',
    WORK / 'delivery/html_routing_projection_r01.py': '542a396124d25f2d279a32430405f336055a4327a46207ef95ce856eff3c5829',
    WORK / 'nenkin_execution_metadata_routing_schema_r01.json': 'de28dbd6b0b72a1f7dbfb8932579197c61a728cca52abb62193183d0e60d609b',
}
PLAN = WORK / 'jobs/plan-04/plan-verified.json'
CAP_SHA = PINS[WORK / 'snapshot-input-02/manifest.json']
CTX_SHA = PINS[WORK / 'execution-context-input-02.json']
PLAN_SHA = PINS[PLAN]

def safe(path):
    path = Path(path).absolute()
    for node in (path, *path.parents):
        if node.exists():
            assert not node.is_symlink() and not (getattr(node.lstat(), 'st_file_attributes', 0) & 0x400), str(node)
    assert path.resolve() == path
    return path

def sha(path):
    return hashlib.sha256(safe(path).read_bytes()).hexdigest()

def pairs(items):
    value = {}
    for key, item in items:
        assert key not in value, 'Duplicate metadata key'
        value[key] = item
    return value

def load(path):
    return json.loads(safe(path).read_bytes().decode('utf-8-sig'), object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite metadata')))

def verify():
    for path, expected in PINS.items():
        assert sha(path) == expected, str(path)

def write(path, value):
    path = safe(path)
    assert path.is_relative_to(REPORT / 'execution-metadata') and not path.exists()
    safe(path.parent).mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    assert load(path) == value

verify()
plan = load(PLAN)
handoff = load(WORK / 'jobs/plan-04/plan-handoff.json')
assert handoff['planSha256'] == PLAN_SHA and handoff['planFile'] == PLAN.name
assert handoff['snapshot']['mode'] == 'source-only' and handoff['snapshot']['manifestSha256'] == CAP_SHA
rows = [{'id': value['id'], 'kind': value['kind'], 'path': value['path']} for value in plan['documents']]
assert len(rows) == 63 and len({row['id'] for row in rows}) == 63
specs = [row for row in rows if row['kind'] != 'analysis-report']
reports = [row for row in rows if row['kind'] == 'analysis-report']
assert len(specs) == 61 and {row['id'] for row in reports} == {'ANL-COVERAGE', 'ANL-TRACEABILITY'}
allowlist = {'schema': 'spec-agent-html-publication-routing/1',
    'runId': '20261014-nenkin-high-01', 'projectId': 'nenkin',
    'capsuleManifestSha256': CAP_SHA, 'executionContextSha256': CTX_SHA, 'planSha256': PLAN_SHA,
    'sourceOnly': True, 'originalApplicationExecuted': False, 'formalPercentage': None,
    'published': False, 'documents': []}
for row in specs:
    path = PurePosixPath(row['path'])
    stem = path.with_suffix('')
    locations = {'md': 'md/' + path.as_posix(),
                 'html': 'html/' + stem.as_posix() + '/' + stem.name + '.html',
                 'pdf': 'PDF/' + stem.as_posix() + '.pdf',
                 'xlsx': 'Excel/' + stem.as_posix() + '.xlsx'}
    allowlist['documents'].append({'documentId': row['id'], 'kind': row['kind'],
                                  'canonicalMarkdownPath': row['path'], 'locations': locations})

# Use only the approved pure shape validator, AST-isolated. No helper module,
# frozen runtime, source code, browser, CLI or renderer imports/calls are needed.
projection_tree = ast.parse((WORK / 'delivery/html_routing_projection_r01.py').read_text(encoding='utf-8-sig'))
names = {'require', 'exact_keys', 'sha_arg', 'windows_component', 'relative_path', 'validate_allowlist'}
nodes = [node for node in projection_tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
nodes += [node for node in projection_tree.body if isinstance(node, ast.ClassDef) and node.name == 'RoutingHold']
nodes += [node for node in projection_tree.body if isinstance(node, ast.Assign) and
          isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'RESERVED']
namespace = {'PurePosixPath': PurePosixPath, 're': re, 'unicodedata': unicodedata,
             'RUN_ID': '20261014-nenkin-high-01', 'PROJECT_ID': 'nenkin',
             'CAPSULE_SHA': CAP_SHA, 'CONTEXT_SHA': CTX_SHA}
exec(compile(ast.Module(body=nodes, type_ignores=[]), '<approved-pure-routing-metadata-validator>', 'exec'), namespace)
validated = namespace['validate_allowlist'](allowlist)
assert list(validated) == [row['id'] for row in specs]

author_routing = {'schema': 'spec-agent-same-run-routing-record/1',
    'runId': '20261014-nenkin-high-01', 'projectId': 'nenkin',
    'capsuleManifestSha256': CAP_SHA, 'executionContextSha256': CTX_SHA, 'planSha256': PLAN_SHA,
    'sourceOnly': True, 'businessEvidenceAuthority': False, 'originalAppExecuted': False,
    'originalSpecificationsAuthorized': False, 'evaluationExpectationsAuthorized': False,
    'newSourceReadPermissions': False, 'documents': [], 'formalPercentage': None, 'published': False}
for item in allowlist['documents']:
    author_routing['documents'].append({'documentId': item['documentId'], 'kind': item['kind'],
        'path': item['canonicalMarkdownPath'], 'disposition': 'specification',
        'locations': [{'scope': 'specification-bundle', 'format': key, 'relativePath': location}
                      for key, location in item['locations'].items()]})
schema = load(WORK / 'nenkin_execution_metadata_routing_schema_r01.json')

def validate_schema_subset(value, definition):
    if 'const' in definition:
        assert value == definition['const'] and type(value) is type(definition['const'])
    if 'enum' in definition:
        assert value in definition['enum']
    dtype = definition.get('type')
    if dtype == 'object':
        assert isinstance(value, dict) and set(definition.get('required', [])) <= set(value)
        if definition.get('additionalProperties') is False:
            assert set(value) <= set(definition['properties'])
        for key, item in value.items():
            validate_schema_subset(item, definition['properties'][key])
    elif dtype == 'array':
        assert isinstance(value, list) and len(value) >= definition.get('minItems', 0)
        for item in value:
            validate_schema_subset(item, definition['items'])
    elif dtype == 'string':
        assert isinstance(value, str) and len(value) >= definition.get('minLength', 0)
        if 'pattern' in definition:
            assert re.fullmatch(definition['pattern'], value)
    assert set(definition) <= {'$schema', 'type', 'additionalProperties', 'required', 'properties', 'const',
                               'enum', 'minItems', 'items', 'minLength', 'pattern'}

validate_schema_subset(author_routing, schema)
assert [(item['documentId'], item['kind'], item['path']) for item in author_routing['documents']] == [tuple(row.values()) for row in specs]
verify()
allowlist_path = REPORT / 'execution-metadata/final-four-folder-routing-plan04-r01.json'
author_path = REPORT / 'execution-metadata/author-four-folder-routing-plan04-r01.json'
write(allowlist_path, allowlist)
write(author_path, author_routing)
verify()
receipt = {'schema': 'spec-agent-plan-derived-routing-preparation/1',
    'createdUtc': datetime.now(timezone.utc).isoformat(), 'status': 'DESCRIPTIVE_ROUTING_METADATA_WRITTEN_ACTUAL_ARTIFACTS_PENDING',
    'projectionAllowlist': {'path': str(allowlist_path), 'sha256': sha(allowlist_path)},
    'reservedIndexRoutingRecord': {'path': str(author_path), 'sha256': sha(author_path)},
    'inputPins': {str(path): expected for path, expected in PINS.items()},
    'inputsBeforeAfterUnchanged': True, 'approvedPlanDocumentCount': 63,
    'specificationRoutingCount': 61, 'declaredFormatLocationCount': 244,
    'excludedReports': reports, 'planOrderPreserved': True,
    'metadataValidationScope': 'Real plan-derived data validated by approved AST-isolated projection shape validator and exact static writer-routing schema vocabulary; no schema/provenance/production pipeline activation implied.',
    'routingRecordEquivalence': True, 'businessProseAssembled': False,
    'completedQualifiedOrExistenceClaimsEmitted': False, 'actualFilesExistenceVerified': False,
    'sourceBusinessOrSpecificationOrOldOutputRead': False,
    'coreHelperProviderRendererBrowserMarkerAuthoringOrPublicationRun': False,
    'newSyntheticSuitesRun': False, 'nativeApproval': False, 'formalPercentage': None, 'published': False,
    'independentReview': 'PENDING', 'script': {'path': str(Path(__file__)), 'sha256': sha(Path(__file__))}}
receipt_path = REPORT / 'independent-audit/final-routing-plan04-preparation-r01.json'
with receipt_path.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(receipt, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'allowlist': str(allowlist_path), 'allowlistSha256': sha(allowlist_path),
                  'authorRouting': str(author_path), 'authorRoutingSha256': sha(author_path),
                  'receipt': str(receipt_path), 'receiptSha256': sha(receipt_path)}, ensure_ascii=False))
