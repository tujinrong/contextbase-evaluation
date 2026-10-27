"""Independent source-obligation audit against published Markdown.

Does not import the producer's SQL/markup/flow parsers or rendering functions.
Source discovery is independent of P1: deleting a P1 entry cannot hide a duty.
All failures are ERRORs; uncertainty is recorded separately, not counted as PASS.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from PIL import Image

JAPANESE=re.compile(r'[ぁ-ゖァ-ヺ一-鿿々〆ｦ-ﾟ]')
IDENT=r'(?:\[[^\]]+\]|"[^"\n]+"|`[^`\n]+`|[\w$#\u203F\u2040\uFF3F]+)'
QUAL=IDENT+r'(?:\s*\.\s*'+IDENT+r')*'
TOK=re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/')
OPS={'C':'挿入','U':'更新','D':'削除','R':'参照','M':'挿入・更新（MERGE）'}
SKIP={'.git','.svn','node_modules','vendor','bin','obj','lib','target','build','dist','__pycache__'}


def decode(raw):
    if raw.startswith((b'\xff\xfe',b'\xfe\xff')):return raw.decode('utf-16')
    for enc in ('utf-8-sig','cp932'):
        try:return raw.decode(enc)
        except UnicodeDecodeError:pass
    raise ValueError('source encoding is unsupported')


def name(value):
    return re.sub(r'\s*\.\s*','.',value.strip()).translate(str.maketrans('','','[]`"'))


def key(value):return name(value).casefold()


def japanese(value):
    if isinstance(value,dict):value=value.get('value')
    return isinstance(value,str) and bool(JAPANESE.search(value)) and not re.search(r'<%|未確認|名称未定|不明',value)


def read_json(path):return json.loads(path.read_text(encoding='utf-8'))


def sql_mask(text):
    return re.sub(r"'(?:''|[^'])*'|--[^\n]*|/\*[\s\S]*?\*/",lambda m:' '*len(m[0]),text)


def java_scopes(text):
    # Separate small lexical scanner: no import from producer flow/SQL parsers.
    masked=TOK.sub(lambda m:re.sub(r'[^\n]',' ',m[0]),text)
    result=[]
    pattern=r'\b(?:public|private|protected)\s+(?:(?:static|final|synchronized|abstract)\s+)*[\w<>\[\].?]+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w.,\s]+)?\{'
    for m in re.finditer(pattern,masked):
        i=m.end();depth=1
        while i<len(masked) and depth:
            if masked[i]=='{':depth+=1
            elif masked[i]=='}':depth-=1
            i+=1
        result.append((m.start(),i,m[1]+'@'+str(text.count('\n',0,m.start())+1)))
    return result


def scan_sources(input_root: Path):
    result={'screens':[],'tables':{},'writes':[],'db_present':False,'unresolved':[], 'source_files':0}
    write_keys=set()
    for p in sorted(input_root.rglob('*')):
        if not p.is_file() or p.is_symlink() or any(x in SKIP for x in p.relative_to(input_root).parts):continue
        if p.suffix.lower() not in {'.sql','.java','.cs','.py','.vb','.bas','.jsp','.cshtml','.aspx','.vue','.html','.frm','.xaml','.xml','.config'}:continue
        if p.stat().st_size>8_000_000:
            result['unresolved'].append({'path':str(p),'reason':'size_limit'});continue
        try:text=decode(p.read_bytes())
        except ValueError:
            result['unresolved'].append({'path':str(p),'reason':'encoding'});continue
        path=p.relative_to(input_root).as_posix();result['source_files']+=1
        ext=p.suffix.lower()
        if ext in {'.jsp','.cshtml','.aspx','.vue','.html','.frm','.xaml'} and not p.name.startswith('_'):
            masked=re.sub(r'<%[\s\S]*?%>|<!--([\s\S]*?)-->|@\*[\s\S]*?\*@','',text)
            if re.search(r'<(?:html|body|input|form|table|main|template|Window|Page)\b|Begin\s+(?:VB\.)?Form\b',masked,re.I):
                result['screens'].append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        if re.search(r'\b(?:PreparedStatement|DbContext|DbSet|SqlConnection)\b|jdbc[/.:]',text):result['db_present']=True
        fragments=[];constants={}
        scopes=java_scopes(text) if ext=='.java' else []
        if ext=='.sql':
            sql=sql_mask(text)
            for m in re.finditer(r'\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?('+QUAL+r')\s*\(',sql,re.I):
                table=name(m[1]);start=m.end();depth=1;i=start
                while i<len(sql) and depth:
                    if sql[i]=='(':depth+=1
                    elif sql[i]==')':depth-=1
                    i+=1
                body=text[start:i-1];columns=[]
                # DDL columns start each top-level comma segment; nested datatype commas stay inside.
                parts=[];last=0;nest=0;quote=None
                for j,ch in enumerate(body):
                    if quote:
                        if ch==quote:quote=None
                    elif ch in {'"','['}:quote=']' if ch=='[' else '"'
                    elif ch=='(':nest+=1
                    elif ch==')':nest-=1
                    elif ch==',' and nest==0:parts.append(body[last:j]);last=j+1
                parts.append(body[last:])
                for part in parts:
                    part=re.sub(r'--[^\n]*','',part).strip()
                    c=re.match('('+IDENT+r')\s+\w',part)
                    if c and name(c[1]).upper() not in {'PRIMARY','FOREIGN','CONSTRAINT','UNIQUE','CHECK','INDEX'}:columns.append(name(c[1]))
                entry=result['tables'].setdefault(key(table),{'name':table,'columns':set(),'evidence':[]})
                entry['columns'].update(columns);entry['evidence'].append({'path':path,'line':text.count('\n',0,m.start())+1})
            fragments=[(sql,0,'')]
        else:
            matches=list(TOK.finditer(text))
            code=TOK.sub(lambda m:' '*len(m[0]) if m[0].startswith(('//','/*')) else m[0],text)
            for m in re.finditer(r'\b(?:final\s+)?(?:String|string)\s+(\w+)\s*=\s*"((?:\\.|[^"\\])*)"\s*;',code):
                constants[m[1]]=m[2].replace('\\"','"')
            for m in matches:
                if not m[0].startswith('"'):continue
                fragments.append((m[0][1:-1].replace('\\"','"'),m.start(),code[m.end():m.end()+180]))
        for fragment,pos,tail in fragments:
            for op,pattern in [('C',r'INSERT\s+INTO'),('U',r'UPDATE'),('D',r'DELETE\s+FROM'),('R',r'FROM|JOIN'),('M',r'MERGE\s+INTO')]:
                for hit in re.finditer(r'\b(?:'+pattern+r')\s+(?:('+QUAL+'))?',fragment,re.I):
                    if op=='R' and re.search(r'\b(?:TRIM|EXTRACT|SUBSTRING)\s*\([^)]*$',fragment[:hit.start()],re.I):continue
                    physical=hit[1]
                    if op=='U' and re.search(r'\b(?:ON|FOR)\s*$',fragment[:hit.start()],re.I):continue
                    if not physical:
                        symbol=re.match(r'\s*(?:\+\s*|\)\s*\.append\(\s*)(\w+)',tail)
                        if symbol:physical=constants.get(symbol[1])
                    if not physical:
                        if op in {'C','U','D','M'}:result['unresolved'].append({'path':path,'line':text.count('\n',0,pos)+1,'reason':'dynamic_sql_target','operation':op})
                        continue
                    physical=name(physical)
                    if physical.upper() in {'SET','SELECT','UPDATE','DELETE','INSERT','VALUES','IF','NULL','SYSTEM','USER','EXCLUDED'}:continue
                    # Non-SQL prose with a FROM/UPDATE word is not an executable reference.
                    if op=='R' and not re.search(r'\b(?:SELECT|FROM|JOIN)\b',fragment,re.I):continue
                    result['db_present']=True
                    t=result['tables'].setdefault(key(physical),{'name':physical,'columns':set(),'evidence':[]})
                    t['evidence'].append({'path':path,'line':text.count('\n',0,pos)+1})
                    if op in {'C','U','D','M'}:
                        scope=next((owner for start,end,owner in scopes if start<=pos<end),'')
                        k=(path,key(physical),op,scope)
                        if k not in write_keys:
                            result['writes'].append({'path':path,'table':physical,'operation':op,'line':text.count('\n',0,pos)+1,'scope':scope});write_keys.add(k)
    for t in result['tables'].values():t['columns']=sorted(t['columns'])
    return result


def consolidated_table_entries(entries):
    """Scope every table obligation to its own published h2 definition section.

    IDs/metadata identify the intended section but never substitute for its
    actual text. A name in the overall index or another table cannot pass.
    """
    result={key(e[0]['db_table']):e for e in entries if e[0].get('db_table')}
    for d,path,raw,soup,records in entries:
        for ref in d.get('db_tables',[]):
            heading=next((h for h in soup.find_all('h2') if h.get_text(' ',strip=True)==ref['section']),None)
            if heading is None:continue
            nodes=[str(heading)]
            for node in heading.next_siblings:
                if getattr(node,'name',None)=='h2':break
                nodes.append(str(node))
            section=BeautifulSoup(''.join(nodes),'html.parser')
            physical=[]
            for row in section.find_all('tr'):
                cells=row.find_all(['th','td'],recursive=False)
                if len(cells)==2 and cells[0].get_text(' ',strip=True)=='物理名':physical.append(cells[1].get_text(' ',strip=True))
            if physical!=[ref['table']]:continue
            result[key(ref['table'])]=(d,path,section.get_text(' ',strip=True),section,records)
    return result


def item_rows(soup):
    result={}
    for t in soup.find_all('table'):
        rows=t.find_all('tr')
        if not rows:continue
        headers=[c.get_text(' ',strip=True) for c in rows[0].find_all(['td','th'],recursive=False)]
        if not {'No','項目名','DB連携項目'}<=set(headers):continue
        for row in rows[1:]:
            values=[c.get_text(' ',strip=True) for c in row.find_all(['td','th'],recursive=False)]
            if len(values)==len(headers):
                record=dict(zip(headers,values));result[record['No']]=record
    return result


def valid_document_image(path, image, mdroot):
    uri=urlsplit(image.get('src',''))
    if uri.scheme or uri.netloc:return False
    asset=path.parent/unquote(uri.path)
    if asset.is_symlink() or not asset.resolve().is_relative_to(mdroot.resolve()):return False
    try:
        with Image.open(asset) as im:
            ok=im.width>=100 and im.height>=40 and any(a!=b for a,b in im.convert('RGB').getextrema())
        with Image.open(asset) as im:im.verify()
        return ok
    except (OSError,ValueError):return False


def inspect(root: Path, *, input_dir=None):
    root=root.resolve()
    if input_dir is None:
        manifest=root/'ContextBase/01-foundation/manifest.json'
        input_dir=read_json(manifest).get('input','input') if manifest.exists() else 'input'
    input_root=root/input_dir
    if not input_root.is_dir():raise ValueError('Independent quality audit requires existing input')
    if input_root.is_symlink() or not input_root.resolve().is_relative_to(root):raise ValueError('Unsafe input')
    expected=scan_sources(input_root);p1=root/'ContextBase/01-foundation';p2=root/'ContextBase/02-detailed'
    features=read_json(p1/'catalogs/features.json');db=read_json(p1/'database/catalog.json')
    catalog=read_json(p2/'resolved/catalog.json');models={f['id']:read_json(p2/f'functions/{f["id"]}/feature.json') for f in catalog['features']}
    entries=[];checks=[]
    def check(code, subject, ok, detail='', evidence=None):
        checks.append({'code':code,'subject':subject,'pass':bool(ok),'severity':'ERROR' if not ok else 'PASS','detail':detail,'evidence':evidence or []})
    for d in catalog['documents']:
        path=root/'output/md'/d['path']
        if not path.resolve().is_relative_to((root/'output/md').resolve()) or path.is_symlink():raise ValueError('Unsafe document path')
        text=path.read_text(encoding='utf-8') if path.is_file() else ''
        soup=BeautifulSoup(MarkdownIt('commonmark',{'html':True}).enable('table').render(text),'html.parser')
        records=[]
        for table in soup.find_all('table'):
            pairs_={}
            for row in table.find_all('tr'):
                cells=row.find_all(['td','th'],recursive=False)
                if len(cells)==2:pairs_[cells[0].get_text(' ',strip=True)]=cells[1].get_text(' ',strip=True)
            if '対象テーブル' in pairs_ and '操作' in pairs_:records.append(pairs_)
        # Published logical-name cells must be checked as well as intermediate JSON.
        for table in soup.find_all('table'):
            rows=table.find_all('tr')
            if not rows:continue
            headers=[c.get_text(' ',strip=True) for c in rows[0].find_all(['td','th'],recursive=False)]
            indexes=[i for i,h in enumerate(headers) if h in {'論理名','項目名','機能名','画面名','テーブル論理名','列論理名'}]
            for no,row in enumerate(rows[1:],2):
                cells=row.find_all(['td','th'],recursive=False)
                for i in indexes:
                    value=cells[i].get_text(' ',strip=True) if i<len(cells) else ''
                    check('NAME-005',d['path']+':'+str(no)+':'+headers[i],japanese(value),'公開MDの論理名セルも日本語が必須')
                if len(cells)==2 and cells[0].get_text(' ',strip=True) in {'論理名','画面名','機能名'}:
                    check('NAME-005',d['path']+':'+str(no),japanese(cells[1].get_text(' ',strip=True)),'公開MDの論理名も照合する')
        entries.append((d,path,text,soup,records))
    for screen in expected['screens']:
        matches=[f for f in features if f['path']==screen['path'] and f['kind']=='screen']
        check('UI-001',screen['path'],bool(matches),'原本の画面に対応する機能が必要',[screen])
        for f in matches:
            docs=[e for e in entries if e[0].get('feature_id')==f['id'] and e[0]['path'].startswith('基本設計書/')]
            check('UI-002',f['id'],bool(docs),'基本設計書が必要',[screen])
            for d,path,text,soup,_ in docs:
                model=models[f['id']];expected_images=model.get('layout',{}).get('images',[])
                if model.get('reviewed'):expected_images=[b for section in d['model']['sections'] for b in section['blocks'] if b['kind']=='image']
                published=soup.find_all('img');has_layout=bool(expected_images) and any('レイアウト' in h.get_text() or '画面' in h.get_text() for h in soup.find_all(['h2','h3','h4']))
                check('UI-003',f['id'],has_layout and bool(published),'画面レイアウト見出しと実際の掲載画像が必要',[screen])
                for image in expected_images:
                    candidates=[im for im in published if unquote(urlsplit(im.get('src','')).path).endswith(image['path'].split('/')[-1])]
                    check('UI-004',f['id']+'/'+image['path'],bool(candidates),'ContextBaseの画像宣言だけでなくMD本文へ掲載する')
                    for im in candidates:
                        src=unquote(urlsplit(im['src']).path);asset=(path.parent/src).resolve();ok=False
                        if asset.is_relative_to((root/'output/md').resolve()) and asset.is_file() and not asset.is_symlink():
                            try:
                                with Image.open(asset) as pic:
                                    ok=pic.width>=100 and pic.height>=40
                                    extrema=pic.convert('RGB').getextrema()
                                    ok=ok and any(a!=b for a,b in extrema)
                                with Image.open(asset) as pic:pic.verify()
                            except Exception:pass
                        check('UI-005',f['id']+'/'+src,ok,'画像欠落・破損・微小画像・単色画像・領域外参照を禁止')
    table_docs=consolidated_table_entries(entries)
    books=[e for e in entries if 'db_tables' in e[0]]
    if books:
        actual=list((root/'output/md').rglob('テーブル定義書*.md'))
        check('DB-004','統合テーブル定義書',len(books)==1 and len(actual)==1,'全テーブル定義を1個のMDへ統合し、旧個別文書を残さない')
    generic_db=[e for e in entries if re.search('(?:テーブル定義書|DB仕様書)',e[0]['path']) and len(e[2])>100]
    check('DB-001','DB仕様書',not expected['db_present'] or bool(generic_db or table_docs),'原本にDB使用根拠がある場合、DB仕様書は必須')
    for k,t in expected['tables'].items():
        doc=table_docs.get(k)
        check('DB-002',t['name'],bool(doc) and len(doc[2])>100,'原本の各テーブルに対応する定義節が必要（統合文書内の各節を別々に検査する）',t['evidence'][:3])
        if doc:
            defined=set()
            for table in doc[3].find_all('table'):
                rows=table.find_all('tr')
                if not rows:continue
                headers=[c.get_text(' ',strip=True) for c in rows[0].find_all(['td','th'],recursive=False)]
                if '物理名' not in headers:continue
                ix=headers.index('物理名')
                for row in rows[1:]:
                    cells=row.find_all(['td','th'],recursive=False)
                    if ix<len(cells):defined.add(cells[ix].get_text(' ',strip=True))
            for column in t['columns']:check('DB-003',t['name']+'.'+column,column in defined,'原本DDLの列が仕様書から欠落している')
    for f in models.values():
        check('NAME-001',f['id'],japanese(f['name']),'機能の論理名は日本語で記載する')
        for item in f['items']:check('NAME-002',f['id']+'/'+item['id'],japanese(item['name']),'画面項目の論理名は日本語で記載する')
    for t in db['tables']:
        check('NAME-003',t['name'],japanese(t.get('logical_name')),'テーブル論理名に物理名だけを流用しない')
        for c in t['columns']:check('NAME-004',t['name']+'.'+c['name'],japanese(c.get('logical_name')),'列論理名は日本語で記載する')
    for op in expected['writes']:
        matches=[]
        for d,path,text,soup,records in entries:
            for rec in records:
                if key(rec['対象テーブル'])==key(op['table']) and rec['操作']==OPS[op['operation']] and op['path'] in rec.get('原本','') and (not op.get('scope') or op['scope'] in rec.get('原本','')):matches.append(rec)
        subject=op['path']+':'+op.get('scope','')+':'+op['operation']+':'+op['table']
        check('DML-001',subject,bool(matches),'原本の各挿入・更新・削除について対象付きDB説明が必要',[op])
        if matches:
            for field in ['処理説明','対象条件','確定・取消']+(['設定項目'] if op['operation'] in {'C','U','M'} else []):
                check('DML-002',subject+'/'+field,any(len(m.get(field,''))>=8 and japanese(m.get(field,'')) for m in matches),'対象名やCRUD記号だけで説明済みとは扱わない')
    # Also check per-function projection: a global DB book cannot replace its own event explanation.
    for f in models.values():
        own=[e for e in entries if e[0].get('feature_id')==f['id'] and not e[0]['path'].startswith('詳細仕様書/')]
        for q in f.get('sql_operations',[]):
            if q['operation'] not in {'C','U','D','M'}:continue
            found=[rec for e in own for rec in e[4] if q['id']==rec.get('操作ID')]
            check('DML-003',f['id']+'/'+q['id'],bool(found),'機能別仕様書にもDB操作説明が必要')
    # Publication checks added for the resolved binding / event contract.
    # No producer parser is imported. Raw evidence and separately scanned DDL
    # are checked in addition to stored values and the actual Markdown cells.
    for f in models.values():
        own=[e for e in entries if e[0].get('feature_id')==f['id'] and e[0]['path'].startswith('基本設計書/')]
        if not own:continue
        d,path,raw,soup,_=own[0]
        rows=item_rows(soup)
        for item in f.get('items',[]):
            links=item.get('db_bindings',[])
            if not links:continue
            record=rows.get(str(item.get('number')), {})
            norm=lambda text:''.join(str(text).split())
            check('BIND-001',f['id']+'/'+item['id'],norm(record.get('DB連携項目',''))==norm(item.get('db','')),'Model名ではなく、追跡済みDB項目を公開欄へ表示する')
            for link in links:
                target=link.get('table','');column=link.get('column','')
                known=expected['tables'].get(key(target))
                if known and known['columns']:
                    check('BIND-002',f['id']+'/'+item['id']+'/'+target+'.'+column,column in known['columns'],'追跡先DB列を独立に読取ったDDLと照合する')
                evidence=link.get('evidence',[])
                valid=bool(evidence)
                for ev in evidence:
                    file=input_root/ev.get('path','')
                    line=ev.get('line')
                    if file.is_symlink() or not file.resolve().is_relative_to(input_root.resolve()) or not file.is_file():valid=False;continue
                    try:valid=valid and isinstance(line,int) and 1<=line<=len(decode(file.read_bytes()).splitlines())
                    except ValueError:valid=False
                check('BIND-003',f['id']+'/'+item['id']+'/'+target+'.'+column,valid,'DB連携の処理経路には有効な原本位置が必要')
            if item.get('binding_remarks'):
                check('BIND-004',f['id']+'/'+item['id'],norm(item['binding_remarks']) in norm(soup.get_text(' ',strip=True)),'複雑なバインド経路・加工内容の備考を欠落させない')
        if f.get('kind')!='screen' or f.get('reviewed'):continue
        for event in f.get('events',[]):
            # Legacy/imported fixtures may not use the enriched event contract.
            if 'narrative' not in event:continue
            title=next((h for h in soup.find_all('h3') if h.get_text(' ',strip=True)==event['name']),None)
            nodes=[]
            if title:
                for node in title.next_siblings:
                    if getattr(node,'name',None) in {'h2','h3'}:break
                    nodes.append(str(node))
            section=BeautifulSoup(''.join(nodes),'html.parser')
            headers={h.get_text(' ',strip=True) for h in section.find_all('h4')}
            check('EVENT-001',f['id']+'/'+event['id'],{'処理概要','処理手順'}<=headers and bool(event['narrative'].get('steps')),'イベントごとに処理概要と順序を持つ説明が必要')
            for field,rule in [('flow_images','EVENT-002'),('er_images','EVENT-003')]:
                required=field=='flow_images' or bool(event.get('sql_operations'))
                if not required:continue
                images=event.get(field,[])
                ok=bool(images)
                for im in images:
                    matches=[x for x in section.find_all('img') if unquote(urlsplit(x.get('src','')).path).endswith(im['path'].split('/')[-1])]
                    ok=ok and bool(matches) and all(valid_document_image(path,x,root/'output/md') for x in matches)
                check(rule,f['id']+'/'+event['id'],ok,'各イベントの本文に対応するフロー／SQLのER画像を掲載する。他イベントの画像では代替不可')
    errors=[c for c in checks if not c['pass']]
    report={'status':'fail' if errors else 'pass','errors':len(errors),'checks_count':len(checks),'checks':checks,
            'source_obligations':expected,'independent_source_scan':True,
            'scope':'原本を別走査し、公開MDの画像・各表定義・日本語論理名・操作説明を照合。全実行経路の意味同等性ではない。'}
    dest=root/'report/quality';dest.mkdir(parents=True,exist_ok=True)
    (dest/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    rows=['# 独立品質評価','',f'判定：{report["status"]}。エラー：{len(errors)}件。検査：{len(checks)}件。','', '| 規則 | 対象 | エラー内容 |','|---|---|---|']
    for c in errors:rows.append('| '+ ' | '.join(str(c[k]).replace('|','&#124;').replace('\n',' ') for k in ['code','subject','detail'])+' |')
    rows+=['','## 解析限界','',f'動的SQL・サイズ・文字コード等の別確認：{len(expected["unresolved"])}件。未解決は存在しない意味ではない。']
    (dest/'独立評価.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    return report


def enforce(root: Path):
    result=inspect(root)
    if result['errors']:raise ValueError(f'Independent quality gate failed: {result["errors"]} errors; report/quality/validation.json')
    return {'status':result['status'],'errors':0,'checks_count':result['checks_count'],'independent_source_scan':True}
