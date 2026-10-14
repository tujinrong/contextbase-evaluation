"""Lossless authorized-reference preparation; no prose or semantic judgement."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from contextbase.ai import capsule

REPORT = Path(__file__).resolve().parents[1]
AGENT = REPORT.parents[1]
REPO = AGENT.parents[1]
SOURCE = REPO / 'test-project1/srcs/CSharp_ASPNET'
BASELINE = AGENT / '.tmp/20261013-rerun-12h/source-only/snapshot'
DESTINATION = AGENT / '.tmp/20261013-rerun-12h/training-assisted/snapshot'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    baseline = capsule.verify(BASELINE)
    references = (SOURCE / 'spec/基本設計書', SOURCE / 'spec/詳細仕様書')
    before = {p.resolve(): sha(p) for root in references for p in root.rglob('*.md')}
    contract = json.loads((REPORT / 'document-contract.json').read_text(encoding='utf-8'))
    manifest = capsule.create(SOURCE, DESTINATION, project_id='test-project1',
        excluded_directories=capsule.EXCLUDED_DIRECTORIES | {'maintenance'},
        authorized_reference_directories=references)
    if [(p['path'], p['sha256']) for p in manifest['files']] != [(p['path'], p['sha256']) for p in baseline['files']]:
        raise ValueError('Assisted source material differs from baseline')
    if len(manifest['referenceFiles']) != 11 or len(before) != 11:
        raise ValueError('Expected exactly eleven authorized original design documents')
    if any(sha(p) != value for p, value in before.items()):
        raise ValueError('Reference source changed during preparation')
    capsule.verify(DESTINATION)
    result = {
        'schema': 'reverse-agent-assisted-preparation/1',
        'preparedAt': datetime.now(timezone.utc).isoformat(),
        'mode': 'training-assisted', 'projectId': 'test-project1',
        'authorization': 'Latest user-authorized basic and detailed designs; recorded in agents/reverse-agent/AGENTS.md Scope',
        'snapshot': str(DESTINATION), 'snapshotState': capsule.verification_state(DESTINATION),
        'sourceFiles': len(manifest['files']), 'authorizedReferenceFiles': len(manifest['referenceFiles']),
        'baselineSourceHashesIdentical': True,
        'originalFilesModified': False, 'inputProgramExecuted': False,
        'evaluatorCriteriaIncluded': False, 'generationStarted': False,
        'semanticAnalysisPerformed': False, 'formalScore': None,
        'baselineManifestSha256': sha(BASELINE / 'manifest.json'),
        'documentContractSha256': sha(REPORT / 'document-contract.json'),
        'references': [{'path': p['path'], 'sha256': p['sha256'], 'basis': p['basis']} for p in manifest['referenceFiles']],
        'referenceModeBoundary': 'Reference designs cannot establish observed implementation; author and evaluator must retain the distinction',
    }
    output = REPORT / 'training-assisted/preparation.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({k: result[k] for k in ('mode', 'sourceFiles', 'authorizedReferenceFiles', 'snapshotState', 'generationStarted')}))

if __name__ == '__main__':
    main()
