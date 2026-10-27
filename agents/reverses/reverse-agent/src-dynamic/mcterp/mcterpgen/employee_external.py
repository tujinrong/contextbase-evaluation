"""Employee pilot orchestration. Preserve original input and unrelated features."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from contextbase.external_spec import render,mdtable,validate_contract
from .employee_layout import screens,PREFIX
from .employee_contract import fields,contract

FILENAME='概要仕様書MCT-HrEmployee_社員管理.md'
EVIDENCE=Path(__file__).with_name('employee_evidence.json')


def write(p:Path,text):
    if not isinstance(text,str):text=json.dumps(text,ensure_ascii=False,indent=2)+'\n'
    if p.exists() and p.read_text(encoding='utf-8')==text:return False
    p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_suffix(p.suffix+'.tmp');temp.write_text(text,encoding='utf-8');temp.replace(p);return True


def validate(root:Path,text:str,spec:dict)->dict:
    if '<!-- employee-db:events -->' in text:
        from .employee_db import audit_document
        return audit_document(text,render(spec))
    errors=[];validate_contract(spec)
    expected=[i for g in spec['item_groups'] for i in g['items']]
    tokens=MarkdownIt('commonmark',{'html':True}).enable('table').parse(text);rows=[];current=None
    for t in tokens:
        if t.type=='tr_open':current=[]
        elif t.type=='inline' and current is not None:current.append(t.content)
        elif t.type=='tr_close':
            if current and re.fullmatch('[SLFB][0-9]+',current[0]):rows.append(current)
            current=None
    if len(rows)!=len(expected):errors.append('項目表の表示行数')
    for actual,wanted in zip(rows,expected):
        if len(actual)!=7 or actual[:3]!=[wanted['number'],wanted['label'],wanted['type']]:errors.append('項目表の名称・順番・タイプ：'+wanted['number'])
        elif actual[3:]!=[wanted[k] for k in ['data','required','length','description']]:errors.append('項目表の定義値：'+wanted['number'])
    if f'固定項目の定義数：{len(expected)}項目' not in text:errors.append('合計件数')
    for e in spec['events']:
        if '### '+e['id']+' '+e['name'] not in text:errors.append('イベント節欠落：'+e['id'])
        for k in ['input','output','failure','example']:
            if e[k] not in text:errors.append('イベントIO・異常・例欠落：'+e['id'])
        if not all(x in text for x in e['steps']):errors.append('処理順の欠落：'+e['id'])
    soup=BeautifulSoup(text,'html.parser')
    for s in spec['screens']:
        view=soup.select_one('[data-screen="'+s['id']+'"]')
        if not view:errors.append('画面欠落：'+s['id']);continue
        frame=view.select_one('.ext-screen')
        if frame is None or frame.get('data-width')!=str(s['width']):errors.append('画面幅：'+s['id'])
        if s.get('modal'):
            tabs=[x.get_text() for x in view.select('.ext-tab')]
            if tabs!=s['tabs']:errors.append('タブ順：'+s['id'])
            labels=[x.get_text() for x in view.select('.ext-footer button')]
            want=[x['label'] for x in s['buttons']]+([s['delete']['label']] if s.get('delete') else [])
            if labels!=want:errors.append('状態別ボタン：'+s['id'])
    source=BeautifulSoup((root/PREFIX/'HrEmployeeList.vue').read_text(encoding='utf-8-sig').split('<script',1)[0],'html.parser')
    headers=[x['title'] for x in source.find_all('vxe-column') if x.get('title') and x.get('width')]
    actual=[x.get_text() for x in soup.select('[data-screen=employee-list] .ext-grid th')]
    if headers!=actual:errors.append('一覧列の原本順序')
    return {'status':'passed_static_contract' if not errors else 'failed','errors':errors,'definition_items':len(expected),'events':len(spec['events']),'layout_states':len(spec['screens']),'fixed_list_columns':len(headers),'runtime_application_tested':False,'pixel_match_to_live_application':'not_measured','full_implementation_readiness':'review_required'}


def generate(root:Path)->str:
    if not EVIDENCE.exists():raise ValueError('Reviewed source manifest is absent')
    evidence=json.loads(EVIDENCE.read_text(encoding='utf-8'));changed=[]
    for rel,h in evidence['sources'].items():
        p=root/rel
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=h:changed.append(rel)
    if changed:raise ValueError('Reviewed employee contract is stale; review changed source before applying: '+', '.join(changed))
    views,trace,columns=screens(root,fields());spec=contract(views,columns);text=render(spec);result=validate(root,text,spec)
    report=root/'report/employee-pilot'
    write(report/'source-evidence.json',evidence);write(report/'layout-trace.json',trace);write(report/'external-contract.json',spec);write(report/'evaluation.json',result)
    doc=['# 社員マスタPilot：外部仕様・画面配置の検証','','**原本定義に対する静的復元の検査です。稼働画面とのピクセル一致、業務アプリの再実装・実API／DBの同等性は未測定です。**','',mdtable(['対象','結果'],[[k,v] for k,v in result.items() if k!='errors']),'','## 改善内容','','一律の項目再配置を止め、原本の行・24分割列・入れ子・グループ・一覧幅・タブ・モード条件を中立な画面ツリーへ変換しました。基本情報は3列、姓名の分割、住所の複合配置、退職日の条件表示、閲覧の値表示を区別します。確認用HTMLは画面幅を保持し、狭い文書領域で横スクロールさせます。','','基本設計書本文は利用者の入力、処理順、結果、データの関連、項目と表示条件に限定しました。物理名、関数、属性式、実装の問題箇所は本検証資料と原本リンクへ分離しました。','','## 対象範囲と再利用','','汎用の外部仕様・レイアウト描画と契約検査はsrc/contextbase/external_spec.py。Vue変換と社員固有の業務定義はsrc-dynamic/mcterpに分離。現在の適用範囲は社員マスタPilotのみ。他88機能へ同じ業務説明を流用しません。本人情報画面・無効な代替フォームはこのPilotの稼働画面として数えません。','','## 原本との差異・未確認事項','','氏名重複の検証先、メールの本人除外、新規フリー項目の社員参照、保存戻り値と画面終了順、削除後の関連データ、取込の固定補正・行範囲・部分更新は追加確認が必要です。固定補正に含まれる実名・値は本資料へ転載しません。給与の固定サンプル値も社員データの確定仕様へ転用していません。','',mdtable(['外部仕様の確認事項','利用者への影響'],[[x[1],x[2]] for x in spec['findings']]),'','## 原本根拠（承認済みではなく、今回レビューした版）','']
    for rel in evidence['sources']:doc.append('- ['+Path(rel).name+'](../../'+rel.replace(' ','%20')+')')
    doc+=['','## 方式の参考','','[Vue条件付き描画](https://vuejs.org/guide/essentials/conditional.html)に従い、表示されない条件分岐を通常項目へ混在させません。[W3Cフォームのグループ化](https://www.w3.org/WAI/tutorials/forms/grouping/)を参考にラベルと領域を保持します。参考資料は業務仕様の根拠ではなく、表示復元方式の補強です。確認日：2026-10-05。']
    write(report/'検証結果.md','\n'.join(doc)+'\n')
    if result['errors']:raise ValueError(str(result['errors']))
    from .employee_db import enhance
    return enhance(root,text)


def publish(root:Path)->dict:
    dest=root/'output/md/基本設計書'/FILENAME;before=hashlib.sha256(dest.read_bytes()).hexdigest() if dest.exists() else None
    write(dest,generate(root))
    return {'path':str(dest.relative_to(root)),'before_sha256':before,'after_sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}

if __name__=='__main__':print(json.dumps(publish(Path.cwd()),ensure_ascii=False,indent=2))
