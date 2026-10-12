"""Final publication, preserving old basic designs and hand-edited new files."""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
from .core import save,load,digest
from .customer import render, OPS
from .publish import table,link,mermaid,q,db_catalog,message_catalog,common_document,COMMON,SYSTEM,KINDS


def publish(root:Path,data):
    state=root/'.specgen-state/overview';out=root/'output';report=root/'report/overview'
    previous=load(state/'ownership.json',{});owned={};conflicts=[];written=0
    def put(path,text):
        nonlocal written
        if not path.resolve().is_relative_to(root) or path.is_symlink():raise ValueError('unsafe output path')
        key=path.relative_to(root).as_posix();expected=digest(text)
        if path.exists():
            actual=digest(path.read_bytes())
            if key in previous and actual not in {previous[key],expected}:conflicts.append(key);return
            if key not in previous and path.parent==out and path.name not in {'README.md','機能一覧.md'} and actual!=expected:conflicts.append(key);return
        written+=int(save(path,text));owned[key]=expected
        save(state/'ownership.json',{**previous,**owned})
    # Create the actual review target before checking cross-document links. This
    # text is explicitly in-progress and is replaced by the independent reviewer.
    if not (report/'独立評価.md').exists():save(report/'独立評価.md','# 独立評価\n\n評価処理を実行中。未判定。\n')
    for f in data['features']:
        text,audit=render(f,data);put(out/f['filename'],text)
        evidence=['# '+f['id']+' 原本との対応','','プログラムの表記は顧客向け本文と分離する。以下はソース調査の証跡であり、業務仕様の承認を意味しない。','',table(['項目ID','画面項目','役割','出典','値対応'],[[i['key'],i['name'],i['role'],link('../../'+i['path']+'#L'+str(i['line']),str(i['line'])),i['binding']] for i in f['items']])]
        for e in audit:
            evidence+=['','## '+e['event']+' '+e['name'],link('../../'+e['path']+'#L'+str(e['line'])+'-L'+str(e['end']),'イベントの原本'),'']
            for mid in e['methods']:
                m=data['methods'][mid];evidence += [link('../../'+m['path']+'#L'+str(m['line'])+'-L'+str(m['end']),m['name'])]
            evidence+=['',table(['行','種別','原本表記','業務上の内容'],[[r['line'],r['kind'],r['raw'],r['text']] for r in e['rules']+e['unresolved']])]
        put(report/('根拠_'+f['id']+'.md'),'\n'.join(evidence)+'\n');save(state/'outlines'/(f['id']+'.json'),f)
    index=['# 機能一覧','','全39画面の旧基本設計書は比較用に保持し、新しい概要仕様書はファイル名で区別する。機能数は下表の現行検出結果を参照。','',table(['機能ID','種別','機能名','概要仕様書','状態'],[[f['id'],KINDS.get(f['kind'],f['kind']),f['name'],link(f['filename'],'開く'),'顧客確認用・独立評価参照'] for f in data['features']]),'','## 共通・補助仕様書','']
    supplements=[(SYSTEM,'システム分析'),(COMMON,'共通仕様'),('メッセージ一覧.md','メッセージ一覧'),('CRUD図.md','CRUD図'),('DB定義書.md','DB定義書'),('DBオブジェクト一覧.md','DBオブジェクト一覧')]
    index+=['- '+link(name,label) for name,label in supplements]
    index+=['',link('../report/overview/独立評価.md','独立評価結果')]
    put(out/'機能一覧.md','\n'.join(index)+'\n')
    put(out/'README.md','# ソースから生成した仕様書\n\n'+link('機能一覧.md','現行の概要仕様書・共通仕様書・DB資料の一覧')+'\n\n旧基本設計書はTKL/配下に保持。新しい概要仕様書の品質状態は独立評価を参照。\n')
    if data['system'].get('system_name')=='Tokyo Librarian':common=common_document(data)
    else:common='# 共通仕様\n\n## 1. システム概要\n共通規則の業務解釈は未確認。\n\n## 2. 項目一覧\n共通項目は調査証跡を参照。\n\n## 3. イベント仕様\n案件固有の条件を確認して定義する。他案件の規則を流用しない。\n\n## 4. 補足説明\n実装可能性は保留。\n'
    put(out/COMMON,common)
    s=data['system'];sys=['# システム分析 — 概要仕様書','','## 1. システム概要','',table(['項目','確認結果'],[['システム名',s['system_name']],['顧客',s['customer']],['作成者',s['author']],['業務',s['business']],['開発言語・画面方式','、'.join(k+' '+str(v)+'ファイル' for k,v in s['languages'].items())],['対象機能数',len(data['features'])],['物理DB定義','DDLあり' if s['physical_schema']=='present' else '原本内で未確認'],['入力の版',s['input_tree']]]),'','## 2. 項目一覧','','システム名・顧客・作成者・業務区分は明示された原本から取得する。記載がない値は未確認とし、コミット所有者から製品作成者を推定しない。','','## 3. イベント仕様','','システム事前分析 → 対応アダプター選択 → 原本の解析 → 呼出・項目・DBの索引 → 機能骨子 → 概要仕様書 → 独立評価の順で処理する。',mermaid(['flowchart LR',' A["システム事前分析"] --> B["言語・画面・DBの解析"]',' B --> C["機能・項目・処理・共通の骨子"]',' C --> D["概要仕様書一式"]',' D --> E["独立評価"]']),'','## 4. 補足説明','','この版の言語アダプターは限定的な静的解析であり、全言語の型解決・動的呼出し・DB内部処理を解決するものではない。実画面・DB・外部連携は動作させていない。事前分析の結果と選択アダプターは中間結果に保存する。']
    put(out/SYSTEM,'\n'.join(sys)+'\n')
    objects=db_catalog(data);objects.pop('WITH',None);data['db_objects']=objects
    objectrows=[];db=['# DB定義書','','**ソースからの推定版。物理DBの確定定義ではない。** DDLがない場合、UIの必須・長さ・変数型からDBのNOT NULL・サイズ・主キー・外部キーを確定しない。ビュー・関数・トリガーの内部は未取得。']
    for name,v in objects.items():
        kind={'table_or_view':'テーブル／ビュー（種別未確定）','function':'関数','sequence':'シーケンス','table':'テーブル宣言'}[v['kind']]
        # Explicit lineage supplies logical observations, never physical DDL.
        logical=defaultdict(set)
        for f in data['features']:
            for item in f['items']:
                for mp in item['db']:
                    if mp['object']==name:logical[mp['column']].add(item['name']+'：'+item['type'])
        objectrows.append([name,kind,'宣言あり' if v['definition']=='declaration' else 'ソース使用箇所から推定','／'.join(OPS.get(op,op) for op in v['operations']),len(v['columns'])])
        db+=['','## '+name,'','種別：'+kind+'。使用元：'+str(len(v['sources']))+'ファイル。','',table(['列名','論理的な用途・値の種類','物理型','NULL','長さ','キー','定義の根拠'],[[c,'、'.join(sorted(logical.get(c,[]))) or '追加確認',d['type'],d['nullable'],d['length'],d['key'],d['origin']] for c,d in sorted(v['columns'].items())])]
        if v['sources']:db+=['出典：'+' ／ '.join(link('../'+p,Path(p).name) for p in v['sources'])]
    put(out/'DBオブジェクト一覧.md','# DBオブジェクト一覧\n\n名前だけでテーブル・ビュー・ワークの実体や制約を確定しない。未検出を不存在とみなさない。\n\n'+table(['物理名','種別','根拠区分','観測操作','列候補数'],objectrows))
    put(out/'DB定義書.md','\n'.join(db)+'\n')
    crud=['# CRUD図','','C：追加、R：参照、U：更新、D：削除。COPY（取込）・TRUNCATE（全件消去）は別操作。後続イベントの登録だけで更新が実行されたとは扱わない。関数・トリガー等の内部副作用は未確定。','',table(['機能ID','機能名','対象','操作','関連付け'],[[f['id'],f['name'],obj,'／'.join(sorted({r['operation'] for r in f['db'] if r['object']==obj})),'イベントから到達／個別候補は骨子参照'] for f in data['features'] for obj in sorted({r['object'] for r in f['db']})])]
    for f in data['features']:
        lines=['flowchart LR',f' F["{q(f["id"]+" "+f["name"])}"]']
        for n,obj in enumerate(sorted({r['object'] for r in f['db']})):
            ops=sorted({r['operation'] for r in f['db'] if r['object']==obj});lines.append(f' D{n}[("{q(obj)}")]')
            if 'R' in ops:lines.append(f' D{n} -->|参照| F')
            w=[x for x in ops if x!='R']
            if w:lines.append(f' F -->|{q("・".join(OPS.get(x,x) for x in w))}| D{n}')
        crud+=['','## '+f['id']+' '+f['name'],mermaid(lines)]
    put(out/'CRUD図.md','\n'.join(crud)+'\n')
    messages=message_catalog(data);data['messages']=messages
    put(out/'メッセージ一覧.md','# メッセージ一覧\n\n共通定義・個別表示・文面組立候補を分けている。断片を完全な文面とみなさず、発生条件・回答後の処理は各イベントも参照する。外部ライブラリ内部と動的な置換値は未確定。\n\n'+table(['ID','区分','文面・確認できた断片','出典'],[[m['id'],m['kind'],m['text'],link('../'+m['path']+'#L'+str(m['line']),Path(m['path']).name+':'+str(m['line']))] for m in messages]))
    commonproof=['# 共通処理の根拠','','適用条件と例外を確認する。全機能にすべての共通処理が適用されるという意味ではない。','']
    commonproof += [link('../../'+p+'#L'+str(m['line'])+'-L'+str(m['end']),m['summary'] or m['name']) for p,r in data['records'].items() if '/Classes/' in p for m in r.get('methods',[])]
    put(report/'共通根拠.md','\n'.join(commonproof)+'\n')
    save(state/'objects.json',objects);save(state/'messages.json',messages);save(state/'ownership.json',{**previous,**owned})
    return {'written':written,'conflicts':conflicts,'feature_documents':len(data['features']),'supplementary_documents':6,'message_definitions_and_candidates':len(messages),'db_object_candidates':len(objects)}
