"""Render normalized evidence as Japanese Markdown, separate from audit evidence."""
from __future__ import annotations
from collections import Counter,defaultdict
import html
import json
from pathlib import Path
import re
from urllib.parse import quote
from .core import digest,dumps,load,save

VERSION='2.0.1'
COMMON='概要仕様書COM-001_共通仕様.md'
SYSTEM='概要仕様書SYS-001_システム分析.md'
ROLES={'input':'入力・選択','display':'表示','operation':'操作','internal':'内部・非表示'}
KINDS={'screen':'画面','mixed':'画面・帳票の混在','batch_dialog':'処理ダイアログ','batch_or_api':'バッチ／API候補'}


def esc(v):
    return html.escape(str(v),quote=False).replace('|','&#124;').replace('\n','<br>').replace('\r','').replace('`','&#96;')


def table(headers,rows):
    if not rows:return '該当する定義は確認できていません。\n'
    return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+'\n'.join('| '+' | '.join(esc(x) for x in row)+' |' for row in rows)+'\n'


def link(path,label):return '['+esc(label)+']('+quote(path,safe='/#')+')'

def q(v):return str(v).replace('"','＂').replace('\n',' ').replace('[','（').replace(']','）').replace('<','＜').replace('>','＞').replace('&','＆')[:150]

def mermaid(lines):return '```mermaid\n'+'\n'.join(lines)+'\n```\n'

def event_name(value):
    value=value.replace('Window ContentRendered','表示完了時の処理開始').replace('Window Loaded','初期表示').replace('Window Closing','終了要求')
    for a,b in [('SelectionChanged','選択変更'),('SelectedDateChanged','日付変更'),('LostFocus','入力確定'),('TextChanged','入力変更'),('MouseDoubleClick','ダブルクリック'),('ContentRendered','表示完了'),('Checked','選択変更'),('Click',''),('Window','画面')]:value=value.replace(a,b)
    return value.strip() or '動作確認が必要なイベント'


def language_terms(f,data):
    labels={item['binding']:item['name'] for item in f['items'] if item['binding']}
    labels.update({item['key']:item['name'] for item in f['items']})
    for path in [f.get('code')]+f.get('models',[]):
        for p in data['records'].get(path,{}).get('fields',[]):
            if p.get('summary'):labels.setdefault(p['name'],p['summary'])
    labels.update({'CommandMode':'操作モード','ADD':'追加','EDT':'修正','DEL':'削除','Today':'当日','Now':'現在日時','True':'有効','False':'無効','Nothing':'未設定','Me':'本画面','IsChangedInput':'未保存変更あり','IsRaiseControlChanged':'入力変更の監視中','IsCloseConfirm':'終了確認を行う','DialogResult':'呼出元へ返す結果','IsEnabled':'操作可能','IsReadOnly':'表示専用','IsChecked':'選択状態','Visibility':'表示状態','HasRows':'対象データあり','Count':'件数','Length':'長さ','Text':'入力内容','Trim':'前後空白除去','Password':'パスワード','Value':'値','SelectedItem':'選択対象','SelectedIndex':'選択位置','IsSeikyuSumi':'請求済み','Orders':'入力明細一覧','ToString':'表示値へ変換','Contains':'含む','Replace':'置換','ToList':'一覧化','Sum':'合計','UserNm':'利用者名','PaymentDate':'入金日'})
    methods={m['name']:event_name(m.get('summary','')) for m in data['methods'].values() if m.get('summary')}
    return labels,methods


def business_expr(expr,labels,methods):
    s=expr.strip().rstrip('_').strip()
    s=re.sub(r'\b(?:_Model|Model|mSelected|mChild|order|MyGlobal|MyPara|MySettings\.Default|My\.Settings)\.', '',s)
    s=s.replace('MyPara.','')
    # Qualified calls become their documented business responsibility when available.
    s=re.sub(r'\b(?:MyApp|MyNpg|MyList|\w+Model)\.(\w+)\([^)]*\)',lambda m:methods.get(m.group(1),'共通処理の結果'),s)
    for key in sorted(labels,key=len,reverse=True):
        s=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(key)+r'(?![A-Za-z0-9_])',lambda _:labels[key],s)
    for key in sorted(methods,key=len,reverse=True):
        if key.startswith('_'):s=re.sub(r'\b'+re.escape(key)+r'\b',methods[key],s)
    s=re.sub(r'\bAndAlso\b|\bAnd\b',' かつ ',s,flags=re.I);s=re.sub(r'\bOrElse\b|\bOr\b',' または ',s,flags=re.I)
    s=re.sub(r'\bIsNot\b',' ではない ',s);s=re.sub(r'\bIs\b',' が ',s);s=re.sub(r'\bNot\b',' 否定：',s)
    s=s.replace('<>',' ≠ ').replace('>=',' ≧ ').replace('<=',' ≦ ').replace('""','空欄')
    s=s.replace('vbCrLf','改行').replace('DBNull.Value','未設定').replace('Visibility.Visible','表示').replace('Visibility.Hidden','非表示').replace('Visibility.Collapsed','領域も非表示')
    # Untranslated implementation expressions are preserved in the evidence file,
    # never presented as a supposedly language-independent business rule.
    if re.search(r'\b(?:_\w+|CType|CInt|CDate|Function|New|ElseIf|Then|StringBuilder|sender|e|drd|npg|sbSql|ListSortDirection|[a-z][A-Za-z]+_[A-Za-z]+)\b',s):return None
    if re.search(r'\b[A-Za-z][A-Za-z_]*\.',s):return None
    return re.sub(r'\s+',' ',s).strip()


def event_rules(f,e,data):
    labels,methods=language_terms(f,data);rules=[];unresolved=[]
    for mid in e['methods']:
        m=data['methods'][mid]
        # Low level DB helpers and UI utilities are documented in common specs.
        if '/Classes/' in m['path']:continue
        for st in m['statements']:
            s=st['text'];kind=None;expr=None
            hit=re.match(r'(?:ElseIf|If)\s+(.+?)\s+Then\b',s,re.I)
            if hit: kind='判定';expr=hit.group(1)
            else:
                hit=re.match(r'(?:_Model|Model)\.(\w+)\s*=\s*(.+)',s)
                if hit:kind='設定';expr=labels.get(hit.group(1),hit.group(1))+' ← '+hit.group(2)
            if kind:
                human=business_expr(expr,labels,methods)
                item={'kind':kind,'text':human or '追加確認が必要な'+kind,'path':m['path'],'line':st['line'],'raw':s}
                if human:rules.append(item)
                else:unresolved.append(item)
    return list({(x['path'],x['line']):x for x in rules}.values()),unresolved


def db_catalog(data):
    objects=defaultdict(lambda:{'operations':set(),'sources':set(),'columns':{},'kind':'table_or_view','definition':'source_inferred'})
    for path,r in data['records'].items():
        ms=r.get('methods',[])+([r['sql_facts']] if r.get('sql_facts') else [])
        for m in ms:
            for x in m.get('db',[]):
                obj=objects[x['object']];obj['operations'].add(x['operation']);obj['sources'].add(path)
            for x in m.get('columns',[]):
                objects[x['object']]['columns'].setdefault(x['column'],{'type':'未確認','nullable':'未確認','length':'未確認','key':'未確認','origin':'ソース参照から推定','path':path,'line':x['line']})
            for name in m.get('db_functions',[]):objects[name]['kind']='function';objects[name]['sources'].add(path)
            for name in m.get('sequences',[]):objects[name]['kind']='sequence';objects[name]['sources'].add(path)
        for t in r.get('tables',[]):
            obj=objects[t['name']];obj['definition']='declaration';obj['sources'].add(path);obj['kind']='table'
            for c in t['columns']:obj['columns'][c['name']]={'type':c['type'],'nullable':c['nullable'],'length':'宣言型参照','key':'PK' if c['primary_key'] else '未確認','origin':t['origin'],'path':path,'line':c['line']}
    for f in data['features']:
        for item in f['items']:
            for mp in item['db']:objects[mp['object']]['columns'].setdefault(mp['column'],{'type':'未確認','nullable':'未確認','length':'未確認','key':'未確認','origin':'画面への取得値対応から推定','path':mp['path'],'line':mp['line']})
    return {name:{**v,'operations':sorted(v['operations']),'sources':sorted(v['sources'])} for name,v in sorted(objects.items())}


def message_catalog(data):
    constants={c['name']:c['value'] for r in data['records'].values() for c in r.get('constants',[])}
    out=[]
    from .adapters import STRING
    for path,r in data['records'].items():
        for c in r.get('constants',[]):
            if '/MyMessage.' in path:
                text='\n'.join(x.group()[1:-1].replace('""','"') for x in STRING.finditer(c['value']))
                out.append({'id':'MSG-'+c['name'],'text':text,'path':path,'line':c['line'],'kind':'共通定義','source_name':c['name']})
        for m in r.get('methods',[]):
            for st in m.get('messages',[]):
                value=st['text']
                value=re.sub(r'MyMessage\.(\w+)',lambda h:constants.get(h.group(1),h.group()),value)
                text='\n'.join(x.group()[1:-1].replace('""','"') for x in STRING.finditer(value))
                if not text:continue
                out.append({'id':'MSG-'+digest(path+':'+m['name']+':'+st['text'])[:12].upper(),'text':text,'path':path,'line':st['line'],'kind':'表示箇所' if re.search(r'\.Show\w*\(',st['text']) else '文面の組立候補','source_name':m['name']})
    return list({(x['id'],x['path'],x['line']):x for x in out}.values())


def render_feature(f,data):
    p=[f"# {f['name']} — 概要仕様書",'',f"機能ID：{f['id']}　種類：{KINDS.get(f['kind'],f['kind'])}　業務区分：{f['group']}",'','> 現行ソースに基づく顧客確認用の版です。未確定事項は第4章と独立評価に記載しています。','', '## 1. システム概要','','### 1.1 概要説明', '', f['purpose'],'','### 1.2 レイアウト','', '画面内の領域構成を示します。寸法・実際の見た目の再現ではありません。入力位置の静的な並び順と、キーボード操作順は区別します。','']
    counts=Counter(i['role'] for i in f['items']);cols=sum(i['is_column'] for i in f['items'])
    p.append(table(['領域','内容','定義数'],[[ROLES[role],'、'.join(i['name'] for i in f['items'] if i['role']==role),counts[role]] for role in ROLES if counts[role]]))
    p += ['### 1.3 入出力（IO）','',table(['区分','入出力情報','相手・用途'],[['入力','、'.join(i['name'] for i in f['items'] if i['role']=='input'),'利用者による入力・選択'],['操作','、'.join(i['name'] for i in f['items'] if i['role']=='operation'),'第3章のイベントを開始'],['出力','、'.join(i['name'] for i in f['items'] if i['role']=='display'),'検索結果・計算結果・確認内容'],['DB','、'.join(sorted({r['object'] for r in f['db']})) or '直接の静的参照なし','参照・更新は次の関連図とCRUD図を参照']]),'','### 1.4 関連図','']
    dg=['flowchart LR',f'  F["{q(f["name"])}"]','  I["利用者の入力・操作"] --> F','  F --> O["表示・処理結果"]']
    for n,obj in enumerate(sorted({r['object'] for r in f['db']})):
        refs=[r for r in f['db'] if r['object']==obj];ops=sorted({r['operation'] for r in refs})
        dg.append(f'  D{n}[("{q(obj)}")]')
        if 'R' in ops:dg.append(f'  D{n} -->|参照| F')
        writes=[op for op in ops if op!='R']
        if writes:dg.append(f'  F -->|{q("・".join(writes))}| D{n}')
    report_names=sorted({r for e in f['events'] for r in e['reports']})
    if report_names:dg+=['  F --> R["帳票データ"]','  R --> V["帳票表示・ファイル出力"]']
    if f['id']=='TKL-025':dg+=['  F --> X["外部バックアップコマンド"]','  X --> B["バックアップファイル"]']
    if f['id']=='TKL-022':dg+=['  CSV["住所更新CSV"] --> F']
    if f['id']=='TKL-013':dg+=['  F --> CSV["送り状CSV"]']
    if f['id']=='TKL-038':dg+=['  R["作成済み帳票"] --> F','  F --> X["PDF・Excelファイル"]']
    p += [mermaid(dg),'関連DBは直接参照と到達可能な共通処理を含みます。動的なSQL・DB内部の副作用まで確定した物理関連図ではありません。候補の区別はCRUD図・根拠一覧に記録します。','','### 1.5 遷移図','']
    transitions=sorted({t for e in f['events'] for t in e['transitions']});by_class={x['source_class']:x for x in data['features']}
    tg=['flowchart LR',f'  F["{q(f["name"])}"]']
    for n,t in enumerate(transitions):tg.append(f'  F --> T{n}["{q(by_class[t]["name"] if t in by_class else "呼出先要確認")}"]')
    if not transitions:tg.append('  F --> R["終了／呼出元へ返却（条件はイベント仕様参照）"]')
    p += [mermaid(tg), '遷移先の一覧：'+('、'.join(link(by_class[t]['filename'],by_class[t]['name']) for t in transitions if t in by_class) or '独立した子画面への直接遷移は未検出。'),'','## 2. 項目一覧','',f"**合計：{len(f['items'])}項目**（入力・選択 {counts['input']}、表示 {counts['display']}、操作 {counts['operation']}、内部・非表示 {counts['internal']}）。うち一覧列は{cols}定義です。一覧のデータ件数は項目数に含めません。共通ヘッダー内の項目は共通仕様で一度だけ定義します。",'']
    for role in ROLES:
        items=[i for i in f['items'] if i['role']==role]
        if not items:continue
        p += ['### 2.'+str(list(ROLES).index(role)+1)+' '+ROLES[role],'']
        rows=[]
        for i in items:
            db='対象外（イベントに関連付け）' if role=='operation' else '、'.join(x['object']+'.'+x['column'] for x in i['db']) or '取得元・保存先の列対応は要確認'
            desc='操作内容は第3章を参照。' if role=='operation' else '値の表示専用。入力の必須・入力長は適用しない。' if role=='display' else '画面入力とは分けて管理する。' if role=='internal' else '利用者が入力・選択する。区分や操作モードによる補完・検証は第3章を参照。'
            if i['db']:desc+=' DBの物理型・制約を確定するものではない。'
            rows.append([f"{i['order']}. {i['name']}",i['type'],db,i['required'],i['length'],desc])
        p += [table(['項目名','タイプ','DB関連','必須','長さ','概要説明'],rows),'']
    p += ['## 3. イベント仕様','','### 3.1 業務処理の要点','',f['flow'],'']
    p += ['- '+rule for rule in f['rules']]
    p += ['','### 3.2 データ例','','以下は説明用の架空データであり、実行試験の結果ではありません。','',f['example'] or 'この機能の具体的な入力値と期待結果は、業務条件の確定後に追加します。','']
    audit=[];untranslated=0
    for n,e in enumerate(f['events'],1):
        human=event_name(e['name']);rules,unknown=event_rules(f,e,data);untranslated+=len(unknown)
        e['rules']=rules;e['unresolved']=unknown
        event_db=sorted({(r['object'],r['operation']) for r in e['db']})
        p += [f"### 3.{n+2} {human}（{e['id']}）",'',f'**契機**：{human}。以下はこの契機に関連する処理と判断です。複数の判定は条件に応じて実行され、表の全行が順番に実行されるわけではありません。','']
        comments=[]
        for mid in e['methods']:
            m=data['methods'][mid]
            if m['path']!=e['path']:continue
            for c in m['comments']:
                text=c['text']
                if re.search('[\u3040-\u9fff]',text) and not re.search(r'\b(?:SQL|AppendLine|sbSql|JBD\d|START|END)|^[\d/]+|[A-Za-z_]\w*\.',text):
                    text=re.sub(r'［(?:登録|変更|更新|削除)］\w+','関連データを更新',text)
                    if text not in comments:comments.append(text)
        if comments:p += ['- '+c+'。' for c in comments]
        if event_db:p+=['- 対象データの操作：'+'、'.join(obj+'（'+op+'）' for obj,op in event_db)+'。']
        if e['transitions']:p+=['- 関連画面：'+'、'.join(by_class[t]['name'] if t in by_class else '対応先要確認' for t in e['transitions'])+'。']
        if e['reports']:p+=['- 対象情報を帳票へ渡す。帳票の表示と印刷・ファイル保存の完了は区別する。']
        if rules:p+=['',table(['区分','判断・設定内容'],[[r['kind'],r['text']] for r in rules])]
        if unknown:p+=['',f'**確認事項**：複合条件・補助処理のうち{len(unknown)}箇所は、業務表現と期待結果の追加確認が必要です。根拠一覧には省略せず記録しています。']
        if not comments and not rules and not event_db and not e['transitions']:p+=['このイベントの業務上の意味と結果は、共通処理を含めた追加確認が必要です。']
        eg=['flowchart LR',f'  E["{q(human)}"]']
        for j,(obj,op) in enumerate(event_db):
            eg.append(f'  D{j}[("{q(obj)}")]')
            eg.append(f'  D{j} -->|参照| E' if op=='R' else f'  E -->|{q(op)}| D{j}')
        if not event_db:eg.append('  E --> S["画面状態・受渡し・共通処理を確認"]')
        p+=['','**イベントとデータの関係**',mermaid(eg)]
        audit.append({'event':e['id'],'name':human,'path':e['path'],'line':e['line'],'end':e['end'],'rules':rules,'unresolved':unknown,'methods':e['methods'],'db':e['db']})
    p += ['## 4. 補足説明','','### 4.1 共通仕様','',link(COMMON,'入力・終了確認・検索・DB更新・帳票の共通仕様')+'を参照します。個別条件と共通条件が異なる場合は、適用範囲と例外を確認してから確定します。','','### 4.2 注意事項・確認事項','']
    p+=['- '+note for note in f['notes']]
    uncertain=sum(i['db_status']=='unresolved' for i in f['items'] if i['role']!='operation')
    p += [f'- DB列の対応が未確定な項目：{uncertain}件。物理定義の不足はDB定義書に分離しています。',f'- 業務表現への追加確認が必要な条件・設定：{untranslated}箇所。', '- レイアウトからの静的な項目順は整理済みですが、実画面の配置・キーボード順・動的表示の検証は未実施です。','- この文書だけによる同等プログラムの再実装可否は、独立評価の判定を参照してください。','','### 4.3 関連資料','',link('メッセージ一覧.md','メッセージ一覧')+' ／ '+link('CRUD図.md','CRUD図')+' ／ '+link('DB定義書.md','DB定義書')+' ／ '+link('DBオブジェクト一覧.md','DBオブジェクト一覧'),' ',link('../report/overview/根拠_'+f['id']+'.md','項目・イベント・条件の根拠')+' ／ '+link('../report/overview/独立評価.md','独立評価結果')]
    f['quality']={'untranslated_rules':untranslated,'unresolved_db_items':uncertain,'physical_schema_missing':data['system']['physical_schema']=='not_found'}
    return '\n'.join(p)+'\n',audit


def common_document(data):
    return '''# 共通仕様 — 概要仕様書

機能ID：COM-001　対象：現行アプリケーションの共通処理

## 1. システム概要

個別機能に共通する入力、操作、検索、データ更新、帳票の扱いを定義します。画面での一時保存とデータベースへの確定を区別し、個別の例外は各概要仕様書に記載します。以下の現行動作はTKLの共通ソースに基づき、別システムへ無条件に適用しません。

### 1.1 入出力と関連

```mermaid
flowchart LR
    U["利用者の入力・操作"] --> F["個別機能"]
    F --> C["入力・検索・終了確認"]
    F --> T["DB更新の共通処理"]
    T --> D[("関連データ")]
    F --> R["帳票表示・ファイル出力"]
    C --> M["メッセージ"]
    T --> M
```

### 1.2 レイアウト・遷移

共通ヘッダー、利用者表示、メニューへ戻る、閉じる、終了などは適用する画面の共通定義に従います。個別画面の項目数には共通テンプレート内の部品を重複計上しません。Enterによる次項目、Shift＋Enterによる前項目への移動が実装されています。見た目の順序と実際の移動順序が一致するかは実画面で確認します。

## 2. 項目一覧

| 項目名 | タイプ | DB関連 | 必須 | 長さ | 概要説明 |
| --- | --- | --- | --- | --- | --- |
| 利用者 | 表示・内部状態 | 認証結果から取得 | 対象外 | 表示形式による | 利用者を変更すると表示と更新者に使用する状態を更新する |
| 操作モード | 内部状態 | 直接のDB列なし | 対象外 | 対象外 | 追加・修正・削除の動作を切り替える |
| 未保存変更 | 内部状態 | 直接のDB列なし | 対象外 | 対象外 | 閉じる・戻る際の保存確認に用いる |
| メニューへ戻る | 操作 | 対象外 | 対象外 | 対象外 | 未保存変更を確認してメニューへ移動する |
| 閉じる・終了 | 操作 | 対象外 | 対象外 | 対象外 | 画面の種類と保存確認の回答に従って終了する |

## 3. イベント仕様

### 3.1 必須検証と入力長

- 必須対象に指定された表示中の入力欄を検証します。文字・パスワードは前後空白を除いた内容、日付は選択値、選択欄は選択状態で判断します。
- 非表示の必須対象は共通検証上、充足扱いとなる経路があります。操作不可と非表示は同じ条件ではありません。
- 文字入力には欄ごとの文字数制限に加え、一部の共通入力処理でShift_JISのバイト数制限が適用されます。DBの列長とは別です。例えば同じ上限50でも全角文字50文字を必ず入力できるという意味ではありません。
- 数値欄、負数許可欄、年月欄、金額表示には別の制御があります。金額の丸めと業務計算の端数処理は、用途ごとの確認を要します。

### 3.2 一時保存・確定・終了確認

```mermaid
flowchart TD
    A["戻る・閉じる"] --> B{"未保存の変更と更新処理があるか"}
    B -->|あり| C["保存するか確認"]
    C -->|保存する| D["更新処理"]
    D --> E{"更新成功"}
    E -->|はい| F["終了または遷移"]
    E -->|いいえ| G["画面にとどまる"]
    C -->|保存しない| F
    C -->|取消| G
    B -->|なし| H["画面種別ごとの終了条件を確認"]
```

上図は子画面・画面遷移時の代表経路です。親を持たない主画面では確認の種類と否定時の扱いが異なります。契約・注文・入金の明細を画面内の一覧へ保存する操作は、DBへの確定とは区別します。

データ例：明細2件を画面内に保存した後、確定せず閉じようとした場合、確定して終了・破棄して終了・終了取消の分岐を確認します。架空の例であり実行試験の結果ではありません。

### 3.3 検索

一致・文字列・範囲の条件を共通処理で組み立てます。空の条件を検索条件へ加えない処理があります。文字列検索は用途によりかな表記の変換と大文字小文字を区別しない検索を使用します。前方一致・部分一致・範囲の境界は、個別の指定引数とDB関数の定義を確認します。

### 3.4 データ更新と異常時

トランザクションを使用する共通更新処理では、正常終了時に確定し、捕捉した例外時に取り消します。複数SQLを一つの更新呼出しで扱う場合も同じ更新境界に入ります。一方、トランザクションを使用しない別の更新処理もあります。複数の呼出しをまたぐ業務全体が一括で取り消されるとは限りません。

接続開始自体の失敗、外部コマンド、DB内関数・トリガー、印刷装置の動作はこの確認だけでは保証しません。排他、分離レベル、再実行、二重実行防止の業務要件は未確定です。

### 3.5 メッセージと帳票

共通文面と表示箇所はメッセージ一覧に集約します。同じ文面でも発生条件が異なる箇所は別に残します。置換値や例外詳細は機密情報が含まれないことを確認します。帳票のデータ作成・プレビュー・印刷・ファイル保存は別の成功判定です。

## 4. 補足説明

### 4.1 現行動作と改善提案の区別

バックアップの終了コード確認、出力失敗後の完了メッセージ、採番の同時実行、DB内部の連動更新には確認事項があります。望ましい処理を現行の確定仕様として補完していません。アクセス権、保存期間、監査、性能、障害復旧は別途合意が必要です。

### 4.2 共通仕様の適用

共通ソースとの対応は[共通根拠一覧](../report/overview/共通根拠.md)を参照します。将来の別言語・別構造のシステムでは、共通部品の検出結果と案件別の編集プロファイルを差し替えます。

### 4.3 作成・評価の参考

- [NASA: How to Write a Good Requirement](https://www.nasa.gov/reference/appendix-c-how-to-write-a-good-requirement/)：曖昧な表現を避け、検証可能性と一貫性を確認するための観点として参照。
- [arc42: Crosscutting Concepts](https://docs.arc42.org/section-8/)：複数機能にまたがる規則を一箇所で説明し、適用範囲を明確にする構成として参照。
- [W3C: Focus Order](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html)：意味・操作を保つ順序の観点を参照。WPFの実動作確認や規格適合の宣言を代替しない。
- [Mermaid: Flowchart Syntax](https://mermaid.js.org/syntax/flowchart.html)：図の構文を参照。

参照確認日：2026-10-03。公開資料は作成・評価方法の補強に用い、現行システムにない業務規則の根拠にはしません。
'''


def publish(root:Path,data):
    state=root/'.specgen-state/overview'; report=root/'report/overview'; output=root/'output'
    previous=load(state/'ownership.json',{});owned={};conflicts=[];written=0
    def put(path,text):
        nonlocal written
        if not path.resolve().is_relative_to(root) or path.is_symlink():raise ValueError('unsafe output')
        key=path.relative_to(root).as_posix()
        if path.exists() and key in previous and digest(path.read_bytes()) not in {previous[key],digest(text)}:
            conflicts.append(key);return
        # The existing root index is intentionally replaced on the user's regeneration request.
        if path.exists() and key not in previous and path.name!='機能一覧.md' and path.parent==output:
            if digest(path.read_bytes())!=digest(text):conflicts.append(key);return
        written+=int(save(path,text));owned[key]=digest(text)
        save(state/'ownership.json',{**previous,**owned})
    for f in data['features']:
        text,audit=render_feature(f,data);put(output/f['filename'],text)
        ev=['# '+f['id']+' 項目・イベントの根拠','','顧客向け本文から分離した調査証跡。コードを業務承認済み仕様と扱わない。','',table(['項目ID','表示名','役割','根拠','値対応'],[[i['key'],i['name'],i['role'],i['path']+':L'+str(i['line']),i['binding']] for i in f['items']])]
        for a in audit:
            ev+=['','## '+a['event']+' '+a['name'],'',link('../../'+a['path']+'#L'+str(a['line'])+'-L'+str(a['end']),'イベント原本'),'']
            for mid in a['methods']:
                m=data['methods'][mid];ev+=[link('../../'+m['path']+'#L'+str(m['line'])+'-L'+str(m['end']),m['name'])]
            ev+=['',table(['行','種別','原本表記','業務表現'],[[r['line'],r['kind'],r['raw'],r['text']] for r in a['rules']+a['unresolved']])]
        put(report/('根拠_'+f['id']+'.md'),'\n'.join(ev)+'\n');save(state/'outlines'/(f['id']+'.json'),f)
    index=['# 機能一覧','','概要仕様書はすべてoutput直下のファイル名で区別します。旧基本設計書は削除せず保持しています。','','## 概要仕様書','',table(['機能ID','種類','機能名','文書','評価状態'],[[f['id'],KINDS.get(f['kind'],f['kind']),f['name'],link(f['filename'],'概要仕様書'),'顧客確認用・独立評価参照'] for f in data['features']]),'','## 共通・補助文書','']
    # table() escapes normal HTML but preserves Markdown links.
    index+=['- '+link(name,label) for name,label in [(SYSTEM,'システム分析'),(COMMON,'共通仕様'),('メッセージ一覧.md','メッセージ一覧'),('CRUD図.md','CRUD図'),('DB定義書.md','DB定義書'),('DBオブジェクト一覧.md','DBオブジェクト一覧')]]
    index+=['',link('../report/overview/独立評価.md','独立評価結果')]
    put(output/'機能一覧.md','\n'.join(index)+'\n')
    common=common_document(data) if data['system'].get('system_name')=='Tokyo Librarian' else '# 共通仕様\n\n## 1. システム概要\n共通部品の業務仕様は追加確認が必要です。\n\n## 2. 項目一覧\n未確認。\n\n## 3. イベント仕様\n未確認。\n\n## 4. 補足説明\n別システムの共通規則を流用していません。\n'
    put(output/COMMON,common)
    put(output/SYSTEM,'# システム分析 — 概要仕様書\n\n## 1. システム概要\n\n'+table(['項目','抽出結果'],[[k,v] for k,v in data['system'].items()])+'\n## 2. 項目一覧\n\n言語・構造・顧客・作成者・業務区分を先に確認し、対応アダプターを選びます。作成者不明をコミット所有者で補いません。\n\n## 3. イベント仕様\n\n入力の版固定 → アダプターによる解析 → 索引・骨子JSON → 文書生成 → 独立評価の順で処理します。異なる言語では当該言語の抽出能力を評価し、未対応を黙って除外しません。\n\n## 4. 補足説明\n\nVB/WPFは限定的な静的解析です。Python・Java等の既存解析器を接続する入口はありますが、各言語の実案件に対する完全な意味解析は検証していません。\n')
    objects=db_catalog(data);data['db_objects']=objects
    put(output/'DBオブジェクト一覧.md','# DBオブジェクト一覧\n\nソースから観測された候補です。名前だけでテーブルとビューを確定しません。未取得のDBオブジェクトが存在しないという意味ではありません。\n\n'+table(['物理名','種別','定義根拠','観測操作','列候補数'],[[name,v['kind'],v['definition'],','.join(v['operations']),len(v['columns'])] for name,v in objects.items()]))
    db=['# DB定義書','','物理DDLがないオブジェクトはソースからの推定版です。画面の必須・文字数、変数型、名称だけからDBのNOT NULL・長さ・主キー・外部キーを確定しません。DB関数・トリガー・ビュー内部の定義は未取得です。']
    for name,v in objects.items():
        db+=['','## '+name,'','定義の状態：'+v['definition']+'。種類：'+v['kind']+'。',table(['列名','型','NULL','長さ','キー','根拠区分'],[[c,d['type'],d['nullable'],d['length'],d['key'],d['origin']] for c,d in sorted(v['columns'].items())])]
    put(output/'DB定義書.md','\n'.join(db)+'\n')
    crud=['# CRUD図','','C：追加、R：参照、U：更新、D：削除。TRUNCATE・COPYは別操作として記載します。DB内部の連鎖更新を創作していません。','',table(['機能ID','機能','DBオブジェクト','操作','到達関係'],[[f['id'],f['name'],obj,','.join(sorted({r['operation'] for r in f['db'] if r['object']==obj})),','.join(sorted({r.get('reachability','candidate') for r in f['db'] if r['object']==obj}))] for f in data['features'] for obj in sorted({r['object'] for r in f['db']})])]
    for f in data['features']:
        lines=['flowchart LR',f' F["{q(f["id"]+" "+f["name"])}"]']
        for n,obj in enumerate(sorted({r['object'] for r in f['db']})):
            ops=sorted({r['operation'] for r in f['db'] if r['object']==obj});lines.append(f' D{n}[("{q(obj)}")]')
            if 'R' in ops:lines.append(f' D{n} -->|R| F')
            if any(op!='R' for op in ops):lines.append(f' F -->|{q("/".join(o for o in ops if o!="R"))}| D{n}')
        crud+=['','## '+f['id'],mermaid(lines)]
    put(output/'CRUD図.md','\n'.join(crud)+'\n')
    messages=message_catalog(data);data['messages']=messages
    put(output/'メッセージ一覧.md','# メッセージ一覧\n\n共通定義、個別の表示箇所、文面組立候補を区別します。変数だけで組み立てる文面や外部ライブラリ内の文面は、完全には確定していません。メッセージの存在と実際に表示される条件を同一視しません。\n\n'+table(['ID','区分','文面','発生箇所'],[[m['id'],m['kind'],m['text'],m['path']+':L'+str(m['line'])] for m in messages]))
    commons=['# 共通根拠一覧','','原本との対応です。全機能にすべての共通処理が適用されることを意味しません。','']
    commons+=[link('../../'+p+'#L'+str(m['line']),m['summary'] or m['name'])+'  '+p for p,r in data['records'].items() if '/Classes/' in p for m in r.get('methods',[])]
    put(report/'共通根拠.md','\n'.join(commons)+'\n')
    save(state/'objects.json',objects);save(state/'messages.json',messages)
    save(state/'ownership.json',{**previous,**owned})
    return {'written':written,'conflicts':conflicts,'feature_documents':len(data['features']),'supplementary_documents':6,'message_definitions_and_candidates':len(messages),'db_object_candidates':len(objects)}
