"""Bind immutable draft bytes and their renderer output for mechanical export."""
import argparse
import hashlib
import json
from pathlib import Path

REPORT = Path(__file__).resolve().parents[1]
REPO = REPORT.parents[3]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--draft-result', required=True, type=Path)
    parser.add_argument('--document', required=True, type=Path)
    parser.add_argument('--render', required=True, type=Path)
    parser.add_argument('--snapshot', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    md, render = args.document.resolve(), args.render.resolve()
    if not args.output.resolve().is_relative_to((REPORT / 'delivery').resolve()):
        raise ValueError('Binding must remain in this run delivery report')
    draft = json.loads(args.draft_result.read_text(encoding='utf-8-sig'))
    pins = json.loads((render / 'render-pins.json').read_text(encoding='utf-8'))
    canonical = pins['canonicalDocumentPath']
    if sha(md) != pins['sourceSha256'] or pins['sourceSnapshotManifestSha256'] != sha(args.snapshot / 'manifest.json'):
        raise ValueError('Draft or snapshot does not match pinned render')
    mdroot = md
    for part in Path(canonical).parts:
        mdroot = mdroot.parent
    if md != (mdroot / canonical).resolve():
        raise ValueError('Canonical draft hierarchy mismatch')
    bound = {
        'schema': 'reverse-agent-delivery-binding/1',
        'referenceMode': pins['referenceMode'],
        'permittedMarkdownRoot': str(mdroot),
        'permittedRenderRoot': str(REPORT / 'render'),
        'sourceSnapshotManifestSha256': sha(args.snapshot / 'manifest.json'),
        'documents': [{
            'documentId': pins['documentId'], 'canonicalDocumentPath': canonical,
            'markdown': str(md), 'markdownSha256': sha(md),
            'draftResult': str(args.draft_result.resolve()), 'draftResultSha256': sha(args.draft_result),
            'renderDirectory': str(render),
            'renderPinsSha256': sha(render / 'render-pins.json'),
            'renderManifestSha256': sha(render / 'manifest.json'),
        }],
        'formalQualityGatePassed': False,
        'purpose': 'Candidate derivative QA; byte bindings are not semantic or visual approval',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(bound, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'binding': str(args.output), 'documentId': pins['documentId'], 'mode': pins['referenceMode']}))

if __name__ == '__main__':
    main()
