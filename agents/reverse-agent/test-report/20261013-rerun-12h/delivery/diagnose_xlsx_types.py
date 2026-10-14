"""Read saved OOXML scalar types without editing any workbook."""
import json
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
BOOK = ROOT / 'xlsx-search-basic-r02/Excel/基本設計書/01_学生検索画面.xlsx'
NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'

counts, examples = Counter(), []
with ZipFile(BOOK) as archive:
    for name in archive.namelist():
        if name.startswith('xl/worksheets/sheet') and name.endswith('.xml'):
            root = ET.fromstring(archive.read(name))
            for cell in root.findall(f'.//{{{NS}}}sheetData/{{{NS}}}row/{{{NS}}}c'):
                value = cell.find(f'{{{NS}}}v')
                if value is not None and value.text:
                    kind = cell.get('t')
                    counts[str(kind)] += 1
                    if kind not in {'s', 'inlineStr'} and len(examples) < 6:
                        examples.append({'sheetPart': name, 'cell': cell.get('r'), 'type': kind, 'value': value.text[:120], 'formula': cell.find(f'{{{NS}}}f') is not None})
result = {'xlsx': str(BOOK), 'readOnly': True, 'valueTypes': dict(counts), 'examples': examples}
with (ROOT / 'xlsx-types-search-basic-r02.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(result, ensure_ascii=False))
