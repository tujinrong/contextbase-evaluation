"""Copy established readback functions only, add V2-format assertions. No XLSX authoring."""
import ast
import hashlib
import json
from pathlib import Path
D=Path(__file__).parent
O=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
source=Path(r'D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\delivery\verify_xlsx_r18_r02.py')
raw=source.read_bytes();tree=ast.parse(raw)
keep={'bounds','unzip','worksheets','values','relation_map','image_positions','border_check','verify'}
pieces=[]
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name in keep:pieces.append(ast.get_source_segment(raw.decode('utf-8'),node))
assert len(pieces)==len(keep)
header='''"""Read-only XLSX verification; no connector, cell mutation, package authoring or CLI.
Caller must guard file reads and pin model/document bytes before calling verify().
Native full-size and actual print appearance remain separate required gates.
"""
import hashlib, io, json, posixpath, re, zipfile
from xml.etree import ElementTree as ET
S='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
XDR='http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def col(number):
    text=''
    while number:
        number,digit=divmod(number-1,26);text=chr(65+digit)+text
    return text
'''
extra='''
BASE_VERIFY=verify
COVER_RANGES={'O6:AU9','O12:W14','X12:AU14','O15:W17','X15:AU17','O18:W20','X18:AU20','O23:Y23','Z23:AJ23','AK23:AU23','O24:Y28','Z24:AJ28','AK24:AU28','O36:AU36'}
def format_assertions(sheet,styles,spec):
    if spec['role']=='normal':
        if spec['columns']!=62 or spec.get('gridColumnWidth')!=3:raise ValueError('Expected V2 normal A:BJ width3')
    if spec['role']=='list' and spec.get('itemList') is True:
        if spec['columns']!=10 or len(spec['tables'])!=1 or spec['tables'][0]['headerRow']!=1:raise ValueError('Item LIST ten columns/header row1 required')
    if spec['role']=='table' and spec['columns']!=9:raise ValueError('TABLE declared content must remain nine columns')
    for row in sheet.findall(f'.//{{{S}}}sheetData/{{{S}}}row'):
        if row.get('hidden','0') not in ('0','false'):raise ValueError('Hidden source rows are not approved')
    for column in sheet.findall(f'{{{S}}}cols/{{{S}}}col'):
        if column.get('hidden','0') not in ('0','false'):raise ValueError('Hidden source columns are not approved')
    if spec['role'] not in ('normal','cover'):return
    for index in range(1,spec['columns']+1):
        candidates=[c for c in sheet.findall(f'{{{S}}}cols/{{{S}}}col') if int(c.get('min'))<=index<=int(c.get('max'))]
        if len(candidates)!=1 or abs(float(candidates[0].get('width','nan'))-3)>0.0001:raise ValueError('V2 width3 actual column mismatch: '+str(index))
    if spec['role']!='cover':return
    if spec['printArea']!='O6:AU36' or {op['range'] for op in spec['operations']}!=COVER_RANGES:raise ValueError('V2 cover fourteen exact frame ranges required')
    xfs=styles.find(f'{{{S}}}cellXfs');borders=styles.find(f'{{{S}}}borders')
    cells={c.get('r'):c for c in sheet.findall(f'.//{{{S}}}sheetData/{{{S}}}row/{{{S}}}c')}
    def edges(x,y):
        cell=cells.get(f'{col(x)}{y}');xf=xfs[int(cell.get('s','0'))] if cell is not None else xfs[0]
        border=borders[int(xf.get('borderId','0'))]
        return {n.tag.rsplit('}',1)[-1]:n.get('style') for n in border if n.get('style')}
    for op in spec['operations']:
        left,top,right,bottom=bounds(op['range']);anchor=edges(left,top)
        if op['range']=='O36:AU36':
            if op['style']!='cover-company-band' or anchor.get('top')!='thin':raise ValueError('Company band top thin missing')
            for x in range(left,right+1):
                seen=edges(x,top)
                if any(k!='top' or v!='thin' for k,v in seen.items()):raise ValueError('Company band has an unapproved extra border')
            continue
        wanted='double' if op['style']=='cover-title' else 'thin'
        for y in range(top,bottom+1):
            for x in range(left,right+1):
                if any(v!=wanted for v in edges(x,y).values()):raise ValueError('Cover frame border style changed')
        for side,coords in [('left',[(left,y) for y in range(top,bottom+1)]),('right',[(right,y) for y in range(top,bottom+1)]),('top',[(x,top) for x in range(left,right+1)]),('bottom',[(x,bottom) for x in range(left,right+1)])]:
            if anchor.get(side)!=wanted and not all(edges(x,y).get(side)==wanted for x,y in coords):raise ValueError('Cover frame outline missing: '+op['range']+' '+side)

def verify(data,document,require_print=True):
    result=BASE_VERIFY(data,document,require_print)
    members=unzip(data);root,sheets=worksheets(members);styles=ET.fromstring(members['xl/styles.xml'])
    for _,_,sheet in sheets:
        # Workbook sheet visibility is checked in its original binding element below.
        pass
    declarations=root.findall(f'{{{S}}}sheets/{{{S}}}sheet')
    for node,(_,_,sheet),spec in zip(declarations,sheets,document['sheets']):
        if node.get('state','visible')!='visible':raise ValueError('Hidden source sheet is not approved')
        format_assertions(sheet,styles,spec)
    result.update(v2FormatAssertions=True,actualNativeVisualReview='PENDING',actualPrintLegibility='PENDING',readOnlyVerification=True)
    return result
'''
candidate=header+'\n\n'.join(pieces)+'\n'+extra
ast.parse(candidate)
out=D/'verify_xlsx_v2_62_r01.py'
with out.open('x',encoding='utf-8') as h:h.write(candidate)
assert source.read_bytes()==raw
receipt={'scope':'READONLY_VERIFIER_CODE_PREPARATION','candidate':{'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},'donor':{'path':str(source),'sha256':hashlib.sha256(raw).hexdigest()},'copiedReadOnlyFunctions':sorted(keep),'excludedMutationFunctions':['set_print','serialize_preserving_namespaces','main'],'additionalAssertions':['14 exact cover ranges','company top thin only','cover six thin empty frames','normal62 width3 actual columns','itemList10 header row1','TABLE9 content','no source rows/columns/sheets hidden'],'actualXlsxReads':0,'actualAuthoring':0,'status':'PREPARED_NOT_YET_SYNTHETICALLY_REVIEWED','limitations':['Established readback plus new strict format assertions require meaningful synthetic tests before actual use.','This module does not verify safe file paths, model generation provenance or visual appearance; caller must do those separately.','Use fresh raw-splice print helper; no old set_print mutator is present.']}
p=O/'readonly-verifier-preparation-r01.json'
with p.open('x',encoding='utf-8') as h:json.dump(receipt,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'candidate':str(out),'sha256':receipt['candidate']['sha256'],'receiptSha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
