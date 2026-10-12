"""Immutable AI drafting and critique rounds, without domain-specific scoring."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from . import capsule, workflow


def run(snapshot: Path, plan_file: Path, document_id: str, job_root: Path,
        output_root: Path, *, max_rounds=3, timeout=1800, deadline=None):
    if type(max_rounds) is not int or not 1 <= max_rounds <= 10:
        raise ValueError('Between one and ten critique rounds required')
    job_root = capsule.safe_path(job_root)
    output_root = capsule.safe_path(output_root)
    if job_root.exists() or output_root.exists():
        raise FileExistsError('Use new job and output roots for an iteration')
    definition = workflow.select_document(plan_file, document_id)
    state = workflow._definition_state(snapshot, definition)
    job_root.mkdir(parents=True)
    records = []
    revision = None
    selected = None
    status = 'REQUIRES_AI_REVISION'
    for number in range(1, max_rounds + 1):
        directory = job_root / f'round-{number:02d}'
        output = output_root / f'round-{number:02d}'
        try:
            # Recompute the remaining deadline for every phase in workflow.
            workflow._timeout(timeout, deadline)
            draft = workflow.document(snapshot, definition, directory, output,
                                      timeout=timeout, deadline=deadline, revision_context=revision)
            document_file = capsule.safe_path(output / definition['path'])
            document_bytes = document_file.read_bytes()
            if capsule.sha256(document_bytes) != draft['contentSha256']:
                raise ValueError('Draft differs from its original AI output')
            try:
                review = workflow.review(snapshot, document_file, definition,
                                         directory / 'independent-review', timeout=timeout, deadline=deadline)
                approval_accepted = review['approved'] and not draft['structureFindings']
            except workflow.ReviewStructureConflict as exc:
                review = exc.answer
                approval_accepted = False
            record = {'round': number, 'draft': draft, 'review': review,
                      'approvalAccepted': approval_accepted,
                      'documentFile': str(document_file)}
            records.append(record)
            if approval_accepted:
                selected = str(document_file)
                status = 'INDEPENDENT_REVIEW_APPROVED'
                break
            # Critique and the actual previous draft are data for a fresh AI job.
            # No Python code rewrites sentences or supplies expected business answers.
            revision = {'previousDraft': document_bytes.decode('utf-8'),
                        'previousDraftSha256': draft['contentSha256'],
                        'previousIndependentReview': review,
                        'structuralFindings': draft['structureFindings']}
            capsule.write_json(directory / 'next-round-context.json', revision)
        except Exception as exc:
            failure = {'round': number, 'status': 'FAILED', 'errorType': type(exc).__name__,
                       'error': str(exc)}
            capsule.write_json(directory / 'iteration-failure.json', failure)
            records.append(failure)
            status = 'NOT_RUN_TIME_LIMIT' if 'RuntimeErrorTimeLimit' in str(exc) else 'FAILED'
            break
    workflow._same_snapshot(snapshot, state)
    result = {'schema': 'reverse-ai-iteration/1', 'createdAt': datetime.now(timezone.utc).isoformat(),
              'documentId': document_id, 'snapshot': state,
              'referenceMode': capsule.reference_mode(capsule.verify(snapshot)),
              'status': status, 'selectedDocument': selected, 'rounds': records,
              'semanticProseAssembledByPython': False,
              'formallyEvaluatedByOriginalRubric': False}
    capsule.write_json(job_root / 'iteration-result.json', result)
    return result
