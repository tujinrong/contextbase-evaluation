"""P1: source inventory, feature skeletons and reconciled database foundation.

No deliverables are written here. C# primary constructors are distinguished
from methods. DTOs and in-memory collections are NOT physical DB tables.
"""
from __future__ import annotations
from collections import defaultdict
import re
from pathlib import Path
from contextbase.discovery import probe
from contextbase.generic import extract
from contextbase.markup_items import property_facts
from contextbase.registry import configure
from contextbase.shared.store import digest, safe, read, write, tree_hashes, seal, verify, locked, staged, engine_hash, fact
from specgen.common import decode_source, tokens, snippet
from specgen.adapters.csharp_flow import analyze_flow
from contextbase.shared.schemas import validate, SCHEMAS
from contextbase.shared.identities import assign
from specgen.adapters.csharp_relations import SemanticIndex
from specgen.adapters.java_sql import analyze_sql, sql_details
from contextbase.shared.logical_names import source_name, load_names, is_japanese

P1 = 'ContextBase/01-foundation'


def read_sources(root, cfg, survey):
    source = safe(root, cfg['input'])
    result={}
    for row in survey['inventory']:
        if 'sha256' not in row or row['status'] in {'too_large','requires_export'}:continue
        path=safe(source,row['path'])
        if any(x in {'bin','obj','node_modules','lib','dist'} for x in path.relative_to(source).parts):continue
        if path.suffix.lower() not in {'.cs','.java','.py','.js','.ts','.vue','.vb','.bas','.cls','.frm','.sql','.cshtml','.html','.jsp','.aspx','.json','.config','.xml','.csproj','.slnx','.css','.md','.txt','.properties'}:continue
        try:result[row['path']]=decode_source(path.read_bytes())[0]
        except ValueError:continue
    return result


def unit(text, path, language):
    r=extract(text,path,language or 'metadata') if language else {'path':path,'symbols':[],'items':[],'tables':[],'crud':[],'warnings':[]}
    if Path(path).suffix.lower() in {'.cs','.java'}:
        flow=analyze_flow(text,path)
        r['types']=flow['types']
        # P1 retains signatures only: P2 independently builds conditional flows.
        r['symbols']=[{k:v for k,v in m.items() if k not in {'flow','steps'}} for m in flow['methods']]
        props=property_facts(text,path)
        r['properties']=[{'name':name,**value} for name,value in props.items()]
        positional=re.search(r'\brecord\s+(\w+)\s*\(([^;{}]*)\)',text,re.S)
        if positional:
            for typ,name in re.findall(r'([\w?.<>]+)\s+(\w+)\s*(?:,|$)',positional[2]):
                r['properties'].append({'name':name,'type':typ,'line':text.count('\n',0,positional.start())+1,'required':None})
    if path.endswith('.java'):
        jdbc=analyze_sql(text,path)
        r['sql_queries']=jdbc['queries'];r['sql_constants']=jdbc['constants']
        r['crud']=[{**q,'evidence':'Javaの文字列式・定数・SQL組立から抽出'} for q in jdbc['queries']]
    if path.endswith('.jsp'):
        r['title']=source_name(path,text)
    r['identifiers']=sorted({t['text'] for t in tokens(text) if t['kind']=='word'})
    r['sha256']=digest(text)
    return r


def reconcile_database(units, sources):
    definitions=defaultdict(list);usages=defaultdict(list);models=[];objects=[];conflicts=[]
    for path,r in units.items():
        for d in r.get('tables',[]):definitions[d['name']].append({**d,'path':path})
        for d in r.get('crud',[]):
            name=d.get('table') or d.get('name')
            if name:usages[name].append({**d,'path':path})
        if r.get('properties'):
            models.append({'id':'D-'+digest(path)[:10].upper(),'name':Path(path).stem,
                           'storage_kind':'data_object_not_physical_table','path':path,
                           'fields':r['properties'],'evidence':[{'path':path,'line':1}]})
        if Path(path).suffix.lower()=='.sql':
            for m in re.finditer(r'\b(?:CREATE\s+(VIEW|PROCEDURE|FUNCTION|TRIGGER|INDEX)|ALTER\s+(TABLE))\s+([\w."\[\]]+)',sources[path],re.I):
                obj={'kind':(m[1] or 'ALTER TABLE').upper(),'name':m[3], 'path':path,
                     'line':sources[path].count('\n',0,m.start())+1,'status':'definition_detected_order_and_semantics_unresolved'}
                objects.append(obj)
                if m[2]:conflicts.append({'kind':'migration_order','object':obj,'message':'ALTERの適用順は未確定。CREATE定義を最終DBと扱わない。'})
    tables=[]
    for name in sorted(set(definitions)|set(usages)):
        defs=definitions[name];refs=usages[name];columns={}
        for d in defs:
            for c in d.get('columns',[]):
                evidence={'path':d['path'],'line':c.get('line',d.get('line',1))}
                entry=columns.setdefault(c['name'],{'name':c['name'],'logical_name':fact(c['name'],[evidence],'inferred'), 'variants':[]})
                entry['variants'].append({'type':c.get('type'),'nullable':c.get('nullable'),'primary_key':c.get('primary_key'),
                                          'default':c.get('default'),'evidence':evidence})
        for ref in refs:
            details=sql_details(ref) if ref.get('sql') else {}
            inferred=details.get('columns',[])
            constants=units.get(ref['path'],{}).get('sql_constants',{})
            inferred+= [v for k,v in constants.items() if k.startswith(('DBKEY_','COL_')) and isinstance(v,str)]
            for cname in inferred:
                if not cname or any(ch in cname for ch in '〈〉?'):continue
                evidence={'path':ref['path'],'line':ref.get('line',1)}
                columns.setdefault(cname,{'name':cname,'logical_name':fact(cname,[evidence],'source'), 'variants':[], 'status':'program_reference_inferred'})
        for c in columns.values():
            variants={digest({k:v for k,v in x.items() if k!='evidence'}) for x in c['variants']}
            c['status']='conflict' if len(variants)>1 else 'declared' if variants else 'program_reference_inferred'
            if c['status']=='conflict':conflicts.append({'kind':'column_definition','table':name,'column':c['name'],'variants':c['variants']})
        tables.append({'id':'T-'+digest(name)[:10].upper(),'name':name,'logical_name':fact(name.split('.')[-1],[{'path':x['path'],'line':x.get('line',1)} for x in defs or refs],'inferred'),
                       'origin':'declaration' if defs else 'program_reference_inferred','columns':list(columns.values()),
                       'definitions':defs,'usages':refs,'physical_schema_verified':False})
    return {'tables':tables,'data_objects':models,'objects':objects,'conflicts':conflicts,
            'physical_table_count':len(tables),'status':'static_observed',
            'limitation':'DDL/ORM明示定義とSQL参照を統合する。ALTER適用、実DB、Excel定義書の自動採用は未検証。DTOをDB表へ変換しない。'}



def supporting_catalogs(features, units, sources):
    catalogs={name:[] for name in ['screens','reports','batches','apis','files','common','codes','messages']}
    catalogs['screens']=[f for f in features if f['kind']=='screen']
    catalogs['common']=[f for f in features if f['kind']=='common']
    for f in catalogs['screens']:
        if '/Reports/' in f['path']:
            catalogs['reports'].append({'feature_id':f['id'],'name':f['name'],'path':f['path'],
                                         'basis':'route_naming_candidate','scheduled_execution_confirmed':False})
        if Path(f['path']).stem.lower()=='batch':
            catalogs['batches'].append({'feature_id':f['id'],'name':f['name'],'path':f['path'],
                                        'basis':'UI_triggered_batch_candidate','scheduled_execution_confirmed':False})
    for path,u in units.items():
        text=sources[path]
        for m in u.get('symbols',[]):
            if m['name'].startswith(('OnGet','OnPost')):
                name=m['name'];verb='GET' if name.startswith('OnGet') else 'POST'
                catalogs['apis'].append({'name':name,'method':verb,'path':path,'line':m['line'],
                                         'basis':'handler_declaration','public_API_contract_confirmed':False})
        for hit in re.finditer(r'"([^"\n]*\.(?:xlsx|csv|zip|pdf|txt))"',text,re.I):
            catalogs['files'].append({'name':hit[1],'path':path,'line':text.count('\n',0,hit.start())+1,
                                      'basis':'filename_literal','direction':'requires_call_context'})
        for hit in re.finditer(r'\benum\s+(\w+)\s*\{([^{}]*)\}',text,re.S):
            values=[x.strip() for x in hit[2].split(',') if x.strip()]
            catalogs['codes'].append({'name':hit[1],'values':values,'path':path,'line':text.count('\n',0,hit.start())+1,'basis':'enum_declaration'})
        for item in u.get('items',[]):
            choices=item.get('choices','')
            if choices.startswith('固定候補：'):
                catalogs['codes'].append({'name':item['name'],'values':choices.removeprefix('固定候補：').split('／'),'path':path,'line':item['line'],'basis':'static_options'})
        for hit in re.finditer(r'(?:ErrorMessage\s*=\s*|AddModelError\([^\n]*?,\s*|Message\s*=\s*)"([^"\n]+)"',text):
            catalogs['messages'].append({'text':hit[1],'path':path,'line':text.count('\n',0,hit.start())+1,'basis':'declaration_or_assignment'})
    return catalogs

def run(root: Path, *, feature=None, cold=False, config_file='config/project.toml') -> dict:
    if feature:raise ValueError('P1 builds a whole-project foundation; --feature is for P2/P3')
    root=root.resolve();cfg=configure(root,config_file);source=safe(root,cfg['input'])
    with locked(root,'contextbase-phases'):
        before=tree_hashes(source);survey=probe(root,cfg);sources=read_sources(root,cfg,survey)
        engine=engine_hash(root,'src/contextbase','src/specgen','src-dynamic')
        cache=safe(root,'.specgen-state/foundation');cache.mkdir(parents=True,exist_ok=True)
        metadata={x['path']:x for x in survey['inventory'] if x.get('path')}
        units={};reused=0
        for path,text in sources.items():
            signature=digest([engine,path,digest(text)])
            cachefile=cache/(signature+'.json')
            if not cold and cachefile.is_file():
                envelope=read(cachefile)
                if envelope.get('signature')==signature and envelope.get('hash')==digest(envelope.get('unit')):
                    units[path]=envelope['unit'];reused+=1;continue
            units[path]=unit(text,path,metadata.get(path,{}).get('language'))
            write(cachefile,{'signature':signature,'hash':digest(units[path]),'unit':units[path]})
        type_index=defaultdict(list)
        for path,u in units.items():
            for t in u.get('types',[]):type_index[t['name']].append(path)
        graph={path:set() for path in units}
        for path,u in units.items():
            for name in u['identifiers']:
                graph[path].update(p for p in type_index.get(name,[]) if p!=path)
            text=sources[path]
            for interface,impl in re.findall(r'Add(?:Singleton|Scoped|Transient)\s*<\s*(\w+)\s*,\s*(\w+)\s*>',text):
                for base in type_index.get(interface,[]):graph[base].update(type_index.get(impl,[]))
            if path.endswith('.cshtml') and path+'.cs' in units:graph[path].add(path+'.cs')
        # Discover uniquely named extension/helper methods, not only type names.
        method_paths=defaultdict(set)
        for path,u in units.items():
            for method in u.get('symbols',[]):method_paths[method['name']].add(path)
        for path,u in units.items():
            for method in u.get('symbols',[]):
                for call in method.get('calls',[]):
                    targets=method_paths.get(call['name'].split('.')[-1],set())
                    if len(targets)==1:graph[path].update(targets-{path})
        globals_=[p for p in units if Path(p).name in {'Program.cs','_Layout.cshtml','_ViewStart.cshtml','_ViewImports.cshtml','site.css','site.js'}]
        features=[];consumed=set();oldids={}
        logical_names=load_names(root,sources)
        old=safe(root,P1)
        if old.is_dir():
            try:verify(old);oldids={x['path']:x for x in read(old/'catalogs/features.json')}
            except (OSError,ValueError):oldids={}
        overrides={}
        for f in sorted(safe(root,'src-dynamic').glob('*/foundation.json')):
            safe(root,f);data=read(f)
            if data.get('trust')=='repository-reviewed':overrides.update(data.get('features',{}))
        for path,u in units.items():
            suffix=Path(path).suffix.lower()
            screen=suffix in {'.cshtml','.vue','.frm','.html','.aspx','.jsp'} and not Path(path).name.startswith('_')
            if screen and suffix=='.jsp' and not re.search(r'<(?:html|body|form|input|button|main|table)\b',sources[path],re.I):screen=False
            if screen:
                deps=set(globals_+[path]);todo=[path];visited=set()
                while todo:
                    current=todo.pop()
                    if current in visited:continue
                    visited.add(current)
                    for d in graph[current]:
                        deps.add(d)
                        if d not in visited:todo.append(d)
                entry_paths=[]
                if suffix=='.jsp':
                    from bs4 import BeautifulSoup
                    dom=BeautifulSoup(re.sub(r'<%[\s\S]*?%>','',sources[path]),'html.parser')
                    view_ids={n.get('value','') for n in dom.find_all('input') if str(n.get('name','')).upper()=='VIEW_ID'}
                    stem=Path(path).stem
                    for candidate in units:
                        if candidate.startswith(path.split('/')[0]+'/') and candidate.endswith('Action.java') and any(Path(candidate).stem.startswith(v) for v in view_ids if v and v==stem):
                            entry_paths.append(candidate);deps.add(candidate)
                            deps.update(graph.get(candidate,set()))
                settings=overrides.get(path,{})
                rename=next((x for p,x in oldids.items() if p not in units and x.get('source_sha256')==u['sha256']),None)
                fid=settings.get('id') or oldids.get(path,{}).get('id') or (rename or {}).get('id') or 'F-'+digest(path)[:10].upper()
                name=settings.get('name') or source_name(path,sources[path],logical_names)
                route='/' + path.split('/Pages/',1)[1].removesuffix('.cshtml') if '/Pages/' in path else None
                features.append({'id':fid,'name':name,'kind':'screen','path':path,'source_sha256':u['sha256'],
                                 'route':route,'entry_paths':entry_paths,'companion':path+'.cs' if path+'.cs' in units else None,
                                 'dependencies':sorted(deps),'items':u.get('items',[]),'event_bindings':u.get('events',[]),
                                 'ready_for_detail':True,'boundary_basis':'entry_markup_with_companion'})
                consumed.update([path,path+'.cs'])
        for path,u in units.items():
            if path in consumed or not u.get('symbols'):continue
            features.append({'id':'C-'+digest(path)[:10].upper(),'name':source_name(path,sources[path],logical_names),'kind':'common','path':path,
                             'source_sha256':u['sha256'],'dependencies':sorted({path}|graph[path]),'items':[],
                             'event_bindings':[],'ready_for_detail':True,'boundary_basis':'source_unit_unreviewed_business_boundary'})
        for f in features:
            for item in f['items']:
                if item.get('name') in logical_names:item['name']=logical_names[item['name']]
        identity_file=safe(root,'ContextBase/identities.json')
        identities=assign(features,read(identity_file) if identity_file.exists() else None,cfg['id'])
        db=reconcile_database(units,sources)
        for t in db['tables']:
            n=t['name'];mapped=logical_names.get(n) or logical_names.get(n.split('.')[-1])
            if mapped:t['logical_name']['value']=mapped
            for c in t['columns']:
                mapped=logical_names.get(n+'.'+c['name']) or logical_names.get(c['name'])
                if mapped:c['logical_name']['value']=mapped
        names={}
        for p in sorted(safe(root,'src-dynamic').glob('*/terminology.json')):
            data=read(safe(root,p))
            if data.get('trust')=='repository-reviewed':names.update(data.get('types',{}))
        db['logical_stores']=SemanticIndex(sources,[{**m,'path':p} for p,u in units.items() if p.endswith('.cs') for m in u.get('symbols',[])],names).stores
        for f in features:validate('skeleton',f)
        if len({f['id'] for f in features})!=len(features):raise ValueError('Duplicate feature identity')
        inventory=[{**x,'parsed':x['path'] in units} for x in survey['inventory']]
        result={'status':'verified_structure_only','input_files':len(before),'source_units':len(units),
                'features':len(features),'screens':sum(f['kind']=='screen' for f in features),
                'physical_tables':len(db['tables']),'data_objects':len(db['data_objects']),
                'cache_hits':reused,'parsed':len(units)-reused,'errors':0}
        with staged(root,P1) as dest:
            write(dest/'system/system.json',{'project':cfg['id'],'languages':survey['languages'],'families':survey['families'],
                                            'repository':cfg['repository'],'input':cfg['input'],'status':'static_detected',
                                            'customer':fact(None,[],'unknown'),'author':fact(None,[],'unknown')})
            write(dest/'source-index/inventory.json',inventory)
            write(dest/'source-index/hashes.json',before)
            write(dest/'catalogs/features.json',features)
            for kind,entries in supporting_catalogs(features,units,sources).items():
                write(dest/f'catalogs/{kind}.json',{'items':entries,'status':'static_candidates' if entries else 'unresolved_not_absent'})
            write(dest/'common-index/units.json',[{'id':f['id'],'path':f['path'],'dependencies':f['dependencies']} for f in features if f['kind']=='common'])
            for f in features:write(dest/f'feature-skeletons/{f["id"]}.json',f)
            for path,u in units.items():write(dest/f'source-index/units/{digest(path)[:20]}.json',u)
            write(dest/'source-index/unit-map.json',{p:digest(p)[:20] for p in units})
            write(dest/'relations/dependencies.json',{p:sorted(v) for p,v in graph.items()})
            write(dest/'database/catalog.json',db)
            for t in db['tables']:write(dest/f'database/tables/{t["id"]}.json',t)
            write(dest/'glossary/terms.json',[{'physical':p['name'],'logical':fact(p['name'],[{'path':path,'line':p['line']}],'inferred')} for path,u in units.items() for p in u.get('properties',[])])
            manifest=seal(dest,{'schema':'contextbase.foundation.v1','project':cfg['id'],'input':cfg['input'],
                               'snapshot':digest(before),'engine':engine,'result':{k:v for k,v in result.items() if k not in {'cache_hits','parsed'}}})
            if tree_hashes(source)!=before:raise ValueError('Input changed during P1')
        write(identity_file,identities)
        for name,schema in SCHEMAS.items():write(safe(root,'ContextBase/schemas/'+name+'.json'),schema)
        write(safe(root,'ContextBase/manifest.json'),{'schema':'contextbase.v1','project':cfg['id'],
                                                   'foundation_generation':manifest['generation'],'detail_state':'requires_generation_check'})
        write(safe(root,'report/foundation/result.json'),{**result,'generation':manifest['generation']})
        write(safe(root,'report/incomplete/foundation.json'),{'conflicts':db['conflicts'],
                'unparsed_files':[x for x in inventory if not x['parsed']], 'database_limitation':db['limitation'],
                'classification_limitation':'帳票・バッチ・API・コードの業務境界は詳細解析と追加レビューで補完する。'})
        return {**result,'generation':manifest['generation']}
