"""Preserve observed Artifact display failure; never mark unviewed crops passed."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

P = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
path = P / 'xlsx-native-tiles-registration-detail-r19-r01/inventory.json'
assert sha(path) == '171d4a54ae50a6e9a698665e0027ba3f88fa3724e548fc221079000d5a884384'
inventory = json.loads(path.read_text(encoding='utf8'))
document = inventory['documents'][0]
assert document['documentId'] == 'CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-002'
assert len(document['captures']) == 114
pins = dict(inventory['sourceBindings'])
pins[str(path)] = sha(path)
for capture in document['captures']:
    pins[capture['path']] = capture['sha256']
assert all(sha(p) == expected for p, expected in pins.items())
reviewed = []
for index in range(16):
    capture = dict(document['captures'][index])
    capture.update(actuallyViewed=True, actuallyViewedBy='delivery_tools', captureIndexZeroBased=index, view='original exact RGBA pixels')
    reviewed.append(capture)
record = {'schema':'derived-artifact-native-review/1', 'createdUtc':datetime.now(timezone.utc).isoformat(),
    'scope':'ARTIFACT_NATIVE_PREVIEW_GEOMETRY_ONLY', 'status':'HOLD_PARTIAL_INTERNAL_TOKEN_WRAP',
    'documentId':document['documentId'], 'markdownSha256':document['markdownSha256'], 'xlsx':document['xlsx'], 'xlsxSha256':document['xlsxSha256'],
    'inventory':str(path), 'inventorySha256':sha(path), 'originalPreviewCount':document['originalPreviewCount'],
    'availableTileCount':114, 'actualTileCount':16, 'actuallyViewedZeroBasedIndices':list(range(16)),
    'unviewedZeroBasedIndices':list(range(16,114)), 'captures':reviewed,
    'blocking':[
        {'sheet':'項目一覧','cell':'D6','literalToken':'input','visibleRows':['i','nput'],'captureIndexZeroBased':11},
        {'sheet':'項目一覧','cell':'H16','literalToken':'02','visibleRows':['0','2'],'captureIndexZeroBased':15}
    ],
    'notes':['The first 16 native crops contain all columns of the inspected ranges; the reported splits occur inside cells rather than at a capture boundary.',
        'The independently verified XLSX stores literal values without formula authoring. This receipt concerns Artifact display only.',
        'No claim is made for the remaining 98 Artifact crops. The owned read-only Excel bitmap is a separate display evidence candidate.'],
    'afterHashes':pins, 'allPinnedBytesUnchanged':True, 'cellsEdited':False, 'stylesEdited':False,
    'businessContentAuthored':False, 'applicationExecuted':False, 'formalApproval':False, 'semanticApproval':False,
    'wholeDocumentApproval':False, 'published':False}
out = P / 'registration-detail-artifact-r19-r01-partial-native-hold.json'
assert not out.exists()
out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps({'path':str(out),'sha256':sha(out),'status':record['status'],'actualTiles':16}, ensure_ascii=False))
