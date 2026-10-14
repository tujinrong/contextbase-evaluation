import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEL = ROOT.parent
INV = DEL / 'pdf-native-tiles-registration-detail-r19-r01' / 'inventory.json'
EXPECTED_INV = '3adb16e3b4f10091aa7a9cf3a6619a5fcc9caefa1de404690706b7b43133cef7'

def digest(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()

def check():
    assert digest(INV) == EXPECTED_INV, 'inventory SHA mismatch'
    inventory = json.loads(INV.read_text(encoding='utf-8'))
    documents = inventory['documents']
    assert len(documents) == 1
    document = documents[0]
    assert document['originalPageCount'] == 46
    captures = document['captures']
    assert len(captures) == 184
    pins = {str(INV): EXPECTED_INV, **inventory['sourceBindings']}
    for capture in captures:
        assert capture['scale'] == 1
        assert capture['pixelsEqualToOriginalRegion'] is True
        assert capture['wholeOriginalSize'] == [2496, 3192]
        pins[capture['path']] = capture['sha256']
        pins[capture['originalPath']] = capture['originalSha256']
    failures = [path for path, expected in pins.items() if digest(path) != expected]
    assert not failures, failures
    return inventory, document, captures, pins

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['before', 'after'], required=True)
    args = parser.parse_args()
    inventory, document, captures, pins = check()
    receipt = {
        'schema': 'independent-pdf-metadata-hash-check/1',
        'createdUtc': datetime.now(timezone.utc).isoformat(),
        'phase': args.phase,
        'status': 'PASS_PINNED_FILES_UNCHANGED',
        'inventoryPath': str(INV),
        'inventorySha256': EXPECTED_INV,
        'documentId': document['documentId'],
        'canonicalDocumentPath': document['canonicalDocumentPath'],
        'markdownSha256': document['markdownSha256'],
        'pdf': document['pdf'],
        'pdfSha256': document['pdfSha256'],
        'pageCount': 46,
        'tileCount': 184,
        'checkedFiles': len(pins),
        'pins': pins,
        'contentReadForSemanticAssessment': False,
        'formalScoring': False,
        'publication': False,
        'applicationExecuted': False,
    }
    target = ROOT / f'metadata-{args.phase}.json'
    assert not target.exists(), 'immutable existing receipt'
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if args.phase == 'after':
        before = json.loads((ROOT / 'metadata-before.json').read_text(encoding='utf-8'))
        assert before['pins'] == pins, 'before/after pin map differs'
    output = {key: value for key, value in receipt.items() if key != 'pins'}
    output['receiptSha256'] = digest(target)
    if args.phase == 'before':
        output['tileRoot'] = str(DEL / 'pdf-native-tiles-registration-detail-r19-r01' / document['documentId'])
        output['captures'] = [{
            'page': capture['page'],
            'file': Path(capture['path']).name,
            'sha256': capture['sha256'],
            'rectangle': capture['sourceRectangle'],
        } for capture in captures]
    print(json.dumps(output, ensure_ascii=False, separators=(',', ':')))

if __name__ == '__main__':
    main()
