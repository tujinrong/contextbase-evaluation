"""Markdown -> explicit, reviewable workbook layout. No business inference here."""
from __future__ import annotations
import hashlib
import math
import re
import unicodedata
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
from markdown_it import MarkdownIt

HEADERS = ['No','グループ','項目名','種類','入出力','DB連携項目','候補取得元','必須','形式・桁','説明']
ITEM_WIDTHS = [5,14,20,13,9,24,24,14,21,40]
SCHEMA = 'contextbase.md-excel.v1'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def col(index: int) -> str:
    result = ''
    while index:
        index, digit = divmod(index-1, 26)
        result = chr(65+digit) + result
    return result


def plain(node) -> str:
    if isinstance(node, NavigableString):
        return str(node)
    if node.name in {'script','style','iframe','object','template'}:
        return ''
    if node.name == 'br':
        return '\n'
    if node.name == 'img':
        return '[画像] ' + node.get('alt','') + ' (' + node.get('src','') + ')'
    if node.name == 'a':
        text = ''.join(plain(x) for x in node.children)
        href = node.get('href','')
        return text + (f' ({href})' if href and href != text else '')
    return ''.join(plain(x) for x in node.children)


def text(node) -> str:
    return re.sub(r'[ \t]+',' ',plain(node)).strip()


def sheet_name(value: str, used: set[str]) -> str:
    base = re.sub(r'[\[\]*:/\\?\x00-\x1f]','_',value).strip(" '") or '本文'
    base = base[:31]
    result, index = base, 2
    while result.casefold() in used:
        suffix = f'_{index}'
        result = base[:31-len(suffix)] + suffix
        index += 1
    used.add(result.casefold())
    return result


def width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in 'FWA' else 1 for c in text)


def wrap(value: str, limit: int) -> list[str]:
    lines = []
    for original in value.split('\n'):
        buf, count = '', 0
        for ch in original:
            cw = width(ch)
            if count+cw > limit and buf:
                lines.append(buf);buf='';count=0
            buf+=ch;count+=cw
        lines.append(buf)
    return lines


def blocks(nodes):
    """Preserve order of paragraphs, lists, headings, tables and literal code."""
    result = []
    for node in nodes:
        if isinstance(node, NavigableString):
            if str(node).strip():result.append(('text',str(node).strip()))
            continue
        name = node.name
        if name in {'script','style','iframe','object','template'}:continue
        if name == 'table':
            matrix=[]
            for tr in node.find_all('tr'):
                matrix.append([text(x) for x in tr.find_all(['th','td'],recursive=False)])
            if matrix:result.append(('table',matrix))
        elif name in {'ul','ol'}:
            for i, li in enumerate(node.find_all('li',recursive=False),1):
                result.append(('text', ('・' if name=='ul' else f'{i}. ') + text(li)))
        elif name in {'h1','h2','h3','h4','h5','h6'}:
            result.append(('heading',text(node)))
        elif name == 'pre':
            result.append(('code',node.get_text().rstrip('\n')))
        elif name in {'p','blockquote','img'}:
            value=text(node)
            if value:result.append(('text',value))
        elif name not in {'hr','br'}:
            result.extend(blocks(node.children))
    return result


def markdown_model(markdown: str, source: str, *, repository: str = '', revision: str = 'main') -> dict:
    soup = BeautifulSoup(MarkdownIt('commonmark',{'html':True}).enable('table').render(markdown),'html.parser')
    title_node = soup.find('h1')
    title = text(title_node) if title_node else Path(source).stem
    sections=[]; current=('概要',[]); preface=[]; started=False
    for node in list(soup.children):
        if node is title_node:continue
        if getattr(node,'name',None)=='h2':
            if started and blocks(current[1]):sections.append(current)
            elif not started:preface=blocks(current[1])
            started=True
            name=re.sub(r'^\d+[.．、]\s*','',text(node))
            current=({'システム概要':'概要'}.get(name,name),[])
        else:current[1].append(node)
    if blocks(current[1]):sections.append(current)
    if not sections:sections=[('本文',[])]
    digest=sha(markdown.encode('utf-8'))
    cover=[('heading','文書情報'),('table',[
        ['項目','内容'],['文書名',title],['原本Markdown',source],
        ['機能ID', (re.search(r'F-[A-F0-9]+',source).group() if re.search(r'F-[A-F0-9]+',source) else '共通')],
        ['変換元SHA-256',digest],
        ['原本参照',f'https://github.com/{repository}/blob/{revision}/output/md/{source}' if repository else source],
        ['作成方針','MDを正本として章・表・項目順を保存する。仮定はMDの表記を引き継ぐ。']])]
    cover.extend(preface)
    all_sections=[('表紙',cover)]+[(name,blocks(nodes)) for name,nodes in sections]
    used=set();sheets=[];warnings=[]
    for name, content in all_sections:
        name=sheet_name(name,used)
        maxcols=max((max(map(len,b[1])) for b in content if b[0]=='table'),default=2)
        if maxcols>40:raise ValueError('Tables with over 40 columns require an explicit split')
        n=max(maxcols,2)
        widths = ITEM_WIDTHS[:] if n==10 and any(b[0]=='table' and b[1][0]==HEADERS for b in content) else ([22,72] if n==2 else [max(10,min(36,120/n))]*n)
        rows=[{'values':[title], 'style':'title','merge':True,'height':34},
              {'values':[name], 'style':'section','merge':True,'height':26},
              {'values':[], 'style':'body','height':10}]
        table_headers=[];table_ranges=[]
        for kind,value in content:
            if kind=='table':
                start=len(rows)+1
                table_headers.append(start)
                table= value
                table_n=max(map(len,table))
                for k, cells in enumerate(table):
                    # Tall cells are continued in extra rows; no silent 32767-character truncation.
                    wrapped=[wrap(v,max(4,int(widths[i])-3)) for i,v in enumerate(cells)]
                    chunks=max(1,math.ceil(max(map(len,wrapped),default=1)/18))
                    if chunks>1:warnings.append(f'{name}: 長い表セルを{chunks}行に分割')
                    for chunk in range(chunks):
                        vals=['\n'.join(lines[chunk*18:(chunk+1)*18]) for lines in wrapped]
                        h=min(300,max(30,16*max((v.count('\n')+1 for v in vals),default=1)+10))
                        rows.append({'values':vals,'style':'header' if k==0 else 'body' if k%2 else 'stripe','height':h})
                table_ranges.append((start,len(rows),table_n))
                rows.append({'values':[], 'style':'body','height':10})
            else:
                if not value:continue
                limit=max(40,int(sum(widths)*0.95)-3)
                lines=wrap(value,limit)
                for start in range(0,len(lines),16):
                    part='\n'.join(lines[start:start+16])
                    rows.append({'values':[part], 'style':'section' if kind=='heading' else 'code' if kind=='code' else 'body',
                                 'merge':True,'height':max(28,16*(part.count('\n')+1)+10)})
        sheets.append({'name':name,'widths':widths,'rows':rows,
                       'repeat':4 if table_headers and table_headers[0]==4 else 2,
                       'filter':table_ranges[0] if len(table_ranges)==1 and name=='項目一覧' and table_ranges[0][1]>table_ranges[0][0] else None,
                       'paper':'A3' if n>=8 else 'A4'})
    if soup.find('img'):warnings.append('画像は代替テキストと参照先を保存。画像そのものの埋め込みは対象外')
    if soup.find('code',class_='language-mermaid'):warnings.append('Mermaidは定義を文字列で保存。Excel図形への変換は対象外')
    return {'schema':SCHEMA,'title':title,'source':source,'source_sha256':digest,'sheets':sheets,'warnings':warnings}


def expected_values(sheet: dict) -> dict[str,str]:
    return {f'{col(c)}{r}':str(v) for r,row in enumerate(sheet['rows'],1)
            for c,v in enumerate(row['values'],1) if str(v)!=''}
