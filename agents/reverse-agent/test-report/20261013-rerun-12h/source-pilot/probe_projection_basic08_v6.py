"""AST-only synthetic runtime identity/schema checks; no production data or provider."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

report = Path(__file__).resolve().parent
helper = report / 'prepare_state_projection_basic08_v6.py'
code = helper.read_bytes()
tree = ast.parse(code.decode('utf-8'))
names = ('contextbase', 'contextbase.__main__', 'contextbase.ai', 'contextbase.ai.__main__',
         'contextbase.ai.workflow', 'contextbase.ai.provider', 'contextbase.ai.prompts', 'contextbase.ai.schemas',
         'contextbase.ai.validation', 'contextbase.ai.iteration', 'contextbase.ai.document_contract', 'docsite', 'specgen')
runtime = Path('D:/synthetic-runtime')
def module_path(name):
    return str(runtime / ('/'.join(name.split('.')) + ('/__init__.py' if name in {'contextbase','contextbase.ai','docsite','specgen'} else '.py')))
resolved = {name: module_path(name) for name in names}
critical = ('contextbase.ai.capsule', 'contextbase.ai.workflow', 'contextbase.ai.provider',
            'contextbase.ai.prompts', 'contextbase.ai.schemas', 'contextbase.ai.validation')
loaded = {name: module_path(name) for name in critical}
freeze = {'imports': deepcopy(resolved), 'files': {'/'.join(name.split('.')) + '.py': 'synthetic-sha' for name in critical}}
fake_imports = SimpleNamespace(import_module=lambda name: SimpleNamespace(__file__=loaded[name]),
    util=SimpleNamespace(find_spec=lambda name: SimpleNamespace(origin=resolved[name])))
namespace = {'Path': Path, 'capsule': SimpleNamespace(safe_path=lambda path: Path(path)),
             'importlib': fake_imports, 'runtime': runtime, 'freeze': freeze, 'json': json,
             'drafts': [{'sha256': '0'*64}], 'state': {'manifestSha256': '1'*64}}
selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in {'runtime_import_pin', 'validate_transport_schema'}]
assignments = [node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name)
               and t.id in {'critical_module_names','ref_schema','location_schema','schema'} for t in node.targets)]
exec(compile(ast.Module(body=selected + assignments, type_ignores=[]), str(helper), 'exec'), namespace)
cases = []
def record(name, callback, reject=False):
    try:
        callback()
        rejected = False
    except ValueError:
        rejected = True
    if rejected != reject:
        raise ValueError('unexpected synthetic result: ' + name)
    cases.append({'name': name, 'expectedReject': reject, 'actualRejected': rejected, 'pass': True})
pin = namespace['runtime_import_pin']
record('critical6 exactfiles + all13 resolved positive', pin)
original_loaded = deepcopy(loaded)
loaded['contextbase.ai.provider'] = module_path('contextbase.ai.schemas')
record('loaded module same-root wrong file', pin, True)
loaded.update(original_loaded)
loaded['contextbase.ai.capsule'] = 'D:/outside-runtime/capsule.py'
record('loaded capsule outside exact inventoried file', pin, True)
loaded.update(original_loaded)
resolved['contextbase.ai.provider'] = module_path('contextbase.ai.schemas')
record('resolved import drift', pin, True)
resolved.update(freeze['imports'])
saved = freeze['files'].pop('contextbase/ai/capsule.py')
record('critical capsule absent from inventory', pin, True)
freeze['files']['contextbase/ai/capsule.py'] = saved
freeze['imports']['contextbase.ai.provider'] = module_path('contextbase.ai.schemas')
record('receipt critical import mismatches exactfile', pin, True)
freeze['imports']['contextbase.ai.provider'] = module_path('contextbase.ai.provider')
record('restore positive', pin)
record('typed real schema', lambda: namespace['validate_transport_schema'](namespace['schema']))
bad = deepcopy(namespace['schema'])
del bad['properties']['snapshotManifestSha256']['type']
record('untyped constant enum rejected', lambda: namespace['validate_transport_schema'](bad), True)
result = {'classification': 'SYNTHETIC_PROJECTION_V6_RUNTIME_SCHEMA_DELTA',
          'createdAt': datetime.now(timezone.utc).isoformat(), 'helperFile': str(helper),
          'helperSha256': hashlib.sha256(code).hexdigest(), 'cases': cases, 'allCasesPass': True,
          'providerExecuted': False, 'helperTopLevelExecuted': False, 'productionSourceDraftReceiptOrRuntimeRead': False}
output = report / 'state-projection-basic08-v6-delta-probe.json'
with output.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'file': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'passCount': len(cases)}, ensure_ascii=False))
