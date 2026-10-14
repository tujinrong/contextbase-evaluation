"""Fresh synthetic self-check builder; no production binding or provider."""
from pathlib import Path
BASE = Path(__file__).parent
source = (BASE / 'self_check_writer_driver_r01.py').read_text(encoding='utf-8')
source = source.replace('nenkin_writer_driver_r01.py', 'nenkin_writer_driver_r02.py').replace('author-driver-synthetic-r01', 'author-driver-synthetic-r02')
source = source.replace('nenkin_author_activation_schema_r02.json', 'nenkin_author_activation_schema_r03.json').replace('nenkin_text_pin_schema_r02.json', 'nenkin_text_pin_schema_r03.json')
source = source.replace("'module_pin'}", "'module_pin', 'provider_evidence', 'prompt_object'}")
source = source.replace("activation['properties']['capsuleManifestSha256']['const']", 'z')
source = source.replace("activation['properties']['executionContextSha256']['const']", 'z')
source = source.replace("'protectedInputSealSha256': z}", "'protectedInputSealSha256': z, 'capsuleRoot': 'toy/snapshot-input-02', 'executionContext': 'toy/context-input-02.json'}")
source = source.replace("('capsuleManifestSha256', z)", "('capsuleManifestSha256', 'A' * 64)")
extra = r'''
# Actual AST provider-evidence function runs against toy raw4 and before/after2 only.
env['WORK'] = OUT / 'toy-work'
job = env['WORK'] / 'jobs/author-wave-01/toy/draft'
job.mkdir(parents=True)
snap = env['WORK'] / 'snapshot-input-02'
snap.mkdir()
state = {'mode': 'source-only', 'manifestSha256': z}
schema = {'type': 'object', 'required': ['documentId'], 'properties': {'documentId': {'const': 'TOY'}}}
answer = {'documentId': 'TOY'}
def jwrite(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')
jwrite(job / 'answer.txt', answer)
jwrite(job / 'schema.json', schema)
(job / 'prompt.txt').write_text('toy prompt', encoding='utf-8')
result = {'exit_code': 0, 'answer': answer, 'metadata': {'status': 'passed', 'schema_supplied': True,
    'workspace': str(snap), 'reference_mode': 'source-only', 'training_reference_authorized': False,
    'error_events': [], 'invalid_event_lines': [], 'answer_sha256': env['sha'](job / 'answer.txt'),
    'prompt_sha256': env['sha'](job / 'prompt.txt')}}
jwrite(job / 'result.json', result)
jwrite(job.parent / 'draft-snapshot-before.json', state)
jwrite(job.parent / 'draft-snapshot-after.json', {'status': 'UNCHANGED', 'before': state, 'after': state})
case('toy provider raw4 evidence2 accepted', lambda: env['provider_evidence'](snap, job, schema, state), True)
for key, value in [('status', 'failed'), ('schema_supplied', 1), ('workspace', 'outside'),
    ('reference_mode', 'training-assisted'), ('training_reference_authorized', True), ('answer_sha256', '1'*64),
    ('prompt_sha256', '1'*64), ('error_events', ['error']), ('invalid_event_lines', ['bad'])]:
    bad = deepcopy(result); bad['metadata'][key] = value; jwrite(job / 'result.json', bad)
    case('provider rejects ' + key, lambda: env['provider_evidence'](snap, job, schema, state), False)
jwrite(job / 'result.json', result)
bad = deepcopy(result); bad['answer'] = {'documentId': 'OTHER'}; jwrite(job / 'result.json', bad)
case('provider rejects result response drift', lambda: env['provider_evidence'](snap, job, schema, state), False)
jwrite(job / 'result.json', result)
jwrite(job / 'schema.json', {'type': 'object'})
case('provider rejects schema drift', lambda: env['provider_evidence'](snap, job, schema, state), False)
jwrite(job / 'schema.json', schema)
jwrite(job.parent / 'draft-snapshot-after.json', {'status': 'UNCHANGED', 'before': state, 'after': {'mode': 'other'}})
case('provider rejects after capsule drift', lambda: env['provider_evidence'](snap, job, schema, state), False)
case('prompt exact typed object', lambda: env['require'](env['prompt_object']('prefix\nMARK\n{"id":"TOY"}\nsuffix', '\nMARK\n') == {'id':'TOY'}, 'object'), True)
case('prompt missing marker', lambda: env['prompt_object']('prefix', '\nMARK\n'), False)
case('prompt invalid JSON', lambda: env['prompt_object']('\nMARK\nwrong', '\nMARK\n'), False)
'''
source = source.replace("record = {'schema':", extra + "\nrecord = {'schema':")
with (BASE / 'self_check_writer_driver_r02.py').open('x', encoding='utf-8', newline='\n') as out:
    out.write(source)
