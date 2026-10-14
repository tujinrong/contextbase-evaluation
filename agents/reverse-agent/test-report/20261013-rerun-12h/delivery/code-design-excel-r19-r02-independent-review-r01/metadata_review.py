import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
DEL = ROOT.parent
INV = DEL / 'excel-bitmap-code-design-r19-r02-widthonly-tiles' / 'inventory.json'
EXPECTED_INV = '86d6e32f975ae90567053be68c253e49abccc97ae117abd030b8db31001d767c'
EXPECTED_XLSX = 'd90801e47b539b057bf456ab729c8d2f491fe2a4acc383c8f5328250603a89b7'
DELTA = DEL / 'code-design-xlsx-r19-r02-widthonly-xml-delta.json'

def digest(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()

def check():
    assert digest(INV) == EXPECTED_INV, 'inventory hash mismatch'
    inventory = json.loads(INV.read_text(encoding='utf-8'))
    assert len(inventory['documents']) == 1
    document = inventory['documents'][0]
    assert document['originalPreviewCount'] == 43
    assert document['xlsxSha256'] == EXPECTED_XLSX
    captures = document['captures']
    assert len(captures) == 81
    pins = {str(INV): EXPECTED_INV, **inventory['sourceBindings']}
    originals = set()
    for capture in captures:
        assert capture['scale'] == 1
        assert capture['pixelsEqualToOriginalRegion'] is True
        pins[capture['path']] = capture['sha256']
        pins[capture['originalPath']] = capture['originalSha256']
        originals.add(capture['originalPath'])
    assert len(originals) == 43
    delta_sha = digest(DELTA)
    assert delta_sha.startswith('3e0a8c84')
    pins[str(DELTA)] = delta_sha
    assert str(Path(document['xlsx'])) in pins
    failures = [path for path, expected in pins.items() if digest(path) != expected]
    assert not failures, failures
    for capture in captures:
        rect = capture['sourceRectangle']
        with Image.open(capture['originalPath']) as original, Image.open(capture['path']) as tile:
            assert list(original.size) == capture['wholeOriginalSize']
            box = (rect['x'], rect['y'], rect['x'] + rect['width'], rect['y'] + rect['height'])
            expected = original.convert('RGBA').crop(box)
            actual = tile.convert('RGBA')
            assert expected.size == actual.size
            assert expected.tobytes() == actual.tobytes(), 'pixel mismatch: ' + capture['path']
    return inventory, document, captures, pins

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['before','after'], required=True)
    args = parser.parse_args()
    inventory, document, captures, pins = check()
    receipt = {
        'schema':'independent-excel-bitmap-metadata-hash-check/1',
        'createdUtc':datetime.now(timezone.utc).isoformat(),
        'phase':args.phase,
        'status':'PASS_PINNED_FILES_AND_EXACT_RGBA',
        'inventoryPath':str(INV),
        'inventorySha256':EXPECTED_INV,
        'documentId':document['documentId'],
        'canonicalDocumentPath':document['canonicalDocumentPath'],
        'markdownSha256FromMetadata':document['markdownSha256'],
        'xlsx':document['xlsx'],
        'xlsxSha256':document['xlsxSha256'],
        'originalCount':43,
        'tileCount':81,
        'checkedFiles':len(pins),
        'exactRgbaComparisons':81,
        'pins':pins,
        'captures':captures,
        'sourceOrCellBodyDecoded':False,
        'semanticAssessment':False,
        'formalScoring':False,
        'publication':False,
        'applicationExecuted':False,
    }
    target = ROOT / ('metadata-' + args.phase + '.json')
    assert not target.exists(), 'immutable existing receipt'
    if args.phase == 'after':
        before = json.loads((ROOT / 'metadata-before.json').read_text(encoding='utf-8'))
        assert before['pins'] == pins
        assert before['captures'] == captures
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    compact = {k:v for k,v in receipt.items() if k not in ['pins','captures']}
    compact['receiptSha256'] = digest(target)
    print(json.dumps(compact, ensure_ascii=False, separators=(',',':')))

if __name__ == '__main__':
    main()

