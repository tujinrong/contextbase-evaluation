"""Record already-performed pixel review; never generate or edit document text."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
from PIL import Image

HERE = Path(__file__).resolve().parent
REPORT = HERE.parent
RUNTIME = REPORT/'training-assisted/runtime-code-assisted-08.json'
RUNTIME_SHA = 'e899df4800147e4ecb1cf29d5bde52999ac07f074b6b71d34fa7a48e5d9645aa'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    assert sha(RUNTIME) == RUNTIME_SHA
    runtime = json.loads(RUNTIME.read_text(encoding='utf8'))
    frozen = Path(runtime['destination'])
    actual = {p.relative_to(frozen).as_posix(): sha(p) for p in frozen.rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc', '.pyo'}}
    assert actual == runtime['files'] and len(actual) == 126
    cases = [
        ('assisted-search-detail-r03-delivery-r16', 'e7a3b1d5afa45eba33f26f404bec1db29f5f09a77efa0e1ab1bc5c9d9356b80b'),
        ('assisted-registration-basic-r06-delivery-r16', 'ab010f89af473b1f008a345282df4eaaf20cc15d0eb0bd9c2cdd95a1e7017dd7')]
    base = {'schema': 'screen-native-review/1', 'createdUtc': datetime.now(timezone.utc).isoformat(),
            'rendererRuntimeReceipt': str(RUNTIME), 'rendererRuntimeReceiptSha256': RUNTIME_SHA,
            'frozenRuntimeAll126FilesUnchanged': True, 'rendererVersion': 'r16',
            'scope': {'canonicalMarkdownEdited': False, 'originalApplicationExecuted': False,
                      'semanticContentReviewed': False, 'formalRubricEvaluated': False,
                      'stateProjectionIncluded': False, 'wholeQualityApproved': False, 'published': False}}
    for name, pins_sha in cases:
        root = REPORT/'render'/name
        pins_path = root/'render-pins.json'
        assert sha(pins_path) == pins_sha
        pins = json.loads(pins_path.read_text(encoding='utf8'))
        assert pins['rendererRuntimeReceiptSha256'] == RUNTIME_SHA
        assert all(sha(p) == value for p, value in pins['inputPins'].items())
        assert sha(root/pins['canonicalHtmlFilename']) == pins['canonicalHtmlSha256']
        report = dict(base, renderPins=str(pins_path), renderPinsSha256=pins_sha,
                      documentId=pins['documentId'], documentSha256=pins['sourceSha256'],
                      referenceMode=pins['referenceMode'], inputPinsUnchanged=True,
                      diagramCount=len(pins['diagrams']), layoutCount=len(pins['layouts']))
        if 'search-detail' in name:
            inventory_path = REPORT/'visual-review'/(name+'-tiles')/'inventory.json'
            inventory = json.loads(inventory_path.read_text(encoding='utf8'))
            assert inventory['renderPinsSha256'] == pins_sha
            assert len(inventory['captures']) == 26
            seen = []
            for index, record in enumerate(inventory['captures']):
                assert sha(record['path']) == record['sha256']
                assert sha(record['originalPath']) == record['originalSha256']
                rect = record['sourceRectangle']
                with Image.open(record['originalPath']) as original, Image.open(record['path']) as crop:
                    assert list(original.size) == record['wholeOriginalSize']
                    expected = original.crop((rect['x'], rect['y'], rect['x']+rect['width'], rect['y']+rect['height'])).convert('RGBA')
                    assert expected.size == crop.size and expected.tobytes() == crop.convert('RGBA').tobytes()
                assert record['scale'] == 1
                seen.append(dict(record, actuallyReviewed=True, viewedInventoryIndex=index,
                                 reviewMethod='view_image original detail; no preview resizing',
                                 geometryFindings=[]))
            for image in {r['imageId'] for r in seen}:
                strips = sorted((r for r in seen if r['imageId'] == image), key=lambda r:r['sourceRectangle']['y'])
                bottom = 0
                for strip in strips:
                    rect = strip['sourceRectangle']
                    assert rect['x'] == 0 and rect['width'] == strip['wholeOriginalSize'][0]
                    assert rect['y'] <= bottom
                    bottom = max(bottom, rect['y']+rect['height'])
                assert bottom == strips[0]['wholeOriginalSize'][1]
            report.update(status='PASS_NATIVE_GEOMETRY_ONLY', actuallyViewedTileCount=26,
                          actuallyViewedImageCount=23, originalPixelCoverageComplete=True,
                          inventory=str(inventory_path), inventorySha256=sha(inventory_path),
                          captures=seen, findings=[],
                          checked=['whole Latin identifiers and numbers', 'opaque edge labels',
                                   'crop continuity', 'visible node/edge/cluster labels', 'static layout bounds'],
                          pdfScaleReadability='NOT_ASSESSED',
                          pdfScaleCandidates=[{'imageId':'diagram-006','height':2394},
                                              {'imageId':'diagram-009','height':1823},
                                              {'imageId':'diagram-011','height':2322}],
                          limits=['Native pixels were reviewed; actual PDF pages and XLSX tiles remain separate gates.',
                                  'Static layout is an inert illustration, not application execution or approved state projection.'])
        else:
            errors = [{'id':r['id'], 'error':r.get('error')} for r in pins['diagrams'] if r['status'] != 'PASS']
            assert len(errors) == 22 and pins['display']['status'] == 'ERROR'
            report.update(status='FAIL_RENDERER_UNSUPPORTED_VALID_LONG_LABEL', displayErrors=errors,
                          allNativeReviewComplete=False,
                          confirmedTechnicalCause='r16 edge lexer did not parse valid Mermaid dotted long labels; literal mapping gate refused display',
                          example='L -. 読取例外 .-> X',
                          action='Preserve r16 failure and canonical bytes; rerender with separately tested and frozen generic lexer extension.',
                          pdfScaleReadability='NOT_ASSESSED')
        destination = HERE/(name+'-native-qa.json')
        assert not destination.exists()
        destination.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
        print(json.dumps({'path':str(destination), 'sha256':sha(destination), 'status':report['status']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
