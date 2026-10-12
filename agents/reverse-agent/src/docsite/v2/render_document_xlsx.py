"""V2 Markdown-to-Excel renderer migrated to ContextBase's layout model.

Based on spec-tools/doc-tools/render_document_xlsx.py (7bf3a20b).
Preserves V2 cover/header bands, 62-column narrative grid, 10-column item list,
heading levels, embedded images and event page boundaries. Instead of importing
V2's project-global openpyxl/HTML/Word controllers, emits a data-only model to
ContextBase's portable package writer. Visual review uses artifact_tool.
See PROVENANCE.json for exact source/attachment identities and adaptations.
"""
from __future__ import annotations
import base64
import hashlib
import io
import math
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit
from bs4 import BeautifulSoup, NavigableString, Comment
from markdown_it import MarkdownIt
from PIL import Image
from ..excel_model import HEADERS, col, wrap, plain
from .upstream_layout import (proportional_spans, safe_sheet_title, HEADER_BANDS,
                              COVER_MERGES, ITEM_WIDTHS, CENTER_ALIGNED_TABLE_HEADERS)

VERSION = 'v2-migrated-2.0'


def column_number(value):
    number=0
    for ch in value:number=number*26+ord(ch)-64
    return number


def range_parts(ref):
    a,b=ref.split(':') if ':' in ref else (ref,ref)
    ca,ra=re.fullmatch(r'([A-Z]+)(\d+)',a).groups()
    cb,rb=re.fullmatch(r'([A-Z]+)(\d+)',b).groups()
    return column_number(ca),int(ra),column_number(cb),int(rb)


def block_text(node):
    return plain(node).strip()


def parse_blocks(nodes):
    out=[]
    for node in nodes:
        if isinstance(node,Comment):continue
        if isinstance(node,NavigableString):
            if str(node).strip():out.append({'kind':'paragraph','value':str(node).strip()})
            continue
        name=node.name
        if name in {'script','style','iframe','object','template'}:continue
        if name=='img':out.append({'kind':'image','path':node.get('src',''),'alt':node.get('alt','')})
        elif name=='table':
            rows=[[block_text(c) for c in tr.find_all(['th','td'],recursive=False)] for tr in node.find_all('tr')]
            if rows:out.append({'kind':'table','value':rows})
        elif name in {'h1','h2','h3','h4','h5','h6'}:
            out.append({'kind':'heading','value':block_text(node),'level':int(name[1])})
        elif name in {'ul','ol'}:
            for i,li in enumerate(node.find_all('li',recursive=False),int(node.get('start',1))):
                out.append({'kind':'paragraph','value':(f'{i}. ' if name=='ol' else '- ')+block_text(li)})
        elif name=='pre':
            code=node.find('code');classes=code.get('class',[]) if code else []
            out.append({'kind':'code','value':node.get_text().rstrip('\n'),'mermaid':'language-mermaid' in classes})
        elif name in {'p','blockquote'}:
            if node.find('img'):
                # Preserve image order and captions rather than flattening an image to text.
                out.extend(parse_blocks(node.children))
            else:out.append({'kind':'paragraph','value':block_text(node)})
        elif name not in {'hr','br'}:out.extend(parse_blocks(node.children))
    return out


def sections_for_render(markdown):
    soup=BeautifulSoup(MarkdownIt('commonmark',{'html':True}).enable('table').render(markdown),'html.parser')
    h1=soup.find('h1');title=block_text(h1) if h1 else ''
    sections=[];name='概要';nodes=[]
    for node in soup.children:
        if node is h1:continue
        if getattr(node,'name',None)=='h2':
            previous=parse_blocks(nodes)
            next_name=re.sub(r'^\d+[.．、]\s*','',block_text(node))
            next_name={'システム概要':'概要'}.get(next_name,next_name)
            if previous and not sections and name==next_name=='概要':
                # Initial document introduction belongs to its first overview sheet.
                continue
            if previous:sections.append((name,previous))
            name=re.sub(r'^\d+[.．、]\s*','',block_text(node))
            if name=='システム概要':name='概要'
            nodes=[]
        else:nodes.append(node)
    if parse_blocks(nodes):sections.append((name,parse_blocks(nodes)))
    return title,sections


def new_sheet(name,widths):
    return {'name':name,'widths':widths,'rows':[],'merges':[],'cell_styles':{},
            'images':[],'repeat':1,'filter':None,'paper':'A4','breaks':[],'style_family':'v2'}


def ensure_row(s,r):
    while len(s['rows'])<r:s['rows'].append({'values':[],'style':'blank','height':18})


def put(s,r,c,value,style='body',end=None):
    ensure_row(s,r);values=s['rows'][r-1]['values']
    while len(values)<c:values.append('')
    if values[c-1] not in ('',value):raise ValueError(f'Duplicate cell {s["name"]}!{col(c)}{r}')
    values[c-1]=str(value)
    if end and end>c:s['merges'].append(f'{col(c)}{r}:{col(end)}{r}')
    for k in range(c,(end or c)+1):s['cell_styles'][f'{col(k)}{r}']=style


def band(s,ref,value,style):
    c,r,d,t=range_parts(ref)
    ensure_row(s,t);put(s,r,c,value,style)
    s['merges'].append(ref)
    for j in range(r,t+1):
        for k in range(c,d+1):s['cell_styles'][f'{col(k)}{j}']=style


def fill_cover(metadata):
    s=new_sheet('表紙',[3]*47);ensure_row(s,36)
    values=[metadata['documentLabel'],'システム名',metadata['systemName'],'機能ID',metadata['functionId'],
            '画面名',metadata['functionName'],'作成','査閲','承認','','','',metadata['companyName']]
    for i,(ref,value) in enumerate(zip(COVER_MERGES,values)):
        style='cover_title' if i==0 else 'cover_label' if i in {1,3,5,7,8,9} else 'cover_value' if i in {2,4,6} else 'approval' if i in {10,11,12} else 'company'
        band(s,ref,value,style)
    s.update(print_area='O6:AU36',fit_height=1,repeat=0,role='cover')
    return s


def write_section_header(s,section_title,metadata):
    ensure_row(s,2);s['rows'][0]['height']=28;s['rows'][1]['height']=18
    for ref,value,style in HEADER_BANDS:
        band(s,ref,section_title if value=='section' else metadata.get(value,value),style)


def write_merged_text(s,row,value,start=2,end=62,style='narrative'):
    # V2 used a 168-unit width cap for Java web narrative. Split tall content
    # instead of clipping it at a fixed row-height cap.
    width=max(12,round((end-start+1)*2.75)) if len(s['widths'])==62 else max(24,int(sum(s['widths'][start-1:end])*0.90))
    lines=wrap(value,width)
    for offset in range(0,len(lines),12):
        part='\n'.join(lines[offset:offset+12]);put(s,row,start,part,style,end)
        s['rows'][row-1]['height']=max(21,17*(part.count('\n')+1)+7);row+=1
    return row


def write_heading(s,row,block):
    if block.get('level',3)<=3:
        put(s,row,1,block['value'],'section',62);s['rows'][row-1]['height']=24
    else:
        put(s,row,2,'◆'+block['value'].lstrip('◆'),'subheading',62);s['rows'][row-1]['height']=22
    return row+1


def table_grid_ranges(headers):
    # V2's C:BJ table area and proportional allocation algorithm.
    n=len(headers)
    if n==3 and headers[0]=='処理区分':weights=[14,24,22]
    elif n==3 and '遷移先' in headers[-1]:weights=[18,18,24]
    else:weights=[1 if h in CENTER_ALIGNED_TABLE_HEADERS else 3 if h in {'説明','処理','期待結果','内容','結果・表示'} else 2 for h in headers]
    spans=proportional_spans(60,weights,min_span=1)
    ranges=[];c=3
    for span in spans:ranges.append((c,c+span-1));c+=span
    return ranges


def write_grid_table(s,row,matrix):
    headers=matrix[0];ranges=table_grid_ranges(headers)
    for i,values in enumerate(matrix):
        if len(values)!=len(headers):raise ValueError('Ragged table in Markdown')
        lines=[wrap(v,max(8,int((b-a+1)*2.7))) for (a,b),v in zip(ranges,values)]
        count=max(math.ceil(len(v)/12) for v in lines)
        for chunk in range(count):
            height=24
            for (a,b),ls,h in zip(ranges,lines,headers):
                value='\n'.join(ls[chunk*12:(chunk+1)*12])
                style='header' if i==0 else 'center' if h in CENTER_ALIGNED_TABLE_HEADERS else 'body'
                put(s,row,a,value,style,b);height=max(height,16*(value.count('\n')+1)+6)
            s['rows'][row-1]['height']=height;row+=1
    ensure_row(s,row);s['rows'][row-1]['height']=9
    return row+1


def resolve_image(path,markdown_path,allowed_root):
    uri=urlsplit(path)
    if uri.scheme or uri.netloc:raise ValueError('Only local document images are accepted')
    if markdown_path is None:raise ValueError('A local Markdown path is needed for images')
    p=markdown_path.parent/unquote(uri.path);root=(allowed_root or markdown_path.parent).resolve()
    if p.is_symlink() or not p.resolve().is_relative_to(root):raise ValueError('Image escapes document root')
    for parent in p.parents:
        if parent==root:break
        if parent.is_symlink():raise ValueError('Image symlink path is prohibited')
    if not p.is_file() or p.stat().st_size>12_000_000:raise ValueError('Missing or oversized document image')
    data=p.read_bytes()
    with Image.open(io.BytesIO(data)) as image:
        image.verify()
    with Image.open(io.BytesIO(data)) as image:
        if image.width*image.height>25_000_000:raise ValueError('Image dimensions exceed limit')
        image=image.convert('RGB');width,height=image.size
        buffer=io.BytesIO();image.save(buffer,format='PNG');data=buffer.getvalue()
    return data,width,height


def add_image(s,row,block,markdown_path,allowed_root):
    data,w,h=resolve_image(block['path'],markdown_path,allowed_root)
    # The 61 x 3-width narrative canvas is 61 x approximately 21px on Excel's 96dpi grid.
    display=min(w,1200);height=round(h*display/w)
    s['images'].append({'col':1,'row':row-1,'width':display,'height':height,
                        'alt':block['alt'],'data':base64.b64encode(data).decode(),
                        'sha256':hashlib.sha256(data).hexdigest()})
    needed=math.ceil(height/24)+1
    ensure_row(s,row+needed)
    return row+needed+1


def write_blocks(s,blocks,markdown_path,allowed_root):
    row=3;event_seen=False;warnings=[]
    for block in blocks:
        kind=block['kind']
        if kind=='heading':
            if s['name']=='イベント仕様' and block.get('level',3)==3:
                if event_seen:s['breaks'].append(row-1)
                event_seen=True
            row=write_heading(s,row,block)
        elif kind=='table':row=write_grid_table(s,row,block['value'])
        elif kind=='image':row=add_image(s,row,block,markdown_path,allowed_root)
        else:
            row=write_merged_text(s,row,block['value'],style='code' if kind=='code' else 'narrative')
            if block.get('mermaid'):warnings.append('Mermaid definition retained; provide a local PNG for a diagram image')
    ensure_row(s,row);s['print_area']=f'A1:BJ{row}'
    return warnings


def write_list_section(name,blocks,metadata):
    s=new_sheet(name,ITEM_WIDTHS[:]);s['repeat']=2;s['freeze']=2
    put(s,1,1,name,'list_title',10);s['rows'][0]['height']=30
    row=2;table_count=0
    for block in blocks:
        if block['kind']!='table':
            row=write_merged_text(s,row,block['value'],start=1,end=10)
            continue
        matrix=block['value'];headers=matrix[0]
        if len(headers)!=10:raise ValueError('V2 basic item list requires ten columns')
        start=row;table_count+=1
        for i,values in enumerate(matrix):
            if len(values)!=10:raise ValueError('Malformed ten-column item row')
            # Longer descriptions are fully readable, not V2's fixed 18pt row.
            ls=[wrap(v,max(6,int(w)-2)) for v,w in zip(values,ITEM_WIDTHS)]
            count=max(math.ceil(len(x)/18) for x in ls)
            for chunk in range(count):
                height=22
                for c,(text_lines,header) in enumerate(zip(ls,headers),1):
                    value='\n'.join(text_lines[chunk*18:(chunk+1)*18])
                    style='header' if i==0 else 'center' if header in CENTER_ALIGNED_TABLE_HEADERS else 'body'
                    put(s,row,c,value,style);height=max(height,16*(value.count('\n')+1)+6)
                s['rows'][row-1]['height']=height;row+=1
        if table_count==1:s['filter']=(start,row-1,10)
        else:s['filter']=None
    ensure_row(s,row);s['print_area']=f'A1:J{row}'
    return s


def markdown_model(markdown,source,*,repository='',revision='main',markdown_path=None,allowed_root=None):
    title,sections=sections_for_render(markdown)
    title=title or Path(source).stem
    meta={'documentLabel':'基本設計書' if '設計書' in source or '仕様書' in source else title,
          'systemName':'','functionName':title,'functionId':'','physicalName':'',
          'author':'','generatedAt':'','companyName':''}
    for name,blocks in sections:
        if name=='表紙':
            fields={row[0]:row[1] for b in blocks if b['kind']=='table' for row in b['value'][1:] if len(row)==2}
            for jp,en in [('システム名','systemName'),('機能ID','functionId'),('画面名','functionName'),('文書名','documentLabel'),('作成日','generatedAt'),('会社名','companyName')]:
                if jp in fields:meta[en]=fields[jp]
    if not meta['functionId']:
        m=re.search(r'F-[A-F0-9]+',source);meta['functionId']=m[0] if m else '共通'
    sheets=[fill_cover(meta)];used={'表紙'};warnings=[]
    for name,blocks in sections:
        if name=='表紙':continue
        name=safe_sheet_title(name,used)
        if name=='項目一覧' and any(b['kind']=='table' and b['value'][0]==HEADERS for b in blocks):
            sheets.append(write_list_section(name,blocks,meta))
        else:
            sheet=new_sheet(name,[3]*62);write_section_header(sheet,name,meta)
            warnings.extend(write_blocks(sheet,blocks,markdown_path,allowed_root));sheets.append(sheet)
    return {'schema':'contextbase.md-excel.v2','source':source,'source_sha256':hashlib.sha256(markdown.encode()).hexdigest(),
            'title':title,'metadata':meta,'sheets':sheets,'warnings':warnings,'renderer':VERSION,
            'provenance':'source-to-doc-v2/spec-tools/doc-tools/render_document_xlsx.py@7bf3a20b'}
