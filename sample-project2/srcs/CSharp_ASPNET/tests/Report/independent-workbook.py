"""Verify live browser downloads independently through Open XML, without the generator."""
from pathlib import Path
import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'build/test-results/independent-browser'
NS={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/package/2006/relationships'}
checks=[]
for name in ['seed-career','literal-career']:
    file=AREA/(name+'.xlsx')
    with ZipFile(file) as archive:
        names=archive.namelist()
        assert not any(re.search(r'vbaProject|externalLinks|connections',entry,re.I) for entry in names)
        workbook=ET.fromstring(archive.read('xl/workbook.xml'))
        sheets=workbook.findall('x:sheets/x:sheet',NS)
        assert [sheet.attrib['name'] for sheet in sheets]==['職務経歴書','案件経歴']
        assert all(sheet.attrib.get('state','visible')=='visible' for sheet in sheets)
        strings=[]
        if 'xl/sharedStrings.xml' in names:
            strings=[''.join(node.itertext()) for node in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('x:si',NS)]
        values=[]
        for sheet in ['xl/worksheets/sheet1.xml','xl/worksheets/sheet2.xml']:
            doc=ET.fromstring(archive.read(sheet))
            assert not doc.findall('.//x:f',NS),'Formula cells are forbidden'
            for cell in doc.findall('.//x:c',NS):
                value=cell.find('x:v',NS)
                if cell.attrib.get('t')=='s' and value is not None:
                    values.append(strings[int(value.text)])
                elif cell.attrib.get('t')=='inlineStr':
                    values.append(''.join(cell.find('x:is',NS).itertext()))
                elif value is not None:
                    assert not value.text,'Report values must be text'
            page=doc.find('x:pageSetup',NS)
            assert page is not None and page.attrib.get('paperSize')=='9' and page.attrib.get('orientation')=='portrait'
            margins=doc.find('x:pageMargins',NS)
            assert margins is not None
            assert all(abs(float(margins.attrib[edge])-15/25.4)<0.001 for edge in ['left','right','top','bottom'])
        for entry in names:
            if entry.endswith('.rels'):
                assert not any(r.attrib.get('TargetMode')=='External' for r in ET.fromstring(archive.read(entry)))
        assert any(re.match(r'^0\d{5} ／',value) for value in values),'Leading-zero employee number lost'
        if name=='literal-career':
            for value in ['=1+1',"'原文 😀","'先頭文字",'+C#','@設計']:
                assert value in values,'Literal or supplementary text changed'
            assert values.count('=1+1')==2 and values.count("'原文 😀")==2,'Paragraphs or original LF boundaries lost'
        checks.append(dict(file=file.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(file.read_bytes()).hexdigest(),status='PASS',sheets=2,textCells=len(values),scope='Actual browser download: sheet names/count, text values, formulas, macros/external links, leading zero, literal prefixes, LF and supplementary Unicode, A4/margins'))
record=dict(status='PASS',reviewer='/root',runId=os.environ.get('SP2_RUN_ID','20261029-sp2-build'),checks=checks,notExecuted=['Visual print layout; recorded separately using real Excel PDF export','Formal acceptance/scoring'],formalScore=None)
(AREA/'workbook-review.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=record['status'],workbooks=len(checks)),ensure_ascii=False))
