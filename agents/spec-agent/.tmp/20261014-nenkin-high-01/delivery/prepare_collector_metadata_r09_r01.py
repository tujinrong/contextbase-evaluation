"""Prepare a fresh collector optional metadata adapter; do not execute pipelines."""
import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

WORK = Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01')
REPORT = Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01')
BASE = WORK / 'collect_reviewed_r08.py'
BASE_SHA = '2848e50ff84671608dfada5dece254ec15e80afe0ae55df5de41cf22abf345e3'
WRITER = WORK / 'nenkin_writer_driver_r05.py'
WRITER_SHA = '6b8e5456d96fabfda1bf43b6c17b6155167726492b10c0f9145473f243ee102c'
TARGET = WORK / 'collect_reviewed_r09.py'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert sha(BASE) == BASE_SHA and sha(WRITER) == WRITER_SHA
raw = BASE.read_bytes()
text = raw.decode('utf-8')
constants = '''
METADATA_WRITER = RUN / 'nenkin_writer_driver_r05.py'
METADATA_WRITER_SHA = '6b8e5456d96fabfda1bf43b6c17b6155167726492b10c0f9145473f243ee102c'
METADATA_REVIEW_MARKER = '\\n同一実行の経路・完了メタデータ全文（業務仕様根拠・原文・期待仕様・追加読取り許可ではありません）:\\n'
DRAFT_SCOPE_MARKER = '\\n前の原稿への原文根拠付き批評（正解期待値ではありません）:\\n'
REVIEW_SCOPE_MARKER = '\\nユーザー指定scopeのメタデータ全文（原文・期待仕様・追加読取り許可ではありません）:\\n'
'''
functions = '''
def metadata_writer(remember):
    path = remember(inside(METADATA_WRITER, RUN), METADATA_WRITER_SHA)
    require(path == safe(METADATA_WRITER), 'Supplemental writer path differs')
    spec = importlib.util.spec_from_file_location('fixed_metadata_writer_r05', path)
    writer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(writer)
    require(safe(writer.__file__) == path and sha(path) == METADATA_WRITER_SHA,
            'Loaded supplemental writer code differs')
    return writer

def bind_optional_metadata(wave_input, definition, plan_value, prepared, grant_value, remember, writer=None):
    if 'executionMetadata' not in wave_input:
        return None
    require(definition['kind'] in {'index', 'analysis-report'} and
            prepared['helper'] == str(safe(METADATA_WRITER)) and
            prepared['helperSha256'] == METADATA_WRITER_SHA and
            grant_value['driverSha256'] == METADATA_WRITER_SHA,
            'Supplemental wave must use the exact reserved-document writer')
    writer = metadata_writer(remember) if writer is None else writer
    require(writer.METADATA_REVIEW_MARKER == METADATA_REVIEW_MARKER,
            'Supplemental review marker differs from trusted writer')
    # Reconstruct the BASE from the real activation binding. Never derive it by
    # trusting or stripping the supplied composite input's arbitrary fields.
    base, exact_plan, context = writer.binding(wave_input['grant'], wave_input['grantSha256'], check_deadline=False)
    require(exact_plan == plan_value and context == load(guard.CONTEXT),
            'Supplemental base plan or original full execution context differs')
    metadata = wave_input['executionMetadata']
    bound = writer.with_execution_metadata(base, exact_plan,
            metadata['supplement']['path'], metadata['supplement']['sha256'])
    writer.metadata_selection(bound, exact_plan, prepared['documents'])
    require(bound == wave_input and definition['id'] in bound['executionMetadata']['documentIds'],
            'Reconstructed complete supplemental author input differs')
    for filename, digest in bound['executionMetadata']['pinnedFiles'].items():
        remember(filename, digest)
    require(sha(METADATA_WRITER) == METADATA_WRITER_SHA, 'Supplemental writer drift while rebinding')
    return {'context': bound['executionMetadata']['context'],
            'provenance': writer.metadata_provenance(bound)}

def prompt_metadata_object(prompt, marker):
    require(prompt.count(marker) == 1, 'Missing or duplicate bound prompt metadata marker')
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'Duplicate bound prompt JSON member')
            value[key] = item
        return value
    decoder = json.JSONDecoder(object_pairs_hook=pairs,
                              parse_constant=lambda item: require(False, 'Nonfinite prompt metadata'))
    return decoder.raw_decode(prompt.split(marker, 1)[1])[0]

def metadata_prompt_binding(optional, definition, original, author_result, handoff,
                            draft_prompt, review_prompt, context):
    # Only review-prefix metadata is parsed; canonical Markdown may itself contain
    # arbitrary literal marker text, and its complete bytes are validated separately.
    review_prefix = review_prompt.split('\\n原稿本文:\\n', 1)[0]
    carriers = (original, author_result, handoff)
    scope = prompt_metadata_object(draft_prompt, DRAFT_SCOPE_MARKER) if DRAFT_SCOPE_MARKER in draft_prompt else None
    if optional is None:
        require(all('executionMetadata' not in value for value in carriers) and
                METADATA_REVIEW_MARKER not in review_prefix and
                not (isinstance(scope, dict) and 'sameRunExecutionMetadata' in scope),
                'Unbound supplemental record or prompt context refused')
        return
    require(definition['kind'] in {'index', 'analysis-report'} and
            all(value.get('executionMetadata') == optional['provenance'] for value in carriers),
            'Supplemental text-pin/result/review provenance differs')
    require(isinstance(scope, dict) and scope.get('executionContext') == context and
            scope.get('sameRunExecutionMetadata') == optional['context'],
            'Supplemental draft changed the original scope or metadata context')
    require(prompt_metadata_object(review_prefix, REVIEW_SCOPE_MARKER) == context and
            prompt_metadata_object(review_prefix, METADATA_REVIEW_MARKER) == optional['context'],
            'Independent supplemental review context differs')

'''
needle = "HELPER_SHA = '9d5ec80c5fd3efe2044302104a64ff928777fd98d3cdd0e0c8ef0ff301ee5802'\n"
assert text.count(needle) == 1
text = text.replace(needle, needle + constants)
needle = 'def main():\n'
assert text.count(needle) == 1
text = text.replace(needle, functions + needle)
needle = "        review_handoff = pin(review_file.parent / 'review-handoff.json')\n"
insert = "        execution_metadata = bind_optional_metadata(after_value['input'], definition, value, prepared, grant_value, pin)\n"
assert text.count(needle) == 1
text = text.replace(needle, insert + needle)
needle = "        workflow.references_valid(review, manifest)\n"
insert = '''        review_prompt = safe(review_file.parent / 'prompt.txt').read_bytes().decode('utf-8')
        context = load(guard.CONTEXT)
        metadata_prompt_binding(execution_metadata, definition, original, result, handoff,
                                original_prompt, review_prompt, context)
        if execution_metadata is not None:
            # Match the complete raw independent review prompt, including original
            # canonical Markdown newline bytes and unchanged structure findings.
            from contextbase.ai import prompts
            structure = validate_document(document.read_bytes().decode('utf-8'), definition['path'],
                                          expected_document_id=definition['id'], expected_kind=definition['kind'])
            bound_definition_for_review = workflow.select_document(plan, definition['id'])
            expected_review = (provider.COMMON_POLICY + '\\nUser task (within that boundary):\\n' +
                prompts.REVIEW + workflow._document_context(guard.SNAPSHOT, bound_definition_for_review) +
                REVIEW_SCOPE_MARKER + json.dumps(context, ensure_ascii=False, indent=2) +
                METADATA_REVIEW_MARKER + json.dumps(execution_metadata['context'], ensure_ascii=False, indent=2) +
                '\\n原稿本文:\\n' + document.read_bytes().decode('utf-8') +
                '\\n構造検査の指摘（意味の正確さを採点した結果ではありません）:\\n' + json.dumps(structure, ensure_ascii=False))
            require(review_prompt == expected_review,
                    'Complete supplemental review prompt differs from bound source/text/structure')
'''
assert text.count(needle) == 1
text = text.replace(needle, insert + needle)
needle = "                        'reportOnly': definition['kind'] == 'analysis-report'})\n"
insert = "        if execution_metadata is not None:\n            records[-1]['executionMetadata'] = execution_metadata['provenance']\n"
assert text.count(needle) == 1
text = text.replace(needle, needle + insert)
revised = text.encode('utf-8')
tree = ast.parse(text)
assert not TARGET.exists() and sha(BASE) == BASE_SHA and sha(WRITER) == WRITER_SHA
with TARGET.open('xb') as stream:
    stream.write(revised)
assert TARGET.read_bytes() == revised and sha(BASE) == BASE_SHA and sha(WRITER) == WRITER_SHA
old_tree = ast.parse(raw.decode('utf-8'))
old_functions = {n.name: ast.dump(n, include_attributes=False) for n in old_tree.body if isinstance(n, ast.FunctionDef)}
new_functions = {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, ast.FunctionDef)}
assert [name for name in old_functions if old_functions[name] != new_functions[name]] == ['main']
audit = {
    'schema': 'spec-agent-collector-supplement-preparation/1',
    'createdUtc': datetime.now(timezone.utc).isoformat(),
    'status': 'FRESH_CODE_PREPARED_INDEPENDENT_DELTA_AUDIT_PENDING',
    'base': {'path': str(BASE), 'sha256': BASE_SHA, 'unchanged': True},
    'candidate': {'path': str(TARGET), 'sha256': sha(TARGET)},
    'writer': {'path': str(WRITER), 'sha256': WRITER_SHA, 'unchanged': True},
    'newFunctions': sorted(set(new_functions) - set(old_functions)),
    'changedExistingFunctions': ['main'],
    'legacyValidationStatementsRemoved': False,
    'newValidationScope': 'Optional exact r05 activation base/composite rebinding, all metadata pin/evidence rechecks and exact generation/review context plus final provenance; absent path rejects unbound extras and retains legacy operations.',
    'actualSourceAuthorRecordProviderCollectorRendererBrowserMarkerReadsOrCalls': 0,
    'helperImported': False, 'frozenPipelineImported': False,
    'nativeApproval': False, 'formalPercentage': None, 'published': False,
    'preparationScript': {'path': str(Path(__file__)), 'sha256': sha(Path(__file__))}
}
receipt = REPORT / 'independent-audit/collector-metadata-r09-preparation-r01.json'
with receipt.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(audit, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'candidate': str(TARGET), 'sha256': sha(TARGET), 'receipt': str(receipt), 'receiptSha256': sha(receipt)}, ensure_ascii=False))
