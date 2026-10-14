"""Create a fresh generic author interface; no source/application/prose input."""
import ast
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).parent
OLD = BASE / 'nenkin_writer_driver_r01.py'
NEW = BASE / 'nenkin_writer_driver_r02.py'
source = OLD.read_text(encoding='utf-8')

def replace(old, new):
    global source
    assert source.count(old) == 1, old[:100]
    source = source.replace(old, new)

def function(name, code):
    global source
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    lines = source.splitlines(keepends=True)
    source = ''.join(lines[:node.lineno-1]) + code.strip() + '\n' + ''.join(lines[node.end_lineno:])

# Exact paths/hashes now come exclusively from the parent activation bytepin.
for line in (
    "SNAPSHOT = WORK / 'snapshot'\n",
    "CAP_SHA = '92c339cb7040019312d0ec01669d22c44e4cc73fa373d5278c3f6f04c0c09631'\n",
    "CONTEXT = WORK / 'execution-context.json'\n",
    "CONTEXT_SHA = 'd3a4e4d1bedd6e4d7a2d8658f162e2d8f7a0119ffdb4529650f2a2d369ca90cc'\n",
):
    replace(line, '')

activation = json.loads((BASE / 'nenkin_author_activation_schema_r02.json').read_text(encoding='utf-8'))
activation['required'].extend(['capsuleRoot', 'executionContext'])
activation['properties']['capsuleRoot'] = {'type': 'string', 'minLength': 1}
activation['properties']['executionContext'] = {'type': 'string', 'minLength': 1}
for key in ('capsuleManifestSha256', 'executionContextSha256'):
    activation['properties'][key] = {'$ref': '#/$defs/sha'}
text_pin = json.loads((BASE / 'nenkin_text_pin_schema_r02.json').read_text(encoding='utf-8'))
text_pin['properties']['capsule']['properties']['manifestSha256'] = {'$ref': '#/$defs/sha'}
schema_sha = {}
for name, value in [('nenkin_author_activation_schema_r03.json', activation), ('nenkin_text_pin_schema_r03.json', text_pin)]:
    payload = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    with (BASE / name).open('xb') as out:
        out.write(payload)
    schema_sha[name] = hashlib.sha256(payload).hexdigest()
replace("'nenkin_author_activation_schema_r02.json', '30b9b6b267d29572d5fce795dad142dd8a10b94c84dd143df2f477e34f3cf4a2'",
        "'nenkin_author_activation_schema_r03.json', '" + schema_sha['nenkin_author_activation_schema_r03.json'] + "'")
replace("'nenkin_text_pin_schema_r02.json', '93bdbc1d0ae6b5f29949a7df96ab57dba783a042fdfef6d37b021d8a4e89619e'",
        "'nenkin_text_pin_schema_r03.json', '" + schema_sha['nenkin_text_pin_schema_r03.json'] + "'")
replace("value['driverSha256'] == sha(__file__) and value['capsuleManifestSha256'] == CAP_SHA and\n        value['executionContextSha256'] == CONTEXT_SHA and value['runtimeReceiptSha256'] == RECEIPT_SHA and",
        "value['driverSha256'] == sha(__file__) and value['runtimeReceiptSha256'] == RECEIPT_SHA and")
replace("grant_path, grant = fixed_grant(grant_path, grant_sha)\n    from contextbase.ai", "grant_path, grant = fixed_grant(grant_path, grant_sha)\n    snapshot = inside(grant['capsuleRoot'], WORK)\n    context_file = inside(grant['executionContext'], WORK)\n    require(snapshot.parent == safe(WORK) and snapshot.name.startswith('snapshot') and\n        context_file.parent == safe(WORK) and context_file.suffix == '.json', 'Selected capsule/context path escapes root')\n    cap_sha = hash_arg(grant['capsuleManifestSha256'])\n    context_sha = hash_arg(grant['executionContextSha256'])\n    from contextbase.ai")
# In binding only: local immutable choices. Other functions use input pin fields.
tree = ast.parse(source)
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'binding')
lines = source.splitlines(keepends=True)
block = ''.join(lines[node.lineno-1:node.end_lineno])
block = block.replace('SNAPSHOT', 'snapshot').replace('CAP_SHA', 'cap_sha').replace('CONTEXT_SHA', 'context_sha').replace('CONTEXT', 'context_file')
block = block.replace("return {'snapshot': state, 'executionContextSha256': context_sha", "return {'snapshot': state, 'snapshotRoot': str(snapshot), 'executionContext': str(context_file),\n        'executionContextSha256': context_sha")
source = ''.join(lines[:node.lineno-1]) + block + ''.join(lines[node.end_lineno:])

# Generic readonly provenance checks for the caller's own previous AI draft.
insert = r'''
def provider_evidence(snapshot, job, schema, state):
    from jsonschema import Draft202012Validator
    job = inside(job, WORK / 'jobs')
    require(job.name in {'analysis', 'analysis-repair', 'draft', 'independent-review'}, 'Unknown prior provider stage')
    paths = [safe(job / n) for n in ('answer.txt', 'result.json', 'schema.json', 'prompt.txt')]
    before = safe(job.parent / (job.name + '-snapshot-before.json'))
    after = safe(job.parent / (job.name + '-snapshot-after.json'))
    paths.extend([before, after])
    answer, result, supplied_schema = load(paths[0]), load(paths[1]), load(paths[2])
    metadata = result.get('metadata', {})
    require(isinstance(metadata, dict) and result.get('exit_code') == 0 and metadata.get('status') == 'passed' and
        metadata.get('schema_supplied') is True and metadata.get('workspace') == str(safe(snapshot)) and
        metadata.get('reference_mode') == 'source-only' and metadata.get('training_reference_authorized') is False and
        metadata.get('error_events') == [] and metadata.get('invalid_event_lines') == [], 'Prior provider was not successfully bound')
    require(metadata.get('answer_sha256') == sha(paths[0]) and metadata.get('prompt_sha256') == sha(paths[3]) and
        supplied_schema == schema and result.get('answer') == answer, 'Prior provider raw response/schema differs')
    Draft202012Validator(schema).validate(answer)
    ap = load(after)
    require(load(before) == state and ap.get('status') == 'UNCHANGED' and ap.get('before') == state and
        ap.get('after') == state, 'Prior provider capsule before/after differs')
    return answer, raw(paths[3]).decode('utf-8'), {str(p): sha(p) for p in paths}

def prompt_object(prompt, marker):
    require(marker in prompt, 'Original provider prompt lacks bound metadata')
    return json.JSONDecoder().raw_decode(prompt.split(marker, 1)[1])[0]

def previous_revision(path, expected_sha, definition, pin, context):
    from contextbase.ai import workflow, capsule, schemas
    from contextbase.ai.validation import validate_document
    path = inside(path, WORK / 'jobs')
    generation = path.parent
    wave = generation.parent
    folder = digest(definition['id'].encode('utf-8'))[:16]
    require(path.name == 'author-document-result.json' and wave.parent == safe(WORK / 'jobs') and
        re.fullmatch(r'author-wave-[0-9]{2}', wave.name) is not None and generation.name == folder,
        'Only same-run author-document-result can seed revisions')
    require(sha(path) == hash_arg(expected_sha), 'Previous author result changed')
    result = load(path)
    require(result.get('schema') == 'spec-agent-author-document-result/1' and result.get('documentId') == definition['id'] and
        result.get('path') == definition['path'] and result.get('kind') == definition['kind'] and
        result.get('capsule') == pin['snapshot'] and result.get('planSha256') == pin['planSha256'] and
        result.get('executionContextSha256') == pin['executionContextSha256'] and
        result.get('runtimeReceiptSha256') == RECEIPT_SHA and
        result.get('status') in {'TEXT_REVIEW_APPROVED', 'REQUIRES_AI_REVISION'}, 'Previous draft identity/scope differs')
    snapshot = safe(pin['snapshotRoot'])
    draft_file = safe(generation / 'draft-result.json')
    structure_file = safe(generation / 'document-structure.json')
    analysis_file = safe(generation / 'analysis-verified.json')
    checkpoint_file = safe(generation / 'analysis-handoff.json')
    draft_info, checkpoint = load(draft_file), load(checkpoint_file)
    require(checkpoint.get('providerDirectory') in {'analysis', 'analysis-repair'}, 'Previous analysis stage unknown')
    # Safe-path checks precede the frozen readonly delegate's reads.
    for name in ('answer.txt', 'result.json', 'schema.json', 'prompt.txt'):
        safe(generation / checkpoint['providerDirectory'] / name)
    for suffix in ('before', 'after'):
        safe(generation / (checkpoint['providerDirectory'] + '-snapshot-' + suffix + '.json'))
    analysis, actual_checkpoint, checkpoint_sha = workflow._resume_analysis(snapshot, definition, generation)
    require(actual_checkpoint == checkpoint and checkpoint_sha == sha(checkpoint_file), 'Previous completed analysis checkpoint differs')
    draft_answer, draft_prompt, pins = provider_evidence(snapshot, generation / 'draft', schemas.DRAFT, pin['snapshot'])
    review, review_prompt, review_pins = provider_evidence(snapshot, generation / 'independent-review', schemas.REVIEW, pin['snapshot'])
    pins.update(review_pins)
    require(prompt_object(draft_prompt, '\n対象文書計画:\n') == dict(definition) and
        prompt_object(draft_prompt, '\nAIによる解析素材:\n') == analysis and
        prompt_object(review_prompt, '\n対象文書計画:\n') == dict(definition), 'Previous prompt is not same-definition/facts bound')
    draft_scope = prompt_object(draft_prompt, '\n前の原稿への原文根拠付き批評（正解期待値ではありません）:\n')
    require((draft_scope == context or isinstance(draft_scope, dict) and draft_scope.get('executionContext') == context) and
        prompt_object(review_prompt, '\nユーザー指定scopeのメタデータ全文（原文・期待仕様・追加読取り許可ではありません）:\n') == context,
        'Previous full execution context differs')
    expected_output = safe(WORK / 'drafts' / wave.name /
        ('analysis-reports' if definition['kind'] == 'analysis-report' else 'specifications'))
    document = inside(result['draft']['canonicalMarkdown'], expected_output)
    require(document == safe(expected_output / definition['path']) and result['draft']['outputRoot'] == str(expected_output) and
        result['draft']['draftResult'] == str(draft_file) and result['draft']['draftResultSha256'] == sha(draft_file),
        'Previous draft path/result binding differs')
    content = raw(document)
    require(draft_answer['documentId'] == definition['id'] and draft_answer['path'] == definition['path'] and
        content == draft_answer['content'].encode('utf-8') and sha(document) == draft_info['contentSha256'] == result['draft']['sha256'] and
        draft_info['documentId'] == definition['id'] and draft_info['path'] == definition['path'] and
        draft_info['snapshot'] == pin['snapshot'] and draft_info['referenceMode'] == 'source-only' and
        draft_info['aiAuthored'] is True and draft_info['semanticProseAssembledByPython'] is False,
        'Previous whole Markdown differs from preserved AI draft')
    structure = load(structure_file)
    findings = validate_document(content.decode('utf-8'), definition['path'], expected_document_id=definition['id'], expected_kind=definition['kind'])
    require(structure['documentId'] == definition['id'] and structure['contentSha256'] == sha(document) and
        structure['findings'] == findings == draft_info['structureFindings'] and
        structure['status'] == ('STRUCTURE_INVALID' if findings else 'STRUCTURE_VALID'), 'Previous structure record differs')
    require(review['documentId'] == definition['id'] and
        (not review['approved'] or (not review['unresolved'] and not any(f['severity'] in {'critical', 'major'} for f in review['findings']))),
        'Previous independent review identity/approval contradicts blocking findings')
    workflow.references_valid(review, capsule.verify(snapshot))
    require(review_prompt.split('\n原稿本文:\n', 1)[1].split('\n構造検査の指摘（意味の正確さを採点した結果ではありません）:\n', 1)[0] == content.decode('utf-8'),
        'Previous review did not contain the whole exact Markdown')
    review_record = inside(result['review']['path'], generation / 'independent-review')
    require(result['review']['sha256'] == sha(review_record) and load(review_record) == review and
        result['review']['approved'] is review['approved'], 'Previous review raw/record binding differs')
    verified = safe(generation / 'independent-review/review-verified.json')
    if result['review']['verified'] is True:
        handoff_file = safe(generation / 'independent-review/review-handoff.json')
        rh = load(handoff_file)
        require(review_record == verified and raw(verified) == raw(generation / 'independent-review/answer.txt') and
            rh['schema'] == 'reverse-ai-review-handoff/1' and rh['snapshot'] == pin['snapshot'] and
            rh['documentFile'] == str(document) and rh['documentSha256'] == sha(document) and rh['reviewSha256'] == sha(verified) and
            rh['approved'] is review['approved'] and rh['executionContextSha256'] == pin['executionContextSha256'] and
            rh['referenceMode'] == 'source-only' and rh['aiResponseBytesModified'] is False,
            'Previous verified independent review handoff differs')
        pins[str(handoff_file)] = sha(handoff_file)
    else:
        conflict_file = safe(generation / 'independent-review/structure-approval-conflict.json')
        conflict = load(conflict_file)
        require(result['review']['verified'] is False and review_record == safe(generation / 'independent-review/answer.txt') and
            review['approved'] is True and findings and not verified.exists() and
            conflict['status'] == 'AI_APPROVAL_REJECTED_STRUCTURE_INVALID' and conflict['findings'] == findings and
            conflict['documentSha256'] == sha(document), 'Only preserved structure-approval refusal can use unverified review')
        pins[str(conflict_file)] = sha(conflict_file)
    pins.update({str(p): sha(p) for p in [path, document, draft_file, structure_file, analysis_file, checkpoint_file, review_record]})
    for name in checkpoint['providerArtifactsSha256']:
        target = safe(generation / checkpoint['providerDirectory'] / name)
        pins[str(target)] = sha(target)
    for name in checkpoint['snapshotEvidenceSha256']:
        target = safe(generation / name)
        pins[str(target)] = sha(target)
    require(sha(path) == expected_sha and all(sha(p) == value for p, value in pins.items()), 'Previous artifacts drift during collection')
    binding = {'sourceResult': str(path), 'sourceResultSha256': expected_sha, 'documentId': definition['id'],
        'planSha256': pin['planSha256'], 'capsule': pin['snapshot'], 'pinnedFiles': pins,
        'completedAnalysisCheckpointRevalidated': True, 'analysisWillBeReused': False}
    revision = {'executionContext': context, 'previousCanonicalMarkdown': content.decode('utf-8'),
        'preservedIndependentReview': review, 'preservedStructureRecord': structure,
        'previousDraftResult': draft_info, 'revisionProvenance': binding,
        'freshAnalysisRequired': True, 'businessProseAssembledByPython': False}
    return binding, revision

def recheck_previous(previous, definition, pin, context):
    now, revision = previous_revision(previous['sourceResult'], previous['sourceResultSha256'], definition, pin, context)
    require(now == previous, 'Previous revision input artifacts drift')
    return revision

'''
replace('\ndef prepare(', '\n' + insert + 'def prepare(')
replace('def prepare(activation, activation_sha, wave, document_ids, workers, timeout):',
        'def prepare(activation, activation_sha, wave, document_ids, workers, timeout, revisions=None):')
replace("require(selected and len(selected) == len(set(selected)) and set(selected) <= available, 'Invalid document wave subset')\n    paths =",
        "require(selected and len(selected) == len(set(selected)) and set(selected) <= available, 'Invalid document wave subset')\n    from contextbase.ai import workflow\n    previous = {}\n    for path, expected_sha in revisions or []:\n        identity = load(inside(path, WORK / 'jobs'))['documentId']\n        require(identity in selected and identity not in previous, 'Revision must map uniquely to selected document')\n        definition = workflow.select_document(Path(pin['plan']), identity)\n        previous[identity], _ = previous_revision(path, hash_arg(expected_sha), definition, pin, context)\n    paths =")
replace("'documents': selected, 'workers': workers, 'timeout': timeout, 'deadline': DEADLINE,", "'documents': selected, 'workers': workers, 'timeout': timeout, 'deadline': DEADLINE,\n        'revisions': previous, 'analysisReuseAuthorized': False,")
replace("state = workflow._definition_state(SNAPSHOT, definition)\n    manifest = capsule.verify(SNAPSHOT)", "snapshot = safe(pin['snapshotRoot'])\n    state = workflow._definition_state(snapshot, definition)\n    manifest = capsule.verify(snapshot)")
replace('workflow._document_context(SNAPSHOT, definition)', 'workflow._document_context(snapshot, definition)')
replace('workflow._bound_job(SNAPSHOT, job, prompt, schemas.REVIEW, timeout, state, DEADLINE)', 'workflow._bound_job(snapshot, job, prompt, schemas.REVIEW, timeout, state, DEADLINE)')
replace("'executionContextSha256': CONTEXT_SHA, 'aiResponseBytesModified': False", "'executionContextSha256': pin['executionContextSha256'], 'aiResponseBytesModified': False")
replace("'sourcePathsRead': analysis['sourcePathsRead'], 'executionContextSha256': CONTEXT_SHA,", "'sourcePathsRead': analysis['sourcePathsRead'], 'executionContextSha256': pin['executionContextSha256'],")
replace("target = safe(generation / 'text-reviewed-pin.json')\n    write(target, result)\n    return {'path': str(target), 'sha256': sha(target), 'disposition': result['disposition']}",
        "job_target = safe(generation / 'text-reviewed-pin.json')\n    target = inside(REPORT / 'text-pins' / generation.relative_to(safe(WORK / 'jobs')) / 'text-reviewed-pin.json', REPORT / 'text-pins')\n    write(job_target, result)\n    target.parent.mkdir(parents=True, exist_ok=True)\n    with target.open('xb') as stream:\n        stream.write(raw(job_target))\n    require(raw(target) == raw(job_target), 'Report text pin differs from job metadata bytes')\n    return {'path': str(target), 'sha256': sha(target), 'jobPin': str(job_target),\n        'jobPinSha256': sha(job_target), 'disposition': result['disposition']}")
replace("definitions = {key: workflow.select_document(Path(pin['plan']), key) for key in selected}\n    job_root.mkdir",
        "definitions = {key: workflow.select_document(Path(pin['plan']), key) for key in selected}\n    previous = record['revisions']\n    require(isinstance(previous, dict) and set(previous) <= set(selected) and record['analysisReuseAuthorized'] is False, 'Prepared revision subset differs')\n    for key, old in previous.items():\n        recheck_previous(old, definitions[key], pin, context)\n    job_root.mkdir")
replace("# Metadata, not previous business prose, is supplied unchanged as scope.\n            draft = workflow.document(SNAPSHOT, definition, generation, output, timeout=record['timeout'],\n                deadline=DEADLINE, revision_context=context)",
        "revision_context = context\n            if identity in previous:\n                revision_context = recheck_previous(previous[identity], definition, pin, context)\n                write(job_root / (folder + '-revision-input-pins.json'), previous[identity])\n            # Full preserved current-run Markdown/review and scope are passed without alteration.\n            # No analysis_job is supplied: this first revision interface always performs fresh analysis.\n            draft = workflow.document(Path(pin['snapshotRoot']), definition, generation, output, timeout=record['timeout'],\n                deadline=DEADLINE, revision_context=revision_context)")
replace("require(sha(preparation) == preparation_sha, 'Preparation drift during generation')\n            document =", "require(sha(preparation) == preparation_sha, 'Preparation drift during generation')\n            if identity in previous:\n                recheck_previous(previous[identity], definition, pin, context)\n            document =")
replace("review = scoped_review(definition, document, generation / 'independent-review', record['timeout'], pin, context)\n            accepted =",
        "structure_conflict = False\n            try:\n                review = scoped_review(definition, document, generation / 'independent-review', record['timeout'], pin, context)\n            except workflow.ReviewStructureConflict:\n                # Preserve the original refused review; it is revision evidence, never approval.\n                recheck(pin)\n                review = load(generation / 'independent-review/answer.txt')\n                structure_conflict = True\n            require(sha(preparation) == preparation_sha, 'Preparation drift during review')\n            if identity in previous:\n                recheck_previous(previous[identity], definition, pin, context)\n            review_file = safe(generation / 'independent-review' / ('answer.txt' if structure_conflict else 'review-verified.json'))\n            accepted = not structure_conflict and")
replace("result = {'documentId': identity, 'path': definition['path'], 'kind': definition['kind'],\n                'status': 'TEXT_REVIEW_APPROVED'", "result = {'schema': 'spec-agent-author-document-result/1', 'documentId': identity, 'path': definition['path'], 'kind': definition['kind'],\n                'capsule': pin['snapshot'], 'planSha256': pin['planSha256'],\n                'executionContextSha256': pin['executionContextSha256'], 'runtimeReceiptSha256': RECEIPT_SHA,\n                'revisionFrom': previous.get(identity), 'analysisFresh': True,\n                'status': 'TEXT_REVIEW_APPROVED'")
replace("'review': {'path': str(safe(generation / 'independent-review/review-verified.json')),\n                    'sha256': sha(generation / 'independent-review/review-verified.json'), 'approved': review['approved']},",
        "'review': {'path': str(review_file), 'sha256': sha(review_file), 'approved': review['approved'],\n                    'verified': not structure_conflict, 'structureApprovalConflict': structure_conflict},")
replace("write(generation / 'author-document-result.json', result)\n            print", "recheck(pin)\n            require(sha(preparation) == preparation_sha, 'Preparation drift before document result')\n            write(generation / 'author-document-result.json', result)\n            print")
replace("write(generation / 'author-failure.json', result)\n            return result", "write(generation / 'author-failure.json', result)\n            return result\n        finally:\n            if identity in previous:\n                recheck_previous(previous[identity], definition, pin, context)")
replace("require(sha(preparation) == preparation_sha, 'Preparation changed before wave completion')\n        write", "require(sha(preparation) == preparation_sha, 'Preparation changed before wave completion')\n        for key, old in previous.items():\n            recheck_previous(old, definitions[key], pin, context)\n        write")
replace("pre.add_argument('--timeout', type=int, default=2400)", "pre.add_argument('--timeout', type=int, default=2400)\n    pre.add_argument('--revision-from', nargs=2, action='append', default=[], metavar=('AUTHOR_RESULT', 'SHA256'))")
replace('args.document_id, args.workers, args.timeout)', 'args.document_id, args.workers, args.timeout, args.revision_from)')
assert not any(token in source for token in ('SNAPSHOT', 'CAP_SHA', 'CONTEXT_SHA'))
tree = ast.parse(source)
with NEW.open('x', encoding='utf-8', newline='\n') as out:
    out.write(source)
print(json.dumps({'driver': str(NEW), 'sha256': hashlib.sha256(NEW.read_bytes()).hexdigest(),
    'functions': len([n for n in tree.body if isinstance(n, ast.FunctionDef)]), 'schemas': schema_sha,
    'providerStarted': False}, ensure_ascii=False))
