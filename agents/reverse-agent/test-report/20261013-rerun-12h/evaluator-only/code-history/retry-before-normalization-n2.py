"""Retry failed inference jobs in a fresh capsule, preserving every prior byte."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
import grader


def copy_checked(source: Path, destination: Path):
    if source.is_symlink():
        raise ValueError('Retry evidence must not be linked')
    before = grader.digest(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    if grader.digest(source) != before or grader.digest(destination) != before:
        raise ValueError('Retry byte copy drift')
    return before


def prepare_retry(source: Path, destination: Path):
    seal, capsule = grader.check_capsule(source)
    if destination.exists():
        raise ValueError('Retry requires a fresh batch directory')
    states = []
    for job in seal['jobs']:
        target = source / 'jobs' / job['shardId']
        result_path = target / 'result.json'
        if not result_path.is_file():
            raise ValueError('Wait for every original job to finish before retry preparation')
        result = grader.load(result_path)
        if result.get('status') == 'RUNNING':
            raise ValueError('Original inference is still running')
        if result.get('status') == 'PASSED':
            if grader.digest(target / 'answer.txt') != result['answerSha256']:
                raise ValueError('Accepted answer drift before reuse')
            grader.validate_answer(grader.load(target / 'answer.txt'),
                grader.load(capsule / job['requestPath']), capsule)
        states.append((job, result))
    if all(result.get('status') == 'PASSED' for _, result in states):
        raise ValueError('No failed inference requires a retry')
    destination.mkdir(parents=True)
    copied = {}
    for name in ('batch.json', 'answer-schema.json', 'canonical-pin.json'):
        copied[name] = copy_checked(source / name, destination / name)
    for path in sorted(capsule.rglob('*')):
        if path.is_file():
            relative = path.relative_to(source)
            copied[relative.as_posix()] = copy_checked(path, destination / relative)
    reused, retried = [], []
    for job, result in states:
        if result.get('status') != 'PASSED':
            retried.append({'shardId': job['shardId'], 'previousStatus': result.get('status'),
                            'previousResultSha256': grader.digest(source / 'jobs' / job['shardId'] / 'result.json')})
            continue
        target = source / 'jobs' / job['shardId']
        for path in sorted(target.rglob('*')):
            if path.is_file():
                relative = path.relative_to(source)
                copied[relative.as_posix()] = copy_checked(path, destination / relative)
        reused.append({'shardId': job['shardId'], 'answerSha256': result['answerSha256']})
    grader.check_capsule(source)
    grader.check_capsule(destination)
    grader.save(destination / 'retry-provenance.json', {
        'schema': 'independent-evaluation-immutable-retry/1',
        'createdAt': datetime.now(timezone.utc).isoformat(), 'sourceBatch': str(source.resolve()),
        'sourceBatchManifestSha256': grader.digest(source / 'batch.json'),
        'reusedAcceptedJobs': reused, 'retryJobs': retried, 'copiedFileHashes': copied,
        'originalBatchModified': False, 'answerContentRewritten': False,
        'rubricOrCanonicalChanged': False,
    })
    return {'reused': len(reused), 'retryJobs': len(retried)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--deadline', required=True)
    args = parser.parse_args()
    user_deadline = grader.load(grader.HERE.parent / 'run-manifest.json')['deadline']
    if grader.remaining(args.deadline) <= 0 or datetime.fromisoformat(args.deadline.replace('Z', '+00:00')) > datetime.fromisoformat(user_deadline.replace('Z', '+00:00')):
        raise ValueError('Retry must stay within the user deadline')
    import json
    print(json.dumps(prepare_retry(grader.safe(args.source, grader.HERE / 'batches'),
                                  grader.safe(args.destination, grader.HERE / 'batches'))))


if __name__ == '__main__':
    main()
