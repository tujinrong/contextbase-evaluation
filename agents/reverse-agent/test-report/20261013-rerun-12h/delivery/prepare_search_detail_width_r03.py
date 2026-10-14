"""Mechanical single-document width projection; original literals stay exact."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json

P = Path(__file__).resolve().parent
ID = 'CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-001'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf8'))
originalpath = P / 'model-assisted-screens-r18-r02.json'
assert sha(originalpath) == '08bc77b7d6a2005f9f39f27d663f5a9373bafa615618f677383f3959d459fa2a'
holdpath = P / 'search-detail-excel-bitmap-r18-r02-actual-native-review.json'
assert sha(holdpath) == '869a7d0cb0e049a7ca0b3c97a6e00055fb1a836772527c8c6b98d552dcb5838f'
hold = read(holdpath)
assert hold['status'] == 'HOLD_ACTUAL_EXCEL_INTERNAL_IDENTIFIER_WRAP' and hold['actualOriginalTiles'] == 89
original = read(originalpath)
ordinal, selected = next((i, d) for i, d in enumerate(original['documents']) if d['documentId'] == ID)
assert ordinal == 1
old = copy.deepcopy(original)
old['documents'] = [copy.deepcopy(selected)]
candidate = copy.deepcopy(old)
sheet = next(s for s in candidate['documents'][0]['sheets'] if s['name'] == '04_内部項目一覧')
assert sheet['role'] == 'list' and sheet['columns'] == 6 and sheet['columnWidths'] == [18, 28, 36, 18, 36, 42]
sheet['columnWidths'][1] = 48
restored = copy.deepcopy(candidate)
next(s for s in restored['documents'][0]['sheets'] if s['name'] == '04_内部項目一覧')['columnWidths'][1] = 28
assert restored == old
paths = {'selectedModel': P / 'model-assisted-search-detail-r18-r02-selected.json',
         'candidateModel': P / 'model-assisted-search-detail-r18-r03-widthonly.json',
         'oldSelectedManifest': P / 'xlsx-search-detail-r18-r02-selected-manifest.json',
         'builder': P / 'build_xlsx_r18_document_ordinal_r03.mjs',
         'receipt': P / 'search-detail-width-r03-preparation.json'}
assert all(not p.exists() for p in paths.values())
manifestpath = P / 'xlsx-assisted-screens-r18-r02/delivery-manifest.json'
manifest = read(manifestpath)
assert manifest['modelSha256'] == sha(originalpath)
selectedmanifest = copy.deepcopy(manifest)
selectedmanifest['documents'] = [copy.deepcopy(next(d for d in manifest['documents'] if d['documentId'] == ID))]
builderpath = P / 'build_xlsx_r18.mjs'
assert sha(builderpath) == 'e6f90d156975a7486c8e968ae449dfa2e329de5d082433da865709f7a87957ed'
code = builderpath.read_text(encoding='utf8')
anchor = "const modelPath=option('--model');const outputRoot=option('--output-root');"
assert code.count(anchor) == 1
code = code.replace(anchor, anchor + "\nconst ordinalText=option('--author-document-ordinal')??'0';\nif(!/^\\d+$/.test(ordinalText))throw new Error('Nonnegative author document ordinal required');\nconst authorDocumentOrdinal=Number(ordinalText);\nif(!Number.isSafeInteger(authorDocumentOrdinal))throw new Error('Author document ordinal outside safe integer range');")
anchor = '`Rows${provenance.documents.length}_'
assert code.count(anchor) == 1
code = code.replace(anchor, '`Rows${authorDocumentOrdinal+provenance.documents.length}_')
anchor = "documents:[],status:'RUNNING',visualReview:'PENDING',authoringMarkerAcknowledged:true};"
assert code.count(anchor) == 1
code = code.replace(anchor, "documents:[],status:'RUNNING',visualReview:'PENDING',authoringMarkerAcknowledged:true,authorDocumentOrdinal};")
paths['selectedModel'].write_text(json.dumps(old, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
paths['candidateModel'].write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
paths['oldSelectedManifest'].write_text(json.dumps(selectedmanifest, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
paths['builder'].write_text(code, encoding='utf8', newline='')
pins = dict(hold['afterHashes'])
pins.update({str(originalpath): sha(originalpath), str(builderpath): sha(builderpath), str(holdpath): sha(holdpath)})
assert all(sha(p) == h for p, h in pins.items())
receipt = {'schema': 'reverse-agent-column-geometry-projection/4', 'createdUtc': datetime.now(timezone.utc).isoformat(),
           'scope': 'ONE_LIST_COLUMN_WIDTH_ONLY_DERIVED_XLSX', 'documentId': ID,
           'markdownSha256': selected['markdownSha256'], 'sheet': sheet['name'], 'columnIndexOneBased': 2,
           'widthBefore': 28, 'widthAfter': 48, 'restoringWidthExactlyEqualsSelectedOriginalModel': True,
           'allBodyLiteralsBlanksRowsMergeStylesTablesImagesSheetOrderUnchanged': True,
           'authorDocumentOrdinal': ordinal, 'technicalTableNamesPreserved': True,
           'builderChange': 'Public Artifact API unchanged; explicit nonnegative document ordinal preserves table technical names after mechanical document selection.',
           'files': {k: {'path': str(p), 'sha256': sha(p)} for k, p in paths.items() if k != 'receipt'},
           'sourcePins': pins, 'allPinnedBytesUnchanged': True, 'actualFullCandidateReview': 'PENDING',
           'oldHoldsPreserved': True, 'businessContentAuthored': False, 'formalApproval': False,
           'wholeDocumentApproval': False, 'adoptionApproval': False, 'published': False}
paths['receipt'].write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps({'receipt': str(paths['receipt']), 'sha256': sha(paths['receipt']), 'files': receipt['files']}, ensure_ascii=False))
