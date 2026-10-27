"""P2-only, offline static markup projection and source-linked visual assets.

C#/Razor and input JavaScript are NEVER executed. Only sanitized DOM/CSS is
rendered by a browser. Screen-specific values are not copied from sample data.
Unsupported dynamic content is disclosed via QA and metadata, not fabricated.
"""
from __future__ import annotations
import html
import io
import math
from pathlib import Path
import re
import shutil
import subprocess
from bs4 import BeautifulSoup, Comment, NavigableString
from PIL import Image
from contextbase.shared.store import digest, safe, write


BASE_CSS = '''*{box-sizing:border-box}body{margin:0;font-family:"Noto Sans CJK JP","Yu Gothic",sans-serif}
.container{max-width:1240px;margin:auto;padding:12px}.d-flex{display:flex}.navbar-nav{display:flex;gap:20px;list-style:none}
.navbar>.container-fluid{display:flex;align-items:center;gap:24px}.navbar-brand{font-size:20px;color:white!important;white-space:nowrap}.navbar-toggler{display:none}.navbar-nav{margin:0;padding:0}.navbar{padding:12px 0}.navbar a{color:inherit;text-decoration:none}.form-control,.form-select{font:inherit;border:1px solid #aaa;padding:3px}
[hidden]{display:none!important}iframe{border:1px dashed #aaa}button{font:inherit}body{overflow:visible!important}
'''


def remove_razor_expressions(text):
    # Balanced inline @(...) and code-only @{...}; never evaluates either.
    for opener, closer in [('@(', ')'), ('@{','}')]:
        while True:
            at=text.find(opener)
            if at<0: break
            depth=1; i=at+2; quote=None; esc=False
            while i<len(text) and depth:
                ch=text[i]
                if quote:
                    if esc:esc=False
                    elif ch=='\\':esc=True
                    elif ch==quote:quote=None
                elif ch in {'"',"'"}:quote=ch
                elif ch==opener[1]:depth+=1
                elif ch==closer:depth-=1
                i+=1
            segment=text[at:i]
            text=text[:at]+''.join('\n' if c=='\n' else ' ' for c in segment)+text[i:]
    return text


def sanitize_markup(text, item_types=None):
    item_types=item_types or {}
    text=re.sub(r'<%[\s\S]*?%>','',text)
    text=re.sub(r'\$\{[^}]*\}','',text)
    text=re.sub(r'@\*[\s\S]*?\*@','',text)
    text=re.sub(r'^\s*@(?:page|model|using|inject|addTagHelper|namespace)\b[^\n]*','',text,flags=re.M)
    text=text.replace('@RenderBody()','__CONTEXTBASE_BODY__')
    text=remove_razor_expressions(text)
    text=re.sub(r'@(?:Html\.Raw|await\s+RenderSectionAsync|RenderSection)\([^\n]*?\)','',text)
    soup=BeautifulSoup(text,'html.parser')
    for tag in soup(['script','link','base','object','embed','meta','partial']):tag.decompose()
    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if attr.lower().startswith('on') or attr in {'src','srcset','href','formaction','action','srcdoc'}:del tag[attr]
        binding=tag.get('asp-for') or tag.get('name')
        if tag.name=='label' and tag.get('asp-for'):tag['for']=tag['asp-for'].replace('.','_')
        if binding and tag.name in {'input','select','textarea'}:
            tag['name']=binding;tag['id']=tag.get('id',binding.replace('.','_'))
            if tag.name=='input' and not tag.get('type'):
                tag['type']='checkbox' if item_types.get(binding)=='CheckBox' else 'text'
        if tag.name=='input':
            if '@' in str(tag.get('value','')):tag['value']=''
            for key in ['readonly','disabled','checked']:
                if '@' in str(tag.get(key,'')):tag.attrs.pop(key,None)
        for attr in list(tag.attrs):
            if attr.startswith('asp-') or attr.startswith('@') or '@' in str(tag.attrs[attr]):tag.attrs.pop(attr,None)
        if tag.name=='iframe':tag['title']=tag.get('title','動的な参照画面')
        if tag.name=='style':
            tag.string=clean_css(tag.get_text())
    for node in list(soup.find_all(string=True)):
        if isinstance(node,Comment):node.extract();continue
        if node.parent and node.parent.name=='style':continue
        value=str(node)
        value=re.sub(r'@(?:if|else\s+if|foreach|for|while|switch)\s*\([^\n]*\)\s*\{?','',value)
        value=re.sub(r'@section\s+\w+\s*\{','',value)
        value=re.sub(r'@(?:Model|item|row|group)\.[\w.]+(?:\([^\n]*?\))?','',value)
        value=re.sub(r'^\s*(?:[{}]+|else)\s*$','',value,flags=re.M)
        if value != str(node):node.replace_with(NavigableString(value))
    for tag in list(soup.select('.status-message,.validation-summary')):
        if not tag.get_text(strip=True):tag['hidden']='hidden'
    # Conditional status placeholders can occur twice; retain one empty region.
    ids=set()
    for tag in list(soup.find_all(id=True)):
        if tag['id'] in ids:
            if not tag.get_text(strip=True):tag.decompose()
        else:ids.add(tag['id'])
    return str(soup)


def clean_css(css):
    css=re.sub(r'@import\b[^;]+;','',css,flags=re.I)
    css=re.sub(r'url\([^)]*\)','none',css,flags=re.I)
    return css.replace('</style','<\\/style')


def projection(source_path, texts, items):
    markup=texts[source_path]
    types={i.get('binding'):i.get('type') for i in items}
    body=sanitize_markup(markup,types)
    chosen=re.search(r'\bLayout\s*=\s*"([^"]+)"',markup)
    layout_name=(chosen[1] if chosen else '_Layout')+'.cshtml'
    layouts=[p for p in texts if p.endswith('/Shared/'+layout_name)]
    layout=layouts[0] if len(layouts)==1 else None
    if layout and '__CONTEXTBASE_BODY__' in sanitize_markup(texts[layout]):
        body=sanitize_markup(texts[layout]).replace('__CONTEXTBASE_BODY__',body)
    parts=source_path.split('/')
    marker=next((i for i,x in enumerate(parts) if x in {'Pages','JSP','Views','WebContent'}),None)
    project_prefix='/'.join(parts[:marker])+'/' if marker else ''
    css_paths=[p for p in texts if (p.startswith(project_prefix) and p.endswith('/site.css')) or p==source_path+'.css' or p==(layout or '')+'.css']
    css=BASE_CSS+'\n'+'\n'.join(clean_css(texts[p]) for p in css_paths)
    soup=BeautifulSoup(body,'html.parser')
    if not soup.html:
        body='<html lang="ja"><head></head><body>'+str(soup)+'</body></html>'
        soup=BeautifulSoup(body,'html.parser')
    if not soup.head:soup.html.insert(0,soup.new_tag('head'))
    meta=soup.new_tag('meta');meta['charset']='utf-8';soup.head.append(meta)
    csp=soup.new_tag('meta');csp['http-equiv']='Content-Security-Policy'
    csp['content']="default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src 'none'; form-action 'none'"
    soup.head.append(csp)
    style=soup.new_tag('style');style.string=css;soup.head.append(style)
    title=soup.new_tag('title');title.string='静的画面定義';soup.head.append(title)
    # Canonicalize generated HTML before hashing: Git stores text assets with LF.
    # This does not modify the input mapping or semantic source-code literals.
    document = str(soup).replace('\r\n', '\n').replace('\r', '\n')
    return document,[source_path,*([layout] if layout else []),*css_paths]


def build_screen(feature, texts, items, destination):
    from playwright.sync_api import sync_playwright
    markup,dependencies=projection(feature['path'],texts,items)
    dest=destination.resolve();dest.mkdir(parents=True,exist_ok=True)
    fid=feature['id'];html_path=safe(dest,fid+'-screen.html');write(html_path,markup)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=shutil.which('chromium') or None,args=['--no-sandbox'])
        try:
            page=browser.new_page(viewport={'width':1320,'height':960},device_scale_factor=1)
            page.route('**/*',lambda route:route.abort())
            page.set_content(markup,wait_until='load',timeout=15000)
            # Bounded static DOM only; browser script evaluates geometry, never input JS.
            width,height=page.evaluate('[document.documentElement.scrollWidth,document.documentElement.scrollHeight]')
            if width>2200 or height>16000:raise ValueError('Static layout exceeds bounded capture dimensions')
            data=page.screenshot(full_page=True,animations='disabled')
            bounds=page.locator('input:not([type=hidden]),select,textarea,button').evaluate_all(
                '(els)=>els.map(e=>({name:e.name||e.id||e.textContent.trim(),rect:{x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height}}))')
        finally:browser.close()
    image=Image.open(io.BytesIO(data));images=[]
    # Page-sized slices avoid one illegibly reduced very tall image in Excel/PDF.
    height_limit=780
    for i,y in enumerate(range(0,image.height,height_limit),1):
        piece=image.crop((0,y,image.width,min(image.height,y+height_limit)))
        # A viewport may extend below the document body. Do not publish blank slices.
        if all(a==b for a,b in piece.convert('RGB').getextrema()):continue
        name=f'{fid}-screen-{len(images)+1:02}.png';piece.save(safe(dest,name))
        images.append({'kind':'image','path':'assets/'+name,'alt':feature['name']+f' 静的画面 {i}'})
    return {'status':'static_projected','source_files':dependencies,'images':images,
            'html_asset':html_path.name,'width':image.width,'height':image.height,
            'controls':bounds,'runtime_verified':False,
            'limitation':'原本のHTML/CSSを静的合成。条件表示・動的データ・スクリプト操作は実行せず、共通CSSの不足部分は近似する。'}


def build_relation_diagram(feature, relations, destination):
    relations=[r for r in relations if r.get('store_id')]
    if not relations:return None
    def q(value):return '"'+str(value).replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')+'"'
    labels={r['store_id']:r['store']+('（メモリー）' if r['kind']=='memory' else '（DB）' if r['kind']=='database' else '（ORM実体）') for r in relations}
    events=sorted({r['event'] for r in relations})
    event_labels={r['event']:r.get('event_label',r['event']) for r in relations}
    lines=['digraph G {','rankdir=LR; graph [bgcolor=white]; node [fontname="Noto Sans CJK JP", fontsize=13, shape=box]; edge [fontname="Noto Sans CJK JP", fontsize=11];']
    for store,label in labels.items():lines.append(q(store)+' [shape=cylinder,label='+q(label)+'];')
    ops={'create':'C 追加','read':'R 参照','update':'U 更新','delete':'D 削除','upsert':'C/U 保存'}
    for i,event in enumerate(events):
        eid='e'+str(i);lines.append(q(eid)+' [label='+q(event_labels[event])+'];')
        for store in labels:
            actions=sorted({ops.get(r['operation'],r['operation']) for r in relations if r['event']==event and r['store_id']==store})
            if actions:lines.append(q(eid)+' -> '+q(store)+' [label='+q(' / '.join(actions))+'];')
    lines.append('}')
    path=safe(destination,feature['id']+'-data-relations.png')
    result=subprocess.run(['dot','-Tpng','-Gdpi=120','-o',str(path)],input='\n'.join(lines),encoding='utf-8',capture_output=True,timeout=30)
    if result.returncode:raise ValueError('Data relation diagram failed: '+result.stderr[:300])
    return {'kind':'image','path':'assets/'+path.name,'alt':feature['name']+' データ操作関連図（物理DBとメモリーを区別）'}
