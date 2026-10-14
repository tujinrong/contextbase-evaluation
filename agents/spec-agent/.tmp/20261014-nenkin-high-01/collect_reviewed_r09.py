"""Collect byte-identical, independently reviewed new-source drafts; no prose authoring."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, importlib.util, json, re, sys
sys.dont_write_bytecode = True
RUN = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
REPORT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
HELPER = RUN / 'review_plan_with_scope_r05.py'
HELPER_SHA = '9d5ec80c5fd3efe2044302104a64ff928777fd98d3cdd0e0c8ef0ff301ee5802'

METADATA_WRITER = RUN / 'nenkin_writer_driver_r05.py'
METADATA_WRITER_SHA = '6b8e5456d96fabfda1bf43b6c17b6155167726492b10c0f9145473f243ee102c'
METADATA_REVIEW_MARKER = '\n同一実行の経路・完了メタデータ全文（業務仕様根拠・原文・期待仕様・追加読取り許可ではありません）:\n'
DRAFT_SCOPE_MARKER = '\n前の原稿への原文根拠付き批評（正解期待値ではありません）:\n'
REVIEW_SCOPE_MARKER = '\nユーザー指定scopeのメタデータ全文（原文・期待仕様・追加読取り許可ではありません）:\n'

def require(ok, message):
    if not ok:
        raise ValueError(message)

def initial_safe(value):
    path = Path(value).absolute()
    for node in (path, *path.parents):
        if node.is_symlink() or (node.exists() and getattr(node.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('Linked path refused before filesystem access')
    return path.resolve()

require(hashlib.sha256(initial_safe(HELPER).read_bytes()).hexdigest() == HELPER_SHA,
        'Audited fixed provenance helper changed')
spec = importlib.util.spec_from_file_location('fixed_spec_scope', initial_safe(HELPER))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
safe, sha, load = guard.safe, guard.sha, guard.load

def inside(value, root):
    value, root = safe(value), safe(root)
    require(value.is_relative_to(root) and value != root, 'Path must be within its explicit permitted root')
    return value


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
    review_prefix = review_prompt.split('\n原稿本文:\n', 1)[0]
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--selection', required=True)
    parser.add_argument('--selection-sha256', required=True)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--plan-handoff-sha256', required=True)
    parser.add_argument('--plan-review', required=True)
    parser.add_argument('--plan-review-sha256', required=True)
    parser.add_argument('--plan-review-handoff-sha256', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--report', required=True)
    parser.add_argument('--partial', action='store_true')
    args = parser.parse_args()
    runtime = guard.bootstrap()
    plan = guard.allowed_plan(args.plan)
    fixed, _, value, manifest, _ = guard.current_pin(plan, args.plan_sha256, args.plan_handoff_sha256)
    state = fixed['snapshot']
    selection = inside(args.selection, REPORT)
    report = inside(args.report, REPORT)
    output = inside(args.output, RUN / 'collections')
    require(not output.exists() and not report.exists(), 'Fresh output and report paths required')
    input_pins = {str(safe(HELPER)): HELPER_SHA, str(safe(__file__)): sha(__file__)}

    def pin(path, expected=None):
        path = safe(path)
        digest = sha(path)
        require(expected is None or digest == expected, 'Pinned input bytes changed: ' + str(path))
        require(str(path) not in input_pins or input_pins[str(path)] == digest, 'Input changed while collecting')
        input_pins[str(path)] = digest
        return path

    pin(selection, args.selection_sha256)
    pin(plan, args.plan_sha256)
    pin(plan.parent / 'plan-handoff.json', args.plan_handoff_sha256)
    plan_review = inside(args.plan_review, RUN / 'jobs')
    require(plan_review.name == 'plan-review-verified.json', 'Verified independent plan review required')
    pin(plan_review, args.plan_review_sha256)
    plan_handoff = pin(plan_review.parent / 'plan-review-handoff.json', args.plan_review_handoff_sha256)
    assessment, handoff = load(plan_review), load(plan_handoff)
    require(assessment['approved'] is True and handoff['approved'] is True and
            handoff['reviewSha256'] == sha(plan_review) and handoff['snapshot'] == state and
            handoff['planSha256'] == args.plan_sha256 and
            handoff['planHandoffSha256'] == args.plan_handoff_sha256 and
            handoff['referenceMode'] == 'source-only' and handoff['aiResponseBytesModified'] is False,
            'Plan review is not bound to the approved unchanged source-only plan')
    original_name = handoff['originalAiResponse']
    require(original_name == 'answer.txt', 'Unexpected original plan response filename')
    raw_plan_review = pin(plan_review.parent / original_name)
    require(raw_plan_review.parent == plan_review.parent and
            raw_plan_review.read_bytes() == plan_review.read_bytes(), 'Original plan review response differs')
    from contextbase.ai import workflow, capsule, plan_review as review_contract, schemas, provider
    from jsonschema import Draft202012Validator
    from contextbase.ai.validation import validate_document
    review_contract._validate(assessment, value, manifest)
    preparation = pin(inside(REPORT / 'independent-plan-review' / plan_review.parent.name / 'preparation.json', REPORT),
                      handoff['scopePreparationSha256'])
    prepared = load(preparation)
    require(prepared['input'] == fixed and prepared['runtime'] == runtime and
            prepared['providerStarted'] is False and prepared['helperSha256'] == HELPER_SHA and
            prepared['helper'] == str(safe(HELPER)) and safe(prepared['job']) == plan_review.parent,
            'Independent plan review preparation differs')
    prepared_prompt = pin(inside(prepared['promptFile'], preparation.parent), prepared['promptSha256'])
    require(prepared_prompt.name == 'prepared-prompt.txt', 'Unexpected prepared prompt filename')
    require(safe(plan_review.parent / 'prompt.txt').read_bytes() ==
            (provider.COMMON_POLICY + '\nUser task (within that boundary):\n').encode('utf-8') + prepared_prompt.read_bytes(),
            'Actual independent plan review scope prompt differs from its audited preparation')
    plan_before = pin(plan_review.parent.parent / (plan_review.parent.name + '-plan-review-before.json'))
    plan_after = pin(plan_review.parent.parent / (plan_review.parent.name + '-plan-review-after.json'))
    require(load(plan_before) == {'input': fixed, 'runtime': runtime, 'preparationSha256': sha(preparation)} and
            load(plan_after) == {'status': 'UNCHANGED_AND_REVIEW_VALIDATED', 'input': fixed, 'runtime': runtime,
                                 'preparationSha256': sha(preparation)},
            'Independent plan review did not finish with the unchanged validated fixed inputs')

    def provider_answer(directory, schema):
        directory = inside(directory, RUN / 'jobs')
        files = {name: pin(directory / name) for name in ('answer.txt', 'result.json', 'schema.json', 'prompt.txt')}
        answer, result = load(files['answer.txt']), load(files['result.json'])
        metadata = result.get('metadata', {})
        require(result.get('exit_code') == 0 and metadata.get('status') == 'passed' and
                metadata.get('schema_supplied') is True and metadata.get('workspace') == str(safe(guard.SNAPSHOT)) and
                metadata.get('reference_mode') == 'source-only' and metadata.get('training_reference_authorized') is False and
                metadata.get('error_events') == [] and metadata.get('invalid_event_lines') == [] and
                metadata.get('answer_sha256') == sha(files['answer.txt']) and
                metadata.get('prompt_sha256') == sha(files['prompt.txt']) and load(files['schema.json']) == schema and
                result.get('answer') == answer, 'Provider raw answer/schema/result provenance differs')
        Draft202012Validator(schema).validate(answer)
        before = pin(directory.parent / (directory.name + '-snapshot-before.json'))
        after = pin(directory.parent / (directory.name + '-snapshot-after.json'))
        require(load(before) == state and load(after) == {'status': 'UNCHANGED', 'before': state, 'after': state},
                'Provider lacks exact unchanged before/after snapshot evidence')
        return answer

    require(provider_answer(plan_review.parent, review_contract.PLAN_REVIEW) == assessment,
            'Plan assessment differs from its successful provider evidence')
    workflow.references_valid(assessment, manifest)
    selected = load(selection)['documents']
    definitions = {doc['id']: doc for doc in value['documents']}
    ids = [item['documentId'] for item in selected]
    require(ids and len(ids) == len(set(ids)) and set(ids) <= set(definitions), 'Duplicate or unknown selection IDs')
    require(args.partial or set(ids) == set(definitions), 'Final selection must include the complete approved plan')
    records = []
    for item in selected:
        definition = definitions[item['documentId']]
        source_pin = pin(inside(item['pin'], REPORT), item['pinSha256'])
        original = load(source_pin)
        require(all(original[key] == definition[target] for key, target in
                    [('documentId', 'id'), ('path', 'path'), ('kind', 'kind')]) and
                original['capsule'] == state and original['structureStatus'] == 'STRUCTURE_VALID' and
                original['independentReviewApproved'] is True and original['noFurtherTextRevisionPlanned'] is True,
                'Selected text pin is not final and valid for this plan')
        document = pin(inside(original['canonicalMarkdown'], RUN), original['sha256'])
        draft_file = pin(inside(original['draftResult'], RUN / 'jobs'), original['draftResultSha256'])
        review_file = pin(inside(original['independentReview'], RUN / 'jobs'), original['independentReviewSha256'])
        require(draft_file.name == 'draft-result.json' and review_file.name == 'review-verified.json',
                'Unexpected original draft or review filename')
        generation = draft_file.parent
        wave = generation.parent
        require(wave.parent == safe(RUN / 'jobs') and re.fullmatch(r'author-wave-[0-9]{2}', wave.name) is not None,
                'Selected draft does not belong to a new author wave')
        author_result = pin(generation / 'author-document-result.json')
        result = load(author_result)
        require(result['schema'] == 'spec-agent-author-document-result/1' and
                result['status'] == 'TEXT_REVIEW_APPROVED' and result['documentId'] == definition['id'] and
                result['path'] == definition['path'] and result['kind'] == definition['kind'] and
                result['capsule'] == state and result['planSha256'] == args.plan_sha256 and
                result['executionContextSha256'] == guard.CONTEXT_SHA and
                safe(result['textPin']['path']) == source_pin and result['textPin']['sha256'] == sha(source_pin),
                'Author result does not confirm the exact reviewed document and source pin')
        wave_before = pin(wave / 'author-inputs-before.json')
        wave_after = pin(wave / 'author-inputs-after.json')
        before_value, after_value = load(wave_before), load(wave_after)
        require(after_value['status'] == 'UNCHANGED' and after_value['input'] == before_value['input'] and
                after_value['preparationSha256'] == before_value['preparationSha256'] and
                after_value['input']['snapshot'] == state and after_value['input']['planSha256'] == args.plan_sha256 and
                after_value['input']['executionContextSha256'] == guard.CONTEXT_SHA and
                after_value['input']['grantSha256'] == original['activationGrantSha256'],
                'Author wave did not complete with unchanged bound inputs')
        require(original['waveIntegrityVerificationRequiredForCollection'] is True and
                original['waveVerification'] == {'before': str(wave_before), 'beforeSha256': sha(wave_before),
                                                'after': str(wave_after), 'result': str(safe(wave / 'author-wave-result.json'))},
                'Text pin wave-integrity requirement or paths differ')
        wave_result = pin(wave / 'author-wave-result.json')
        completed = load(wave_result)
        require(completed['waveIntegrityVerified'] is True and completed['input'] == after_value['input'] and
                completed['preparationSha256'] == after_value['preparationSha256'] and
                safe(completed['inputsAfter']) == wave_after and completed['inputsAfterSha256'] == sha(wave_after),
                'Completed author wave result differs from successful unchanged inputs')
        matching = [doc for doc in completed['documents'] if doc['documentId'] == definition['id']]
        require(len(matching) == 1 and matching[0] == result,
                'Final wave result does not contain the exact approved document result')
        preparation = pin(inside(completed['preparation'], REPORT / 'author-preparation'),
                          after_value['preparationSha256'])
        require(preparation == safe(REPORT / 'author-preparation' / wave.name / 'preparation.json'),
                'Actual author preparation belongs to another wave')
        prepared = load(preparation)
        require(prepared['schema'] == 'spec-agent-author-wave-preparation/1' and prepared['wave'] == wave.name and
                prepared['input'] == after_value['input'] and prepared['providerStarted'] is False and
                definition['id'] in prepared['documents'], 'Actual author preparation input/selection differs')
        grant = pin(inside(after_value['input']['grant'], REPORT), after_value['input']['grantSha256'])
        grant_value = load(grant)
        require(grant_value['driverSha256'] == prepared['helperSha256'] and
                grant_value['capsuleManifestSha256'] == guard.SNAPSHOT_SHA and
                grant_value['executionContextSha256'] == guard.CONTEXT_SHA,
                'Actual activation grant differs from this source/context/driver')
        for filename, digest in after_value['input']['pinnedFiles'].items():
            metadata_file = safe(filename)
            require(metadata_file.is_relative_to(safe(RUN)) or metadata_file.is_relative_to(safe(REPORT)) or
                    metadata_file == safe(guard.RECEIPT), 'Wave metadata pin leaves its permitted roots')
            pin(metadata_file, digest)
        execution_metadata = bind_optional_metadata(after_value['input'], definition, value, prepared, grant_value, pin)
        review_handoff = pin(review_file.parent / 'review-handoff.json')
        draft, review, handoff = load(draft_file), load(review_file), load(review_handoff)
        require(draft['aiAuthored'] is True and draft['semanticProseAssembledByPython'] is False and
                draft['documentId'] == definition['id'] == review['documentId'] and
                draft['path'] == definition['path'] and draft['snapshot'] == state == handoff['snapshot'] and
                draft['referenceMode'] == 'source-only' == handoff['referenceMode'] and
                draft['contentSha256'] == sha(document) == handoff['documentSha256'] and
                handoff['reviewSha256'] == sha(review_file) and safe(handoff['documentFile']) == document and
                handoff['approved'] is True and review['approved'] is True and not review['unresolved'] and
                handoff['reviewScope'] == 'text-source-and-structure' and
                handoff['visualFidelityVerified'] is False and handoff['formallyEvaluatedByOriginalRubric'] is False and
                not any(f['severity'] in {'major', 'critical'} for f in review['findings']),
                'Draft and approved review do not bind the unchanged canonical text')
        raw_review = pin(review_file.parent / 'answer.txt')
        require(capsule._load_json(raw_review) == review, 'Original independent review answer differs')
        require(provider_answer(review_file.parent, schemas.REVIEW) == review,
                'Independent document review differs from its successful original provider evidence')
        generated = provider_answer(draft_file.parent / 'draft', schemas.DRAFT)
        require(generated['documentId'] == definition['id'] and generated['path'] == definition['path'] and
                generated['content'].encode('utf-8') == document.read_bytes(),
                'Reviewed canonical Markdown differs from the unchanged original AI draft response')
        original_prompt = safe(draft_file.parent / 'draft/prompt.txt').read_text(encoding='utf-8')
        marker = '\n対象文書計画:\n'
        require(marker in original_prompt, 'Draft prompt lacks its original document definition')
        prompt_definition, _ = json.JSONDecoder().raw_decode(original_prompt.split(marker, 1)[1])
        require(prompt_definition == definition, 'Draft prompt belongs to another document plan')
        review_prompt = safe(review_file.parent / 'prompt.txt').read_bytes().decode('utf-8')
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
            expected_review = (provider.COMMON_POLICY + '\nUser task (within that boundary):\n' +
                prompts.REVIEW + workflow._document_context(guard.SNAPSHOT, bound_definition_for_review) +
                REVIEW_SCOPE_MARKER + json.dumps(context, ensure_ascii=False, indent=2) +
                METADATA_REVIEW_MARKER + json.dumps(execution_metadata['context'], ensure_ascii=False, indent=2) +
                '\n原稿本文:\n' + document.read_bytes().decode('utf-8') +
                '\n構造検査の指摘（意味の正確さを採点した結果ではありません）:\n' + json.dumps(structure, ensure_ascii=False))
            require(review_prompt == expected_review,
                    'Complete supplemental review prompt differs from bound source/text/structure')
        workflow.references_valid(review, manifest)
        findings = validate_document(document.read_text(encoding='utf-8'), definition['path'],
                                     expected_document_id=definition['id'], expected_kind=definition['kind'])
        require(not findings, 'Current structure inspection failed: ' + json.dumps(findings, ensure_ascii=False))
        analysis_job = inside(draft['analysisJob'], RUN / 'jobs')
        bound_definition = workflow.select_document(plan, definition['id'])
        analysis, checkpoint, checkpoint_sha = workflow._resume_analysis(guard.SNAPSHOT, bound_definition, analysis_job)
        analysis_marker = '\nAIによる解析素材:\n'
        require(analysis_marker in original_prompt, 'Draft prompt lacks its original AI analysis bundle')
        analysis_text = original_prompt.rsplit(analysis_marker, 1)[1]
        prompt_analysis, analysis_end = json.JSONDecoder().raw_decode(analysis_text)
        require(not analysis_text[analysis_end:].strip() and prompt_analysis == analysis,
                'Draft used a different analysis bundle from the selected unchanged checkpoint')
        require(analysis['documentId'] == definition['id'] and checkpoint['referenceMode'] == 'source-only',
                'Fresh source analysis identity/mode mismatch')
        pin(analysis_job / 'analysis-verified.json', checkpoint['analysisSha256'])
        pin(analysis_job / 'analysis-handoff.json', checkpoint_sha)
        for filename, digest in checkpoint['providerArtifactsSha256'].items():
            pin(inside(analysis_job / checkpoint['providerDirectory'] / filename, analysis_job), digest)
        for filename, digest in checkpoint['snapshotEvidenceSha256'].items():
            pin(inside(analysis_job / filename, analysis_job), digest)
        workflow.references_valid(analysis, manifest)
        for role in ('generationRuntime', 'reviewRuntime', 'structureRuntime'):
            role_pin = original[role]
            require(safe(role_pin['record']) == safe(guard.RECEIPT) and
                    role_pin['recordSha256'] == guard.RECEIPT_SHA and
                    safe(role_pin['directory']) == safe(guard.RUNTIME), 'Unexpected document stage runtime')
        relative = workflow.relative_path(definition['path'])
        target = inside(output / relative, output)
        records.append({'documentId': definition['id'], 'kind': definition['kind'], 'path': definition['path'],
                        'sourceReviewedMarkdown': str(document), 'sha256': sha(document),
                        'canonicalMarkdown': str(target), 'sourcePin': str(source_pin),
                        'sourcePinSha256': sha(source_pin), 'draftResult': str(draft_file),
                        'draftResultSha256': sha(draft_file), 'independentReview': str(review_file),
                        'independentReviewSha256': sha(review_file), 'analysisJob': str(analysis_job),
                        'analysisHandoffSha256': checkpoint_sha, 'reviewScope': handoff['reviewScope'],
                        'basisCounts': original['basisCounts'], 'sourcePathsRead': analysis['sourcePathsRead'],
                        'independentReviewApproved': True, 'structureStatus': 'STRUCTURE_VALID',
                        'reportOnly': definition['kind'] == 'analysis-report'})
        if execution_metadata is not None:
            records[-1]['executionMetadata'] = execution_metadata['provenance']

    def recheck():
        guard.recheck(fixed, runtime)
        for path, expected in input_pins.items():
            require(sha(path) == expected, 'Collected input changed: ' + path)

    recheck()
    output.mkdir(parents=True, exist_ok=False)
    for record in records:
        target = safe(record['canonicalMarkdown'])
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = safe(record['sourceReviewedMarkdown']).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == record['sha256'], 'Source changed before copying')
        with target.open('xb') as stream:
            stream.write(raw)
        require(sha(target) == record['sha256'], 'Byte copy changed the reviewed document')
    recheck()
    actual = {}
    def inventory(directory):
        for entry in safe(directory).iterdir():
            entry = safe(entry)
            if entry.is_dir():
                inventory(entry)
            else:
                require(entry.is_file(), 'Unsupported output entry')
                actual[entry.relative_to(output).as_posix()] = sha(entry)
    inventory(output)
    require(actual == {doc['path']: doc['sha256'] for doc in records}, 'Collected file inventory differs')
    result = {'schema': 'spec-agent-text-reviewed-collection/1',
              'createdAt': datetime.now(timezone.utc).isoformat(),
              'status': 'TEXT_REVIEWED_CANDIDATE_DISPLAY_AND_QUALIFICATION_PENDING',
              'completePlan': not args.partial, 'documentCount': len(records),
              'specificationCount': sum(not d['reportOnly'] for d in records),
              'reportOnlyCount': sum(d['reportOnly'] for d in records),
              'documents': records, 'capsule': state, 'outputRoot': str(output),
              'pinnedInputs': input_pins, 'runtimeProvenance': runtime,
              'inputBeforeAfterUnchanged': True, 'bodyTransformationPerformed': False,
              'semanticProseAssembledByPython': False, 'visualFidelityVerified': False,
              'formalPercentage': None, 'originalApplicationExecuted': False, 'published': False}
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'documentCount': len(records),
                      'report': str(report), 'reportSha256': sha(report)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
