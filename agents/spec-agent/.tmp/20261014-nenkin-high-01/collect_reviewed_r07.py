"""Collect byte-identical, independently reviewed new-source drafts; no prose authoring."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, importlib.util, json, re, sys
sys.dont_write_bytecode = True
RUN = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
REPORT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
HELPER = RUN / 'review_plan_with_scope_r03.py'
HELPER_SHA = 'cec73d552fa2ae35f14f9b6151f4552ca0c8d7a3c451bcba92fef8f43b0944c2'

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
