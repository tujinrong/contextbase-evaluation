"""Source-backed UI -> model -> JDBC column lineage (P2 only).

Names alone NEVER establish a binding. Java setter/request reads, JSP getter
expressions, JDBC setter positions and SELECT aliases are separate evidence
edges. Ambiguous types/parameter positions remain unresolved. No source runs.
"""
from __future__ import annotations
from functools import lru_cache
from collections import defaultdict
from pathlib import Path
import re
from specgen.common import tokens, pairs, split_top
from specgen.adapters.java_sql import analyze_sql
from specgen.sql import QUALIFIED, IDENT, identifier
from contextbase.shared.store import fact

VERSION = 'source-bindings-1.0'
_GET = re.compile(r'\b(\w+)\.(?:get|is)([A-Z\u0080-\uffff]\w*)\s*\(\s*\)')
_SET = re.compile(r'\b(\w+)\.set([A-Z\u0080-\uffff]\w*)\s*\(')


def prop(name):
    return name[:1].lower()+name[1:]


@lru_cache(maxsize=8192)
def _calls(text):
    ts=tokens(text);pm=pairs(ts);out=[]
    for i,t in enumerate(ts[:-1]):
        if ts[i+1]['text']!='(' or i+1 not in pm or not re.fullmatch(r'[\w$]+',t['text']):continue
        if t['text'] in {'if','for','while','switch','catch','synchronized'}:continue
        end=pm[i+1];start=i
        while start>=2 and ts[start-1]['text']=='.' and re.fullmatch(r'[\w$]+',ts[start-2]['text']):start-=2
        prefix=''.join(x['text'] for x in ts[start:i+1])
        args=text[ts[i+1]['end']:ts[end]['start']]
        out.append({'name':prefix,'args':split_top(args) if args.strip() else [],'start':ts[start]['start'],
                    'end':ts[end]['end'],'line':t['line'],'text':text[ts[start]['start']:ts[end]['end']]})
    return out


def _params(signature):
    hit=re.search(r'\((.*)\)',signature,re.S)
    result=[]
    for arg in split_top(hit[1]) if hit else []:
        p=re.search(r'([\w.$<>?\[\]]+)\s+(\w+)\s*$',arg.strip())
        if p:result.append((p[1],p[2]))
    return result


def _types(text):
    return {var:typ.split('.')[-1] for typ,var in re.findall(r'\b([A-Z]\w*(?:\.\w+)*)\s+(\w+)\s*(?=[=,;)])',text)}


def _sub(expr, env):
    # Replace identifiers outside strings only. A single pass avoids self cycles.
    ts=tokens(expr);out=[];pos=0
    for i,t in enumerate(ts):
        out.append(expr[pos:t['start']]);v=t['text']
        out.append(env.get(v,v) if t['kind'] not in {'string','char'} and (i==0 or ts[i-1]['text']!='.') else v)
        pos=t['end']
    return ''.join(out)+expr[pos:]


@lru_cache(maxsize=4096)
def sql_aliases(sql):
    mapping={}
    reserved={'WHERE','SET','ON','LEFT','RIGHT','FULL','INNER','OUTER','JOIN','ORDER','GROUP','VALUES','AS','FOR','UNION'}
    for m in re.finditer(r'\b(?:FROM|JOIN|UPDATE|INTO)\s+('+QUALIFIED+r')(?:\s+(?:AS\s+)?([A-Za-z_]\w*))?',sql,re.I):
        table=identifier(m[1]);alias=m[2]
        if alias and alias.upper() not in reserved:mapping[alias.casefold()]=table
        mapping[table.casefold()]=table
    return mapping


@lru_cache(maxsize=4096)
def select_columns(sql):
    """Return output alias -> referenced physical columns, preserving JOIN sources."""
    a=sql_aliases(sql);m=re.search(r'\bSELECT\s+(.*?)\s+FROM\b',sql,re.I|re.S)
    if not m:return {}
    out={}
    for expr in split_top(m[1]):
        hit=re.search(r'\s+AS\s+('+IDENT+r')\s*$',expr,re.I)
        alias=identifier(hit[1]) if hit else identifier(expr.split('.')[-1])
        refs=[]
        base=expr[:hit.start()] if hit else expr
        for ref in re.finditer(r'\b(\w+)\.('+IDENT+r')',base):
            if ref[1].casefold() in a:refs.append((a[ref[1].casefold()],identifier(ref[2])))
        if not refs and re.fullmatch(IDENT,base.strip()) and len(set(a.values()))==1:
            refs=[(next(iter(a.values())),identifier(base.strip()))]
        if refs:out[alias]=[{'table':t,'column':c,'expression':base.strip()} for t,c in refs]
    return out


class BindingIndex:
    def __init__(self, sources, operations, database):
        self.sources=sources;self.operations=operations;self.database=database
        self.parsed={};self.methods={};self.models=defaultdict(list);self.requests=[];self.reads=[];self.writes=[]
        self.unresolved=[];self._body_cache={};self._reach_cache={}
        for path,text in sources.items():
            if not path.endswith('.java'):continue
            parsed=analyze_sql(text,path);self.parsed[path]=parsed
            self.models[Path(path).stem].append(path)
            self.methods[path]=parsed['methods']
        self.tables={t['name'].casefold():t for t in database['tables']}
        self._request_edges();self._read_edges();self._write_edges()

    def body(self,path,m):
        key=(path,m['line'],m['end_line'])
        if key not in self._body_cache:self._body_cache[key]=''.join(self.sources[path].splitlines(keepends=True)[m['line']-1:m['end_line']])
        return self._body_cache[key]

    def model_type(self,path,typ):
        candidates=self.models.get(typ.split('.')[-1],[])
        if len(candidates)==1:return candidates[0]
        # Resolve explicit import rather than choosing the first same-named class.
        imports=re.findall(r'\bimport\s+([\w.]+)\s*;',self.sources[path])
        hits=[c for c in candidates if any(c.endswith(i.replace('.','/')+'.java') for i in imports)]
        return hits[0] if len(hits)==1 else None

    def scope(self,path,m):
        return {**_types(self.sources[path]),**_types(self.body(path,m)),**{v:t for t,v in _params(m['signature'])}}

    def properties(self,expr,path,m,depth=0):
        scope=self.scope(path,m);out=[]
        for match in _GET.finditer(expr):
            typ=scope.get(match[1]);model=self.model_type(path,typ) if typ else None
            if model:out.append((model,prop(match[2])))
        # Derived writes can receive the model object, not just a direct getter.
        if depth<2:
            for c in _calls(expr):
                name=c['name'].split('.')[-1]
                methods=[x for x in self.methods[path] if x['name']==name and len(_params(x['signature']))==len(c['args'])]
                if len(methods)!=1:continue
                child=methods[0];params=_params(child['signature'])
                for (typ,formal),actual in zip(params,c['args']):
                    if actual.strip() not in scope:continue
                    if scope[actual.strip()].split('.')[-1]!=typ.split('.')[-1]:continue
                    model=self.model_type(path,typ)
                    if model:
                        for g in _GET.finditer(self.body(path,child)):
                            if g[1]==formal:out.append((model,prop(g[2])))
        return list(dict.fromkeys(out))

    def _request_edges(self):
        for path,methods in self.methods.items():
            for m in methods:
                body=self.body(path,m);scope=self.scope(path,m)
                for call in _calls(body):
                    hit=re.fullmatch(r'(\w+)\.set([A-Z\u0080-\uffff]\w*)',call['name'])
                    if not hit or not call['args']:continue
                    model=self.model_type(path,scope.get(hit[1],''))
                    if not model:continue
                    expr=call['args'][0]
                    names=re.findall(r'\b\w+\.getParameter\s*\(\s*"([^"\n]+)"\s*\)',expr)
                    if not names:
                        # Helper reads getParameter(name): bind the actual constant name.
                        for inner in _calls(expr):
                            helpers=[x for x in methods if x['name']==inner['name'] and len(_params(x['signature']))==len(inner['args'])]
                            if len(helpers)!=1:continue
                            params=_params(helpers[0]['signature']);env=dict(zip((x[1] for x in params),inner['args']))
                            for formal in re.findall(r'\b\w+\.getParameter\s*\(\s*(\w+)\s*\)',self.body(path,helpers[0])):
                                actual=env.get(formal,'').strip()
                                if re.fullmatch(r'"[^"\n]+"',actual):names.append(actual[1:-1])
                    for name in names:self.requests.append({'binding':name,'model':model,'property':prop(hit[2]),
                        'expression':expr,'evidence':[{'path':path,'line':m['line']+call['line']-1}]})

    def query_method(self,q):
        owner=q['owner'].split('@')[0]
        candidates=[m for m in self.methods.get(q['path'],[]) if m['name']==owner and
                    ('@' not in q['owner'] or str(m['line'])==q['owner'].split('@')[-1])]
        return candidates[0] if len(candidates)==1 else None

    def reaches(self,path,entry,target):
        """Bounded call reachability, cached per query/mapper (never by names alone)."""
        key=(path,entry['line'],target['line'])
        if key in self._reach_cache:return self._reach_cache[key]
        todo=[(entry,0)];seen=set();found=False
        while todo:
            method,depth=todo.pop(0);ident=(method['name'],method['line'])
            if ident in seen:continue
            seen.add(ident)
            if ident==(target['name'],target['line']):found=True;break
            if depth>=5:continue
            body=self.body(path,method);body=body[body.find('{')+1:]
            for call in _calls(body):
                name=call['name'].split('.')[-1]
                candidates=[m for m in self.methods[path] if m['name']==name and len(_params(m['signature']))==len(call['args'])]
                if len(candidates)==1:todo.append((candidates[0],depth+1))
        self._reach_cache[key]=found
        return found

    def write_input_role(self,path,method):
        """Separate a copy of a DB-loaded record from a submitted model.

        Does not infer a 'history' role from a table/method name. It checks the
        actual helper argument and the assignment from a SQL-reading method.
        Mixed or unresolved provenance is explicitly qualified, not guessed.
        """
        params=_params(method['signature'])
        positions=[i for i,(typ,_) in enumerate(params) if self.model_type(path,typ)]
        targets=[self.query_method(q) for q in self.operations if q['path']==path and q['operation']=='R']
        readers={m['name'] for m in self.methods[path] if any(target and self.reaches(path,m,target) for target in targets)}
        roles=set()
        for caller in self.methods[path]:
            body=self.body(path,caller);body=body[body.find('{')+1:]
            for call in _calls(body):
                if call['name'].split('.')[-1]!=method['name'] or len(call['args'])!=len(params):continue
                for i in positions:
                    arg=call['args'][i].strip()
                    # Examine only assignments before the call: future values cannot be its source.
                    assignments=list(re.finditer(r'\b'+re.escape(arg)+r'\s*=(?!=)\s*(.+?);',body[:call['start']],re.S)) if re.fullmatch(r'\w+',arg) else []
                    value=assignments[-1][1] if assignments else arg
                    if any(c['name'].split('.')[-1] in readers for c in _calls(value)):roles.add('database_snapshot')
                    else:roles.add('model_value')
        return 'database_snapshot' if roles=={'database_snapshot'} else 'mixed' if len(roles)>1 else 'model_value'

    def _read_edges(self):
        for path,methods in self.methods.items():
            queries=[q for q in self.operations if q['path']==path and q['operation']=='R']
            for m in methods:
                scope=self.scope(path,m)
                for call in _calls(self.body(path,m)):
                    hit=re.fullmatch(r'(\w+)\.set([A-Z\u0080-\uffff]\w*)',call['name'])
                    if not hit or not call['args']:continue
                    model=self.model_type(path,scope.get(hit[1],''))
                    if not model:continue
                    expr=call['args'][0];labels=[]
                    for c in _calls(expr):
                        if c['name'].split('.')[0] in scope and scope[c['name'].split('.')[0]].split('.')[-1]=='ResultSet':
                            if c['args'] and re.fullmatch(r'"[^"\n]+"',c['args'][0].strip()):labels.append(c['args'][0].strip()[1:-1])
                        elif any(scope.get(a.strip(),'').split('.')[-1]=='ResultSet' for a in c['args']):
                            labels.extend(a.strip()[1:-1] for a in c['args'] if re.fullmatch(r'"[^"\n]+"',a.strip()))
                    for q in queries:
                        query_method=self.query_method(q)
                        if not query_method or not self.reaches(path,query_method,m):continue
                        for label in labels:
                            for ref in select_columns(q['sql']).get(label,[]):
                                self.reads.append({**ref,'model':model,'property':prop(hit[2]),'direction':'read',
                                  'operation_id':q['id'],'query_owner':q['owner'],'expression':expr,'select_alias':label,
                                  'evidence':[{'path':path,'line':m['line']+call['line']-1},{'path':path,'line':q['line']}]})

    def _bind_calls(self,path,m,env=None,scope=None,depth=0):
        if depth>4:return [],False
        env=env or {};scope=scope or self.scope(path,m);body=self.body(path,m)
        # Exclude method declaration; capture only executable body.
        at=body.find('{');body=body[at+1:];base=m['line']+self.body(path,m)[:at+1].count('\n')
        bindings=[];index_values={k:int(v) for k,v in env.items() if str(v).isdigit()}
        for init in re.finditer(r'\bint\s+(\w+)\s*=\s*(\d+)\s*;',body):index_values[init[1]]=int(init[2])
        consumed=-1;complete=True
        for c in _calls(body):
            if c['start']<consumed:continue
            parts=c['name'].split('.');args=c['args'];name=parts[-1]
            if name=='prepareStatement':continue
            slot=None;expr=None;is_set=False
            if len(parts)==2 and scope.get(parts[0],'').split('.')[-1]=='PreparedStatement' and name in {'setString','setInt','setLong','setBigDecimal','setDate','setTime','setTimestamp','setBoolean','setObject','setNull','setDouble','setFloat','setBytes','setShort'} and len(args)>=2:
                slot=args[0];expr=args[1];is_set=True
            if not is_set:
                candidates=[x for x in self.methods[path] if x['name']==name and len(_params(x['signature']))==len(args)]
                candidates=[x for x in candidates if any(t.split('.')[-1]=='PreparedStatement' for t,n in _params(x['signature']))]
                if len(candidates)!=1:continue
                child=candidates[0];params=_params(child['signature']);formal_env=dict(zip((n for t,n in params),args))
                childbody=self.body(path,child)
                # One-position conversion helper (including NULL branch) occupies one parameter.
                direct=[x for x in _calls(childbody[childbody.find('{')+1:]) if '.' in x['name'] and x['name'].split('.')[-1].startswith('set')]
                index_names={x['args'][0].strip() for x in direct if x['args']}
                if direct and len(index_names)==1 and next(iter(index_names)) in formal_env and '++' not in next(iter(index_names)):
                    slot=formal_env[next(iter(index_names))]
                    value_args=[formal_env[n] for t,n in params if t.split('.')[-1] not in {'PreparedStatement','Connection'} and n!=next(iter(index_names))]
                    if not value_args:continue
                    expr=c['text'];is_set=True
                else:
                    bound_env={n:_sub(v,env) for n,v in formal_env.items()}
                    for k,v in list(bound_env.items()):
                        if v in index_values:bound_env[k]=str(index_values[v])
                    childscope={**self.scope(path,child),**scope}
                    nested,ok=self._bind_calls(path,child,bound_env,childscope,depth+1)
                    bindings.extend(nested);complete=complete and ok;consumed=c['end'];continue
            if is_set:
                raw=slot.strip();inc=raw.endswith('++');name_=raw[:-2].strip() if inc else raw
                value=index_values.get(name_)
                if value is None:
                    resolved=_sub(name_,env)
                    value=int(resolved) if resolved.isdigit() else None
                if value is None:
                    complete=False;continue
                if inc:index_values[name_]=value+1
                expression=_sub(re.sub(r'\b'+re.escape(name_)+r'\s*\+\+',str(value),expr),env)
                # Property resolution uses caller model aliases as well as formal scope.
                original_scope=self.scope(path,m)
                properties=[]
                for g in _GET.finditer(expression):
                    typ=scope.get(g[1],original_scope.get(g[1],''));model=self.model_type(path,typ)
                    if model:properties.append((model,prop(g[2])))
                if not properties:properties=self.properties(expr,path,m)
                bindings.append({'position':value,'expression':expression,'properties':list(dict.fromkeys(properties)),
                                 'evidence':[{'path':path,'line':base+c['line']-1}]})
                consumed=c['end']
        return bindings,complete

    def _write_edges(self):
        for q in self.operations:
            if q['operation'] not in {'C','U'} or q['path'] not in self.methods:continue
            path=q['path'];owner=q['owner'].split('@')[0]
            methods=[m for m in self.methods[path] if m['name']==owner and ('@' not in q['owner'] or str(m['line'])==q['owner'].split('@')[-1])]
            if len(methods)!=1:continue
            m=methods[0];bindings,ok=self._bind_calls(path,m)
            input_role=self.write_input_role(path,m)
            q['input_role']=input_role
            bypos=defaultdict(list)
            for b in bindings:bypos[b['position']].append(b)
            q['parameter_bindings']=[]
            # Parameter indexes are counted, not column ordinal when literal values exist.
            position=0
            for column,value in zip(q.get('columns',[]),q.get('values',[])):
                count=value.count('?')
                if count==1:
                    position+=1;choices=bypos.get(position,[])
                    if len({b['expression'] for b in choices})==1:
                        b=choices[0];q['parameter_bindings'].append({'column':column,**b})
                        for model,p in b['properties']:
                            self.writes.append({'table':q['table'],'column':column,'model':model,'property':p,'direction':'write',
                              'operation_id':q['id'],'query_owner':q['owner'],'expression':b['expression'],'position':position,'input_role':input_role,
                              'evidence':b['evidence']+[{'path':path,'line':q['line']}]})
                    elif choices:self.unresolved.append({'operation':q['id'],'position':position,'reason':'conditional_or_ambiguous_setters'})
                else:position+=count
            if not ok:self.unresolved.append({'operation':q['id'],'reason':'dynamic_parameter_index_or_helper'})

    def _jsp_properties(self,source,binding):
        text=self.sources.get(source,'');scope=_types(text);found=[]
        for tag in re.finditer(r'<(?:input|textarea|select)\b(?:<%[\s\S]*?%>|[^>])*>',text,re.I):
            name=re.search(r'\bname\s*=\s*[\"\']([^\"\']+)[\"\']',tag[0])
            if not name or name[1]!=binding:continue
            chunk=tag[0]
            if chunk.lower().startswith('<select'):
                end=text.find('</select>',tag.end());chunk=text[tag.start():end] if end>=0 else chunk
            elif chunk.lower().startswith('<textarea'):
                end=text.find('</textarea>',tag.end());chunk=text[tag.start():end] if end>=0 else chunk
            for g in _GET.finditer(chunk):
                model=self.model_type(source,scope.get(g[1],''))
                if model:found.append({'model':model,'property':prop(g[2]),'expression':g[0],
                                      'evidence':[{'path':source,'line':text.count('\n',0,tag.start())+1}]})
        return found

    def apply(self,feature):
        source=feature['source'];deps=set(feature['dependencies']);operation_ids={q['id'] for q in feature.get('sql_operations',[])}
        stats={'traced':0,'unresolved':0,'items':0}
        for item in feature['items']:
            if item['io']=='‐' or item.get('db')=='‐':continue
            stats['items']+=1;binding=item.get('binding','')
            origins=[e for e in self.requests if e['binding']==binding and e['evidence'][0]['path'] in deps]
            display=self._jsp_properties(source,binding) if source.endswith('.jsp') else []
            if display:
                displaykeys={(e['model'],e['property']) for e in display}
                if origins:origins=[e for e in origins if (e['model'],e['property']) in displaykeys] or origins
            candidates=[]
            for origin in origins+display:
                for edge in self.reads+self.writes:
                    if edge['operation_id'] not in operation_ids or edge['model']!=origin['model'] or edge['property']!=origin['property']:continue
                    table=self.tables.get(edge['table'].casefold())
                    if not table:continue
                    column=next((c for c in table['columns'] if c['name'].casefold()==edge['column'].casefold()),None)
                    if not column:continue
                    candidates.append({**edge,'table_logical':table['logical_name']['value'],'column_logical':column['logical_name']['value'],
                                       'binding':binding,'model_property':Path(edge['model']).stem+'.'+edge['property'],
                                       'evidence':origin['evidence']+edge['evidence'],
                                       'input_expression':origin['expression'],'status':'source_traced'})
            unique={}
            for edge in candidates:
                k=(edge['direction'],edge['table'],edge['column'],edge['operation_id'])
                unique.setdefault(k,edge)
            edges=list(unique.values());item['db_bindings']=edges
            if edges:
                stats['traced']+=1;names=[]
                for direction,jp in [('read','表示'),('write','保存')]:
                    refs=list(dict.fromkeys(e['table_logical']+'・'+e['column_logical'] for e in edges if e['direction']==direction and e.get('input_role')!='database_snapshot'))
                    if refs:names.append(jp+'：'+'／'.join(refs))
                item['db']='；'.join(names)
                item.setdefault('facts',{})['db']=fact(item['db'],[ev for e in edges for ev in e['evidence']],'derived')
                remarks=[]
                for e in edges:
                    text=('表示元' if e['direction']=='read' else '関連保存先（DBから取得した既存データ。画面入力の直接保存ではない）' if e.get('input_role')=='database_snapshot' else '保存先')+'：'+e['table']+'.'+e['column']+'。経由：'+binding+' → '+e['model_property']+'。'
                    if e.get('position'):text+='バインド順序：'+str(e['position'])+'。'
                    text+='加工・変換式：'+e['expression']+'。'
                    text+='処理：'+e.get('query_owner',e['operation_id'])+'。'
                    if e.get('input_role')=='mixed':text+='取得済みデータと入力モデルの複数経路を含むため、実行条件をイベント仕様で区別する。'
                    if text not in remarks:remarks.append(text)
                item['binding_remarks']='\n'.join(remarks)
                item.setdefault('source_description',item['description'])
                item['description']=item['source_description'].replace('業務上の制約は確認済みの範囲だけを記載する。','')+' DB対応の経由・加工は項目別DB連携備考を参照。'
            else:
                stats['unresolved']+=1
                item['binding_remarks']='DB列への接続を原本から確定できていない。名称が似ている列へ自動接続しない。'+item.get('db','')
                if '画面データ連携' in item.get('db',''):
                    item['db']=item['db'].replace('画面データ連携','DB項目未確定')
                    item.setdefault('facts',{})['db']=fact(item['db'],item.get('evidence',[]),'assumed')
        feature['binding_review']=stats
        return stats
