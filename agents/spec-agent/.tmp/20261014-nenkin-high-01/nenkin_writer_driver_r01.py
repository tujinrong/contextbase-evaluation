"""Scoped source-only author driver. Prepare first; root activation/audit precedes AI.

Python binds metadata and copies AI responses. It creates no business facts/prose.
Frozen core and loaded prompts are never replaced or monkeypatched.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import time

sys.dont_write_bytecode = True
REPO = Path(r'D:/開発/contextbase-evaluation')
WORK = REPO / 'agents/spec-agent/.tmp/20261014-nenkin-high-01'
REPORT = REPO / 'agents/spec-agent/report/20261014-nenkin-high-01'
SNAPSHOT = WORK / 'snapshot'
CAP_SHA = '92c339cb7040019312d0ec01669d22c44e4cc73fa373d5278c3f6f04c0c09631'
CONTEXT = WORK / 'execution-context.json'
CONTEXT_SHA = 'd3a4e4d1bedd6e4d7a2d8658f162e2d8f7a0119ffdb4529650f2a2d369ca90cc'
RECEIPT = REPO / 'agents/reverse-agent/test-report/20261013-rerun-12h/source-pilot/runtime-code-source-13.json'
RECEIPT_SHA = '5c3eeafb764afb64e3ef80fb422e4f68a9c41b98f000d13a8d57a505d947cc79'
RUNTIME = REPO / 'agents/reverse-agent/.tmp/20261013-rerun-12h/source-only/runtime-code/source-13/src'
SOURCE = REPO / 'agents/reverse-agent/input'
PROTECTED_SEAL = REPORT / 'protected-inputs-before.json'
DEADLINE = '2026-10-14T13:06:43.011844+00:00'
MANDATORY_KINDS = frozenset({'basic-design', 'detailed-specification',
    'logical-table-definition', 'physical-table-definition'})
# Other kinds are the exact root-approved plan/grant strings, never renamed here.
CRITICAL = ('contextbase.ai.capsule', 'contextbase.ai.workflow', 'contextbase.ai.provider',
    'contextbase.ai.prompts', 'contextbase.ai.schemas', 'contextbase.ai.validation', 'contextbase.ai.plan_review')
SCHEMAS = {
    'activation': (WORK / 'nenkin_author_activation_schema_r02.json', '30b9b6b267d29572d5fce795dad142dd8a10b94c84dd143df2f477e34f3cf4a2'),
    'text-pin': (WORK / 'nenkin_text_pin_schema_r02.json', '93bdbc1d0ae6b5f29949a7df96ab57dba783a042fdfef6d37b021d8a4e89619e'),
}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def safe(path):
    original = Path(path).absolute()
    for node in (original, *original.parents):
        require(not node.is_symlink() and not (node.exists() and
            getattr(node.lstat(), 'st_file_attributes', 0) & 0x400), 'Linked path refused before read/write')
    return original.resolve()

def inside(path, root):
    target, base = safe(path), safe(root)
    require(target != base and target.is_relative_to(base), 'Path outside the selected new-run root')
    return target

def raw(path):
    return safe(path).read_bytes()

def digest(value):
    return hashlib.sha256(value).hexdigest()

def sha(path):
    return digest(raw(path))

def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'Duplicate JSON member')
        result[key] = value
    return result

def load(path):
    return json.loads(raw(path).decode('utf-8-sig'), object_pairs_hook=pairs)

def write(path, value):
    path = safe(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def hash_arg(value):
    require(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None,
        'Exact lowercase SHA256 required')
    return value

def check_schema(name, value):
    from jsonschema import Draft202012Validator
    path, expected = SCHEMAS[name]
    require(sha(path) == expected, 'Author schema bytes changed')
    schema = load(path)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(value)

def inventory(root, *, cache=False):
    root, found = safe(root), {}
    def descend(directory):
        for candidate in sorted(safe(directory).iterdir()):
            path = safe(candidate)
            if cache and ('__pycache__' in path.parts or path.suffix == '.pyc'):
                continue
            if path.is_dir():
                descend(path)
            elif path.is_file():
                found[path.relative_to(root).as_posix()] = {'bytes': path.stat().st_size, 'sha256': sha(path)}
            else:
                raise ValueError('Unsupported inventory entry')
    descend(root)
    return found

def module_pin(name, expected, files):
    expected = safe(expected)
    require(expected.is_relative_to(safe(RUNTIME)), 'Module not in exact frozen runtime')
    found = importlib.util.find_spec(name)
    require(found is not None and found.origin is not None and safe(found.origin) == expected,
        'Discovery differs from exact frozen module before import')
    existing = sys.modules.get(name)
    if existing is not None:
        require(safe(existing.__file__) == expected and existing.__spec__ is not None and
            safe(existing.__spec__.origin) == expected, 'Preloaded module differs from exact freeze')
    module = importlib.import_module(name)
    require(safe(module.__file__) == expected and module.__spec__ is not None and
        safe(module.__spec__.origin) == expected and found is not None and safe(found.origin) == expected,
        'Loaded file/spec/find_spec differs from exact frozen module')
    key = expected.relative_to(safe(RUNTIME)).as_posix()
    require(key in files and sha(expected) == files[key], 'Module bytes differ from receipt')
    return {'path': str(expected), 'specOrigin': str(expected), 'sha256': files[key]}

def bootstrap():
    require(sha(RECEIPT) == RECEIPT_SHA, 'Frozen receipt changed')
    receipt = load(RECEIPT)
    require(safe(receipt['destination']) == safe(RUNTIME) and receipt['fileCount'] == 128,
        'Unexpected runtime receipt destination/count')
    files = {key: value['sha256'] for key, value in inventory(RUNTIME, cache=True).items()}
    require(files == receipt['files'] and len(files) == 128 and len(receipt['imports']) == 13,
        'Full frozen inventory or receipt import set differs')
    if not sys.path or sys.path[0] != str(safe(RUNTIME)):
        sys.path.insert(0, str(safe(RUNTIME)))
    imported = {name: module_pin(name, path, files) for name, path in receipt['imports'].items()}
    critical = {name: module_pin(name, RUNTIME / (name.replace('.', '/') + '.py'), files) for name in CRITICAL}
    validation = importlib.import_module('contextbase.ai.validation')
    require(validation.FEATURE_KINDS == frozenset({'basic-design', 'detailed-specification'}) and
        frozenset({'logical-table-definition', 'physical-table-definition'}) <= validation.TABLE_KINDS,
        'Mandatory canonical kind validators differ from the frozen profile')
    require(sha(RECEIPT) == RECEIPT_SHA and
        {k: v['sha256'] for k, v in inventory(RUNTIME, cache=True).items()} == files,
        'Runtime drift while loading imports')
    return {'receipt': str(safe(RECEIPT)), 'receiptSha256': RECEIPT_SHA,
        'runtimeRoot': str(safe(RUNTIME)), 'fileCount': 128, 'files': files,
        'receiptImports': imported, 'criticalModules': critical}

def plan_path(path):
    path = inside(path, WORK / 'jobs')
    require(path.name == 'plan-verified.json' and path.parent.parent == safe(WORK / 'jobs') and
        re.fullmatch(r'plan-[0-9]{2}', path.parent.name) is not None, 'Not this run verified plan')
    return path

def fixed_grant(path, expected_sha):
    path = inside(path, REPORT)
    require(sha(path) == hash_arg(expected_sha), 'Activation grant changed')
    value = load(path)
    check_schema('activation', value)
    require(value['schema'] == 'spec-agent-author-activation/1' and value['approved'] is True and
        value['agentRole'] == 'AG-SPEC' and value['projectId'] == 'nenkin' and value['mode'] == 'source-only' and
        value['runId'] == '20261014-nenkin-high-01' and value['deadline'] == DEADLINE and
        value['driverSha256'] == sha(__file__) and value['capsuleManifestSha256'] == CAP_SHA and
        value['executionContextSha256'] == CONTEXT_SHA and value['runtimeReceiptSha256'] == RECEIPT_SHA and
        value['codeAuditApproved'] is True, 'Activation role/code/scope/timing differs')
    audit = inside(value['codeAudit']['path'], REPORT)
    require(sha(audit) == hash_arg(value['codeAudit']['sha256']), 'Parent code-audit record drift')
    return path, value

def binding(grant_path, grant_sha, *, check_deadline=True):
    runtime = bootstrap()
    grant_path, grant = fixed_grant(grant_path, grant_sha)
    from contextbase.ai import capsule, workflow, plan_review
    if check_deadline:
        workflow._timeout(1, DEADLINE)
    require(sha(SNAPSHOT / 'manifest.json') == CAP_SHA and sha(CONTEXT) == CONTEXT_SHA,
        'Capsule manifest or full execution context changed')
    context = load(CONTEXT)
    require(context['schema'] == 'spec-agent-execution-context/1' and context['agentRole'] == 'AG-SPEC' and
        context['projectId'] == 'nenkin' and context['primarySourceDirectory'] == 'nenkin' and
        context['dependencySourceDirectory'] == 'n2framework' and context['sourceOnly'] is True and
        context['originalSpecificationsAuthorized'] is False and context['evaluationExpectationsAuthorized'] is False and
        context['originalProgramsAndDatabaseExecutionAuthorized'] is False and context['existingBusinessProseProvided'] is False,
        'Execution context scope/mode differs')
    manifest = capsule.verify(SNAPSHOT)
    state = capsule.verification_state(SNAPSHOT)
    require(state['mode'] == 'source-only' and state['manifestSha256'] == CAP_SHA and manifest['projectId'] == 'nenkin',
        'Capsule source-only identity differs')
    plan = plan_path(grant['plan']['path'])
    require(sha(plan) == hash_arg(grant['plan']['sha256']), 'Exact approved plan changed')
    handoff = safe(plan.parent / 'plan-handoff.json')
    require(sha(handoff) == hash_arg(grant['plan']['handoffSha256']), 'Plan handoff changed')
    plan_value = load(plan)
    workflow._validate_plan(plan_value, manifest)
    tuples = [(x['id'], x['kind'], x['path']) for x in plan_value['documents']]
    granted = [(x['id'], x['kind'], x['path']) for x in grant['documents']]
    require(len(tuples) == len(set(tuples)) and len(granted) == len(set(granted)) and
        set(tuples) == set(granted) and all(isinstance(kind, str) and kind and kind == kind.strip() for _, kind, _ in tuples),
        'Activation must contain all exact approved IDs/paths/canonical kinds')
    first = workflow.select_document(plan, plan_value['documents'][0]['id'])
    require(first.handoff_sha == grant['plan']['handoffSha256'] and
        workflow._definition_state(SNAPSHOT, first) == state, 'Bound plan capsule/handoff differs')
    review_file = inside(grant['planReview']['path'], WORK / 'jobs')
    require(review_file.name == 'plan-review-verified.json' and
        sha(review_file) == hash_arg(grant['planReview']['sha256']), 'Independent plan review differs')
    review = load(review_file)
    plan_review._validate(review, plan_value, manifest)
    require(review['approved'] is True and not review['blockingUnresolved'] and
        not any(x['severity'] in {'critical', 'major'} for x in review['findings']), 'Plan is not independently approved')
    review_handoff = safe(review_file.parent / 'plan-review-handoff.json')
    require(sha(review_handoff) == hash_arg(grant['planReview']['handoffSha256']), 'Plan review handoff differs')
    rh = load(review_handoff)
    require(rh['snapshot'] == state and rh['planSha256'] == sha(plan) and rh['planHandoffSha256'] == sha(handoff) and
        rh['referenceMode'] == 'source-only' and rh['executionContextSha256'] == CONTEXT_SHA and
        rh['reviewSha256'] == sha(review_file) and rh['approved'] is True and rh['aiResponseBytesModified'] is False,
        'Plan review provenance is not bound to current scope and plan')
    before = safe(review_file.parent.parent / (review_file.parent.name + '-plan-review-before.json'))
    after = safe(review_file.parent.parent / (review_file.parent.name + '-plan-review-after.json'))
    bp, ap = load(before), load(after)
    require(ap['status'] == 'UNCHANGED_AND_REVIEW_VALIDATED' and ap['input'] == bp['input'] and
        bp['input']['snapshot'] == state and bp['input']['planSha256'] == sha(plan) and
        bp['input']['executionContextSha256'] == CONTEXT_SHA, 'Plan-review before/after binding differs')
    artifacts = [review_file, review_handoff, before, after]
    for name in ('answer.txt', 'result.json', 'schema.json', 'prompt.txt'):
        artifacts.append(safe(review_file.parent / name))
    require(load(review_file.parent / 'answer.txt') == review and rh['originalAiResponse'] == 'answer.txt',
        'Verified plan review differs from unchanged raw AI answer')
    require(sha(PROTECTED_SEAL) == hash_arg(grant['protectedInputSealSha256']), 'Original input seal changed')
    original_seal = load(PROTECTED_SEAL)
    require(original_seal['schema'] == 'spec-agent-input-seal/1' and safe(original_seal['sourceRoot']) == safe(SOURCE),
        'Protected original source root differs')
    original_files = {x['path']: {'bytes': x['bytes'], 'sha256': x['sha256']} for x in original_seal['files']}
    require(len(original_files) == len(original_seal['files']) and inventory(SOURCE) == original_files,
        'Full original input inventory drift')
    files = [grant_path, safe(__file__), safe(CONTEXT), safe(RECEIPT), safe(PROTECTED_SEAL), plan, handoff,
        *[safe(item[0]) for item in SCHEMAS.values()],
        inside(grant['codeAudit']['path'], REPORT), *artifacts]
    pins = {str(path): sha(path) for path in files}
    require(sha(SNAPSHOT / 'manifest.json') == CAP_SHA and sha(CONTEXT) == CONTEXT_SHA and sha(grant_path) == grant_sha,
        'Fixed metadata drift during collection')
    return {'snapshot': state, 'executionContextSha256': CONTEXT_SHA, 'grant': str(grant_path), 'grantSha256': grant_sha,
        'plan': str(plan), 'planSha256': sha(plan), 'planHandoffSha256': sha(handoff),
        'planReviewSha256': sha(review_file), 'runtime': runtime, 'pinnedFiles': pins}, plan_value, context

def recheck(pin, *, check_deadline=True):
    now, value, context = binding(pin['grant'], pin['grantSha256'], check_deadline=check_deadline)
    require(now == pin, 'Author input/runtime/context drift')
    return value, context

def prepare(activation, activation_sha, wave, document_ids, workers, timeout):
    require(isinstance(wave, str) and re.fullmatch(r'author-wave-[0-9]{2}', wave) is not None, 'Invalid fresh wave name')
    require(type(workers) is int and 1 <= workers <= 4 and type(timeout) is int and 1 <= timeout <= 2400,
        'Invalid bounded worker/timeout values')
    pin, plan, context = binding(activation, hash_arg(activation_sha))
    available = {d['id'] for d in plan['documents']}
    selected = list(document_ids) if document_ids else sorted(available)
    require(selected and len(selected) == len(set(selected)) and set(selected) <= available, 'Invalid document wave subset')
    paths = {'jobs': str(safe(WORK / 'jobs' / wave)), 'drafts': str(safe(WORK / 'drafts' / wave)),
        'preparation': str(safe(REPORT / 'author-preparation' / wave))}
    require(not any(safe(path).exists() for path in paths.values()), 'Use new preparation/job/draft paths')
    recheck(pin)
    record = {'schema': 'spec-agent-author-wave-preparation/1', 'createdAt': datetime.now(timezone.utc).isoformat(),
        'agentRole': 'AG-SPEC', 'projectId': 'nenkin', 'mode': 'source-only', 'wave': wave,
        'documents': selected, 'workers': workers, 'timeout': timeout, 'deadline': DEADLINE,
        'paths': paths, 'input': pin, 'helper': str(safe(__file__)), 'helperSha256': sha(__file__),
        'providerStarted': False, 'frozenCoreOrLoadedPromptModified': False, 'businessProseAssembledByPython': False}
    target = safe(Path(paths['preparation']) / 'preparation.json')
    write(target, record)
    return {'preparation': str(target), 'sha256': sha(target), 'providerStarted': False}

def scoped_review(definition, document, job, timeout, pin, context):
    from contextbase.ai import capsule, workflow, prompts, schemas
    from contextbase.ai.validation import validate_document
    recheck(pin)
    state = workflow._definition_state(SNAPSHOT, definition)
    manifest = capsule.verify(SNAPSHOT)
    document = safe(document)
    document_bytes, document_sha = raw(document), sha(document)
    findings = validate_document(document_bytes.decode('utf-8'), definition['path'],
        expected_document_id=definition['id'], expected_kind=definition['kind'])
    prompt = (prompts.REVIEW + workflow._document_context(SNAPSHOT, definition) +
        '\nユーザー指定scopeのメタデータ全文（原文・期待仕様・追加読取り許可ではありません）:\n' +
        json.dumps(context, ensure_ascii=False, indent=2) + '\n原稿本文:\n' + document_bytes.decode('utf-8') +
        '\n構造検査の指摘（意味の正確さを採点した結果ではありません）:\n' + json.dumps(findings, ensure_ascii=False))
    answer = workflow._bound_job(SNAPSHOT, job, prompt, schemas.REVIEW, timeout, state, DEADLINE)
    recheck(pin)
    require(sha(document) == document_sha and answer['documentId'] == definition['id'], 'Reviewed document identity/bytes drift')
    workflow.references_valid(answer, manifest)
    require(not answer['approved'] or (not answer['unresolved'] and
        not any(x['severity'] in {'critical', 'major'} for x in answer['findings'])), 'AI cannot approve blocking findings')
    require(load(job / 'answer.txt') == answer, 'Review differs semantically from preserved raw AI response')
    if answer['approved'] and findings:
        write(job / 'structure-approval-conflict.json', {'status': 'AI_APPROVAL_REJECTED_STRUCTURE_INVALID',
            'findings': findings, 'documentSha256': document_sha})
        raise workflow.ReviewStructureConflict(answer, findings)
    verified = safe(job / 'review-verified.json')
    with verified.open('xb') as stream:
        stream.write(raw(job / 'answer.txt'))
    write(job / 'review-handoff.json', {'schema': 'reverse-ai-review-handoff/1', 'snapshot': state,
        'documentFile': str(document), 'documentSha256': document_sha, 'reviewSha256': sha(verified),
        'referenceMode': 'source-only', 'approved': answer['approved'], 'reviewScope': 'text-source-and-structure',
        'visualFidelityVerified': False, 'formallyEvaluatedByOriginalRubric': False,
        'unassessedScopes': ['visual-fidelity', 'application-runtime', 'formal-semantic-scoring'],
        'executionContextSha256': CONTEXT_SHA, 'aiResponseBytesModified': False})
    recheck(pin)
    return answer

def text_pin(definition, generation, document, draft, review, pin, output):
    from contextbase.ai.validation import validate_document
    findings = validate_document(raw(document).decode('utf-8'), definition['path'],
        expected_document_id=definition['id'], expected_kind=definition['kind'])
    require(review['approved'] is True and not review['findings'] and not review['unresolved'] and not findings,
        'Final text pin requires zero-finding independent review and structure')
    draft_file = safe(generation / 'draft-result.json')
    review_file = safe(generation / 'independent-review/review-verified.json')
    require(sha(document) == draft['contentSha256'] and load(review_file) == review, 'Final text provenance differs')
    analysis = load(generation / 'analysis-verified.json')
    basis = {name: sum(f['basis'] == name for f in analysis['facts']) for name in ['observed-source', 'reference-design']}
    require(basis['reference-design'] == 0, 'Source-only facts cannot adopt reference-design material')
    runtime = {'record': str(safe(RECEIPT)), 'recordSha256': RECEIPT_SHA, 'runtimeId': 'source-13',
        'directory': str(safe(RUNTIME)), 'fileCount': 128, 'receiptImportCount': 13,
        'promptModuleSha256': pin['runtime']['files']['contextbase/ai/prompts.py']}
    result = {'schema': 'spec-agent-text-reviewed-document-pin/1', 'createdAt': datetime.now(timezone.utc).isoformat(),
        'agentRole': 'AG-SPEC', 'projectId': 'nenkin', 'mode': 'source-only', 'documentId': definition['id'],
        'path': definition['path'], 'kind': definition['kind'], 'canonicalMarkdown': str(safe(document)), 'sha256': sha(document),
        'draftResult': str(draft_file), 'draftResultSha256': sha(draft_file), 'outputRoot': str(safe(output)),
        'independentReview': str(review_file), 'independentReviewSha256': sha(review_file),
        'independentReviewApproved': True, 'noFurtherTextRevisionPlanned': True,
        'structureStatus': 'STRUCTURE_VALID', 'structureFindings': [], 'capsule': pin['snapshot'], 'basisCounts': basis,
        'generationRuntime': runtime, 'reviewRuntime': runtime, 'structureRuntime': runtime,
        'analysisJob': str(safe(generation)), 'analysisExecutedInThisJob': True,
        'sourcePathsRead': analysis['sourcePathsRead'], 'executionContextSha256': CONTEXT_SHA,
        'planSha256': pin['planSha256'], 'activationGrantSha256': pin['grantSha256'],
        'disposition': 'report-only' if definition['kind'] == 'analysis-report' else 'specification',
        'includedInFinalSpecificationBundle': definition['kind'] != 'analysis-report',
        'reviewScope': 'text-source-and-structure', 'visualFidelityVerified': False,
        'formalScoringVerified': False, 'published': False, 'originalApplicationOrDatabaseExecuted': False,
        'businessProseAssembledByPython': False}
    recheck(pin)
    check_schema('text-pin', result)
    target = safe(generation / 'text-reviewed-pin.json')
    write(target, result)
    return {'path': str(target), 'sha256': sha(target), 'disposition': result['disposition']}

def run(preparation, preparation_sha):
    preparation = inside(preparation, REPORT / 'author-preparation')
    require(preparation.name == 'preparation.json' and sha(preparation) == hash_arg(preparation_sha), 'Preparation differs')
    record = load(preparation)
    require(record['schema'] == 'spec-agent-author-wave-preparation/1' and record['agentRole'] == 'AG-SPEC' and
        record['mode'] == 'source-only' and record['deadline'] == DEADLINE and record['providerStarted'] is False and
        record['helper'] == str(safe(__file__)) and record['helperSha256'] == sha(__file__), 'Prepared author identity differs')
    require(type(record['workers']) is int and 1 <= record['workers'] <= 4 and
        type(record['timeout']) is int and 1 <= record['timeout'] <= 2400, 'Prepared bounds differ')
    pin = record['input']
    plan, context = recheck(pin)
    wave = record['wave']
    require(re.fullmatch(r'author-wave-[0-9]{2}', wave) is not None, 'Invalid prepared wave')
    job_root, drafts = safe(WORK / 'jobs' / wave), safe(WORK / 'drafts' / wave)
    require(record['paths'] == {'jobs': str(job_root), 'drafts': str(drafts),
        'preparation': str(safe(REPORT / 'author-preparation' / wave))} and
        preparation == safe(REPORT / 'author-preparation' / wave / 'preparation.json'), 'Prepared path escape')
    require(not job_root.exists() and not drafts.exists(), 'Use fresh job and draft roots')
    available = {d['id']: d for d in plan['documents']}
    selected = record['documents']
    require(selected and len(selected) == len(set(selected)) and set(selected) <= set(available), 'Prepared document set differs')
    from contextbase.ai import workflow
    definitions = {key: workflow.select_document(Path(pin['plan']), key) for key in selected}
    job_root.mkdir(parents=True, exist_ok=False)
    drafts.mkdir(parents=True, exist_ok=False)
    write(job_root / 'author-inputs-before.json', {'preparationSha256': preparation_sha, 'input': pin})
    started = time.monotonic()

    def task(identity):
        definition = definitions[identity]
        folder = digest(identity.encode('utf-8'))[:16]
        generation = safe(job_root / folder)
        output = safe(drafts / ('analysis-reports' if definition['kind'] == 'analysis-report' else 'specifications'))
        try:
            require((datetime.fromisoformat(DEADLINE) - datetime.now(timezone.utc)).total_seconds() > 60,
                'RuntimeErrorTimeLimit: no fresh author phase near deadline')
            require(sha(preparation) == preparation_sha, 'Preparation drift before generation')
            recheck(pin)
            begin = time.monotonic()
            # Metadata, not previous business prose, is supplied unchanged as scope.
            draft = workflow.document(SNAPSHOT, definition, generation, output, timeout=record['timeout'],
                deadline=DEADLINE, revision_context=context)
            recheck(pin)
            require(sha(preparation) == preparation_sha, 'Preparation drift during generation')
            document = safe(output / definition['path'])
            saved = {'event': 'new-draft-saved', 'documentId': identity, 'path': definition['path'],
                'kind': definition['kind'], 'canonicalMarkdown': str(document), 'sha256': sha(document),
                'draftResult': str(safe(generation / 'draft-result.json')), 'draftResultSha256': sha(generation / 'draft-result.json'),
                'outputRoot': str(output), 'capsule': pin['snapshot'], 'runtimeId': 'source-13',
                'generationElapsedSeconds': round(time.monotonic() - begin, 3),
                'structureStatus': 'STRUCTURE_INVALID' if draft['structureFindings'] else 'STRUCTURE_VALID',
                'disposition': 'report-only' if definition['kind'] == 'analysis-report' else 'specification'}
            require(saved['sha256'] == draft['contentSha256'], 'Saved draft differs from AI response')
            write(generation / 'draft-saved-notification.json', saved)
            print(json.dumps(saved, ensure_ascii=False), flush=True)
            review = scoped_review(definition, document, generation / 'independent-review', record['timeout'], pin, context)
            accepted = review['approved'] is True and not review['findings'] and not review['unresolved'] and not draft['structureFindings']
            result = {'documentId': identity, 'path': definition['path'], 'kind': definition['kind'],
                'status': 'TEXT_REVIEW_APPROVED' if accepted else 'REQUIRES_AI_REVISION', 'draft': saved,
                'review': {'path': str(safe(generation / 'independent-review/review-verified.json')),
                    'sha256': sha(generation / 'independent-review/review-verified.json'), 'approved': review['approved']},
                'visualFidelityVerified': False, 'formalScoringVerified': False, 'published': False}
            if accepted:
                result['textPin'] = text_pin(definition, generation, document, draft, review, pin, output)
            write(generation / 'author-document-result.json', result)
            print(json.dumps({'event': 'document-review-completed', **result}, ensure_ascii=False), flush=True)
            return result
        except Exception as exc:
            result = {'documentId': identity, 'path': definition['path'], 'kind': definition['kind'],
                'status': 'NOT_RUN_TIME_LIMIT' if 'RuntimeErrorTimeLimit' in str(exc) else 'FAILED',
                'errorType': type(exc).__name__, 'error': str(exc), 'originalAiArtifactsPreserved': True,
                'published': False}
            write(generation / 'author-failure.json', result)
            return result

    results = []
    try:
        with ThreadPoolExecutor(max_workers=record['workers']) as executor:
            futures = {executor.submit(task, identity): identity for identity in selected}
            for future in as_completed(futures):
                results.append(future.result())
        recheck(pin, check_deadline=False)
        require(sha(preparation) == preparation_sha, 'Preparation changed before wave completion')
        write(job_root / 'author-inputs-after.json', {'status': 'UNCHANGED', 'preparationSha256': preparation_sha, 'input': pin})
    except Exception as exc:
        write(job_root / 'author-inputs-after.json', {'status': 'NOT_VERIFIED', 'errorType': type(exc).__name__,
            'error': str(exc), 'preparationSha256': preparation_sha})
        raise
    complete = len(results) == len(selected) and all(x['status'] == 'TEXT_REVIEW_APPROVED' for x in results)
    summary = {'schema': 'spec-agent-author-wave-result/1', 'createdAt': datetime.now(timezone.utc).isoformat(),
        'status': 'TEXT_REVIEW_APPROVED' if complete else 'INCOMPLETE', 'agentRole': 'AG-SPEC',
        'mode': 'source-only', 'capsule': pin['snapshot'], 'seconds': round(time.monotonic() - started, 3),
        'documents': results, 'specificationDocuments': [x['documentId'] for x in results if x['kind'] != 'analysis-report'],
        'reportOnlyDocuments': [x['documentId'] for x in results if x['kind'] == 'analysis-report'],
        'analysisReportsIncludedInFinalExcelCount': False, 'visualFidelityVerified': False,
        'formalScoringVerified': False, 'published': False, 'businessProseAssembledByPython': False}
    write(job_root / 'author-wave-result.json', summary)
    return summary

def main():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest='command', required=True)
    pre = subs.add_parser('prepare')
    pre.add_argument('--activation', required=True)
    pre.add_argument('--activation-sha256', required=True)
    pre.add_argument('--wave', required=True)
    pre.add_argument('--document-id', action='append', default=[])
    pre.add_argument('--workers', type=int, default=2)
    pre.add_argument('--timeout', type=int, default=2400)
    exe = subs.add_parser('run')
    exe.add_argument('--preparation', required=True)
    exe.add_argument('--preparation-sha256', required=True)
    args = parser.parse_args()
    value = prepare(args.activation, args.activation_sha256, args.wave, args.document_id, args.workers, args.timeout) \
        if args.command == 'prepare' else run(args.preparation, args.preparation_sha256)
    print(json.dumps(value, ensure_ascii=False))

if __name__ == '__main__':
    main()
