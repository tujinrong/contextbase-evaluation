"""Language-independent external specifications. Adapters supply reviewed contracts."""
from __future__ import annotations
import html,re
from typing import Any

def esc(value:Any)->str:return html.escape(str(value),quote=True)

def mdtable(headers,rows):
    def cell(v):return html.escape(str(v),quote=False).replace('|','&#124;').replace('\n','<br>')
    return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join('| '+' | '.join(cell(v) for v in row)+' |\n' for row in rows)

CSS='''
.screen-layout .ext-screen{font-family:"Yu Gothic UI",Meiryo,sans-serif;color:#262626;background:#fff;font-size:14px;line-height:1.55;box-sizing:border-box}
.screen-layout .ext-screen *{box-sizing:border-box}
.screen-layout .ext-screen h4{font-size:16px;font-weight:600;margin:12px 0 10px;padding-left:8px;border-left:3px solid #1677ff;line-height:26px}
.screen-layout .ext-row{display:flex;flex-wrap:wrap;margin-left:-8px;margin-right:-8px;align-items:flex-start}
.screen-layout .ext-col{flex-shrink:0;padding:0 8px;min-width:0}
.screen-layout .ext-field{display:flex;align-items:center;min-height:32px;margin:8px 0 12px;width:100%;gap:8px}
.screen-layout .ext-field>label{width:120px;flex:0 0 120px;text-align:right;white-space:nowrap;font-size:14px;color:#262626}
.screen-layout .ext-field>label.ext-empty{display:none}
.screen-layout .ext-control{flex:1;min-width:0;display:flex;align-items:center;gap:10px}
.screen-layout .ext-control input:not([type=checkbox]):not([type=radio]),.screen-layout .ext-control select,.screen-layout .ext-control textarea{width:100%;min-width:0;height:32px;border:1px solid #d9d9d9;border-radius:6px;padding:4px 10px;color:#262626;background:white;font:inherit;line-height:22px}
.screen-layout .ext-control textarea{height:auto;resize:none}
.screen-layout .ext-control select{appearance:auto}
.screen-layout .ext-required{color:#e14040;margin-right:4px}
.screen-layout .ext-checkbox{display:flex;align-items:center;white-space:nowrap;gap:6px;font-size:13px;min-height:40px;padding-top:6px}
.screen-layout .ext-checkbox input{accent-color:#1677ff;width:14px;height:14px;margin:0}
.screen-layout .ext-button{border:1px solid #d9d9d9;border-radius:6px;background:white;padding:4px 14px;min-height:32px;white-space:nowrap;font:inherit;color:#262626;line-height:22px}
.screen-layout .ext-button.primary{background:#1677ff;border-color:#1677ff;color:white}
.screen-layout .ext-button.danger{background:#ff4d4f;border-color:#ff4d4f;color:white}
.screen-layout .ext-button:disabled{opacity:.5}
.screen-layout .ext-toolbar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:10px 0}
.screen-layout .ext-toolbar>.ext-field{width:200px;flex:0 0 200px;margin:0}
.screen-layout .ext-display{display:block;min-height:26px;background:#f5f5f5;border-radius:4px;padding:2px 8px;color:#595959;min-width:55px}
.screen-layout .ext-grid-scroll{overflow:auto;width:100%;border:1px solid #e8e8e8;margin-top:12px}
.screen-layout .ext-grid{border-collapse:collapse;table-layout:fixed;font-size:13px;line-height:20px;margin:0}
.screen-layout .ext-grid th,.screen-layout .ext-grid td{border:1px solid #e8e8e8;padding:8px 10px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;height:38px}
.screen-layout .ext-grid th{background:#fafafa;color:#262626;text-align:center;font-weight:600}
.screen-layout .ext-grid th[data-fixed=left]{position:sticky;z-index:1}
.screen-layout .ext-tabs{display:flex;border-bottom:1px solid #d9d9d9;gap:3px;margin:0 0 12px;padding:10px 0 0}
.screen-layout .ext-tab{padding:8px 16px;min-width:80px;text-align:center;background:#fafafa;border:1px solid #d9d9d9;border-radius:6px 6px 0 0}
.screen-layout .ext-tab.active{color:#1677ff;background:white;border-bottom-color:white}
.screen-layout .ext-modal-head{font-size:20px;font-weight:bold;padding:16px 24px;border-bottom:1px solid #eee}
.screen-layout .ext-modal-body{padding:0 48px;height:750px;overflow-y:auto;overflow-x:hidden}
.screen-layout .ext-footer{position:relative;display:flex;align-items:center;justify-content:center;gap:8px;height:60px;box-shadow:0 4px 16px rgba(0,78,201,.1);border-top:1px solid #eee}
.screen-layout .ext-footer .ext-delete{position:absolute;right:50px}
.screen-layout .ext-note{padding:10px 12px;font-size:12px;background:#f6f9ff;color:#536879}
.screen-layout .ext-dynamic{padding:14px;border:1px dashed #8ca1b6;margin:10px 0;color:#536879}
'''

def layout_node(n:dict,prefix:str='')->str:
    kind=n['kind'];children=lambda:''.join(layout_node(c,prefix) for c in n.get('children',[]))
    if kind=='row':
        gap=float(n.get('gap',16))/2
        return f'<div class="ext-row" data-row="{esc(n.get("id",""))}" style="margin-left:-{gap:g}px;margin-right:-{gap:g}px">'+children()+'</div>'
    if kind=='col':
        span=float(n.get('span',24))
        if not 0<span<=24:raise ValueError('Invalid column span')
        return f'<div class="ext-col" data-span="{span:g}" style="width:{span/24*100:.8f}%">'+children()+'</div>'
    if kind=='group':return '<section class="ext-group"><h4>'+esc(n['label'])+'</h4>'+children()+'</section>'
    if kind=='toolbar':return '<div class="ext-toolbar">'+children()+'</div>'
    if kind=='stack':return children()
    if kind=='note':return '<div class="ext-dynamic">'+esc(n['text'])+'</div>'
    if kind=='text':return '<span>'+esc(n['text'])+'</span>'
    if kind=='button':return '<button type="button" class="ext-button '+esc(n.get('style',''))+'"'+(' disabled' if n.get('disabled') else ' aria-disabled="true"')+'>'+esc(n['label'])+'</button>'
    if kind=='table':
        widths=[int(c['width']) for c in n['columns']];left=0;heads=[]
        for c,w in zip(n['columns'],widths):
            fixed=''
            if c.get('fixed')=='left':fixed=f' data-fixed="left" style="left:{left}px"';left+=w
            heads.append('<th'+fixed+'>'+esc(c['label'])+'</th>')
        cols=''.join(f'<col style="width:{w}px">' for w in widths)
        return '<div class="ext-grid-scroll"><table class="ext-grid" style="width:'+str(sum(widths))+'px"><colgroup>'+cols+'</colgroup><thead><tr>'+''.join(heads)+'</tr></thead><tbody><tr><td colspan="'+str(len(widths))+'" style="height:150px;text-align:center;color:#888">データなし（配置確認用）</td></tr></tbody></table></div>'
    if kind=='field':
        ident=prefix+n['id'];label=n['label'];typ=n.get('type','text');state=n.get('mode','input')
        attr=' data-field="'+esc(n['id'])+'" data-mode="'+state+'"'
        required='<span class="ext-required">*</span>' if n.get('required') and state=='input' else ''
        labelhtml='<label for="'+esc(ident)+'"'+(' class="ext-empty"' if not label else '')+'>'+required+esc(label)+'</label>'
        lim=' maxlength="'+str(int(n['max_length']))+'"' if str(n.get('max_length','')).isdigit() else ''
        if state=='display':control='<span id="'+esc(ident)+'" class="ext-display">'+esc(n.get('value') or '―')+'</span>'
        elif typ=='checkbox':return '<label class="ext-checkbox"'+attr+'><input type="checkbox" id="'+esc(ident)+'"'+(' disabled' if state=='disabled' else '')+'>'+esc(label)+'</label>'
        elif typ=='select':control='<select id="'+esc(ident)+'" aria-label="'+esc(label or '選択項目')+'"><option>'+esc(n.get('value') or '選択してください')+'</option></select>'
        elif typ=='radio':control='<span id="'+esc(ident)+'">○ 選択肢（区分定義）</span>'
        elif typ=='button':control=layout_node({'kind':'button','label':label,'style':n.get('style','')});labelhtml=''
        elif typ=='textarea':control='<textarea id="'+esc(ident)+'" rows="'+str(int(n.get('rows',2)))+'"'+lim+'></textarea>'
        else:control='<input id="'+esc(ident)+'" type="text"'+lim+' placeholder="'+esc(n.get('placeholder',''))+'" value="'+esc(n.get('value',''))+'" aria-label="'+esc(label or n.get('aria_label','入力欄'))+'">'
        return '<div class="ext-field"'+attr+'>'+labelhtml+'<div class="ext-control">'+control+'</div></div>'
    raise ValueError('Unsupported language-neutral layout node: '+kind)

def layout_screen(s:dict)->str:
    prefix=s['id']+'-';content=layout_node(s['tree'],prefix)
    if s.get('modal',False):
        tabs=''.join('<span class="ext-tab'+(' active' if t==s['active_tab'] else '')+'">'+esc(t)+'</span>' for t in s['tabs'])
        footer=''.join(layout_node(b,prefix) for b in s['buttons'])
        content='<div class="ext-modal-head">'+esc(s['title'])+'</div><div class="ext-modal-body"><div class="ext-tabs">'+tabs+'</div>'+content+'</div><div class="ext-footer">'+footer+('</div>' if not s.get('delete') else '<div class="ext-delete">'+layout_node(s['delete'],prefix)+'</div></div>')
    else:content='<div style="padding:20px 24px">'+content+'</div>'
    return '<div class="screen-layout" data-screen="'+esc(s['id'])+'"><style>'+CSS+'</style><div class="ext-screen" style="width:'+str(int(s['width']))+'px" data-width="'+str(int(s['width']))+'">'+content+'</div></div>'

def render(spec:dict)->str:
    validate_contract(spec)
    out=['# '+spec['name']+' — 基本設計書（外部仕様）','',spec['purpose'],'','## 1. システム概要','','### 1.1 対象と入出力','',spec['scope'],'',mdtable(['入力','処理の目的','出力'],spec['io']),spec['context_diagram'],'','### 1.2 画面レイアウト','','原本の配置定義に合わせた静的な確認用画面です。値は説明用で、業務操作は実行しません。狭い表示領域では画面枠内を横スクロールしてください。フォント・製品固有の装飾や稼働画面とのピクセル単位の一致は未確認です。']
    for i,s in enumerate(spec['screens']):
        label='配置'+str(i+1)+'：'+s['caption'];out+=['','<details'+(' open' if i<2 else '')+'><summary>'+esc(label)+'</summary>','','<!-- docsite:screen-layout begin -->\n'+layout_screen(s)+'\n<!-- docsite:screen-layout end -->','','</details>','',s.get('note','')]
    out+=['','### 1.3 画面状態と遷移','',mdtable(['状態','表示・編集できる内容','操作'],spec['states']),spec['transition_diagram'],'','## 2. 項目一覧','',spec.get('item_guidance','入力・表示・操作を区別し、入力部品の上限と業務上有効な値を分けます。固定項目と追加設定で増える項目は混在集計しません。')]
    count=0
    for group in spec['item_groups']:
        rows=[]
        for item in group['items']:
            count+=1;rows.append([item['number'],item['label'],item['type'],item['data'],item['required'],item['length'],item['description']])
        out+=['','### '+group['title'],'',mdtable(['No.','項目名','タイプ','DB関連（論理名）','必須','長さ・範囲','概要説明'],rows)]
    out+=['',f'**固定項目の定義数：{count}項目**。同じ値を表示・編集する状態違いは別件に数えません。',spec['dynamic_items'],'','## 3. イベント仕様','','次の順番は利用者から見える業務上の処理順です。入力検証、確認、データの反映、通知と遷移を区別します。内部の呼出し順や実装方式は記載しません。']
    for e in spec['events']:
        out+=['','### '+e['id']+' '+e['name'],'',mdtable(['契機・前提','入力','出力・反映先'],[[e['trigger'],e['input'],e['output']]]),'']
        out += [f'{i}. {step}' for i,step in enumerate(e['steps'],1)]
        out+=['','**取消・異常時**：'+e['failure'],'','**データ例**：'+e['example']]
        if e.get('diagram'):out+=['',e['diagram']]
    out+=['','## 4. 補足説明','','### 4.1 データ間の関係','',mdtable(['データ','関連・用途','反映される操作'],spec['relations']),spec['data_diagram'],'','### 4.2 共通仕様と適用範囲','',spec['common'],'','### 4.3 確認が必要な業務上の差異','',mdtable(['ID','確認事項','影響'],spec['findings']),'',spec.get('evidence_note','設計根拠と内部実装の照合情報は、対象別の検証資料に分離します。')]
    return '\n'.join(out)+'\n'

def validate_contract(spec:dict)->None:
    for key in ['name','purpose','scope','screens','item_groups','events','relations','findings']:
        if not spec.get(key):raise ValueError('Missing external specification section: '+key)
    nums=[i['number'] for g in spec['item_groups'] for i in g['items']]
    if len(nums)!=len(set(nums)):raise ValueError('Duplicate item numbers')
    for e in spec['events']:
        for key in ['input','output','trigger','steps','failure','example']:
            if not e.get(key):raise ValueError('Event contract missing '+key)
        if len(e['steps'])<2:raise ValueError('Event sequence is missing')
    prose=' '.join([spec['purpose'],spec['scope']]+[str(i[k]) for g in spec['item_groups'] for i in g['items'] for k in ['label','type','data','description']]+[str(e[k]) for e in spec['events'] for k in ['name','input','output','failure','example']]+[x for e in spec['events'] for x in e['steps']])
    forbidden=re.compile(r'(?<![A-Za-z0-9_])(?:SELECT|INSERT|UPDATE|DELETE|DTO|Nolock|DbContext|v-model|formData|searchParams|SaveRequest)(?![A-Za-z0-9_])|\b\w+\.(?:cs|vue|ts)\b')
    if forbidden.search(prose):raise ValueError('Implementation detail in external specification: '+forbidden.search(prose)[0])
