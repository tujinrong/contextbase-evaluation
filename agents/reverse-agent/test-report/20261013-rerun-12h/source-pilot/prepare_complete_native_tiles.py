"""Crop existing pinned captures losslessly, including complete document images."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops

p = argparse.ArgumentParser()
p.add_argument('--render', required=True, type=Path)
p.add_argument('--destination', required=True, type=Path)
a = p.parse_args()
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
pins_file = a.render / 'render-pins.json'
pins_bytes = pins_file.read_bytes()
pins = json.loads(pins_bytes)
source = Path(pins['source'])
if pins['referenceMode'] != 'source-only' or pins['display']['status'] != 'PASS':
    raise ValueError('Successful source-only render required')
if sha(source) != pins['sourceSha256'] or a.destination.exists():
    raise ValueError('Fixed canonical parent and fresh destination required')
images = []
for entry in pins['diagrams'] + pins['layouts']:
    if entry['status'] != 'PASS':
        raise ValueError('Every diagram and layout must be successfully captured')
    images.append((entry['id'], entry['id'] + '.png', entry['png'], 'diagram-or-layout'))
display = pins['display']
if 'documentPng' in display:
    images.append(('document', 'document.png', display['documentPng'], 'complete-document'))
else:
    capture = display['documentCapture']
    if not capture['complete'] or capture['mode'] != 'complete-vertical-tiles':
        raise ValueError('Complete native document capture required')
    cursor = 0
    for page in capture['pages']:
        rectangle = page['sourceRectangle']
        if rectangle['x'] != 0 or rectangle['y'] != cursor or rectangle['width'] != capture['width']:
            raise ValueError('Document strips have a gap, overlap, or incomplete width')
        cursor += rectangle['height']
        images.append((Path(page['path']).stem, page['path'], page['png'], 'complete-document-strip'))
    if cursor != capture['height']:
        raise ValueError('Document strip extent is incomplete')
a.destination.mkdir(parents=True)
records = []
for image_id, name, png, kind in images:
    if Path(name).name != name:
        raise ValueError('Capture path must remain within render root')
    path = a.render / name
    before = sha(path)
    if before != png['sha256']:
        raise ValueError('Pinned image changed')
    with Image.open(path) as original:
        original.load()
        if original.size != (png['width'], png['height']):
            raise ValueError('Pinned dimensions differ from actual capture')
        for y in range(0, original.height, 1700):
            for x in range(0, original.width, 1700):
                bounds = (x, y, min(x + 1800, original.width), min(y + 1800, original.height))
                crop = original.crop(bounds)
                target = a.destination / f'{image_id}-{x:04}-{y:04}.png'
                crop.save(target)
                with Image.open(target) as saved:
                    if saved.size != crop.size or ImageChops.difference(saved.convert('RGBA'), crop.convert('RGBA')).getbbox():
                        raise ValueError('Cropped pixels changed')
                records.append({'imageId': image_id, 'imageKind': kind,
                    'originalPath': str(path.resolve()), 'originalSha256': before,
                    'path': str(target.resolve()), 'sha256': sha(target),
                    'sourceRectangle': {'x': x, 'y': y, 'width': bounds[2] - x, 'height': bounds[3] - y},
                    'wholeOriginalSize': [original.width, original.height], 'scale': 1,
                    'pixelsEqualToOriginalRegion': True, 'actuallyReviewed': False})
    if sha(path) != before:
        raise ValueError('Original capture changed during cropping')
if sha(source) != pins['sourceSha256'] or pins_file.read_bytes() != pins_bytes:
    raise ValueError('Parent or render pins changed during cropping')
record = {'schema': 'native-review-tile-inventory/1', 'createdAt': datetime.now(timezone.utc).isoformat(),
    'documentId': pins['documentId'], 'referenceMode': pins['referenceMode'],
    'documentSha256': pins['sourceSha256'], 'renderPinsSha256': hashlib.sha256(pins_bytes).hexdigest(),
    'sourceSnapshotSha256': pins['sourceSnapshotManifestSha256'],
    'coverage': 'all diagrams, layouts, and complete document native pixels; crops overlap 100 pixels',
    'captures': records, 'nativeApproval': False, 'applicationExecuted': False}
with (a.destination / 'inventory.json').open('x', encoding='utf-8', newline='\n') as f:
    json.dump(record, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(json.dumps({'images': len(images), 'nativeTiles': len(records), 'approved': False}))
