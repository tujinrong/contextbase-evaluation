"""Render a completed immutable AI draft, with a separate visual review state."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from contextbase.ai import capsule
from contextbase.ai.rendering import render_document

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--draft-result', type=Path, required=True)
    parser.add_argument('--document', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--deadline', default='2026-10-13T20:15:58Z')
    args = parser.parse_args()
    if datetime.now(timezone.utc) >= datetime.fromisoformat(args.deadline.replace('Z', '+00:00')):
        raise RuntimeError('Deadline reached before rendering')
    state = capsule.verify(args.snapshot)
    draft = json.loads(args.draft_result.read_text(encoding='utf-8'))
    document_bytes = args.document.read_bytes()
    checksum = hashlib.sha256(document_bytes).hexdigest()
    if checksum != draft['contentSha256']:
        raise ValueError('Only the unchanged completed AI response may be rendered')
    relative = Path(draft['path'])
    document = args.document.resolve()
    if relative.is_absolute() or '..' in relative.parts or tuple(document.parts[-len(relative.parts):]) != relative.parts:
        raise ValueError('Draft must retain its contracted canonical relative path')
    canonical_root = document.parents[len(relative.parts) - 1]
    mermaid = os.environ.get('CONTEXTBASE_MERMAID_PACKAGE')
    result = render_document(args.document, args.destination, document_path=draft['path'],
                             asset_root=canonical_root,
                             mermaid_package=Path(mermaid) if mermaid else None)
    capsule.verify(args.snapshot)
    if args.document.read_bytes() != document_bytes:
        raise ValueError('Draft changed during rendering')
    canonical = args.destination / (Path(draft['path']).stem + '.html')
    shutil.copyfile(args.destination / 'document.html', canonical)
    result.update({
        'documentId': draft['documentId'], 'canonicalDocumentPath': draft['path'],
        'canonicalHtmlFilename': canonical.name,
        'canonicalHtmlSha256': hashlib.sha256(canonical.read_bytes()).hexdigest(),
        'sourceSnapshotManifestSha256': hashlib.sha256((args.snapshot / 'manifest.json').read_bytes()).hexdigest(),
        'draftResultSha256': hashlib.sha256(args.draft_result.read_bytes()).hexdigest(),
        'referenceMode': capsule.reference_mode(state),
        'originalApplicationExecuted': False, 'visualFidelityVerified': False,
        'formalRubricEvaluated': False, 'createdAt': datetime.now(timezone.utc).isoformat(),
    })
    capsule.write_json(args.destination / 'render-pins.json', result)
    print(json.dumps({'documentId': draft['documentId'], 'structure': result['structure']['status'],
                      'display': result['display']['status'], 'layouts': len(result['layouts']),
                      'diagrams': len(result['diagrams']), 'visualFidelityVerified': False}, ensure_ascii=False))

if __name__ == '__main__':
    main()
