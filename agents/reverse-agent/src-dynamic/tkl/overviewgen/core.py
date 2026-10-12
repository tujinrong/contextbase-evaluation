"""Language-neutral orchestration and normalized intermediate data.

All application files are read-only. The TKL editorial data is a profile, not a
language adapter. Unknown metadata and unresolved mappings remain explicit.
"""
from __future__ import annotations
import ast
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from . import adapters

EXCLUDE = {'.git','obj','bin','node_modules','packages','vendor','__pycache__','.venv','dist','build'}
INPUT_TAGS = {'TextBox','PasswordBox','ComboBox','DatePicker','CheckBox','RadioButton','ListBox','TreeView'}
VALUE_ATTRS = {'Text','SelectedValue','SelectedItem','SelectedDate','IsChecked','Binding','Content'}


def digest(value):
    return hashlib.sha256(value if isinstance(value,bytes) else str(value).encode()).hexdigest()


def dumps(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n'


def save(path:Path,value):
    text=value if isinstance(value,str) else dumps(value)
    if path.is_symlink(): raise ValueError('symlink output rejected')
    if path.exists() and path.read_text(encoding='utf-8')==text: return False
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    with tmp.open('w',encoding='utf-8',newline='\n') as f:
        f.write(text); f.flush(); os.fsync(f.fileno())
    tmp.replace(path)
    return True


def load(path,default=None):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError): return default


def literals(path):
    if not path.exists(): return {}
    result={}
    for node in ast.parse(path.read_text(encoding='utf-8-sig')).body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try: result[node.targets[0].id]=ast.literal_eval(node.value)
            except (ValueError,TypeError): pass
    return result


def git(root,*args):
    try: return subprocess.check_output(['git',*args],cwd=root,text=True,stderr=subprocess.DEVNULL).strip()
    except (OSError,subprocess.CalledProcessError): return ''


def safe_name(value):
    value=re.sub(r'[<>:"/\\|?*\x00-\x1f]','＿',value).strip(' .')
    return value[:90] or '名称未確定'


def bindings(attrs):
    out=[]
    for key,val in attrs.items():
        if key not in VALUE_ATTRS: continue
        m=re.search(r'\{Binding\s+(?:Path\s*=\s*)?([\w.]+)',val)
        if m and m.group(1) not in out: out.append(m.group(1))
    return out


def style_registry(records):
    styles={}
    for r in records.values():
        for i,n in enumerate(r.get('nodes',[])):
            a=n['attrs']
            if n['tag']=='Style' and a.get('x:Key'):
                values={}; handlers=[]
                for child in r['nodes'][i+1:]:
                    if child['parent']==i:
                        if child['tag']=='Setter' and 'Value' in child['attrs']: values[child['attrs'].get('Property')]=child['attrs']['Value']
                        if child['tag']=='EventSetter': handlers.append(child['attrs'])
                styles[a['x:Key']]={'values':values,'base':a.get('BasedOn',''),'handlers':handlers,'path':r['path'],'line':n['line']}
    return styles


def resolve_style(attrs,styles):
    values,chain,seen={},[],set()
    style=attrs.get('Style','')
    while m:=re.search(r'\{(?:Static|Dynamic)Resource\s+([^}]+)\}',style):
        key=m.group(1)
        if key in seen or key not in styles: break
        seen.add(key); item=styles[key]; chain.insert(0,item); style=item['base']
    for item in chain: values.update(item['values'])
    values.update(attrs)
    return values,chain


def logical_type(name,tag,attrs):
    if tag.endswith('Button'): return '操作'
    if tag in {'CheckBox','RadioButton'}: return '選択（真偽）'
    if tag in {'ComboBox','TreeView','ListBox'}: return '選択'
    if tag=='DatePicker': return '日付'
    if tag=='PasswordBox': return '秘匿文字'
    if re.search('金額|単価|定価|合計|残高|入金額',name): return '金額'
    if re.search('率|％|%',name): return '率'
    if re.search('部数|数量|月数|年数|号数',name): return '数値'
    if re.search('日付|更新日|注文日|契約日|入金日|期限',name): return '日付'
    if 'number' in attrs.get('Style',''): return '数値'
    return '文字'


def visual_key(node,nodes):
    # Container hierarchy first; row/column and local coordinates second. This is
    # a static approximation and deliberately distinct from focus/tab order.
    chain=[]; cur=node
    while cur is not None:
        a=cur['attrs']
        def num(x):
            try:return float(x)
            except (ValueError,TypeError):return 0.0
        margin=a.get('Margin','0,0,0,0').split(',')
        xy=(num(margin[1]) if len(margin)>1 else 0.0,num(margin[0]))
        chain.insert(0,(num(a.get('Grid.Row','0')),num(a.get('Grid.Column','0')),xy[0],xy[1],cur['line']))
        cur=nodes[cur['parent']] if cur['parent'] is not None else None
    return chain


def fields(screen,code,models,styles):
    names={p['name']:p['summary'] for r in models for p in r.get('fields',[]) if p['summary']}
    required={x for m in code.get('methods',[]) for x in m['required']}
    out=[]; nodes=screen['nodes']
    for ni,node in enumerate(nodes):
        a=node['attrs']; tag=node['tag']; name=a.get('x:Name',a.get('Name',''))
        iscol=tag.endswith('Column') and ('Header' in a or 'Binding' in a or tag=='DataGridTemplateColumn')
        bound=bindings(a)
        if tag not in INPUT_TAGS and not tag.endswith('Button') and not iscol and not (tag in {'TextBlock','Label'} and bound): continue
        inherited,chain=resolve_style(a,styles)
        b=bound[0] if bound else ''
        label=a.get('Header') or (a.get('Content') if not a.get('Content','').startswith('{') else '') or ''
        origin='caption'
        if not label and b in names: label=names[b]; origin='model_comment'
        if not label:
            try:
                x,y=[float(v) for v in a['Margin'].split(',')[:2]]
                cand=[]
                for l in nodes:
                    if l['parent']!=node['parent'] or l['tag'] not in {'Label','TextBlock'}: continue
                    la=l['attrs']; text=la.get('Content',la.get('Text',''))
                    if not text or text.startswith('{') or not re.search('[\u3040-\u9fff]',text):continue
                    try:
                        lx,ly=[float(v) for v in la.get('Margin','').split(',')[:2]]
                        if abs(ly-y)<3 and lx<x:cand.append((lx,text))
                    except ValueError:pass
                if cand: label=max(cand)[1]; origin='static_label_position'
            except (KeyError,ValueError):pass
        if not label and tag.endswith('Button'):
            label=inherited.get('Content','')
        if not label: label=names.get(b) or ('一覧選択' if tag in {'ListBox','TreeView'} else '管理項目' if iscol else '名称要確認'); origin='unresolved'
        if label.startswith('{'): label='名称要確認'; origin='unresolved'
        invisible=inherited.get('Visibility') in {'Hidden','Collapsed'}
        parent=node['parent']
        while parent is not None:
            pa,_=resolve_style(nodes[parent]['attrs'],styles)
            invisible=invisible or pa.get('Visibility') in {'Hidden','Collapsed'}
            parent=nodes[parent]['parent']
        role='operation' if tag.endswith('Button') else 'display' if iscol or tag in {'TextBlock','Label'} or inherited.get('IsReadOnly','').lower()=='true' or inherited.get('IsEnabled','').lower()=='false' else 'input'
        if invisible: role='internal'
        if tag.endswith('Button'):
            req,length='対象外','対象外'
        elif role in {'display','internal'}: req,length='対象外','表示形式による'
        else:
            req='条件付き必須（表示中・対象操作時）' if name in required else '必須指定なし（業務条件はイベント参照）'
            limit=inherited.get('MaxLength')
            byte_limited=any(any(h.get('Handler','') in {'txtImeOn_PreviewTextInput','txtImeOn_PreviewExecuted'} for h in s['handlers']) for s in chain)
            length=(limit+('バイト（Shift_JIS）／文字数制限も適用' if byte_limited else '文字')) if limit and limit!='0' else '個別上限未確認'
        out.append({'key':name or 'node_'+str(ni),'node':ni,'name':label.replace('\n',' '),'label_origin':origin,'role':role,'type':logical_type(label,tag,inherited),'required':req,'length':length,'binding':b,'tag':tag,'is_column':iscol,'line':node['line'],'path':screen['path'],'display_order':visual_key(node,nodes),'tab_index':inherited.get('TabIndex'),'visibility':inherited.get('Visibility','Visible'),'style_refs':[{'path':s['path'],'line':s['line']} for s in chain], 'db':[],'db_status':'not_applicable' if role=='operation' else 'unresolved','handlers': [h for s in chain for h in s['handlers']]+([{'Handler':a['Click'],'Event':'Click'}] if 'Click' in a else [])})
    out.sort(key=lambda x:(x['display_order'],x['node']))
    for i,item in enumerate(out,1):item['order']=i
    return out


def profile_data(root):
    # Reviewed profile is source, not a cache. Cold builds never need old analysis JSON.
    profile=load(Path(__file__).resolve().parents[1]/'profile.json',{})
    legacy={'features':profile.get('features',[]),'inventory':profile.get('inventory',[])}
    return legacy,profile.get('purpose',{}),profile.get('editorial',{})


def collect(root:Path,input_name='input',cold=False):
    started=time.perf_counter(); source=(root/input_name).resolve(); state=root/'.specgen-state/overview'
    if not source.is_relative_to(root) or source==root or source.is_symlink(): raise ValueError('invalid input root')
    if state.is_symlink(): raise ValueError('invalid state root')
    state.mkdir(parents=True,exist_ok=True)
    records={}; inventory=[]; stats={'parsed':0,'cache_hits':0,'errors':0,'read_bytes':0}
    adapter_hash=digest(Path(adapters.__file__).read_bytes())
    for path in sorted(source.rglob('*')):
        if not path.is_file() or path.is_symlink(): continue
        rel=path.relative_to(root).as_posix(); skipped=bool(set(path.relative_to(source).parts)&EXCLUDE)
        raw=path.read_bytes(); sha=digest(raw); stats['read_bytes']+=len(raw)
        selected=not skipped and path.suffix.lower() in adapters.EXTENSIONS
        inv={'path':rel,'sha256':sha,'bytes':len(raw),'selected':selected,'reason':'依存物・生成物' if skipped else '対応形式' if selected else '対象外形式・設定・資源'}
        inventory.append(inv)
        if not selected:continue
        cache=state/'files'/(digest(rel)+'.json')
        key=digest(sha+adapter_hash+path.suffix.lower())
        previous=load(cache,{})
        if not cold and previous.get('key')==key and previous.get('integrity')==digest(dumps(previous.get('record'))) and previous.get('record',{}).get('status')!='error':
            records[rel]=previous['record'];stats['cache_hits']+=1;continue
        try:
            if len(raw)>4_000_000: raise ValueError('source exceeds 4 MB limit')
            record=adapters.parse(adapters.decode(raw),rel);record['sha256']=sha;stats['parsed']+=1
        except Exception as ex:
            record={'path':rel,'status':'error','sha256':sha,'error':type(ex).__name__+': '+str(ex)};stats['errors']+=1
        records[rel]=record;save(cache,{'key':key,'record':record,'integrity':digest(dumps(record))})
    snapshot=digest(dumps(inventory)); save(state/'inventory.json',inventory)
    legacy,purposes,editorial=profile_data(root)
    compatible=bool(legacy) and all(next((i['sha256'] for i in inventory if i['path']==old['path']),None)==old['sha256'] for old in legacy.get('inventory',[]) if old.get('selected'))
    class_index=defaultdict(list)
    for path,r in records.items():
        for cls in r.get('classes',[]):class_index[cls['name']].append(path)
    method_index={};methods_by_name=defaultdict(list)
    for path,r in records.items():
        for m in r.get('methods',[]):
            mid=path+'#'+m['name']+'@'+str(m['line']); method_index[mid]={'path':path,**m};methods_by_name[m['name'].casefold()].append(mid)
    def targets(mid):
        m=method_index[mid];r=records[m['path']];found=[]
        for call in m['calls']:
            parts=call.rsplit('.',1);name=parts[-1]
            paths=[m['path']] if len(parts)==1 else class_index.get(r.get('types',{}).get(parts[0],parts[0]),[])
            for p in paths:
                found += [x for x in methods_by_name.get(name.casefold(),[]) if method_index[x]['path']==p]
        return sorted(set(found)-{mid})
    graph={mid:targets(mid) for mid in method_index}
    reverse=defaultdict(list)
    for parent,children in graph.items():
        for child in children:reverse[child].append(parent)
    def closure(mid):
        seen=set();queue=[mid]
        while queue:
            cur=queue.pop()
            if cur in seen:continue
            seen.add(cur);queue+=graph.get(cur,[])
        return sorted(seen)
    styles=style_registry(records)
    ids=load(state/'feature-ids.json',{})
    for f in legacy.get('features',[]): ids.setdefault(f['class'],f['id'])
    screens=[r for r in records.values() if r.get('class') and (r.get('title') or r.get('base','').endswith('Window') or 'Window' in r.get('base','')) and r.get('nodes')]
    all_features=[]
    for screen in screens:
        cls=screen['class'];ident=ids.setdefault(cls,'F-'+digest(cls)[:10].upper())
        code=records.get(screen['path']+'.vb',{})
        if not code and class_index.get(cls):code=records[class_index[cls][0]]
        old=next((f for f in legacy.get('features',[]) if f['class']==cls),{})
        purpose=purposes.get('PURPOSES',{}).get(ident,[]) if compatible else []
        rules=editorial.get('RULES',{}).get(ident[-3:],[]) if compatible else []
        example=editorial.get('EXAMPLES',{}).get(ident[-3:],'') if compatible else ''
        # Correct the prior illustrative text: the shared IME rule is byte based.
        example=example.replace('顧客名50文字の欄へ51文字を入力することはできない。','顧客名には画面上の文字数制限に加え、共通入力処理のShift_JISバイト数制限が適用される。')
        modelpaths=sorted(set(p for name in code.get('models',[]) for p in class_index.get(name,[])))
        items=fields(screen,code,[records[p] for p in modelpaths],styles)
        feature={'id':ident,'name':purpose[0] if purpose else screen['title'] or cls,'kind':'screen','group':old.get('group','未分類'),'purpose':purpose[1] if purpose else '業務上の目的は追加確認が必要です。','flow':purpose[2] if purpose else '', 'rules':rules,'example':example,'notes':editorial.get('NOTES',{}).get(ident[-3:],[]) if compatible else [], 'source':screen['path'],'code':code.get('path'),'source_class':cls,'base':screen['base'],'items':items,'events':[],'db':[],'models':modelpaths,'common_refs':[],'open_questions':[], 'source_hash':screen['sha256'],'snapshot_id':snapshot,'schema_version':'2.0','analysis_status':'review_required','profile_status':'source_hash_matched' if compatible else 'profile_not_available'}
        xhandlers={n['attrs'][k] for n in screen['nodes'] for k in ('Click','Loaded','SelectionChanged','Checked','TextChanged','Closing') if k in n['attrs']}
        code_methods=[mid for mid,m in method_index.items() if m['path']==code.get('path')]
        for mid in code_methods:
            m=method_index[mid]
            if not m['handles'] and m['name'] not in xhandlers:continue
            reachable=closure(mid)
            event={'id':ident+'-E'+digest(m['name'])[:8].upper(),'name':m['summary'] or 'イベント内容要確認','trigger':m['handles'] or '画面操作','source_name':m['name'],'path':m['path'],'line':m['line'],'end':m['end'],'methods':reachable,'db':[],'rules':[],'messages':[],'transitions':[],'reports':[],'unresolved':[]}
            for target in reachable:
                tm=method_index[target]
                event['db'] += [dict(x,path=tm['path'],method=tm['name']) for x in tm['db']]
                event['messages'] += [dict(x,path=tm['path']) for x in tm['messages']]
                event['transitions'] += tm['windows'];event['reports']+=tm['reports']
            event['db']=list({(x['object'],x['operation'],x['path'],x['line']):x for x in event['db']}.values())
            event['transitions']=sorted(set(event['transitions']));event['reports']=sorted(set(event['reports']))
            feature['events'].append(event)
        # Feature-level references include helpers not proven reachable, explicitly classified.
        reached={mid for e in feature['events'] for mid in e['methods']}
        for mid in sorted(set(code_methods)|reached):
            m=method_index[mid]
            feature['db'] += [dict(x,path=m['path'],method=m['name'],reachability='event' if mid in reached else 'source_candidate') for x in m['db']]
        feature['db']=list({(x['object'],x['operation'],x['path'],x['line']):x for x in feature['db']}.values())
        # Bind DB read results conservatively: multiple objects produce explicit candidates.
        mappings=[]
        for path in [code.get('path')]+modelpaths:
            for m in records.get(path,{}).get('methods',[]):
                objects=sorted({x['object'] for x in m['db'] if x['operation']=='R'})
                for mapping in m['mapping']:
                    mappings.append(dict(mapping,objects=objects,path=path))
        for item in items:
            if item['role']=='operation':continue
            for mp in mappings:
                if mp['property']==item['binding'] and len(mp['objects'])==1:
                    item['db'].append({'object':mp['objects'][0],'column':mp['column'],'path':mp['path'],'line':mp['line'],'certainty':'source_mapping'})
            item['db']=list({(x['object'],x['column']):x for x in item['db']}.values())
            if item['db']:item['db_status']='source_mapping'
        if any(e['reports'] for e in feature['events']):feature['kind']='mixed'
        if 'Process' in cls:feature['kind']='batch_dialog'
        feature['filename']='概要仕様書'+ident+'_'+safe_name(feature['name'])+'.md'
        all_features.append(feature)
    # Non-WPF projects still generate feature outlines, without claiming UI recovery.
    if not screens:
        for path,r in records.items():
            for m in r.get('methods',[]):
                if m.get('routes') or (r.get('language')=='Python' and not m['name'].startswith('_')):
                    key=path+':'+m['name'];fid=ids.setdefault(key,'F-'+digest(key)[:10].upper())
                    all_features.append({'id':fid,'name':m['summary'] or m['name'],'kind':'batch_or_api','group':'処理','purpose':m['summary'] or '業務目的要確認','flow':'','rules':[],'example':'','notes':[],'source':path,'code':path,'source_class':key,'base':'','items':[],'events':[],'db':m['db'],'models':[],'common_refs':[],'open_questions':['言語アダプターは入口の限定抽出のみ。詳細な入出力・イベント・DB意味解析は未完了。'],'snapshot_id':snapshot,'schema_version':'2.0','analysis_status':'review_required','filename':'概要仕様書'+fid+'_'+safe_name(m['name'])+'.md'})
    all_features.sort(key=lambda f:f['id'])
    save(state/'feature-ids.json',ids)
    metadata={'system_name':'未確認','customer':'未確認','author':'未確認（コミット作成者を製品作成者とはみなさない）','business':'未確認','languages':dict(Counter(r.get('language','unknown') for r in records.values())),'snapshot_id':snapshot,'input_tree':git(root,'rev-parse','HEAD:'+input_name),'source_commit':git(root,'log','-1','--format=%H','--',input_name),'source_files':len(inventory),'selected_files':sum(i['selected'] for i in inventory),'features':len(all_features),'physical_schema':'present' if any(r.get('tables') for r in records.values()) else 'not_found'}
    for path,r in records.items():
        if path.endswith('AssemblyInfo.vb'):
            text=adapters.decode((root/path).read_bytes())
            for attr,key in [('AssemblyTitle','system_name'),('AssemblyDescription','description'),('AssemblyCompany','author')]:
                m=re.search(attr+r'\("([^"]+)"\)',text)
                if m:metadata[key]=m.group(1)
            desc=metadata.get('description','')
            if '殿向け' in desc:metadata['customer']=desc.split('殿向け')[0];metadata['business']=desc.split('殿向け')[1]
    save(state/'system.json',metadata)
    save(state/'index.json',{'classes':dict(class_index),'methods':method_index,'calls':graph,'reverse_calls':dict(reverse)})
    stats['scan_seconds']=round(time.perf_counter()-started,6)
    data={'system':metadata,'features':all_features,'records':records,'methods':method_index,'styles':styles,'stats':stats,'inventory':inventory}
    for feature in all_features:save(state/'outlines'/(feature['id']+'.json'),feature)
    save(state/'catalog.json',{'system':metadata,'features':[{'id':f['id'],'name':f['name'],'filename':f['filename']} for f in all_features]})
    return data
