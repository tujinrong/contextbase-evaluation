"""Pin an existing approved AI manuscript for parent selection; do not adopt or edit it."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from contextbase.ai import capsule, validation

parser = argparse.ArgumentParser()
parser.add_argument('--document', required=True, type=Path)
parser.add_argument('--draft-result', required=True, type=Path)
parser.add_argument('--review-handoff', required=True, type=Path)
parser.add_argument('--runtime-receipt', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
report = Path(__file__).resolve().parent
repo = report.parents[4]
snapshot = repo / 'agents/reverse-agent/.tmp/20261013-rerun-12h/source-only/snapshot'
document_bytes = args.document.read_bytes()
draft_bytes = args.draft_result.read_bytes()
review_bytes = args.review_handoff.read_bytes()
draft = json.loads(draft_bytes)
review = json.loads(review_bytes)
digest = hashlib.sha256(document_bytes).hexdigest()
state = capsule.verification_state(snapshot)
if digest != draft['contentSha256'] or digest != review['documentSha256'] or draft['snapshot'] != state or review['snapshot'] != state:
    raise ValueError('ready candidate document/draft/review/capsule SHA bindings differ')
verified_file = args.review_handoff.parent / 'review-verified.json'
verified_bytes = verified_file.read_bytes()
verified = json.loads(verified_bytes)
if (review['approved'] is not True or verified['approved'] is not True or verified['findings'] != [] or
    hashlib.sha256(verified_bytes).hexdigest() != review['reviewSha256'] or
    review['reviewScope'] != 'text-source-and-structure' or review['referenceMode'] != 'source-only'):
    raise ValueError('ready candidate requires its exact approved source-only independent review')
findings = validation.validate_document(document_bytes.decode('utf-8'), draft['path'], expected_document_id=draft['documentId'])
if findings:
    raise ValueError('ready candidate requires current structural PASS')
receipt_bytes = args.runtime_receipt.read_bytes()
receipt = json.loads(receipt_bytes)
runtime = Path(receipt['destination'])
actual = {p.relative_to(runtime).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in runtime.rglob('*')
          if p.is_file() and '__pycache__' not in p.parts and p.suffix.lower() not in {'.pyc', '.pyo'}}
if actual != receipt['files'] or runtime not in Path(validation.__file__).resolve().parents:
    raise ValueError('ready candidate must use its full pinned generation/current-structure runtime')
result = {'classification': 'SOURCE_ONLY_TEXT_SOURCE_STRUCTURE_REVIEW_READY_FOR_PARENT_SELECTION',
          'createdAt': datetime.now(timezone.utc).isoformat(), 'documentId': draft['documentId'],
          'canonicalDocumentFile': str(args.document.resolve()), 'canonicalDocumentSha256': digest,
          'draftResultFile': str(args.draft_result.resolve()), 'draftResultSha256': hashlib.sha256(draft_bytes).hexdigest(),
          'generationRuntimeReceipt': str(args.runtime_receipt.resolve()),
          'generationRuntimeReceiptSha256': hashlib.sha256(receipt_bytes).hexdigest(),
          'generationRuntimeAll124HashesMatched': True, 'actualValidatorImport': validation.__file__,
          'structureFindings': findings, 'independentReview': {'handoffFile': str(args.review_handoff.resolve()),
          'handoffSha256': hashlib.sha256(review_bytes).hexdigest(), 'verifiedFile': str(verified_file.resolve()),
          'verifiedSha256': hashlib.sha256(verified_bytes).hexdigest(), 'approved': True, 'scope': review['reviewScope']},
          'snapshot': str(snapshot), 'snapshotManifestSha256': state['manifestSha256'], 'newRevisionPlanned': False,
          'adopted': False, 'visualFidelityVerified': False, 'applicationRuntimeVerified': False,
          'formallyEvaluatedByOriginalRubric': False}
with args.output.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
if args.document.read_bytes() != document_bytes or args.review_handoff.read_bytes() != review_bytes:
    raise ValueError('ready candidate bytes changed during pinning')
print(json.dumps({'file': str(args.output), 'documentSha256': digest, 'approved': True, 'adopted': False}, ensure_ascii=False))
