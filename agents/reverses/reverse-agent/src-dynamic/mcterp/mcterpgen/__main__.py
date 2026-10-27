"""Analyze current MCTERP sources, write canonical MD and verifiable scope records."""
from __future__ import annotations
from pathlib import Path
from collections import Counter
from html.parser import HTMLParser
import argparse,json,time,re
from .model import collect
from .scan import sha,VueReader
from .render import feature,filename,title,table,link,common
from .contracts import shared
from .ui_state import separate,describe


def save(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    s=data if isinstance(data,str) else json.dumps(data,ensure_ascii=False,indent=2)+'\n'
    if p.exists() and p.read_text(encoding='utf-8')==s:return False
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(s,encoding='utf-8');tmp.replace(p);return True


class Layout(HTMLParser):
    def __init__(self):super().__init__();self.ids=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'data-item' in a:self.ids.append(a['data-item'])


def validate(root,d):
    errors=[];items=0;bindings=0
    for g in d['features']:
        p=root/'output/md/基本設計書'/filename(g);text=p.read_text();parser=Layout();parser.feed(text)
        if g['key']=='HrEmployee':
            from .employee_external import validate as validate_external
            from .employee_contract import contract,fields
            from .employee_layout import screens
            views,_,columns=screens(root,fields());external=validate_external(root,text,contract(views,columns))
            errors.extend({'feature':g['id'],'rule':'external_specification','detail':x} for x in external['errors'])
            items+=sum(len(s['items']) for s in g['screens']);bindings+=sum(len(s['events']) for s in g['screens'])
            continue
        expected=[i['id'] for s in g['screens'] for i in s['items']]
        if Counter(expected)!=Counter(parser.ids):errors.append({'feature':g['id'],'rule':'layout_item_identity'})
        if len(set(parser.ids))!=len(parser.ids):errors.append({'feature':g['id'],'rule':'duplicate_layout_id'})
        for heading in ['1. システム概要','2. 項目一覧','3. イベント仕様','4. 補足説明']:
            if '## '+heading not in text:errors.append({'feature':g['id'],'rule':'required_chapter','detail':heading})
        from markdown_it import MarkdownIt
        tokens=MarkdownIt('commonmark').enable('table').parse(text);current=[];rows=[]
        for tok in tokens:
            if tok.type=='tr_open':current=[]
            elif tok.type=='inline':current.append(tok.content)
            elif tok.type=='tr_close':rows.append(list(current));current=[]
        itemrows=[r for r in rows if len(r)==7 and r[0].isdigit()]
        if len(itemrows)!=len(expected):errors.append({'feature':g['id'],'rule':'visible_item_rows','expected':len(expected),'actual':len(itemrows)})
        from bs4 import BeautifulSoup
        for screen in g['screens']:
            soup=BeautifulSoup((root/screen['path']).read_text(encoding='utf-8-sig'),'html.parser')
            for node in soup.find_all(['script','style']):node.decompose()
            events=sum(1 for node in soup.find_all(True) for k in node.attrs if k.startswith(('@','v-on:')))
            if events!=len(screen['events']):errors.append({'feature':g['id'],'rule':'source_event_count','path':screen['path'],'source':events,'index':len(screen['events'])})
        items+=len(expected);bindings+=sum(len(s['events']) for s in g['screens'])
    for p in (root/'output/md').rglob('*.md'):
        if 'TKL-' in p.read_text() or 'Tokyo Librarian' in p.read_text():errors.append({'rule':'old_project_contamination','path':str(p)})
    return {'status':'partial_static_review' if not errors else 'error','errors':errors,'features':len(d['features']),'screen_components':len(d['screens']),'items':items,'event_bindings':bindings,'scope':'原本イベントの別パーサ列挙、本文行数、レイアウトID、章、旧案件混入を照合。業務意味の完全性・稼働DBの検証ではない。','implementation_readiness':'保留：実行時条件・未対応資源・動的経路の追加確認が必要','native_pilot':{'status':'not_run','reason':'新案件の再実装比較は未作成。旧TKLの416ケースを新案件の合格に流用しない'}}


def run(root,input_dir='input',cold=False):
    start=time.perf_counter();d=collect(root,input_dir,cold);separate(d);out=root/'output/md';report=root/'report/mcterp';written=0
    if not d['features']:raise ValueError('No business features extracted')
    if d['stats']['errors']:raise ValueError('Source parser failures: '+str(d['stats']['errors']))
    rows=[[g['id'],title(g),g['kind'],len(g['screens']),link('基本設計書/'+filename(g),'概要仕様書')] for g in d['features']]
    index='# 機能一覧 — MCTERP\n\nサービス境界を基本に、画面・子部品を関連付けた静的解析版。API専用、バッチ、共通ダイアログ、モバイルは区分して記録する。\n\n'+table(['ID','機能名','種別','画面・子部品数','仕様書'],rows)
    written+=save(out/'機能一覧.md',index)
    for g in d['features']:
        if g['key']=='HrEmployee':
            from .employee_external import generate as external_generate
            text=external_generate(root)
        else:text=describe(feature(root,g,d),g)
        written+=save(out/'基本設計書'/filename(g),text)
        summary={k:v for k,v in g.items() if k!='shapes'}
        save(root/'.specgen-state/mcterp/outlines'/(g['id']+'.json'),summary)
    docs=common(root,d)|shared(root,d)
    for name,text in docs.items():written+=save(out/'共通'/name,text)
    index+='\n## 横断仕様\n\n'+'\n'.join('- '+link('共通/'+name,name[:-3]) for name in docs)+'\n\n解析対象と未対応範囲は `report/mcterp/解析範囲.md`、検査結果は同フォルダの `独立評価.md` を参照。\n'
    save(out/'機能一覧.md',index)
    evaluation=validate(root,d)
    if (root/'report/employee-pilot/evaluation.json').exists():
        evaluation['employee_external_pilot']=json.loads((root/'report/employee-pilot/evaluation.json').read_text())
        evaluation['item_count_scope']='itemsは従来の静的抽出件数。社員マスタの外部定義数はemployee_external_pilot.definition_itemsに分離。'
    after={p.relative_to(root).as_posix():sha(p.read_bytes()) for p in (root/input_dir).rglob('*') if p.is_file() and not p.is_symlink()}
    before={r['path']:r['sha256'] for r in d['inventory']};evaluation['input_unchanged']=before==after
    if before!=after:evaluation['errors'].append({'rule':'input_changed'})
    save(report/'evaluation.json',evaluation);save(report/'inventory.json',d['inventory']);save(report/'api-unresolved.json',d['unresolved_api']);save(report/'workbooks.json',d['workbooks'])
    scope='# 解析範囲 — MCTERP\n\n原本ファイル数：'+str(len(d['inventory']))+'。すべての通常ファイルの内容ハッシュを記録し、処理状態を区別した。ハッシュ取得や構造確認を全仕様の解析とみなさない。\n\n'+table(['状態','件数'],list(d['stats']['statuses'].items()))+'\n## ファイルごとの扱い\n\n'+table(['ファイル','状態','扱い'],[[r['path'],r['status'],r['reason']] for r in d['inventory']])+'\n## 制限\n\nExcel・マクロ帳票はシート構造のみ。画像・鍵・フォント・ビルド成果物は業務仕様の解析対象にしない。SQLデータ行は出力しない。DBダンプは復元せずDDLだけを読み、保存時点と稼働時点を区別する。静的に結べないAPI・共通関数・DB名は未確定である。\n'
    save(report/'解析範囲.md',scope)
    summary={**d['stats'],**d['render_counts'],'features':len(d['features']),'screen_components':len(d['screens']),'items':evaluation['items'],'event_bindings':evaluation['event_bindings'],'tables':len(d['tables']),'table_columns':sum(len(t['columns']) for t in d['tables'].values()),'sql_routines':len(d['routines']),'methods':len(d['methods']),'schema_snapshot':d['active_schema_snapshot'],'markdown_documents':len(list(out.rglob('*.md'))),'written':written,'elapsed_seconds':round(time.perf_counter()-start,3),'status':evaluation['status'],'input_unchanged':before==after,'validation_errors':len(evaluation['errors']),'native_pilot':'not_run_for_new_project'}
    save(report/'result.json',summary)
    save(report/('metrics-cold.json' if cold else 'metrics-warm.json'),summary)
    save(report/'独立評価.md','# 独立評価 — MCTERP\n\n**静的構造の照合結果。機能全体の再実装・実画面・実DBの検証は保留。**\n\n'+table(['項目','結果'],[[k,v] for k,v in summary.items() if k not in {'errors','statuses'}])+'\n'+table(['規則','指摘'],[[e.get('rule'),json.dumps(e,ensure_ascii=False)] for e in evaluation['errors']])+'\n\n旧TKLの名称・説明・Pilot結果は使用しない。未解決APIは api-unresolved.json、全ファイルの扱いは解析範囲.md、基礎抽出と表示変換の検証はreport/rebuildとreport/docsiteを参照。\n')
    save(root/'.specgen-state/mcterp/index.json',{'schema_version':1,'input_hashes':before,'features':[{'id':g['id'],'name':title(g),'files':g['files']} for g in d['features']],'api_contracts':d['apis'],'calls':d['graph'],'schema_snapshot':d['active_schema_snapshot'],'cache_contains_source_fragments':True})
    if evaluation['errors']:raise ValueError('Independent structural check failed: '+str(evaluation['errors'][:12]))
    return summary


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',default='input');p.add_argument('--cold',action='store_true');args=p.parse_args();print(json.dumps(run(Path.cwd(),args.input,args.cold),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
