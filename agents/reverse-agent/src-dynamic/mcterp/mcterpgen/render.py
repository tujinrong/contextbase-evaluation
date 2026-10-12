"""Japanese specifications from source evidence; raw source is never active HTML."""
from __future__ import annotations
from collections import defaultdict,Counter
from pathlib import Path
from urllib.parse import quote
import html,json,re,os
from .model import walk,normalize
from .scan import masked,sha

OPS={'R':'参照','C':'登録','U':'更新','D':'削除','?':'用途確認'}
NAMES={'Mobile.HpTimecard':'モバイル勤怠打刻','Mobile.login_index':'モバイルログイン','HpMain':'従業員ホーム','OmSESWorker':'SES作業者選択','OmSESCustSave':'SES取引先登録','OmTaxRate':'消費税率照会'}
PARTS={'MailModal':'メール送信','MemoModal':'メモ編集','PdfExcelView':'PDF・Excel閲覧','PreviewView':'帳票プレビュー','StatusModal':'ステータス確認','ResumeModal':'職務経歴確認','403':'権限エラー','404':'ページ未検出'}
EV={'Init':'初期表示','Search':'検索','InitDetail':'詳細初期表示','Save':'保存','Delete':'削除','CsvExport':'CSV出力','Approval':'承認','Print':'帳票出力','Export':'出力','Download':'ダウンロード','Upload':'アップロード','Login':'ログイン','Logout':'ログアウト','handleReset':'検索条件クリア','searchData':'検索','forwardAdd':'新規入力へ移動','save':'保存','onClockIn':'出勤打刻','onClockOut':'退勤打刻'}


def safe(value):
    text=str(value)
    text=re.sub(r'(?i)(password|passwd|secret|api[_-]?key|access[_-]?token)(\s*[:=]\s*)([\'\"])[^\n]*?\3',r'\1\2"[非表示]"',text)
    return text


def cell(value):return html.escape(safe(value),quote=False).replace('|','&#124;').replace('`','&#96;').replace('\n','<br>')
def table(headers,rows):
    rows=list(rows)
    if not rows:return '該当する定義はこの解析では抽出されていません。存在しないという判定ではありません。\n'
    return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join('| '+' | '.join(cell(v) for v in row)+' |\n' for row in rows)
def link(path,label):return '['+cell(label)+']('+quote(str(path).replace('\\','/'),safe='/#')+')'
def source(root,dest,path,line=None,end=None):
    rel=os.path.relpath(root/path,dest.parent).replace('\\','/')
    return link(rel+(f'#L{line}'+(f'-L{end}' if end and end!=line else '') if line else ''),path+(f'：{line}行' if line else ''))
def code(text,lang='text'):
    fence='`'*max(3,1+max([len(x) for x in re.findall('`+',text)] or [0]));return fence+lang+'\n'+safe(text)+'\n'+fence+'\n'
def title(g):return NAMES.get(g['key'],PARTS.get(g['name'],g['name']))
def filename(g):return '概要仕様書'+g['id']+'_'+re.sub(r'[/\\:*?"<>|]','_',title(g))+'.md'
def logical(d,name):return d['tables'].get(name,{}).get('logical',name)
def references(d,m):
    mids=walk(d['graph'],m['id']);refs=[r for mid in mids for r in d['methods'][mid]['db']]
    for mid in mids:
        for proc in d['methods'][mid]['routines']:refs.extend({**r,'via':'DB処理 '+proc} for r in d['routines'][proc]['recursive_refs'])
    return list({(x['table'],x['op']):x for x in refs}.values())


def diagram(nodes,edges):
    out=['flowchart LR']
    for key,label,db in nodes:
        label=str(label).replace('"','＂').replace('\n',' ').replace('\\','／').replace('[','［').replace(']','］')
        out.append(key+('[('+ '"'+label+'"'+')]' if db else '["'+label+'"]'))
    for a,b,label in edges:out.append(a+' -->'+('|'+str(label).replace('|','／')+'|' if label else '')+' '+b)
    return code('\n'.join(out),'mermaid')


def screen_title(screen):
    stem=Path(screen['path']).stem
    if stem=='index':stem=Path(screen['path']).parent.name
    return PARTS.get(stem,stem)


def layout(g):
    out=['<!-- docsite:screen-layout begin -->', '<section class="screen-layout" id="layout-'+g['id']+'">',
         '<style>.screen-layout{background:#f4f7fa;border:1px solid #c4d1dc;padding:18px;margin:16px 0;color:#22354a}.screen-layout .ui-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.screen-layout .ui-item{padding:8px;background:white;border:1px solid #d4dfe8;min-width:0}.screen-layout label{display:block;font-weight:600;margin-bottom:4px}.screen-layout input,.screen-layout select,.screen-layout button{width:100%;min-width:0;box-sizing:border-box;padding:7px;color:#22354a;background:#fff;border:1px solid #acbdcb}.screen-layout small{display:block;overflow-wrap:anywhere}.screen-layout .ui-columns{overflow-x:auto}.screen-layout th{white-space:nowrap}</style>',
         '<p>原本の項目順を基にした仕様確認用レイアウトです。表示は2列に再配置し、動的な表示・繰返し件数・実寸法・実際の操作は再現しません。値は空の表示例です。</p>']
    for s in g['screens']:
        esc=lambda x:html.escape(str(x),quote=True)
        out+=['<h3>'+esc(screen_title(s))+'</h3>','<div class="ui-grid">']
        cols=[]
        for item in s['items']:
            if item['type']=='一覧表示':cols.append(item);continue
            ident=item['id'];label=esc(item['name']);role=item['role'];attrs=' id="'+ident+'" aria-label="'+label+'"'
            if role.startswith('操作'):control='<button type="button" disabled'+attrs+'>'+label+'</button>'
            elif item['type']=='選択':control='<select disabled'+attrs+'><option>選択候補</option></select>'
            else:control='<input type="'+('date' if item['type']=='日付' else 'text')+'" disabled'+attrs+'>'
            out+=['<div class="ui-item" data-item="'+ident+'"><label for="'+ident+'">'+str(item['order'])+'. '+label+'</label>'+control+'<small>'+esc(role)+'／'+esc(item['length'])+'</small></div>']
        out+=['</div>']
        if cols:out+=['<div class="ui-columns"><table><thead><tr>']+['<th data-item="'+i['id']+'">'+esc(i['name'])+'</th>' for i in cols]+['</tr></thead><tbody><tr>']+['<td>表示値</td>' for _ in cols]+['</tr></tbody></table></div>']
        if not s['items']:out+=['<p>この部品は構成・表示の組立てが中心で、個別入力項目は抽出されていません。子部品または共通部品の仕様を参照します。</p>']
    out+=['</section>','<!-- docsite:screen-layout end -->','']
    return '\n'.join(out)


def explain(m,d,frontend=False):
    body=m['body'];bullets=[]
    if frontend:
        if re.search(r'\bvalidate(?:Fields)?\s*\(',body):bullets.append('操作対象の入力を検証する。検証に失敗した場合の通知・継続条件は、この画面の検証規則と例外処理を優先する。')
        if re.search(r'\b(?:showSaveModal|showDeleteModal|showConfirmModal|confirm)\s*\(',body):bullets.append('確定前の確認を表示する。了承時と取消時を別経路として扱い、確認が返る前に保存済みとみなさない。')
        if re.search(r'\b(?:push|replace)\s*\(',body):bullets.append('画面または経路の切替えを行う。遷移先へ渡す識別子・表示モードは原本の指定を用い、一覧と編集画面の状態を混同しない。')
        if 'resetFields(' in body or 'resetForm(' in body:bullets.append('フォームのリセット処理を呼び出す。DB内の情報の削除を意味しない。対象の項目集合はフォーム定義に従う。')
    else:
        mode=next((x for x in ['Transction','Nolock','Lock'] if re.search(r'\b'+x+r'\(',body)),None)
        if mode:bullets.append({'Transction':'共通の更新用トランザクション処理を通す。要求を受け取り、処理が正常終了した場合に確定する。','Nolock':'共通の参照用処理を通す。「Nolock」という実装名でもトランザクション開始があり、取引なしとは扱わない。','Lock':'共通の直列化分離レベル指定の処理を通す。排他の対象・DB実効動作は呼出先定義と併せて確認する。'}[mode])
    comments=list(dict.fromkeys(normalize(c['text']) for c in m['comments'] if re.search(r'[ぁ-龯]',c['text']) and not re.search('TODO|todo|コメントアウト',c['text'])))
    for c in comments:
        if len(c)>3:bullets.append('処理の要点（原本コメント）：'+c.rstrip('。')+'。')
    refs=references(d,m)
    for r in refs:bullets.append('「'+logical(d,r['table'])+'」を'+OPS[r['op']]+'する。'+('直接のDAO参照または解決した呼出先で確認した操作であり、同名の画面項目だけから推定したCRUDではない。' if not r.get('via','').startswith('DB処理') else 'DB処理定義をたどって確認した参照・更新先である。'))
    if re.search(r'\.SetLock\s*\(',body):bullets.append('更新時にロック検査用の値を渡す。画面で読み込んだ更新時点と保存要求の値を照合する経路がある。比較方式と例外は共通DBライブラリの契約にも依存する。')
    if re.search(r'\bthrow\b',masked(body)):bullets.append('処理を継続できない条件では例外を発生させる。後段の正常応答と区別し、共通例外変換を通る場合はそこで利用者向けの応答へ変換する。')
    if re.search(r'\b(?:Upload|Download|Export|Csv|Excel|PDF|Pdf|Print)',m['name']):bullets.append('帳票・ファイルの生成／受渡しを担当する。生成の完了、プレビューの表示、利用者端末への保存は別の完了状態であり、端末への保存成功まで静的解析で確認したものではない。')
    if not bullets:bullets.append('この処理は「'+(m['summary'] or EV.get(m['name'],m['name']))+'」の要求を扱う。入力、判断条件、呼出先は下表に記録する。未抽出の外部処理の内部動作まで確定していない。')
    return list(dict.fromkeys(bullets))


def feature(root,g,d):
    dest=root/'output/md/基本設計書'/filename(g);out=['# '+cell(g['id']+' '+title(g)),'', '> ソースから逆引きした顧客確認用の概要仕様。実装の宣言と推定・未確認を区別する。原本のコード・DB・マクロは実行していない。','', '## 1. システム概要','', '### 1.1 概要','',cell(title(g))+'に関する'+('画面とサーバー処理' if g['screens'] else 'サーバー処理')+'を整理する。'+('一覧・詳細・子部品は同じ業務サービスの範囲にまとめ、共通部品への参照は別に記録する。' if g['screens'] else '実装上のサービス境界を機能の単位とする。画面が抽出されていないことは画面が存在しないという断定ではない。'),'']
    out += [table(['項目','内容'],[['機能種別',g['kind']],['サービス識別子',g['key']],['画面・子部品',len(g['screens'])],['サービスメソッド',len(g['methods'])],['関連ソース',len(g['files'])],['DB定義の基準',d['active_schema_snapshot'] or 'ソースのDTO宣言のみ']]),'','### 1.2 画面レイアウト','',layout(g) if g['screens'] else '画面レイアウトの対象ではない、または入口との対応が未確定である。','', '### 1.3 入出力・データの関係','']
    apis=list({(a['service'],a['method'],a['path']):a for s in g['screens'] for a in s['apis']}.values())
    out+=[table(['呼出先サービス','処理','受渡し方式','照合状態'],[[a['service'],a['method'],a['kind'],'宣言と対応' if len(a.get('matched',[]))==1 else '対応要確認'] for a in apis]),'']
    nodes=[('U','利用者／呼出元',False),('F',title(g),False),('S','業務サービス',False)];edges=[('U','F','入力・操作'),('F','S','要求')]
    for n,tab in enumerate(sorted({x['table'] for x in g['db']})):
        key='D'+str(n);nodes.append((key,logical(d,tab),True));edges.append(('S',key,'／'.join(sorted({OPS[x['op']] for x in g['db'] if x['table']==tab}))))
    out += [diagram(nodes,edges),'### 1.4 画面・部品の関係','']
    screenids={s['path']:'P'+str(n) for n,s in enumerate(g['screens'])}
    if screenids:
        out += [diagram([(screenids[s['path']],screen_title(s),False) for s in g['screens']],[(screenids[s['path']],screenids[t],'構成参照') for s in g['screens'] for t in s['imports'] if t in screenids]),'図の接続は静的な部品importの関係であり、そのまま実行時の画面遷移順を意味しない。各操作の遷移はイベント節で確認する。','']
    out+=['## 2. 項目一覧','','項目はソースの宣言順で列挙する。繰返し表示する明細列は列定義を1項目として数える。条件付き非表示、親部品の検証、DB列の物理長は区別する。','']
    for idx,s in enumerate(g['screens'],1):
        out+=['### 2.'+str(idx)+' '+cell(screen_title(s)),'',source(root,dest,s['path']),f"\n項目数：{len(s['items'])}。\n"]
        rows=[]
        for i in s['items']:
            db=[]
            for x in i.get('db',[]):
                col=next((c['logical'] for c in d['tables'][x['table']]['columns'] if c['physical']==x['column']),x['column']);db.append(logical(d,x['table'])+'・'+col)
            explanation=i['role']+'。'+(('条件：'+i['condition']+'。') if i['condition'] else '')+('属性：'+normalize(json.dumps(i['attributes'],ensure_ascii=False))+'。' if i['attributes'] else '')+'原本 '+str(i['line'])+'行。'
            rows.append([str(i['order']),i['name'],i['type'],'対象外' if i['role'].startswith('操作') else '候補：'+'／'.join(db) if db else '明示対応未抽出',i['required'],i['length'],explanation])
        out += [table(['No.','項目名','タイプ','DB関連（論理名）','必須','長さ','概要説明'],rows),'']
    out += [f"**合計：{sum(len(s['items']) for s in g['screens'])}項目**。画面を持たない処理では下記の要求・応答項目を参照する。\n",'### 2.補足 要求・応答の宣言','']
    for shape in g['shapes']:
        out += ['#### '+cell(shape['name']),'', '継承元：'+cell(shape['base'] or 'なし／未検出')+'。共通項目の継承は共通仕様を参照。',table(['項目','宣言上の型','説明','行'],[[x['name'],x['type'],x['description'] or '用途説明未記載',x['line']] for x in shape['fields']]),source(root,dest,shape['path']),'']
    out+=['## 3. イベント仕様','','画面のイベント結合とサーバーの処理を別に記録する。同じ処理を呼ぶ複数のボタンは結合先として残す。非同期処理、動的な条件、外部ライブラリの内部動作には未確定部分がある。','']
    evcount=0
    for si,s in enumerate(g['screens'],1):
        unique={(e['handler'],e['trigger']):e for e in s['events']}
        if not unique:continue
        out+=['### 3.UI'+str(si)+' '+cell(screen_title(s)),'',table(['発火条件','呼出処理・式','原本行'],[[e['trigger'],e['handler'],e['line']] for e in s['events']]),'']
        for (handler,trigger),e in unique.items():
            evcount+=1;name=re.match(r'[\w$]+',handler);method=next((m for m in s['methods'] if name and m['name']==name[0]),None)
            out+=['#### '+cell(g['id']+'-EV'+str(evcount).zfill(3)+' '+EV.get(handler,handler)),'']
            if method:
                out+=['- '+cell(x) for x in explain(method,d,True)]
                associated=[a for a in s['apis'] if any(c.split('.')[-1]==a['export'] for c in method['calls'])]
                if associated:out+=['- '+cell('要求先：'+'、'.join(a['service']+'／'+a['method'] for a in associated)+'。応答後の状態変更とエラー時の扱いはサーバー節と併せて確認する。')]
                out+=['',table(['判断条件（実装表記）','行'],[[c['text'],c['line']] for c in method['conditions']]),source(root,dest,method['path'],method['line'],method['end']),'']
            else:out+=['- '+cell('このイベントは '+handler+' を契機とする。インライン式・共通部品・import先の処理が含まれるため、このファイル単独の関数本体への対応は未確定。呼出元の入力と共通UIの受渡しを確認する。'),source(root,dest,s['path'],e['line']),'']
    for idx,mid in enumerate(g['methods'],1):
        m=d['methods'][mid];refs=references(d,m)
        out+=['### 3.S'+str(idx)+' '+cell(m['summary'] or EV.get(m['name'],m['name'])),'', '**処理識別子**：'+cell(m['name'])+'。',code(m['signature'],'text')]
        out+=['- '+cell(x) for x in explain(m,d)]
        out+=['',table(['判断条件（実装表記）','原本行'],[[c['text'],c['line']] for c in m['conditions']]),table(['論理データ','操作','経路'],[[logical(d,x['table']),OPS[x['op']],x.get('via','DB処理の再帰参照')] for x in refs]),'']
        if refs:
            ns=[('E',m['summary'] or m['name'],False)]+[('D'+str(k),logical(d,r['table']),True) for k,r in enumerate(refs)]
            out+=[diagram(ns,[('E','D'+str(k),OPS[r['op']]) for k,r in enumerate(refs)])]
        out+=[source(root,dest,m['path'],m['line'],m['end']),'']
    out+=['### 3.補足 データ例と確認方法','','APIの受渡しは次の形式を用いる。以下は構造説明用であり、実ユーザーや本番データを含まない。個別の必須条件、型、更新時点の値は要求モデルと各処理の条件を優先する。',code(json.dumps({'servicename':g['key'].removeprefix('Mobile.'),'methodname':d['methods'][g['methods'][0]]['name'] if g['methods'] else '処理名確認','bizrequest':{'data':'{"項目名":"説明用の値"}'}},ensure_ascii=False,indent=2),'json'),'## 4. 補足説明','','共通の認証、アクセス権、取引境界、エラー通知、日付・数値・ファイルの扱いは '+link('../共通/共通仕様.md','共通仕様')+' と '+link('../共通/開発規約.md','開発規約')+' を参照する。DB型・論理名の出典は '+link('../共通/DB定義書.md','DB定義書')+'。','', '**未確定事項**：画面の実行時可視性・正確な寸法、動的API/DB名、継承した検証の完全展開、外部ライブラリ内部、権限別の全経路、実DBとの一致、帳票テンプレートの印字結果。ここに記載した条件や件数は静的な抽出範囲であり、全仕様の完成判定ではない。','', '### 関連原本','']
    out += ['- '+source(root,dest,p) for p in g['files']]
    return '\n'.join(out)+'\n'


def common(root,d):
    out={};dest=root/'output/md/共通/DB定義書.md';tables=d['tables'];uses=defaultdict(list)
    for g in d['features']:
        for r in g['db']:uses[r['table']].append((g,r))
    db=['# DB定義書','','基準は入力に含まれる最新日付名のDBダンプから読み取った定義である。**ダンプの保存時点の定義であり、稼働DBの現在の定義ではない。** データ行を復元せず、長さ情報を検証したDDL文字列のみを読む。DTOにだけ現れる列は物理型・NULL・主キーを推定で補わない。',table(['定義スナップショット','テーブル数','定義文字列'],[[x['path'],x['tables'],x['ddl_strings']] for x in d['schema_snapshots']]),'']
    for name,t in tables.items():
        db+=['## '+cell(t['logical']),'','物理名：`'+cell(name)+'`。確度：'+cell(t['status'])+'。',source(root,dest,t['origin']),'',table(['論理項目名','物理列名','定義型','NULL','既定値','キー','説明'],[[c['logical'],c['physical'],c['type'],'未確認' if c['nullable'] is None else '可' if c['nullable'] else '不可', '[非表示]' if re.search('password|secret|token',c['physical'],re.I) else c['default'],c['key'] or '未明記',c.get('definition','')+'／DTO型：'+c.get('dto_type','未検出')] for c in t['columns']]),'### 使用箇所からの用途','',table(['機能ID','業務','操作','追跡経路'],[[g['id'],title(g),OPS[r['op']],r['via']] for g,r in uses[name]]),'### 制約・索引','',table(['区分','原文定義'],[['制約',x] for x in t['constraints']]+[['索引',x] for x in t['indexes']]),'']
    out['DB定義書.md']='\n'.join(db)
    objects=[['表',t['logical'],name,t['status'],t['origin']] for name,t in tables.items()]
    objects += [[r['kind'],r['name'],r['name'],'SQL定義を読取（未実行）',r['path']] for r in d['routines'].values()]
    out['DBオブジェクト一覧.md']='# DBオブジェクト一覧\n\n一覧は表・ソースで定義されたDB処理を対象とする。外部DBや実行時生成オブジェクトの不存在は意味しない。\n\n'+table(['種別','論理名／処理名','物理名','状態','原本'],objects)
    routine=['# DB処理仕様','','DB処理の実行、データ移行は行っていない。参照関係を再帰的にたどり、画面のAPI処理と対応する表を記録する。SQL中の一時表は本番の永続表と区別する。','']
    for name,r in d['routines'].items():
        params=re.search(r'(?:FUNCTION|PROCEDURE)\s+(?:public\.)?'+re.escape(name)+r'\s*(\([\s\S]*?\))\s*(RETURNS[^\n]+)?',r['text'],re.I)
        conditions=[normalize(m[0]) for m in re.finditer(r'(?im)^\s*(?:WHERE|AND|OR|ORDER BY|GROUP BY|HAVING|LIMIT|OFFSET|RETURN)\b[^\n]*',r['text'])]
        routine+=['## '+cell(name),'',source(root,root/'output/md/共通/DB処理仕様.md',r['path'],r['line']),'',code(params[0] if params else '引数・戻り値の形式は原本参照','sql'),table(['論理データ','操作'],[[logical(d,x['table']),OPS[x['op']]] for x in r['recursive_refs']]),'### 条件・集約・出力順の原本表記','',table(['定義'],[[x] for x in conditions]),'']
    out['DB処理仕様.md']='\n'.join(routine)
    apirows=[]
    for p,entries in d['apis'].items():
        for a in entries:
            matched=[m for m in d['methods'].values() if m['class']=='Service' and m['namespace']=='MCT.ERP.Service.'+a['service'] and m['name']==a['method']]
            apirows.append([a['service'],a['method'],a['kind'],len(matched),'宣言対応' if len(matched)==1 else '未確定',p+':'+str(a['line'])])
    out['API一覧.md']='# API一覧\n\n画面のAPI関数が送信するサービス名・処理名を抽出し、サーバーの宣言に照合した。実行時の認証やリフレクションの成功は未検証。宣言数が0または複数なら確認対象である。\n\n'+table(['サービス','処理','通信種別','サーバー宣言数','照合','送信側'],apirows)
    crud=['# CRUD図・機能別データ利用','','C：登録、R：参照、U：更新、D：削除。DAOの明示操作とSQL処理の再帰参照を対象とする。動的な表名、EUC利用者が実行時に指定するデータソースは未解決となる。','',table(['機能ID','機能名','論理データ','操作','経路'],[[g['id'],title(g),logical(d,x['table']),OPS[x['op']],x['via']] for g in d['features'] for x in g['db']])]
    out['CRUD図.md']='\n'.join(crud)
    shares=defaultdict(set)
    for g in d['features']:
        for mid in g['reachable_methods']:shares[mid].add(g['id'])
    common_methods=[m for mid,m in d['methods'].items() if '/Generated/' not in m['path'] and (len(shares[mid])>1 or '/Common/' in m['path'] or '/ErpCommon/' in m['path'] or '/utils/' in m['path'])]
    common_methods=[m for m in common_methods if m['class']!='Service']
    cm=['# 共通関数・共通UI仕様','','全ソースの共通領域と解決できた呼出元を横断して整理する。同名メソッドの候補が複数ある場合に、名前だけで結合しない。共通ライブラリDLLの内部と、動的呼出先は未確定。','']
    for idx,m in enumerate(common_methods,1):
        cm+=['## CF-'+str(idx).zfill(4)+' '+cell(m['summary'] or m['name']),'',code(m['signature']), '利用機能：'+cell('、'.join(sorted(shares[m['id']])) or '共通領域の宣言・対応未解決')+'。']
        cm+=['- '+cell(x) for x in explain(m,d,m['path'].endswith(('.ts','.vue','.js')))]
        cm+=[source(root,root/'output/md/共通/共通関数仕様.md',m['path'],m['line'],m['end']),'']
    out['共通関数仕様.md']='\n'.join(cm)
    components=[(p,r) for p,r in d['records'].items() if p.endswith('.vue') and '/src/views/' not in p]
    out['共通UI仕様.md']='# 共通UI仕様\n\n業務画面外のVue部品を対象とする。画面内の子部品は各機能仕様へ含める。入力・表示の役割、引数、動的な状態は部品ごとに異なり、共通の必須・長さを一律に適用しない。\n\n'+table(['部品','項目定義数','イベント結合数','原本'],[[Path(p).stem,len(r['items']),len(r['events']),p] for p,r in components])
    messages=[]
    for p,t in d['texts'].items():
        if not p.endswith(('.cs','.ts','.vue')):continue
        for m in re.finditer(r'(?:(?:const|readonly)\s+string\s+(\w+)\s*=\s*|(?:message\.(?:error|warning|success|info)|ShowWarning|throw new \w+Exception)\s*\(\s*)[\'\"]([^\'\"\n]{1,400})[\'\"]',t):
            if re.search('[ぁ-龯]',m[2]):messages.append([m[1] or '表示箇所',m[2],p,t.count('\n',0,m.start())+1])
    out['メッセージ一覧.md']='# メッセージ一覧\n\n定数定義・直接表示の文字列を列挙する。DB管理のメッセージ、結合で作る文面、翻訳キーの実行時解決は未確定。実データ・初期データのメッセージ本文は取り込まない。\n\n'+table(['識別子／種別','文面（固定部分）','原本','行'],messages)
    out['命名規則.md']='# 命名規則・論理名辞書\n\n顧客向け本文はDBのCOMMENTと画面表示を照合し、異なる意味の列を同名だけで統合しない。表・列の物理識別子、APIのサービス名、画面項目名は対応を保持する。同じ列名でも所属表が異なれば別の定義である。未確定の名称を顧客承認済みとしない。\n\n'+table(['論理名','物理名','根拠'],[[t['logical'],name,t['status']] for name,t in tables.items()])+'\nサービスは業務領域の名前、要求・応答はRequest／Response、SQL処理はsp_等の命名が観測される。名前は現行の慣例であり、他言語・他案件への強制規則ではない。機能IDは業務サービスまたは画面経路から作り、表示順で再採番しない。\n'
    d['render_counts']={'common_functions':len(common_methods),'common_ui_components':len(components),'messages':len(messages),'api_contracts':len(apirows)}
    return out
