"""Independent read-back checks for the Staff pilot; no application execution."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile
from xml.etree import ElementTree as ET

S='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'


def review(root: Path) -> dict:
    status_file=root/'report/pilot/status.json'
    status=json.loads(status_file.read_text()) if status_file.exists() else {}
    if not status.get('pilot_applied'):
        result={'status':'not_applicable','scope':'No unchanged reviewed Staff pilot was selected.'}
    else:
        path=root/'output/Excel/基本設計書/基本設計書_100008_職員番号入力.xlsx'
        fixture=json.loads((root/'src/docsite/v2/reference_format.json').read_text(encoding='utf-8'))
        checks=[]
        def check(label,condition):
            checks.append({'check':label,'pass':bool(condition)})
        with zipfile.ZipFile(path) as z:
            book=ET.fromstring(z.read('xl/workbook.xml'))
            sheets=book.find(f'{{{S}}}sheets')
            check('V2 five-sheet order',[s.attrib['name'] for s in sheets]==fixture['sheet_names'])
            alltext='';cell_count=0;item_rows=[]
            for i,sheet in enumerate(sheets,1):
                node=ET.fromstring(z.read(f'xl/worksheets/sheet{i}.xml'))
                cells={c.attrib['r']:''.join(c.find(f'{{{S}}}is').itertext()) for c in node.findall(f'.//{{{S}}}c') if c.find(f'{{{S}}}is') is not None}
                alltext+='\n'.join(cells.values());cell_count+=sum(bool(v) for v in cells.values())
                check(sheet.attrib['name']+' literal values',not node.findall(f'.//{{{S}}}f'))
                merges=[m.attrib['ref'] for m in node.findall(f'{{{S}}}mergeCells/{{{S}}}mergeCell')]
                if i==1:check('V2 cover cell anchors',set(merges)==set(fixture['sheets']['表紙']['merges']))
                elif sheet.attrib['name']!='項目一覧':check(sheet.attrib['name']+' 62-column header','A1:J1' in merges and 'BE1:BJ1' in merges)
                else:
                    headers=['No','グループ','項目名','種類','入出力','DB連携項目','候補取得元','必須','形式・桁','説明']
                    check('ten item headers at row 2',[cells.get(chr(65+c)+'2') for c in range(10)]==headers)
                    item_rows=[[cells.get(chr(65+c)+str(r),'') for c in range(10)] for r in range(3,7)]
                    check('four source-derived items',[row[0] for row in item_rows]==['1','2','3','4'])
                    check('no copied logout control',not any('ログアウト' in row[2] for row in item_rows))
                    check('required staff number',item_rows[1][4]=='I／O' and item_rows[1][7]=='必須')
            images=[n for n in z.namelist() if n.startswith('xl/media/')]
            check('two embedded images',len(images)==2)
            normalized=re.sub(r'\s+','',alltext)
            for phrase in ['HTTP204','メニュー画面へ遷移する処理ではない','既存のセッション職員情報は更新・削除しない','8時間','物理DBテーブルを参照・更新しない']:
                check('content: '+phrase,phrase in normalized)
        result={'status':'pass' if all(c['pass'] for c in checks) else 'fail','checks':checks,'checks_count':len(checks),'sheets':len(sheets),'checked_nonempty_cells':cell_count,'embedded_images':len(images),
                'xlsx_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'scope':'Independent ZIP/XML read-back and source-reviewed contract checks. Not a native application, DB, or Microsoft Excel print-equivalence test.'}
    report=root/'report/pilot';report.mkdir(parents=True,exist_ok=True)
    (report/'evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));a=p.parse_args()
    result=review(a.root.resolve());print(json.dumps(result,ensure_ascii=False,indent=2))
    return int(result['status']=='fail')

if __name__=='__main__':raise SystemExit(main())
