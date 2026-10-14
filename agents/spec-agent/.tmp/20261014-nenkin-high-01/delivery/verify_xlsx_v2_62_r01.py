"""Read-only XLSX verification; no connector, cell mutation, package authoring or CLI.
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
def bounds(value):
    match=re.fullmatch(r'\$?([A-Z]+)\$?(\d+)(?::\$?([A-Z]+)\$?(\d+))?',value)
    if not match: raise ValueError('Invalid range')
    def number(text):
        value=0
        for char in text: value=value*26+ord(char)-64
        return value
    left,top,right,bottom=match.groups()
    return number(left),int(top),number(right or left),int(bottom or top)

def unzip(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if archive.testzip(): raise ValueError('Broken XLSX ZIP')
        names=archive.namelist()
        if len(names)!=len(set(names)): raise ValueError('Duplicate ZIP members')
        if any('vba' in name.lower() or 'externallinks' in name.lower() for name in names): raise ValueError('Active/external workbook content')
        members={name:archive.read(name) for name in names}
    for name,raw in members.items():
        if name.endswith(('.xml','.rels')):
            if b'<!DOCTYPE' in raw or b'<!ENTITY' in raw: raise ValueError('XML entities prohibited')
            ET.fromstring(raw)
    return members

def worksheets(members):
    root=ET.fromstring(members['xl/workbook.xml'])
    relationships=ET.fromstring(members['xl/_rels/workbook.xml.rels'])
    refs={node.get('Id'):node.get('Target') for node in relationships}
    result=[]
    for node in root.findall(f'{{{S}}}sheets/{{{S}}}sheet'):
        name=refs[node.get(f'{{{R}}}id')]
        target=name.lstrip('/') if name.startswith('/') else posixpath.normpath('xl/'+name)
        result.append((node.get('name'),target,ET.fromstring(members[target])))
    return root,result

def values(sheet,members):
    strings=[]
    if 'xl/sharedStrings.xml' in members:
        strings=[''.join(t.text or '' for t in si.iter(f'{{{S}}}t')) for si in ET.fromstring(members['xl/sharedStrings.xml'])]
    actual={}
    for cell in sheet.findall(f'.//{{{S}}}sheetData/{{{S}}}row/{{{S}}}c'):
        if cell.find(f'{{{S}}}f') is not None: raise ValueError('Formula found in specification workbook')
        kind=cell.get('t');value=cell.find(f'{{{S}}}v')
        if kind=='e': raise ValueError('Excel error cell')
        if kind=='inlineStr': text=''.join(t.text or '' for t in cell.iter(f'{{{S}}}t'))
        elif kind=='s': text=strings[int(value.text)]
        else: text=value.text if value is not None and value.text else ''
        if text:
            # Artifact Tool emits literal strings as t="str"; these are not
            # numeric values. Formula cells were rejected above independently.
            if kind not in {'s','inlineStr','str'}: raise ValueError('Specification value was coerced to numeric/date type')
            actual[cell.get('r')]=text
    return actual

def relation_map(part,members):
    name=posixpath.join(posixpath.dirname(part),'_rels',posixpath.basename(part)+'.rels')
    if name not in members:return {}
    result={}
    for rel in ET.fromstring(members[name]):
        target=rel.get('Target')
        if rel.get('TargetMode')=='External':raise ValueError('External drawing relationship')
        result[rel.get('Id')]=target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join(posixpath.dirname(part),target))
    return result

def image_positions(part,sheet,members):
    result=[];sheet_rel=relation_map(part,members)
    for link in sheet.findall(f'{{{S}}}drawing'):
        drawing_part=sheet_rel[link.get(f'{{{R}}}id')]
        drawing_rel=relation_map(drawing_part,members)
        for anchor in ET.fromstring(members[drawing_part]):
            origin=anchor.find(f'{{{XDR}}}from')
            if origin is None:raise ValueError('Unsupported absolute image anchor')
            blip=anchor.find(f'.//{{{A}}}blip')
            if blip is None:continue
            image_part=drawing_rel[blip.get(f'{{{R}}}embed')]
            result.append({'row':int(origin.find(f'{{{XDR}}}row').text),'col':int(origin.find(f'{{{XDR}}}col').text),'sha256':sha(members[image_part])})
    return result

def border_check(sheet,styles,spec):
    xfs=styles.find(f'{{{S}}}cellXfs'); borders=styles.find(f'{{{S}}}borders')
    def edges(style):
        border=borders[int(xfs[int(style)].get('borderId','0'))]
        return {n.tag.rsplit('}',1)[-1]:n.get('style') for n in border if n.get('style')}
    if edges(0) or any(xfs[0].get(k,'0')!='0' for k in ('fillId','numFmtId','fontId')):
        raise ValueError('Non-neutral standard Excel style')
    for dimension in list(sheet.findall(f'{{{S}}}cols/{{{S}}}col'))+list(sheet.findall(f'{{{S}}}sheetData/{{{S}}}row')):
        if edges(dimension.get('style',dimension.get('s','0'))): raise ValueError('Inherited borders outside document')
    cells={c.get('r'):c for c in sheet.findall(f'.//{{{S}}}sheetData/{{{S}}}row/{{{S}}}c')}
    left,top,right,bottom=bounds(spec['printArea']);outside=0
    for ref,cell in cells.items():
        x,y,_,_=bounds(ref)
        if not(left<=x<=right and top<=y<=bottom):
            outside+=1
            if edges(cell.get('s','0')): raise ValueError('Border outside print extent: '+ref)
    merges={n.get('ref') for n in sheet.findall(f'{{{S}}}mergeCells/{{{S}}}mergeCell')}
    expected={op['range'] for op in spec['operations'] if bounds(op['range'])[:2]!=bounds(op['range'])[2:]}
    if merges!=expected: raise ValueError('Merged rectangles changed')
    def cell_edges(x,y): return edges(cells.get(f'{col(x)}{y}',{}).get('s','0'))
    if spec['role']=='normal':
        for side,coordinates in [('left',[(left,y) for y in range(top,bottom+1)]),('right',[(right,y) for y in range(top,bottom+1)]),('top',[(x,top) for x in range(left,right+1)]),('bottom',[(x,bottom) for x in range(left,right+1)])]:
            for x,y in coordinates:
                if cell_edges(x,y).get(side)!='medium': raise ValueError('Missing continuous normal outer frame')
        for x in range(left,right+1):
            if cell_edges(x,top).get('bottom')!='double': raise ValueError('Missing double header rule')
    if spec['role']=='cover':
        covered=[bounds(op['range']) for op in spec['operations']]
        for ref,cell in cells.items():
            x,y,_,_=bounds(ref)
            if edges(cell.get('s','0')) and not any(a<=x<=b and r<=y<=t for a,r,b,t in covered): raise ValueError('Cover border leaked into whitespace')
    # A merged anchor may repeat its outline; continuations must not paint interiors.
    for operation in spec['operations']:
        a,r,b,t=bounds(operation['range'])
        if a==b and r==t: continue
        for y in range(r,t+1):
            for x in range(a,b+1):
                if (x,y)==(a,r): continue
                seen=cell_edges(x,y)
                exceptions={'left':x==left,'right':x==right,'top':y==top,'bottom':y==bottom or (spec['role']=='normal' and y==top)}
                for side,interior in [('left',x!=a),('right',x!=b),('top',y!=r),('bottom',y!=t)]:
                    if interior and side in seen and not(spec['role']=='normal' and exceptions[side]): raise ValueError('Border inside merged block')
    for table in spec['tables']:
        if spec['role'] not in {'table','list'}: continue
        a,r,b,t=bounds(table['range'])
        for x in range(a,b+1):
            if cell_edges(x,r).get('top')!='medium': raise ValueError('LIST/TABLE header top frame missing')
        if cell_edges(a,r).get('left')!='medium' or cell_edges(b,r).get('right')!='medium': raise ValueError('LIST/TABLE header side frame missing')
    return {'standardStyleNeutral':True,'outsideCellsChecked':outside,'mergedRectanglesChecked':len(merges),'borderPattern':spec['role']}

def verify(data,document,require_print=True):
    members=unzip(data);root,sheets=worksheets(members)
    if [name for name,_,_ in sheets]!=[s['name'] for s in document['sheets']]: raise ValueError('Declared sheet order/name changed')
    styles=ET.fromstring(members['xl/styles.xml']); checks=[]
    defined={n.get('localSheetId'):n.text for n in root.findall(f'{{{S}}}definedNames/{{{S}}}definedName') if n.get('name')=='_xlnm.Print_Area'}
    count=0
    for ordinal,((name,part,sheet),spec) in enumerate(zip(sheets,document['sheets'])):
        expected={re.match(r'[A-Z]+\d+',op['range'])[0]:op['value'] for op in spec['operations'] if op['value']}
        actual=values(sheet,members)
        if expected!=actual:
            mismatches=[key for key in set(expected)|set(actual) if expected.get(key)!=actual.get(key)]
            raise ValueError('Lossy cell conversion: '+name+' '+repr(sorted(mismatches)[:8]))
        count+=len(actual)
        checks.append(border_check(sheet,styles,spec))
        expected_positions=[{'row':i['row'],'col':i['col'],'sha256':i['sha256']} for i in spec['images']]
        sort=lambda records:sorted(records,key=lambda i:(i['row'],i['col'],i['sha256']))
        if sort(image_positions(part,sheet,members))!=sort(expected_positions):raise ValueError('Image source/placement mapping changed')
        if require_print:
            expected_area="'"+name.replace("'","''")+"'!"+':'.join('$'+re.sub(r'(\d+)',r'$\1',part) for part in spec['printArea'].split(':'))
            if defined.get(str(ordinal))!=expected_area: raise ValueError('Print area missing/mismatched')
            if sheet.find(f'{{{S}}}pageSetup') is None: raise ValueError('Print page setup missing')
    expected_images=[image['sha256'] for s in document['sheets'] for image in s['images']]
    actual_images=[sha(raw) for name,raw in members.items() if name.startswith('xl/media/')]
    if sorted(actual_images)!=sorted(expected_images): raise ValueError('Embedded image hashes/counts changed')
    return {'cellsChecked':count,'sheetCount':len(sheets),'embeddedImagesChecked':len(actual_images),'formulaCount':0,
            'borderChecks':checks,'printMetadataVerified':require_print,'visualReview':'PENDING'}

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
