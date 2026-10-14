"""Audit saved AI prose against the latest generic contract without rewriting it."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from contextbase.ai.validation import validate_document

parser = argparse.ArgumentParser()
parser.add_argument('--draft-result', type=Path, required=True)
parser.add_argument('--document', type=Path, required=True)
parser.add_argument('--contract', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
report_root = Path(__file__).resolve().parents[1]
if not args.output.resolve().is_relative_to(report_root):
    raise ValueError('Structure report must be inside this run report')
draft = json.loads(args.draft_result.read_text(encoding='utf-8'))
contract = json.loads(args.contract.read_text(encoding='utf-8'))
entry = next(item for item in contract['documents'] if item['id'] == draft['documentId'])
before = args.document.read_bytes()
sha = hashlib.sha256(before).hexdigest()
if sha != draft['contentSha256'] or entry['path'] != draft['path']:
    raise ValueError('Saved AI response or contracted path changed')
findings = validate_document(before.decode('utf-8'), entry['path'],
    expected_document_id=entry['id'], expected_kind=entry['kind'])
if args.document.read_bytes() != before:
    raise ValueError('AI prose changed during structure audit')
args.output.parent.mkdir(parents=True, exist_ok=True)
result = {'schema': 'pinned-ai-draft-structure-audit/1', 'observedAt': datetime.now(timezone.utc).isoformat(),
    'documentId': entry['id'], 'kind': entry['kind'], 'canonicalDocumentPath': str(args.document.resolve()),
    'relativePath': entry['path'], 'documentSha256': sha, 'findings': findings,
    'status': 'PASS' if not findings else 'ERROR', 'validatorModuleSha256': hashlib.sha256(
        Path(__import__('contextbase.ai.validation', fromlist=['__file__']).__file__).read_bytes()).hexdigest(),
    'businessMeaningApproved': False, 'documentRewritten': False, 'originalApplicationExecuted': False}
with args.output.open('x', encoding='utf-8') as output:
    json.dump(result, output, ensure_ascii=False, indent=2)
    output.write('\n')
print(json.dumps({'documentId': entry['id'], 'status': result['status'], 'findings': findings}, ensure_ascii=False))
raise SystemExit(1 if findings else 0)
