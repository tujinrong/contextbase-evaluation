"""Independent OOXML readback and a print-metadata-only connection.

Artifact Tool authors all values, cells, merges, images and styles. The optional
connector touches only print metadata absent from its supplied public API.
"""
from __future__ import annotations
import argparse
import io
import json
import posixpath
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from delivery_model_r18 import safe_path, sha, col, load_bound, document_model

S='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
XDR='http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
XML_ORDER=['sheetPr','dimension','sheetViews','sheetFormatPr','cols','sheetData','sheetCalcPr','sheetProtection','protectedRanges','scenarios','autoFilter','sortState','dataConsolidate','customSheetViews','mergeCells','phoneticPr','conditionalFormatting','dataValidations','hyperlinks','printOptions','pageMargins','pageSetup','headerFooter','rowBreaks','colBreaks','customProperties','cellWatches','ignoredErrors','smartTags','drawing','legacyDrawing','legacyDrawingHF','picture','oleObjects','controls','webPublishItems','tableParts','extLst']

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

def set_print(members,document):
    root,sheets=worksheets(members)
    defined=root.find(f'{{{S}}}definedNames')
    if defined is None:
        defined=ET.Element(f'{{{S}}}definedNames');after=root.find(f'{{{S}}}sheets');root.insert(list(root).index(after)+1,defined)
    for ordinal,((name,target,sheet),spec) in enumerate(zip(sheets,document['sheets'])):
        for node in list(defined):
            if node.get('localSheetId')==str(ordinal) and node.get('name') in {'_xlnm.Print_Area','_xlnm.Print_Titles'}: defined.remove(node)
        area=ET.SubElement(defined,f'{{{S}}}definedName',name='_xlnm.Print_Area',localSheetId=str(ordinal))
        area.text="'"+name.replace("'","''")+"'!"+':'.join('$'+re.sub(r'(\d+)',r'$\1',part) for part in spec['printArea'].split(':'))
        if spec['tables'] or spec['role']=='normal':
            repeat=spec['tables'][-1]['headerRow'] if spec['role'] in {'list','table'} and spec['tables'] else 1
            item=ET.SubElement(defined,f'{{{S}}}definedName',name='_xlnm.Print_Titles',localSheetId=str(ordinal));item.text="'"+name.replace("'","''")+f"'!${repeat}:${repeat}"
        for tag,attributes in [('pageMargins',{'left':'0.25','right':'0.25','top':'0.4','bottom':'0.4','header':'0.15','footer':'0.15'}),
                               ('pageSetup',{'paperSize':'8' if spec['columns']>=10 else '9','orientation':'landscape','fitToWidth':'1','fitToHeight':'1' if spec['role']=='cover' else '0'})]:
            old=sheet.find(f'{{{S}}}'+tag)
            if old is not None: sheet.remove(old)
            node=ET.Element(f'{{{S}}}'+tag,attributes)
            order=XML_ORDER.index(tag);next_position=next((i for i,child in enumerate(sheet) if child.tag.rsplit('}',1)[-1] in XML_ORDER and XML_ORDER.index(child.tag.rsplit('}',1)[-1])>order),len(sheet))
            sheet.insert(next_position,node)
        members[target]=serialize_preserving_namespaces(sheet,members[target])
    members['xl/workbook.xml']=serialize_preserving_namespaces(root,members['xl/workbook.xml'])
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,raw in members.items(): archive.writestr(name,raw)
    return output.getvalue()

def serialize_preserving_namespaces(root,original):
    namespaces={}
    for _,(prefix,uri) in ET.iterparse(io.BytesIO(original),events=['start-ns']):
        namespaces[prefix]=uri
        if not re.fullmatch(r'ns\d+',prefix): ET.register_namespace(prefix,uri)
    raw=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    # Preserve prefixes referenced by QName-valued attributes such as mc:Ignorable.
    for prefix,uri in namespaces.items():
        attribute=('xmlns:'+prefix) if prefix else 'xmlns'
        if (attribute+'=').encode() not in raw:
            root.set(attribute,uri)
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',type=Path,required=True);parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--connect-print-metadata',action='store_true')
    args=parser.parse_args();model_bytes=safe_path(args.model).read_bytes();model=json.loads(model_bytes)
    manifest_path=safe_path(args.manifest);manifest=json.loads(manifest_path.read_bytes())
    if manifest['modelSha256']!=sha(model_bytes): raise ValueError('Changed authoring model')
    _,entry_list,_=load_bound(model['binding'])
    projection=model.get('projection',{})
    source_models={e['documentId']:document_model(e,projection.get('imageMaxWidth',1100),projection.get('previewMaxHeight')) for e in entry_list}
    if {d['documentId'] for d in manifest['documents']}!={d['documentId'] for d in model['documents']}:
        raise ValueError('Exported document set incomplete or changed')
    def save():
        temporary=manifest_path.with_suffix('.verification.tmp')
        temporary.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temporary.replace(manifest_path)
    try:
        for record in manifest['documents']:
            document=source_models[record['documentId']]
            path=safe_path(record['xlsx'])
            if not path.is_relative_to(manifest_path.parent): raise ValueError('Output outside selected delivery tree')
            raw=path.read_bytes()
            if sha(raw)!=record['xlsxSha256']: raise ValueError('Changed exported XLSX')
            if args.connect_print_metadata and record.get('printMetadataConnection') is None:
                verify(raw,document,require_print=False)
                connected=set_print(unzip(raw),document)
                checks=verify(connected,document,require_print=True)
                temporary=path.with_suffix('.print-connection.tmp');temporary.write_bytes(connected);temporary.replace(path)
                record['printMetadataConnection']={'scope':'PRINT_METADATA_ONLY','artifactToolExportSha256':sha(raw),'connectedSha256':sha(connected)}
                record['xlsxSha256']=sha(connected)
            else: checks=verify(raw,document,require_print=True)
            record.update(independentCellVerification='PASS',printSettings='VERIFIED',readbackChecks=checks)
            save()
        load_bound(model['binding'])
        manifest['status']='MECHANICALLY_VERIFIED_VISUAL_REVIEW_PENDING'
    except Exception as exc:
        manifest.update(status='FAILED',error=str(exc),published=False)
        raise
    finally: save()
    print(json.dumps({'documents':len(manifest['documents']),'status':manifest['status']}))

if __name__=='__main__':main()
