"""Source-backed event narratives and offline flow/SQL entity diagrams.

The rules describe observed control structure, never execute application code,
and never turn a SQL JOIN into an unproved FK or cardinality. Rendering stays in
P2 so the sealed P3 input is self-contained. Unknown expressions remain in the
traceability notes, not silently guessed into business rules.
"""
from __future__ import annotations
import html
import io
import json
from pathlib import Path
import re
import subprocess
from PIL import Image
from specgen.common import split_top
from specgen.sql import IDENT, QUALIFIED, identifier
from contextbase.shared.store import digest, safe, write
from .bindings import sql_aliases, select_columns, _calls

VERSION='event-templates-1.1-structured-procedures'
JP=re.compile('[ぁ-ゖァ-ヺ一-鿿]')
OPS={'C':'登録','U':'更新','D':'削除','R':'参照','M':'登録・更新'}
RULES=json.loads((Path(__file__).parents[1]/'templates/standard_rules.json').read_text(encoding='utf-8'))


def _quote(value):return '"'+str(value).replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')+'"'


def _wrap(value,n=24):
    return '\n'.join(str(value)[i:i+n] for i in range(0,len(str(value)),n))


def _image(lines,destination,name,alt):
    dot='\n'.join(lines)+'\n';write(safe(destination,name+'.dot'),dot)
    result=subprocess.run(['dot','-Tpng','-Gdpi=110'],input=dot.encode(),capture_output=True,timeout=30)
    if result.returncode:raise ValueError('Diagram rendering failed: '+result.stderr.decode(errors='replace')[:400])
    image=Image.open(io.BytesIO(result.stdout)).convert('RGB')
    if image.width*image.height>35_000_000:raise ValueError('Event diagram exceeds image safety bound')
    if image.width>1350:image=image.resize((1350,round(image.height*1350/image.width)),Image.Resampling.LANCZOS)
    blocks=[]
    for no,y in enumerate(range(0,image.height,860),1):
        piece=image.crop((0,y,image.width,min(image.height,y+860)))
        filename=f'{name}-{no:02}.png';piece.save(safe(destination,filename))
        blocks.append({'kind':'image','path':'assets/'+filename,'alt':alt+(f'（{no}／{(image.height+859)//860}）' if image.height>860 else '')})
    return blocks


class Narrator:
    def __init__(self,model,event,sources,names=None):
        self.model=model;self.event=event;self.sources=sources;self.names=names or {}
        self.methods=event.get('methods',[]);self.labels={**model.get('field_labels',{})}
        for item in model.get('items',[]):
            if item.get('binding'):self.labels[item['binding']]=item['name']
            for e in item.get('db_bindings',[]):self.labels[e['property']]=item['name']
        self.variables={};self.notes=[];self.routes={};self.messages={}
        aliases=[]
        for p in model['dependencies']:
            text=sources.get(p,'')
            for k,v in re.findall(r'\bString\s+(\w+)\s*=\s*"([^"\n]+\.jsp)"',text):
                title=next((n for path,n in self.names.items() if path.endswith(v.removeprefix('./'))),None)
                self.routes[k]=title or ('ログイン画面' if 'login' in v.lower() else '対象画面')
            aliases.extend(re.findall(r'\bString\s+(\w+)\s*=\s*(\w+)\s*;',text))
            for key_,value_ in re.findall(r'\bString\s+(\w+)\s*=\s*"([^"\n]+)"\s*;',text):
                if JP.search(value_) and len(value_)<500:self.messages[key_]=value_
        for _ in range(8):
            for a,b in aliases:
                if b in self.routes:self.routes[a]=self.routes[b]
        if self.methods:
            counter=0
            for n in self.methods[0].get('steps',[]):
                ex=n.get('expression','');m=re.search(r'\b\w+\s+(\w+)\s*=\s*(.+)',ex,re.S)
                if not m:continue
                if re.search(r'\b(?:find|query|search|getBy)\w*\(',m[2],re.I):
                    counter+=1;self.variables[m[1]]='照会結果'+str(counter)
                elif re.search(r'\bread\w*\(request\)',m[2]):self.variables[m[1]]='入力データ'
                elif re.search(r'\bvalidate\w*\(',m[2]):self.variables[m[1]]='入力エラー'
                elif 'getInstance()' in m[2]:self.variables[m[1]]='データ操作サービス'

    def _body(self,name):
        ms=[m for m in self.methods if m.get('name')==name]
        if len(ms)>1 and self.methods:
            caller=self.methods[0];same=[m for m in ms if m.get('path')==caller.get('path')]
            parent=re.search(r'\bextends\s+(\w+)',self.sources.get(caller.get('path',''),''))
            inherited=[m for m in ms if parent and m.get('owner')==parent[1]]
            ms=same or inherited or ms
        if len(ms)!=1:return ''
        m=ms[0];return ''.join(self.sources.get(m['path'],'').splitlines(keepends=True)[m['line']-1:m['end_line']])

    def field(self,name):
        return self.labels.get(name,self.labels.get(name[:1].lower()+name[1:],name if JP.search(name) else '対象項目'))

    def describe_call(self,name,args):
        short=name.split('.')[-1];body=self._body(short)
        if short in {'getInstance','getSession'}:return ''
        if short in {'commit','rollback','close','setAutoCommit'}:
            return {'commit':'変更内容を確定する（コミット）','rollback':'このトランザクションの変更を取り消す（ロールバック）','close':'使用した接続・処理資源を解放する','setAutoCommit':'変更内容の確定を明示的に制御する' if args.strip()=='false' else '接続の自動確定方式を設定する'}[short]
        if '.getParameter(' in body and '.set' in body:return '画面の入力値を読み取り、処理用データへ設定する'
        if 'getParameter(' in body and 'getMethod()' in body and 'equals' in body:return '送信方法と画面確認用トークンの一致を確認する'
        if 'getSession' in body and ('ログイン' in body or 'LOGIN_INFO' in body) and ('return false' in body or 'return true' in body):return 'ログイン済み職員を確認し、セッションを準備する'
        if 'getRoleCode' in body or re.search(r'\b(?:hasRole|isUserInRole)\(',body):return '操作権限の制限を確認する'
        if 'Normalizer.normalize' in body and 'equals' in body:return '照合キーが一致するか確認する'
        if 'getAttribute(' in body and 'return' in body:return 'セッションに保持された利用者情報を取得する'
        if short.lower().startswith(('validate','check')):
            if body and ('getParameter' in body or '.get' in body or re.search(r'(?:null|length|matches|parse)',body)):
                return '入力値の制約と変換結果を確認する'
            return ''
        if short.lower().startswith(('find','query','search','getby')):
            fields=[self.field(m) for m in re.findall(r'\.(?:get|is)([A-Z]\w*)\(\)',args)]
            fields=[f for f in dict.fromkeys(fields) if f!='対象項目']
            return ('・'.join(fields)+'を条件に' if fields else '指定した条件で')+'データを照会する'
        if short.lower() in {'save','insert','update','delete','remove'}:
            return {'save':'入力内容を保存する（対象・実行条件はDB操作の詳細を参照）','insert':'新しいデータを登録する','update':'対象データを更新する','delete':'対象データを削除する','remove':'対象データを削除する'}[short.lower()]
        if 'createEmpty' in short:return '入力用の空データを用意する'
        if short.startswith('set') and len(short)>3:
            if 'ViewBean' in short or 'Bean' in args:
                msgs=[s for s in re.findall(r'"((?:\\.|[^"\\])*)"',args) if JP.search(s)]
                msgs += [self.messages[k] for k in re.findall(r'\b[A-Z][A-Z_]+\b',args) if k in self.messages]
                if msgs:return '表示内容を設定し、「'+msgs[-1].replace('\\r\\n','／')+'」を表示する'
                return '処理結果とメッセージを画面の表示内容へ設定する'
            return '「'+self.field(short[3:])+'」を設定する'
        label=self.names.get(short)
        if label and JP.search(label):return label+'を実行する'
        if JP.search(short):return short+'を実行する'
        return ''

    def condition(self,expr):
        raw=expr.strip()
        chunks=split_top(raw,'&&')
        if len(chunks)>1:return '、かつ'.join(self.condition(c) for c in chunks)
        chunks=split_top(raw,'||')
        if len(chunks)>1:return '、または'.join(self.condition(c) for c in chunks)
        m=re.fullmatch(r'(\w+)\s*(==|!=)\s*null',raw)
        if m:
            label=self.variables.get(m[1],self.field(m[1]))
            return label+('がない' if m[2]=='==' else 'がある')
        m=re.fullmatch(r'(!?)([\w.]+)\((.*)\)',raw,re.S)
        if m:
            text=self.describe_call(m[2],m[3])
            if text:
                if 'トークン' in text:return '送信方法・確認用トークン'+('が一致しない' if m[1] else 'が一致する')
                if 'ログイン済み職員' in text:return 'ログイン職員を'+('確認できない' if m[1] else '確認できる')
                if '照合キー' in text:return '照合キー'+('が一致しない' if m[1] else 'が一致する')
                if '操作権限' in text:return '操作権限'+('が制限されない' if m[1] else 'が制限される')
                text=text.removesuffix('を確認する').removesuffix('か確認する')
                return text+('が成立しない' if m[1] else 'が成立する')
        from .procedures import field_condition
        described=field_condition(self,raw)
        if described is not None:return described
        val=raw
        for g in re.finditer(r'\b\w+\.(?:get|is)([A-Z]\w*)\(\)',raw):val=val.replace(g[0],'「'+self.field(g[1])+'」')
        val=val.replace('!=',' が異なる ').replace('==',' が等しい ').replace('null','未設定').replace('true','はい').replace('false','いいえ')
        if JP.search(val):return val
        cid='条件'+str(len(self.notes)+1)
        self.notes.append({'id':cid,'kind':'condition','expression':raw})
        return cid+'を満たす（原本条件は補足説明を参照）'

    def statement(self,node):
        expr=node.get('expression','');kind=node['kind']
        if kind=='return':
            value=node.get('value',expr.removeprefix('return').strip())
            if value in self.routes:return self.routes[value]+'へ表示を戻す'
            if 'Page()' in value:return '同じ画面を表示する'
            if 'Redirect' in value:return '指定した画面へ遷移する'
            if 'Json' in value:return '処理結果を応答データとして返す'
            if value in {'null','true','false'}:return {'null':'戻り先画面を指定せず処理を終了する','true':'成立の結果を返す','false':'不成立の結果を返す'}[value]
            if value.startswith('"') and JP.search(value):return 'エラーまたは処理結果「'+value.strip('"')+'」を返す'
            return '処理結果を呼出元へ返す'
        if kind=='throw':return '処理の異常を通知し、この経路を終了する'
        messages=[s for s in re.findall(r'"((?:\\.|[^"\\])*)"',expr) if JP.search(s)]
        calls=node.get('calls',[])
        for c in calls:
            phrase=self.describe_call(c['name'],c.get('arguments',''))
            if phrase:
                variable=re.search(r'\b\w+\s+(\w+)\s*=',expr)
                if variable and variable[1] in self.variables and self.variables[variable[1]].startswith('照会結果'):
                    phrase+='（'+self.variables[variable[1]]+'）'
                return phrase
        if messages:return '「'+messages[-1]+'」を設定する'
        if re.search(r'getInstance\(\)',expr):return ''
        if not expr.strip():return ''
        nid='処理'+str(len(self.notes)+1)
        self.notes.append({'id':nid,'kind':'statement','expression':expr,'line':node.get('line')})
        return '関連情報を取得・設定する（'+nid+'：詳細仕様参照）'


def flow_model(narrator,event):
    nodes=[];edges=[];steps=[]
    def new(text,shape='box',line=None):
        nid='n'+str(len(nodes));nodes.append({'id':nid,'text':text,'shape':shape,'line':line});return nid
    end=new('終了','oval')
    def grouped(values):
        result=[];i=0
        while i<len(values):
            node=values[i];i+=1
            if node['kind']=='try':
                node=dict(node,catches=[],cleanup=[])
                while i<len(values) and values[i]['kind']=='catch':node['catches'].append(values[i]);i+=1
                if i<len(values) and values[i]['kind']=='finally':node['cleanup']=values[i].get('body',[]);i+=1
            result.append(node)
        return result
    def sequence(values,after,return_to=None,exception_to=None,depth=0):
        current=after;return_to=return_to or end;exception_to=exception_to or end
        if depth>24:
            narrator.notes.append({'kind':'depth','expression':'深い入れ子は詳細仕様の原本処理順を参照'})
            n=new('深い入れ子の処理（詳細仕様を参照）');edges.append((n,current,''));return n
        for n in reversed(grouped(values)):
            kind=n['kind']
            if kind=='if':
                yes=sequence(n.get('body',[]),current,return_to,exception_to,depth+1)
                no=sequence(n.get('else',[]),current,return_to,exception_to,depth+1)
                c=new(narrator.condition(n.get('condition',''))+'？','diamond',n.get('line'))
                edges.extend([(c,yes,'はい'),(c,no,'いいえ')]);current=c
            elif kind in {'for','foreach','while'}:
                c=new('繰返し条件：'+narrator.condition(n.get('condition','')),'diamond',n.get('line'))
                body=sequence(n.get('body',[]),c,return_to,exception_to,depth+1)
                edges.extend([(c,body,'継続'),(c,current,'終了')]);current=c
            elif kind=='try':
                cleanup=n.get('cleanup',[])
                normal=sequence(cleanup,current,return_to,exception_to,depth+1) if cleanup else current
                returned=sequence(cleanup,return_to,return_to,exception_to,depth+1) if cleanup else return_to
                thrown=sequence(cleanup,exception_to,return_to,exception_to,depth+1) if cleanup else exception_to
                catches=[]
                for handler in n.get('catches',[]):
                    target=sequence(handler.get('body',[]),normal,returned,thrown,depth+1)
                    catch=new('例外に該当した場合の処理（'+handler.get('condition','')+'）',line=handler.get('line'))
                    edges.append((catch,target,''));catches.append(catch)
                body=sequence(n.get('body',[]),normal,returned,catches[0] if len(catches)==1 else thrown,depth+1)
                c=new('本処理／例外処理の範囲',line=n.get('line'));edges.append((c,body,'通常'))
                for target in catches:edges.append((c,target,'範囲内で該当例外が発生した場合'))
                current=c
            elif kind in {'using','lock','synchronized','finally'}:
                text={'using':'資源の有効範囲内で処理する','lock':'排他範囲内で処理する','synchronized':'排他範囲内で処理する','finally':'終了時の後処理を行う'}[kind]
                child=sequence(n.get('body',[]),current,return_to,exception_to,depth+1)
                c=new(text,line=n.get('line'));edges.append((c,child,''));current=c
            elif kind in {'catch','switch'}:
                narrator.notes.append({'kind':kind,'expression':n.get('condition',''),'line':n.get('line')})
                text='値に応じた分岐（各分岐は詳細仕様参照）' if kind=='switch' else '例外処理（接続条件は詳細仕様参照）'
                c=new(text,line=n.get('line'));edges.append((c,current,''));current=c
            else:
                text=narrator.statement(n)
                if not text:continue
                c=new(text,'oval' if kind in {'return','throw'} else 'box',n.get('line'))
                target=return_to if kind=='return' else exception_to if kind=='throw' else current
                edges.append((c,target,''));current=c
        return current
    method=event.get('methods',[{}])[0] if event.get('methods') else {}
    seq=method.get('flow') or method.get('steps',[])
    root=sequence(seq,end);start=new('開始：'+event['name'],'oval');edges.append((start,root,''))
    from .procedures import procedure_steps
    steps=procedure_steps(narrator,event)
    return {'nodes':nodes,'edges':edges,'steps':steps,
            'scope':'入口処理の順序・分岐を示す。呼出先の処理は別単位とし、SQLの対象と実行条件はDB操作の詳細へ記載する。例外線は範囲内で例外が発生した場合の経路で、各命令が必ず例外を送出する意味ではない。'}


def er_model(queries,database):
    tables={t['name'].casefold():t for t in database['tables']};entities={};joins=[]
    for q in queries:
        aliases=sql_aliases(q['sql']);targets={q['table'],*aliases.values()}
        for name in sorted(targets):
            table=tables.get(name.casefold())
            if not table:continue
            entities.setdefault(name,{'table':name,'logical_name':table['logical_name']['value'],'columns':[], 'operations':[]})
            if q['table']==name and q['operation'] not in entities[name]['operations']:entities[name]['operations'].append(q['operation'])
        for match in re.finditer(r'\b(\w+)\.('+IDENT+r')\s*=\s*(\w+)\.('+IDENT+r')',q['sql']):
            left=aliases.get(match[1].casefold());right=aliases.get(match[3].casefold())
            if not left or not right or left not in entities or right not in entities or left==right:continue
            relation={'left':left,'left_column':identifier(match[2]),'right':right,'right_column':identifier(match[4]),
                      'kind':'sql_join','cardinality':'未確定','operation_id':q['id']}
            if not any(all(r[k]==relation[k] for k in ['left','left_column','right','right_column']) for r in joins):joins.append(relation)
        for name in targets & entities.keys():
            table=tables[name.casefold()]
            used=set(q.get('columns',[])) if q['table']==name else set()
            for refs in select_columns(q['sql']).values():used.update(r['column'] for r in refs if r['table']==name)
            used.update(r[k] for r in joins for side,k in [('left','left_column'),('right','right_column')] if r[side]==name)
            for c in table['columns']:
                if c['name'] not in used:continue
                value={'physical':c['name'],'logical':c['logical_name']['value'],'pk':any(v.get('primary_key') for v in c['variants'])}
                if value not in entities[name]['columns']:entities[name]['columns'].append(value)
    return {'entities':list(entities.values()),'relationships':joins,'legend':'実線はSQLの結合条件。外部キー制約や多重度を断定しない。単独表は独立したエンティティで表す。'}


def enrich(model,sources,database,destination,names=None):
    if model.get('reviewed'):return
    for event in model['events']:
        narrator=Narrator(model,event,sources,names)
        flow=flow_model(narrator,event)
        event['narrative']={'summary':model['name']+'で「'+event['name']+'」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。',
                            'steps':flow['steps'],'notes':narrator.notes,'scope':flow['scope']}
        event['flow_model']=flow
        entry=event.get('methods',[{}])[0] if event.get('methods') else {}
        event['narrative']['outcomes']=[{'condition':'・'.join(narrator.condition(g) for g in n.get('guards',[]) if g not in {'try','finally'}) or 'この終了経路へ到達した場合','result':narrator.statement(n)} for n in entry.get('steps',[]) if n['kind'] in {'return','throw'}]
        # Diagrams are required for screen events; keep common units textual to avoid giant duplicate books.
        if model['kind']!='screen':continue
        prefix=model['id']+'-'+event['id'].lower()
        lines=['digraph flow {','graph [rankdir=TB, bgcolor=white, nodesep=0.25, ranksep=0.35];',
               'node [fontname="Noto Sans CJK JP",fontsize=12,margin="0.12,0.07"]; edge [fontname="Noto Sans CJK JP",fontsize=11];']
        for n in flow['nodes']:lines.append(_quote(n['id'])+' [shape='+n['shape']+',label='+_quote(_wrap(n['text']))+'];')
        for a,b,label in flow['edges']:lines.append(_quote(a)+' -> '+_quote(b)+' [label='+_quote(label)+'];')
        lines.append('}')
        event['flow_images']=_image(lines,destination,prefix+'-flow',event['name']+' 処理フロー')
        queries=event.get('sql_operations',[])
        if queries:
            er=er_model(queries,database);event['er_model']=er
            ids={e['table']:'t'+str(i) for i,e in enumerate(er['entities'])}
            lines=['graph er {','graph [rankdir=LR,bgcolor=white,nodesep=0.4,ranksep=0.8];',
                   'node [shape=plain,fontname="Noto Sans CJK JP",fontsize=12]; edge [fontname="Noto Sans CJK JP",fontsize=10];']
            for e in er['entities']:
                cells=[html.escape(e['logical_name'])+'<BR/>'+html.escape(e['table'])+'<BR/>'+html.escape('・'.join(OPS.get(o,o) for o in e['operations']))]
                cells += [html.escape(('PK ' if c['pk'] else '')+c['logical']+' ['+c['physical']+']') for c in e['columns'][:12]]
                if len(e['columns'])>12:cells.append('他'+str(len(e['columns'])-12)+'項目：統合テーブル定義書参照')
                label='<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="5">'+''.join('<TR><TD ALIGN="LEFT">'+v+'</TD></TR>' for v in cells)+'</TABLE>'
                lines.append(_quote(ids[e['table']])+' [label=<'+label+'>];')
            for r in er['relationships']:
                label=r['left_column']+' = '+r['right_column']+'\nSQL結合（多重度未確定）'
                lines.append(_quote(ids[r['left']])+' -- '+_quote(ids[r['right']])+' [label='+_quote(label)+'];')
            lines.append('}')
            event['er_images']=_image(lines,destination,prefix+'-er',event['name']+' SQL・テーブル関連ER図')
