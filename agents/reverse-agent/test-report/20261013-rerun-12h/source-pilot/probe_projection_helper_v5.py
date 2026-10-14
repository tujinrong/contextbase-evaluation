"""Synthetic delta checks for schema transport and fixed canonical review guards."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

report = Path(__file__).resolve().parent
helper = report / 'prepare_state_projection_detail07_v5.py'
code = helper.read_bytes()
tree = ast.parse(code.decode('utf-8'))
selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and
            node.name in {'validate_transport_schema', 'validate_approved_review'}]
schemas = [node for node in tree.body if isinstance(node, ast.Assign) and
           any(isinstance(target, ast.Name) and target.id in {'ref_schema', 'location_schema', 'schema'}
               for target in node.targets)]
namespace = {'hashlib': hashlib, 'json': json, 'drafts': [{'sha256': '0' * 64}],
             'state': {'manifestSha256': '1' * 64}}
exec(compile(ast.Module(body=selected + schemas, type_ignores=[]), str(helper), 'exec'), namespace)
observations = []
def record(name, callback, reject=False):
    try:
        callback()
        rejected = False
    except ValueError:
        rejected = True
    if rejected != reject:
        raise ValueError('unexpected synthetic gate result: ' + name)
    observations.append({'name': name, 'expectedReject': reject, 'actualRejected': rejected, 'pass': True})
schema = namespace['schema']
record('typed production schema + CLI serialization', lambda: namespace['validate_transport_schema'](schema))
for field in ['reviewScope', 'snapshotManifestSha256']:
    bad = deepcopy(schema)
    del bad['properties'][field]['type']
    record('untyped enum ' + field, lambda bad=bad: namespace['validate_transport_schema'](bad), True)
bad = deepcopy(schema)
bad['properties']['states']['items']['properties']['id'] = {'const': 'normal'}
record('nested untyped const state id', lambda: namespace['validate_transport_schema'](bad), True)

review = {'approved': True, 'findings': [], 'documentId': 'synthetic'}
review_bytes = json.dumps(review).encode()
review_sha = hashlib.sha256(review_bytes).hexdigest()
handoff = {'schema': 'reverse-ai-review-handoff/1', 'approved': True, 'reviewScope': 'text-source-and-structure',
           'referenceMode': 'source-only', 'snapshot': {'mode': 'source-only', 'manifestSha256': '1' * 64},
           'documentFile': 'synthetic-canonical.md', 'documentSha256': '0' * 64, 'reviewSha256': review_sha}
handoff_bytes = json.dumps(handoff).encode()
kwargs = dict(expected_handoff_sha256=hashlib.sha256(handoff_bytes).hexdigest(),
              expected_review_sha256=review_sha, document_file='synthetic-canonical.md',
              document_sha256='0' * 64, snapshot_sha256='1' * 64)
guard = namespace['validate_approved_review']
record('approved exact review', lambda: guard(handoff_bytes, review_bytes, **kwargs))
record('handoff bytes drift', lambda: guard(handoff_bytes + b' ', review_bytes, **kwargs), True)
record('verified review bytes drift', lambda: guard(handoff_bytes, review_bytes + b' ', **kwargs), True)
for name, value in [('approved', False), ('reviewScope', 'visual-only'), ('referenceMode', 'other-mode'),
                    ('documentFile', 'other.md'), ('documentSha256', '2' * 64), ('reviewSha256', '3' * 64)]:
    bad = deepcopy(handoff)
    bad[name] = value
    raw = json.dumps(bad).encode()
    altered = {**kwargs, 'expected_handoff_sha256': hashlib.sha256(raw).hexdigest()}
    record('semantic pin ' + name, lambda raw=raw, altered=altered: guard(raw, review_bytes, **altered), True)
for name, value in [('mode', 'other-mode'), ('manifestSha256', '4' * 64)]:
    bad = deepcopy(handoff)
    bad['snapshot'][name] = value
    raw = json.dumps(bad).encode()
    altered = {**kwargs, 'expected_handoff_sha256': hashlib.sha256(raw).hexdigest()}
    record('snapshot pin ' + name, lambda raw=raw, altered=altered: guard(raw, review_bytes, **altered), True)
result = {'classification': 'SYNTHETIC_SCHEMA_AND_APPROVED_REVIEW_DELTA_PROBE',
          'createdAt': datetime.now(timezone.utc).isoformat(), 'helperFile': str(helper),
          'helperSha256': hashlib.sha256(code).hexdigest(), 'cases': observations,
          'allCasesPass': True, 'productionSourceDraftOrRuntimeRead': False,
          'providerExecuted': False, 'helperTopLevelExecuted': False, 'liveCLITransportAccepted': False}
output = report / 'state-projection-detail07-v5-delta-probe.json'
with output.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'file': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                  'passCount': len(observations)}, ensure_ascii=False))
