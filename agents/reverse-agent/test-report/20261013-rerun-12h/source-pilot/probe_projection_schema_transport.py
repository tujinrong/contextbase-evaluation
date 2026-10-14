"""Extract schema assignments only; no provider, source material, or top-level helper execution."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

report = Path(__file__).resolve().parent
helper = report / 'prepare_state_projection_detail06_v4.py'
code = helper.read_bytes()
tree = ast.parse(code.decode('utf-8'))
names = {'ref_schema', 'location_schema', 'schema'}
assignments = [node for node in tree.body if isinstance(node, ast.Assign)
               and any(isinstance(target, ast.Name) and target.id in names for target in node.targets)]
if len(assignments) != 3:
    raise ValueError('schema extraction shape changed')
namespace = {'drafts': [{'sha256': '0' * 64}], 'state': {'manifestSha256': '1' * 64}}
exec(compile(ast.Module(body=assignments, type_ignores=[]), str(helper), 'exec'), namespace)
schema = namespace['schema']
Draft202012Validator.check_schema(schema)
nodes = []
def visit(value, path='$'):
    if isinstance(value, dict):
        if 'enum' in value or 'const' in value:
            if 'type' not in value:
                raise ValueError('transport const/enum node lacks explicit type: ' + path)
            nodes.append({'path': path, 'type': value['type']})
        for key, child in value.items():
            visit(child, path + '.' + key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            visit(child, path + '[' + str(index) + ']')
visit(schema)
example = {
    'reviewScope': 'STATIC_PROJECTION_VS_SOURCE_RESOURCES',
    'snapshotManifestSha256': '1' * 64, 'boundDraftSha256s': ['0' * 64],
    'states': [dict(id=ident, title='Synthetic', canonicalLocations=[], references=[],
                    projectionAssumptions=[], requiresCanonicalRevision=True,
                    canonicalRevisionReason='Synthetic omission', html='')
               for ident in ['normal', 'empty', 'tooMany', 'viewer']],
    'unresolved': [], 'sourcePathsRead': [],
}
Draft202012Validator(schema).validate(example)
transport = json.loads(json.dumps(schema))
if transport != schema:
    raise ValueError('CLI output-schema JSON serialization changed the schema')
visit(transport, 'serializedCLI')
result = {
    'classification': 'SYNTHETIC_SCHEMA_TRANSPORT_TECHNICAL_PROBE',
    'createdAt': datetime.now(timezone.utc).isoformat(),
    'helperFile': str(helper), 'helperSha256': hashlib.sha256(code).hexdigest(),
    'typedEnumOrConstNodes': nodes, 'untypedEnumOrConstCount': 0,
    'draft202012CheckSchemaPass': True, 'syntheticFourStatePass': True,
    'cliTransportSerializationIdentical': True,
    'providerExecuted': False, 'helperTopLevelExecuted': False,
    'productionSourceOrDraftOrRuntimeRead': False,
    'liveCLITransportAccepted': False,
}
output = report / 'state-projection-source-schema-transport-probe-v4.json'
with output.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'file': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                  'untypedNodes': 0, 'schemaPass': True}, ensure_ascii=False))
