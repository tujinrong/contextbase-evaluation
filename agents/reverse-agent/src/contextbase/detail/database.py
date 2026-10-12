"""P2 database operation descriptions from reread Java/SQL source.

Stores query targets, assignments, conditions and transaction evidence as facts;
P3 only renders these stored blocks. Never connects to the application's DB.
"""
from __future__ import annotations
import re
from pathlib import Path
from collections import defaultdict,deque
from specgen.adapters.java_sql import analyze_sql, sql_details
from specgen.sql import sql_facts, QUALIFIED, identifier
from specgen.common import split_top
from contextbase.shared.store import digest

OPS={'C':'挿入','U':'更新','D':'削除','R':'参照','M':'挿入・更新（MERGE）'}


def java_related(entry, methods, dependencies, sources, limit=80):
    byname=defaultdict(list)
    for m in methods:
        if m['path'] in dependencies:byname[m['name']].append(m)
    out=[];seen=set();todo=deque([entry])
    while todo and len(out)<limit:
        m=todo.popleft()
        if m['id'] in seen:continue
        seen.add(m['id']);out.append(m)
        source=sources[m['path']];scope=dict(re.findall(r'\b([A-Z]\w*)(?:<[^;\n]+>)?\s+(\w+)\s*(?=[=,)])',source))
        scope={var:typ for typ,var in re.findall(r'\b([A-Z]\w*)(?:<[^;\n]+>)?\s+(\w+)\s*(?=[=,)])',source)}
        parent=re.search(r'\bextends\s+(\w+)',source)
        for c in m.get('calls',[]):
            parts=c['name'].split('.');candidates=byname.get(parts[-1],[])
            same=[x for x in candidates if x['path']==m['path']]
            if len(parts)>1:
                typ=scope.get(parts[-2],parts[-2]);owned=[x for x in candidates if x.get('owner')==typ]
                if owned:candidates=owned
            elif same:candidates=same
            elif parent:
                inherited=[x for x in candidates if x.get('owner')==parent[1]]
                if inherited:candidates=inherited
            if len(candidates)==1:todo.append(candidates[0])
            elif candidates and len({x.get('owner') for x in candidates})==1:
                # Keep possible overloads as candidates; do not claim compiler-grade dispatch.
                todo.extend(candidates)
    return out


def collect(sources):
    operations=[];parsed={}
    for path,source in sources.items():
        if not path.endswith('.java'):continue
        result=analyze_sql(source,path);parsed[path]=result
        used={(q['table'],q['operation'],q['sql']) for q in result['queries'] if not q['owner'].startswith('<constant:')}
        for q in result['queries']:
            if q['owner'].startswith('<constant:') and (q['table'],q['operation'],q['sql']) in used:continue
            info=sql_details(q)
            owner=q['owner'].split('@')[0]
            method=next((m for m in result['methods'] if m['name']==owner and ('@' not in q['owner'] or str(m['line'])==q['owner'].split('@')[-1])),None)
            body=''.join(source.splitlines(keepends=True)[method['line']-1:method['end_line']]) if method else ''
            clauses=[]
            for verb,jp in [('setAutoCommit','自動コミット設定'),('commit','コミット'),('rollback','ロールバック')]:
                if re.search(r'\.'+verb+r'\s*\(',body):clauses.append(jp)
            tx=('当該メソッド内で'+ '・'.join(clauses)+'を行う。例外時の処理順は詳細仕様の分岐に従う。') if clauses else '呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。'
            if not clauses and re.search(r'\.setAutoCommit\(false\)',source):
                tx+=' 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。'
            q={**q,**info,'id':'SQL-'+digest([path,q['owner'],q['table'],q['operation'],q['sql']])[:12].upper(),
               'transaction':tx,'description':f'原本の{owner}で「{q["table"]}」を{OPS.get(q["operation"],q["operation"])}する。条件と設定値は以下のSQL式・バインド順序に従う。'}
            operations.append(q)
    # SQL file DML: documented as data provisioning, distinct from screen runtime.
    for path,source in sources.items():
        if not path.endswith('.sql'):continue
        for stmt in source.split(';'):
            _,refs,_=sql_facts(stmt,ddl=False)
            for ref in refs:
                if ref['operation']=='R':continue
                op='M' if ref['operation'].startswith('MERGE') else ref['operation']
                q={'path':path,'owner':'SQLファイル','line':source[:source.find(stmt)].count('\n')+1,'table':ref['table'],'operation':op,'sql':stmt.strip()}
                info=sql_details(q)
                if op=='M':
                    m=re.search(r'\bMERGE\s+INTO\s+'+QUALIFIED+r'\s*\((.*?)\)\s*KEY\s*\((.*?)\)',stmt,re.I|re.S)
                    if m:info.update(columns=[identifier(v) for v in split_top(m[1])],where='KEY ('+m[2]+')',values=['原本の初期データ値（値自体は非転載）']*len(split_top(m[1])))
                # Do not reproduce passwords or seed personal data into specifications.
                q.update(info,sql='初期データ定義のため値は原本参照。',id='SQL-'+digest([path,q['table'],op])[:12].upper(),
                         transaction='配備・初期化時に実行するSQL。アプリケーションの更新トランザクションとは別に扱う。',
                         description=f'SQLファイルの初期化処理で「{q["table"]}」を{OPS[op]}する。実データ値は納品仕様書へ転載しない。')
                operations.append(q)
    unique={}
    for q in operations:unique.setdefault(q['id'],q)
    return list(unique.values())


def operation_blocks(q, *, public=False):
    from .documents import table,heading,paragraph
    op=q['operation'];columns=q['columns'];values=q['values']
    pairs_=[]
    for i,c in enumerate(columns):
        val=values[i] if i<len(values) else '実行時のバインド引数'
        if val=='?':val=f'バインド引数{i+1}（PreparedStatementまたは呼出側の設定順序）'
        pairs_.append(c+' ← '+val)
    setters='／'.join(pairs_) if pairs_ else '当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。'
    where='抽出・更新対象条件：'+q['where'] if q['where'] else ('新しい行を挿入する。重複や採番の扱いは呼出元および列制約に従う。' if op=='C' else 'WHERE句による限定はこのSQL式にない。呼出条件・動的付加条件は原本を参照する。')
    blocks=[heading('DB操作 '+q['id'],4),table(['情報','内容'],[
        ['操作ID',q['id']],['対象テーブル',q['table']],['操作',OPS.get(op,op)],
        ['処理説明',('対象テーブルの'+('新しい行を登録する。' if op=='C' else '条件に一致する行を更新する。' if op=='U' else '条件に一致する行を削除する。' if op=='D' else '対象データを読み取る。' if op=='R' else 'キーの一致に従って行を登録または更新する。')+'設定項目・対象条件・確定取消は以下の定義に従う。') if public else q['description']],['設定項目',setters],['対象条件',where],['確定・取消',q['transaction']],
        ['原本',q['path']+':'+str(q['line'])+' / '+q['owner']]]),
        paragraph('SQLの組立規則：'+q['sql'])]
    if public:
        blocks=blocks[:-1]
        bindings=q.get('parameter_bindings',[])
        if bindings:blocks.append(table(['設定先のDB項目','バインド順','値の設定・変換（原本）'],[[b['column'],str(b['position']),b['expression']] for b in bindings]))
    return blocks


def database_documents(database, operations):
    from .documents import table,paragraph,heading
    docs=[]
    import json
    rules=json.loads((Path(__file__).parents[1]/'templates/standard_rules.json').read_text(encoding='utf-8'))
    sections=[{'title':'テーブル一覧','blocks':[
        paragraph('この1文書に全表の定義をまとめる。表IDを見出し・Excelシート名に使用し、世代・スキーマ・参照推定を区別する。'),
        table(['表ID','論理名','物理名','根拠種別','列数'],[[f'TBL-{i:03}',t['logical_name']['value'],t['name'],t['origin'],str(len(t['columns']))] for i,t in enumerate(database['tables'],1)])]}]
    table_refs=[]
    for i,t in enumerate(database['tables'],1):
        logical=t['logical_name']['value'];rows=[];tid=f'TBL-{i:03}'
        for c in t['columns']:
            variants=c['variants'];types='／'.join(dict.fromkeys(str(v.get('type') or '原本に型定義なし') for v in variants)) or '参照式のみ・DDLなし'
            nullable='／'.join(dict.fromkeys(('NULL可' if v['nullable'] is True else 'NULL不可' if v['nullable'] is False else str(v.get('nullable') or '原本にNULL指定なし')) for v in variants)) or '原本に制約定義なし'
            pk='／'.join(dict.fromkeys('主キー' if v.get('primary_key') else '主キー指定なし' for v in variants)) or '原本にキー定義なし'
            rows.append([c['logical_name']['value'],c['name'],types,nullable,pk,c['status']])
        evidence=t.get('definitions') or t.get('usages') or []
        title=tid+' '+logical
        table_refs.append({'id':tid,'table':t['name'],'section':title})
        sections.append({'title':title,'blocks':[
            table(['情報','内容'],[['表ID',tid],['論理名',logical],['物理名',t['name']],['定義根拠',t['origin']],['列数',str(len(rows))]]),
            heading('項目定義'),table(['論理名','物理名','データ型','NULL条件','主キー','根拠状態'],rows),
            heading('利用・確認事項'),paragraph('定義ファイルの世代・環境を区別する。参照から推定した列に型・制約の宣言がなければ、確定値として作り出さない。'),
            *[paragraph('根拠：'+e['path']+':'+str(e.get('line',1))) for e in evidence[:8]]]})
    if not database['tables']:sections[0]['blocks'].append(paragraph('今回の原本走査では物理表の定義・SQL参照を検出していない。'))
    docs.append({'db_tables':table_refs,'path':rules['db_definition_path'],
                 'model':{'title':'テーブル定義書','sections':sections}})
    if operations:
        docs.append({'path':'共通/DB仕様書/DB操作仕様書.md','model':{'title':'DB操作仕様書','sections':[
            {'title':'概要','blocks':[paragraph('SQL原本を対象として、参照・挿入・更新・削除とパラメーター・対象条件・確定取消を記載する。')]+[
                table(['操作ID','処理','対象テーブル','原本'],[[q['id'],OPS.get(q['operation'],q['operation']),q['table'],q['path']] for q in operations])]},
            {'title':'操作詳細','blocks':[b for q in operations for b in operation_blocks(q)]}]}})
    return docs
