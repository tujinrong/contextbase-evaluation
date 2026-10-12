"""Refine source relationships, keeping deferred callbacks separate from calls.

Adapters yield syntax facts; this stage resolves references conservatively. It
never imports application code and never silently promotes a guess to schema.
"""
from __future__ import annotations
from collections import defaultdict
import re
from pathlib import Path
from .adapters import STRING, clean_vb, decode
from .core import bindings, resolve_style, save, digest

RESERVED={'WITH','FROM','WHERE','JOIN','SELECT','TABLE','SET','VALUES','COPY','TRUNCATE','ON','AS','INTO','GROUP','ORDER','BY','UNION','RETURNING'}


def split_args(text):
    parts=[];start=0;depth=0;quoted=False;i=0
    while i<len(text):
        c=text[i]
        if c=='"':
            if quoted and i+1<len(text) and text[i+1]=='"':i+=2;continue
            quoted=not quoted
        elif not quoted:
            if c in '({[':depth+=1
            elif c in ')}]':depth-=1
            elif c==',' and depth==0:parts.append(text[start:i].strip());start=i+1
        i+=1
    return parts+[text[start:].strip()]


def source_calls(method):
    calls=[];deferred=[]
    for stmt in method.get('statements',[]):
        text=STRING.sub('""',stmt['text'])
        deferred += re.findall(r'\bAddressOf\s+([\w.]+)',text,re.I)
        text=re.sub(r'\bAddressOf\s+[\w.]+','',text,flags=re.I)
        for m in re.finditer(r'(?<![\w.])((?:[A-Za-z_]\w*\.)?[A-Za-z_]\w*)\s*\(',text):
            name=m.group(1)
            if name not in calls:calls.append(name)
        for name in re.findall(r'\b(?:Not|If)\s+(_\w+)\s+Then\b',text,re.I):
            if name not in calls:calls.append(name)
    return calls,sorted(set(deferred))


def map_columns(method):
    """Resolve explicit SQL placeholders to properties in the same method only."""
    params=defaultdict(set)
    for st in method.get('statements',[]):
        for hit in re.finditer(r'\bSqlParameter\(\s*"(\w+)"\s*,\s*([^\n]+)',st['text'],re.I):
            # Stop at the next SqlParameter expression in a multiline initializer.
            value=hit.group(2).split('MyNpg.SqlParameter',1)[0]
            prop=re.search(r'\b(?:_?Model|order|mOrder|mChild)\.(\w+)',value,re.I)
            if prop:params[hit.group(1).casefold()].add(prop.group(1))
    mappings=[]
    for fragment in method.get('sql_fragments',[]):
        sql=fragment['sql']
        for hit in re.finditer(r'\bINSERT\s+INTO\s+([\w.]+)\s*\(([^)]+)\)\s*VALUES\s*\(([\s\S]*?)\)\s*;',sql,re.I):
            columns=split_args(hit.group(2));values=split_args(hit.group(3))
            for col,value in zip(columns,values):
                pm=re.search(r':(\w+)',value)
                if pm:
                    for prop in params.get(pm.group(1).casefold(),[]):mappings.append({'property':prop,'object':hit.group(1),'column':col.strip(),'direction':'write','line':method['line']})
        for hit in re.finditer(r'\bUPDATE\s+([\w.]+)\s+SET\s+([\s\S]*?)(?=\bWHERE\b|;|$)',sql,re.I):
            for pair in re.finditer(r'(\w+)\s*=\s*:(\w+)',hit.group(2)):
                for prop in params.get(pair.group(2).casefold(),[]):mappings.append({'property':prop,'object':hit.group(1),'column':pair.group(1),'direction':'write','line':method['line']})
    return mappings


def exact_caption(item,screen,models,styles):
    node=screen['nodes'][item['node']];a=node['attrs'];tag=node['tag'];values,chain=resolve_style(a,styles)
    own=a.get('Header') or a.get('Content') or ''
    if own and not own.startswith('{'):return own.replace('\n',' '),'caption'
    if tag.endswith('Button') and values.get('Content') and not values['Content'].startswith('{'):return values['Content'],'style_caption'
    # Prefer a same-row caption to potentially abbreviated model comments.
    try:
        xy=[float(x) for x in a.get('Margin','').split(',')[:2]]
        candidates=[]
        if len(xy)==2:
            for n in screen['nodes']:
                if n['parent']!=node['parent'] or n['tag'] not in {'Label','TextBlock'}:continue
                la=n['attrs'];text=la.get('Content',la.get('Text',''))
                try:lxy=[float(x) for x in la.get('Margin','').split(',')[:2]]
                except ValueError:continue
                if len(lxy)==2 and abs(xy[1]-lxy[1])<=2 and lxy[0]<xy[0] and text and not text.startswith('{') and re.search('[\u3040-\u9fff]',text):
                    candidates.append((lxy[0],text.replace('\n',' ')))
        if candidates:return max(candidates)[1],'static_label_position'
    except ValueError:pass
    prop=item.get('binding','')
    for r in models:
        for field in r.get('fields',[]):
            if field['name']==prop and field.get('summary'):return field['summary'],'model_comment'
    if item['role']=='internal' and prop:return '内部管理項目','internal'
    return item['name'],item['label_origin']


def refine(root:Path,data):
    records=data['records'];methods=data['methods'];classes=defaultdict(list)
    for p,r in records.items():
        for cls in r.get('classes',[]):classes[cls['name'].casefold()].append(p)
    by_name=defaultdict(list)
    for mid,m in methods.items():by_name[m['name'].casefold()].append(mid)
    graph={};deferred={}
    for mid,m in methods.items():
        calls,callbacks=source_calls(m);targets=[];r=records[m['path']]
        for call in calls:
            parts=call.rsplit('.',1);name=parts[-1]
            paths=[m['path']] if len(parts)==1 else classes.get(r.get('types',{}).get(parts[0],parts[0]).casefold(),[])
            for p in paths:
                targets += [x for x in by_name.get(name.casefold(),[]) if methods[x]['path']==p and x!=mid]
        graph[mid]=list(dict.fromkeys(targets));deferred[mid]=callbacks
        m['db']=[x for x in m.get('db',[]) if x['object'].upper() not in RESERVED]
        m['db_mappings']=map_columns(m)
        # Functions/sequences may appear as a scalar expression, not full SQL.
        literal_text=' '.join(x.group()[1:-1] for st in m.get('statements',[]) for x in STRING.finditer(st['text']))
        m['db_functions']=sorted(set(m.get('db_functions',[]))|set(re.findall(r'\bfunc_\w+\b',literal_text,re.I)))
        m['sequences']=sorted(set(m.get('sequences',[]))|set(re.findall(r"(?:setval|nextval|currval)\s*\(\s*'([^']+)'",literal_text,re.I)))
    def reachable(mid):
        seen=set();ordered=[];queue=[mid]
        while queue:
            cur=queue.pop(0)
            if cur in seen:continue
            seen.add(cur);ordered.append(cur);queue+=graph.get(cur,[])
        return ordered
    for f in data['features']:
        mids=[mid for mid,m in methods.items() if m['path']==f.get('code')]
        for event in f['events']:
            entry=next((mid for mid in mids if methods[mid]['name']==event['source_name']),None)
            if not entry:continue
            event['methods']=reachable(entry);event['deferred_callbacks']=sorted({c for mid in event['methods'] for c in deferred[mid]})
            event['db']=[];event['messages']=[];event['transitions']=[];event['reports']=[]
            for mid in event['methods']:
                m=methods[mid]
                event['db'] += [dict(x,path=m['path'],method=m['name']) for x in m['db']]
                event['messages'] += [dict(x,path=m['path']) for x in m['messages']]
                event['transitions'] += m['windows'];event['reports'] += m['reports']
            event['db']=list({(x['object'],x['operation'],x['path'],x['line']):x for x in event['db']}.values())
            event['transitions']=sorted(set(event['transitions']));event['reports']=sorted(set(event['reports']))
        reached={mid for e in f['events'] for mid in e['methods']}
        f['db']=[dict(x,path=methods[mid]['path'],method=methods[mid]['name'],reachability='event' if mid in reached else 'source_candidate') for mid in dict.fromkeys(mids+sorted(reached)) for x in methods[mid]['db']]
        f['db']=list({(x['object'],x['operation'],x['path'],x['line']):x for x in f['db']}.values())
        screen=records.get(f['source'],{});code=records.get(f.get('code'),{});models=[records[p] for p in f['models']]
        if not screen.get('nodes'):continue
        mappings=[dict(mp,path=methods[mid]['path']) for mid in mids for mp in methods[mid]['db_mappings']]
        for item in f['items']:
            name,origin=exact_caption(item,screen,models,data['styles']);item['name']=name;item['label_origin']=origin
            node=screen['nodes'][item['node']];attrs,chain=resolve_style(node['attrs'],data['styles'])
            item['style_handlers']=[h for st in chain for h in st['handlers']]
            if item['role']=='input' and item['tag'] in {'CheckBox','RadioButton','ComboBox','DatePicker','ListBox','TreeView'}:item['length']='対象外（選択肢・日付形式による）'
            if '郵便番号' in name:item['type']='数字列（先頭ゼロ保持）'
            if item['role']!='operation':
                for mp in mappings:
                    if item.get('binding')==mp['property']:item['db'].append({k:mp[k] for k in ['object','column','path','line','direction']})
                item['db']=list({(mp['object'],mp['column'],mp.get('direction','read')):mp for mp in item['db']}.values())
                if item['db']:item['db_status']='source_mapping'
                elif not item['binding'] and item['tag'] in {'CheckBox','RadioButton'}:item['db_status']='ui_state_only'
            if item['key']=='txtCustomerNm' and f['id']=='TKL-003':
                # This verified screen uses txt--imeon_len, NOT txt--imeon.
                f['example']='架空の顧客「見本図書館」、顧客ID「000123」、郵便番号「100」「0001」を使用する。ID手入力時は重複確認を行う。顧客名欄の上限は50文字であり、51文字は入力できない。この欄のStyleにはShift_JISバイト制限のイベント登録はない。'
        for item in f['items']:
            # Distinguish repeated range components using the actual binding.
            b=item.get('binding','')
            if b.endswith('From'):item['name']+='（開始）'
            elif b.endswith('To'):item['name']+='（終了）'
            elif b in {'Postalno1','SagawaPostalno1'}:item['name']+='（前3桁）'
            elif b in {'Postalno3','SagawaPostalno3'}:item['name']+='（後4桁）'
        f['layout_rows']=[{'order':i['order'],'name':i['name'],'role':i['role'],'line':i['line']} for i in f['items']]
        f['common_refs']=[{'key':i['key'],'handlers':i['style_handlers']} for i in f['items'] if i['style_handlers']]
        save(root/'.specgen-state/overview/outlines'/(f['id']+'.json'),f)
    reverse=defaultdict(list)
    for mid,children in graph.items():
        for child in children:reverse[child].append(mid)
    save(root/'.specgen-state/overview/reference-index.json',{'calls':graph,'reverse_calls':dict(reverse),'deferred_callbacks':deferred})
    data['call_graph']=graph;data['deferred_callbacks']=deferred
    return data


def preflight(root:Path,input_name='input'):
    """Cheap system survey before choosing source adapters; no source execution."""
    source=(root/input_name).resolve()
    if source==root or not source.is_relative_to(root):raise ValueError('invalid source')
    from collections import Counter
    exts=Counter();manifests=[];metadata={'customer':'未確認','author':'未確認','business':'未確認'}
    for path in sorted(source.rglob('*')):
        if path.is_symlink() or not path.is_file() or {'obj','bin','node_modules','packages','.git'}&set(path.relative_to(source).parts):continue
        exts[path.suffix.lower()]+=1
        if path.suffix.lower() in {'.vbproj','.csproj','.sln'} or path.name in {'pom.xml','package.json','pyproject.toml','go.mod','Cargo.toml'}:manifests.append(path.relative_to(root).as_posix())
        if path.name=='AssemblyInfo.vb':
            text=decode(path.read_bytes())
            for attr,key in [('AssemblyTitle','system_name'),('AssemblyDescription','description'),('AssemblyCompany','author')]:
                m=re.search(attr+r'\("([^"]+)"\)',text)
                if m:metadata[key]=m.group(1)
    desc=metadata.get('description','')
    if '殿向け' in desc:metadata['customer'],metadata['business']=desc.split('殿向け',1)
    plan={'metadata':metadata,'extensions':dict(exts),'manifests':manifests,'adapter_families':[v for suffix,v in {'.vb':'VB.NET','.xaml':'WPF/XAML','.py':'Python','.java':'Java','.cs':'C#','.ts':'TypeScript','.js':'JavaScript','.sql':'SQL'}.items() if suffix in exts],'scope':'静的調査。対応外形式と不足情報は別途報告する。'}
    save(root/'.specgen-state/overview/preflight.json',plan)
    return plan
