"""Keep component visibility/open/loading models out of business input fields."""
from .scan import VueReader,sha
from .render import cell,table

STATE_MODELS={'v-model:visible','v-model:open','v-model:loading'}


def separate(data):
    views={s['path']:s for s in data['screens']};total=0
    for path,record in data['records'].items():
        if not path.endswith('.vue'):continue
        parser=VueReader(data['texts'][path],path);states=[];exclude=set();values={}
        for index,node in enumerate(parser.nodes):
            attrs=node['attrs'];models={k.split('.',1)[0]:v for k,v in attrs.items() if k.startswith('v-model')}
            state={k:v for k,v in models.items() if k in STATE_MODELS}
            if not state:continue
            for name,value in state.items():
                states.append({'component':node['tag'],'property':name.split(':',1)[1],'value':value,'line':node['line']})
            # A select may bind both open state and a business value. Do not remove it.
            key='UI-'+sha(path+':'+str(index))[:10]
            business={k:v for k,v in models.items() if k not in STATE_MODELS}
            if not business:exclude.add(key)
            else:values[key]=next(iter(business.values()))
        cleaned=[i for i in record['items'] if i['id'] not in exclude]
        total+=len(record['items'])-len(cleaned)
        for number,item in enumerate(cleaned,1):
            item['order']=number
            value=values.get(item['id'])
            if value and value!=item.get('binding'):
                item['binding']=value;item['field']=str(value).split('.')[-1]
                item['db']=[]  # Do not keep a mapping inferred from the state property.
                item['required']='未明記（複数モデル結合の検証規則参照）'
        record['items']=cleaned;record['state_bindings']=states
        if path in views:
            views[path]['items']=cleaned;views[path]['state_bindings']=states
        inventory=next((r for r in data['inventory'] if r['path']==path),None)
        if inventory is not None:
            inventory['items']=len(cleaned);inventory['component_state_bindings']=len(states)
    data['stats']['state_bindings_excluded_from_business_items']=total
    return total


def describe(text,feature):
    rows=[[s['path'],state['component'],state['property'],state['value'],state['line']]
          for s in feature['screens'] for state in s.get('state_bindings',[])]
    if not rows:return text
    note='\n### 1.補足 子画面・共通部品の状態受渡し\n\n'
    note+='以下は表示・開閉・処理中の状態を部品へ渡す結合であり、利用者の業務入力項目数には含めない。値を直接入力する欄としてHTMLに表示しない。子画面自身の入力項目は、その画面・部品の項目一覧を参照する。\n\n'
    note+=table(['画面・部品原本','部品','状態属性','保持値の識別子','行'],rows)+'\n'
    return text.replace('## 2. 項目一覧',note+'## 2. 項目一覧',1)
