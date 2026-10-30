"""Independent glyph bounds and page regions; does not infer print acceptance."""
import argparse
import datetime
import json
import pdfplumber
from pathlib import Path
from pdf_observe import SOURCE, owned, record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', action='append', required=True)
    parser.add_argument('--record', required=True)
    args = parser.parse_args()
    output = (SOURCE / args.record).resolve()
    if not output.is_relative_to(SOURCE / 'build/test-results'):
        raise ValueError('Owned test-results output required')
    results = []
    for name in args.pdf:
        path = owned(name)
        before = record(path)
        pages = []
        with pdfplumber.open(path) as document:
            for page in document.pages:
                chars = [c for c in page.chars if c['text'].strip()]
                outside = [c for c in chars if c['x0'] < 0 or c['top'] < 0
                           or c['x1'] > page.width or c['bottom'] > page.height]
                bounds = [min(c['x0'] for c in chars), min(c['top'] for c in chars),
                          max(c['x1'] for c in chars), max(c['bottom'] for c in chars)] if chars else None
                pages.append({'page': page.page_number, 'widthPoints': page.width,
                              'heightPoints': page.height, 'nonWhitespaceChars': len(chars),
                              'glyphBoundsPoints': bounds, 'glyphsOutsideMediaBox': len(outside),
                              'fontSizesPoints': sorted({c['size'] for c in chars}),
                              'headerRegionText': page.crop((0, 0, page.width, 180)).extract_text(),
                              'footerRegionText': page.crop((0, page.height - 80, page.width, page.height)).extract_text()})
        if record(path) != before:
            raise RuntimeError('PDF changed during observation')
        results.append({**before, 'pages': pages})
    value = {'schemaVersion': 1, 'runId': 'sp2-ui-regenerate-20261029', 'profileId': 'Access',
             'recordedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'reader': {'name': 'pdfplumber', 'version': pdfplumber.__version__},
             'regionsPoints': {'headerFromTop': 180, 'footerFromBottom': 80},
             'scope': 'All-page glyph boxes and text regions; no raster or physical print acceptance inferred',
             'measurementSources': [record(Path(__file__).resolve()), record(SOURCE / 'tests/independent/pdf_observe.py')],
             'pdfs': results, 'formalScore': None}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'record': args.record, 'pages': sum(len(r['pages']) for r in results),
                      'glyphsOutsideMediaBox': sum(p['glyphsOutsideMediaBox'] for r in results for p in r['pages'])}))


if __name__ == '__main__':
    main()
