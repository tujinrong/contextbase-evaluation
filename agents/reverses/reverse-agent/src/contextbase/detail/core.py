"""P2: reread related source, extract conditional flows and seal resolved specs.

The reviewed pilot is structured data applied ONLY while its source identity
and independently extracted method contract match. P3 never calls this module.
"""
from __future__ import annotations
from collections import defaultdict, deque
from copy import deepcopy
import re
from pathlib import Path
from contextbase.foundation.core import P1
from contextbase.shared.store import digest, safe, read, write, verify, seal, locked, staged, tree_hashes, engine_hash, fact
from contextbase.itemlist import normalize
from contextbase.markup_items import extract_markup
from contextbase.shared.extensions import load_extension
from contextbase.delivery_policy import ReviewLog
from specgen.adapters.csharp_flow import analyze_flow
from specgen.common import decode_source, snippet
from contextbase.shared.schemas import validate
from .documents import basic_document, detail_document, common_documents
from contextbase.shared.identities import resolve as resolve_identity
from specgen.adapters.csharp_relations import SemanticIndex
from .semantics import terminology, field_labels, enrich_event, attach_item_storage, client_events
from .layout import build_screen, build_relation_diagram
from .database import collect as collect_sql, java_related, database_documents
from .bindings import BindingIndex
from .event_templates import enrich as enrich_event_document

P2='ContextBase/02-detailed'


def flow_relations(methods, memory_fields=()):
    result=[]
    for m in methods:
        for step in m['steps']:
            expr=step.get('expression','')
            kind=None;operation=None
            if re.search(r'\b(?:Session|session)\.',expr):
                kind='session';operation='delete' if re.search(r'\.(?:Remove|Clear)',expr) else 'update' if '.Set' in expr else 'read'
            elif any(re.search(r'(?<![\w])'+re.escape(field)+r'(?![\w])',expr) for field in memory_fields):
                kind='memory';operation='delete' if '.Remove(' in expr else 'create' if '.Add(' in expr else 'update' if re.search(r'\w+\[.+\]\s*=',expr) else 'read'
            elif re.search(r'\b(?:BeginTransaction|Commit|Rollback)\s*\(',expr):
                kind='transaction';operation='control'
            if kind:
                result.append({'kind':kind,'store':'セッション保持情報' if kind=='session' else 'プログラム内コレクション' if kind=='memory' else 'トランザクション',
                               'operation':operation,'event':m['name'],'evidence':[{'path':m['path'],'line':step['line']}],
                               'guards':step.get('guards',[]),'expression':expr})
    return result


def reachable(entry, methods, dependencies, limit=60):
    byname=defaultdict(list)
    for m in methods:
        if m['path'] in dependencies:byname[m['name']].append(m)
    found=[];seen=set();queue=deque([entry]);unresolved=[]
    while queue and len(found)<limit:
        m=queue.popleft();key=(m['path'],m['name'],m['line'])
        if key in seen:continue
        seen.add(key);found.append(m)
        for call in m['calls']:
            name=call['name'].split('.')[-1];candidates=byname.get(name,[])
            same=[c for c in candidates if c['path']==m['path']]
            candidates=same or candidates
            if len(candidates)==1:queue.append(candidates[0])
            elif candidates:unresolved.append({'caller':key,'call':call,'reason':'ambiguous_overload_or_owner','candidates':[c['path'] for c in candidates]})
    if queue:unresolved.append({'reason':'traversal_limit','limit':limit})
    return found,unresolved


def public_event(method, name, qa_id):
    descriptions=[]
    for n in method['steps']:
        value=n.get('expression','');kind=n['kind']
        if kind=='return':
            if 'RedirectToPage' in value:
                target=re.search(r'RedirectToPage\("([^"]+)"',value)
                description='所定の処理後、'+(target[1]+'へ遷移する。' if target else '対象画面へ遷移する。')
            elif 'Page()' in value:description='該当する分岐では同一画面を返す。'
            elif 'JsonResult' in value:description='該当する分岐では処理結果をJSON形式で返す。'
            elif 'NoContentResult' in value:description='該当する分岐ではHTTP 204を返す。'
            elif 'File(' in value:description='生成したファイルを応答として返す。'
            else:continue
        elif 'AddModelError' in value:
            strings=re.findall(r'"([^"\n]*)"',value)
            description='入力エラーを表示する。'+(strings[-1] if strings else '')
        elif re.search(r'\.Save\(',value):description='条件を満たす場合に、対象データの保存処理を呼び出す。'
        elif re.search(r'\.Delete\(',value):description='条件を満たす場合に、対象データの削除処理を呼び出す。'
        elif 'ModelState.Clear()' in value:description='画面入力の検証状態を消去する。'
        else:continue
        descriptions.append(description)
    return {'id':'E-'+digest([method['path'],method['name'],method['signature']])[:12].upper(),
            'name':name,'trigger':method['name'],
            'description':f'静的に検出した処理順を示す。業務上の条件解釈は暫定であり、原本の分岐を詳細仕様に記録する（仮定 {qa_id}）。',
            'public_steps':descriptions,'methods':[method],'steps':method['steps'],
            'basis':'static_partial','qa_id':qa_id}


def adopted_fields(items, review, dependencies):
    decisions=[]
    for row in items:
        for field in ['required','length','db','choices']:
            qids=re.findall(r'Q-[A-Z0-9-]+',str(row.get(field,'')))
            for qid in qids:
                q=review.questions.get(qid,{})
                adoption=q.get('adoption',{})
                if adoption.get('status')!='approved':continue
                if adoption.get('source_hashes')!=dependencies:
                    q['status']='recheck';decisions.append({'qa_id':qid,'adopted':False,'reason':'dependency_hash_mismatch'});continue
                value=adoption.get('value')
                if not isinstance(value,(str,bool,int,float)):continue
                label=('必須' if value else '任意') if field=='required' and isinstance(value,bool) else str(value)
                row[field]=label+f'（採用判断 {qid}）'
                decisions.append({'qa_id':qid,'field':field,'adopted':True,'basis':'reviewed_decision_not_source_fact'})
    return decisions


def run(root: Path, *, feature=None, cold=False, config_file='config/project.toml') -> dict:
    root=root.resolve()
    with locked(root,'contextbase-phases'):
        foundation=safe(root,P1);base=verify(foundation);source=safe(root,base['input'])
        if base['engine']!=engine_hash(root,'src/contextbase','src/specgen','src-dynamic'):
            raise ValueError('P1 analyzer generation changed; rerun P1')
        hashes=read(foundation/'source-index/hashes.json')
        if tree_hashes(source)!=hashes:raise ValueError('P1/source generation mismatch; rerun P1')
        system=read(foundation/'system/system.json');catalog=read(foundation/'catalogs/features.json')
        feature=resolve_identity(feature,catalog)
        selected=[f for f in catalog if not feature or f['id']==feature]
        if not selected:raise ValueError('Unknown feature ID: '+str(feature))
        mapping=read(foundation/'source-index/unit-map.json')
        units={p:read(foundation/f'source-index/units/{key}.json') for p,key in mapping.items()}
        texts={p:decode_source(safe(source,p).read_bytes())[0] for p in units}
        methods=[];flow_hits=0
        flow_cache=safe(root,'.specgen-state/detail-source');flow_cache.mkdir(parents=True,exist_ok=True)
        for p,text in texts.items():
            if Path(p).suffix.lower() in {'.cs','.java'}:
                key=digest([base['engine'],p,hashes[p]])
                cachefile=flow_cache/(key+'.json')
                entry=read(cachefile) if not cold and cachefile.exists() else {}
                if entry.get('hash')==digest(entry.get('methods')) and 'methods' in entry:
                    extracted=entry['methods'];flow_hits+=1
                else:
                    extracted=analyze_flow(text,p)['methods']
                    write(cachefile,{'hash':digest(extracted),'methods':extracted})
                methods.extend(extracted)
            else:
                methods.extend({'name':m['name'],'path':p,'signature':m.get('signature',''), 'line':m.get('line',1),
                                'end_line':m.get('end_line',1),'steps':[{'kind':s.get('kind','statement'),'expression':s.get('text',''),
                                'line':s.get('line',1),'guards':[]} for s in m.get('steps',[])],
                                'calls':m.get('calls',[]),'flow':[]} for m in units[p].get('symbols',[]))
        for m in methods:m['id']='M-'+digest([m['path'],m['name'],m['signature']])[:14]
        terminology_diagnostics=[]
        terminology_context={'project':base['project'],'input_dir':base['input'],
                             'source_hashes':hashes,'diagnostics':terminology_diagnostics}
        type_names=terminology(root,**terminology_context)
        field_names=terminology(root,'fields',**terminology_context)
        semantic_index=SemanticIndex(texts,methods,type_names)
        sql_operations=collect_sql(texts)
        logical_names={**type_names,**field_names}
        models_index=defaultdict(list)
        for p,u in units.items():
            for t in u.get('types',[]):models_index[t['name']].append((texts[p],p))
        models={name:values[0] for name,values in models_index.items() if len(values)==1}
        database=read(foundation/'database/catalog.json');review=ReviewLog(root)
        binding_index=BindingIndex(texts,sql_operations,database)
        oldquestions={q['id']:q for q in read(root/'QA/questions.json')['questions']} if (root/'QA/questions.json').exists() else {}
        # Historical/manual QA not visited by a targeted run retains its active state.
        for q in review.questions.values():q['active']=oldquestions.get(q['id'],{}).get('active',False) if feature else False
        pilot,extension,changed=load_extension(root,base['input'])
        if changed:
            review.add('pilot-source-change','職員番号入力','レビュー済み原本が変更されたため再照合が必要。','静的詳細解析を適用する。',', '.join(changed),'analysis')
        reviewed=None
        if pilot:
            descriptor=safe(root,pilot['directory']/pilot['review_data'])
            if descriptor.exists():
                reviewed=read(descriptor)
                for path,contract in reviewed['source_contract'].items():
                    actual={m['name'] for m in methods if m['path']==path}
                    if not set(contract['methods']).issubset(actual):raise ValueError('Independent pilot method extraction failed')
                    if any(v not in texts[path] for v in contract['expressions']):raise ValueError('Pilot source contract failed')
                extension.add_pilot_questions(review)
        engine=engine_hash(root,'src/contextbase','src/specgen','src-dynamic')
        cache=safe(root,'.specgen-state/detail');cache.mkdir(parents=True,exist_ok=True)
        results=[];messages=[];unresolved=[];adoptions=[];hits=0
        with staged(root,P2) as dest:
            # Preserve other feature results only if their entire upstream generation matches.
            previous=safe(root,P2)
            preserved=[]
            if feature and previous.exists():
                old=verify(previous)
                if old['foundation_generation']==base['generation']:
                    preserved=[read(previous/f'functions/{fid}/feature.json') for fid in old['feature_ids'] if fid!=feature]
            for f in selected:
                dependencies={p:hashes[p] for p in f['dependencies'] if p in hashes}
                binding=units[f['path']]
                items=binding.get('items',[])
                if f['path'].endswith('.cshtml'):
                    companion=f.get('companion')
                    markup=extract_markup(texts[f['path']],f['path'],texts.get(companion,''),companion or '',models)
                    items=markup['items'];binding={**binding,**markup}
                items=deepcopy(items)
                for item in items:
                    if item.get('name') in logical_names:item['name']=logical_names[item['name']]
                clean=review.delivery({**binding,'items':items})
                decisions=adopted_fields(clean['items'],review,dependencies);adoptions.extend(decisions)
                normalized=[normalize(row,i+1) for i,row in enumerate(clean['items'])]
                for i,row in enumerate(normalized):
                    row['id']=f['id']+f'-I{i+1:03}'
                    row['binding']=items[i].get('binding','')
                    row['facts']={field:fact(row[field],row.get('evidence',[]),'assumed' if '仮定' in str(row[field]) else 'source') for field in ['name','type','io','required','format','db','choices']}
                signature=digest({'engine':engine,'feature':f,'dependencies':dependencies,'database':database,
                                  'qa_adoptions':decisions,'adoption_values':clean['items']})
                cached=cache/(signature+'.json')
                if not cold and cached.exists():
                    saved=read(cached)
                    if saved.get('hash')==digest(saved.get('model')):
                        results.append(saved['model']);hits+=1
                        write(dest/'checkpoints.json',{'completed':[x['id'] for x in results]});continue
                entries=[m for m in methods if m['path']==(f.get('companion') or f['path']) and (f['kind']!='screen' or m['name'].startswith(('OnGet','OnPost')))]
                if f.get('entry_paths'):
                    entries += [m for m in methods if m['path'] in f['entry_paths'] and m['name']=='perform']
                events=[];reached=[];storage_effects=[]
                labels_by_field={**field_names,**field_labels(normalized)}
                for m in entries:
                    visits,call_edges,missed=semantic_index.trace(m,set(f['dependencies']))
                    related=list({v['method']['id']:v['method'] for v in visits}.values())
                    if m['path'].endswith('.java'):related=java_related(m,methods,set(f['dependencies']),texts)
                    reached.extend(related);unresolved.extend({'feature_id':f['id'],**x} for x in missed)
                    labels=[b['trigger'] for b in f['event_bindings'] if b.get('handler')==m['name'].removeprefix('OnPost')]
                    suffix=m['name'].removeprefix('OnPost').removeprefix('OnGet')
                    event_name=labels[0] if labels else '初期表示' if m['name']=='OnGet' else '送信・確認' if m['name']=='OnPost' else {'Save':'登録','Delete':'削除','Clear':'クリア'}.get(suffix,m['name'])
                    qid=review.add(f['id']+'|event|'+m['name'],f['name'], '分岐・処理順の業務解釈と例外経路を確認する。',
                                   '原本から取得した順序・条件と応答を適用する。',m['path']+':'+str(m['line']),'analysis')
                    event=public_event(m,event_name,qid);event['related_method_ids']=[x['id'] for x in related]
                    effects=semantic_index.effects(m,visits);storage_effects.extend(effects)
                    event['call_graph']=call_edges
                    enrich_event(event,semantic_index,m,visits,effects,labels_by_field)
                    if m['name'].startswith('OnGet') and m['name']!='OnGet' and effects:
                        import re as _re
                        params=_re.search(r'\((.*)\)',m['signature'],_re.S)
                        names=_re.findall(r'[\w?]+\s+(\w+)',params[1]) if params else []
                        event['name']='検索・照会（'+'・'.join(labels_by_field.get(n,n) for n in names)+'）'
                    if m['path'].endswith('.java'):
                        event['methods']=related
                        event['sql_operations']=[q for q in sql_operations if any(q['path']==x['path'] and q['owner'].split('@')[0]==x['name'] for x in related)]
                        if m['name']=='perform':event['name']=next((x['name'] for x in catalog if x['path']==m['path']),Path(m['path']).stem)
                    for effect in effects:effect['event_label']=event['name']
                    events.append(event)
                memory_fields={name for p in f['dependencies'] for name in re.findall(r'\b(?:List|Dictionary|HashSet|ConcurrentDictionary)<[^;]+?>\s+(\w+)\s*=',texts.get(p,''))}
                relations=[x for x in flow_relations({m['id']:m for m in reached}.values(),()) if x['kind']!='memory']+storage_effects
                attach_item_storage(normalized,f,texts,semantic_index,storage_effects,[v for e in events for v in e.get('validation_rules',[])])
                for p in f['dependencies']:
                    for d in units.get(p,{}).get('crud',[]):
                        relations.append({'kind':'database','store':d.get('table','未確定'),'operation':d.get('op',d.get('operation','unknown')),'event':'literal_sql','evidence':[{'path':p,'line':d.get('line',1)}]})
                value={'schema':'contextbase.feature.v1','id':f['id'],'aliases':f.get('aliases',[]),'name':f['name'],'kind':f['kind'],'route':f.get('route'),
                       'source':f['path'],'dependencies':dependencies,'summary':f['name']+'の入力・表示・要求処理を行う。',
                       'items':normalized,'events':events,'data_relations':relations,'scenarios':[],
                       'scope_note':'各仮定のQA番号を確認する。静的に確認できた操作・条件を適用する。',
                       'explanation_basis':'static_partial','signature':signature,
                       'related_data_names':sorted({r['store'] for r in relations}),
                       'field_labels':labels_by_field,'storage_catalog':[d for d in semantic_index.stores if d['id'] in {r.get('store_id') for r in relations}],
                       'client_events':client_events(texts[f['path']],f['path']) if f['kind']=='screen' else []}
                direct=[q for q in sql_operations if q['path']==f['path']]
                value['sql_operations']=list({q['id']:q for q in direct+[q for e in events for q in e.get('sql_operations',[])]}.values())
                # DB facts remain separate from memory/ORM collections.
                for q in value['sql_operations']:
                    value['data_relations'].append({'kind':'database','store':q['table'],'store_id':'DB-'+digest(q['table'])[:10],
                        'operation':{'C':'create','U':'update','D':'delete','R':'read','M':'upsert'}.get(q['operation'],q['operation']),
                        'event':q['owner'],'event_label':q['owner'].split('@')[0], 'evidence':[{'path':q['path'],'line':q['line']}]})
                primary={r['store'] for r in storage_effects if r['operation'] in {'create','update','delete'}}
                if primary and f['kind']=='screen':
                    ops={'create':'追加','read':'参照','update':'更新','delete':'削除','upsert':'追加／更新'}
                    actions='・'.join(ops[o] for o in ('read','create','update','delete','upsert') if any(r['operation']==o and r['store'] in primary for r in storage_effects))
                    value['summary']='対象データ「'+'・'.join(sorted(primary))+'」の'+actions+'を受け付ける画面。各イベントの入力条件・照合条件に従って処理する。'
                if reviewed and f['id']==reviewed['id']:
                    value.update(items=deepcopy(reviewed['items']),events=deepcopy(reviewed['events']),
                                 data_relations=reviewed['data_relations'],scenarios=reviewed['scenarios'],reviewed=reviewed,
                                 summary=next(b['value'] for b in reviewed['overview_blocks'] if b['kind']=='paragraph'),
                                 explanation_basis='source_hash_and_method_contract_matched')
                    for e in value['events']:
                        e['methods']=[m for m in methods if m['path']==f.get('companion') and m['name']==e['trigger']]
                    value['signature']=signature
                for e in value['events']:
                    if not value['scenarios']:
                        value['scenarios']=[{'id':f['id']+'-S01','input':'各イベントの分岐条件を満たす入力',
                                              'expected':'詳細仕様の分岐ごとの応答・状態変更を照合する（静的抽出による期待仕様候補）'}]
                results.append(value);write(cached,{'hash':digest(value),'model':value})
                write(dest/'checkpoints.json',{'completed':[x['id'] for x in results]})
            results += preserved
            results.sort(key=lambda v:v['id'])
            layout_findings=[]
            asset_dir=dest/'resolved/assets';asset_dir.mkdir(parents=True,exist_ok=True)
            for value in results:
                if value['kind']!='screen' or value.get('reviewed'):continue
                f=next(f for f in catalog if f['id']==value['id'])
                qid=review.add(value['id']+'|static-layout',value['name'],
                    '動的表示・共通CSS・画面遷移後の表示を実画面と照合する。',
                    '原本のマークアップ・CSSから構成した静的画面を掲載する。',value['source'],'analysis')
                try:
                    value['layout']=build_screen(f,texts,value['items'],asset_dir)
                    value['layout']['qa_id']=qid
                except Exception as exc:
                    value['layout']={'status':'projection_failed','runtime_verified':False,'images':[],'qa_id':qid}
                    layout_findings.append({'feature_id':value['id'],'reason':str(exc)})
                try:value['data_diagram']=build_relation_diagram(f,value['data_relations'],asset_dir)
                except Exception as exc:layout_findings.append({'feature_id':value['id'],'diagram_error':str(exc)})

            binding_stats=[]
            for value in results:
                if not value.get('reviewed'):
                    binding_stats.append({'feature_id':value['id'],**binding_index.apply(value)})
                    enrich_event_document(value,texts,database,asset_dir,{**logical_names,**{f['path']:f['name'] for f in catalog}})
            write(safe(root,'report/detail/db-bindings.json'),{'features':binding_stats,'unresolved':binding_index.unresolved,
                 'scope':'要求パラメーター・Modelアクセサー・JDBC位置・SELECT別名の静的追跡。別インスタンスや動的呼出の完全解析ではない。'})

            allids={m['id'] for m in methods}
            for value in results:
                validate('feature',value)
                for qid in re.findall(r'Q-[A-Z0-9-]+',str(value)):
                    if qid in review.questions:review.questions[qid]['active']=True
                for e in value['events']:
                    if not set(e.get('related_method_ids',[])).issubset(allids):raise ValueError('Broken method reference')
                folder=dest/'functions'/value['id']
                write(folder/'feature.json',value)
                for field,file in [('items','items'),('events','events'),('data_relations','data-relations'),('scenarios','scenarios')]:write(folder/(file+'.json'),value[field])
                write(folder/'layout.json',value.get('layout') or {'kind':'reviewed_assets' if value.get('reviewed') else 'source_definition_order','item_ids':[i['id'] for i in value['items']],'runtime_layout_verified':False})
                write(folder/'explanation.md',value['summary'])
            for p,text in texts.items():
                for m in re.finditer(r'(?:ErrorMessage\s*=\s*|AddModelError\([^\n]*?,\s*|Message\s*=\s*)"([^"\n]+)"',text):
                    messages.append({'id':'MSG-'+digest([p,m[1]])[:12],'text':m[1],'path':p,'line':text.count('\n',0,m.start())+1,
                                     'condition':'宣言・代入・エラー追加位置を根拠に抽出。実行経路は各イベント参照。'})
            documents=[]
            for value in results:
                name=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',value['name']).strip(' .') or value['id']
                category='基本設計書' if value['kind']=='screen' else '共通'
                prefix='基本設計書' if value['kind']=='screen' else '共通仕様書'
                documents.append({'feature_id':value['id'],'path':f'{category}/{prefix}_{value["id"]}_{name}.md','model':basic_document(value)})
                if value['kind']=='screen':documents.append({'feature_id':value['id'],'path':f'詳細仕様書/詳細仕様書_{value["id"]}_{name}.md','model':detail_document(value)})
            database['logical_stores']=semantic_index.stores
            documents+=common_documents(system,database,results,messages)
            documents+=database_documents(database,sql_operations)
            write(dest/'table-usage/sql-operations.json',sql_operations)
            from .documents import table,paragraph
            for category,title in [('reports','帳票一覧'),('batches','バッチ一覧'),('apis','要求処理一覧'),('files','ファイル一覧'),('codes','コード一覧')]:
                records=read(foundation/f'catalogs/{category}.json')['items']
                rows=[[str(r.get('name',r.get('text',''))),str(r.get('path','')),str(r.get('basis','')),str(r.get('values',r.get('method',r.get('direction',''))))] for r in records]
                documents.append({'path':'共通/'+title+'.md','model':{'title':title,'sections':[{'title':'概要','blocks':[
                    paragraph('原本の宣言・固定候補・ファイル名・入口から抽出した候補を示す。対象機能の実行条件と合わせて利用する。'),
                    table(['名称','原本','抽出根拠','定義内容'],rows)]}]}})
            write(dest/'common/methods.json',methods)
            write(dest/'messages/messages.json',messages)
            write(dest/'table-usage/operations.json',[r for v in results for r in v['data_relations']])
            write(dest/'interfaces/responses.json',[{'feature_id':v['id'],'event_id':e['id'],'responses':[n for m in e.get('methods',[]) for n in m['steps'] if n['kind']=='return']} for v in results for e in v['events']])
            write(dest/'decisions/qa-adoptions.json',adoptions)
            write(dest/'decisions/foundation-proposals.json',{'proposals':[],'policy':'P2はP1を書き換えない。差異は根拠付き提案として保存する。'})
            assets=[]
            applied=bool(reviewed and any(v['id']==reviewed['id'] for v in results))
            if applied:
                status=extension.prepare_assets(root,base['input'],pilot,asset_root=dest/'resolved/assets')
                # Pilot adds its images without replacing generic screen assets.
                write(safe(root,'report/pilot/status.json'),{**status,'pilot_applied':True,'status':'structured_review_source_matched'})
            else:write(safe(root,'report/pilot/status.json'),{'pilot_applied':False,'status':'source_changed' if changed else 'not_applicable'})
            assets=[{'source':'assets/'+p.name,'destination':'基本設計書/assets/'+p.name,'sha256':digest(p.read_bytes())} for p in sorted(asset_dir.iterdir()) if p.is_file()]
            write(safe(root,'report/detail/layout.json'),{'status':'partial' if layout_findings else 'pass','findings':layout_findings,'screens':[{'id':v['id'],**v['layout']} for v in results if v.get('layout')]})
            resolved={'schema':'contextbase.resolved.v1','project':base['project'],
                  'foundation_generation':base['generation'],'source_snapshot':base['snapshot'],
                  'features':[{'id':v['id'],'aliases':v.get('aliases',[]),'name':v['name'],'kind':v['kind']} for v in results],
                  'documents':documents,'assets':assets,'qa_ids':sorted(review.questions)}
            validate('resolved',resolved)
            write(dest/'resolved/catalog.json',resolved)
            # This directory is self-contained: P3 does not need source or dynamic code.
            manifest=seal(dest,{'schema':'contextbase.detail.v1','project':base['project'],
                                'foundation_generation':base['generation'],'source_snapshot':base['snapshot'],
                                'engine':engine,'feature_ids':[v['id'] for v in results]})
            if tree_hashes(source)!=hashes:raise ValueError('Input changed during P2')
        review.save()
        result={'status':'verified_structure_only','features':len(results),'selected':len(selected),'cache_hits':hits,
                'source_files_reread':len(texts),'flow_cache_hits':flow_hits,'methods':len(methods),'events':sum(len(v['events']) for v in results),
                'physical_tables':len(database['tables']),'pilot_structured':applied,'documents':len(documents),
                'generation':manifest['generation'],'errors':0}
        write(safe(root,'report/detail/result.json'),result)
        write(safe(root,'report/incomplete/detail.json'),{'unresolved_calls':unresolved,'source_changed':changed,'layout_findings':layout_findings,
                'terminology_adoptions':terminology_diagnostics,
                'limitations':['型解決・間接呼出・例外伝播の完全解析ではない。','他言語の詳細は既存アダプターの抽出範囲に限定する。','入力のDB定義書（Excel等）を自動確定する汎用読取は未実装。','QA自由記述回答は自動採用せず、approvedの型付き判断と依存ハッシュを検査する。']})
        write(safe(root,'ContextBase/manifest.json'),{'schema':'contextbase.v1','project':base['project'],
              'foundation_generation':base['generation'],'detail_generation':manifest['generation'],'detail_state':'resolved'})
        return result
