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
    'activation': (WORK / 'nenkin_author_activation_schema_r03.json', '5f4b54ebd7f44bd152870eb733f7dc8dfba50d7de5368c614f6da32961276a87'),
    'text-pin': (WORK / 'nenkin_text_pin_schema_r03.json', 'ac3ef2fe057d94f71e5283cf3604d306c66699a5793a0dc0576380226ae45179'),
}

METADATA_SCHEMAS = {
    'completion': (WORK / 'nenkin_execution_metadata_completion_schema_r01.json', 'baa7c57552376765ee7dfc4e735a8f68975ec847f5a33ea3480027eb496947ca'),
    'routing': (WORK / 'nenkin_execution_metadata_routing_schema_r01.json', 'de28dbd6b0b72a1f7dbfb8932579197c61a728cca52abb62193183d0e60d609b'),
    'supplement': (WORK / 'nenkin_execution_metadata_supplement_schema_r01.json', '07b6588942e001f4e463b33a0e03f27b25f5ed23abeec9312f3dbe8d79a847c2'),
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
        value['driverSha256'] == sha(__file__) and value['runtimeReceiptSha256'] == RECEIPT_SHA and
        value['codeAuditApproved'] is True, 'Activation role/code/scope/timing differs')
    audit = inside(value['codeAudit']['path'], REPORT)
    require(sha(audit) == hash_arg(value['codeAudit']['sha256']), 'Parent code-audit record drift')
    return path, value

def binding(grant_path, grant_sha, *, check_deadline=True):
    runtime = bootstrap()
    grant_path, grant = fixed_grant(grant_path, grant_sha)
    from contextbase.ai import provider
    snapshot = inside(grant['capsuleRoot'], WORK)
    context_file = inside(grant['executionContext'], WORK)
    require(snapshot.parent == safe(WORK) and snapshot.name.startswith('snapshot') and
        context_file.parent == safe(WORK) and context_file.suffix == '.json', 'Selected capsule/context path escapes root')
    cap_sha = hash_arg(grant['capsuleManifestSha256'])
    context_sha = hash_arg(grant['executionContextSha256'])
    from contextbase.ai import capsule, workflow, plan_review
    if check_deadline:
        workflow._timeout(1, DEADLINE)
    require(sha(snapshot / 'manifest.json') == cap_sha and sha(context_file) == context_sha,
        'Capsule manifest or full execution context changed')
    context = load(context_file)
    require(context['schema'] == 'spec-agent-execution-context/1' and context['agentRole'] == 'AG-SPEC' and
        context['projectId'] == 'nenkin' and context['primarySourceDirectory'] == 'nenkin' and
        context['dependencySourceDirectory'] == 'n2framework' and context['sourceOnly'] is True and
        context['originalSpecificationsAuthorized'] is False and context['evaluationExpectationsAuthorized'] is False and
        context['originalProgramsAndDatabaseExecutionAuthorized'] is False and context['existingBusinessProseProvided'] is False,
        'Execution context scope/mode differs')
    manifest = capsule.verify(snapshot)
    state = capsule.verification_state(snapshot)
    require(state['mode'] == 'source-only' and state['manifestSha256'] == cap_sha and manifest['projectId'] == 'nenkin',
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
        workflow._definition_state(snapshot, first) == state, 'Bound plan capsule/handoff differs')
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
        rh['referenceMode'] == 'source-only' and rh['executionContextSha256'] == context_sha and
        rh['reviewSha256'] == sha(review_file) and rh['approved'] is True and rh['aiResponseBytesModified'] is False,
        'Plan review provenance is not bound to current scope and plan')
    before = safe(review_file.parent.parent / (review_file.parent.name + '-plan-review-before.json'))
    after = safe(review_file.parent.parent / (review_file.parent.name + '-plan-review-after.json'))
    bp, ap = load(before), load(after)
    require(ap['status'] == 'UNCHANGED_AND_REVIEW_VALIDATED' and ap['input'] == bp['input'] and
        bp['input']['snapshot'] == state and bp['input']['planSha256'] == sha(plan) and
        bp['input']['executionContextSha256'] == context_sha, 'Plan-review before/after binding differs')
    artifacts = [review_file, review_handoff, before, after]
    for name in ('answer.txt', 'result.json', 'schema.json', 'prompt.txt'):
        artifacts.append(safe(review_file.parent / name))
    require(raw(review_file.parent / 'answer.txt') == raw(review_file) and rh['originalAiResponse'] == 'answer.txt',
        'Verified plan review differs from unchanged raw AI answer bytes')
    raw_review, unused_prompt, provider_pins = provider_evidence(snapshot, review_file.parent, plan_review.PLAN_REVIEW, state)
    require(raw_review == review and rh['runtimeReceiptSha256'] == RECEIPT_SHA, 'Plan review provider/runtime differs')
    fixed_review_input = {'schema': 'reverse-ai-plan-review-input/1', 'snapshot': state,
        'planFile': str(plan), 'planSha256': sha(plan), 'planHandoffSha256': sha(handoff),
        'planOrigin': first.handoff['origin'], 'referenceMode': 'source-only',
        'executionContext': str(context_file), 'executionContextSha256': context_sha}
    prep_file = inside(REPORT / 'independent-plan-review' / review_file.parent.name / 'preparation.json', REPORT)
    require(sha(prep_file) == hash_arg(rh['scopePreparationSha256']), 'Scoped plan review preparation bytes differ')
    prepared = load(prep_file)
    helper = inside(prepared['helper'], WORK)
    require(helper.parent == safe(WORK) and re.fullmatch(r'review_plan_with_scope_r[0-9]{2}\.py', helper.name) is not None and
        sha(helper) == hash_arg(prepared['helperSha256']), 'Scoped review helper path/hash differs')
    expected_runtime = {'receiptSha256': RECEIPT_SHA, 'runtimeRoot': str(safe(RUNTIME)),
        'runtimeFileCount': 128, 'runtimeFiles': runtime['files'],
        'loadedImports': {name: {'path': x['path'], 'sha256': x['sha256']} for name, x in runtime['receiptImports'].items()},
        'criticalModules': {name: {'path': x['path'], 'sha256': x['sha256']} for name, x in runtime['criticalModules'].items()}}
    require(prepared['schema'] == 'spec-agent-scoped-plan-review-preparation/1' and prepared['agentRole'] == 'AG-SPEC' and
        prepared['reviewerRole'] == 'independent-plan-review' and prepared['providerStarted'] is False and
        prepared['coreOrFrozenPromptModified'] is False and prepared['businessProseAuthored'] is False and
        prepared['deadline'] == DEADLINE and type(prepared['timeout']) is int and 1 <= prepared['timeout'] <= 2400 and
        safe(prepared['job']) == review_file.parent and prepared['input'] == fixed_review_input and
        prepared['runtime'] == expected_runtime and
        prepared['schemaSha256'] == digest(json.dumps(plan_review.PLAN_REVIEW, sort_keys=True).encode()),
        'Scoped independent plan-review preparation identity/runtime/input differs')
    prepared_prompt = inside(prepared['promptFile'], prep_file.parent)
    require(prepared_prompt == safe(prep_file.parent / 'prepared-prompt.txt') and
        sha(prepared_prompt) == hash_arg(prepared['promptSha256']), 'Prepared plan-review prompt bytes differ')
    require(raw(review_file.parent / 'prompt.txt') ==
        (provider.COMMON_POLICY + '\nUser task (within that boundary):\n').encode('utf-8') + raw(prepared_prompt),
        'Actual plan-review scope prompt differs from its pinned preparation')
    require(bp == {'input': fixed_review_input, 'runtime': expected_runtime, 'preparationSha256': sha(prep_file)} and
        ap == {'status': 'UNCHANGED_AND_REVIEW_VALIDATED', 'input': fixed_review_input,
            'runtime': expected_runtime, 'preparationSha256': sha(prep_file)},
        'Scoped plan review did not finish with exact approved preparation/runtime')
    artifacts.extend([prep_file, prepared_prompt, helper, *[Path(p) for p in provider_pins]])
    require(sha(PROTECTED_SEAL) == hash_arg(grant['protectedInputSealSha256']), 'Original input seal changed')
    original_seal = load(PROTECTED_SEAL)
    require(original_seal['schema'] == 'spec-agent-input-seal/1' and safe(original_seal['sourceRoot']) == safe(SOURCE),
        'Protected original source root differs')
    original_files = {x['path']: {'bytes': x['bytes'], 'sha256': x['sha256']} for x in original_seal['files']}
    require(len(original_files) == len(original_seal['files']) and inventory(SOURCE) == original_files,
        'Full original input inventory drift')
    files = [grant_path, safe(__file__), safe(context_file), safe(RECEIPT), safe(PROTECTED_SEAL), plan, handoff,
        *[safe(item[0]) for item in SCHEMAS.values()],
        inside(grant['codeAudit']['path'], REPORT), *artifacts]
    pins = {str(path): sha(path) for path in files}
    require(sha(snapshot / 'manifest.json') == cap_sha and sha(context_file) == context_sha and sha(grant_path) == grant_sha,
        'Fixed metadata drift during collection')
    return {'snapshot': state, 'snapshotRoot': str(snapshot), 'executionContext': str(context_file),
        'executionContextSha256': context_sha, 'grant': str(grant_path), 'grantSha256': grant_sha,
        'plan': str(plan), 'planSha256': sha(plan), 'planHandoffSha256': sha(handoff),
        'planReviewSha256': sha(review_file), 'runtime': runtime, 'pinnedFiles': pins}, plan_value, context

METADATA_REVIEW_MARKER = '\n同一実行の経路・完了メタデータ全文（業務仕様根拠・原文・期待仕様・追加読取り許可ではありません）:\n'
METADATA_POLICY = ('The supplemental records describe only this run document routing and recorded execution state. '
    'They confer no business-evidence authority or source-reading permissions. Business facts must remain grounded '
    'in the unchanged source-only capsule. A recorded completion state is not a formal percentage or application-runtime result.')

def metadata_schema(name, value):
    from jsonschema import Draft202012Validator
    path, expected = METADATA_SCHEMAS[name]
    require(sha(path) == expected, 'Execution metadata schema bytes changed')
    schema = load(path)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(value)

def metadata_record_path(path):
    path = safe(path)
    bases = (safe(WORK / 'execution-metadata'), safe(REPORT / 'execution-metadata'))
    require(path.suffix == '.json' and any(path != base and path.is_relative_to(base) for base in bases),
        'Supplement and routing/completion records must be owned execution-metadata JSON files')
    return path

def metadata_evidence_path(path):
    path = safe(path)
    require(path.suffix == '.json' and any(path != safe(base) and path.is_relative_to(safe(base)) for base in (WORK, REPORT)),
        'Execution evidence JSON leaves the owned current run')
    if path.is_relative_to(safe(WORK)):
        require(not any(part.startswith('snapshot') for part in path.relative_to(safe(WORK)).parts),
            'Execution metadata adds no capsule or source reads')
    return path

def metadata_identity(value, pin):
    require(value['runId'] == '20261014-nenkin-high-01' and value['projectId'] == 'nenkin' and
        value['capsuleManifestSha256'] == pin['snapshot']['manifestSha256'] and
        value['executionContextSha256'] == pin['executionContextSha256'] and
        value['planSha256'] == pin['planSha256'] and value['sourceOnly'] is True and
        value['businessEvidenceAuthority'] is False and value['originalAppExecuted'] is False and
        value['originalSpecificationsAuthorized'] is False and value['evaluationExpectationsAuthorized'] is False and
        value['newSourceReadPermissions'] is False, 'Execution metadata run/project/capsule/context/plan boundary differs')

def metadata_documents(entries, plan, *, targets=False):
    definitions = {item['id']: item for item in plan['documents']}
    ids = [item['documentId'] for item in entries]
    require(ids and len(ids) == len(set(ids)) and set(ids) <= set(definitions), 'Metadata contains duplicate or unknown document IDs')
    for item in entries:
        original = definitions[item['documentId']]
        require(item['kind'] == original['kind'] and item['path'] == original['path'], 'Metadata document kind/path differs from the exact plan')
        if targets:
            require(item['kind'] in {'index', 'analysis-report'}, 'Supplemental context is reserved for index and analysis-report documents')
    return ids

def metadata_relative_path(value):
    from pathlib import PurePosixPath
    require(isinstance(value, str) and value and not any(c in value for c in '\\:\r\n\x00?#%'), 'Invalid metadata routing path')
    path = PurePosixPath(value)
    require(not path.is_absolute() and '..' not in path.parts and '.' not in path.parts and
        path.as_posix() == value and all(part for part in value.split('/')), 'Routing paths must be normalized relative paths')
    return path

def with_execution_metadata(pin, plan, path, expected_sha):
    require('executionMetadata' not in pin, 'Supplement binding requires the original base input')
    path = metadata_record_path(path)
    expected_sha = hash_arg(expected_sha)
    require(sha(path) == expected_sha, 'Supplement JSON bytes changed')
    supplement = load(path)
    metadata_schema('supplement', supplement)
    metadata_identity(supplement, pin)
    ids = metadata_documents(supplement['documents'], plan, targets=True)
    pins = {str(path): expected_sha, **{str(safe(p)): expected for p, expected in METADATA_SCHEMAS.values()}}
    referenced, seen, referenced_ids = [], set(), set()
    for reference in supplement['records']:
        record_path = metadata_record_path(reference['path'])
        require(str(record_path) not in seen and record_path != path, 'Duplicate or cyclic supplemental record reference')
        seen.add(str(record_path))
        require(sha(record_path) == hash_arg(reference['sha256']), 'Routing/completion record bytes changed')
        record = load(record_path)
        metadata_schema(reference['kind'], record)
        metadata_identity(record, pin)
        referenced_ids.update(metadata_documents(record['documents'], plan))
        for item in record['documents']:
            if reference['kind'] == 'routing':
                is_report = item['kind'] == 'analysis-report'
                require(item['disposition'] == ('report-only' if is_report else 'specification'), 'Routing report/specification disposition differs')
                locations = set()
                for location in item['locations']:
                    relative = metadata_relative_path(location['relativePath'])
                    require(location['scope'] == ('execution-report' if is_report else 'specification-bundle'),
                        'Analysis reports must remain outside the final specification bundle')
                    require(relative.suffix == '.' + location['format'], 'Routing filename extension differs from declared format')
                    key = (location['scope'], location['format'], location['relativePath'])
                    require(key not in locations, 'Duplicate metadata routing location')
                    locations.add(key)
            else:
                evidence_seen = set()
                require(item['recordStatus'] != 'RECORDED' or bool(item['evidence']), 'Recorded execution state needs pinned evidence')
                for evidence in item['evidence']:
                    evidence_path = metadata_evidence_path(evidence['path'])
                    require(str(evidence_path) not in evidence_seen and evidence_path != path and
                        evidence_path != record_path, 'Duplicate or self-referencing completion evidence')
                    evidence_seen.add(str(evidence_path))
                    require(sha(evidence_path) == hash_arg(evidence['sha256']), 'Completion evidence JSON bytes changed')
                    require(str(evidence_path) not in pins or pins[str(evidence_path)] == evidence['sha256'], 'Completion evidence conflicts with an existing pin')
                    pins[str(evidence_path)] = evidence['sha256']
        pins[str(record_path)] = reference['sha256']
        referenced.append({'reference': reference, 'record': record})
    require(set(ids) <= referenced_ids, 'Each supplemental target needs a routing or completion record entry')
    supplemental_context = {'schema': 'spec-agent-author-same-run-metadata-context/1',
        'policy': METADATA_POLICY, 'supplement': supplement, 'referencedRecords': referenced}
    context_sha = digest(json.dumps(supplemental_context, ensure_ascii=False, sort_keys=True).encode('utf-8'))
    result = dict(pin)
    result['pinnedFiles'] = dict(pin['pinnedFiles'])
    for filename, expected in pins.items():
        require(filename not in result['pinnedFiles'] or result['pinnedFiles'][filename] == expected, 'Supplement conflicts with an original input pin')
        require(sha(filename) == expected, 'Supplement or reference drift during binding')
        result['pinnedFiles'][filename] = expected
    result['executionMetadata'] = {'schema': 'spec-agent-author-execution-metadata-binding/1',
        'supplement': {'path': str(path), 'sha256': expected_sha}, 'contextSha256': context_sha,
        'documentIds': ids, 'pinnedFiles': pins, 'context': supplemental_context,
        'businessEvidenceAuthority': False, 'newSourceReadPermissions': False,
        'originalAppExecuted': False,
        'verificationBoundaries': ['composite-generation-before-after', 'scoped-review-before-after', 'final-text-pin', 'wave-completion'],
        'internalAnalysisDraftCallbackChecksPerformed': False, 'atomicOrRaceFreeProof': False}
    return result

def metadata_selection(pin, plan, selected):
    expected = pin['executionMetadata']['documentIds']
    require(len(selected) == len(set(selected)) and set(selected) == set(expected), 'Supplement document IDs must equal the prepared reserved-document wave')
    chosen = [item for item in plan['documents'] if item['id'] in selected]
    require(all(item['kind'] in {'index', 'analysis-report'} for item in chosen), 'Supplement cannot enter business specification authors')

def metadata_provenance(pin):
    metadata = pin['executionMetadata']
    return {key: value for key, value in metadata.items() if key != 'context'}

def metadata_revision_context(revision_context, original_context, pin):
    if revision_context == original_context:
        result = {'executionContext': original_context}
    else:
        require(isinstance(revision_context, dict) and revision_context.get('executionContext') == original_context,
            'Supplement cannot replace or modify the complete original execution context')
        result = dict(revision_context)
    require('sameRunExecutionMetadata' not in result, 'A supplemental context cannot overwrite an existing revision member')
    result['sameRunExecutionMetadata'] = pin['executionMetadata']['context']
    return result

def previous_execution_metadata(result, generation, definition, pin):
    if 'executionMetadata' not in result:
        return None
    base = {key: value for key, value in pin.items() if key != 'executionMetadata'}
    if 'executionMetadata' in pin:
        excluded = pin['executionMetadata']['pinnedFiles']
        base['pinnedFiles'] = {key: value for key, value in pin['pinnedFiles'].items() if key not in excluded}
    prior = result['executionMetadata']
    previous = with_execution_metadata(base, load(pin['plan']), prior['supplement']['path'], prior['supplement']['sha256'])
    require(metadata_provenance(previous) == prior and definition['id'] in previous['executionMetadata']['documentIds'] and
        definition['kind'] in {'index', 'analysis-report'}, 'Previous supplemental provenance differs')
    wave_before = safe(generation.parent / 'author-inputs-before.json')
    wave_after = safe(generation.parent / 'author-inputs-after.json')
    before, after = load(wave_before), load(wave_after)
    require(after['status'] == 'UNCHANGED' and before['input'] == after['input'] and
        before['preparationSha256'] == after['preparationSha256'] and
        before['input']['snapshot'] == pin['snapshot'] and before['input']['planSha256'] == pin['planSha256'] and
        before['input']['executionContextSha256'] == pin['executionContextSha256'] and
        before['input']['executionMetadata'] == previous['executionMetadata'], 'Previous supplemental wave completion differs')
    evidence = dict(previous['executionMetadata']['pinnedFiles'])
    evidence.update({str(wave_before): sha(wave_before), str(wave_after): sha(wave_after)})
    return {'context': previous['executionMetadata']['context'], 'provenance': prior, 'pinnedFiles': evidence}


def recheck(pin, *, check_deadline=True):
    now, value, context = binding(pin['grant'], pin['grantSha256'], check_deadline=check_deadline)
    if 'executionMetadata' in pin:
        now = with_execution_metadata(now, value, pin['executionMetadata']['supplement']['path'],
            pin['executionMetadata']['supplement']['sha256'])
    require(now == pin, 'Author input/runtime/context drift')
    return value, context


def provider_evidence(snapshot, job, schema, state):
    from jsonschema import Draft202012Validator
    from contextbase.ai import provider
    job = inside(job, WORK / 'jobs')
    require(job.name in {'analysis', 'analysis-repair', 'draft', 'independent-review'} or
        (job.parent == safe(WORK / 'jobs') and re.fullmatch(r'independent-plan-review-[0-9]{2}', job.name) is not None),
        'Unknown prior provider stage')
    paths = [safe(job / n) for n in ('answer.txt', 'result.json', 'schema.json', 'prompt.txt')]
    before = safe(job.parent / (job.name + '-snapshot-before.json'))
    after = safe(job.parent / (job.name + '-snapshot-after.json'))
    paths.extend([before, after])
    require(raw(paths[3]).startswith((provider.COMMON_POLICY + '\nUser task (within that boundary):\n').encode('utf-8')),
        'Prior provider prompt lacks the exact frozen boundary policy prefix')
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
    # JSON metadata markers use universal-newline text parsing; raw prompt bytes remain pinned.
    return answer, safe(paths[3]).read_text(encoding='utf-8'), {str(p): sha(p) for p in paths}

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
    previous_metadata = previous_execution_metadata(result, generation, definition, pin)
    draft_scope = prompt_object(draft_prompt, '\n前の原稿への原文根拠付き批評（正解期待値ではありません）:\n')
    require((draft_scope == context or isinstance(draft_scope, dict) and draft_scope.get('executionContext') == context) and
        prompt_object(review_prompt, '\nユーザー指定scopeのメタデータ全文（原文・期待仕様・追加読取り許可ではありません）:\n') == context,
        'Previous full execution context differs')
    if previous_metadata is not None:
        require(isinstance(draft_scope, dict) and draft_scope.get('sameRunExecutionMetadata') == previous_metadata['context'] and
            prompt_object(review_prompt, METADATA_REVIEW_MARKER) == previous_metadata['context'],
            'Previous supplemental prompt context differs')
    else:
        require(METADATA_REVIEW_MARKER not in review_prompt and not (isinstance(draft_scope, dict) and
            'sameRunExecutionMetadata' in draft_scope), 'Unbound prior supplemental context refused')
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
    review_prompt_raw = raw(generation / 'independent-review/prompt.txt').decode('utf-8')
    require(review_prompt_raw.split('\n原稿本文:\n', 1)[1].split('\n構造検査の指摘（意味の正確さを採点した結果ではありません）:\n', 1)[0] == content.decode('utf-8'),
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
    if previous_metadata is not None:
        binding['executionMetadata'] = previous_metadata['provenance']
        binding['pinnedFiles'].update(previous_metadata['pinnedFiles'])
    if previous_metadata is not None or 'executionMetadata' in pin:
        revision['preservedPreviousExecutionMetadata'] = previous_metadata['context'] if previous_metadata is not None else None
        revision['preservedIndependentReviewRawResponse'] = raw(generation / 'independent-review/answer.txt').decode('utf-8')
    return binding, revision

def recheck_previous(previous, definition, pin, context):
    now, revision = previous_revision(previous['sourceResult'], previous['sourceResultSha256'], definition, pin, context)
    require(now == previous, 'Previous revision input artifacts drift')
    return revision

def prepare(activation, activation_sha, wave, document_ids, workers, timeout, revisions=None, execution_metadata=None, execution_metadata_sha=None):
    require(isinstance(wave, str) and re.fullmatch(r'author-wave-[0-9]{2}', wave) is not None, 'Invalid fresh wave name')
    require(type(workers) is int and 1 <= workers <= 4 and type(timeout) is int and 1 <= timeout <= 2400,
        'Invalid bounded worker/timeout values')
    pin, plan, context = binding(activation, hash_arg(activation_sha))
    available = {d['id'] for d in plan['documents']}
    selected = list(document_ids) if document_ids else sorted(available)
    require(selected and len(selected) == len(set(selected)) and set(selected) <= available, 'Invalid document wave subset')
    require((execution_metadata is None) == (execution_metadata_sha is None), 'Supplement path and SHA must be paired')
    if execution_metadata is not None:
        pin = with_execution_metadata(pin, plan, execution_metadata, hash_arg(execution_metadata_sha))
        metadata_selection(pin, plan, selected)
    from contextbase.ai import workflow
    previous = {}
    for path, expected_sha in revisions or []:
        identity = load(inside(path, WORK / 'jobs'))['documentId']
        require(identity in selected and identity not in previous, 'Revision must map uniquely to selected document')
        definition = workflow.select_document(Path(pin['plan']), identity)
        previous[identity], _ = previous_revision(path, hash_arg(expected_sha), definition, pin, context)
    paths = {'jobs': str(safe(WORK / 'jobs' / wave)), 'drafts': str(safe(WORK / 'drafts' / wave)),
        'preparation': str(safe(REPORT / 'author-preparation' / wave))}
    require(not any(safe(path).exists() for path in paths.values()), 'Use new preparation/job/draft paths')
    recheck(pin)
    record = {'schema': 'spec-agent-author-wave-preparation/1', 'createdAt': datetime.now(timezone.utc).isoformat(),
        'agentRole': 'AG-SPEC', 'projectId': 'nenkin', 'mode': 'source-only', 'wave': wave,
        'documents': selected, 'workers': workers, 'timeout': timeout, 'deadline': DEADLINE,
        'revisions': previous, 'analysisReuseAuthorized': False,
        'paths': paths, 'input': pin, 'helper': str(safe(__file__)), 'helperSha256': sha(__file__),
        'providerStarted': False, 'frozenCoreOrLoadedPromptModified': False, 'businessProseAssembledByPython': False}
    target = safe(Path(paths['preparation']) / 'preparation.json')
    write(target, record)
    return {'preparation': str(target), 'sha256': sha(target), 'providerStarted': False}

def scoped_review(definition, document, job, timeout, pin, context):
    from contextbase.ai import capsule, workflow, prompts, schemas
    from contextbase.ai.validation import validate_document
    recheck(pin)
    snapshot = safe(pin['snapshotRoot'])
    state = workflow._definition_state(snapshot, definition)
    manifest = capsule.verify(snapshot)
    document = safe(document)
    document_bytes, document_sha = raw(document), sha(document)
    findings = validate_document(document_bytes.decode('utf-8'), definition['path'],
        expected_document_id=definition['id'], expected_kind=definition['kind'])
    prompt = (prompts.REVIEW + workflow._document_context(snapshot, definition) +
        '\nユーザー指定scopeのメタデータ全文（原文・期待仕様・追加読取り許可ではありません）:\n' +
        json.dumps(context, ensure_ascii=False, indent=2) + '\n原稿本文:\n' + document_bytes.decode('utf-8') +
        '\n構造検査の指摘（意味の正確さを採点した結果ではありません）:\n' + json.dumps(findings, ensure_ascii=False))
    if 'executionMetadata' in pin:
        marker = '\n原稿本文:\n'
        prefix, suffix = prompt.split(marker, 1)
        prompt = prefix + METADATA_REVIEW_MARKER + json.dumps(pin['executionMetadata']['context'], ensure_ascii=False, indent=2) + marker + suffix
    answer = workflow._bound_job(snapshot, job, prompt, schemas.REVIEW, timeout, state, DEADLINE)
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
    handoff_value = {'schema': 'reverse-ai-review-handoff/1', 'snapshot': state,
        'documentFile': str(document), 'documentSha256': document_sha, 'reviewSha256': sha(verified),
        'referenceMode': 'source-only', 'approved': answer['approved'], 'reviewScope': 'text-source-and-structure',
        'visualFidelityVerified': False, 'formallyEvaluatedByOriginalRubric': False,
        'unassessedScopes': ['visual-fidelity', 'application-runtime', 'formal-semantic-scoring'],
        'executionContextSha256': pin['executionContextSha256'], 'aiResponseBytesModified': False}
    if 'executionMetadata' in pin:
        handoff_value['executionMetadata'] = metadata_provenance(pin)
    write(job / 'review-handoff.json', handoff_value)
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
        'sourcePathsRead': analysis['sourcePathsRead'], 'executionContextSha256': pin['executionContextSha256'],
        'planSha256': pin['planSha256'], 'activationGrantSha256': pin['grantSha256'],
        'disposition': 'report-only' if definition['kind'] == 'analysis-report' else 'specification',
        'includedInFinalSpecificationBundle': definition['kind'] != 'analysis-report',
        'reviewScope': 'text-source-and-structure', 'visualFidelityVerified': False,
        'formalScoringVerified': False, 'published': False, 'originalApplicationOrDatabaseExecuted': False,
        'businessProseAssembledByPython': False,
        'waveIntegrityVerificationRequiredForCollection': True,
        'waveVerification': {'before': str(safe(generation.parent / 'author-inputs-before.json')),
            'beforeSha256': sha(generation.parent / 'author-inputs-before.json'),
            'after': str(safe(generation.parent / 'author-inputs-after.json')),
            'result': str(safe(generation.parent / 'author-wave-result.json'))},
        'finalSpecificationBundleApproved': False}
    if 'executionMetadata' in pin:
        result['executionMetadata'] = metadata_provenance(pin)
    recheck(pin)
    check_schema('text-pin', result)
    job_target = safe(generation / 'text-reviewed-pin.json')
    target = inside(REPORT / 'text-pins' / generation.relative_to(safe(WORK / 'jobs')) / 'text-reviewed-pin.json', REPORT / 'text-pins')
    write(job_target, result)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(raw(job_target))
    require(raw(target) == raw(job_target), 'Report text pin differs from job metadata bytes')
    return {'path': str(target), 'sha256': sha(target), 'jobPin': str(job_target),
        'jobPinSha256': sha(job_target), 'disposition': result['disposition']}

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
    if 'executionMetadata' in pin:
        metadata_selection(pin, plan, selected)
    previous = record['revisions']
    require(isinstance(previous, dict) and set(previous) <= set(selected) and record['analysisReuseAuthorized'] is False, 'Prepared revision subset differs')
    for key, old in previous.items():
        recheck_previous(old, definitions[key], pin, context)
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
            revision_context = context
            if identity in previous:
                revision_context = recheck_previous(previous[identity], definition, pin, context)
                write(job_root / (folder + '-revision-input-pins.json'), previous[identity])
            if 'executionMetadata' in pin:
                revision_context = metadata_revision_context(revision_context, context, pin)
            # Full preserved current-run Markdown/review and scope are passed without alteration.
            # No analysis_job is supplied: this first revision interface always performs fresh analysis.
            draft = workflow.document(Path(pin['snapshotRoot']), definition, generation, output, timeout=record['timeout'],
                deadline=DEADLINE, revision_context=revision_context)
            recheck(pin)
            require(sha(preparation) == preparation_sha, 'Preparation drift during generation')
            if identity in previous:
                recheck_previous(previous[identity], definition, pin, context)
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
            structure_conflict = False
            try:
                review = scoped_review(definition, document, generation / 'independent-review', record['timeout'], pin, context)
            except workflow.ReviewStructureConflict:
                # Preserve the original refused review; it is revision evidence, never approval.
                recheck(pin)
                review = load(generation / 'independent-review/answer.txt')
                structure_conflict = True
            require(sha(preparation) == preparation_sha, 'Preparation drift during review')
            if identity in previous:
                recheck_previous(previous[identity], definition, pin, context)
            review_file = safe(generation / 'independent-review' / ('answer.txt' if structure_conflict else 'review-verified.json'))
            accepted = not structure_conflict and review['approved'] is True and not review['findings'] and not review['unresolved'] and not draft['structureFindings']
            result = {'schema': 'spec-agent-author-document-result/1', 'documentId': identity, 'path': definition['path'], 'kind': definition['kind'],
                'capsule': pin['snapshot'], 'planSha256': pin['planSha256'],
                'executionContextSha256': pin['executionContextSha256'], 'runtimeReceiptSha256': RECEIPT_SHA,
                'revisionFrom': previous.get(identity), 'analysisFresh': True,
                'status': 'TEXT_REVIEW_APPROVED' if accepted else 'REQUIRES_AI_REVISION', 'draft': saved,
                'review': {'path': str(review_file), 'sha256': sha(review_file), 'approved': review['approved'],
                    'verified': not structure_conflict, 'structureApprovalConflict': structure_conflict},
                'visualFidelityVerified': False, 'formalScoringVerified': False, 'published': False}
            if 'executionMetadata' in pin:
                result['executionMetadata'] = metadata_provenance(pin)
            if accepted:
                result['textPin'] = text_pin(definition, generation, document, draft, review, pin, output)
            recheck(pin)
            require(sha(preparation) == preparation_sha, 'Preparation drift before document result')
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
        finally:
            if identity in previous:
                recheck_previous(previous[identity], definition, pin, context)

    results = []
    try:
        with ThreadPoolExecutor(max_workers=record['workers']) as executor:
            futures = {executor.submit(task, identity): identity for identity in selected}
            for future in as_completed(futures):
                results.append(future.result())
        recheck(pin, check_deadline=False)
        require(sha(preparation) == preparation_sha, 'Preparation changed before wave completion')
        for key, old in previous.items():
            recheck_previous(old, definitions[key], pin, context)
        write(job_root / 'author-inputs-after.json', {'status': 'UNCHANGED', 'preparationSha256': preparation_sha, 'input': pin})
    except Exception as exc:
        write(job_root / 'author-inputs-after.json', {'status': 'NOT_VERIFIED', 'errorType': type(exc).__name__,
            'error': str(exc), 'preparationSha256': preparation_sha})
        raise
    complete = len(results) == len(selected) and all(x['status'] == 'TEXT_REVIEW_APPROVED' for x in results)
    summary = {'schema': 'spec-agent-author-wave-result/1', 'createdAt': datetime.now(timezone.utc).isoformat(),
        'status': 'TEXT_REVIEW_APPROVED' if complete else 'INCOMPLETE', 'agentRole': 'AG-SPEC',
        'mode': 'source-only', 'capsule': pin['snapshot'], 'seconds': round(time.monotonic() - started, 3),
        'preparation': str(preparation), 'preparationSha256': preparation_sha, 'input': pin,
        'waveIntegrityVerified': True, 'inputsAfter': str(safe(job_root / 'author-inputs-after.json')),
        'inputsAfterSha256': sha(job_root / 'author-inputs-after.json'),
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
    pre.add_argument('--revision-from', nargs=2, action='append', default=[], metavar=('AUTHOR_RESULT', 'SHA256'))
    pre.add_argument('--execution-metadata')
    pre.add_argument('--execution-metadata-sha256')
    exe = subs.add_parser('run')
    exe.add_argument('--preparation', required=True)
    exe.add_argument('--preparation-sha256', required=True)
    args = parser.parse_args()
    value = prepare(args.activation, args.activation_sha256, args.wave, args.document_id, args.workers, args.timeout, args.revision_from, args.execution_metadata, args.execution_metadata_sha256) \
        if args.command == 'prepare' else run(args.preparation, args.preparation_sha256)
    print(json.dumps(value, ensure_ascii=False))

if __name__ == '__main__':
    main()
