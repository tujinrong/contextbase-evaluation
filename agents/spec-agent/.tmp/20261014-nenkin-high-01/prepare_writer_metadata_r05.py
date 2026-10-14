"""Code-only preparation of optional, typed current-run metadata boundaries."""
from pathlib import Path
import ast, hashlib, json

ROOT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
REPORT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
BASE = ROOT / 'nenkin_writer_driver_r04.py'
EXPECTED = 'ce836766e61f5abad0fc4d2abfe11b3c6e6588f4dc8b9d46f62f913f0cd8e664'

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert sha(BASE) == EXPECTED
source = BASE.read_text(encoding='utf-8')
sha_def = {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}
file_def = {'type': 'object', 'additionalProperties': False,
    'required': ['path', 'sha256'], 'properties': {
        'path': {'type': 'string', 'minLength': 1}, 'sha256': sha_def}}
identity = {'runId': {'const': '20261014-nenkin-high-01'}, 'projectId': {'const': 'nenkin'},
    'capsuleManifestSha256': sha_def, 'executionContextSha256': sha_def, 'planSha256': sha_def,
    'sourceOnly': {'const': True}, 'businessEvidenceAuthority': {'const': False},
    'originalAppExecuted': {'const': False}, 'originalSpecificationsAuthorized': {'const': False},
    'evaluationExpectationsAuthorized': {'const': False}, 'newSourceReadPermissions': {'const': False}}
doc = {'type': 'object', 'additionalProperties': False, 'required': ['documentId', 'kind', 'path'],
    'properties': {name: {'type': 'string', 'minLength': 1} for name in ['documentId', 'kind', 'path']}}
location = {'type': 'object', 'additionalProperties': False,
    'required': ['scope', 'format', 'relativePath'], 'properties': {
        'scope': {'enum': ['specification-bundle', 'execution-report']},
        'format': {'enum': ['md', 'html', 'pdf', 'xlsx', 'json']},
        'relativePath': {'type': 'string', 'minLength': 1}}}
route_doc = json.loads(json.dumps(doc))
route_doc['required'] += ['disposition', 'locations']
route_doc['properties'].update({'disposition': {'enum': ['specification', 'report-only']},
    'locations': {'type': 'array', 'minItems': 1, 'items': location}})
completion_doc = json.loads(json.dumps(doc))
completion_doc['required'] += ['recordStatus', 'evidence']
completion_doc['properties'].update({'recordStatus': {'enum': ['NOT_RUN', 'IN_PROGRESS', 'RECORDED', 'FAILED']},
    'evidence': {'type': 'array', 'items': file_def}})
schemas = {}
for key, schema_id, entry in [('routing', 'spec-agent-same-run-routing-record/1', route_doc),
        ('completion', 'spec-agent-same-run-completion-record/1', completion_doc)]:
    schemas[key] = {'$schema': 'https://json-schema.org/draft/2020-12/schema',
        'type': 'object', 'additionalProperties': False,
        'required': ['schema', *identity, 'documents', 'formalPercentage', 'published'],
        'properties': {'schema': {'const': schema_id}, **identity,
            'documents': {'type': 'array', 'minItems': 1, 'items': entry},
            'formalPercentage': {'const': None}, 'published': {'const': False}}}
ref = json.loads(json.dumps(file_def))
ref['required'] += ['kind']
ref['properties']['kind'] = {'enum': ['routing', 'completion']}
schemas['supplement'] = {'$schema': 'https://json-schema.org/draft/2020-12/schema',
    'type': 'object', 'additionalProperties': False,
    'required': ['schema', *identity, 'documents', 'records'],
    'properties': {'schema': {'const': 'spec-agent-same-run-execution-metadata/1'}, **identity,
        'documents': {'type': 'array', 'minItems': 1, 'items': doc},
        'records': {'type': 'array', 'minItems': 1, 'items': ref}}}
schema_paths = {}
for key, value in schemas.items():
    path = ROOT / ('nenkin_execution_metadata_' + key + '_schema_r01.json')
    write(path, value)
    schema_paths[key] = {'path': str(path), 'sha256': sha(path)}

functions = (ROOT / 'writer_metadata_functions_r05.txt').read_text(encoding='utf-8')
schema_constants = 'METADATA_SCHEMAS = {\n' + ''.join(
    f"    {key!r}: (WORK / {Path(item['path']).name!r}, {item['sha256']!r}),\n"
    for key, item in sorted(schema_paths.items())) + '}\n'
source = source.replace('\ndef require(condition, message):', '\n' + schema_constants + '\ndef require(condition, message):', 1)
source = source.replace('\ndef recheck(pin, *, check_deadline=True):', '\n' + functions + '\ndef recheck(pin, *, check_deadline=True):', 1)
source = source.replace("    require(now == pin, 'Author input/runtime/context drift')", "    if 'executionMetadata' in pin:\n        now = with_execution_metadata(now, value, pin['executionMetadata']['supplement']['path'],\n            pin['executionMetadata']['supplement']['sha256'])\n    require(now == pin, 'Author input/runtime/context drift')", 1)
source = source.replace('def prepare(activation, activation_sha, wave, document_ids, workers, timeout, revisions=None):',
    'def prepare(activation, activation_sha, wave, document_ids, workers, timeout, revisions=None, execution_metadata=None, execution_metadata_sha=None):', 1)
source = source.replace("    require(selected and len(selected) == len(set(selected)) and set(selected) <= available, 'Invalid document wave subset')",
    "    require(selected and len(selected) == len(set(selected)) and set(selected) <= available, 'Invalid document wave subset')\n    require((execution_metadata is None) == (execution_metadata_sha is None), 'Supplement path and SHA must be paired')\n    if execution_metadata is not None:\n        pin = with_execution_metadata(pin, plan, execution_metadata, hash_arg(execution_metadata_sha))\n        metadata_selection(pin, plan, selected)", 1)
source = source.replace("    definitions = {key: workflow.select_document(Path(pin['plan']), key) for key in selected}",
    "    definitions = {key: workflow.select_document(Path(pin['plan']), key) for key in selected}\n    if 'executionMetadata' in pin:\n        metadata_selection(pin, plan, selected)", 1)
source = source.replace("            # Full preserved current-run Markdown/review and scope are passed without alteration.",
    "            if 'executionMetadata' in pin:\n                revision_context = metadata_revision_context(revision_context, context, pin)\n            # Full preserved current-run Markdown/review and scope are passed without alteration.", 1)
source = source.replace("    answer = workflow._bound_job(snapshot, job, prompt, schemas.REVIEW, timeout, state, DEADLINE)",
    "    if 'executionMetadata' in pin:\n        marker = '\\n原稿本文:\\n'\n        prefix, suffix = prompt.split(marker, 1)\n        prompt = prefix + METADATA_REVIEW_MARKER + json.dumps(pin['executionMetadata']['context'], ensure_ascii=False, indent=2) + marker + suffix\n    answer = workflow._bound_job(snapshot, job, prompt, schemas.REVIEW, timeout, state, DEADLINE)", 1)
source = source.replace("    write(job / 'review-handoff.json', {'schema':", "    handoff_value = {'schema':", 1)
source = source.replace("        'executionContextSha256': pin['executionContextSha256'], 'aiResponseBytesModified': False})\n    recheck(pin)\n    return answer",
    "        'executionContextSha256': pin['executionContextSha256'], 'aiResponseBytesModified': False}\n    if 'executionMetadata' in pin:\n        handoff_value['executionMetadata'] = metadata_provenance(pin)\n    write(job / 'review-handoff.json', handoff_value)\n    recheck(pin)\n    return answer", 1)
source = source.replace("    recheck(pin)\n    check_schema('text-pin', result)",
    "    if 'executionMetadata' in pin:\n        result['executionMetadata'] = metadata_provenance(pin)\n    recheck(pin)\n    check_schema('text-pin', result)", 1)
source = source.replace("            if accepted:\n                result['textPin']", "            if 'executionMetadata' in pin:\n                result['executionMetadata'] = metadata_provenance(pin)\n            if accepted:\n                result['textPin']", 1)
source = source.replace("    draft_scope = prompt_object(draft_prompt, '\\n前の原稿への原文根拠付き批評（正解期待値ではありません）:\\n')",
    "    previous_metadata = previous_execution_metadata(result, generation, definition, pin)\n    draft_scope = prompt_object(draft_prompt, '\\n前の原稿への原文根拠付き批評（正解期待値ではありません）:\\n')", 1)
source = source.replace("        'Previous full execution context differs')", "        'Previous full execution context differs')\n    if previous_metadata is not None:\n        require(isinstance(draft_scope, dict) and draft_scope.get('sameRunExecutionMetadata') == previous_metadata['context'] and\n            prompt_object(review_prompt, METADATA_REVIEW_MARKER) == previous_metadata['context'],\n            'Previous supplemental prompt context differs')\n    else:\n        require(METADATA_REVIEW_MARKER not in review_prompt and not (isinstance(draft_scope, dict) and\n            'sameRunExecutionMetadata' in draft_scope), 'Unbound prior supplemental context refused')", 1)
source = source.replace("    return binding, revision\n\ndef recheck_previous", "    if previous_metadata is not None:\n        binding['executionMetadata'] = previous_metadata['provenance']\n        binding['pinnedFiles'].update(previous_metadata['pinnedFiles'])\n    if previous_metadata is not None or 'executionMetadata' in pin:\n        revision['preservedPreviousExecutionMetadata'] = previous_metadata['context'] if previous_metadata is not None else None\n        revision['preservedIndependentReviewRawResponse'] = raw(generation / 'independent-review/answer.txt').decode('utf-8')\n    return binding, revision\n\ndef recheck_previous", 1)
source = source.replace("    pre.add_argument('--revision-from', nargs=2, action='append', default=[], metavar=('AUTHOR_RESULT', 'SHA256'))",
    "    pre.add_argument('--revision-from', nargs=2, action='append', default=[], metavar=('AUTHOR_RESULT', 'SHA256'))\n    pre.add_argument('--execution-metadata')\n    pre.add_argument('--execution-metadata-sha256')", 1)
source = source.replace('args.workers, args.timeout, args.revision_from) \\',
    'args.workers, args.timeout, args.revision_from, args.execution_metadata, args.execution_metadata_sha256) \\', 1)
ast.parse(source)
target = ROOT / 'nenkin_writer_driver_r05.py'
with target.open('x', encoding='utf-8', newline='\n') as f:
    f.write(source)
assert sha(BASE) == EXPECTED
print(json.dumps({'driver': str(target), 'sha256': sha(target), 'schemas': schema_paths,
    'providerStarted': False, 'actualBindingVerified': False}, ensure_ascii=False))
