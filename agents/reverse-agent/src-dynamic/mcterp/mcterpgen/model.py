"""Cross-file model: UI -> request service -> methods -> database/procedures."""
from __future__ import annotations
from collections import Counter,defaultdict,deque
from pathlib import Path
import json,re
from specgen.common import split_top
from .scan import read,sha,functions,vue,masked,pairs,archive_schema,workbook_structure

CODE={'.cs','.vue','.ts','.tsx','.js','.sql'}
EXCLUDE={'.git','node_modules','bin','obj','dist','build','__pycache__'}


def normalize(s):return ' '.join(str(s).replace('///','').split())


def schema(entries,origin):
    tables={};routines={}
    text='\n'.join(e['sql'] for e in entries)
    for m in re.finditer(r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?(?:public\.)?"?(\w+)"?\s*\(([\s\S]*?)\n\);',text,re.I):
        cols=[]
        for part in split_top(m[2]):
            c=re.match(r'\s*"?(\w+)"?\s+(.+)',part,re.S)
            if not c or c[1].upper() in {'CONSTRAINT','PRIMARY','FOREIGN','UNIQUE','CHECK'}:continue
            definition=normalize(c[2]);typ=re.split(r'\s+(?:NOT NULL|DEFAULT|CONSTRAINT|GENERATED|NULL)\b',definition,flags=re.I)[0]
            default=re.search(r'\bDEFAULT\s+(.+?)(?:\s+NOT NULL|$)',definition,re.I)
            cols.append({'physical':c[1],'logical':c[1],'type':typ,'nullable':not bool(re.search(r'\bNOT NULL\b',definition,re.I)),'default':default[1] if default else '未指定','key':'','definition':definition})
        tables[m[1]]={'physical':m[1],'logical':m[1],'columns':cols,'origin':origin,'status':'保存時点のDDL','constraints':[],'indexes':[],'dto':[]}
    for m in re.finditer(r"COMMENT ON TABLE\s+(?:public\.)?(\w+)\s+IS\s+'((?:''|[^'])*)';",text,re.I):
        if m[1] in tables:tables[m[1]]['logical']=normalize(m[2].replace("''","'"))
    for m in re.finditer(r"COMMENT ON COLUMN\s+(?:public\.)?(\w+)\.(\w+)\s+IS\s+'((?:''|[^'])*)';",text,re.I):
        for c in tables.get(m[1],{}).get('columns',[]):
            if c['physical']==m[2]:c['logical']=normalize(m[3].replace("''","'"))
    for m in re.finditer(r'ALTER TABLE(?: ONLY)?\s+(?:public\.)?(\w+)\s+ADD CONSTRAINT\s+([^;]+);',text,re.I):
        if m[1] not in tables:continue
        tables[m[1]]['constraints'].append(normalize(m[2]));pk=re.search(r'PRIMARY KEY\s*\(([^)]+)\)',m[2],re.I)
        if pk:
            for c in tables[m[1]]['columns']:
                if c['physical'] in [s.strip(' "') for s in pk[1].split(',')]:c['key']='PK'
    for m in re.finditer(r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+\w+\s+ON\s+(?:public\.)?(\w+)\s+([^;]+);',text,re.I):
        if m[1] in tables:tables[m[1]]['indexes'].append(normalize(m[0]))
    return tables


def walk(graph,start):
    seen={start};q=deque([start])
    while q:
        for c in graph.get(q.popleft(),[]):
            if c not in seen:seen.add(c);q.append(c)
    return sorted(seen)


def collect(root:Path,input_dir:str,cold:bool=False):
    source=root/input_dir; inventory=[]; texts={};records={}; errors=[];cache=root/'.specgen-state/mcterp/files';cache.mkdir(parents=True,exist_ok=True)
    parsed=hits=0;bookmeta=[];archives=[]
    version=sha(''.join(p.read_text() for p in sorted(Path(__file__).parent.glob('*.py'))))
    for p in sorted(source.rglob('*')):
        if not p.is_file() or p.is_symlink():continue
        rel=p.relative_to(root).as_posix();raw=p.read_bytes();ext=p.suffix.lower();h=sha(raw);row={'path':rel,'bytes':len(raw),'sha256':h,'status':'inventory_only','reason':'非コード資源・定義以外の内容は未解析'}
        inventory.append(row)
        if any(x in EXCLUDE for x in p.relative_to(source).parts):row.update(status='excluded',reason='依存・ビルド成果物');continue
        if ext in {'.key','.crt','.pfx','.pem','.licx','.ttf','.otf','.tte','.woff','.woff2','.eot'}:row.update(status='restricted_metadata',reason='鍵・ライセンス・フォントは内容を出力しない');continue
        if ext=='.dump':
            try:entries=archive_schema(raw);archives.append((rel,entries));row.update(status='schema_archive',reason='DDL文字列のみ。データ行は展開・出力しない',ddl_strings=len(entries))
            except ValueError as exc:row.update(status='requires_export',reason=str(exc))
            continue
        if ext in {'.xlsx','.xlsm'}:
            try:
                sheets=workbook_structure(p);bookmeta.append({'path':rel,'sheets':[{'name':s['name'],'nonempty_rows':len(s['rows'])} for s in sheets],'macro_executed':False})
                row.update(status='workbook_structure',reason='シート構造のみ。数式・マクロ・帳票印字位置・実データは未解析')
            except Exception as exc:row.update(status='requires_export',reason=type(exc).__name__)
            continue
        if ext not in CODE|{'.json','.csproj','.sln','.yml','.yaml','.config','.md','.txt','.cshtml','.html'}:continue
        if ('/public/' in rel and ext in {'.js','.json','.html','.css'}) or len(raw)>8_000_000:
            row.update(status='excluded',reason='同梱外部ライブラリまたは大容量資源。業務関数として数えない');continue
        try:text=read(p)
        except ValueError:row.update(status='requires_export',reason='対応文字コード外');continue
        texts[rel]=text
        if ext not in CODE:row.update(status='configuration_read',reason='構成テキスト読取・一部の関連付けに利用。値の網羅的仕様化は未実施');continue
        file=cache/(sha(rel)+'.json');key=sha(version+h+rel)
        try:prior=json.loads(file.read_text()) if file.exists() and not cold else None
        except (ValueError,OSError):prior=None
        if isinstance(prior,dict) and prior.get('key')==key and isinstance(prior.get('data'),dict) and prior.get('integrity')==sha(json.dumps(prior['data'],ensure_ascii=False,sort_keys=True)):
            record=prior['data'];hits+=1
        else:
            try:
                record=vue(text,rel) if ext=='.vue' else {'methods':functions(text,rel,'cs' if ext=='.cs' else 'ts'),'items':[],'events':[]} if ext!='.sql' else {'methods':[],'items':[],'events':[]}
                parsed+=1
            except Exception as exc:errors.append({'path':rel,'error':type(exc).__name__});record={'methods':[],'items':[],'events':[]}
            file.write_text(json.dumps({'key':key,'integrity':sha(json.dumps(record,ensure_ascii=False,sort_keys=True)),'data':record},ensure_ascii=False),encoding='utf-8')
        records[rel]=record;row.update(methods=len(record['methods']),items=len(record['items']),event_bindings=len(record['events']),status='parsed',reason='静的構造・宣言・呼出・項目の抽出。実行意味の完全解析ではない')
    # Read schema snapshots separately. Do not merge historical snapshots into a fictitious live DB.
    schemas=[{'path':p,'tables':schema(entries,p),'ddl_strings':len(entries)} for p,entries in sorted(archives)]
    latest=schemas[-1] if schemas else None
    tables=latest['tables'] if latest else {}
    for p,t in texts.items():
        if p.endswith('.sql') and 'CREATE TABLE' in t.upper():
            for name,table in schema([{'sql':t}],p).items():
                if name not in tables:tables[name]=table
    methods={m['id']:m for r in records.values() for m in r['methods']}
    for p,t in texts.items():
        if p.endswith('Dto.cs') and '/Generated/' in p:
            tm=re.search(r'TABLE_NAME\s*=\s*"(\w+)"',t)
            if not tm:continue
            name=tm[1]
            if name not in tables:tables[name]={'physical':name,'logical':name,'columns':[],'origin':p,'status':'DTO宣言のみ・物理DDL未取得','constraints':[],'indexes':[],'dto':[]}
            table=tables[name];table['dto'].append(p)
            for m in re.finditer(r'public\s+([\w?<>\[\]]+)\s+(\w+)\s*\{\s*get;\s*set;\s*\}\s*(?://([^\n]*))?',t):
                found=next((c for c in table['columns'] if c['physical']==m[2]),None)
                if found:
                    found['dto_type']=m[1]
                    if found['logical']==found['physical'] and m[3]:found['logical']=normalize(m[3])
                else:table['columns'].append({'physical':m[2],'logical':normalize(m[3] or m[2]),'type':'物理型未確認','dto_type':m[1],'nullable':None,'default':'未確認','key':'','definition':'DTOで使用・DDLに未検出'})
    # Routine dependencies from SQL definitions (not test/seed data).
    routines={}
    for path,text in texts.items():
        if not path.endswith('.sql') or not re.search(r'CREATE (?:OR REPLACE )?(?:FUNCTION|PROCEDURE)',text,re.I):continue
        for m in re.finditer(r'CREATE (?:OR REPLACE )?(FUNCTION|PROCEDURE)\s+(?:public\.)?"?(\w+)"?',text,re.I):
            refs=[]
            for t in re.finditer(r'\b(DELETE\s+FROM|INSERT\s+INTO|TRUNCATE(?:\s+TABLE)?|FROM|JOIN|UPDATE)\s+(?:public\.)?"?(\w+)"?',text,re.I):
                if t[2] in tables:refs.append({'table':t[2],'op':'D' if t[1].upper().startswith(('DELETE','TRUNCATE')) else 'C' if t[1].upper().startswith('INSERT') else 'U' if t[1].upper()=='UPDATE' else 'R'})
            routines[m[2]]={'name':m[2],'path':path,'line':text.count('\n',0,m.start())+1,'kind':m[1],'references':list({(x['table'],x['op']):x for x in refs}.values()),'text':text,'calls':[]}
    for r in routines.values():r['calls']=[name for name in routines if name!=r['name'] and re.search(r'\b'+re.escape(name)+r'\s*\(',r['text'])]
    for r in routines.values():
        closure=walk({k:v['calls'] for k,v in routines.items()},r['name']);r['recursive_tables']=sorted({x['table'] for k in closure for x in routines[k]['references']});r['recursive_refs']=list({(x['table'],x['op']):x for k in closure for x in routines[k]['references']}.values())
    byclass=defaultdict(list);byscope=defaultdict(list)
    for m in methods.values():byclass[(m['class'],m['name'])].append(m['id']);byscope[(m['namespace'],m['class'],m['name'])].append(m['id'])
    graph={};unresolved=[]
    for mid,m in methods.items():
        direct=[];body=m['body'];m['db']=[];m['routines']=[];m['mappings']=[]
        if m['path'].endswith('.cs'):
            for dbref in re.finditer(r'\b(?:db|_db|context)\.(\w+)\s*\.\s*(\w+)',masked(body)):
                tab,op=dbref[1],dbref[2]
                if tab not in tables:continue
                operation={'SELECT':'R','GROUP':'R','GetDtoByKey':'R','GetDto':'R','INSERT':'C','UPDATE':'U','UpdateDto':'U','DELETE':'D','DeleteByKey':'D'}.get(op,'?')
                m['db'].append({'table':tab,'op':operation,'line':m['line']+body[:dbref.start()].count('\n'),'via':'DAO:'+op})
            # SQL constants are scoped to the current file, never global PROC_NAME substitution.
            filetext=texts[m['path']];constants={k:v for k,v in re.findall(r'(?:const|readonly)\s+string\s+(\w+)\s*=\s*"([^"]+)"',filetext)}
            for name,r in routines.items():
                if re.search(r'"'+re.escape(name)+r'"',body) or any(v==name and re.search(r'\b'+re.escape(k)+r'\b',masked(body)) for k,v in constants.items()):m['routines'].append(name)
            for mp in re.finditer(r'(?P<lhs>\w+(?:\.\w+)*)\s*=\s*(?P<rhs>[^;\n]+)',body):
                refs=re.findall(r'\b(\w+)Dto\.(\w+)\b',mp['rhs'])
                for tab,col in refs:
                    if tab in tables:m['mappings'].append({'field':mp['lhs'].split('.')[-1],'table':tab,'column':col,'expression':normalize(mp['rhs'])})
        for call in m['calls']:
            bits=call.split('.');name=bits[-1];cls=bits[-2] if len(bits)>1 else m['class']
            candidates=byscope.get((m['namespace'],cls,name),[])
            if not candidates and len(bits)>1:candidates=byclass.get((cls,name),[])
            if len(candidates)==1 and candidates[0]!=mid:direct.append(candidates[0])
        graph[mid]=list(dict.fromkeys(direct))
    # A service corresponds to a business boundary, not every helper source file.
    services={}
    for m in methods.values():
        if m['class']=='Service' and '.Service.' in m['namespace'] and '/BusinessService/' in m['path']:
            name=m['namespace'].split('.Service.',1)[1]
            group=services.setdefault(name,{'key':name,'name':re.sub(r'^\d+[.．]','',Path(m['path']).parent.parent.name),'path':str(Path(m['path']).parent.parent).replace('\\','/'),'methods':[],'screens':[]})
            group['methods'].append(m['id'])
    # Vue imports -> TypeScript dispatch declarations.
    apis={}
    for p,text in texts.items():
        if not p.endswith(('.ts','.vue')):continue
        service=re.search(r'\b(?:servicename|serviceName|SERVICE_NAME)\s*=\s*[\'\"]([^\'\"]+)',text)
        entries=[]
        for m in records.get(p,{}).get('methods',[]):
            mt=re.search(r'\b(?:methodname|methodName)\s*=\s*[\'\"]([^\'\"]+)',m['body'])
            if not mt:mt=re.search(r'\b(?:api|download|upload|preview)\s*\(\s*(?:servicename|serviceName|SERVICE_NAME)\s*,\s*[\'\"]([^\'\"]+)',m['body'])
            if service and mt:entries.append({'export':m['name'],'service':service[1],'method':mt[1],'line':m['line'],'path':p,'kind':'upload' if re.search(r'\bupload\(',m['body']) else 'download' if re.search(r'\bdownload\(',m['body']) else 'preview' if re.search(r'\bpreview\(',m['body']) else 'api'})
        if entries:apis[p]=entries
    screens=[]
    for p,rec in records.items():
        if not p.endswith('.vue') or '/src/views/' not in p:continue
        text=texts[p];bindings=[];imports=[]
        for im in re.finditer(r'import\s+([\s\S]*?)\s+from\s+[\'\"]([^\'\"]+)[\'\"]',text):
            spec=im[2]
            if spec.startswith('@/'):
                base=Path(p.split('/src/',1)[0])/'src'/spec[2:]
            elif spec.startswith('.'):base=Path(p).parent/spec
            else:continue
            candidates=[str(base).replace('\\','/'),str(base)+'.ts',str(base)+'.vue',str(base/'index.ts')]
            import os
            resolved=next((os.path.normpath(x).replace('\\','/') for x in candidates if os.path.normpath(x).replace('\\','/') in records),None)
            if resolved:
                imports.append(resolved)
                for a in apis.get(resolved,[]):
                    if re.search(r'\b'+re.escape(a['export'])+r'\b',im[1]):bindings.append(a)
        # Common modules are linked from the nearest service module if they have no direct import.
        services_found=list(dict.fromkeys(a['service'] for a in bindings))
        if not services_found:
            parent=Path(p).parent
            for _ in range(4):
                key=str(parent/'service.ts')
                if key in apis:services_found=list(dict.fromkeys(a['service'] for a in apis[key]));break
                parent=parent.parent
        # The owning service follows the nearest feature directory; shared API imports do not split it.
        main=next((part for part in reversed(Path(p).parts) if part in services),None)
        if not main:
            parent=Path(p).parent
            while '/src/views' in str(parent):
                key=str(parent/'service.ts')
                own=list(dict.fromkeys(a['service'] for a in apis.get(key,[])))
                if len(own)==1:main=own[0];break
                parent=parent.parent
        main=main or (services_found[0] if len(services_found)==1 else None)
        mobile='/mcterp-mobile-app/' in p
        # Distinguish mobile interface when it uses same backend business service.
        featurekey=('Mobile.'+main if mobile and main else main) or ('Mobile.' if mobile else 'Web.')+re.sub(r'[^\w.-]','_',p.split('/src/views/',1)[1].rsplit('.',1)[0])
        group=services.setdefault(featurekey,{'key':featurekey,'name':('モバイル ' if mobile else '')+(services.get(main,{}).get('name') or Path(p).parent.name),'path':str(Path(p).parent),'methods':services.get(main,{}).get('methods',[]) if mobile else [],'screens':[]})
        entry={'path':p,**rec,'apis':bindings,'imports':imports,'backend_services':services_found,'title':next(iter(re.findall(r'(?:label|title)="([^"{}:]+)"',text)),'')}
        group['screens'].append(entry);screens.append(entry)
    owner={s['path']:g['key'] for g in services.values() for s in g['screens']}
    for key,g in list(services.items()):
        if not key.startswith(('Web.','Mobile.')) or g['methods']:continue
        for screen in list(g['screens']):
            path=screen['path'];parts=Path(path).parts
            if 'components' not in parts and 'modules' not in parts:continue
            parents=[(p,owner[p]) for p in owner if owner[p]!=key and path.startswith(str(Path(p).parent)+'/') and '/components/' not in p and '/modules/' not in p]
            if not parents:continue
            best=max(parents,key=lambda x:len(str(Path(x[0]).parent)))
            services[best[1]]['screens'].append(screen);g['screens'].remove(screen);owner[path]=best[1]
        if not g['screens'] and not g['methods']:del services[key]
    # Give screen-only and common-component groups names from their actual path/title, not a generic 'modules'.
    for key,g in services.items():
        if key.startswith(('Web.','Mobile.')) and g['screens']:
            s0=g['screens'][0];stem=Path(s0['path']).stem
            if stem=='index':stem=Path(s0['path']).parent.name
            g['name']=('モバイル ' if key.startswith('Mobile.') else '')+stem
        g['name']=re.sub(r'^\d+[._．]','',g['name'])
    for name,g in services.items():
        g['id']='MCT-'+re.sub(r'[^\w-]','-',name);g['kind']='画面・API' if g['screens'] else 'バッチ' if '/BatchBusinessService/' in g['path'] else 'API・業務処理'
        allmethods=set()
        for mid in g['methods']:allmethods.update(walk(graph,mid))
        g['reachable_methods']=sorted(allmethods);g['db']=[];g['routines']=sorted({r for mid in sorted(allmethods) for r in methods[mid]['routines']})
        for mid in sorted(allmethods):g['db']+=methods[mid]['db']
        for r in g['routines']:
            for ref in routines[r]['recursive_refs']:g['db'].append({'table':ref['table'],'op':ref['op'],'via':'SQL関数:'+r,'line':routines[r]['line']})
        g['db']=list({(x['table'],x['op'],x['via']):x for x in g['db']}.values())
        g['files']=sorted({methods[mid]['path'] for mid in sorted(allmethods)}|{s['path'] for s in g['screens']}|{routines[r]['path'] for r in g['routines']})
        mappings=[mp for mid in sorted(allmethods) for mp in methods[mid]['mappings']]
        for s in g['screens']:
            for i in s['items']:
                i['db']=[] if i['role'].startswith('操作') else list({(mp['table'],mp['column']):mp for mp in mappings if mp['field']==i['field']}.values())
    # Exact method availability for explicit API contracts; do not claim runtime dispatch success.
    unresolved_api=[]
    for s in screens:
        for a in s['apis']:
            a['matched']=[mid for mid in services.get(a['service'],{}).get('methods',[]) if methods[mid]['name']==a['method']]
            if len(a['matched'])!=1:unresolved_api.append(a)
    shapes=[]
    for p,t in texts.items():
        if not (p.endswith('.cs') and '/BusinessService/' in p):continue
        mask=masked(t);brackets=pairs(mask);ns=re.search(r'namespace\s+([\w.]+)',mask)
        for cm in re.finditer(r'public\s+(?:partial\s+)?class\s+(\w+)\s*(?::\s*([^\n{]+))?\s*({)',mask):
            op=cm.start(3);end=brackets.get(op)
            if end is None:continue
            body=t[op+1:end];fields=[]
            for m in re.finditer(r'public\s+([\w?.<>\[\],]+)\s+(\w+)\s*\{\s*get;\s*set;\s*\}[^\n]*',body):
                nearby=body[max(0,m.start()-400):m.start()]
                summaries=re.findall(r'<summary>([\s\S]*?)</summary>',nearby)
                inline=re.search(r'//([^\n]+)',m[0])
                fields.append({'name':m[2],'type':m[1],'description':normalize(inline[1] if inline else summaries[-1] if summaries else ''),'line':t.count('\n',0,op+1+m.start())+1})
            shapes.append({'name':cm[1],'namespace':ns[1] if ns else '', 'base':normalize(cm[2] or ''),'path':p,'fields':fields})
    for g in services.values():
        g['shapes']=[x for x in shapes if x['namespace']=="MCT.ERP.Service."+g['key'].removeprefix('Mobile.')]
    return {'inventory':inventory,'texts':texts,'records':records,'methods':methods,'tables':tables,'routines':routines,'graph':graph,'shapes':shapes,'features':sorted(services.values(),key=lambda x:x['id']),'screens':screens,'apis':apis,'unresolved_api':unresolved_api,'workbooks':bookmeta,'schema_snapshots':[{'path':x['path'],'tables':len(x['tables']),'ddl_strings':x['ddl_strings']} for x in schemas], 'active_schema_snapshot':latest['path'] if latest else None,'stats':{'input_files':len(inventory),'parsed_files':len(records),'parsed_this_run':parsed,'cache_hits':hits,'errors':errors,'statuses':dict(Counter(x['status'] for x in inventory))}}
