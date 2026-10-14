"""Audit immutable provider quotations by role; never repair answers or grade prose."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import grader

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    batch = grader.safe(args.batch, grader.HERE)
    seal = grader.load(batch / 'batch.json')
    capsule = batch / 'capsule'
    if grader.digest(capsule / 'manifest.json') != seal['capsuleManifestSha256']:
        raise ValueError('Capsule manifest drift')
    manifest = grader.load(capsule / 'manifest.json')
    manifest_paths = {item['path'] for item in manifest['files']}
    for item in manifest['files']:
        if grader.digest(grader.safe(capsule / item['path'], capsule)) != item['sha256']:
            raise ValueError('Capsule file drift')
    counts, invalid, answers = Counter(), [], []
    for job in seal['jobs']:
        answer_path = batch / 'jobs' / job['shardId'] / 'answer.txt'
        if not answer_path.is_file():
            continue
        before = grader.digest(answer_path)
        answer = grader.load(answer_path)
        ids = [row['evaluationId'] for row in answer['rows']]
        entries = []
        for row in answer['rows']:
            entries.extend(('row-generated', row['evaluationId'], 'generated/', item) for item in row['generatedEvidence'])
            entries.extend(('row-source', row['evaluationId'], 'source/', item) for item in row['sourceFidelity']['sourceEvidence'])
        for check in answer['safetyChecks']:
            entries.extend(('safety-generated', check['topic'], 'generated/', item) for item in check['generatedEvidence'])
            entries.extend(('safety-source', check['topic'], 'source/', item) for item in check['sourceEvidence'])
        for scope, key, prefix, item in entries:
            valid = grader.evidence_valid([item], capsule, prefix, manifest_paths)
            counts[scope + '-total'] += 1
            counts[scope + ('-valid' if valid else '-invalid')] += 1
            if not valid:
                reason = 'ROLE_OR_PATH_MISMATCH' if not item['path'].startswith(prefix) else ('EMPTY_QUOTE' if not item['quote'] else 'PATH_RANGE_OR_VERBATIM_MISMATCH')
                invalid.append({'shardId': job['shardId'], 'scope': scope, 'subject': key, 'reason': reason, 'evidence': item})
        if before != grader.digest(answer_path):
            raise ValueError('Provider answer changed during diagnostic')
        answers.append({'shardId': job['shardId'], 'answerSha256': before, 'answerUnchanged': True,
            'rows': len(ids), 'uniqueRows': len(set(ids)), 'exactRequestedIdSet': set(ids) == set(job['evaluationIds'])})
    grader.save(grader.safe(args.output, batch), {'schema': 'independent-evidence-diagnostic/1',
        'diagnosedAt': datetime.now(timezone.utc).isoformat(), 'counts': dict(counts), 'invalidEvidence': invalid,
        'answers': answers, 'capsuleManifestSha256': seal['capsuleManifestSha256'],
        'capsuleFilesUnchanged': True, 'answerRepairPerformed': False, 'formalScoreAssigned': False})
    print({'counts': dict(counts), 'invalidEvidence': len(invalid), 'formalScoreAssigned': False})

if __name__ == '__main__':
    main()
