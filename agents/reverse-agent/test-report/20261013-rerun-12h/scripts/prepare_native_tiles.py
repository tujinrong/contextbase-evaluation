"""Lossless overlapping crops for actual native review, without approving them."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
from PIL import Image, ImageChops

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--render', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    pins = json.loads((args.render/'render-pins.json').read_text(encoding='utf-8'))
    source = Path(pins['source'])
    if sha(source) != pins['sourceSha256'] or args.destination.exists():
        raise ValueError('Pinned parent and fresh crop directory required')
    args.destination.mkdir(parents=True)
    records = []
    for entry in pins['diagrams'] + pins['layouts']:
        path = args.render/(entry['id']+'.png')
        before = sha(path)
        if before != entry['png']['sha256'] or entry['status'] != 'PASS':
            raise ValueError('Only pinned successful captures can be reviewed')
        with Image.open(path) as original:
            original.load()
            xs = list(range(0, original.width, 1700))
            ys = list(range(0, original.height, 1700))
            for y in ys:
                for x in xs:
                    bounds = (x, y, min(x+1800, original.width), min(y+1800, original.height))
                    crop = original.crop(bounds)
                    target = args.destination/f'{entry["id"]}-{x:04}-{y:04}.png'
                    crop.save(target)
                    with Image.open(target) as saved:
                        if saved.size != crop.size or ImageChops.difference(saved.convert('RGBA'), crop.convert('RGBA')).getbbox():
                            raise ValueError('Native crop pixels changed')
                    records.append({'imageId': entry['id'], 'originalPath': str(path.resolve()),
                        'originalSha256': before, 'path': str(target.resolve()), 'sha256': sha(target),
                        'sourceRectangle': {'x': x, 'y': y, 'width': bounds[2]-x, 'height': bounds[3]-y},
                        'wholeOriginalSize': [original.width, original.height],
                        'scale': 1, 'pixelsEqualToOriginalRegion': True, 'actuallyReviewed': False})
        if sha(path) != before:
            raise ValueError('Original capture changed')
    if sha(source) != pins['sourceSha256']:
        raise ValueError('Canonical draft changed')
    receipt = {'schema': 'native-review-tile-inventory/1',
        'createdAt': datetime.now(timezone.utc).isoformat(), 'documentId': pins['documentId'],
        'referenceMode': pins['referenceMode'], 'documentSha256': pins['sourceSha256'],
        'renderPinsSha256': sha(args.render/'render-pins.json'),
        'sourceSnapshotSha256': pins['sourceSnapshotManifestSha256'],
        'coverage': 'all diagram and layout pixels; 100px overlap for images exceeding 1800px',
        'captures': records, 'nativeApproval': False}
    (args.destination/'inventory.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'images': len(pins['diagrams'])+len(pins['layouts']), 'nativeTiles': len(records), 'approved': False}))

if __name__ == '__main__':
    main()
