"""Independently read native Excel PDFs; never edits a workbook or invokes Office."""
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
from zipfile import ZipFile
import hashlib,json,re,sys,xml.etree.ElementTree as ET
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'build/test-results/print-review'
RECORD=AREA/'record.json'
NS={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def compact(t): return re.sub(r'\s+','',t)
def values(file):
    with ZipFile(file) as book:
        shared=[]
        if 'xl/sharedStrings.xml' in book.namelist():
            shared=[''.join(n.itertext()) for n in ET.fromstring(book.read('xl/sharedStrings.xml')).findall('x:si',NS)]
        found=[]
        for name in ['xl/worksheets/sheet1.xml','xl/worksheets/sheet2.xml']:
            for cell in ET.fromstring(book.read(name)).findall('.//x:c',NS):
                value=cell.find('x:v',NS)
                if cell.attrib.get('t')=='s' and value is not None:found.append(shared[int(value.text)])
                elif cell.attrib.get('t')=='inlineStr':found.append(''.join(cell.find('x:is',NS).itertext()))
        return [t for t in found if t.strip()]
record=json.loads(RECORD.read_text(encoding='utf-8-sig'))
assert record['status']=='EXPORTED_FOR_INDEPENDENT_VISUAL_REVIEW'
checks=[]
try:
    assert record['excel']['cleanExit'] and record['excel']['exitCode']==0
    for item in record['records']:
        workbook=ROOT/item['workbook'];pdf=ROOT/item['pdf']
        assert sha(workbook)==item['workbookSha256'] and sha(pdf)==item['pdfSha256']
        reader=PdfReader(pdf,strict=True)
        assert len(reader.pages)==item['pages']
        page_text=[]
        for index,page in enumerate(reader.pages,1):
            assert abs(float(page.mediabox.width)-595.28)<2 and abs(float(page.mediabox.height)-841.89)<2,'Native PDF is not A4 portrait'
            text=page.extract_text() or ''
            assert len(compact(text))>=20,'Blank or contentless PDF page '+str(index)
            page_text.append(text)
        actual=compact('\n'.join(page_text));expected=values(workbook)
        assert '職務経歴書' in actual and '案件経歴' in actual,'Both printed sheets must be present'
        short=[compact(v) for v in expected if len(compact(v))<=80]
        missing=[v for v in short if v not in actual]
        assert not missing,'Printed source-cell fragment missing: '+repr(missing[:3])
        assert re.search(r'00000[14]／',actual),'Leading-zero employee identifier missing'
        text_counts=Counter(actual);source_counts=Counter(compact(''.join(expected)))
        special={c:{'expected':source_counts[c],'actual':text_counts[c]} for c in ['文',"'",'=', '😀','🐱'] if source_counts[c]}
        for c,counts in special.items():
            assert counts['actual']>=counts['expected'],'Printed scalar count incomplete for '+repr(c)+': '+repr(counts)
        checks.append(dict(pdf=item['pdf'],sha256=item['pdfSha256'],pages=len(reader.pages),nonblankPages=len(page_text),sourceCellFragments=len(short),missingFragments=0,specialScalarCounts=special,status='PASS'))
    record['textReadback']=dict(status='PASS',recordedAtUtc=datetime.now(timezone.utc).isoformat(),tool='pypdf 6.21.4; independent OOXML source-cell reader',measurementSources=[dict(file='tests/Report/review-pdf.py',sha256=sha(Path(__file__)))],checks=checks,scope='Native PDF A4/portrait, both printed sheet headings, every page nonblank, every short OOXML source-cell fragment, leading-zero IDs and complete counts of repeated maximum-field/literal/supplementary scalars; visual layout remains separate.')
    record['status']='TEXT_READBACK_PASS_VISUAL_REVIEW_PENDING'
except Exception as error:
    record['status']='FAIL'
    record['textReadback']=dict(status='FAIL',error=str(error),completedChecks=checks)
    RECORD.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise
RECORD.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=record['status'],workbooks=len(checks),pages=sum(c['pages'] for c in checks))))
