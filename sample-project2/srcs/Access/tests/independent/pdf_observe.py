"""Read owned PDF text/font geometry; observations alone are not report acceptance."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import sys

sys.dont_write_bytecode = True
import pypdf

SOURCE = Path(__file__).resolve().parents[2]


def owned(name):
    path = (SOURCE / name).resolve(strict=True)
    if not path.is_relative_to(SOURCE) or not path.is_file():
        raise ValueError('An existing owned file is required')
    return path


def record(path):
    return {'file': path.relative_to(SOURCE).as_posix(),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'bytes': path.stat().st_size}


def observe(path):
    before = record(path)
    pages = []
    for number, page in enumerate(pypdf.PdfReader(path).pages, 1):
        spans = []

        def visitor(text, cm, tm, font, size):
            if text.strip():
                spans.append({'text': text.strip(), 'fontSpacePoints': size,
                              'currentMatrix': list(cm), 'textMatrix': list(tm),
                              'fontName': str((font or {}).get('/BaseFont', ''))})

        text = page.extract_text(visitor_text=visitor)
        pages.append({'page': number, 'mediaBoxPoints': [float(v) for v in page.mediabox],
                      'text': text, 'spans': spans})
    if record(path) != before:
        raise RuntimeError('PDF changed while being inspected')
    return {**before, 'pages': pages}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', action='append', required=True)
    parser.add_argument('--record', required=True)
    args = parser.parse_args()
    output = (SOURCE / args.record).resolve()
    if not output.is_relative_to(SOURCE / 'build/test-results'):
        raise ValueError('Record must remain under owned build/test-results')
    value = {'schemaVersion': 1, 'projectId': 'sample-project2', 'profileId': 'Access',
             'runId': 'sp2-ui-regenerate-20261029',
             'recordedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'scope': 'Independent PDF text/font observations; no workbook or product acceptance inferred',
             'productPass': False, 'formalScore': None,
             'reader': {'name': 'pypdf', 'version': pypdf.__version__},
             'measurementSources': [record(Path(__file__).resolve())],
             'arguments': {'pdf': args.pdf}, 'pdfs': [observe(owned(name)) for name in args.pdf]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'record': args.record, 'pdfs': len(value['pdfs']), 'productPass': False}))


if __name__ == '__main__':
    main()
