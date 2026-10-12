"""Run python -m qualitygen; application sources remain read-only."""
from __future__ import annotations
import argparse, json, re, time
from collections import Counter
from pathlib import Path
from html.parser import HTMLParser
import xml.etree.ElementTree as ET
from overviewgen.core import collect,save,load,digest,safe_name
from overviewgen.refine import preflight,refine
from overviewgen.dblineage import enrich
from overviewgen.contexts import apply as contexts
from overviewgen.publish import table,link,COMMON,SYSTEM
from . import catalog,render,pilot
from .profile import DB_CONTRACT
from .ui_components import enrich_layout
from . import semantic_review,spec_revision


class LayoutReader(HTMLParser):
    def __init__(self):super().__init__();self.items=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'data-item' in a:self.items.append(a)


def independent_review(root,data,metrics,registry):
    errors=[];items=events=0
    def problem(fid,rule,detail):errors.append({'feature':fid,'rule':rule,'detail':detail})
    for f,metric in zip(data['features'],metrics):
        fid=f['id'];text=(root/'output'/f['filename']).read_text()
        if any('## '+heading not in text for heading in ['1. システム概要','2. 項目一覧','3. イベント仕様','4. 補足説明']):problem(fid,'CHAPTERS','必須章不足')
        nodes=list(ET.fromstring((root/f['source']).read_text(encoding='utf-8-sig')).iter()) if f['source'].endswith('.xaml') else []
        expected=[]
        for n,node in enumerate(nodes):
            tag=node.tag.split('}')[-1];a={k.split('}')[-1]:v for k,v in node.attrib.items()}
            binding=any('{Binding ' in v for k,v in a.items() if k in {'Text','Content','SelectedValue','SelectedItem','Binding','IsChecked','SelectedDate'})
            col=tag.endswith('Column') and ('Header' in a or 'Binding' in a or tag=='DataGridTemplateColumn')
            if tag in {'TextBox','PasswordBox','ComboBox','DatePicker','CheckBox','RadioButton','ListBox','TreeView'} or tag.endswith('Button') or col or (tag in {'TextBlock','Label'} and binding):expected.append(a.get('Name','node_'+str(n)))
        marked=re.findall(r'<!-- item:(\S+) order:(\d+) role:(\w+) -->',text)
        if Counter(expected)!=Counter(m[0] for m in marked):problem(fid,'ITEM_SOURCE','原本の項目集合と文書が不一致')
        roles={m[0]:m[2] for m in marked}
        for n,node in enumerate(nodes):
            tag=node.tag.split('}')[-1];a={k.split('}')[-1]:v for k,v in node.attrib.items()};key=a.get('Name','node_'+str(n))
            if key not in roles:continue
            visible=a.get('Visibility','Visible')=='Visible'
            if visible and tag.endswith('Button') and roles[key]!='operation':problem(fid,'ITEM_ROLE','ボタンが操作項目として定義されていない：'+key)
            if visible and a.get('IsReadOnly')=='True' and tag=='TextBox' and roles[key]!='display':problem(fid,'ITEM_ROLE','表示専用欄の入力分類：'+key)
        if [int(m[1]) for m in marked]!=list(range(1,len(marked)+1)):problem(fid,'ITEM_ORDER','順番の重複または欠番')
        total=re.search(r'合計：([0-9]+)項目',text)
        if not total or int(total.group(1))!=len(expected):problem(fid,'ITEM_TOTAL','合計が原本と不一致')
        parser=LayoutReader();parser.feed((root/'output'/metric['html']).read_text())
        if Counter(expected)!=Counter(i['data-item'] for i in parser.items):problem(fid,'HTML_ITEMS','HTML項目と原本が不一致')
        for e in f['events']:
            if e['id'] not in text:problem(fid,'EVENT','イベントの文書欠落：'+e['id'])
        for obj in {r['object'] for r in f['db']}:
            logical=registry['objects'].get(obj,{}).get('logical_name',obj)
            diagrams='\n'.join(re.findall(r'```mermaid\n([\s\S]*?)```',text))
            if logical not in diagrams and obj not in diagrams:problem(fid,'DB_DIAGRAM','DB関連図の欠落：'+logical)
        for match in re.finditer(r'(?<!!)\[[^\]]*\]\(([^)]+)\)',text):
            from urllib.parse import unquote
            target=unquote(match.group(1)).split('#')[0]
            if target and not re.match(r'\w+://',target) and not (root/'output'/target).resolve().exists():problem(fid,'LINK','リンク切れ：'+target)
        items+=len(expected);events+=len(f['events'])
    return {'status':'error' if errors else 'review_required','automatic_errors':errors,'features':len(data['features']),'items':items,'events':events,'html_documents':len(metrics),'scope':registry['scope'],'review_required':['論理名・複数用途の顧客承認','未取得DDL・DB内関数と副作用','全イベントの詳細条件と期待結果','HTMLの実画面寸法・動的挙動・フォーカス順','Pilotの全機能再現性'],'independence':'原本XMLは別の読取処理で再列挙。業務の人間承認ではない。'}


def run(root:Path,input_dir='input',cold=False,with_pilot=True):
    started=time.perf_counter();state=root/'.specgen-state/quality';report=root/'report/quality';out=root/'output'
    state.mkdir(parents=True,exist_ok=True)
    before_hash={p.relative_to(root).as_posix():digest(p.read_bytes()) for p in (root/input_dir).rglob('*') if p.is_file() and not p.is_symlink()}
    plan=preflight(root,input_dir);data=collect(root,input_dir,cold);refine(root,data);enrich(data);nested=catalog.quarantine_nested_keys(data);contexts(root,data)
    save(report/'subquery-key-candidates.json',nested)
    for r in data['records'].values():
        for m in r.get('methods',[]):
            key=r['path']+'#'+m['name']+'@'+str(m['line'])
            if key in data['methods']:m.update(data['methods'][key])
    for f in data['features']:render.captions(f,data)
    spec_revision.apply_facts(data)
    registry=spec_revision.normalize_names(catalog.build(data))
    previous=load(state/'ownership.json',{});baseline=load(root/'.specgen-state/overview/ownership.json',{});current={};conflicts=[];written=0
    def put(path,text):
        nonlocal written
        if not path.resolve().is_relative_to(root) or path.is_symlink():raise ValueError('unsafe destination')
        key=path.relative_to(root).as_posix();h=digest(text)
        if path.exists() and digest(path.read_bytes()) not in {h,previous.get(key),baseline.get(key)}:
            if key not in {'output/README.md','output/機能一覧.md'}:conflicts.append(key);return
        written+=int(save(path,text));current[key]=h
        save(state/'ownership.json',{**previous,**current})
    metrics=[]
    save(report/'独立評価.md','# 独立評価\n\n今回の生成結果を評価中。合格を意味しません。\n')
    for f in data['features']:
        text,html_doc,measure=render.feature(f,data,registry)
        text=spec_revision.amend_feature(text,f);measure['after_characters']=len(text)
        html_doc=enrich_layout(html_doc,f,data)
        measure['html']=safe_name(Path(measure['html']).stem)+'.html'
        text=text.replace('../report/overview/独立評価.md','../report/quality/独立評価.md')
        put(out/f['filename'],text);put(out/measure['html'],html_doc);metrics.append(measure)
        save(state/'outlines'/(f['id']+'.json'),f)
    documents=render.shared(data,registry)|render.databases(data,registry)|{'開発規約.md':render.standards(data)}
    if data['system'].get('system_name')=='Tokyo Librarian':
        documents['開発規約.md']+='\n```json\n'+json.dumps({'contract_scope':'development','language':'VB.NET','option_strict':True,'exceptions':'preserve_failure_not_success','database_access':'evaluation_mock_only'},ensure_ascii=False,indent=2)+'\n```\n'
        documents['DB定義書.md']+='\n<details><summary>PilotのDB受渡し契約（物理制約は未確定）</summary>\n\n```json\n'+json.dumps(DB_CONTRACT,ensure_ascii=False,indent=2)+'\n```\n</details>\n'
    documents=spec_revision.amend_shared(documents,data)
    for name,text in documents.items():put(out/name,text)
    for name in ['CRUD図.md']:
        if (out/name).exists():source=(out/name).read_text();put(out/name,render.name_text(source,registry))
    index=['# 機能一覧','','概要仕様とHTML画面レイアウトをファイル名で区別する。表示用のHTMLは実画面と同一寸法・挙動を保証するものではない。','',table(['ID','機能名','概要仕様書','HTMLレイアウト'],[[f['id'],f['name'],link(f['filename'],'仕様書'),link(m['html'],'HTML')] for f,m in zip(data['features'],metrics)]),'','## 横断仕様','']
    index+=['- '+link(n,n[:-3]) for n in [SYSTEM,COMMON,'概要仕様書COM-002_共通関数仕様.md','概要仕様書COM-003_共通UI仕様.md','DB定義書.md','DBオブジェクト一覧.md','メッセージ一覧.md','CRUD図.md','開発規約.md','命名規則.md'] if (out/n).exists()]
    index+=['',link('../report/quality/独立評価.md','独立評価'),link('../pilot/TKL-011/README.md','Pilot総合検証（検証範囲と制限）')]
    put(out/'機能一覧.md','\n'.join(index)+'\n')
    if with_pilot and any(f['id']=='TKL-011' for f in data['features']):pilot.prepare(root,data)
    review=independent_review(root,data,metrics,registry)
    review['visible_content_errors']=semantic_review.review(root,data,registry)
    review['automatic_errors']+=review['visible_content_errors']
    if review['automatic_errors']:review['status']='error'
    review['conflicts']=conflicts
    after_hash={p.relative_to(root).as_posix():digest(p.read_bytes()) for p in (root/input_dir).rglob('*') if p.is_file() and not p.is_symlink()}
    review['input_changed']=[p for p in before_hash if before_hash[p]!=after_hash.get(p)];review['input_file_count']=len(before_hash)
    save(report/'evaluation.json',review)
    body=['# 独立評価 — 横断仕様・HTML・粒度改善','','**状態：'+review['status']+'。機械検査の一致と顧客承認・全機能再現は別の判定である。**','',table(['対象','結果'],[[k,v] for k,v in review.items() if k not in {'automatic_errors','scope'}]),'',table(['機能','規則','不一致'],[[e['feature'],e['rule'],e['detail']] for e in review['automatic_errors']]),'','## 説明量の実測','','イベント箇条書きの文字数は原本から補った責務・条件・更新範囲を対象とする。文書全体の倍率とは別に報告し、文章量だけで仕様の十分性は判定しない。','',table(['機能','変更前全文','変更後全文','イベント箇条書き倍率'],[[m['id'],m['before_characters'],m['after_characters'],m['event_bullet_ratio']] for m in metrics])]
    save(report/'独立評価.md','\n'.join(body)+'\n');save(report/'granularity.json',metrics)
    summary={**data['stats'],'features':len(metrics),'common_functions':len(registry['common']),'db_objects':len(registry['objects']),'written':written,'conflicts':conflicts,'automatic_errors':len(review['automatic_errors']),'review_status':review['status'],'elapsed_seconds':round(time.perf_counter()-started,4),'event_bullet_ratio':round(sum(m['event_bullets_before']+m['event_bullets_added'] for m in metrics)/max(1,sum(m['event_bullets_before'] for m in metrics)),2),'input_unchanged':not review['input_changed']}
    save(report/'実行結果.json',summary)
    save(state/'crosscut.json',json.dumps(registry,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n')
    save(state/'checkpoint.json',{'input_snapshot':data['system']['snapshot_id'],'stage':'documents_generated_native_pilot_pending','summary':summary,'next_command':'python -m qualitygen.native_checks'})
    save(state/'ownership.json',{**previous,**current})
    return summary


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',default='.');parser.add_argument('--input',default='input');parser.add_argument('--cold',action='store_true');parser.add_argument('--finalize-pilot',action='store_true');args=parser.parse_args();root=Path(args.root).resolve()
    if args.finalize_pilot:
        result=pilot.finalize(root);print(json.dumps({k:v for k,v in result.items() if k!='results'},ensure_ascii=False,indent=2));return int(result['failed']>0)
    lock=root/'.specgen-state/quality.lock';lock.parent.mkdir(exist_ok=True)
    with lock.open('x') as stream:stream.write('running\n')
    try:result=run(root,args.input,args.cold)
    finally:lock.unlink(missing_ok=True)
    print(json.dumps(result,ensure_ascii=False,indent=2));return int(bool(result['conflicts'] or result['automatic_errors'] or not result['input_unchanged']))

if __name__=='__main__':raise SystemExit(main())
