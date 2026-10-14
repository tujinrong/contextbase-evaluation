"""Render seven immutable, source-reviewed candidates using frozen r15 only."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from contextbase.ai import capsule, rendering

report = Path(__file__).resolve().parent
parent = report.parent
repo = report.parents[4]
source_root = repo / 'agents/reverse-agent/.tmp/20261013-rerun-12h/source-only'
runtime = source_root / 'runtime-code/source-09/src'
receipt_file = report / 'runtime-code-source-09.json'
receipt_bytes = receipt_file.read_bytes()
sha = lambda b: hashlib.sha256(b).hexdigest()
assert sha(receipt_bytes) == '6566357d3989760c1bbd19afe751109bb5e85f2121c7a337d80d7ab8a805ce98'
receipt = json.loads(receipt_bytes)
assert Path(receipt['destination']).resolve() == runtime.resolve()
assert Path(capsule.__file__).resolve() == runtime / 'contextbase/ai/capsule.py'
assert Path(rendering.__file__).resolve() == runtime / 'contextbase/ai/rendering.py'

def runtime_inventory():
    return {p.relative_to(runtime).as_posix(): sha(capsule.safe_path(runtime, p).read_bytes())
            for p in runtime.rglob('*') if p.is_file() and '__pycache__' not in p.parts
            and p.suffix.casefold() not in {'.pyc', '.pyo'}}

assert runtime_inventory() == receipt['files']
manifest = source_root / 'snapshot/manifest.json'
assert sha(manifest.read_bytes()) == '2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b'
capsule.verify(source_root / 'snapshot')
inventory_file = report / 'candidate-inventory-r15-1412.json'
inventory_bytes = inventory_file.read_bytes()
inventory = json.loads(inventory_bytes)
ids = {
    'CSHARP_ASPNET-BAS-STU-03-M_CODE_CATEGORY': 'source-category-r15-01',
    'CSHARP_ASPNET-BAS-STU-03': 'source-tableindex-r15-01',
    'CSHARP_ASPNET-BAS-STU-03-M_CLASS': 'source-mclass-r15-01',
    'CSHARP_ASPNET-BAS-STU-03-M_CODE': 'source-mcode-r15-01',
    'CSHARP_ASPNET-BAS-STU-03-M_STUDENT': 'source-mstudent-r15-01',
    'CSHARP_ASPNET-BAS-STU-03-T_OPERATION_LOG': 'source-oplog-r15-01',
    'CSHARP_ASPNET-BAS-STU-04': 'source-codedesign-r15-01',
}
selected = [d for d in inventory['documents'] if d['documentId'] in ids]
assert len(selected) == len(ids)
env = dict(os.environ)
env['PYTHONPATH'] = str(runtime)
env['CONTEXTBASE_CHROMIUM_EXE'] = r'C:\Users\tujin\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe'
env['CONTEXTBASE_MERMAID_PACKAGE'] = str(repo / 'agents/reverse-agent/.tmp/render-tools/node_modules/mermaid')

def run_one(item):
    canonical = Path(item['documentFile'])
    canonical_bytes = canonical.read_bytes()
    assert sha(canonical_bytes) == item['documentSha256']
    assert item['currentStructureFindings'] == []
    reviews = [v for v in item['reviewHandoffs'] if v['approved']]
    if item['documentId'].endswith('T_OPERATION_LOG'):
        reviews = [v for v in reviews if 'remaining-oplog-04-review-r02' in v['file']]
    assert reviews
    pinned_reviews = []
    for review in reviews:
        path = Path(review['file'])
        raw = path.read_bytes()
        value = json.loads(raw)
        assert value['approved'] and value['documentSha256'] == item['documentSha256']
        pinned_reviews.append({'file': str(path), 'sha256': sha(raw)})
    target = parent / 'render' / ids[item['documentId']]
    tiles = parent / 'visual-review' / (ids[item['documentId']] + '-tiles')
    assert not target.exists() and not tiles.exists()
    commands = [
        [sys.executable, '-X', 'utf8', str(parent / 'scripts/render_pinned.py'),
         '--draft-result', item['draftResultFile'], '--document', str(canonical),
         '--snapshot', str(source_root / 'snapshot'), '--destination', str(target),
         '--deadline', '2026-10-13T20:15:58Z'],
        [sys.executable, '-X', 'utf8', str(parent / 'scripts/prepare_native_tiles.py'),
         '--render', str(target), '--destination', str(tiles)],
    ]
    results = []
    for command in commands:
        run = subprocess.run(command, env=env, cwd=repo, capture_output=True, text=True,
                             encoding='utf-8', timeout=1800)
        results.append({'command': command, 'exitCode': run.returncode,
                        'stdout': run.stdout, 'stderr': run.stderr})
        if run.returncode:
            break
    assert canonical.read_bytes() == canonical_bytes
    record = {'documentId': item['documentId'], 'documentFile': str(canonical),
              'documentSha256': item['documentSha256'], 'reviewPins': pinned_reviews,
              'draftResult': item['draftResultFile'], 'renderRoot': str(target),
              'nativeInventory': str(tiles / 'inventory.json'), 'results': results,
              'runtimeReceiptSha256': sha(receipt_bytes), 'runtimeFrozen': 'source-09/r15',
              'nativeActuallyViewed': False, 'geometryApproved': False, 'adopted': False,
              'applicationExecuted': False, 'createdAt': datetime.now(timezone.utc).isoformat()}
    path = report / (ids[item['documentId']] + '-run.json')
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'documentId': item['documentId'], 'exitCodes': [r['exitCode'] for r in results],
                      'inventory': str(tiles / 'inventory.json')}, ensure_ascii=False), flush=True)
    return record

with ThreadPoolExecutor(max_workers=2) as pool:
    futures = [pool.submit(run_one, item) for item in selected]
    records = [f.result() for f in as_completed(futures)]
assert runtime_inventory() == receipt['files']
assert manifest.read_bytes() and sha(manifest.read_bytes()) == inventory['snapshotManifestSha256']
assert inventory_file.read_bytes() == inventory_bytes
with (report / 'table-code-native-r15-render-summary.json').open('x', encoding='utf-8', newline='\n') as f:
    json.dump({'createdAt': datetime.now(timezone.utc).isoformat(), 'runtimeUnchanged': True,
               'inventoryInputSha256': sha(inventory_bytes), 'renders': records,
               'actualNativeReviewPending': True, 'adopted': False}, f, ensure_ascii=False, indent=2)
    f.write('\n')
