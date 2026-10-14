"""Seal one completed AI draft for evaluation without mixing concurrently generated drafts."""
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
import argparse
import json
import shutil
import grader
from combine_batches import FIXED_SNAPSHOTS
from contextbase.ai import capsule as source_capsule
from contextbase.ai.validation import validate_document


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--draft-result', type=Path, required=True)
    parser.add_argument('--canonical', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--maximum-rows', type=int, default=80)
    parser.add_argument('--deadline', default='2026-10-13T20:15:58Z')
    args = parser.parse_args()
    if grader.remaining(args.deadline) <= 0:
        raise TimeoutError('Deadline expired before evaluation preparation')
    user_deadline = grader.load(grader.HERE.parent / 'run-manifest.json')['deadline']
    if datetime.fromisoformat(args.deadline.replace('Z', '+00:00')) > datetime.fromisoformat(user_deadline.replace('Z', '+00:00')):
        raise ValueError('Requested deadline exceeds the user-authorized twelve-hour run')
    if args.maximum_rows < 1 or args.maximum_rows > 80:
        raise ValueError('This run requires shards of at most eighty rows')
    canonical = grader.safe(args.canonical, grader.REPO / 'test-project1/spec-analysis/CSharp_ASPNET')
    draft_result = grader.safe(args.draft_result, grader.AGENT / '.tmp/20261013-rerun-12h')
    receipt_bytes = draft_result.read_bytes()
    receipt = json.loads(receipt_bytes.decode('utf-8-sig'))
    relative = PurePosixPath(receipt['path'])
    if relative.is_absolute() or '..' in relative.parts or relative.suffix != '.md':
        raise ValueError('Canonical relative Markdown path required')
    if tuple(canonical.parts[-len(relative.parts):]) != relative.parts:
        raise ValueError('Original filename hierarchy must be preserved')
    before = canonical.read_bytes()
    if grader.digest(canonical) != receipt['contentSha256']:
        raise ValueError('Canonical draft differs from its AI receipt')
    contract = grader.load(grader.HERE.parent / 'document-contract.json')
    entries = [entry for entry in contract['documents'] if entry['id'] == receipt['documentId']]
    if len(entries) != 1 or entries[0]['path'] != relative.as_posix():
        raise ValueError('Canonical must match the metadata-only document contract')
    findings = validate_document(before.decode('utf-8-sig'), relative.as_posix(),
        expected_document_id=receipt['documentId'], expected_kind=entries[0]['kind'])
    if findings:
        raise ValueError('Draft has not passed current structural validation: ' + str(findings))
    snapshot = grader.safe(args.snapshot, grader.AGENT / '.tmp/20261013-rerun-12h')
    state = source_capsule.verify(snapshot)
    snapshot_sha = grader.digest(snapshot / 'manifest.json')
    mode = source_capsule.reference_mode(state)
    if snapshot_sha != FIXED_SNAPSHOTS[mode]['manifestSha256']:
        raise ValueError('Evaluation requires the fixed run capsule for the selected reference mode')
    batch = grader.safe(args.batch, grader.HERE / 'batches')
    staged = grader.safe(grader.HERE / 'pinned-candidates' / batch.name, grader.HERE)
    if staged.exists() or batch.exists():
        raise ValueError('Fresh immutable evaluation paths required')
    target = staged / Path(relative.as_posix())
    target.parent.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(canonical, target)
    if target.read_bytes() != before or canonical.read_bytes() != before:
        raise ValueError('Byte copy or canonical drift during preparation')
    grader.prepare(SimpleNamespace(batch=batch, draft=staged, snapshot=snapshot,
        document_id=[receipt['documentId']], maximum_rows=args.maximum_rows))
    if canonical.read_bytes() != before or draft_result.read_bytes() != receipt_bytes:
        raise ValueError('Canonical changed while preparing its evaluation capsule')
    source_capsule.verify(snapshot)
    if grader.digest(snapshot / 'manifest.json') != snapshot_sha:
        raise ValueError('Source capsule manifest changed during evaluation preparation')
    grader.save(batch / 'canonical-pin.json', {
        'schema': 'independent-evaluation-canonical-pin/1', 'documentId': receipt['documentId'],
        'createdAt': datetime.now(timezone.utc).isoformat(), 'canonicalPath': str(canonical),
        'canonicalRelativePath': relative.as_posix(), 'canonicalSha256': receipt['contentSha256'],
        'draftResultPath': str(draft_result), 'draftResultSha256': grader.digest(draft_result),
        'sourceSnapshotSha256': snapshot_sha,
        'referenceMode': mode, 'stagedRoot': str(staged),
        'structuralFindings': findings, 'byteIdenticalCopy': True,
        'independentReviewRequiredForQualification': True,
        'formalScore': None, 'visualFidelityVerified': False,
    })


if __name__ == '__main__':
    main()
