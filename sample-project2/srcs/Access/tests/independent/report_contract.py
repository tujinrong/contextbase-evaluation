"""Independent F05 print-contract checks; a string roundtrip is not a printing PASS."""
from pathlib import Path
import argparse, datetime as dt, gc, hashlib, json, re, sys, zipfile
import xml.etree.ElementTree as ET
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
JST = re.compile(r'\d{4}年\d{2}月\d{2}日 \d{2}:\d{2}(?![:\d])')
CHAPTERS = ('職務要約', '活かせる経験・知識・技術', '資格', '自己PR')
FIELDS = ('期間', '所属会社', '会社名', '概要', '業務概要', '担当業務', '担当工程', '工程', '実績・工夫', '成果・工夫', '開発環境', '使用技術', '役割／人数')

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def row_number(address): return int(re.search(r'\d+$', address).group())
def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--workbook', type=Path, default=ROOT / '.tmp/tests/roundtrip-long.xlsx'); parser.add_argument('--companion-workbook', type=Path); parser.add_argument('--excel', action='store_true'); parser.add_argument('--candidate-sha256'); args = parser.parse_args()
    book = args.workbook.resolve(); result = []; page_evidence = []; before = sha(book)
    candidate_before = sha(ROOT / 'build/CareerManagement.accdb')
    if args.candidate_sha256 and candidate_before != args.candidate_sha256.lower(): raise RuntimeError('Candidate differs from the explicitly selected version')
    def check(case, okay, detail): result.append({'id': case, 'status': 'PASS' if okay else 'FAIL', 'detail': detail})
    with zipfile.ZipFile(book) as archive:
        styles = ET.fromstring(archive.read('xl/styles.xml')); fonts = styles.find('s:fonts', NS); formats = styles.find('s:cellXfs', NS)
        shared = ET.fromstring(archive.read('xl/sharedStrings.xml')); texts = [''.join(t.text or '' for t in v.findall('.//s:t', NS)) for v in shared]
        workbook = ET.fromstring(archive.read('xl/workbook.xml')); metadata = list(workbook.find('s:sheets', NS)); sheets = []
        for index, meta in enumerate(metadata, 1):
            sheet = ET.fromstring(archive.read(f'xl/worksheets/sheet{index}.xml')); cells = {}; cell_style = {}
            for cell in sheet.findall('.//s:sheetData/s:row/s:c', NS):
                value = cell.find('s:v', NS)
                text = texts[int(value.text)] if cell.get('t') == 's' and value is not None else ''.join(t.text or '' for t in cell.findall('.//s:t', NS))
                cells[cell.get('r')] = text
                font = fonts[int(formats[int(cell.get('s', '0'))].get('fontId', '0'))]
                bold = font.find('s:b', NS)
                cell_style[cell.get('r')] = {'size': float(font.find('s:sz', NS).get('val')), 'bold': bold is not None and bold.get('val', '1') != '0'}
            merges = {m.get('ref') for m in sheet.findall('s:mergeCells/s:mergeCell', NS)}
            footer = ''.join(x.text or '' for x in sheet.findall('s:headerFooter/s:oddFooter', NS))
            sheets.append({'name': meta.get('name'), 'state': meta.get('state', 'visible'), 'xml': sheet, 'cells': cells, 'styles': cell_style, 'merges': merges, 'footer': footer})
        check('IR-P01-two-visible-sheets', [x['name'] for x in sheets] == ['職務経歴書', '案件経歴'] and all(x['state'] == 'visible' for x in sheets), 'F05 two named visible sheets')
        chapter_rows = []
        for title in CHAPTERS:
            found = [(address, row_number(address)) for address, text in sheets[0]['cells'].items() if text == title]
            okay = len(found) == 1
            detail = {'title': title, 'matches': found}
            if okay:
                address, row = found[0]; chapter_rows.append(row)
                detail.update(style=sheets[0]['styles'][address], headingMerge=f'A{row}:X{row}' in sheets[0]['merges'], bodyMerge=f'A{row+1}:X{row+1}' in sheets[0]['merges'])
                okay = address == f'A{row}' and sheets[0]['styles'][address] == {'size': 11.0, 'bold': True} and detail['headingMerge'] and detail['bodyMerge'] and bool(sheets[0]['cells'].get(f'A{row+1}'))
            check('IR-P02-chapter-' + title, okay, detail)
        for index, sheet in enumerate(sheets, 1):
            stamp = sheet['cells'].get('A4', ''); found = JST.search(stamp)
            check(f'IR-P03-jst-format-{index}', bool(found) and stamp.endswith(found.group()), {'A4': stamp, 'expected': 'yyyy年MM月dd日 HH:mm'})
            plain_footer = re.sub(r'&"[^"]*"|&\d+(?:\.\d+)?|&[LCR]|&K[0-9A-Fa-f]{6}', '', sheet['footer']).replace('\n', '')
            check(f'IR-P04-footer-{index}', bool(found) and '界' * 40 in plain_footer and sheet['name'] in sheet['footer'] and found.group() in sheet['footer'] and '&P' in sheet['footer'] and '&N' in sheet['footer'], {'footer': sheet['footer'], 'required': '最大fixture氏名40字/シート名/取得JST/&P/&N'})
        career = sheets[1]; headings = []
        for address, text in career['cells'].items():
            match = re.match(r'^(\d{2})[ 　]', text)
            if match and '続き' not in text and re.match(r'^[AG]\d+$', address):
                headings.append({'row': row_number(address), 'ordinal': match.group(1), 'text': text, 'style': career['styles'][address]})
        headings.sort(key=lambda x: x['row'])
        check('IR-P05-twenty-11pt-bold-project-headings', len(headings) == 20 and all(x['style'] == {'size': 11.0, 'bold': True} for x in headings), {'count': len(headings), 'examples': headings[:2]})
        print_proofs = [dict(name=s['name'], jst=s['cells'].get('A4'), footer=s['footer'], manualBreakRows=[int(b.get('id')) + 1 for b in s['xml'].findall('s:rowBreaks/s:brk', NS)], chapterRows=chapter_rows if i == 0 else None) for i, s in enumerate(sheets)]
    companion_proofs = []
    if args.excel:
        sys.path.insert(0, str(ROOT / 'tools')); import build
        import win32api, win32event, win32process
        app = None; workbook = None; handle = None; process_id = None; process_exited = False
        build.pythoncom.CoInitialize()
        try:
            app = build.win32com.client.DispatchEx('Excel.Application'); app.Visible = False; app.DisplayAlerts = False; app.EnableEvents = False
            process_id = win32process.GetWindowThreadProcessId(app.Hwnd)[1]; handle = win32api.OpenProcess(0x100000, False, process_id)
            workbook = app.Workbooks.Open(str(book), 0, True)
            for index, sheet in enumerate(sheets, 1):
                ws = workbook.Worksheets(index); ws.Activate(); ws.DisplayPageBreaks = True
                samples = []
                for _ in range(3): samples.append([int(ws.HPageBreaks.Item(i).Location.Row) for i in range(1, ws.HPageBreaks.Count + 1)])
                breaks = samples[-1]
                check(f'IR-P06-measured-break-locations-stable-{index}', samples[0] == samples[1] == samples[2], {'breakRows': breaks, 'source': 'actual Excel HPageBreaks.Location.Row; no printer setting changed'})
                print_range = ws.Range(ws.PageSetup.PrintArea); first_col = int(print_range.Column); last_col = first_col + int(print_range.Columns.Count) - 1
                vertical_samples = []
                for _ in range(3): vertical_samples.append([int(ws.VPageBreaks.Item(i).Location.Column) for i in range(1, ws.VPageBreaks.Count + 1) if first_col < int(ws.VPageBreaks.Item(i).Location.Column) <= last_col])
                columns = vertical_samples[-1]
                try: actual_pages = int(ws.PageSetup.Pages.Count)
                except Exception: actual_pages = None
                geometry = {'printArea': str(ws.PageSetup.PrintArea), 'rangeWidthPoints': float(print_range.Width), 'zoom': ws.PageSetup.Zoom, 'fitToPagesWide': ws.PageSetup.FitToPagesWide, 'fitToPagesTall': ws.PageSetup.FitToPagesTall, 'paperSize': ws.PageSetup.PaperSize, 'leftMarginPoints': float(ws.PageSetup.LeftMargin), 'rightMarginPoints': float(ws.PageSetup.RightMargin), 'breakColumns': columns, 'horizontalPageBands': len(columns) + 1, 'verticalPageBands': len(breaks) + 1, 'estimatedTotalPages': (len(columns) + 1) * (len(breaks) + 1), 'pageSetupPagesCount': actual_pages}
                check(f'IR-P06-horizontal-single-band-{index}', vertical_samples[0] == vertical_samples[1] == vertical_samples[2] and not columns, geometry)
                if index == 1:
                    isolated = [r for r in chapter_rows if any(r < b <= r + 1 for b in breaks)]
                    check('IR-P07-main-heading-first-body-kept', len(chapter_rows) == 4 and not isolated, {'isolatedHeadingRows': isolated})
                else:
                    isolated = []; continuation_failures = []
                    for n, heading in enumerate(headings):
                        start = heading['row']; end = headings[n + 1]['row'] if n + 1 < len(headings) else 10**9
                        period_rows = [row_number(a) for a, text in sheet['cells'].items() if a.startswith('A') and start < row_number(a) < end and text == '期間']
                        if not period_rows or any(start < b <= min(period_rows) for b in breaks): isolated.append(start)
                        # Project name begins in G on the prior layout and A on full-width heading layouts.
                        project_prefix = ''
                        for a, text in sheet['cells'].items():
                            if start <= row_number(a) < min(start + 8, end):
                                match = re.search(r'\d{2}案{2}', text)
                                if match: project_prefix = match.group(); break
                        for boundary in (b for b in breaks if start < b < end):
                            visible = '\n'.join(text for a, text in sheet['cells'].items() if boundary <= row_number(a) < min(boundary + 12, end))
                            if not project_prefix or heading['ordinal'] not in visible or project_prefix not in visible or '続き' not in visible or not any(field in visible for field in FIELDS): continuation_failures.append({'row': boundary, 'ordinal': heading['ordinal'], 'projectPrefix': project_prefix, 'visiblePrefix': visible[:120]})
                    check('IR-P08-project-heading-first-body-kept', len(headings) == 20 and not isolated, {'isolatedHeadingRows': isolated})
                    check('IR-P09-next-page-project-and-field-context', not continuation_failures, {'failures': continuation_failures[:10], 'failureCount': len(continuation_failures), 'fixture': 'maximum 20 projects with 100-scalar project names'})
                page_evidence.append({'sheet': sheet['name'], 'breakRows': breaks, **geometry})
                print_range = None
                ws = None
            workbook.Close(False); workbook = None
            if args.companion_workbook:
                companion = args.companion_workbook.resolve(); companion_before = sha(companion); workbook = app.Workbooks.Open(str(companion), 0, True)
                for index in (1, 2):
                    ws = workbook.Worksheets(index); ws.Activate(); ws.DisplayPageBreaks = True; area = ws.Range(ws.PageSetup.PrintArea); first_col = int(area.Column); last_col = first_col + int(area.Columns.Count) - 1
                    hs = []; vs = []
                    for _ in range(3):
                        hs.append([int(ws.HPageBreaks.Item(i).Location.Row) for i in range(1, ws.HPageBreaks.Count + 1)])
                        vs.append([int(ws.VPageBreaks.Item(i).Location.Column) for i in range(1, ws.VPageBreaks.Count + 1) if first_col < int(ws.VPageBreaks.Item(i).Location.Column) <= last_col])
                    pages = int(ws.PageSetup.Pages.Count); expected_pages = (len(hs[-1]) + 1) * (len(vs[-1]) + 1)
                    geometry = {'sheet': str(ws.Name), 'breakRows': hs[-1], 'breakColumns': vs[-1], 'verticalPageBands': len(hs[-1]) + 1, 'horizontalPageBands': len(vs[-1]) + 1, 'estimatedTotalPages': expected_pages, 'pageSetupPagesCount': pages, 'rangeWidthPoints': float(area.Width), 'zoom': ws.PageSetup.Zoom}
                    check(f'IR-P11-normal-horizontal-and-page-count-{index}', hs[0] == hs[1] == hs[2] and vs[0] == vs[1] == vs[2] and not vs[-1] and pages == expected_pages, geometry)
                    companion_proofs.append({'workbook': str(companion.relative_to(ROOT)).replace('\\', '/'), 'workbookSha256': companion_before, 'workbookUnchanged': companion_before == sha(companion), **geometry}); area = None; ws = None
                workbook.Close(False); workbook = None
                check('IR-P11-normal-workbook-unchanged', companion_before == sha(companion), {'workbookSha256': companion_before})
            app.Quit(); app = None
        except Exception as error:
            check('IR-P-EXCEL-API', False, type(error).__name__ + ': ' + str(error))
        finally:
            if workbook is not None:
                try: workbook.Close(False)
                except Exception: pass
            workbook = None
            if app is not None:
                try: app.Quit()
                except Exception: pass
            app = None; gc.collect(); build.release(); build.pythoncom.CoUninitialize()
            if handle is not None: process_exited = win32event.WaitForSingleObject(handle, 5000) == 0; handle.Close()
        check('IR-P10-owned-excel-exited', process_exited, {'ownedExcelPid': process_id})
    repo = ROOT.parents[2]; spec = repo / 'sample-project2/spec/Access'
    specs = [spec / '詳細仕様書/05_経歴書出力.md', spec / '基本設計書/05_経歴書出力.md', spec / '共通/方式別/01_共通実装仕様.md']
    record = {'status': 'PASS' if all(x['status'] == 'PASS' for x in result) and before == sha(book) and candidate_before == sha(ROOT / 'build/CareerManagement.accdb') else 'FAIL', 'reviewer': '/root/req_desktop', 'reviewedAtUtc': dt.datetime.now(dt.timezone.utc).isoformat(), 'workbook': str(book.relative_to(ROOT)).replace('\\', '/'), 'workbookSha256': before, 'workbookUnchanged': before == sha(book), 'candidateArtifactSha256': candidate_before, 'candidateUnchanged': candidate_before == sha(ROOT / 'build/CareerManagement.accdb'), 'artifactAssociation': 'Explicitly selected candidate plus author-notified matching workbook' if args.candidate_sha256 else 'Contextual current candidate; workbook is independently fixed by its own SHA', 'testSourceSha256': sha(Path(__file__)), 'specInputs': [{'path':str(p.relative_to(repo)).replace('\\','/'),'sha256':sha(p)} for p in specs], 'checks': result, 'printProofs': print_proofs, 'actualExcelPageEvidence': page_evidence, 'scope': 'Maximum fixture (40-scalar name/100-scalar project names/20 careers): OOXML font/merge/JST/footer contracts; optional actual private Excel measured page-break locations and continuation context. This does not replace PDF/printed-page visual review or full-text proof.', 'notPerformed': ['PDF/printed-page visual review by this reviewer', 'Complete F05 fault/permission/overwrite/cancellation matrix', 'User acceptance/formal scoring'] + ([] if args.excel else ['Actual Excel page-break API']), 'formalScore': None}
    record['companionExcelPageEvidence'] = companion_proofs
    record['apiReferences'] = [
        {'url': 'https://learn.microsoft.com/en-us/office/vba/api/excel.hpagebreaks', 'usedFor': 'Print-area-dependent horizontal break collection; compare locations, not only Count.'},
        {'url': 'https://learn.microsoft.com/en-us/office/vba/api/excel.hpagebreak.location', 'usedFor': 'Location Range top edge defines horizontal page boundary.'},
        {'url': 'https://learn.microsoft.com/en-us/office/vba/api/excel.vpagebreaks', 'usedFor': 'Horizontal1page requires no vertical page break inside the explicit print area; HPageBreaks alone are insufficient.'},
        {'url': 'https://learn.microsoft.com/en-us/office/vba/excel/concepts/workbooks-and-worksheets/formatting-and-vba-codes-for-headers-and-footers', 'usedFor': 'Literal captured JST versus dynamic date/time fields; sheet/page formatting codes.'}
    ]
    output = ROOT / 'build/test-results/independent-review/print-contract.json'; output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(record, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'status': record['status'], 'checks': len(result), 'failed': [x['id'] for x in result if x['status'] != 'PASS'], 'workbookSha256': before}, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1

if __name__ == '__main__': raise SystemExit(main())
