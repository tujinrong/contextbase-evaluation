"""Portable, deterministic OOXML package serializer for the MD workbook model.

Creates new data-only workbooks; it is not a general workbook editing library.
No Excel, network, macros, external formulas or font files are required.
"""
from __future__ import annotations
import io
import base64
import hashlib
import posixpath
import re
import zipfile
from xml.etree import ElementTree as ET
from .excel_model import col, expected_values

S='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
P='http://schemas.openxmlformats.org/package/2006/relationships'
C='http://schemas.openxmlformats.org/package/2006/content-types'
XML='http://www.w3.org/XML/1998/namespace'
ET.register_namespace('',S)
ET.register_namespace('r',R)


def el(parent,tag,attrs=None,ns=S,**kwargs):
    return ET.SubElement(parent,f'{{{ns}}}{tag}',{**(attrs or {}),**{k:str(v) for k,v in kwargs.items()}})


def xml(element):
    ET.register_namespace('',element.tag.split('}')[0].lstrip('{'))
    return ET.tostring(element,encoding='utf-8',xml_declaration=True)


# V2 presentation styles; data values remain explicit literal strings.
STYLE_DEFS = {
 # Cell XF 0 is the default for *all* unspecified worksheet cells.
 # It must remain General / no fill / no borders, not a table-body style.
 'blank':(0,0,0),
 'body':(0,0,1), 'title':(1,0,1), 'section':(2,2,1),
 'header':(3,3,1), 'stripe':(0,4,1), 'code':(0,4,0),
 'narrative':(0,0,0), 'subheading':(4,0,0),
 'center':(0,0,1), 'cover_title':(5,0,2), 'cover_label':(3,3,1),
 'cover_value':(6,0,1), 'approval':(0,0,1), 'company':(4,0,0),
 'list_title':(1,0,0),
}
STYLES={name:i for i,name in enumerate(STYLE_DEFS)}

# Neutral default + per-edge styles. Mixed borders are needed at intersections
# of the thick document frame, thin table rules and double header rule.
EDGE_SIDES = ('left', 'right', 'top', 'bottom')
ALL_EDGES = 15
# kind: (Excel line style, RGB); 0 has no painted edge.
EDGE_DEFS = {0: (None, None), 1: ('thin', 'FF808080'),
             2: ('double', 'FF595959'), 3: ('medium', 'FF000000'),
             4: ('medium', 'FF595959'), 5: ('thin', 'FF000000')}
STYLE_VARIANTS = [(name, ALL_EDGES) for name in STYLE_DEFS]
STYLE_VARIANTS += [(name, mask) for name, (_, _, kind) in STYLE_DEFS.items()
                   if kind for mask in range(ALL_EDGES)]
STYLE_IDS = {pair: index for index, pair in enumerate(STYLE_VARIANTS)}


class StyleCatalog:
    """Per-workbook catalog, avoiding global state and a combinatorial style grid."""
    def __init__(self):
        self.entries = []
        self.ids = {}
        for name, mask in STYLE_VARIANTS:
            kind = STYLE_DEFS[name][2]
            edges = tuple(kind if mask & (1 << bit) else 0 for bit in range(4))
            # Preserve initial public style indexes used by validation fixtures.
            self.ids.setdefault((name, edges), len(self.entries))
            self.entries.append((name, edges))

    def register(self, name, edges):
        key = (name, tuple(edges))
        if key not in self.ids:
            self.ids[key] = len(self.entries)
            self.entries.append(key)
        return self.ids[key]


def border_pattern(sheet: dict) -> str:
    pattern = sheet.get('border_pattern')
    if pattern is None:
        pattern = ('cover' if sheet.get('role') == 'cover' else
                   'normal' if sheet.get('style_family') == 'v2' and len(sheet['widths']) == 62 else
                   'list' if sheet.get('style_family') == 'v2' else 'legacy')
    if pattern not in {'cover', 'normal', 'list', 'legacy'}:
        raise ValueError('Unknown Excel border pattern: ' + str(pattern))
    return pattern


def range_bounds(ref: str) -> tuple[int, int, int, int]:
    """Parse a single A1 rectangle, accepting absolute print-area references."""
    match = re.fullmatch(r'\$?([A-Z]+)\$?([1-9]\d*)(?::\$?([A-Z]+)\$?([1-9]\d*))?', ref)
    if not match:
        raise ValueError('Invalid worksheet rectangle: ' + ref)
    def column(value):
        result = 0
        for char in value:
            result = result * 26 + ord(char) - 64
        return result
    a, r, b, t = match.groups()
    bounds = (column(a), int(r), column(b or a), int(t or r))
    if not (bounds[0] <= bounds[2] <= 16384 and bounds[1] <= bounds[3] <= 1048576):
        raise ValueError('Worksheet rectangle is out of bounds: ' + ref)
    return bounds


def sheet_merges(sheet: dict) -> list[str]:
    merges = list(sheet.get('merges', []))
    n = len(sheet['widths'])
    merges.extend(f'A{r}:{col(n)}{r}' for r, row in enumerate(sheet['rows'], 1)
                  if row.get('merge') and n > 1)
    return merges


def base_cell_style(sheet: dict, row: int, column: int) -> str:
    data = sheet['rows'][row - 1]
    # Do not spread table-body borders into padding or empty spacer rows.
    default = data['style'] if column <= len(data['values']) else 'blank'
    return sheet.get('cell_styles', {}).get(f'{col(column)}{row}', default)


def style_id(name: str, mask: int = ALL_EDGES) -> int:
    return STYLE_IDS[(name, mask if STYLE_DEFS[name][2] else ALL_EDGES)]


def resolved_cell_styles(sheet: dict, merges: list[str], catalog=None) -> dict[str, int]:
    catalog = catalog or StyleCatalog()
    n, last = len(sheet['widths']), len(sheet['rows'])
    a, r, b, t = range_bounds(sheet.get('print_area', f'A1:{col(n)}{last}'))
    if b > n or t > last:
        raise ValueError('Print range exceeds the document canvas')
    inside = lambda row, column: r <= row <= t and a <= column <= b
    cells = {}
    for row in range(1, last + 1):
        for column in range(1, n + 1):
            name = base_cell_style(sheet, row, column)
            cells[(column, row)] = [name, [STYLE_DEFS[name][2]] * 4]
    occupied = set()
    for ref in merges:
        left, top, right, bottom = range_bounds(ref)
        if right > n or bottom > last:
            raise ValueError('Merged region exceeds the document canvas: ' + ref)
        name = base_cell_style(sheet, top, left)
        kind = STYLE_DEFS[name][2]
        for row in range(top, bottom + 1):
            for column in range(left, right + 1):
                key = (column, row)
                if key in occupied:
                    raise ValueError('Overlapping merged region: ' + ref)
                occupied.add(key)
                keep = [column == left, column == right, row == top, row == bottom]
                if row == top and column == left:
                    keep = [True] * 4  # V2/Excel merged-anchor convention.
                cells[key] = [name, [kind if x else 0 for x in keep]]

    pattern = border_pattern(sheet)
    if pattern == 'normal':
        # Reference: A1:BJ<last>, medium black outline including spacer/image rows.
        # Overlay last so an inner merge cannot remove the right/bottom frame.
        for (column, row), (_, edges) in cells.items():
            if not inside(row, column):
                continue
            if row == r:
                edges[3] = 2  # V2 double rule beneath the document header.
            for bit, boundary in enumerate((column == a, column == b, row == r, row == t)):
                if boundary:
                    edges[bit] = 3
    elif pattern == 'cover':
        # Cover is several separate boxes, NOT a rectangle around O6:AU36.
        # The reference has only a top rule above its company/footer band.
        for (column, row), (name, edges) in cells.items():
            if name == 'company':
                cells[(column, row)][1] = [0, 0, 5, 0]
    elif pattern == 'list':
        # Title and trailing narrative/spacers remain unframed. Header has
        # medium left/right/top; data rows provide the thin lower separator.
        for (_, _), (name, edges) in cells.items():
            if name == 'header':
                for bit in range(4):
                    edges[bit] = 4 if bit != 3 and edges[bit] else 0

    result = {}
    for (column, row), (name, edges) in cells.items():
        if not inside(row, column):
            edges = [0] * 4
        result[f'{col(column)}{row}'] = catalog.register(name, edges)
    return result


def styles_xml(catalog=None):
    catalog = catalog or StyleCatalog()
    root=ET.Element(f'{{{S}}}styleSheet')
    fonts=el(root,'fonts',count=7)
    for size,bold in [(10,False),(18,True),(12.5,True),(10,True),(11.5,True),(32,True),(16,True)]:
        font=el(fonts,'font');el(font,'sz',val=size);el(font,'name',val='Yu Gothic');el(font,'family',val=2)
        el(font,'color',rgb='FF000000')
        if bold:el(font,'b')
    fills=el(root,'fills',count=5)
    for pattern,color in [('none',None),('gray125',None),('solid','EDEDED'),('solid','D9D9D9'),('solid','F4F7FA')]:
        fill=el(fills,'fill');pat=el(fill,'patternFill',patternType=pattern)
        if color:el(pat,'fgColor',rgb='FF'+color);el(pat,'bgColor',indexed=64)
    border_values = list(dict.fromkeys(edges for _, edges in catalog.entries))
    border_ids = {value: i for i, value in enumerate(border_values)}
    borders=el(root,'borders',count=len(border_values))
    for edges in border_values:
        border=el(borders,'border')
        for side, kind in zip(EDGE_SIDES, edges):
            line, color = EDGE_DEFS[kind]
            tag=el(border,side,style=line) if line else el(border,side)
            if line:el(tag,'color',rgb=color)
        el(border,'diagonal')
    cellstyle=el(root,'cellStyleXfs',count=1);el(cellstyle,'xf',numFmtId=0,fontId=0,fillId=0,borderId=0)
    xfs=el(root,'cellXfs',count=len(catalog.entries))
    for name, edges in catalog.entries:
        font, fill, _ = STYLE_DEFS[name]
        xf=el(xfs,'xf',numFmtId=0 if name=='blank' else 49,fontId=font,fillId=fill,
              borderId=border_ids[edges],xfId=0,applyFont=1,applyFill=1,applyBorder=1,
              applyNumberFormat=1,applyAlignment=1)
        centered=name in {'header','center','cover_title','cover_label','cover_value','company'}
        el(xf,'alignment',horizontal='center' if centered else 'left',
           vertical='center' if centered else 'top',wrapText=1)
    cs=el(root,'cellStyles',count=1);el(cs,'cellStyle',name='Normal',xfId=0,builtinId=0)
    return xml(root)


def sheet_xml(sheet, catalog=None):
    root=ET.Element(f'{{{S}}}worksheet')
    props=el(root,'sheetPr');el(props,'pageSetUpPr',fitToPage=1)
    n=len(sheet['widths']);last=len(sheet['rows']);end=f'{col(n)}{last}'
    el(root,'dimension',ref='A1:'+end)
    views=el(root,'sheetViews');view=el(views,'sheetView',workbookViewId=0,showGridLines=0)
    frozen=sheet.get('freeze',sheet['repeat'])
    if frozen:
        el(view,'pane',ySplit=frozen,topLeftCell=f'A{frozen+1}',activePane='bottomLeft',state='frozen')
        el(view,'selection',pane='bottomLeft',activeCell=f'A{frozen+1}',sqref=f'A{frozen+1}')
    el(root,'sheetFormatPr',defaultRowHeight=20)
    columns=el(root,'cols')
    for c,w in enumerate(sheet['widths'],1):el(columns,'col',min=c,max=c,width=w,customWidth=1)
    data=el(root,'sheetData');merges=sheet_merges(sheet)
    cell_styles=resolved_cell_styles(sheet,merges,catalog)
    for r,row in enumerate(sheet['rows'],1):
        rn=el(data,'row',r=r,ht=row['height'],customHeight=1)
        vals=row['values']
        for c in range(1,n+1):
            value=str(vals[c-1]) if c<=len(vals) else ''
            if any(ord(ch)<32 and ch not in '\t\n\r' for ch in value):raise ValueError('Control character in worksheet cell')
            if len(value)>32767:raise ValueError('Cell exceeds Excel text limit')
            cell=el(rn,'c',r=f'{col(c)}{r}',s=cell_styles[f'{col(c)}{r}'],t='inlineStr')
            ss=el(cell,'is');t=el(ss,'t', {f'{{{XML}}}space':'preserve'});t.text=value
    if sheet.get('filter'):
        a,b,c=sheet['filter'];el(root,'autoFilter',ref=f'A{a}:{col(c)}{b}')
    if merges:
        ms=el(root,'mergeCells',count=len(merges))
        for ref in merges:el(ms,'mergeCell',ref=ref)
    el(root,'printOptions',horizontalCentered=1)
    el(root,'pageMargins',left=0.25,right=0.25,top=0.4,bottom=0.4,header=0.15,footer=0.15)
    el(root,'pageSetup',paperSize=8 if sheet['paper']=='A3' else 9,orientation='landscape',fitToWidth=1,fitToHeight=sheet.get('fit_height',0))
    hf=el(root,'headerFooter');el(hf,'oddFooter').text='&LCONTEXTBASE&RPAGE &P / &N'
    if sheet.get('breaks'):
        breaks=el(root,'rowBreaks',count=len(sheet['breaks']),manualBreakCount=len(sheet['breaks']))
        for row in sheet['breaks']:el(breaks,'brk',id=row,min=0,max=16383,man=1)
    if sheet.get('images'):el(root,'drawing',{f'{{{R}}}id':'drawing'})
    return xml(root)


def drawing_files(sheet,index):
    X='http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing'
    A='http://schemas.openxmlformats.org/drawingml/2006/main'
    ET.register_namespace('xdr',X);ET.register_namespace('a',A)
    root=ET.Element(f'{{{X}}}wsDr');rels=ET.Element(f'{{{P}}}Relationships');files={}
    for i,image in enumerate(sheet['images'],1):
        anchor=el(root,'oneCellAnchor',ns=X);start=el(anchor,'from',ns=X)
        for tag,value in [('col',image['col']),('colOff',0),('row',image['row']),('rowOff',0)]:el(start,tag,ns=X).text=str(value)
        el(anchor,'ext',ns=X,cx=image['width']*9525,cy=image['height']*9525)
        pic=el(anchor,'pic',ns=X);nv=el(pic,'nvPicPr',ns=X)
        el(nv,'cNvPr',ns=X,id=i,name=f'Image {i}',descr=image.get('alt',''))
        locks=el(nv,'cNvPicPr',ns=X);el(locks,'picLocks',ns=A,noChangeAspect=1)
        fill=el(pic,'blipFill',ns=X);el(fill,'blip',{f'{{{R}}}embed':f'image{i}'},ns=A)
        stretch=el(fill,'stretch',ns=A);el(stretch,'fillRect',ns=A)
        shape=el(pic,'spPr',ns=X);geom=el(shape,'prstGeom',ns=A,prst='rect');el(geom,'avLst',ns=A)
        el(anchor,'clientData',ns=X)
        fname=f'image{index}_{i}.png';files['xl/media/'+fname]=base64.b64decode(image['data'],validate=True)
        el(rels,'Relationship',ns=P,Id=f'image{i}',Type=R+'/image',Target='../media/'+fname)
    files[f'xl/drawings/drawing{index}.xml']=xml(root)
    files[f'xl/drawings/_rels/drawing{index}.xml.rels']=xml(rels)
    page_rels=ET.Element(f'{{{P}}}Relationships')
    el(page_rels,'Relationship',ns=P,Id='drawing',Type=R+'/drawing',Target=f'../drawings/drawing{index}.xml')
    files[f'xl/worksheets/_rels/sheet{index}.xml.rels']=xml(page_rels)
    return files


def package(model: dict) -> bytes:
    """Serialize only reviewed values/layout; the model cannot supply XML or formulas."""
    workbook=ET.Element(f'{{{S}}}workbook')
    bookviews=el(workbook,'bookViews');el(bookviews,'workbookView',activeTab=0)
    sheets=el(workbook,'sheets');names=el(workbook,'definedNames')
    rels=ET.Element(f'{{{P}}}Relationships');types=ET.Element(f'{{{C}}}Types')
    for ext,mime in [('rels','application/vnd.openxmlformats-package.relationships+xml'),('xml','application/xml')]:
        el(types,'Default',ns=C,Extension=ext,ContentType=mime)
    el(types,'Override',ns=C,PartName='/xl/workbook.xml',ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml')
    el(types,'Override',ns=C,PartName='/xl/styles.xml',ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml')
    catalog=StyleCatalog()
    files={}
    for i,sheet in enumerate(model['sheets'],1):
        el(sheets,'sheet',{'name':sheet['name'],'sheetId':str(i),f'{{{R}}}id':f'rId{i}'})
        el(rels,'Relationship',ns=P,Id=f'rId{i}',Type=R+'/worksheet',Target=f'worksheets/sheet{i}.xml')
        el(types,'Override',ns=C,PartName=f'/xl/worksheets/sheet{i}.xml',ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml')
        quoted="'"+sheet['name'].replace("'","''")+"'!"
        area=sheet.get('print_area',f'A1:{col(len(sheet["widths"]))}{len(sheet["rows"])}')
        area=re.sub(r'\$?([A-Z]+)\$?(\d+)',r'$\1$\2',area)
        el(names,'definedName',name='_xlnm.Print_Area',localSheetId=i-1).text=quoted+area
        if sheet['repeat']:
            el(names,'definedName',name='_xlnm.Print_Titles',localSheetId=i-1).text=quoted+f'$1:${sheet["repeat"]}'
        files[f'xl/worksheets/sheet{i}.xml']=sheet_xml(sheet,catalog)
        if sheet.get('images'):
            files.update(drawing_files(sheet,i))
            el(types,'Override',ns=C,PartName=f'/xl/drawings/drawing{i}.xml',ContentType='application/vnd.openxmlformats-officedocument.drawing+xml')
    if any(s.get('images') for s in model['sheets']):
        el(types,'Default',ns=C,Extension='png',ContentType='image/png')
    el(rels,'Relationship',ns=P,Id='styles',Type=R+'/styles',Target='styles.xml')
    top=ET.Element(f'{{{P}}}Relationships');el(top,'Relationship',ns=P,Id='root',Type=R+'/officeDocument',Target='xl/workbook.xml')
    files['xl/styles.xml']=styles_xml(catalog)
    files.update({'[Content_Types].xml':xml(types),'_rels/.rels':xml(top),'xl/workbook.xml':xml(workbook),'xl/_rels/workbook.xml.rels':xml(rels)})
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name,(2020,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,data)
    return stream.getvalue()



def verify_border_layout(styles, sheet_xml_node, spec: dict) -> dict:
    """Reject implicit/explicit margin borders and damaged merged outlines."""
    borders = styles.find(f'{{{S}}}borders')
    xfs = styles.find(f'{{{S}}}cellXfs')
    def edges(style_index):
        border = borders[int(xfs[style_index].get('borderId', '0'))]
        return {node.tag.rsplit('}', 1)[-1]: node.get('style')
                for node in border if node.get('style')}
    if edges(0):
        raise ValueError('Default cell style paints borders on unspecified worksheet cells')
    if any(xfs[0].get(key, '0') != '0' for key in ('fillId', 'numFmtId', 'fontId')):
        raise ValueError('Default cell style must use the neutral Normal format')
    for dimension in list(sheet_xml_node.findall(f'{{{S}}}cols/{{{S}}}col')) + list(
            sheet_xml_node.findall(f'{{{S}}}sheetData/{{{S}}}row')):
        inherited = dimension.get('style', dimension.get('s', '0'))
        if edges(int(inherited)):
            raise ValueError('A row/column default would paint borders beyond its data')
    cells = {node.get('r'): node for node in sheet_xml_node.findall(
        f'{{{S}}}sheetData/{{{S}}}row/{{{S}}}c')}
    def cell_edges(column, row):
        node = cells.get(f'{col(column)}{row}')
        return edges(int(node.get('s', '0'))) if node is not None else edges(0)
    n, last = len(spec['widths']), len(spec['rows'])
    left, top, right, bottom = range_bounds(spec.get('print_area', f'A1:{col(n)}{last}'))
    pattern = border_pattern(spec)
    outside = 0
    for ref, node in cells.items():
        c, r, _, _ = range_bounds(ref)
        if not (left <= c <= right and top <= r <= bottom):
            outside += 1
            if edges(int(node.get('s', '0'))):
                raise ValueError(f"{spec['name']}!{ref}: border outside the document range")
    perimeter = 0
    if pattern == 'normal':
        for side, coordinates in (
            ('left', ((left, y) for y in range(top, bottom + 1))),
            ('right', ((right, y) for y in range(top, bottom + 1))),
            ('top', ((x, top) for x in range(left, right + 1))),
            ('bottom', ((x, bottom) for x in range(left, right + 1)))):
            for x, y in coordinates:
                perimeter += 1
                if cell_edges(x, y).get(side) != 'medium':
                    raise ValueError(f"{spec['name']}!{col(x)}{y}: missing medium outer frame ({side})")
    if pattern in {'cover', 'list'}:
        for y in range(1, last + 1):
            for x in range(1, n + 1):
                name = base_cell_style(spec, y, x)
                if name in {'blank', 'narrative', 'list_title', 'company'}:
                    expected = {'top': 'thin'} if pattern == 'cover' and name == 'company' else {}
                    if not (left <= x <= right and top <= y <= bottom):
                        expected = {}
                    if cell_edges(x, y) != expected:
                        raise ValueError(f"{spec['name']}!{col(x)}{y}: border in unframed space")
                if pattern == 'list' and name == 'header':
                    if cell_edges(x, y) != {'left':'medium','right':'medium','top':'medium'}:
                        raise ValueError('List header must follow the medium reference rule')
    actual_merges = [m.get('ref') for m in sheet_xml_node.findall(f'{{{S}}}mergeCells/{{{S}}}mergeCell')]
    if sorted(actual_merges) != sorted(sheet_merges(spec)):
        raise ValueError('Merged document rectangles changed')
    for ref in actual_merges:
        a, r, b, t = range_bounds(ref)
        kind = STYLE_DEFS[base_cell_style(spec, r, a)][2]
        line = {0: None, 1: 'thin', 2: 'double'}[kind]
        for y in range(r, t + 1):
            for x in range(a, b + 1):
                expected = {}
                if line and left <= x <= right and top <= y <= bottom:
                    expected = {side: line for side, keep in (
                        ('left', x == a), ('right', x == b),
                        ('top', y == r), ('bottom', y == t)) if keep}
                    if x == a and y == r:
                        expected = dict.fromkeys(EDGE_SIDES, line)
                if left <= x <= right and top <= y <= bottom:
                    if pattern == 'normal':
                        if y == top:
                            expected['bottom'] = 'double'
                        for side, hit in (('left', x == left), ('right', x == right),
                                          ('top', y == top), ('bottom', y == bottom)):
                            if hit:
                                expected[side] = 'medium'
                    elif pattern == 'cover' and base_cell_style(spec, r, a) == 'company':
                        expected = {'top':'thin'}
                if cell_edges(x, y) != expected:
                    raise ValueError(f"{spec['name']}!{col(x)}{y}: merged border is not an outer outline")
    return {'pattern':pattern, 'outer_frame_edges_checked':perimeter,
            'default_borderless': True, 'outside_cells_checked': outside,
            'merged_outlines_checked': len(actual_merges)}


def verify(data: bytes, model: dict) -> dict:
    """Read ZIP/XML independently and compare every nonempty cell, sheet and value."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        bad=z.testzip()
        if bad:raise ValueError('Corrupt XLSX member: '+bad)
        files=set(z.namelist())
        if any('vba' in name.lower() or 'externallinks' in name.lower() for name in files):raise ValueError('Active content prohibited')
        for name in files:
            if name.endswith('.xml') or name.endswith('.rels'):
                raw=z.read(name)
                if b'<!DOCTYPE' in raw or b'<!ENTITY' in raw:raise ValueError('XML entities prohibited')
                ET.fromstring(raw)
        wb=ET.fromstring(z.read('xl/workbook.xml'))
        actual_sheets=wb.findall(f'{{{S}}}sheets/{{{S}}}sheet')
        if [s.attrib['name'] for s in actual_sheets]!=[s['name'] for s in model['sheets']]:raise ValueError('Sheet identity mismatch')
        rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        targets={r.attrib['Id']:r.attrib['Target'] for r in rels}
        strings=[]
        if 'xl/sharedStrings.xml' in files:
            strings=[''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        styles=ET.fromstring(z.read('xl/styles.xml'))
        border_checks=[]
        count=0
        for s, spec in zip(actual_sheets,model['sheets']):
            target=targets[s.attrib[f'{{{R}}}id']]
            target=target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
            sheet=ET.fromstring(z.read(target));actual={}
            border_checks.append(verify_border_layout(styles,sheet,spec))
            for c in sheet.findall(f'.//{{{S}}}sheetData/{{{S}}}row/{{{S}}}c'):
                if c.find(f'{{{S}}}f') is not None:raise ValueError('Unexpected formula')
                if c.attrib.get('t')=='e':raise ValueError('Error cell')
                if c.attrib.get('t')=='inlineStr':value=''.join(c.find(f'{{{S}}}is').itertext())
                else:
                    v=c.find(f'{{{S}}}v');value=v.text if v is not None and v.text else ''
                    if c.attrib.get('t')=='s':value=strings[int(value)]
                if value:actual[c.attrib['r']]=value
            expected=expected_values(spec)
            if actual!=expected:
                keys=sorted(set(actual)|set(expected));bad=[k for k in keys if actual.get(k)!=expected.get(k)]
                raise ValueError(f"{spec['name']}: cell mismatch {bad[:5]}")
            count+=len(actual)
        expected_images=[image for sheet in model['sheets'] for image in sheet.get('images',[])]
        media=[name for name in files if name.startswith('xl/media/')]
        if len(media)!=len(expected_images):raise ValueError('Embedded image count mismatch')
        if sorted(hashlib.sha256(z.read(n)).hexdigest() for n in media)!=sorted(i['sha256'] for i in expected_images):
            raise ValueError('Embedded image bytes mismatch')
        return {'status':'verified','sheets':len(actual_sheets),'checked_cells':count,'embedded_images':len(media),
                'borders_verified':True,'border_checks':border_checks,'formulas':0,'errors':0}
