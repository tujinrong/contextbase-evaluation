"""P2 document plans from stored semantic facts, not final Markdown strings."""
from __future__ import annotations
import re
import json
from pathlib import Path
RULES=json.loads((Path(__file__).parents[1]/"templates/standard_rules.json").read_text(encoding="utf-8"))
from contextbase.itemlist import HEADERS
from .semantics import explain, field_labels, OPS, public_condition, operation_summary


def table(headers, rows):return {'kind':'table','value':[list(headers),*rows]}
def paragraph(value):return {'kind':'paragraph','value':str(value)}
def heading(value, level=3):return {'kind':'heading','value':value,'level':level}


def cover(name, fid, metadata=None):
    m=metadata or {}
    return {'title':'表紙','blocks':[table(['項目','内容'],[
        ['文書名',m.get('文書名','基本設計書')],['システム名',m.get('システム名','')],
        ['機能ID',m.get('機能ID',fid)],['画面名',name],['会社名',m.get('会社名','')],['作成日',m.get('作成日','')]])]}


def basic_document(model):
    name=model['name'];fid=model['id'];review=model.get('reviewed',{})
    overview=review.get('overview_blocks') or [heading('概要説明'),paragraph(model['summary']),
        table(['情報','内容'],[['対象種別',model['kind']],['開始契機',model.get('route') or '呼出元からの要求'],
                              ['処理対象', '、'.join(model.get('related_data_names',[])) or '入力値・画面状態']])]
    labels={**model.get('field_labels',{}),**field_labels(model['items'])}
    if not review:
        layout=model.get('layout',{})
        if layout.get('images'):
            overview += [heading('画面レイアウト'),paragraph('原本HTML・CSSの静的再構成。実行時の表示条件・値は未実行（仮定 '+layout.get('qa_id','')+'）。'),*layout['images']]
        stores=model.get('storage_catalog',[])
        if stores:
            overview += [heading('処理対象データ'),paragraph('物理DB表と、メモリーに保持する論理データを分ける。メモリー上の保存をDBへの永続化とは扱わない。'),
                table(['データID','論理名','保持方式','データ構造'],[[x['id'],x['name'],'メモリー' if x['kind']=='memory' else 'ORM実体（物理定義は別確認）',x['element_type']] for x in stores])]
        if model.get('data_diagram'):overview += [heading('データ操作関連図'),model['data_diagram']]
    item_keys=['number','group','name','type','io','db','choices','required','format','description']
    itemrows=[[str(row.get(k,'')) for k in item_keys] for row in model['items']]
    items=[table(HEADERS,itemrows)]
    items += [paragraph(x) for x in review.get('item_notes',[]) or [f"項目定義数：{len(itemrows)}項目。表示順と反復行の定義数を区別する。"]]
    blocks=[]
    for event in model['events']:
        blocks.append(heading(event['name']))
        if event.get('sections'):
            for section in event['sections']:
                blocks.append(heading(section['title'],4))
                blocks.extend(paragraph(str(i+1)+'. '+p) for i,p in enumerate(section.get('paragraphs',[])))
                blocks.extend({'kind':'table','value':t} for t in section.get('tables',[]))
        else:
            narrative=event.get('narrative')
            if narrative:
                blocks += [heading(RULES['event_sections'][0],4),paragraph(narrative['summary']),heading(RULES['event_sections'][1],4)]
                for i,step in enumerate(narrative['steps'],1):blocks.append(paragraph(str(step.get('number',i))+'. '+step['description'].rstrip('。')+'。'))
                if event.get('flow_images'):blocks += [heading(RULES['event_sections'][2],4),paragraph(narrative['scope']),*event['flow_images']]
                if event.get('er_images'):blocks += [heading(RULES['event_sections'][3],4),paragraph(event['er_model']['legend']),*event['er_images']]
                if event.get('sql_operations'):
                    from .database import operation_blocks
                    blocks.append(heading(RULES['event_sections'][4],4))
                    for q in event['sql_operations']:blocks.extend(operation_blocks(q,public=True))
            else:
                blocks.append(paragraph(event['description']))
                for i,step in enumerate(event.get('public_steps',[]),1):blocks.append(paragraph(str(i)+'. '+step))
            if narrative and narrative.get('outcomes'):
                blocks += [heading(RULES['event_sections'][6],4),table(['到達条件','結果'],[[o['condition'],o['result']] for o in narrative['outcomes']])]
            rules=event.get('validation_rules',[])
            if rules:
                blocks += [heading('入力条件・エラー',4),table(['対象項目','エラーになる条件（原本から導出）','表示メッセージ'],[[r['label'],public_condition(' / '.join(r['guards']),event,labels),r['message']] for r in rules])]
            effects=event.get('storage_effects',[])
            if effects:
                blocks += [heading('データの検索・登録・更新・削除',4),table(['対象','操作','実行条件','照合・設定内容'],[[r['store']+('（メモリー）' if r['kind']=='memory' else ''),OPS.get(r['operation'],r['operation']),public_condition(' / '.join(g for g in r['guards'] if g not in r.get('lock_expressions',[])),event,labels) or '当該処理へ到達した場合',operation_summary(r,event,labels)] for r in effects])]
                if any(r.get('lock_expressions') for r in effects):blocks.append(paragraph('原本でロックが指定された対象（'+'・'.join(dict.fromkeys(r['store'] for r in effects if r.get('lock_expressions')))+'）は、その範囲内で操作する。プロセス内の排他であり、DBのコミット・ロールバックとは区別する。'))
            if event.get('data_rules'):
                blocks += [heading('照合・保存値の設定規則',4),table(['対象','処理規則'],[[r['target'],r['rule']] for r in event['data_rules']])]
    if not review and model.get('client_events'):
        blocks.append(heading('画面上の入力補助・確認操作'))
        for e in model['client_events']:
            blocks += [heading(e['name'],4)]
            if e['confirmation']:blocks.append(paragraph('確認ダイアログを表示し、利用者の選択を受け付ける。'))
            if e['cancellation_return']:blocks.append(paragraph('確認に同意しなかった場合は、そのイベントの後続処理へ進まない。'))
            if e['request_submit']:blocks.append(paragraph('確認成立時に対応するフォームの送信処理を呼び出す。'))
            blocks += [table(['検出した画面側条件'],[[explain(c,labels)] for c in e['conditions']]),table(['表示メッセージ'],[[m] for m in e['messages']])]

    if model.get('sql_operations'):
        from .database import operation_blocks
        blocks.append(heading('DB関連処理'))
        shown={q['id'] for e in model['events'] if e.get('narrative') for q in e.get('sql_operations',[])}
        for operation in model['sql_operations']:
            if operation['id'] not in shown:blocks.extend(operation_blocks(operation,public=True))
    if not blocks:blocks=[paragraph('本資料はデータ定義または共通構造を示す。操作イベントは関連機能の仕様を参照する。')]
    supplements=review.get('supplement_blocks') or [heading('適用条件'),paragraph(model['scope_note'])]
    notes=[[str(i['number']),i['name'],i['binding_remarks']] for i in model['items'] if i.get('binding_remarks')]
    if notes:
        supplements += [heading(RULES['binding_notes_heading']),paragraph('表示元と保存先は別方向の対応。DBから読み出した既存データの履歴保存は、画面入力の直接バインド先と区別する。同じ列の複数経路はイベントの実行条件に従う。'),table(['No','項目名','備考'],notes)]
    unresolved=[[e['name'],n.get('id','例外'),n.get('expression','')] for e in model['events'] for n in e.get('narrative',{}).get('notes',[])]
    if unresolved:supplements += [heading('処理・条件の原本対応'),paragraph('文書内の条件番号・処理番号は次の原本表記に対応する。完全な業務用語への置換を行っていない箇所はQA・reportで確認する。'),table(['イベント','参照番号','原本条件・処理'],unresolved)]
    return {'title':name,'sections':[cover(name,fid,review.get('metadata')),{'title':'概要','blocks':overview},
            {'title':'項目一覧','blocks':items},{'title':'イベント仕様','blocks':blocks},
            {'title':'補足説明','blocks':supplements}]}


def detail_document(model):
    blocks=[]
    for event in model['events']:
        blocks.append(heading(event['name']))
        for method in event.get('methods',[]):
            blocks.append(heading(method['name']+'：'+method['path'],4))
            blocks.append(table(['順番','分類','条件・ガード','処理・設定内容','根拠行'],
                [[str(i+1),n['kind'],' / '.join(n.get('guards',[])),n.get('condition') or n.get('expression',''),str(n['line'])] for i,n in enumerate(method['steps'])]))
    blocks += [heading('データ関連'),table(['種別','対象','操作','根拠'],
                  [[r.get('kind',''),r.get('store',''),r.get('operation',''),r.get('event','')] for r in model['data_relations']])]
    scenarios=table(['ID','入力・条件','期待結果'],[[s['id'],s['input'],s['expected']] for s in model['scenarios']])
    return {'title':model['name']+' 詳細仕様','sections':[{'title':'概要','blocks':[paragraph(model['summary'])]},
            {'title':'処理詳細','blocks':blocks},{'title':'検証シナリオ','blocks':[scenarios]}]}


def common_documents(system, database, features, messages):
    docs=[]
    def add(path,title,blocks):docs.append({'path':path,'model':{'title':title,'sections':[{'title':'概要','blocks':blocks}]}})
    add('共通/システム分析.md','システム分析',[table(['技術','件数'],[[k,str(v)] for k,v in system['languages'].items()]),
        paragraph('対象案件：'+system['project']+'。機能と処理を分けて基盤解析・詳細解析を実施する。')])
    add('共通/データオブジェクト定義書.md','データオブジェクト定義書',[
        paragraph('以下はプログラム内のデータ構造であり、物理DBテーブルではない。'),
        *[block for d in database['data_objects'] for block in [heading(d['name']),table(['項目','宣言型','宣言必須','根拠行'],[[f['name'],f['type'],str(f.get('required')),str(f['line'])] for f in d['fields']])]]])
    if database.get('logical_stores'):
        add('共通/論理データ・保存先一覧.md','論理データ・保存先一覧',[
            paragraph('原本に宣言された保持領域を、物理DB定義とは別に整理する。名称は型名またはレビュー済み用語対応に基づく。'),
            table(['ID','名称','保持方式','データ構造','原本'],[[x['id'],x['name'],x['kind'],x['element_type'],x['path']+':'+str(x['line'])] for x in database['logical_stores']])])
    add('共通/DBオブジェクト一覧.md','DBオブジェクト一覧',[table(['種別','名称','根拠','状態'],[[o['kind'],o['name'],o['path'],o['status']] for o in database['objects']]),paragraph('未検出は、稼働環境に存在しないことの保証ではない。')])
    add('共通/メッセージ一覧.md','メッセージ一覧',[table(['ID','内容','根拠','表示条件の扱い'],[[m['id'],m['text'],m['path']+':'+str(m['line']),m['condition']] for m in messages])])
    add('共通/データ操作一覧.md','データ操作一覧',[paragraph('CRUDはSQLとセッション・メモリー操作を分ける。静的に解決した範囲を示す。'),table(['機能','保持先種別','対象','操作'],[[f['name'],r['kind'],r['store'],r['operation']] for f in features for r in f['data_relations']])])
    return docs
