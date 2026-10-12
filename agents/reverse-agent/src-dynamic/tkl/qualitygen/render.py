"""Customer-facing specification refinement from language-neutral facts."""
from __future__ import annotations
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote
import html, json, re
from overviewgen.core import resolve_style
from overviewgen.customer import render as baseline_render, expression, words, OPS
from overviewgen.publish import table, link, mermaid, event_name, COMMON, SYSTEM
from .profile import COMMON_RULES, PILOT_DETAILS, PILOT_CONTRACT


def name_text(text, registry):
    """Logical names in prose, with physical identifiers retained in the DB dictionary."""
    for physical,obj in sorted(registry['objects'].items(),key=lambda x:-len(x[0])):
        if obj['logical_name'].startswith('用途名要確認'):continue
        for col,d in sorted(obj['columns'].items(),key=lambda x:-len(x[0])):
            text=text.replace(physical+'.'+col, obj['logical_name']+'・'+d['logical_name'])
        text=re.sub(r'(?<![\w])'+re.escape(physical)+r'(?![\w])',lambda _:obj['logical_name'],text)
    return text


def captions(f,data):
    preferred={}
    for path in f.get('models',[]):
        for field in data['records'].get(path,{}).get('fields',[]):
            if field.get('summary'):preferred.setdefault(field['name'],field['summary'])
    for i in f['items']:
        b=i.get('binding','')
        if i.get('label_origin')=='unresolved' and b in preferred:
            i['name']=preferred[b];i['label_origin']='model_comment'
        if b in {'CustomerNm','SendNm'} and i['name'] in {'顧客ID','送付先'}:
            i['name']={'CustomerNm':'顧客名','SendNm':'送付先顧客名'}[b];i['label_origin']='value_semantics'
        if f['id']=='TKL-001' and i['key'] in {'txtUserId','pwd'}:
            i['name']={'txtUserId':'利用者ID','pwd':'パスワード'}[i['key']];i['label_origin']='login_semantics'
        if re.fullmatch('Biko[1-5]',b) and '/CustomerHistory' in f.get('code',''):
            i['name']='対応履歴'+b[-1];i['label_origin']='numbered_history'


def layout(f,data):
    """Static HTML, no network resources or executable application logic."""
    esc=lambda x:html.escape(str(x),quote=True)
    groups=defaultdict(list);screen=data['records'].get(f['source'],{});nodes=screen.get('nodes',[])
    for i in f['items']:
        node=nodes[i['node']] if nodes else {'parent':None,'attrs':{}}
        group='基本情報';p=node.get('parent');chain=[]
        while p is not None:
            n=nodes[p];a=n['attrs'];chain.insert(0,a.get('Grid.Row','0'))
            if a.get('Header'):group=str(a['Header']);break
            p=n['parent']
        if group=='基本情報':group='基本情報・入力内容' if not chain or chain[-1]=='0' else '明細・確認内容'
        if i['is_column']:group='一覧の列定義'
        if i['role']=='internal':group='内部・初期非表示項目'
        groups[group].append(i)
    body=[]
    for group,items in groups.items():
        body.append('<section><h2>'+esc(group)+'</h2><div class="fields">')
        for i in items:
            key=esc(i['key']);label=esc(str(i['order'])+'. '+i['name']);role=i['role'];disabled=' disabled' if role in {'display','internal'} else ''
            tag=i['tag']
            if role=='operation':control='<button type="button" disabled>'+esc(i['name'])+'</button>'
            elif tag in {'ComboBox','ListBox','TreeView'}:control='<select'+disabled+'><option>選択候補（実データなし）</option></select>'
            elif tag in {'CheckBox','RadioButton'}:control='<input type="'+('radio' if tag=='RadioButton' else 'checkbox')+'"'+disabled+'>'
            elif tag=='DatePicker':control='<input type="date"'+disabled+'>'
            else:control='<input type="'+('password' if tag=='PasswordBox' else 'text')+'" placeholder="'+esc(i['name'])+'"'+(' readonly' if role in {'display','internal'} else '')+'>'
            control=control.replace('<input ','<input id="'+key+'" ',1).replace('<select','<select id="'+key+'"',1).replace('<button ','<button id="'+key+'" ',1)
            node=nodes[i['node']] if nodes else {'attrs':{}}
            body.append('<div class="field '+role+'" data-item="'+key+'" data-source-line="'+str(i['line'])+'" data-role="'+role+'" data-source-margin="'+esc(node['attrs'].get('Margin',''))+'"><label for="'+key+'">'+label+'</label>'+control+'<small>'+esc({'input':'入力・選択','display':'表示専用','operation':'操作','internal':'内部・非表示'}[role])+' ／ '+esc(i['length'])+'</small></div>')
        body.append('</div></section>')
    title=esc(f['id']+' '+f['name'])
    return '''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'''+title+'''</title><style>
body{font-family:system-ui,sans-serif;margin:0;background:#f1f5f9;color:#17293a}main{max-width:1150px;margin:24px auto;padding:24px;background:white;border-radius:12px}h1{margin:0 0 12px;font-size:26px}h2{font-size:16px;border-bottom:2px solid #dce7ef;padding:10px 0}p{line-height:1.8}.notice{padding:12px;background:#fff6df;border-left:4px solid #bd7b17}.fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px 24px}.field{display:grid;grid-template-columns:150px minmax(0,1fr);align-items:center;gap:4px 10px;padding:7px;border:1px solid #dbe4ec;border-radius:5px}label{font-size:13px;font-weight:600}input,select,button{min-width:0;box-sizing:border-box;padding:8px;font:inherit;width:100%;border:1px solid #acbcc9;border-radius:4px}input[type=checkbox],input[type=radio]{width:auto;justify-self:start}small{grid-column:2;font-size:11px;color:#536879}input[readonly]{background:#edf2f5}button{background:#dceaf6;color:#183a57}button:disabled{opacity:1}.internal{background:#f6f0e8}.display{background:#f8fafc}@media(max-width:750px){main{margin:0}.fields{grid-template-columns:1fr}}@media print{main{margin:0}section{break-inside:avoid}}
</style></head><body><main><h1>'''+title+'''</h1><p class="notice">原本の項目・領域・順番を参照した仕様確認用HTMLです。見やすさのため2列に再配置しており、WPFの寸法、動的表示、フォーカス順の完全再現ではありません。値は実データではなく、ボタンは業務処理を実行しません。</p><p>個別項目 '''+str(len(f['items']))+'''件。内部項目を含む定義照合用です。</p>'''+''.join(body)+'''</main></body></html>'''


def readable(s,f,data):
    glossary=words(f,data)
    glossary.update({'IsEnabled':'操作可能','IsReadOnly':'表示専用','Visibility':'表示状態','Visible':'表示','Hidden':'非表示','Collapsed':'領域非表示','Orders':'明細一覧','IsCloseConfirm':'終了確認','_isUpdated':'確定済み','SelectedDate':'指定日付','CustomerKbn':'顧客区分','DeliveryKbn':'配送区分','SeikyuTanka':'請求単価','FixedPrice':'定価','ReducePercent':'値引率','Discounts':'値引額','SendCopies':'数量','SeikyuPrice':'請求金額','SagawaBulkUpdate':'送付先一括更新'})
    return expression(s,glossary)


def method_steps(mid,f,data,reg):
    m=data['methods'][mid];out=[]
    for st in m.get('statements',[]):
        raw=st['text'].strip();translated=None
        hit=re.match(r'(?:_Model|Model)\.(\w+)\s*=\s*(.+)',raw)
        if hit:
            translated=readable(hit.group(1)+' ← '+hit.group(2),f,data)
            if translated:translated='保持情報を更新する：'+translated+'。この設定は当該処理を通る場合に適用する。'
        hit=re.match(r'(?:If|ElseIf)\s+(.+?)\s+Then(?:\s+(.+))?',raw,re.I)
        if hit:
            cond=readable(hit.group(1),f,data)
            tail=hit.group(2) or ''
            if cond:translated='「'+cond+'」を判定する。'+('成立時は後続の処理へ進まず、この処理を終了する。' if re.search('Exit Sub|Return False|Return True',tail) else '成立側と非成立側を区別し、後続の設定・参照・更新を分岐する。')
        if translated and translated not in out:out.append(translated)
    grouped=defaultdict(list)
    for col in m.get('columns',[]):grouped[col['object']].append(col['column'])
    for obj,op in dict.fromkeys((r['object'],r['operation']) for r in m.get('db',[])):
        title=reg['objects'].get(obj,{}).get('logical_name',obj)
        cols=[reg['objects'].get(obj,{}).get('columns',{}).get(c,{}).get('logical_name',c) for c in dict.fromkeys(grouped[obj])]
        s=title+'を'+OPS.get(op,op)+'する。'
        if cols:s+='対象項目は'+ '、'.join(cols)+'。'
        if op in {'C','U','D'}:s+='この処理で作成する変更要求と、共通処理による最終確定を区別する。対象条件の未解決部分は根拠台帳に残す。'
        else:s+='取得した情報を後続の判断・表示・計算に渡す。複数の参照先がある場合も物理的な外部キーの存在を意味しない。'
        out.append(s)
    for c in m.get('comments',[]):
        s=c['text']
        if re.search('[ぁ-龯]',s) and not re.search(r'AppendLine|^\d{4}/|START|END|JBD|^[［\[]',s) and s not in {'検証','入力チェック','確認','パラメータ','後処理','SQL'}:
            s=re.sub('セット$','を設定する',s).replace('グリッド','一覧').replace('モデル','保持情報')
            if s not in out:out.append(s.rstrip('。')+'。')
    return out


def feature(f,data,reg):
    old,audit=baseline_render(f,data)
    text=old
    htmlname='画面レイアウト'+f['id']+'_'+f['name']+'.html'
    text=text.replace('### 1.2 レイアウト','### 1.2 レイアウト\n\n'+link(htmlname,'HTML画面レイアウトを開く')+'\n\nHTMLは個別項目の確認用であり、実画面と同一寸法の再現ではありません。共通部品、画面状態ごとの可否、入力順は共通仕様と併せて確認します。\n')
    entries={c['method']:c for c in reg['common']};sections=[];bullet_chars=0
    for n,e in enumerate(f['events'],1):
        rows=[]
        if f['id']=='TKL-011' and e['source_name'] in PILOT_DETAILS:rows.append(PILOT_DETAILS[e['source_name']])
        mids=[mid for mid in e['methods'] if mid in data['methods'] and data['methods'][mid]['path']==f.get('code')]
        mids.sort(key=lambda mid:data['methods'][mid]['line'])
        for mid in mids:
            m=data['methods'][mid];steps=method_steps(mid,f,data,reg)
            if steps:rows.append('【'+event_name(m.get('summary') or e['name'])+'】'+' '.join(steps))
        common=list(dict.fromkeys(mid for mid in e['methods'] if mid in entries))
        if common:
            rows.append('適用する共通処理は'+ '、'.join(entries[mid]['id']+'（'+event_name(entries[mid]['name'])+'）' for mid in common)+'。各処理の入力、返却結果、DB参照、副作用は共通関数仕様の同じIDを参照する。呼出し候補を全機能共通の必須処理とはみなさない。')
        if e.get('deferred_callbacks'):rows.append('後続操作の登録があるため、初期化だけでデータを確定しない。登録された明細追加・修正・削除等の実際の契機と共通UIの振分けは、共通UI仕様で照合する。')
        sections+=['### 3.補足'+str(n)+' '+event_name(e['name'])+'の処理内訳（'+e['id']+'）','','以下は呼出関係で対応する処理の責務を展開したものです。並びは原本内の定義順で、条件分岐を含む実行順序そのものではありません。']
        sections+=['- '+r for r in rows]
        sections+=['','**検証する観点**：上記の入力・設定・データ操作と、元のイベント節の成功・取消・通知が整合することを確認する。未解決の分岐は説明文を増やして確定扱いにせず、実装可能性の保留条件として残す。','']
        bullet_chars+=sum(len(r) for r in rows)
    insert='\n'.join(sections)+'\n'
    text=text.replace('## 4. 補足説明',insert+'\n## 4. 補足説明')
    text+='\n共通関数の入力・出力・副作用：'+link('概要仕様書COM-002_共通関数仕様.md','共通関数仕様')+'。共通UIと開発時の取り決め：'+link('概要仕様書COM-003_共通UI仕様.md','共通UI仕様')+' ／ '+link('開発規約.md','開発規約')+'。\n'
    text=name_text(text,reg)
    for i in f['items']:text+='\n<!-- item:'+i['key']+' order:'+str(i['order'])+' role:'+i['role']+' -->'
    if f['id']=='TKL-011':
        text+='\n\n<details><summary>Pilotの機械可読な受入契約（業務ルールと同内容）</summary>\n\n```json\n'+json.dumps(PILOT_CONTRACT,ensure_ascii=False,indent=2)+'\n```\n</details>\n'
    baseline_bullets=sum(len(x) for x in old.split('## 3. イベント仕様',1)[-1].split('## 4. 補足説明',1)[0].splitlines() if x.startswith('- '))
    return text,layout(f,data),{'id':f['id'],'before_characters':len(old),'after_characters':len(text),'event_bullets_before':baseline_bullets,'event_bullets_added':bullet_chars,'event_bullet_ratio':round((baseline_bullets+bullet_chars)/max(1,baseline_bullets),2),'items':len(f['items']),'events':len(f['events']),'html':htmlname}


def shared(data,reg):
    features={f['id']:f['name'] for f in data['features']};bycommon={c['method']:c['id'] for c in reg['common']}
    common=['# 共通仕様 — システム全体の業務規則','','## 1. システム概要','','顧客、月刊誌契約、特別出版注文、請求計上・発行、入金、帳票、運用保守を横断する仕様をここに集約する。個別画面ごとに同じ規則を複写せず、適用する共通IDで参照する。','',table(['対象範囲','抽出数'],list(reg['scope'].items())),'','## 2. 共通情報と参照先','','共通関数の利用側、戻り値、状態変更は別冊COM-002、表示部品と入力制御はCOM-003、データの論理名と使用箇所はDB定義書、例外・取引境界・命名は開発規約を参照する。','', '## 3. 共通業務仕様','']
    for cid,title,body,source in COMMON_RULES:
        paths=[p for p in data['records'] if Path(p).name==source]
        if not paths:continue
        common+=['### '+cid+' '+title,'',body,'','根拠：'+' ／ '.join(link('../'+p,Path(p).name) for p in paths),'']
    common+=['## 4. 適用上の注意','','共通規則は実装の観測結果であり、推奨する新規設計と同一ではない。既存の例外処理の不足、未取得のDB制約、未承認の論理名を合意済みとしない。']
    if data['system'].get('system_name')=='Tokyo Librarian':
        common+=['','<details><summary>共通業務の機械可読契約</summary>','','```json',json.dumps({'contract_scope':'common_business','money':PILOT_CONTRACT['money'],'price_lookup':PILOT_CONTRACT['price_lookup']},ensure_ascii=False,indent=2),'```','</details>']
    funcs=['# 共通関数仕様','','## 1. 全体の適用範囲','','プロジェクト全体の呼出・逆参照を横断して、複数機能から使われる処理と共通実装領域を抽出した。未使用の宣言も利用者0件と表示し、機能に無条件で割り当てない。','', '## 2. 共通関数一覧','',table(['共通ID','責務','利用機能数'],[[c['id'],event_name(c['name']),len(c['feature_ids'])] for c in reg['common']]),'','## 3. 共通関数の入出力と処理','']
    for c in reg['common']:
        m=data['methods'][c['method']];owners=[features.get(x,x) for x in c['feature_ids']]
        params=[]
        match=re.search(r'\((.*)\)',m.get('signature',''))
        if match:
            for param in re.findall(r'(\w+)\s+As\s+([\w?.]+)',match.group(1)):
                params.append(param[0])
        ret='処理結果の返却あり（正常・未取得・異常の区別は処理本文で確認）' if 'Function' in m.get('signature','') else '直接の返却値なし。引数・画面状態・DB等の変更に注意する'
        funcs+=['### '+c['id']+' '+event_name(c['name']),'','**利用範囲**：'+('、'.join(owners) or '呼出元の静的対応なし／共通宣言として保持')+'。','', '**入出力**：'+ret+'。' + ('入力・受渡し識別子：'+ '、'.join(params) +'。' if params else '引数宣言なし、または複数行宣言の追加確認が必要。'),'']
        use=next((f for f in data['features'] if f['id'] in c['feature_ids']),{'items':[],'models':[],'code':m['path']})
        steps=method_steps(c['method'],use,data,reg)
        funcs += ['- '+s for s in steps] if steps else ['- '+event_name(c['name'])+'を担当する。条件・値の確定に必要な業務説明は未完了であり、再実装の判断を保留する。']
        if m.get('db'):funcs+=['','**データの副作用**：'+'、'.join(reg['objects'].get(x['object'],{}).get('logical_name',x['object'])+'を'+OPS.get(x['operation'],x['operation']) for x in m['db'])+'。']
        funcs+=['','**参照関係**：'+'、'.join(bycommon.get(x,'個別処理') for x in reg['calls'].get(c['method'],[]))+'。','根拠：'+link('../'+m['path']+'#L'+str(m['line'])+'-L'+str(m['end']),c['id']+' の原本'),'']
    funcs+=['## 4. 補足','','処理名だけで同名関数を統合しない。出典の位置と呼出関係が異なるオーバーロードは別の共通IDで保持する。型や例外の詳細な契約が欠ける関数は、一覧化できたことだけで再実装可能とは判定しない。']
    if data['system'].get('system_name')=='Tokyo Librarian':
        funcs+=['','<details><summary>Pilotで利用する共通関数の契約</summary>','','```json',json.dumps({'contract_scope':'shared_functions','functions':['discount','unit_price','price_lookup','transaction_contract'],'failure_state':'unchanged','live_database_tested':False},ensure_ascii=False,indent=2),'```','</details>']
    ui=['# 共通UI仕様','','## 1. 共通部品の範囲','','部品の継承、表示上書き、イベント登録を全画面から照合する。入力検証や画面終了とDB更新の混同を避け、各画面の適用先を明示する。','','## 2. 部品一覧','']
    for key,style in sorted(data['styles'].items()):
        uses=[(f,i) for f in data['features'] for i in f['items'] if any(s['path']==style['path'] and s['line']==style['line'] for s in i.get('style_refs',[]))]
        if not uses:continue
        attrs='、'.join(k+'='+str(v) for k,v in style['values'].items() if k in {'IsReadOnly','IsEnabled','MaxLength','IsTabStop','IsEditable','SelectionMode','Visibility'}) or '個別項目の設定を使用'
        ui+=['### '+key,'', '**適用**：'+'、'.join(dict.fromkeys(f['id']+' '+f['name'] for f,i in uses))+'。','**状態・入力制約**：'+attrs+'。','**登録される共通動作**：'+'、'.join(h.get('Event','')+'：'+h.get('Handler','') for h in style['handlers'])+'。', '根拠：'+link('../'+style['path']+'#L'+str(style['line']),key),'']
    ui+=['## 3. 操作と入力の共通動作','',COMMON_RULES[0][2],COMMON_RULES[1][2],COMMON_RULES[2][2],COMMON_RULES[7][2],'','## 4. 制限','','HTMLは仕様確認用の再配置であり、上記の部品継承・フォーカス・IME・データ受渡しの実動作を再現したものではない。部品IDと登録先の技術表記は開発側の対応付け用で、顧客向けの動作説明と分離する。']
    return {COMMON:'\n'.join(common)+'\n','概要仕様書COM-002_共通関数仕様.md':name_text('\n'.join(funcs),reg)+'\n','概要仕様書COM-003_共通UI仕様.md':'\n'.join(ui)+'\n'}


def databases(data,reg):
    objects=reg['objects'];fnames={f['id']:f['name'] for f in data['features']}
    out=['# DB定義書 — 論理名・利用文脈・データ処理','','**原本の使用箇所から復元した論理定義・物理定義候補であり、実DBへの照合は未実施。** 物理型・桁数・NULL・主外部キー・索引・DB関数内部を、画面上限や命名から断定しない。論理名の候補が複数ある場合は競合として保持する。','']
    index=[]
    for name,o in objects.items():
        index.append([o['logical_name'],name,o['kind'],len(o['columns']),len(o['uses']),'・'.join(o['feature_ids']) or '静的呼出未解決'])
        out+=['## '+o['logical_name'],'','物理名：`'+name+'`。名称の確度：'+o['name_status']+'。','', '**業務上の使用範囲**：'+('、'.join(fnames.get(x,x) for x in o['feature_ids']) or '機能との到達関係は未解決。直接の使用箇所を下表に保持する')+'。','',table(['論理項目名','物理列名','用途・説明','物理型','NULL・長さ・キー','名称の競合'],[[d['logical_name'],c,d['description'],d['type'],'／'.join(str(d.get(x,'未確認')) for x in ['nullable','length','key']),'候補：'+'、'.join(d['label_candidates']) if d['conflict'] else '競合未検出'] for c,d in o['columns'].items()]),'', '### 登録・検索・更新元からの再帰追跡','',table(['直接使用処理','操作','到達する機能','到達の種類','原本'],[[event_name(data['methods'][u['method']].get('summary') or '名称要確認'),OPS.get(u['operation'],u['operation']),'・'.join(sorted({v['feature'] for v in u['consumers']})) or '未解決','・'.join(sorted({v['relation'] for v in u['consumers']})) or '直接使用のみ',u['path']+':L'+str(u['line'])] for u in o['uses']]),'', '参照、結合、更新対象の関係はソース上の利用関係であり、外部キー制約の証明ではない。最短の呼出鎖と全エッジは横断解析JSONに保持し、循環参照で走査を打ち切って情報を黙って捨てない。','']
    objectdoc='# DBオブジェクト一覧\n\n論理名を先に示し、原本照合用の物理名と対応させる。種別は物理DDL不在の場合に未確定となる。\n\n'+table(['論理名','物理名','種別','列候補数','直接使用箇所','利用機能'],index)
    names='# 命名規則・論理名辞書\n\n## 1. 表現の使い分け\n\n顧客向け本文は日本語論理名を優先する。DB連携、再実装、変更影響の照合では論理名と物理名を両方保持する。同名の列を異なる表の同じ業務値と決めつけない。\n\n## 2. データ名\n\n'+table(['日本語の論理名候補','物理名','確度'],[[o['logical_name'],n,o['name_status']] for n,o in objects.items()])+'\n## 3. プログラムの観測規則と新規命名\n\n原本の画面・モデル・共通クラスは責務名とWindow／Model等の役割を組み合わせる。画面部品にはtxt、cmb、btn等の役割を示す接頭辞が観測される。これらを他言語へ必須の命名として持ち込まない。新規の業務識別子は意味を表す名称とし、言語固有の大小文字・文字制約は言語アダプター側で適用する。機能・項目・イベントIDは表示順から独立させ、名称変更でも再採番しない。\n'
    return {'DB定義書.md':'\n'.join(out)+'\n','DBオブジェクト一覧.md':objectdoc,'命名規則.md':names}


def standards(data):
    return '''# 開発規約 — 横断的な実装・検証の取り決め

## 1. 適用と既存仕様の優先順位
原本で確認した現行動作と、今後の再実装に適用する規約を区別する。業務仕様、共通仕様、DB定義、項目辞書、受入例、開発規約を同じ版で固定する。矛盾を見つけた場合は、都合のよい方を実装せず差分記録を起票する。

## 2. 例外処理
現行の共通DB更新では、接続開始・取引開始が内部の例外捕捉より前に置かれるものがある。更新文実行中の例外は取消を試み、通知して失敗を返す。取引を使わない処理、読み取り、画面内の変更を同じ例外契約とみなさない。
再実装時の規約案：入力不備、業務上の不成立、通信・DB・ファイル障害を分ける。利用者通知、操作継続可否、ログ、再試行の可否をイベント単位で定義する。原因や資格情報をそのまま顧客向けメッセージへ出さない。捕捉後の成功通知を禁止し、取消処理自身の失敗も記録する。この改善案は現行で実現済みという意味ではない。

## 3. トランザクションと採番
現行の複数SQL更新は、配列順に実行して全件終了後に1回確定する。途中失敗時には取消を試みる。画面内の明細保存は、このDB確定の前段である。送り状一括更新の対象条件、採番が行われる時点、共通更新関数の内外を仕様に残す。
再実装時の規約案：更新対象、キー、値の由来、実行順、確定境界、取消範囲を事前に固定する。採番の欠番許容やシーケンスの巻戻しを通常行更新と同一視しない。同時更新・楽観ロック・二重送信・再実行時の重複回避はDB定義と業務合意で確定する。未取得の制約を勝手にDDLへ追加しない。

## 4. データ型・金額・日付
数量の符号・0の許容は操作モードごとに定める。金額・率の途中精度、端数処理、丸め時点を固定する。単に「四捨五入」と書かず、中間値の例を持つ。日付は暦日と時刻を分け、保存値・表示値・空値を明記する。文字数と文字コード別のバイト数、前後空白除去、入力長と物理列長を区別する。

## 5. 命名と責務
命名規則.mdの論理名辞書を正本とし、表示名、物理名、ソース上の識別子を混同しない。共通業務ルール、DBアクセス、UI制御、帳票、外部接続を分離する。他案件のコード接頭辞やフォルダ名を汎用スキャナーの前提にしない。

## 6. Pilot再実装の独立性
再実装側に渡すのは固定した仕様書・共通仕様・DB定義・開発規約だけとする。原本と期待値の抽出は評価側に限定する。外部依存を代替した場合は代替箇所と未検証範囲を記録する。同一の生成ロジックから期待値を作って一致率を上げてはならない。ソース一致率ではなく、入力、結果、更新対象、更新順、失敗時状態の再現性を評価する。

## 7. 回帰・公開
基本処理、境界、未設定、対象なし、複数候補、取消、障害、更新順と再実行を分けて検査する。新しい不足が見つかったら個別仕様だけでなく共通・DB・規約の該当箇所を修正し、影響する機能も再生成する。機械検査成功と顧客承認を別状態にし、再実装可能性の未検証を合格に読み替えない。
'''
