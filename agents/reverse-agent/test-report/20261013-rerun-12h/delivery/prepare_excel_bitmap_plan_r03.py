"""Create a metadata-only read-only Excel plan from verified Artifact output."""
from pathlib import Path
import argparse
import hashlib
import json
import re
from delivery_model_r18 import safe_path

def sha(p): return hashlib.sha256(safe_path(p).read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--document-id', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest_path = safe_path(args.manifest)
    model_path = safe_path(args.model)
    manifest = json.loads(manifest_path.read_text(encoding='utf8'))
    model = json.loads(model_path.read_text(encoding='utf8'))
    assert manifest['status'] == 'MECHANICALLY_VERIFIED_VISUAL_REVIEW_PENDING'
    assert sha(model_path) == manifest['modelSha256']
    document = next(d for d in manifest['documents'] if d['documentId'] == args.document_id)
    original = next(d for d in model['documents'] if d['documentId'] == args.document_id)
    assert sha(document['xlsx']) == document['xlsxSha256']
    assert document['markdownSha256'] == original['markdownSha256']
    expected = [{'sheet':s['name'],'cell':re.fullmatch(r'([A-Z]+\d+):([A-Z]+\d+)',op['range'])[1], 'value':op['value']}
        for s in original['sheets'] for op in s['operations']]
    actual = [{k:c[k] for k in ('sheet','cell','value')} for c in document['writtenCells']]
    assert expected == actual
    expected_ranges = [{'sheet':s['name'],'range':t['range']} for s in original['sheets'] for t in s['previewTiles']]
    actual_ranges = [{k:p[k] for k in ('sheet','range')} for p in document['previews']]
    assert expected_ranges == actual_ranges
    plan = {'workbook':str(safe_path(document['xlsx'])), 'workbookSha256':document['xlsxSha256'],
        'manifest':str(manifest_path), 'manifestSha256':sha(manifest_path), 'model':str(model_path), 'modelSha256':sha(model_path),
        'documentId':args.document_id, 'canonicalDocumentPath':original['canonicalDocumentPath'], 'markdownSha256':original['markdownSha256'],
        'sheets':[s['name'] for s in original['sheets']], 'cells':actual, 'previews':actual_ranges,
        'readOnly':True, 'save':False, 'originalApplicationExecuted':False, 'scope':'STATIC_DERIVED_EXCEL_DISPLAY_ONLY'}
    output = safe_path(args.output)
    assert not output.exists()
    output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'plan':str(output), 'sha256':sha(output), 'cells':len(actual), 'ranges':len(actual_ranges)}, ensure_ascii=False))

if __name__ == '__main__': main()
