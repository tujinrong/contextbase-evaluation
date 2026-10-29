"""Read-only OOXML palette/table-line checks for the selected Access F05 maximum fixture."""
from pathlib import Path
import argparse, datetime as dt, hashlib, json, re, sys, zipfile
import xml.etree.ElementTree as ET
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
CHAPTERS = {'職務要約', '活かせる経験・知識・技術', '資格', '自己PR'}
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('workbook', type=Path); args = parser.parse_args(); workbook = args.workbook.resolve(); before = sha(workbook)
    with zipfile.ZipFile(workbook) as archive:
        styles = ET.fromstring(archive.read('xl/styles.xml')); borders = list(styles.find('s:borders', NS)); formats = list(styles.find('s:cellXfs', NS)); fonts = list(styles.find('s:fonts', NS)); fills = list(styles.find('s:fills', NS))
        shared = [''.join(t.text or '' for t in item.findall('.//s:t', NS)) for item in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        sheets = []; bad_font_fill = []
        for index in (1, 2):
            rows = {}
            for row in ET.fromstring(archive.read(f'xl/worksheets/sheet{index}.xml')).findall('.//s:sheetData/s:row', NS):
                cells = {}; colors = set()
                for cell in row.findall('s:c', NS):
                    address = cell.get('r'); value = cell.find('s:v', NS); text = shared[int(value.text)] if cell.get('t') == 's' and value is not None else ''
                    cells[re.sub(r'\d', '', address)] = text
                    style = formats[int(cell.get('s', '0'))]; border = borders[int(style.get('borderId', '0'))]
                    for side in border:
                        color = side.find('s:color', NS)
                        if side.get('style') and color is not None and color.get('rgb'): colors.add(color.get('rgb')[-6:].lower())
                    if text:
                        font = fonts[int(style.get('fontId', '0'))]; fill = fills[int(style.get('fillId', '0'))].find('s:patternFill', NS)
                        name = font.find('s:name', NS).get('val'); size = float(font.find('s:sz', NS).get('val')); white = fill is None or fill.get('patternType', 'none') == 'none' or fill.get('patternType') == 'solid' and fill.find('s:fgColor', NS) is not None and fill.find('s:fgColor', NS).get('rgb', '')[-6:].lower() == 'ffffff'
                        if name not in ('Meiryo', 'メイリオ') or size not in (10.5, 11, 18) or not white: bad_font_fill.append({'sheet': index, 'cell': address, 'font': name, 'size': size, 'white': white})
                rows[int(row.get('r'))] = {'cells': cells, 'colors': colors}
            sheets.append(rows)
        missing_navy = []; heading_count = 0; missing_gray = []; table_count = 0
        for index, rows in enumerate(sheets, 1):
            for number, row in rows.items():
                label = row['cells'].get('A', '')
                if label in CHAPTERS or re.fullmatch(r'\d{2} 案件', label):
                    heading_count += 1; end = number
                    while rows.get(end + 1, {}).get('cells', {}).get('A') == label + '（続き）': end += 1
                    if not any('173650' in rows[r]['colors'] for r in range(number, end + 1)): missing_navy.append({'sheet': index, 'row': number, 'label': label})
                if label in {'氏名', '社員番号／所属', '期間', '会社名', '業務概要', '担当業務', '担当工程', '成果・工夫', '使用技術', '役割／人数'}:
                    table_count += 1
                    if 'aeb8c5' not in row['colors']: missing_gray.append({'sheet': index, 'row': number, 'label': label})
    checks = [{'id': 'IR-FORMAT-navy-heading-lines', 'status': 'PASS' if heading_count == 24 and not missing_navy else 'FAIL', 'headingCount': heading_count, 'missing': missing_navy}, {'id': 'IR-FORMAT-gray-table-outlines', 'status': 'PASS' if table_count == 2 + 8 * 20 and not missing_gray else 'FAIL', 'tableCount': table_count, 'expectedTableCount': '2 cover fields + 8 body fields for each of20 projects', 'missing': missing_gray}, {'id': 'IR-FORMAT-white-paper-meiryo-fonts', 'status': 'PASS' if not bad_font_fill else 'FAIL', 'invalid': bad_font_fill}]
    record = {'status': 'PASS' if all(x['status'] == 'PASS' for x in checks) and sha(workbook) == before else 'FAIL', 'reviewer': '/root/req_desktop', 'reviewedAtUtc': dt.datetime.now(dt.timezone.utc).isoformat(), 'workbookSha256': before, 'workbookUnchanged': sha(workbook) == before, 'testSourceSha256': sha(Path(__file__)), 'checks': checks, 'scope': 'Selected Access F05 maximum fixture: actual used-cell borders/colors, whole chapter/project heading blocks, white paper/Meiryo nominal font sizes. No Office instance or PDF visual claim.', 'formalScore': None}
    output = ROOT / 'build/test-results/independent-review/print-format.json'; output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(record, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'status': record['status'], 'checks': len(checks), 'failed': [x['id'] for x in checks if x['status'] != 'PASS'], 'workbookSha256': before})); return 0 if record['status'] == 'PASS' else 1

if __name__ == '__main__': raise SystemExit(main())
