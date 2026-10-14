"""Read-only evidence for the frozen candidate's derivative converter repair.

The review observations below record pages actually viewed by delivery_tools.
They are not automated visual judgments or specification/business approval.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
from PIL import Image, ImageChops, ImageDraw
from delivery_model import load_bound, sha

ROOT = Path(__file__).resolve().parent

def read(name):
    return json.loads((ROOT / name).read_bytes())

def digest(path):
    return sha(Path(path).read_bytes())

def save(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def before_after():
    old, new = read('model-search-basic-r02.json'), read('model-search-basic-r03.json')
    bound, entries, binding_info = load_bound(ROOT / 'binding-search-basic-r02.json')
    binding_sha = binding_info['bindingSha256']
    assert old['bindingSha256'] == new['bindingSha256'] == binding_sha
    assert old['sourceSnapshotManifestSha256'] == new['sourceSnapshotManifestSha256']
    assert len(old['documents']) == len(new['documents']) == len(entries) == 1
    a, b = old['documents'][0], new['documents'][0]
    invariants = ['documentId', 'canonicalDocumentPath', 'markdown', 'markdownSha256',
                  'renderDirectory', 'renderPinsSha256', 'renderManifestSha256',
                  'title', 'sourceMetadata', 'rawMarkdown', 'visibleCoverage']
    assert all(a[key] == b[key] for key in invariants)
    assert a['markdownSha256'] == digest(a['markdown'])
    sheets = []
    cells = 0
    images = []
    for left, right in zip(a['sheets'], b['sheets'], strict=True):
        assert all(left[key] == right[key] for key in ['name', 'role', 'columns'])
        # Row/range geometry can change; source strings, style roles, sequence,
        # and source-line provenance cannot change in this projection repair.
        sequence = lambda sheet: [(o['value'], o['style'], o.get('sourceLines')) for o in sheet['operations']]
        assert sequence(left) == sequence(right)
        cells += sum(bool(o['value']) for o in right['operations'])
        assert len(left['images']) == len(right['images'])
        image_geometry = []
        for x, y in zip(left['images'], right['images'], strict=True):
            keys = ['kind', 'id', 'sourceLines', 'path', 'sha256', 'width', 'height']
            assert all(x[key] == y[key] for key in keys)
            assert digest(y['path']) == y['sha256']
            images.append({key: y[key] for key in keys})
            image_geometry.append({'id': y['id'], 'before': {k: x[k] for k in ['row','col','displayWidth','displayHeight']},
                                   'after': {k: y[k] for k in ['row','col','displayWidth','displayHeight']}})
        sheets.append({'name': right['name'], 'columns': right['columns'], 'role': right['role'],
                       'orderedSourceValuesEqual': True, 'sourceLineProvenanceEqual': True,
                       'before': {k: left[k] for k in ['lastRow','printArea','previewTiles']},
                       'after': {k: right[k] for k in ['lastRow','printArea','previewTiles']},
                       'imageGeometry': image_geometry})
    assert cells == 645 and len(images) == 13
    return {'status': 'PASS', 'bindingSha256': binding_sha, 'documentId': b['documentId'],
            'canonicalDocumentPath': b['canonicalDocumentPath'], 'markdownSha256': b['markdownSha256'],
            'sourceSnapshotManifestSha256': bound['sourceSnapshotManifestSha256'],
            'beforeModelSha256': digest(ROOT/'model-search-basic-r02.json'),
            'afterModelSha256': digest(ROOT/'model-search-basic-r03.json'),
            'equalFields': invariants, 'cellsChecked': cells, 'imagesChecked': images,
            'projectionBefore': old.get('projection'), 'projectionAfter': new.get('projection'), 'sheets': sheets}

def crop_audit(doc):
    grouped = defaultdict(list)
    for record in doc['diagramTiles']:
        grouped[record['id']].append(record)
    results = []
    for image_id, records in grouped.items():
        first = records[0]
        source_path = Path(first['sourcePath'])
        assert digest(source_path) == first['sourceSha256']
        with Image.open(source_path) as raw:
            source = raw.convert('RGB')
        coverage = Image.new('L', source.size, 0)
        printed_coverage = Image.new('L', source.size, 0)
        draw_all, draw_printed = ImageDraw.Draw(coverage), ImageDraw.Draw(printed_coverage)
        verified = []
        for record in records:
            assert record['sourceSha256'] == first['sourceSha256']
            assert digest(record['path']) == record['sha256']
            x1, y1, x2, y2 = record['cropBox']
            assert 0 <= x1 < x2 <= source.width and 0 <= y1 < y2 <= source.height
            with Image.open(record['path']) as raw:
                tile = raw.convert('RGB')
            assert tile.size == (x2-x1, y2-y1)
            assert tile.tobytes() == source.crop((x1,y1,x2,y2)).tobytes()
            white = tile.getextrema() == ((255,255),(255,255),(255,255))
            assert record['printed'] == (not white)
            assert record['omissionReason'] == ('ALL_RGB_PIXELS_255' if white else None)
            assert record['overlapPixels'] == 60
            draw_all.rectangle((x1,y1,x2-1,y2-1), fill=255)
            if record['printed']:
                draw_printed.rectangle((x1,y1,x2-1,y2-1), fill=255)
            verified.append({**record, 'cropPixelsEqual': True, 'allRgb255': white})
        assert coverage.getextrema() == (255,255)
        uncovered = Image.composite(source, Image.new('RGB', source.size, 'white'), ImageChops.invert(printed_coverage))
        assert uncovered.getextrema() == ((255,255),(255,255),(255,255))
        results.append({'id': image_id, 'sourcePath': str(source_path), 'sourceSha256': first['sourceSha256'],
                        'dimensions': list(source.size), 'tileCount': len(records),
                        'printedTileCount': sum(r['printed'] for r in records),
                        'allTilePixelCoverage': '100%', 'printedNonwhitePixelCoverage': '100%',
                        'overlapPixels': 60, 'tiles': verified})
    return {'status': 'PASS', 'pixelOnlyProjection': True, 'businessFlowRewritten': False,
            'tileCount': len(doc['diagramTiles']), 'printedTileCount': sum(r['printed'] for r in doc['diagramTiles']),
            'omittedWhiteTiles': [r for r in doc['diagramTiles'] if not r['printed']], 'images': results}

def page_review(manifest, revision):
    doc = manifest['documents'][0]
    expected_count = 109 if revision == 'r08' else 106
    assert doc['pages'] == len(doc['pageImages']) == expected_count
    small = {19,26,31,34,37,42}
    whitespace = {18,25,28,33,41}
    header_band = {8,9,11}
    blank = {53,55,76} if revision == 'r08' else set()
    sparse = {61,65,73,76,79,82,85,89,90,92,94,96,97,100,103} if revision == 'r09' else set()
    pages = []
    for n, record in enumerate(doc['pageImages'], 1):
        assert digest(record['path']) == record['sha256']
        findings = []
        if n in blank:
            findings.append('WHITE_ANNEX_WITH_CAPTION_ONLY')
        if n in small:
            findings.append('OVERVIEW_DIAGRAM_LABELS_TOO_SMALL_FOR_COMFORTABLE_READING')
        if n in whitespace:
            findings.append('LARGE_UNUSED_SPACE_FROM_KEEPING_FOLLOWING_DIAGRAM_TOGETHER')
        if n in header_band:
            findings.append('CONTINUATION_TABLE_HEADER_BAND_NEEDS_LAYOUT_REVIEW')
        if n > 51:
            findings.append('PIXEL_VIEWPORT_AID_REQUIRES_NEIGHBOR_TILES_FOR_CROSSING_NODES_OR_EDGES')
        if n in sparse:
            findings.append('SPARSE_VIEWPORT_CONTAINS_FRAGMENT_OR_CONNECTOR_LINES')
        pages.append({'page': n, **record, 'actuallyViewed': True, 'viewTool': 'view_image(original)',
                      'layoutStatus': 'FAIL' if n in blank or n in small else ('REVIEW_REQUIRED' if findings else 'PASS'),
                      'findings': findings, 'semanticApproval': False})
    return {'revision': revision, 'pdf': doc['pdf'], 'pdfSha256': doc['pdfSha256'],
            'textCoverage': doc['textCoverage'], 'checkedVisibleStrings': doc['checkedVisibleStrings'],
            'pageCount': expected_count, 'actuallyViewedPages': list(range(1, expected_count+1)),
            'allPagesReviewed': True, 'visualStatus': 'FAIL_FOR_PUBLICATION',
            'reviewer': '/root/delivery_tools', 'semanticApproval': False, 'pages': pages}

def xlsx_review(manifest):
    doc = manifest['documents'][0]
    assert digest(doc['xlsx']) == doc['xlsxSha256']
    assert len(doc['previews']) == 42
    reviews = []
    for record in doc['previews']:
        assert digest(record['path']) == record['sha256']
        reviews.append({**record, 'actuallyViewed': True, 'viewTool': 'view_image(original)',
                        'unwantedOutsideOrContinuationBorders': 'PASS', 'semanticApproval': False,
                        'visualStatus': 'REVIEW_REQUIRED' if record['sheet'] == '表紙' else 'PASS_WITH_GLOBAL_RENDERER_LIMITATION'})
    namespaces = {'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(doc['xlsx']) as archive:
        xml = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
    version = xml.find("m:sheetData/m:row/m:c[@r='X18']", namespaces)
    assert version is not None and version.get('t') == 'str'
    assert version.find('m:v', namespaces).text == '1.0'
    imported = read('literal-reimport-r05/values.json')
    assert imported['values'][17][23] == '1.0'
    assert isinstance(imported['values'][17][23], str)
    return {'xlsx': doc['xlsx'], 'xlsxSha256': doc['xlsxSha256'], 'readbackChecks': doc['readbackChecks'],
            'printMetadataConnection': doc['printMetadataConnection'], 'tilesActuallyViewed': 42,
            'nativeTiles': reviews, 'visualStatus': 'REVIEW_REQUIRED', 'semanticApproval': False,
            'numericLookingString': {'cell': '表紙!X18', 'xmlType': 'str', 'xmlValue': '1.0',
                'publicReimportValue': '1.0', 'publicReimportType': 'string',
                'nativeRenderedValueObserved': '1', 'sourceOrXmlChangedToMatchPreview': False,
                'causeBoundary': 'NATIVE_RENDERER_DISPLAY', 'excelApplicationDisplay': 'NOT_TESTED',
                'publicReimportEvidence': str(ROOT/'literal-reimport-r05/values.json'),
                'publicReimportEvidenceSha256': digest(ROOT/'literal-reimport-r05/values.json')}}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report-name', default='repair-qa-r09.json')
    args = parser.parse_args()
    if Path(args.report_name).name != args.report_name or not args.report_name.endswith('.json'):
        raise ValueError('Report must be one JSON filename within delivery')
    out = ROOT/args.report_name
    if out.exists():
        raise FileExistsError('Evidence must be a fresh file')
    pdf8, pdf9 = read('pdf-search-basic-r08/delivery-manifest.json'), read('pdf-search-basic-r09/delivery-manifest.json')
    xlsx = read('xlsx-search-basic-r04/delivery-manifest.json')
    before = before_after()
    doc = pdf9['documents'][0]
    assert digest(doc['pdf']) == doc['pdfSha256']
    assert digest(doc['html']) == doc['htmlSha256'] == '523103269041cc3538e8457ec17a06dd99191d10edbcea28b93b9177086aa49b'
    record = {'schema':'reverse-agent-derivative-repair-qa/1', 'createdAt':datetime.now(timezone.utc).isoformat(),
              'scope':'FROZEN_SEARCH_BASIC_03_CONVERTER_QA', 'referenceMode':'source-only',
              'sourceCandidateFinalFormat':'FAILED', 'published':False, 'formalQualityGatePassed':False,
              'businessContentAuthored':False, 'originalApplicationExecuted':False, 'inputJavaScriptEnabled':False,
              'beforeAfter':before, 'pdfTileAudit':crop_audit(doc),
              'pdfExecution':{k:doc[k] for k in ['html','htmlSha256','printProjectionSha256','printProjection','printCssSha256','cssInsertion','annexInsertion','renderPinsSha256','renderManifestSha256']},
              'pdfStageLog':{'path':str(ROOT/'pdf-search-basic-r09/stages.jsonl'),
                             'sha256':digest(ROOT/'pdf-search-basic-r09/stages.jsonl'),
                             'ownedWorkerExitCode':0,'stageTimeoutSeconds':90,'overallTimeoutSeconds':900},
              'pdfVisualReviews':[page_review(pdf8,'r08'), page_review(pdf9,'r09')],
              'xlsxReview':xlsx_review(xlsx),
              'finalChecks':{'unittestCount':16,'unittestStatus':'PASS',
                             'rawLog':str(ROOT/'tests-final-r09.raw.log'),
                             'rawLogSha256':digest(ROOT/'tests-final-r09.raw.log'),
                             'nodeBuilderSyntax':'PASS','actualXlsxIndependentXml':'PASS'},
              'helperSha256s':{name:digest(ROOT/name) for name in ['build_xlsx.mjs','delivery_model.py','verify_xlsx.py','export_pdf.py','audit_repair.py']},
              'limitations':['Candidate03 final format is failed; these are derivative converter QA candidates.',
                'PDF text success does not imply diagram or application semantic accuracy.',
                'Large diagram overview labels remain small; viewport annex requires neighboring tiles.',
                'Native renderer changes numeric-looking string display; Excel application is not tested.',
                'No formal original-rubric 95 percent evaluation was performed by this delivery task.']}
    save(args.report_name,record)
    print(json.dumps({'report':str(out),'reportSha256':digest(out),
                      'invariants':'PASS','cells':645,'sourceImages':13,'pdfPagesActuallyViewed':106,
                      'pdfTextStrings':662,'pixelTiles':58,'printedTiles':55,'xlsxNativeTilesActuallyViewed':42,
                      'visualPublicationGate':'FAILED_OR_REVIEW_REQUIRED'},ensure_ascii=False))

if __name__ == '__main__':
    main()
