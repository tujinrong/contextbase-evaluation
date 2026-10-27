"""Customer-oriented rendering with bounded, explicit business interpretation.

Unsupported expressions are retained in evidence, not mechanically translated
into misleading pseudo-Japanese. Event setup is not treated as event execution.
"""
from __future__ import annotations
from collections import Counter
import re
from .adapters import STRING
from .publish import render_feature as first_render, table, link, mermaid, q, event_name, COMMON

OPS={'C':'追加','R':'参照','U':'更新','D':'削除','COPY':'ファイル取込','TRUNCATE':'全件消去'}
GLOSSARY={'CommandMode':'操作モード','MyPara.CommandMode.ADD':'追加','MyPara.CommandMode.EDT':'修正','MyPara.CommandMode.DEL':'削除','Today':'当日','Now':'現在日時','True':'有効','False':'無効','Nothing':'未設定','IsSeikyuSumi':'請求済み','IsHakkoNew':'新規発行','IsHakkoRe':'再発行','IsChangedInput':'未保存の変更','IsRaiseControlChanged':'変更監視状態','DialogResult':'呼出元への結果','UserNm':'利用者名','PaymentDate':'入金日','SelectedItem':'選択行','HasRows':'対象データの存在','Count':'件数','Length':'文字数','IsChecked':'選択状態','Text':'入力内容','Password':'パスワード','SelectedIndex':'選択位置'}
COMMENT_SENTENCES={'入力チェック':'入力条件を検証する。','検証':'対象の値と処理条件を検証する。','確認':'処理を進めてよいか確認する。','リストセット':'選択欄に使用する選択肢を設定する。','モデルセット':'画面に表示・編集する情報を設定する。','初期値セット':'個別に定めた初期値を設定する。','初期設定':'操作モードに応じて初期状態を設定する。','グリッドセット':'一覧の内容を取得して表示する。','データ取得':'処理に使用するデータを取得する。','帳票出力':'対象情報を帳票に設定して表示処理へ渡す。','値クリア':'入力した条件を初期状態へ戻す。','グリッド行削除':'対象行を画面の一覧から取り除く。','グリッド行追加':'対象の明細を画面の一覧へ追加する。','グリッド行編集':'画面の一覧へ明細の変更を反映する。','保存ダイアログ表示':'保存先を選択する画面を表示する。','ファイル出力':'選択した形式と保存先にファイルを出力する。','顧客IDリスト再セット':'更新後の顧客IDを選択肢へ反映する。','修正値反映':'変更した値を呼出元の表示へ反映する。'}


def words(f,data):
    out=dict(GLOSSARY)
    for i in f['items']:
        if i['binding']:out[i['binding']]=i['name']
        out[i['key']]=i['name']
    for p in [f.get('code')]+f.get('models',[]):
        for field in data['records'].get(p,{}).get('fields',[]):
            if field.get('summary'):out.setdefault(field['name'],field['summary'])
    return out


def expression(value,glossary):
    s=value.strip()
    # String contents are not code identifiers.
    strings=[]
    def literal(m):
        strings.append(m.group()[1:-1].replace('""','"'))
        return '§'+str(len(strings)-1)+'§'
    s=STRING.sub(literal,s)
    s=re.sub(r'\b(?:_Model|Model|MyGlobal)\.', '',s)
    for key in sorted(glossary,key=len,reverse=True):
        s=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(key)+r'(?![A-Za-z0-9_])',lambda _:glossary[key],s)
    replacements={'AndAlso':'かつ','OrElse':'または','And':'かつ','Or':'または','IsNot':'ではない','Is':'が','Not':'否定：','vbCrLf':'改行'}
    for a,b in replacements.items():s=re.sub(r'\b'+a+r'\b',b,s)
    s=s.replace('<>','≠').replace('>=','≧').replace('<=','≦')
    # Reject leftover source identifiers, unmatched parentheses and call syntax.
    check=re.sub(r'\b(?:ID|DB|TEL|FAX|CSV|PDF|PR)\b','',s)
    if re.search('[A-Za-z_]',check) or s.count('(')!=s.count(')') or re.search(r'[\u3040-\u9fff]\(',s):return None
    for n,text in enumerate(strings):s=s.replace('§'+str(n)+'§','「'+text+'」' if text else '空欄')
    return re.sub(r'\s+',' ',s).strip()


def conditions_and_settings(f,event,data):
    glossary=words(f,data);rows=[];unresolved=[]
    for mid in event['methods']:
        m=data['methods'][mid]
        if m['path']!=f.get('code'):continue
        for st in m['statements']:
            text=st['text'];kind=None;raw=None
            match=re.match(r'(?:ElseIf|If)\s+(.+?)\s+Then\b',text,re.I)
            if match:kind='判定条件';raw=match.group(1)
            else:
                match=re.match(r'(?:_Model|Model)\.(\w+)\s*=\s*(.+)',text)
                if match:kind='値の設定';raw=glossary.get(match.group(1),match.group(1))+' ← '+match.group(2)
            if kind:
                human=expression(raw,glossary)
                entry={'kind':kind,'text':human or '条件・設定の業務解釈を要確認','path':m['path'],'line':st['line'],'raw':text}
                (rows if human else unresolved).append(entry)
    return rows,unresolved


def event_messages(event,data):
    constants={c['name']:c['value'] for r in data['records'].values() for c in r.get('constants',[])}
    result=[]
    for st in event['messages']:
        raw=st['text'];value=re.sub(r'MyMessage\.(\w+)',lambda m:constants.get(m.group(1),m.group()),raw)
        strings=[x.group()[1:-1].replace('""','"') for x in STRING.finditer(value)]
        if not strings:continue
        caption='表示文面' if re.search(r'\.Show\w*\(',raw) else '条件によって組み立てる文面'
        pair=(caption,'\n'.join(strings))
        if pair not in result:result.append(pair)
    return result


def render(f,data):
    # Retain the standardized first chapter, diagrams and evidence conventions.
    initial,_=first_render(f,data)
    text=initial.split('## 2. 項目一覧',1)[0]
    counts=Counter(i['role'] for i in f['items'])
    text+='## 2. 項目一覧\n\n'
    text+=f"**合計：{len(f['items'])}項目**（入力・選択 {counts['input']}、表示 {counts['display']}、操作 {counts['operation']}、内部・非表示 {counts['internal']}）。一覧の繰返しデータ件数は含めず、列定義を一度ずつ数える。共通テンプレートの項目は共通仕様に分離する。\n\n"
    text+='以下は静的な画面配置順である。並び順番号は全種類で共通とし、種類別に並べ替えない。実画面の位置・フォーカス順は独立評価の確認対象とする。\n\n'
    rows=[]
    for i in f['items']:
        role={'input':'入力・選択','display':'表示','operation':'操作','internal':'内部'}[i['role']]
        if i['role']=='operation':db='対象外（処理はイベントで定義）';desc='この操作で開始する処理は第3章を参照する。'
        else:
            db='、'.join(x['object']+'.'+x['column']+('［保存］' if x.get('direction')=='write' else '［取得］') for x in i['db'])
            if not db:db='直接のDB列なし（画面の選択状態）' if i['db_status']=='ui_state_only' else '列の対応は追加確認'
            desc=(i['name']+'を入力・選択する。' if i['role']=='input' else i['name']+'を表示する。入力は受け付けない。' if i['role']=='display' else '通常は画面に表示しない制御用情報。')
            if i['tag']=='ComboBox':desc+=' 選択肢の値と名称は区分・関連マスタに従う。'
            if i['is_column']:desc+=' 一覧の1列を表す。'
        req=i['required'];length=i['length']
        rows.append([str(i['order'])+'. '+i['name'],role+'／'+i['type'],db,req,length,desc])
    text+=table(['項目名','タイプ','DB関連','必須','長さ','概要説明'],rows)+'\n'
    text+='## 3. イベント仕様\n\n### 3.1 業務処理の全体像\n\n'+f['flow']+'\n\n'
    text+='\n'.join('- '+r for r in f['rules'])+'\n\n'
    text+='### 3.2 データ例\n\n'+(f['example'] or '具体的な入力値と期待結果は業務条件の確定後に補足する。')+'\n\n※説明用の架空データであり、プログラムを実行した試験結果ではない。\n\n'
    byclass={x['source_class']:x for x in data['features']};audit=[];total_unresolved=0
    for n,e in enumerate(f['events'],3):
        title=event_name(e['name']);e['rules'],e['unresolved']=conditions_and_settings(f,e,data);total_unresolved+=len(e['unresolved'])
        text+=f"### 3.{n} {title}（{e['id']}）\n\n"
        text+=f'**開始条件**：{title}の操作・通知を受けたとき。\n\n'
        entry=next((data['methods'][mid] for mid in e['methods'] if data['methods'][mid]['name']==e['source_name'] and data['methods'][mid]['path']==e['path']),None)
        steps=[]
        if entry:
            for c in entry['comments']:
                if c['text'] in COMMENT_SENTENCES and COMMENT_SENTENCES[c['text']] not in steps:steps.append(COMMENT_SENTENCES[c['text']])
        db=sorted({(r['object'],r['operation']) for r in e['db']})
        if not steps and db:steps.append('このイベントから呼び出す処理のデータ参照・変更範囲を、下表に示す。')
        if any(op!='R' for obj,op in db):steps.append('追加・修正・削除等は操作モードや業務条件で分岐する。すべての変更を一度に実行するという意味ではない。')
        if e.get('deferred_callbacks'):steps.append('後続操作で使用する処理を登録する。登録時点では、その処理に含まれるDB更新を実行しない。')
        for target in e['transitions']:
            if target in byclass:steps.append(byclass[target]['name']+'へ処理を引き継ぐ。選択結果や戻り条件は対象機能の仕様も参照する。')
        if e['reports']:steps.append('対象データを帳票へ渡す。プレビュー、印刷、ファイル保存はそれぞれの成否を区別する。')
        if not steps:steps.append('画面の値・表示状態・呼出元への受渡しに関するイベントである。個別の条件は以下と共通仕様を参照する。')
        text+='\n'.join('- '+s for s in steps)+'\n\n'
        if e['rules']:
            text+='**確認できた条件・設定**\n\n以下は関連する処理内の個別条件であり、分岐の親子関係や全体の実行順を代替する表ではない。\n\n'+table(['内容区分','条件・設定'],[[r['kind'],r['text']] for r in e['rules']])+'\n'
        if db:text+='**参照・変更するデータ**\n\n'+table(['対象','操作'],[[obj,OPS.get(op,op)] for obj,op in db])+'\n'
        messages=event_messages(e,data)
        if messages:text+='**確認・警告・結果通知**\n\n'+table(['区分','文面'],messages)+'\n'
        eg=['flowchart LR',f' E["{q(title)}"]']
        for j,(obj,op) in enumerate(db):
            eg.append(f' D{j}[("{q(obj)}")]');eg.append(f' D{j} -->|参照| E' if op=='R' else f' E -->|{q(OPS.get(op,op))}| D{j}')
        for j,target in enumerate(e['transitions']):
            eg.append(f' E --> T{j}["{q(byclass[target]["name"] if target in byclass else "連携先確認")}"]')
        if not db and not e['transitions']:eg.append(' E --> V["表示状態・受渡し情報を反映"]')
        if e.get('deferred_callbacks'):eg.append(' E -. 登録のみ .-> C["後続イベントの処理"]')
        text+='**イベント関連図**\n\n'+mermaid(eg)+'\n'
        if e['unresolved']:text+=f"**未確定事項**：関連する条件・値設定のうち{len(e['unresolved'])}箇所は、業務上の解釈と分岐後の結果の確認を要する。原本表記は根拠一覧に保存している。\n\n"
        audit.append({'event':e['id'],'name':title,'path':e['path'],'line':e['line'],'end':e['end'],'rules':e['rules'],'unresolved':e['unresolved'],'methods':e['methods'],'db':e['db']})
    unknown=sum(i['db_status']=='unresolved' for i in f['items'] if i['role']!='operation')
    f['quality']={'untranslated_rules':total_unresolved,'unresolved_db_items':unknown,'physical_schema_missing':data['system']['physical_schema']=='not_found'}
    text+='## 4. 補足説明\n\n### 4.1 適用する共通仕様\n\n'+link(COMMON,'共通仕様')+'の入力・終了確認・検索・DB更新・帳票の規則を適用範囲に従って参照する。個別機能の例外を優先し、他機能の規則を無条件に流用しない。\n\n'
    text+='### 4.2 注意事項・未確定事項\n\n'+'\n'.join('- '+x for x in f['notes'])+'\n'
    text+=f'- DB列対応が未確定の項目は{unknown}件、業務解釈が未確定の条件・値設定は{total_unresolved}箇所である。\n'
    text+='- 実際の画面配置、キーボード順、動的表示、物理DB制約・DB内処理は未検証である。表示位置やDB資料の欠落を「存在しない」と判定していない。\n'
    text+='- 正常系・境界値・取消・障害時を含めた実装可能性は独立評価で判定する。機械検査の一致だけを完成の根拠にしない。\n\n'
    text+='### 4.3 関連資料\n\n'+' ／ '.join(link(x,x[:-3]) for x in ['メッセージ一覧.md','CRUD図.md','DB定義書.md','DBオブジェクト一覧.md'])+'\n\n'
    text+=link('../report/overview/根拠_'+f['id']+'.md','項目とイベントの根拠')+' ／ '+link('../report/overview/独立評価.md','独立評価結果')+'\n'
    return text,audit
