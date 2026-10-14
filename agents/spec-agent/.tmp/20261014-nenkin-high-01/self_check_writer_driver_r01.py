"""AST/functions-only synthetic checks; no driver main, production inputs or AI."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace
from jsonschema import Draft202012Validator

BASE = Path(__file__).resolve().parent
DRIVER = BASE / 'nenkin_writer_driver_r01.py'
OUT = BASE / 'author-driver-synthetic-r01'
OUT.mkdir(exist_ok=False)
tree = ast.parse(DRIVER.read_text(encoding='utf-8'))
selected = {'require', 'safe', 'inside', 'raw', 'digest', 'sha', 'pairs', 'load', 'hash_arg', 'inventory', 'module_pin'}
functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in selected]
env = {'Path': Path, 'hashlib': hashlib, 'json': json, 're': re, 'sys': sys}
exec(compile(ast.Module(body=functions, type_ignores=[]), str(DRIVER), 'exec'), env)
cases = []

def case(name, action, accept):
    try:
        action()
        accepted = True
        error = None
    except Exception as exc:
        accepted = False
        error = type(exc).__name__
    cases.append({'name': name, 'expectedAccept': accept, 'accepted': accepted,
        'pass': accepted == accept, 'errorType': error})

activation = json.loads((BASE / 'nenkin_author_activation_schema_r02.json').read_text(encoding='utf-8'))
pin_schema = json.loads((BASE / 'nenkin_text_pin_schema_r02.json').read_text(encoding='utf-8'))
Draft202012Validator.check_schema(activation)
Draft202012Validator.check_schema(pin_schema)
z = '0' * 64
a = {'schema': 'spec-agent-author-activation/1', 'approved': True, 'agentRole': 'AG-SPEC',
    'projectId': 'nenkin', 'mode': 'source-only', 'runId': '20261014-nenkin-high-01',
    'deadline': activation['properties']['deadline']['const'], 'driverSha256': z,
    'capsuleManifestSha256': activation['properties']['capsuleManifestSha256']['const'],
    'executionContextSha256': activation['properties']['executionContextSha256']['const'],
    'runtimeReceiptSha256': activation['properties']['runtimeReceiptSha256']['const'],
    'codeAuditApproved': True, 'codeAudit': {'path': 'toy-audit.json', 'sha256': z},
    'plan': {'path': 'toy-plan.json', 'sha256': z, 'handoffSha256': z},
    'planReview': {'path': 'toy-review.json', 'sha256': z, 'handoffSha256': z},
    'documents': [{'id': 'T-001', 'kind': 'common-specification', 'path': 'toy.md'}],
    'protectedInputSealSha256': z}
case('activation exact typed shape', lambda: Draft202012Validator(activation).validate(a), True)
for key, value in [('approved', False), ('agentRole', 'AG-REVERSE'), ('mode', 'training-assisted'),
    ('projectId', 'other'), ('codeAuditApproved', 1), ('capsuleManifestSha256', z),
    ('deadline', '2026-10-13T20:15:58Z')]:
    bad = deepcopy(a); bad[key] = value
    case('activation rejects ' + key, lambda bad=bad: Draft202012Validator(activation).validate(bad), False)
bad = deepcopy(a); bad['unknown'] = True
case('activation unknown key', lambda: Draft202012Validator(activation).validate(bad), False)
bad = deepcopy(a); del bad['planReview']
case('activation missing review', lambda: Draft202012Validator(activation).validate(bad), False)
runtime = {'record': 'toy.json', 'recordSha256': a['runtimeReceiptSha256'], 'runtimeId': 'source-13',
    'directory': 'toy/runtime', 'fileCount': 128, 'receiptImportCount': 13,
    'promptModuleSha256': pin_schema['$defs']['runtime']['properties']['promptModuleSha256']['const']}
pin = {'schema': 'spec-agent-text-reviewed-document-pin/1', 'documentId': 'T-001', 'path': 'toy.md',
    'kind': 'common-specification', 'canonicalMarkdown': 'toy.md', 'sha256': z,
    'draftResult': 'toy-draft.json', 'draftResultSha256': z, 'independentReview': 'toy-review.json',
    'independentReviewSha256': z, 'structureStatus': 'STRUCTURE_VALID', 'structureFindings': [],
    'independentReviewApproved': True, 'noFurtherTextRevisionPlanned': True,
    'capsule': {'manifestSha256': a['capsuleManifestSha256'], 'mode': 'source-only'},
    'basisCounts': {'observed-source': 1, 'reference-design': 0}, 'generationRuntime': runtime,
    'reviewRuntime': runtime, 'structureRuntime': runtime, 'disposition': 'specification',
    'includedInFinalSpecificationBundle': True, 'reviewScope': 'text-source-and-structure',
    'visualFidelityVerified': False, 'formalScoringVerified': False, 'published': False,
    'businessProseAssembledByPython': False}
case('text pin exact generic fields', lambda: Draft202012Validator(pin_schema).validate(pin), True)
rp = deepcopy(pin); rp.update({'kind': 'analysis-report', 'disposition': 'report-only', 'includedInFinalSpecificationBundle': False})
case('report pin segregated', lambda: Draft202012Validator(pin_schema).validate(rp), True)
rp['includedInFinalSpecificationBundle'] = True
case('report cannot enter specification bundle', lambda: Draft202012Validator(pin_schema).validate(rp), False)
for key, value in [('independentReviewApproved', False), ('noFurtherTextRevisionPlanned', False),
    ('structureStatus', 'STRUCTURE_INVALID'), ('reviewScope', 'native'), ('visualFidelityVerified', True),
    ('formalScoringVerified', True), ('published', True)]:
    bad_pin = deepcopy(pin); bad_pin[key] = value
    case('pin rejects ' + key, lambda bad_pin=bad_pin: Draft202012Validator(pin_schema).validate(bad_pin), False)
bad_pin = deepcopy(pin); bad_pin['basisCounts']['reference-design'] = 1
case('source-only ref-design count', lambda: Draft202012Validator(pin_schema).validate(bad_pin), False)
case('SHA lowercase accepted', lambda: env['hash_arg']('a' * 64), True)
for invalid in ['A' * 64, 'a' * 63, None, 1]:
    case('SHA rejects ' + repr(invalid), lambda invalid=invalid: env['hash_arg'](invalid), False)
inside = OUT / 'within'; inside.mkdir()
(inside / 'one.txt').write_bytes(b'toy')
case('safe normal read', lambda: env['raw'](inside / 'one.txt'), True)
case('inside rejects root itself', lambda: env['inside'](inside, inside), False)
case('inside rejects outside', lambda: env['inside'](OUT / 'outside.txt', inside), False)
case('duplicate JSON member', lambda: env['pairs']([('a', 1), ('a', 2)]), False)
inv = env['inventory'](inside)
case('inventory ordinary file', lambda: env['require'](inv == {'one.txt': {'bytes': 3, 'sha256': hashlib.sha256(b'toy').hexdigest()}}, 'inventory'), True)
rt = OUT / 'runtime'; rt.mkdir()
module = rt / 'toy.py'; module.write_bytes(b'toy-code-no-execution')
env['RUNTIME'] = rt
spy = []
expected_module = SimpleNamespace(__file__=str(module), __spec__=SimpleNamespace(origin=str(module)))
expected_import = SimpleNamespace(util=SimpleNamespace(find_spec=lambda name: SimpleNamespace(origin=str(module))),
    import_module=lambda name: (spy.append(name) or expected_module))
env['importlib'] = expected_import
files = {'toy.py': hashlib.sha256(module.read_bytes()).hexdigest()}
case('exact module file/spec/hash', lambda: env['module_pin']('toy.not_loaded', module, files), True)
spy.clear(); env['importlib'] = SimpleNamespace(util=SimpleNamespace(find_spec=lambda name: SimpleNamespace(origin=str(rt / 'other.py'))),
    import_module=lambda name: spy.append(name))
case('wrong discovery refused before import', lambda: env['module_pin']('toy.not_loaded', module, files), False)
case('wrong discovery executed import zero', lambda: env['require'](not spy, 'import unexpectedly executed'), True)
env['importlib'] = expected_import
expected_module.__spec__.origin = str(rt / 'other.py')
case('wrong loaded spec refused', lambda: env['module_pin']('toy.not_loaded', module, files), False)
record = {'schema': 'spec-agent-driver-self-check/1', 'createdAt': datetime.now(timezone.utc).isoformat(),
    'driver': str(DRIVER), 'driverSha256': hashlib.sha256(DRIVER.read_bytes()).hexdigest(), 'cases': cases,
    'total': len(cases), 'passed': sum(c['pass'] for c in cases), 'providerCalls': 0,
    'driverMainOrProductionBindingExecuted': False, 'productionSourceOrPlanOrReviewRead': False,
    'scope': 'AST functions and synthetic schema/path/module checks only; not whole-driver, business, native or parent approval'}
with (OUT / 'review.json').open('x', encoding='utf-8', newline='\n') as f:
    json.dump(record, f, ensure_ascii=False, indent=2); f.write('\n')
print(json.dumps({'path': str(OUT / 'review.json'), 'sha256': hashlib.sha256((OUT / 'review.json').read_bytes()).hexdigest(),
    'total': record['total'], 'passed': record['passed'], 'providerCalls': 0}))
raise SystemExit(0 if record['passed'] == record['total'] else 1)
