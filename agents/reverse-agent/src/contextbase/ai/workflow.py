"""Artifact orchestration; analysis, prose and review are authored by the AI."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from . import capsule, prompts, schemas
from .provider import run_job


def relative_path(value: str) -> str:
    from .validation import _canonical_document_path
    if not isinstance(value, str) or not _canonical_document_path(value):
        raise ValueError('Unsafe or noncanonical Markdown output path: ' + str(value))
    path = PurePosixPath(value)
    if not value or '\\' in value or ':' in value or path.is_absolute() or '..' in path.parts or '.' in path.parts:
        raise ValueError('Noncanonical output path: ' + value)
    if str(path) != value or path.suffix.lower() != '.md':
        raise ValueError('Relative Markdown output path required: ' + value)
    if any(part.endswith((' ', '.')) for part in path.parts):
        raise ValueError('Unsafe Windows output path: ' + value)
    return value


def require_answer(result: dict) -> dict:
    metadata = result.get('metadata', {})
    if result.get('exit_code') != 0 or metadata.get('status') != 'passed':
        raise RuntimeError('AI job did not succeed; see provider job artifacts')
    if not isinstance(result.get('answer'), dict):
        raise ValueError('A structured AI answer is required')
    return result['answer']


def _materials(manifest: dict) -> dict:
    entries = {}
    def add(alias, original, kind, entry):
        value = {'original': original, 'kind': kind, 'entry': entry}
        if alias in entries and entries[alias] != value:
            raise ValueError('Ambiguous snapshot material alias: ' + alias)
        entries[alias] = value
    for entry in manifest['files']:
        for alias in (entry['path'], 'sources/' + entry['path'], entry['indexed']):
            add(alias, entry['path'], 'source', entry)
    for entry in manifest.get('referenceFiles', []):
        add(entry['path'], entry['path'], 'design', entry)
    # Inventory is a planning/read material, never implementation evidence.
    if 'manifest.json' in entries:
        del entries['manifest.json']
    entries['manifest.json'] = {'original': 'manifest.json', 'kind': 'inventory', 'entry': None}
    return entries


def references_valid(answer: dict, manifest: dict) -> None:
    entries = _materials(manifest)
    references = []
    for fact in answer.get('facts', []):
        if not fact['references']:
            raise ValueError('Unsubstantiated fact must be unresolved: ' + fact['id'])
        kinds = [entries.get(ref['path'], {}).get('kind') for ref in fact['references']]
        if fact.get('basis') == 'observed-source' and not all(kind == 'source' for kind in kinds):
            raise ValueError('A reference design cannot establish observed implementation: ' + fact['id'])
        if fact.get('basis') == 'reference-design' and not any(kind == 'design' for kind in kinds):
            raise ValueError('A design-based fact must cite the authorized design: ' + fact['id'])
        if fact.get('basis') not in {'observed-source', 'reference-design'}:
            raise ValueError('Unknown fact basis')
        references.extend(fact['references'])
    for finding in answer.get('findings', []):
        references.extend(finding['references'])
    for ref in references:
        material = entries.get(ref['path'], {})
        entry = material.get('entry')
        if (entry is None or type(ref['startLine']) is not int or type(ref['endLine']) is not int or
                not (1 <= ref['startLine'] <= ref['endLine'] <= entry['lines'])):
            raise ValueError('Invalid evidence location: ' + str(ref))
    for name in answer.get('sourcePathsRead', []):
        if name not in entries:
            raise ValueError('Non-snapshot source claimed as read: ' + name)


def _validate_plan(answer: dict, manifest: dict) -> None:
    from jsonschema import Draft202012Validator, ValidationError
    try:
        Draft202012Validator(schemas.PLAN).validate(answer)
    except ValidationError as exc:
        raise ValueError('Invalid AI plan schema') from exc
    entries = _materials(manifest)
    ids, paths = set(), set()
    for document in answer['documents']:
        name = relative_path(document['path'])
        if document['id'] in ids or name.casefold() in paths:
            raise ValueError('Duplicate document identity or path')
        ids.add(document['id']); paths.add(name.casefold())
        if not document['sourcePaths'] or not set(document['sourcePaths']) <= set(entries):
            raise ValueError('Document plan uses unknown or empty source paths')
    if not answer['documents']:
        raise ValueError('No documents planned')


def _same_snapshot(snapshot: Path, expected: dict) -> dict:
    current = capsule.verification_state(snapshot)
    if current != expected:
        raise ValueError('Snapshot generation changed during/between AI phases')
    return current


def _timeout(timeout, deadline):
    if deadline is None:
        return timeout
    if isinstance(deadline, str):
        deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
    if not isinstance(deadline, datetime) or deadline.tzinfo is None:
        raise ValueError('An absolute timezone-aware deadline is required')
    remaining = (deadline - datetime.now(timezone.utc)).total_seconds()
    if remaining <= 30:
        raise RuntimeError('RuntimeErrorTimeLimit: less than 30 seconds remain')
    return min(timeout, remaining - 30)


def _bound_job(snapshot, job, prompt, schema, timeout, state, deadline=None):
    _same_snapshot(snapshot, state)
    allowance = _timeout(timeout, deadline)
    job = capsule.safe_path(job)
    before_file = job.parent / (job.name + '-snapshot-before.json')
    capsule.write_json(before_file, state)
    result = run_job(snapshot, job, prompt, schema, allowance)
    try:
        current = _same_snapshot(snapshot, state)
    except (OSError, ValueError) as exc:
        capsule.write_json(job.parent / (job.name + '-snapshot-after.json'),
                           {'status': 'INPUT_CHANGED', 'error': str(exc), 'before': state})
        raise
    capsule.write_json(job.parent / (job.name + '-snapshot-after.json'),
                       {'status': 'UNCHANGED', 'before': state, 'after': current})
    return require_answer(result)


def _handoff(plan_file, state, origin):
    capsule.write_json(plan_file.parent / 'plan-handoff.json', {
        'schema': 'reverse-ai-plan-handoff/1', 'snapshot': state,
        'planFile': plan_file.name, 'planSha256': capsule.sha256(plan_file.read_bytes()),
        'origin': origin,
    })


def plan(snapshot: Path, job: Path, *, timeout=1800, deadline=None, revision_context=None) -> dict:
    state = capsule.verification_state(snapshot)
    manifest = capsule.verify(snapshot)
    context = ''
    if revision_context is not None:
        context = '\n以前のAI文書計画と改善指摘:\n' + json.dumps(revision_context, ensure_ascii=False, indent=2)
    answer = _bound_job(snapshot, job, prompts.PLAN + context, schemas.PLAN, timeout, state, deadline)
    _validate_plan(answer, manifest)
    capsule.write_json(job / 'plan-verified.json', answer)
    _handoff(job / 'plan-verified.json', state, 'same-job-before-after-snapshot-verified')
    return answer


def bind_existing_plan(snapshot: Path, plan_file: Path, expected_manifest_sha256: str, *,
                       binding_scope='current-verified-capsule-correspondence-only') -> dict:
    """Recover a legacy job with explicitly stated provenance scope.

    The AI response and live capsule are never edited. The handoff records
    that binding happened later rather than claiming a new model execution.
    """
    state = capsule.verification_state(snapshot)
    if binding_scope not in {'current-verified-capsule-correspondence-only',
                             'independently-recorded-starting-manifest-hash'}:
        raise ValueError('Unknown legacy plan binding scope')
    if not isinstance(expected_manifest_sha256, str) or state['manifestSha256'] != expected_manifest_sha256.lower():
        raise ValueError('Legacy plan starting manifest hash does not match')
    plan_file = capsule.safe_path(plan_file)
    answer = capsule._load_json(plan_file)
    _validate_plan(answer, capsule.verify(snapshot))
    verified = plan_file.parent / 'plan-verified.json'
    if plan_file != verified:
        with verified.open('xb') as handle:
            handle.write(plan_file.read_bytes())
    _same_snapshot(snapshot, state)
    _handoff(verified, state, 'legacy-job-bind:' + binding_scope)
    return {'planFile': str(verified), 'handoffFile': str(verified.parent / 'plan-handoff.json'),
            'snapshot': state, 'bindingScope': binding_scope, 'aiResponseBytesModified': False}


class PlannedDocument(dict):
    """Keep transport provenance outside the unchanged AI document definition."""
    def __init__(self, definition, plan_file, handoff, handoff_sha):
        super().__init__(definition)
        self.plan_file = plan_file
        self.handoff = handoff
        self.handoff_sha = handoff_sha


class ReviewStructureConflict(ValueError):
    """A valid AI review cannot override a repairable structural defect."""
    def __init__(self, answer, findings):
        super().__init__('AI approval cannot override invalid document structure')
        self.answer = answer
        self.findings = findings


def select_document(plan_file: Path, document_id: str) -> dict:
    plan_file = capsule.safe_path(plan_file)
    plan_value = capsule._load_json(plan_file)
    handoff_file = capsule.safe_path(plan_file.parent / 'plan-handoff.json')
    if not handoff_file.is_file():
        raise ValueError('Unbound plan: bind its independently recorded starting snapshot hash first')
    handoff = capsule._load_json(handoff_file)
    if (handoff.get('schema') != 'reverse-ai-plan-handoff/1' or handoff.get('planFile') != plan_file.name or
            handoff.get('planSha256') != capsule.sha256(plan_file.read_bytes())):
        raise ValueError('Plan differs from its snapshot handoff')
    matches = [doc for doc in plan_value['documents'] if doc['id'] == document_id]
    if len(matches) != 1:
        raise ValueError('Unique planned document required: ' + document_id)
    return PlannedDocument(matches[0], plan_file, handoff, capsule.sha256(handoff_file.read_bytes()))


def _definition_state(snapshot, definition):
    if not isinstance(definition, PlannedDocument):
        raise ValueError('Document definition must come from a snapshot-bound plan')
    current = select_document(definition.plan_file, definition['id'])
    if (dict(current) != dict(definition) or current.handoff_sha != definition.handoff_sha):
        raise ValueError('Document plan changed between phases')
    state = definition.handoff['snapshot']
    _same_snapshot(snapshot, state)
    _validate_plan(capsule._load_json(definition.plan_file), capsule.verify(snapshot))
    return state


def document(snapshot: Path, definition: dict, job_root: Path, output: Path,
             *, timeout=1800, revision_context=None, deadline=None) -> dict:
    state = _definition_state(snapshot, definition)
    output = capsule.safe_path(output)
    planned_target = capsule.safe_path(output / relative_path(definition['path']))
    if output not in planned_target.parents:
        raise ValueError('Output escapes target root')
    if planned_target.exists():
        raise FileExistsError('Immutable document output already exists')
    manifest = capsule.verify(snapshot)
    context = '\n対象文書計画:\n' + json.dumps(definition, ensure_ascii=False, indent=2)
    if revision_context is not None:
        context += '\n前の原稿への原文根拠付き批評（正解期待値ではありません）:\n' + json.dumps(revision_context, ensure_ascii=False, indent=2)
    analysis = _bound_job(snapshot, job_root / 'analysis', prompts.ANALYZE + context,
                          schemas.ANALYSIS, timeout, state, deadline)
    if analysis['documentId'] != definition['id']:
        raise ValueError('Analysis document identity mismatch')
    try:
        references_valid(analysis, manifest)
    except ValueError as exc:
        # Preserve the original answer and ask the AI to correct its own evidence.
        # This retry handles generic validation, never application-specific answers.
        correction = {'validationError': str(exc), 'previousAiAnalysis': analysis}
        capsule.write_json(job_root / 'analysis-validation-failure.json', correction)
        repair_context = context + '\n根拠検査で受理されなかったAI解析を訂正してください:\n' + json.dumps(correction, ensure_ascii=False, indent=2)
        analysis = _bound_job(snapshot, job_root / 'analysis-repair', prompts.ANALYZE + repair_context,
                              schemas.ANALYSIS, timeout, state, deadline)
        if analysis['documentId'] != definition['id']:
            raise ValueError('Corrected analysis document identity mismatch')
        references_valid(analysis, manifest)
    capsule.write_json(job_root / 'analysis-verified.json', analysis)
    writer_context = context + '\nAIによる解析素材:\n' + json.dumps(analysis, ensure_ascii=False, indent=2)
    _definition_state(snapshot, definition)
    draft = _bound_job(snapshot, job_root / 'draft', prompts.WRITE + writer_context,
                       schemas.DRAFT, timeout, state, deadline)
    if draft['documentId'] != definition['id'] or draft['path'] != definition['path']:
        raise ValueError('Draft identity/path differs from approved source-derived plan')
    if not isinstance(draft['content'], str) or not draft['content'].strip():
        raise ValueError('AI returned an empty document draft')
    target = capsule.safe_path(output / relative_path(draft['path']))
    if output not in target.parents:
        raise ValueError('Output escapes target root')
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x', encoding='utf-8', newline='\n') as handle:
        handle.write(draft['content'])
    from .validation import validate_document
    structural_findings = validate_document(draft['content'], draft['path'])
    capsule.write_json(job_root / 'document-structure.json', {
        'documentId': definition['id'], 'contentSha256': capsule.sha256(draft['content'].encode('utf-8')),
        'status': 'STRUCTURE_INVALID' if structural_findings else 'STRUCTURE_VALID',
        'semanticFidelityVerified': False, 'findings': structural_findings,
    })
    # Original AI response and output content are preserved, including failures.
    result = {'documentId': definition['id'], 'path': draft['path'],
              'contentSha256': capsule.sha256(draft['content'].encode('utf-8')),
              'aiAuthored': True, 'semanticProseAssembledByPython': False,
              'analysisFacts': len(analysis['facts']), 'unresolved': draft['unresolved'],
              'snapshot': state, 'referenceMode': capsule.reference_mode(manifest),
              'structureFindings': structural_findings,
              'status': 'STRUCTURE_INVALID' if structural_findings else 'AI_DRAFT_NOT_YET_INDEPENDENTLY_REVIEWED'}
    _same_snapshot(snapshot, state)
    capsule.write_json(job_root / 'draft-result.json', result)
    return result


def review(snapshot: Path, document_file: Path, definition: dict, job: Path,
           *, timeout=1800, deadline=None) -> dict:
    state = _definition_state(snapshot, definition)
    manifest = capsule.verify(snapshot)
    context = '\n文書計画:\n' + json.dumps(definition, ensure_ascii=False)
    document_file = capsule.safe_path(document_file)
    document_bytes = document_file.read_bytes()
    if not document_bytes.strip():
        raise ValueError('An empty document cannot be reviewed as complete')
    document_sha = capsule.sha256(document_bytes)
    from .validation import validate_document
    structural_findings = validate_document(document_bytes.decode('utf-8'), definition['path'])
    context += '\n原稿本文:\n' + document_bytes.decode('utf-8')
    context += '\n構造検査の指摘（意味の正確さを採点した結果ではありません）:\n' + json.dumps(structural_findings, ensure_ascii=False)
    answer = _bound_job(snapshot, job, prompts.REVIEW + context, schemas.REVIEW, timeout, state, deadline)
    _definition_state(snapshot, definition)
    if capsule.sha256(document_file.read_bytes()) != document_sha:
        raise ValueError('Review input document changed during the AI job')
    if answer['documentId'] != definition['id']:
        raise ValueError('Review document identity mismatch')
    references_valid(answer, manifest)
    if answer['approved'] and (answer['unresolved'] or any(f['severity'] in {'critical', 'major'} for f in answer['findings'])):
        raise ValueError('AI review cannot approve unresolved or important findings')
    if answer['approved'] and structural_findings:
        capsule.write_json(job / 'structure-approval-conflict.json', {
            'status': 'AI_APPROVAL_REJECTED_STRUCTURE_INVALID',
            'findings': structural_findings, 'documentSha256': document_sha,
        })
        raise ReviewStructureConflict(answer, structural_findings)
    _same_snapshot(snapshot, state)
    capsule.write_json(job / 'review-verified.json', answer)
    capsule.write_json(job / 'review-handoff.json', {
        'schema': 'reverse-ai-review-handoff/1', 'snapshot': state,
        'documentFile': str(document_file), 'documentSha256': document_sha,
        'reviewSha256': capsule.sha256((job / 'review-verified.json').read_bytes()),
        'referenceMode': capsule.reference_mode(manifest), 'approved': answer['approved'],
    })
    return answer
