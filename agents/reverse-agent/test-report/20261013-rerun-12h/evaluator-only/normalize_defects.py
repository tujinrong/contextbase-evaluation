"""Separate AI review of defect identities after semantic shards are graded."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import subprocess
import sys
import grader

SCHEMA = grader.object_schema({'documentId': {'type': 'string'},
    'groups': {'type': 'array', 'items': grader.object_schema({'canonicalDefectId': {'type': 'string'},
        'evaluationIds': {'type': 'array', 'items': {'type': 'string'}}, 'reason': {'type': 'string'}})},
    'limitations': {'type': 'array', 'items': {'type': 'string'}}})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--deadline', required=True)
    parser.add_argument('--timeout-seconds', type=int, default=1800)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    batch = grader.safe(args.batch, grader.HERE)
    seal, capsule = grader.check_capsule(batch)
    items, _ = grader.rubric()
    indexed = {r['evaluationId']: dict(r, documentId=d['documentId']) for d in items['documents'] for r in d['rows']}
    answers, raw_hashes = {}, []
    for job in seal['jobs']:
        target = batch / 'jobs' / job['shardId']
        result = grader.load(target / 'result.json')
        if result['status'] != 'PASSED' or grader.digest(target / 'answer.txt') != result['answerSha256']:
            raise ValueError('Every shard must be accepted and unchanged before defect review')
        answer = grader.load(target / 'answer.txt')
        grader.validate_answer(answer, grader.load(capsule / job['requestPath']), capsule)
        raw_hashes.append({'shardId': job['shardId'], 'answerSha256': result['answerSha256']})
        for row in answer['rows']:
            if row['actualDeduction'] is not None and row['actualDeduction'] < 0:
                answers.setdefault(job['documentId'], []).append(dict(row,
                    subject=indexed[row['evaluationId']]['subject'], attribute=indexed[row['evaluationId']]['attribute'],
                    category=indexed[row['evaluationId']]['category']))
    all_groups, review_hashes = [], []
    for document in seal['documentIds']:
        defects = answers.get(document, [])
        # Even zero-defect documents require an independent inference confirmation.
        target = batch / 'normalization-jobs' / document
        target.mkdir(parents=True, exist_ok=False)
        prompt = grader.POLICY + '\nIndependent defect identity review. Do not regrade or alter deductions.\n'
        prompt += 'The exact sealed capsule root is ' + str(capsule.resolve()) + '.\n'
        prompt += 'Every tool call must explicitly set its workdir/cwd to that absolute capsule root. '
        prompt += 'If no workdir/cwd option is available, use only absolute paths beneath that root. '
        prompt += 'The tool default directory may be elsewhere even though this process cwd is the capsule. '
        prompt += 'Read ' + str((capsule / 'manifest.json').resolve()) + ' first; do not enumerate relative parent or sibling paths.\n'
        prompt += 'Read sealed capsule data as necessary. Group only the same causal defect and same semantic unit '
        prompt += 'within this document. Distinct item attributes, events, branches, or processing steps remain distinct. '
        prompt += 'A shared absence of a whole section is not permission to merge every missing requirement into one cause. '
        prompt += 'Return every negative row exactly once in groups; include singleton groups. Give a specific reason for each group. '
        prompt += 'With no defects, return an empty groups array after reviewing the evidence.\n'
        prompt += 'For this identity-only task, limitations means unresolved identity/coverage verification '
        prompt += 'or a procedural violation. Original application and deployment limitations are already '
        prompt += 'preserved in the raw grading answers; do not restate them as an identity-review limitation. '
        prompt += 'If identity verification is complete and the read boundary was respected, return limitations=[]. '
        prompt += 'Any actual read-boundary violation or unresolved identity must still be disclosed.\n'
        import json
        prompt += json.dumps({'documentId': document, 'defects': defects}, ensure_ascii=False)
        (target / 'prompt.txt').write_text(prompt, encoding='utf-8')
        grader.save(target / 'schema.json', SCHEMA)
        remaining = min(args.timeout_seconds, grader.remaining(args.deadline))
        if remaining <= 0:
            raise TimeoutError('Deadline expired before independent defect review')
        cli = grader.resolve_cli()
        command = [str(cli), 'exec', '--ephemeral', '--sandbox', 'read-only', '--color', 'never', '--json',
            '-c', 'approval_policy="never"', '-c', 'project_doc_max_bytes=0', '--output-last-message', str(target / 'answer.txt'),
            '--output-schema', str(target / 'schema.json'), '-']
        result = {'status': 'RUNNING', 'documentId': document, 'deadline': args.deadline, 'timeoutSeconds': remaining,
            'modelSelection': 'user_configured_default', 'normalizerSha256': grader.digest(Path(__file__)),
            'promptSha256': grader.digest(target / 'prompt.txt'), 'batchManifestSha256': grader.digest(batch / 'batch.json'),
            'startedAt': datetime.now(timezone.utc).isoformat()}
        try:
            with (target / 'prompt.txt').open('rb') as stdin, (target / 'events.jsonl').open('xb') as stdout, (target / 'stderr.log').open('xb') as stderr:
                options = {'creationflags': subprocess.CREATE_NO_WINDOW} if sys.platform == 'win32' else {}
                process = subprocess.run(command, cwd=capsule, stdin=stdin, stdout=stdout, stderr=stderr,
                    timeout=remaining, shell=False, check=False, **options)
            if process.returncode:
                raise ValueError('Normalization CLI failed')
            usage, event_summary = grader._events(target / 'events.jsonl')
            if event_summary['error_events'] or event_summary['invalid_event_lines']:
                raise ValueError('Normalization inference events failed')
            answer = grader.load(target / 'answer.txt')
            from jsonschema import Draft202012Validator
            Draft202012Validator(SCHEMA).validate(answer)
            if answer['documentId'] != document or answer['limitations']:
                raise ValueError('Independent normalization is incomplete or target differs')
            row_ids = [row_id for group in answer['groups'] for row_id in group['evaluationIds']]
            if len(row_ids) != len(set(row_ids)) or set(row_ids) != {r['evaluationId'] for r in defects}:
                raise ValueError('Every defect must be covered exactly once')
            if len({g['canonicalDefectId'] for g in answer['groups']}) != len(answer['groups']):
                raise ValueError('Distinct groups must have distinct defect identities')
            for group in answer['groups']:
                if not group['reason'].strip() or not group['evaluationIds']:
                    raise ValueError('Defect group needs meaningful explanation and members')
                all_groups.append(dict(group, documentId=document))
            result.update(status='PASSED', usage=usage, answerSha256=grader.digest(target / 'answer.txt'))
            review_hashes.append({'documentId': document, 'answerSha256': result['answerSha256']})
        except Exception as exc:
            result.update(status='FAILED', errorType=type(exc).__name__, error=str(exc)[:350])
            grader.save(target / 'result.json', result)
            raise
        grader.save(target / 'result.json', result)
        print(json.dumps({'documentId': document, 'groups': len(answer['groups']), 'status': 'PASSED'}), flush=True)
    grader.check_capsule(batch)
    grader.save(grader.safe(args.output, batch), {'schema': 'independent-defect-normalization/1',
        'status': 'INDEPENDENTLY_REVIEWED', 'batchManifestSha256': grader.digest(batch / 'batch.json'),
        'rawGradingAnswers': raw_hashes, 'independentReviews': review_hashes, 'groups': all_groups})

if __name__ == '__main__':
    main()
