"""Summarize preserved provider timing/usage metadata; never expose or rewrite answer bodies."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--inventory', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
inventory_bytes = args.inventory.read_bytes()
inventory = json.loads(inventory_bytes)
def provider(path):
    if not path.exists():
        return {'resultFile': str(path), 'completedResultAvailable': False}
    data = path.read_bytes()
    value = json.loads(data)
    return {'resultFile': str(path), 'resultSha256': hashlib.sha256(data).hexdigest(),
            'completedResultAvailable': True, 'seconds': value['metadata'].get('seconds'),
            'status': value['metadata'].get('status'), 'modelSelection': value['metadata'].get('model_selection'),
            'usage': value.get('usage'), 'rawAnswerSha256': value['metadata'].get('answer_sha256')}
rows = []
for item in inventory['documents']:
    if 'draftResultFile' not in item:
        continue
    result_path = Path(item['draftResultFile'])
    draft = json.loads(result_path.read_text(encoding='utf-8'))
    original_analysis_job = Path(draft.get('analysisJob') or result_path.parent)
    rows.append({'documentId': item['documentId'], 'documentSha256': item['documentSha256'],
                 'analysisFacts': item['analysisFacts'], 'analysisExecutedInLatestJob': draft.get('analysisExecutedInThisJob'),
                 'originalAnalysisCheckpoint': str(original_analysis_job),
                 'originalAnalysis': provider(original_analysis_job / 'analysis/result.json'),
                 'latestDraft': provider(result_path.parent / 'draft/result.json'),
                 'latestExactShaReviews': [provider(Path(review['file']).parent / 'result.json')
                                          for review in item['reviewHandoffs']]})
value = {'classification': 'PRESERVED_AI_PHASE_TIMING_METADATA_NOT_COMPLETION',
         'createdAt': datetime.now(timezone.utc).isoformat(), 'inventorySha256': hashlib.sha256(inventory_bytes).hexdigest(),
         'documents': rows, 'savedDistinctDocumentCount': len(rows), 'overallCompleted': False,
         'scope': 'Provider elapsed wall seconds; original reused analysis time is historical work, not execution in the latest revision.'}
with args.output.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(value, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'file': str(args.output), 'documents': len(rows), 'overallCompleted': False}, ensure_ascii=False))
