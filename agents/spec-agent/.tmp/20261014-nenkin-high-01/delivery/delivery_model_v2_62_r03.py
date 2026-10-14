"""Mechanical extraction and pinned-render validation; never authors prose."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt

SCHEMA = 'reverse-agent-delivery-model/1'
# User-selected V2 format profile. No change to Markdown/source content.
GRID_COLUMNS = 62
GRID_COLUMN_WIDTH = 3
GRID_TEXT_UNITS_PER_COLUMN = 2.75
GRID_BODY_START_COLUMN = 2
GRID_IMAGE_MAX_WIDTH = 1100
FORMAT_PROFILE = {'id':'v2-62-preserved-reference','coverPrintArea':'O6:AU36','gridColumns':GRID_COLUMNS,'gridColumnWidth':GRID_COLUMN_WIDTH,'gridBodyStartColumn':GRID_BODY_START_COLUMN,'itemListColumns':10,'listHeaderRow':1,'literalStrings':True}
TABLE_COLUMNS = ['No','論理名','物理名','PK','NOT NULL','タイプ','長さ','初期値','説明']

def sha(value):
    return hashlib.sha256(value).hexdigest()

def safe_path(value):
    path = Path(os.path.abspath(value))
    if any(part.casefold() == 'spec-eval' for part in path.parts):
        raise ValueError('Evaluation paths are not delivery inputs')
    parts=[part.casefold() for part in path.parts]
    if 'srcs' in parts and 'spec' in parts[parts.index('srcs')+1:]:
        raise ValueError('Original specification paths are not delivery inputs')
    for ancestor in (path, *path.parents):
        try:
            if ancestor.is_symlink() or getattr(ancestor.lstat(), 'st_file_attributes', 0) & 0x400:
                raise ValueError('Linked paths are forbidden')
        except FileNotFoundError:
            pass
    return path.resolve()

def json_read(path):
    return json.loads(safe_path(path).read_text(encoding='utf-8-sig'))

def canonical(value):
    if not isinstance(value, str) or value.startswith(('/','\\')) or '\\' in value or ':' in value:
        raise ValueError('Canonical relative path required')
    path = Path(value)
    if path.is_absolute() or '..' in path.parts or path.suffix.lower() != '.md':
        raise ValueError('Canonical Markdown path required')
    if path.as_posix()!=value or any(ord(char)<32 for char in value):
        raise ValueError('Noncanonical path spelling')
    return path

def load_bound(binding_path):
    binding_path = safe_path(binding_path)
    binding_bytes = binding_path.read_bytes()
    bound = json.loads(binding_bytes.decode('utf-8-sig'))
    if bound.get('schema') != 'reverse-agent-delivery-binding/1':
        raise ValueError('Unsupported binding schema')
    mdroot = safe_path(bound['permittedMarkdownRoot'])
    renderroot = safe_path(bound['permittedRenderRoot'])
    rows, ids, paths = [], set(), set()
    for entry in bound['documents']:
        cp = canonical(entry['canonicalDocumentPath'])
        if entry['documentId'] in ids or cp.as_posix().casefold() in paths:
            raise ValueError('Duplicate delivery document')
        ids.add(entry['documentId']); paths.add(cp.as_posix().casefold())
        md = safe_path(entry['markdown'])
        render = safe_path(entry['renderDirectory'])
        if not md.is_relative_to(mdroot) or not render.is_relative_to(renderroot):
            raise ValueError('Input outside explicit permitted roots')
        raw = md.read_bytes()
        if sha(raw) != entry['markdownSha256']:
            raise ValueError('Changed Markdown')
        pinned_files = {}
        for filename, key in [('render-pins.json','renderPinsSha256'), ('manifest.json','renderManifestSha256')]:
            value = (render / filename).read_bytes()
            if sha(value) != entry[key]:
                raise ValueError('Changed render binding: ' + filename)
            pinned_files[filename] = json.loads(value.decode('utf-8-sig'))
        pins, manifest = pinned_files['render-pins.json'], pinned_files['manifest.json']
        if pins['documentId'] != entry['documentId'] or pins['canonicalDocumentPath'] != cp.as_posix():
            raise ValueError('Render document identity mismatch')
        if pins['sourceSnapshotManifestSha256'] != bound['sourceSnapshotManifestSha256']:
            raise ValueError('Mixed source snapshot')
        if entry.get('sourceSnapshotManifestSha256', bound['sourceSnapshotManifestSha256']) != bound['sourceSnapshotManifestSha256']:
            raise ValueError('Mixed source snapshot entry')
        for record in (pins, manifest):
            if record['sourceSha256'] != sha(raw):
                raise ValueError('Mixed rendered draft')
            if record['structure']['status'] != 'PASS' or record['structure'].get('findings'):
                raise ValueError('Structure errors are not publishable')
            if record['display']['status'] != 'PASS' or record['display'].get('blockedRequests') or record['display'].get('errors'):
                raise ValueError('Incomplete display is not publishable')
            if record['safety'].get('removed') or record['safety'].get('inputJavaScriptEnabled'):
                raise ValueError('Sanitized/active display is not publishable')
            if record.get('originalModified') is True:
                raise ValueError('Renderer changed original Markdown')
        if bound.get('referenceMode') and pins.get('referenceMode')!=bound['referenceMode']:
            raise ValueError('Mixed source-only/training-assisted mode')
        artifacts = {}
        for artifact in manifest['artifacts']:
            name = artifact['path']
            if Path(name).name != name:
                raise ValueError('Render artifact must be one relative filename')
            content = (render / name).read_bytes()
            if sha(content) != artifact['sha256']:
                raise ValueError('Changed render artifact: ' + name)
            artifacts[name] = artifact
        html_file = render / pins['canonicalHtmlFilename']
        if html_file.name != cp.stem + '.html' or sha(html_file.read_bytes()) != pins['canonicalHtmlSha256']:
            raise ValueError('Changed or misnamed canonical HTML')
        if html_file.read_bytes() != (render / 'document.html').read_bytes():
            raise ValueError('Canonical HTML must be the rendered view')
        images = []
        for kind in ('layouts','diagrams'):
            for record in manifest[kind]:
                if record['status'] != 'PASS':
                    raise ValueError('Incomplete image render')
                name = record['id'] + '.png'
                if name not in artifacts:
                    raise ValueError('Missing bound image')
                images.append({'kind':kind[:-1], 'id':record['id'], 'sourceLines':record['sourceLines'],
                               'path':str(render / name), 'sha256':artifacts[name]['sha256'],
                               'width':record['png']['width'], 'height':record['png']['height']})
        rows.append({**entry, 'markdown':str(md), 'renderDirectory':str(render), 'canonicalHtml':str(html_file),
                     'rawMarkdown':raw.decode('utf-8-sig'), 'images':images})
    if not rows:
        raise ValueError('Empty delivery selection')
    return bound, rows, {'binding':str(binding_path), 'bindingSha256':sha(binding_bytes)}

def inline_text(token):
    pieces = []
    for child in token.children or []:
        if child.type in {'text','code_inline'}:
            pieces.append(child.content)
        elif child.type in {'softbreak','hardbreak'}:
            pieces.append('\n')
        elif child.type == 'html_inline':
            fragment = BeautifulSoup(child.content, 'html.parser')
            pieces.append('\n' if fragment.find('br') else fragment.get_text())
        elif child.type == 'image':
            pieces.append(child.content)
    return ''.join(pieces)

def parse_markdown(markdown, images):
    parser = MarkdownIt('commonmark', {'html':True}).enable('table')
    tokens = parser.parse(markdown)
    meta_tokens = [t for t in tokens if t.type == 'html_block' and re.fullmatch(r'\s*<!--\s*spec-meta:\s*(.*?)-->\s*',t.content,re.S)]
    if len(meta_tokens) != 1:
        raise ValueError('Exactly one real metadata block is required')
    match = re.fullmatch(r'\s*<!--\s*spec-meta:\s*(.*?)-->\s*', meta_tokens[0].content,re.S)
    meta = json.loads(match[1])
    if meta.get('schema') not in {'spec-md/1.0','spec-md/1.1'}:
        raise ValueError('Unsupported specification schema')
    image_map = {tuple(image['sourceLines']): image for image in images}
    title, preamble, sections, current = '', [], [], None
    lists=[]
    index = 0
    while index < len(tokens):
        token = tokens[index]
        target = preamble if current is None else current['blocks']
        lines = [token.map[0]+1, token.map[1]] if token.map else None
        if token.type == 'heading_open':
            value = inline_text(tokens[index+1])
            level = int(token.tag[1])
            if level == 1:
                if title: raise ValueError('Multiple document titles')
                title = value
            elif level == 2:
                current = {'heading':value, 'blocks':[]}; sections.append(current)
            else:
                target.append({'kind':'heading','text':value,'level':level,'sourceLines':lines})
            index += 3; continue
        if token.type in {'ordered_list_open','bullet_list_open'}:
            lists.append({'ordered':token.type=='ordered_list_open','next':int(token.attrGet('start') or 1),'prefix':None})
        elif token.type in {'ordered_list_close','bullet_list_close'}:
            lists.pop()
        elif token.type=='list_item_open' and lists:
            item=lists[-1]
            item['prefix']=(str(item['next'])+'. ') if item['ordered'] else '- '
            item['next']+=1
        if token.type == 'table_open':
            matrix, row, cell = [], None, None
            start = index
            while tokens[index].type != 'table_close':
                item = tokens[index]
                if item.type == 'tr_open': row=[]
                elif item.type in {'th_open','td_open'}: cell=''
                elif item.type == 'inline': cell=inline_text(item)
                elif item.type in {'th_close','td_close'}: row.append(cell)
                elif item.type == 'tr_close': matrix.append(row)
                index += 1
            if not matrix or any(len(row)!=len(matrix[0]) for row in matrix):
                raise ValueError('Nonrectangular table')
            target.append({'kind':'table','matrix':matrix,'sourceLines':[tokens[start].map[0]+1,tokens[start].map[1]]})
        elif token.type in {'paragraph_open'}:
            value = inline_text(tokens[index+1])
            pdf_text=value
            if lists and lists[-1]['prefix'] is not None:
                value=lists[-1]['prefix']+value;lists[-1]['prefix']=None
            # Prefixes preserve Markdown's displayed list order, never business prose.
            target.append({'kind':'paragraph','text':value,'pdfText':pdf_text,'sourceLines':lines})
        elif token.type in {'fence','code_block'}:
            block={'kind':'code','text':token.content.rstrip('\n'),'language':token.info.strip(), 'sourceLines':lines}
            if token.type=='fence' and token.info.strip()=='mermaid':
                if tuple(lines) not in image_map: raise ValueError('Mermaid has no same-line pinned PNG')
                block.update(kind='image', image=image_map[tuple(lines)])
            target.append(block)
        elif token.type == 'html_block' and token is not meta_tokens[0]:
            if tuple(lines) in image_map:
                target.append({'kind':'image','image':image_map[tuple(lines)], 'rawHtml':token.content,'sourceLines':lines})
            else:
                soup = BeautifulSoup(token.content, 'html.parser')
                for node in soup.select('style,script,meta'): node.decompose()
                if soup.find(['form','input','select','textarea','table']):
                    raise ValueError('Visible controls have no same-line pinned PNG')
                text = soup.get_text('\n',strip=True)
                if text: target.append({'kind':'paragraph','text':text,'rawHtml':token.content,'sourceLines':lines})
        index += 1
    if not title: raise ValueError('Document title required')
    return meta, title, preamble, sections

def col(number):
    result=''
    while number:
        number, remainder=divmod(number-1,26); result=chr(65+remainder)+result
    return result

def a1(row,start,end=None):
    return f'{col(start)}{row}' if end is None else f'{col(start)}{row}:{col(end)}{row}'

def text_width(value):
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(char) in {'F','W','A'} else 1 for char in value)

def cell_height(value, width):
    lines = sum(max(1,math.ceil(text_width(line)/max(1,width))) for line in value.split('\n'))
    if lines*15+9>409:
        raise ValueError('Cell would exceed readable Excel row height; revise source design without truncation')
    return max(24,lines*15+9)


APPROVAL_FRAMES = ['O23:Y23','Z23:AJ23','AK23:AU23','O24:Y28','Z24:AJ28','AK24:AU28']
COVER_EXTRA_FRAMES = APPROVAL_FRAMES + ['O36:AU36']
def cover_extra_operations(entry, preamble):
    # Explicit caller mapping references an existing Markdown preamble table cell.
    # Never guess approval/company values from source code, names or neighboring cells.
    bindings=entry.get('coverBindings',[])
    if not isinstance(bindings,list):raise ValueError('Explicit cover mapping must be a list')
    tables=[b for b in preamble if b['kind']=='table'];selected={}
    for item in bindings:
        if set(item)!={'range','sourceTable','sourceRow','sourceColumn'}:raise ValueError('Unknown cover source mapping fields')
        target=item['range']
        if target not in COVER_EXTRA_FRAMES or target in selected:raise ValueError('Unknown/duplicate cover frame target')
        indexes=[item[k] for k in ('sourceTable','sourceRow','sourceColumn')]
        if any(type(n) is not int or n<0 for n in indexes):raise ValueError('Cover source indexes must be explicit nonnegative integers')
        a,b,c=indexes
        if a>=len(tables) or b>=len(tables[a]['matrix']) or c>=len(tables[a]['matrix'][b]):raise ValueError('Cover source cell outside original preamble')
        value=tables[a]['matrix'][b][c]
        if not isinstance(value,str) or len(value.encode('utf-16-le'))//2>32767 or any(ord(ch)<32 and ch not in '\t\r\n' for ch in value):raise ValueError('Cover literal cannot be represented')
        selected[target]=(value,tables[a]['sourceLines'],dict(item))
    operations=[]
    for target in COVER_EXTRA_FRAMES:
        value,lines,binding=selected.get(target,('',None,None))
        operation={'range':target,'value':value,'style':'cover-company-band' if target=='O36:AU36' else 'cover-cell','sourceLines':lines,'formatOnlyBlank':binding is None}
        if binding:operation['sourceCellBinding']=binding
        operations.append(operation)
    return operations

def new_sheet(name, role, columns):
    if not name or len(name)>31 or re.search(r'[/\\?*:\[\]]',name) or name.startswith("'") or name.endswith("'"):
        raise ValueError('Invalid declared sheet name')
    sheet={'name':name,'role':role,'columns':columns,'operations':[], 'images':[], 'rowHeights':{},'tables':[], 'lastRow':1}
    if role=='normal':
        if columns != GRID_COLUMNS: raise ValueError('V2-62 normal sheet geometry mismatch')
        sheet['gridColumnWidth']=GRID_COLUMN_WIDTH
    if role=='table':
        # Generic nine-column TABLE projection: reserve the final explanation
        # column for long literal text; do not truncate or reinterpret values.
        sheet['columnWidths']=[5,18,20,6,8,17,16,10,95]
    return sheet

def add_text(sheet, row, left, right, value, style='body', source_lines=None):
    if len(value.encode('utf-16-le'))//2 > 32767:
        raise ValueError('Excel text cell limit exceeded')
    if any(ord(char)<32 and char not in '\t\n\r' for char in value):
        raise ValueError('Unrepresentable control character in source cell')
    sheet['operations'].append({'range':a1(row,left,right), 'value':value, 'style':style, 'sourceLines':source_lines})
    width=(right-left+1)*GRID_TEXT_UNITS_PER_COLUMN if sheet['role']=='normal' else sum(sheet['columnWidths'][left-1:right])*13/18 if 'columnWidths' in sheet else (right-left+1)*13
    sheet['rowHeights'][str(row)]=max(sheet['rowHeights'].get(str(row),24),cell_height(value,max(8,width)))
    sheet['lastRow']=max(sheet['lastRow'],row)

def add_matrix(sheet, row, matrix, grid=False, source_lines=None):
    columns=len(matrix[0]); begin=row
    if sheet['role']=='list' and not grid:
        # Whole ASCII identifiers/numbers reserve sufficient width before the
        # existing height gate. Canonical matrices remain one record per row.
        widths=[]
        longest=[]
        for index in range(columns):
            tokens=[token.group() for values in matrix for token in re.finditer(r'[A-Za-z0-9_]+(?:[.\-][A-Za-z0-9_]+)*',values[index])]
            token_length=max((len(token) for token in tokens),default=0)
            width=max(18,math.ceil((token_length+4)*18/13/2)*2)
            while True:
                if width>120:raise ValueError('LIST indivisible token or row exceeds bounded width; no truncation permitted')
                try:
                    heights=[cell_height(values[index],max(8,width*13/18)) for values in matrix]
                    if max(heights)<=350:break
                except ValueError as exc:
                    if 'readable Excel row height' not in str(exc):raise
                width+=2
            widths.append(width);longest.append(token_length)
        sheet['columnWidths']=widths
        sheet['geometryProjection']={'kind':'adaptive-list-whole-token-width-only','originalDefaultColumnWidth':18,'widths':widths,'longestAsciiTokenCharacters':longest,'literalMatrixOrderPreserved':True,'maxTargetRowHeightPt':350,'maximumWidth':120}
    if columns>sheet['columns']: raise ValueError('Table exceeds worksheet width')
    spans=[]
    if grid:
        # Integer ranges consume exactly the declared GRID canvas.
        for index in range(columns): spans.append((index*sheet['columns']//columns+1,(index+1)*sheet['columns']//columns))
    else: spans=[(index+1,index+1) for index in range(columns)]
    for ordinal, values in enumerate(matrix):
        for (left,right), value in zip(spans, values):
            add_text(sheet,row,left,right,value,'table-header' if ordinal==0 else 'table-cell',source_lines)
        row+=1
    sheet['tables'].append({'range':f'A{begin}:{col(sheet['columns'] if grid else columns)}{row-1}', 'headerRow':begin,
                            'header':matrix[0], 'recordCount':len(matrix)-1,'grid':grid})
    return row

def add_blocks(sheet, blocks, row, image_max_width=1100):
    for block in blocks:
        if block['kind']=='table': row=add_matrix(sheet,row,block['matrix'],grid=sheet['role']=='normal',source_lines=block['sourceLines'])+1
        elif block['kind']=='image':
            image=block['image']; width=min(image_max_width,image['width']); height=round(image['height']*width/image['width'])
            count=math.ceil(height/20)+1
            sheet['images'].append({**image,'row':row-1,'col':1,'displayWidth':width,'displayHeight':height})
            for offset in range(count): sheet['rowHeights'][str(row+offset)]=15
            row+=count+1; sheet['lastRow']=max(sheet['lastRow'],row)
        else:
            text=block['text']
            # Lossless continuation at fixed character offsets for narrative only.
            pieces=[text[i:i+850] for i in range(0,len(text),850)] or ['']
            for piece in pieces:
                add_text(sheet,row,1 if block['kind']=='heading' or sheet['role']!='normal' else GRID_BODY_START_COLUMN,sheet['columns'],piece,
                         'heading' if block['kind']=='heading' else 'code' if block['kind']=='code' else 'body',block['sourceLines'])
                row+=1
    return row

def document_model(entry, image_max_width=1100, preview_max_height=None):
    if not 1<=image_max_width<=GRID_IMAGE_MAX_WIDTH:raise ValueError('Image projection exceeds bounded V2-62 canvas')
    meta,title,preamble,sections=parse_markdown(entry['rawMarkdown'],entry['images'])
    if meta['documentId']!=entry['documentId'] or meta.get('path')!=entry['canonicalDocumentPath']:
        raise ValueError('Metadata does not match selected canonical document')
    used=set(); sheets=[]
    if meta.get('layout')=='TABLE':
        if meta.get('schema')!='spec-md/1.1' or len(meta['sheets'])!=1 or meta.get('columns')!=TABLE_COLUMNS:
            raise ValueError('TABLE declaration mismatch')
        declarations=meta['sections']
        if [(s['heading'],s['kind']) for s in declarations]!=[('テーブルヘッダー','HEADER'),('項目詳細','LIST')]:
            raise ValueError('TABLE section order mismatch')
        if [s['heading'] for s in sections]!=[s['heading'] for s in declarations]:
            raise ValueError('TABLE chapter mismatch')
        sheet=new_sheet(meta['sheets'][0]['sheet'],'table',9)
        add_text(sheet,1,1,9,title,'title'); row=3
        # Keep author-provided ID/version/preamble in its original order on the
        # declared TABLE sheet. This changes only cell placement, never prose.
        if preamble:
            row=add_blocks(sheet,preamble,row,image_max_width)
            row+=1
        for section in sections:
            if len(section['blocks'])!=1 or section['blocks'][0]['kind']!='table': raise ValueError('TABLE requires one table per section')
            add_text(sheet,row,1,9,section['heading'],'heading');row+=1
            block=section['blocks'][0]; matrix=block['matrix']
            if section['heading']=='テーブルヘッダー':
                if len(matrix[0])!=2: raise ValueError('TABLE header must have two columns')
                for ordinal, values in enumerate(matrix):
                    add_text(sheet,row,1,2,values[0],'table-header' if ordinal==0 else 'table-cell',block['sourceLines'])
                    add_text(sheet,row,3,9,values[1],'table-header' if ordinal==0 else 'table-cell',block['sourceLines']); row+=1
                row+=1
            else:
                if matrix[0]!=TABLE_COLUMNS: raise ValueError('Nine-column TABLE header mismatch')
                row=add_matrix(sheet,row,matrix,source_lines=block['sourceLines'])
        sheets=[sheet]
    else:
        declarations=meta['sheets']
        if [s['heading'] for s in sections]!=[s['heading'] for s in declarations]: raise ValueError('Declared chapter order mismatch')
        if preamble and (not declarations or declarations[0]['kind']!='GRID'):
            raise ValueError('Preamble preservation requires the first declared GRID chapter')
        cover=new_sheet('表紙','cover',47)
        cover['lastRow']=36
        cover['operations'].append({'range':'O6:AU9','value':title,'style':'cover-title','sourceLines':None})
        attrs=[row for b in preamble if b['kind']=='table' for row in b['matrix'][1:] if len(row)==2]
        for i, values in enumerate((attrs + [['',''],['',''],['','']])[:3]):
            start=12+i*3
            cover['operations'].append({'range':f'O{start}:W{start+2}','value':values[0],'style':'cover-cell','sourceLines':None})
            cover['operations'].append({'range':f'X{start}:AU{start+2}','value':values[1],'style':'cover-cell','sourceLines':None})
        cover['operations'].extend(cover_extra_operations(entry,preamble))
        sheets.append(cover);used.add('表紙'.casefold())
        for ordinal,(decl, section) in enumerate(zip(declarations,sections)):
            kind=decl['kind']
            if kind not in {'GRID','LIST'}: raise ValueError('Unsupported chapter kind')
            if decl['sheet'].casefold() in used: raise ValueError('Duplicate/reserved declared sheet')
            used.add(decl['sheet'].casefold())
            blocks=section['blocks']
            if kind=='LIST':
                if len(blocks)!=1 or blocks[0]['kind']!='table': raise ValueError('LIST must have one rectangular table')
                matrix=blocks[0]['matrix']
                if section['heading']=='項目一覧' and len(matrix[0])!=10: raise ValueError('Item LIST requires the declared ten-column form')
                sheet=new_sheet(decl['sheet'],'list',len(matrix[0]))
                sheet['itemList']=section['heading']=='項目一覧'
                add_matrix(sheet,1,matrix,source_lines=blocks[0]['sourceLines'])
            else:
                sheet=new_sheet(decl['sheet'],'normal',GRID_COLUMNS)
                add_text(sheet,1,1,GRID_COLUMNS,section['heading'],'title')
                if ordinal==0: add_blocks(sheet,preamble,3,image_max_width)
                row=sheet['lastRow']+2
                add_blocks(sheet,blocks,row,image_max_width)
            sheets.append(sheet)
    for sheet in sheets:
        sheet['printArea']='O6:AU36' if sheet['role']=='cover' else f'A1:{col(sheet['columns'])}{sheet['lastRow']}'
        sheet['previewTiles']=[{'range':f'A{row}:{col(sheet['columns'])}{min(row+44,sheet['lastRow'])}'} for row in range(1,sheet['lastRow']+1,45)]
        if preview_max_height:
            if not 600<=preview_max_height<=1400:raise ValueError('Preview height outside QA viewport')
            sheet['previewTiles']=[];begin=1;pixels=0
            for row in range(1,sheet['lastRow']+1):
                height=sheet['rowHeights'].get(str(row),15)*4/3
                if row>begin and (pixels+height>preview_max_height or row-begin>=45):
                    sheet['previewTiles'].append({'range':f'A{begin}:{col(sheet['columns'])}{row-1}'});begin=row;pixels=0
                pixels+=height
            sheet['previewTiles'].append({'range':f'A{begin}:{col(sheet['columns'])}{sheet["lastRow"]}'})
    all_blocks=preamble+sum([s['blocks'] for s in sections],[])
    html_cells=[cell.get_text(' ',strip=True) for b in all_blocks if b.get('rawHtml')
                for cell in BeautifulSoup(b['rawHtml'],'html.parser').select('table th,table td') if cell.get_text(strip=True)]
    return {'documentId':entry['documentId'], 'canonicalDocumentPath':entry['canonicalDocumentPath'],
            'markdown':entry['markdown'],'markdownSha256':entry['markdownSha256'], 'renderDirectory':entry['renderDirectory'],
            'renderPinsSha256':entry['renderPinsSha256'],'renderManifestSha256':entry['renderManifestSha256'],
            'title':title,'sourceMetadata':meta,'rawMarkdown':entry['rawMarkdown'], 'formatProfile':FORMAT_PROFILE, 'sheets':sheets,
            'visibleCoverage':[b.get('pdfText',b['text']) for b in all_blocks if 'text' in b and b['kind']!='image']+
                [cell for b in all_blocks if b['kind']=='table' for row in b['matrix'] for cell in row if cell]+html_cells}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--binding',type=Path,required=True); parser.add_argument('--model',type=Path,required=True)
    parser.add_argument('--image-max-width',type=int,default=1100)
    parser.add_argument('--preview-max-height',type=int,default=None)
    args=parser.parse_args()
    bound, entries, provenance=load_bound(args.binding)
    model={'schema':SCHEMA, **provenance,'sourceSnapshotManifestSha256':bound['sourceSnapshotManifestSha256'],
           'referenceMode':bound.get('referenceMode'),
           'formatProfile':FORMAT_PROFILE,
           'projection':{'imageMaxWidth':args.image_max_width,'previewMaxHeight':args.preview_max_height},
           'documents':[document_model(entry,args.image_max_width,args.preview_max_height) for entry in entries], 'businessContentAuthored':False,
           'visualReview':'PENDING','applicationExecuted':False}
    output=safe_path(args.model)
    roots=[safe_path(bound['permittedMarkdownRoot']),safe_path(bound['permittedRenderRoot']),safe_path(args.binding)]
    if any(output==p or output.is_relative_to(p) or p.is_relative_to(output) for p in roots):
        raise ValueError('Model output must be disjoint from pinned inputs')
    if output.exists(): raise ValueError('Fresh model output required')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    load_bound(args.binding)
    print(json.dumps({'documents':len(entries),'modelSha256':sha(output.read_bytes()),'visualReview':'PENDING'}))

if __name__=='__main__': main()
