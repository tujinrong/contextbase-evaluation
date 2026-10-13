"""Bind old completed table analyses; display only artifact metadata, no AI jobs."""
from datetime import datetime, timezone
import json
from pathlib import Path

from contextbase.ai import capsule, workflow


def main():
    agent = Path(__file__).resolve().parents[3]
    pilot = agent / '.tmp/20261013-tuning-01/pilot-v3'
    plan = pilot / 'plan/plan-verified.json'
    capsule_root = capsule.safe_path(agent / '.tmp/20261013-tuning-01/capsules')
    records = []
    for job in sorted((pilot / 'physical-tables').iterdir()):
        if not job.is_dir():
            continue
        record = {'job': str(job.relative_to(agent))}
        snapshot = definition = None
        immutable = [job / 'analysis-verified.json']
        for directory in ('analysis', 'analysis-repair'):
            immutable.extend(job / directory / name for name in ('answer.txt', 'result.json', 'schema.json', 'prompt.txt'))
            immutable.extend(job / (directory + suffix) for suffix in ('-snapshot-before.json', '-snapshot-after.json'))
        before = {str(path.relative_to(job)): capsule.sha256(path.read_bytes()) for path in immutable if path.is_file()}
        try:
            # Parsing is internal to verification. Only identity and metadata
            # are recorded; business fact statements are never printed/copied.
            analysis = capsule._load_json(job / 'analysis-verified.json')
            document_id = analysis['documentId']
            record['documentId'] = document_id
            definition = workflow.select_document(plan, document_id)
            provider_result = capsule._load_json(job / 'analysis/result.json')
            snapshot = capsule.safe_path(Path(provider_result['metadata']['workspace']))
            if capsule_root not in snapshot.parents:
                raise ValueError('Legacy provider workspace is outside the authorized capsule root')
            record['snapshot'] = str(snapshot.relative_to(agent))
            if (job / 'analysis-handoff.json').exists():
                _, checkpoint, checkpoint_sha = workflow._resume_analysis(snapshot, definition, job)
                record['status'] = 'EXISTING_CHECKPOINT_VALIDATED'
            else:
                checkpoint = workflow.recover_analysis_checkpoint(snapshot, definition, job)
                checkpoint_sha = capsule.sha256((job / 'analysis-handoff.json').read_bytes())
                record['status'] = 'LEGACY_CHECKPOINT_RECOVERED'
            record.update(referenceMode=checkpoint['referenceMode'], origin=checkpoint['origin'],
                          checkpointSha256=checkpoint_sha, planBindingScope=checkpoint['planBindingScope'])
        except (OSError, ValueError, KeyError, TypeError) as exc:
            record.update(status='NOT_RECOVERED', errorType=type(exc).__name__, error=str(exc))
            evidence_errors = []
            if snapshot is not None and definition is not None:
                for directory in ('analysis-repair', 'analysis'):
                    if (job / directory).is_dir():
                        try:
                            workflow._analysis_pin(snapshot, definition, job, directory)
                        except (OSError, ValueError, KeyError, TypeError) as evidence_error:
                            evidence_errors.append({'providerDirectory': directory,
                                                    'errorType': type(evidence_error).__name__,
                                                    'error': str(evidence_error)})
            record['evidenceErrors'] = evidence_errors
        after = {str(path.relative_to(job)): capsule.sha256(path.read_bytes()) for path in immutable if path.is_file()}
        record['originalProviderArtifactsUnchanged'] = before == after
        record['originalArtifactHashes'] = before
        records.append(record)
        print(json.dumps({key: value for key, value in record.items()
                          if key not in {'originalArtifactHashes', 'evidenceErrors'}}, ensure_ascii=False), flush=True)
    result = {'schema': 'reverse-ai-legacy-analysis-recovery-test/1',
              'createdAt': datetime.now(timezone.utc).isoformat(), 'aiJobsStarted': 0,
              'scope': 'legacy physical-table analysis provenance only; no business semantic score',
              'selected': len(records),
              'recovered': sum(record['status'] == 'LEGACY_CHECKPOINT_RECOVERED' for record in records),
              'validatedExisting': sum(record['status'] == 'EXISTING_CHECKPOINT_VALIDATED' for record in records),
              'failed': sum(record['status'] == 'NOT_RECOVERED' for record in records),
              'originalArtifactsUnchanged': all(record['originalProviderArtifactsUnchanged'] for record in records),
              'records': records}
    destination = Path(__file__).with_name('legacy-recovery-results.json')
    with destination.open('x', encoding='utf-8') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2); handle.write('\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'records'}, ensure_ascii=False))
    return 0 if not result['failed'] and result['originalArtifactsUnchanged'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
