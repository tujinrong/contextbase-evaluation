"""Run planned AI document jobs; do not implement application-specific grading."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from . import capsule, workflow


def run(snapshot: Path, plan_file: Path, job_root: Path, output: Path,
        *, document_ids=None, workers=2, deadline=None, timeout=1800,
        independent_review=True):
    if type(workers) is not int or workers < 1 or workers > 4:
        raise ValueError('Between one and four workers required')
    job_root = capsule.safe_path(job_root)
    output = capsule.safe_path(output)
    if job_root.exists():
        raise ValueError('Use a new batch directory for each run')
    manifest = capsule.verify(snapshot)
    plan_value = capsule._load_json(capsule.safe_path(plan_file))
    workflow._validate_plan(plan_value, manifest)
    definition_list = plan_value['documents']
    available = {doc['id'] for doc in definition_list}
    analysis_reports = {doc['id'] for doc in definition_list if doc['kind'] == 'analysis-report'}
    chosen = available - analysis_reports if document_ids is None else set(document_ids)
    if not chosen <= available or not chosen:
        raise ValueError('Nonempty subset of source-derived document IDs required')
    if chosen & analysis_reports:
        raise ValueError('Analysis reports require a separate document job and report output root')
    stop = datetime.fromisoformat(deadline.replace('Z', '+00:00')) if deadline else None
    if stop is not None and stop.tzinfo is None:
        raise ValueError('An absolute timezone-aware deadline is required')
    definitions = {item: workflow.select_document(plan_file, item) for item in chosen}
    for definition in definitions.values():
        workflow._definition_state(snapshot, definition)
    job_root.mkdir(parents=True)
    started = time.monotonic()
    records = []

    def task(document_id):
        if stop:
            remaining = (stop - datetime.now(timezone.utc)).total_seconds()
            if remaining <= 60:
                return {'documentId': document_id, 'status': 'NOT_RUN_TIME_LIMIT'}
            job_timeout = min(timeout, int(remaining - 30))
        else:
            job_timeout = timeout
        definition = definitions[document_id]
        # Safe document IDs only select job folder names; output names come from the plan.
        folder = capsule.sha256(document_id.encode('utf-8'))[:16]
        directory = job_root / folder
        try:
            result = workflow.document(snapshot, definition, directory, output, timeout=job_timeout, deadline=deadline)
            if independent_review:
                review = workflow.review(snapshot, output / definition['path'], definition,
                                         directory / 'independent-review', timeout=job_timeout, deadline=deadline)
                result['independentReview'] = review
                result['status'] = 'INDEPENDENT_REVIEW_APPROVED' if review['approved'] else 'REQUIRES_AI_REVISION'
            return result
        except workflow.ReviewStructureConflict as exc:
            result['independentReview'] = exc.answer
            result['approvalAccepted'] = False
            result['status'] = 'REQUIRES_AI_REVISION'
            return result
        except Exception as exc:
            result = {'documentId': document_id, 'status': 'FAILED',
                      'errorType': type(exc).__name__, 'error': str(exc)}
            capsule.write_json(directory / 'batch-failure.json', result)
            return result

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(task, item): item for item in sorted(chosen)}
        for future in as_completed(futures):
            result = future.result()
            result['reviewScope'] = 'text-source-and-structure' if 'independentReview' in result else 'not-performed'
            result['visualFidelityVerified'] = False
            result['formallyEvaluatedByOriginalRubric'] = False
            records.append(result)
            # Persist each completed job immediately. A disconnected caller can
            # discover finished drafts without waiting for the whole batch.
            folder = capsule.sha256(result['documentId'].encode('utf-8'))[:16]
            capsule.write_json(job_root / 'progress' / (folder + '.json'), result)
            print(json.dumps({'documentId': result['documentId'], 'status': result['status']}, ensure_ascii=False), flush=True)
    capsule.verify(snapshot)
    result = {'schema': 'reverse-ai-batch/1', 'createdAt': datetime.now(timezone.utc).isoformat(),
              'seconds': round(time.monotonic() - started, 2), 'mode': manifest.get('mode', 'source-only'),
              'selected': len(chosen), 'planned': len(available),
              'notSelected': sorted(available - chosen), 'documents': records,
              'analysisReportsExcludedFromPublication': sorted(analysis_reports),
              'semanticAnalysisByAI': True, 'semanticProseAssembledByPython': False,
              'reviewScope': 'text-source-and-structure' if independent_review else 'not-performed',
              'visualFidelityVerified': False,
              'formallyEvaluatedByOriginalRubric': False,
              'status': 'REVIEWED' if all(r['status'] == 'INDEPENDENT_REVIEW_APPROVED' for r in records) else 'INCOMPLETE'}
    capsule.write_json(job_root / 'batch-result.json', result)
    return result
