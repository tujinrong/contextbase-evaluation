"""Record actual native tile observations; never change manuscript/rendered content."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('--inventory', required=True, type=Path)
parser.add_argument('--observations', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
sha = lambda data: hashlib.sha256(data).hexdigest()
inventory_bytes = args.inventory.read_bytes()
inventory = json.loads(inventory_bytes)
observation_bytes = args.observations.read_bytes()
observations = json.loads(observation_bytes)
if observations['documentSha256'] != inventory['documentSha256']:
    raise ValueError('observation parent SHA differs from native inventory')
names = [Path(row['path']).name for row in inventory['captures']]
if sorted(names) != sorted(observations['actuallyViewedCaptureNames']) or len(set(names)) != len(names):
    raise ValueError('actual-view receipt must enumerate every distinct inventory tile')
pins_path = Path(inventory['captures'][0]['originalPath']).parent / 'render-pins.json'
pins_bytes = pins_path.read_bytes()
pins = json.loads(pins_bytes)
if sha(pins_bytes) != inventory['renderPinsSha256'] or pins['sourceSha256'] != inventory['documentSha256']:
    raise ValueError('render pins differ from immutable native inventory')
document = Path(pins['source'])
document_bytes = document.read_bytes()
if sha(document_bytes) != inventory['documentSha256']:
    raise ValueError('canonical parent changed after rendering')
captures = []
for row in inventory['captures']:
    tile, original = Path(row['path']), Path(row['originalPath'])
    tile_bytes, original_bytes = tile.read_bytes(), original.read_bytes()
    if sha(tile_bytes) != row['sha256'] or sha(original_bytes) != row['originalSha256'] or row['scale'] != 1:
        raise ValueError('native image bytes/scale differ from immutable inventory')
    rect = row['sourceRectangle']
    with Image.open(original) as source, Image.open(tile) as capture:
        box = (rect['x'], rect['y'], rect['x'] + rect['width'], rect['y'] + rect['height'])
        region = source.crop(box).convert('RGBA')
        if region.size != capture.size or region.tobytes() != capture.convert('RGBA').tobytes():
            raise ValueError('tile is not the original-scale exact pixel region')
    captures.append({**row, 'actuallyReviewed': True, 'pixelsEqualToOriginalRegionReverified': True})
result = {
    'classification': 'SOURCE_ONLY_ACTUAL_NATIVE_GEOMETRY_REVIEW',
    'createdAt': datetime.now(timezone.utc).isoformat(),
    'reviewScope': 'OWN_MODE_NATIVE_DIAGRAM_LAYOUT_AND_COMPLETE_DOCUMENT_GEOMETRY_ONLY',
    'documentFile': str(document), 'documentSha256': inventory['documentSha256'],
    'sourceSnapshotSha256': inventory['sourceSnapshotSha256'],
    'renderPinsFile': str(pins_path), 'renderPinsSha256': sha(pins_bytes),
    'inventoryFile': str(args.inventory.resolve()), 'inventorySha256': sha(inventory_bytes),
    'observationFile': str(args.observations.resolve()), 'observationSha256': sha(observation_bytes),
    'allNativeCapturesActuallyViewed': True, 'captureCount': len(captures),
    'nativeImageCount': len(set(row['imageId'] for row in captures)),
    'captures': captures, 'findings': observations['findings'],
    'geometryApproved': not observations['findings'],
    'adopted': False, 'applicationRuntimeVerified': False,
    'pixelFidelityAgainstRunningApplicationVerified': False,
    'allDynamicStatesVerified': False, 'formalSemanticScoreVerified': False,
    'manuscriptBytesModified': False, 'renderBytesModified': False,
}
with args.output.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
if document.read_bytes() != document_bytes or args.inventory.read_bytes() != inventory_bytes or pins_path.read_bytes() != pins_bytes:
    raise ValueError('native review inputs changed while recording')
print(json.dumps({'file': str(args.output.resolve()), 'documentSha256': result['documentSha256'],
                  'captureCount': len(captures), 'geometryApproved': result['geometryApproved']}, ensure_ascii=False))
