"""AST-only previous-revision guards with toy delegated checkpoint/validation."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from types import ModuleType, SimpleNamespace

BASE = Path(__file__).parent
DRIVER = BASE / 'nenkin_writer_driver_r02.py'
OUT = BASE / 'author-revision-synthetic-r02'
OUT.mkdir(exist_ok=False)
WORK = OUT / 'toy-work'
snapshot = WORK / 'snapshot-input-02'
snapshot.mkdir(parents=True)
tree = ast.parse(DRIVER.read_text(encoding='utf-8'))
names = {'require', 'safe', 'inside', 'raw', 'digest', 'sha', 'pairs', 'load', 'hash_arg',
    'provider_evidence', 'prompt_object', 'previous_revision', 'recheck_previous'}
env = {'Path': Path, 'hashlib': hashlib, 'json': json, 're': re, 'WORK': WORK, 'RECEIPT_SHA': 'f'*64}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), str(DRIVER), 'exec'), env)

definition = {'id': 'TOY-01', 'path': 'toy.md', 'kind': 'common-specification'}
context = {'schema': 'toy-context', 'sourceOnly': True}
state = {'mode': 'source-only', 'manifestSha256': '0'*64}
pin = {'snapshotRoot': str(snapshot), 'snapshot': state, 'planSha256': 'a'*64, 'executionContextSha256': 'b'*64}
folder = env['digest'](b'TOY-01')[:16]
generation = WORK / 'jobs/author-wave-01' / folder
generation.mkdir(parents=True)
output = WORK / 'drafts/author-wave-01/specifications'
output.mkdir(parents=True)
document = output / 'toy.md'
document.write_bytes(b'toy body')
analysis = {'documentId': 'TOY-01', 'facts': []}
checkpoint = {'providerDirectory': 'analysis', 'providerArtifactsSha256': {}, 'snapshotEvidenceSha256': {}}
structure_findings = []

pkg = ModuleType('contextbase'); pkg.__path__ = []
ai = ModuleType('contextbase.ai'); ai.__path__ = []
validation = ModuleType('contextbase.ai.validation')
schemas = SimpleNamespace(DRAFT={'type': 'object'}, REVIEW={'type': 'object'})
delegate_calls = []
workflow = SimpleNamespace(_resume_analysis=lambda s,d,g: (delegate_calls.append('readonly_resume') or
    (analysis, deepcopy(checkpoint), env['sha'](generation / 'analysis-handoff.json'))),
    references_valid=lambda review, manifest: delegate_calls.append('references'))
capsule = SimpleNamespace(verify=lambda s: {'toy': True})
validation.validate_document = lambda *args, **kwargs: deepcopy(structure_findings)
ai.workflow = workflow; ai.capsule = capsule; ai.schemas = schemas
sys.modules.update({'contextbase': pkg, 'contextbase.ai': ai, 'contextbase.ai.validation': validation})

def jwrite(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')

def provider(stage, answer, prompt, schema):
    job = generation / stage
    job.mkdir(exist_ok=True)
    jwrite(job / 'answer.txt', answer)
    jwrite(job / 'schema.json', schema)
    (job / 'prompt.txt').write_text(prompt, encoding='utf-8')
    jwrite(job / 'result.json', {'exit_code': 0, 'answer': answer, 'metadata': {'status': 'passed',
        'schema_supplied': True, 'workspace': str(snapshot), 'reference_mode': 'source-only',
        'training_reference_authorized': False, 'error_events': [], 'invalid_event_lines': [],
        'answer_sha256': env['sha'](job / 'answer.txt'), 'prompt_sha256': env['sha'](job / 'prompt.txt')}})
    jwrite(generation / (stage + '-snapshot-before.json'), state)
    jwrite(generation / (stage + '-snapshot-after.json'), {'status': 'UNCHANGED', 'before': state, 'after': state})

draft = {'documentId': 'TOY-01', 'path': 'toy.md', 'content': 'toy body'}
review = {'documentId': 'TOY-01', 'approved': False, 'unresolved': [], 'findings': []}
original_prefix = '\n対象文書計画:\n' + json.dumps(definition)
draft_prompt = original_prefix + '\n前の原稿への原文根拠付き批評（正解期待値ではありません）:\n' + json.dumps(context) + '\nAIによる解析素材:\n' + json.dumps(analysis)
review_prompt = original_prefix + '\nユーザー指定scopeのメタデータ全文（原文・期待仕様・追加読取り許可ではありません）:\n' + json.dumps(context) + '\n原稿本文:\n' + 'toy body' + '\n構造検査の指摘（意味の正確さを採点した結果ではありません）:\n[]'
provider('draft', draft, draft_prompt, schemas.DRAFT)
provider('independent-review', review, review_prompt, schemas.REVIEW)
for name in ('answer.txt', 'result.json', 'schema.json', 'prompt.txt'):
    jwrite(generation / 'analysis' / name, {'toy': name})
    checkpoint['providerArtifactsSha256'][name] = env['sha'](generation / 'analysis' / name)
for suffix in ('before', 'after'):
    name = 'analysis-snapshot-' + suffix + '.json'
    jwrite(generation / name, {'toy': suffix})
    checkpoint['snapshotEvidenceSha256'][name] = env['sha'](generation / name)
jwrite(generation / 'analysis-handoff.json', checkpoint)
jwrite(generation / 'analysis-verified.json', analysis)
jwrite(generation / 'draft-result.json', {'documentId': 'TOY-01', 'path': 'toy.md',
    'contentSha256': env['sha'](document), 'snapshot': state, 'referenceMode': 'source-only',
    'aiAuthored': True, 'semanticProseAssembledByPython': False, 'structureFindings': []})
jwrite(generation / 'document-structure.json', {'documentId': 'TOY-01', 'contentSha256': env['sha'](document),
    'status': 'STRUCTURE_VALID', 'findings': []})
verified = generation / 'independent-review/review-verified.json'
verified.write_bytes((generation / 'independent-review/answer.txt').read_bytes())
jwrite(generation / 'independent-review/review-handoff.json', {'schema': 'reverse-ai-review-handoff/1',
    'snapshot': state, 'documentFile': str(document), 'documentSha256': env['sha'](document),
    'reviewSha256': env['sha'](verified), 'approved': False, 'executionContextSha256': 'b'*64,
    'referenceMode': 'source-only', 'aiResponseBytesModified': False})
result = {'schema': 'spec-agent-author-document-result/1', 'documentId': 'TOY-01', 'path': 'toy.md',
    'kind': 'common-specification', 'capsule': state, 'planSha256': 'a'*64, 'executionContextSha256': 'b'*64,
    'runtimeReceiptSha256': 'f'*64, 'status': 'REQUIRES_AI_REVISION', 'draft': {'canonicalMarkdown': str(document),
    'sha256': env['sha'](document), 'outputRoot': str(output), 'draftResult': str(generation / 'draft-result.json'),
    'draftResultSha256': env['sha'](generation / 'draft-result.json')}, 'review': {'path': str(verified),
    'sha256': env['sha'](verified), 'approved': False, 'verified': True}}
result_path = generation / 'author-document-result.json'
jwrite(result_path, result)
cases = []
def case(name, action, accept):
    try:
        action(); accepted=True; error=None
    except Exception as exc:
        accepted=False; error=type(exc).__name__ + ': ' + str(exc)
    cases.append({'name': name, 'expectedAccept': accept, 'accepted': accepted, 'pass': accept == accepted, 'error': error})
def check():
    return env['previous_revision'](result_path, env['sha'](result_path), definition, pin, context)
case('whole toy prior draft-review bound', check, True)
prior, payload = check()
case('whole text and review preserved without edits', lambda: env['require'](payload['previousCanonicalMarkdown'] == 'toy body' and payload['preservedIndependentReview'] == review and payload['executionContext'] == context and prior['analysisWillBeReused'] is False, 'payload'), True)
for key, value in [('documentId','OTHER'),('path','other.md'),('kind','basic-design'),('capsule',{'mode':'other'}),
    ('planSha256','c'*64),('executionContextSha256','c'*64),('runtimeReceiptSha256','c'*64),('status','FAILED')]:
    bad = deepcopy(result); bad[key]=value; jwrite(result_path,bad)
    case('previous rejects '+key, check, False)
jwrite(result_path,result)
case('previous rejects wrong result SHA', lambda: env['previous_revision'](result_path,'c'*64,definition,pin,context), False)
old_body=document.read_bytes(); document.write_bytes(b'changed')
case('previous rejects Markdown drift', check, False)
document.write_bytes(old_body)
old_prompt=(generation/'independent-review/prompt.txt').read_bytes()
provider('independent-review', review, review_prompt.replace('toy body','different body'), schemas.REVIEW)
case('previous rejects review whole-body mismatch', check, False)
provider('independent-review',review,review_prompt,schemas.REVIEW)
old_struct=(generation/'document-structure.json').read_bytes()
jwrite(generation/'document-structure.json', {'documentId':'TOY-01','contentSha256':env['sha'](document),'findings':['bad'],'status':'STRUCTURE_VALID'})
case('previous rejects structure record drift',check,False)
(generation/'document-structure.json').write_bytes(old_struct)
old_handoff=(generation/'independent-review/review-handoff.json').read_bytes()
h=json.loads(old_handoff);h['approved']=True;jwrite(generation/'independent-review/review-handoff.json',h)
case('previous rejects handoff approved drift',check,False)
(generation/'independent-review/review-handoff.json').write_bytes(old_handoff)
case('previous after restoration accepted',check,True)
record={'schema':'spec-agent-driver-revision-self-check/1','createdAt':datetime.now(timezone.utc).isoformat(),
    'driver':str(DRIVER),'driverSha256':hashlib.sha256(DRIVER.read_bytes()).hexdigest(),'cases':cases,
    'total':len(cases),'passed':sum(x['pass'] for x in cases),'providerCalls':0,'delegateCalls':delegate_calls,
    'scope':'actual previous_revision AST with toy raw files; frozen resume/references/structure are mocks, not core/production validation',
    'productionSourceOrPlanOrReviewRead':False,'mainPrepareRunOrProviderExecuted':False,'parentApproval':False}
target=OUT/'review.json';jwrite(target,record)
print(json.dumps({'path':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'total':record['total'],'passed':record['passed'],'providerCalls':0}))
raise SystemExit(0 if record['total']==record['passed'] else 1)
