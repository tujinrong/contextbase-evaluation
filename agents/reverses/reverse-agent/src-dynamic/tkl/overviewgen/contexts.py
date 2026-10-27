"""WPF binding context and inherited layout safeguards.

Same property names in different models are not interchangeable. Ambiguous
relations are retained as candidates, not printed as confirmed item mappings.
"""
from __future__ import annotations
from collections import defaultdict
import re
from .core import resolve_style,save
from .dblineage import parenthesized
from .refine import split_args


def grid_owner(screen,item,code,records):
    node=screen['nodes'][item['node']];parent=node['parent'];grid=None
    while parent is not None:
        n=screen['nodes'][parent]
        if n['tag']=='DataGrid':grid=n['attrs'].get('x:Name',n['attrs'].get('Name'));break
        parent=n['parent']
    if not grid:return None
    variables=set();body='\n'.join(s['text'] for m in code.get('methods',[]) for s in m.get('statements',[]))
    for hit in re.finditer(r'\bBindGrid\s*\(',body):
        args,_=parenthesized(body,hit.end()-1)
        if args:
            values=split_args(args)
            if len(values)>=3 and values[0]==grid:variables.add(values[2])
    owners=set()
    for var in variables:
        for hit in re.finditer(re.escape(var)+r'\s*=\s*(?:New\s+ObservableCollection\s*\(Of\s+(\w+)|([\w]+)\.GetList\s*\()',body,re.I):
            name=hit.group(1) or hit.group(2)
            for path,r in records.items():
                if any(c['name'].casefold()==name.casefold() for c in r.get('classes',[])):owners.add(path)
    return next(iter(owners)) if len(owners)==1 else None


def filter_display_mappings(item,owner):
    if not item.get('is_column'):return
    candidates=item.get('db',[])
    # A display column never receives a form field's write/selection relation.
    certain=[x for x in candidates if owner and x['path']==owner and x.get('direction','read')=='read']
    other=[x for x in candidates if x not in certain]
    item['db']=certain
    item['db_candidates']=other
    item['binding_owner']=owner or '未確定'
    item['db_status']='source_mapping' if certain else 'unresolved'


def layout_order(screen,item,styles):
    chain=[];node=screen['nodes'][item['node']]
    def number(v):
        try:return float(v)
        except (ValueError,TypeError):return 0.0
    while node is not None:
        a,_=resolve_style(node['attrs'],styles)
        margin=a.get('Margin','0,0,0,0').split(',')
        x=number(a.get('Canvas.Left',margin[0]));y=number(a.get('Canvas.Top',margin[1] if len(margin)>1 else margin[0]))
        # Without rendering, right/bottom alignment has ordinal rather than pixel coordinates.
        if a.get('HorizontalAlignment')=='Right':x=1000000-x
        if a.get('VerticalAlignment')=='Bottom':y=1000000-y
        chain.insert(0,(number(a.get('Grid.Row',0)),number(a.get('Grid.Column',0)),y,x,node['line']))
        node=screen['nodes'][node['parent']] if node['parent'] is not None else None
    return chain


def apply(root,data):
    candidates=[]
    for f in data['features']:
        screen=data['records'].get(f['source'],{});code=data['records'].get(f.get('code'),{})
        if not screen.get('nodes'):continue
        for item in f['items']:
            if item.get('is_column'):
                owner=grid_owner(screen,item,code,data['records'])
                filter_display_mappings(item,owner)
                if item.get('db_candidates'):
                    candidates.append({'feature':f['id'],'item':item['key'],'name':item['name'],'binding_owner':item['binding_owner'],'candidates':item['db_candidates'],'reason':'同名プロパティの一致だけでは一覧の取得元を確定しない。'})
            item['display_order']=layout_order(screen,item,data['styles'])
        f['items'].sort(key=lambda item:(item['display_order'],item['node']))
        for i,item in enumerate(f['items'],1):item['order']=i
    save(root/'.specgen-state/overview/item-db-candidates.json',candidates)
    lines=['# 項目のDB対応・確認候補','','同名のプロパティを持つ別モデルの参照を、一覧表示の確定した取得元として扱わない。所属する一覧データを追跡できない対応は、本文のDB関連を未確定とし、以下に候補を保持する。','','| 機能ID | 項目 | 候補 | 所属データ |','| --- | --- | --- | --- |']
    for c in candidates:
        refs='、'.join(x['object']+'.'+x['column']+'（'+x.get('direction','read')+'）' for x in c['candidates'])
        lines.append('| '+' | '.join(str(v).replace('|','／') for v in [c['feature'],c['name'],refs,c['binding_owner']])+' |')
    save(root/'report/overview/項目DB対応確認.md','\n'.join(lines)+'\n')
    return data
