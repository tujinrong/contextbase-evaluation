"""Bounded static Java SQL reconstruction; no input code or database is executed.

Resolves string constants, concatenation, builders and simple return templates.
Unresolved expressions remain explicit markers, never guessed SQL identifiers.
"""
from __future__ import annotations
import ast
import re
from collections import defaultdict
from specgen.common import tokens, pairs, split_top
from specgen.sql import sql_facts, identifier, QUALIFIED
from specgen.adapters.csharp_flow import analyze_flow


def literal(value):
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value[1:-1]


def analyze_sql(text: str, path: str) -> dict:
    ts=tokens(text); pm=pairs(ts)
    clean=list(text)
    # Tokenizer already excludes comments, but offsets/line numbers stay original.
    globals_={}; templates={}; helpers={}; append_helpers={}
    methods=analyze_flow(text,path)['methods']
    lines=text.splitlines(keepends=True)
    def fragment(a,b): return text[ts[a]['start']:ts[b]['end']] if b>=a else ''
    def ev(expr,env,depth=0):
        expr=expr.strip()
        if depth>8:return '〈再帰上限〉'
        if not expr:return ''
        parts=split_top(expr,'+')
        if len(parts)>1:return ''.join(str(ev(p,env,depth+1)) for p in parts)
        xt=tokens(expr); xp=pairs(xt)
        if len(xt)==1 and xt[0]['kind']=='string':return literal(xt[0]['text'])
        if expr in env:return env[expr]
        if expr.isdigit():return int(expr)
        if expr.endswith('.length') and expr[:-7] in env:return len(env[expr[:-7]])
        if expr.endswith('.toString()'):return env.get(expr[:-11],f'〈{expr}〉')
        if expr.startswith('{') and expr.endswith('}'):
            return [ev(p,env,depth+1) for p in split_top(expr[1:-1])]
        m=re.fullmatch(r'new\s+(?:StringBuilder|StringBuffer)\s*\((.*)\)',expr,re.S)
        if m:return ev(m[1],env,depth+1) if m[1].strip() else ''
        m=re.fullmatch(r'(\w+)\s*\((.*)\)',expr,re.S)
        if m:
            name=m[1];args=[ev(x,env,depth+1) for x in split_top(m[2])]
            if name in templates:
                params,body=templates[name]
                if len(args)==len(params):return ev(body,{**env,**dict(zip(params,args))},depth+1)
            kind=helpers.get(name)
            if kind=='join' and len(args)==2 and isinstance(args[0],list):return str(args[1]).join(map(str,args[0]))
            if kind=='assignments' and len(args)==1 and isinstance(args[0],list):return ', '.join(str(v)+' = ?' for v in args[0])
            if kind=='placeholders' and len(args)==1 and isinstance(args[0],int) and 0<=args[0]<=1000:return ', '.join('?' for _ in range(args[0]))
        # Do not erase expressions: later diagnostics can identify an incomplete query.
        return '〈'+re.sub(r'\s+',' ',expr)[:180]+'〉'
    for m in methods:
        body=''.join(lines[m['line']-1:m['end_line']])
        returns=re.findall(r'\breturn\s+([^;]+);',body,re.S)
        sig=re.search(r'\((.*?)\)',m['signature'],re.S)
        params=[re.sub(r'.*\s','',x.strip()) for x in split_top(sig[1])] if sig else []
        if len(returns)==1 and not re.search(r'\b(if|for|while|switch)\s*\(',body):
            templates[m['name']]=(params,returns[0])
        # Verify recognizable helper bodies, not just helper names.
        if re.search(r'\.append\(\w+\[\w+\]\)\.append\(" = \?"\)',body):helpers[m['name']]='assignments'
        elif re.search(r"\.append\('\?'\)",body) and 'count' in body:helpers[m['name']]='placeholders'
        elif re.search(r'\.append\(\w+\[\w+\]\)',body) and len(params)==2 and ('separator' in body):helpers[m['name']]='join'
    declarations=[]
    for i,t in enumerate(ts[:-3]):
        if t['text'] not in {'String','StringBuilder','StringBuffer'}:continue
        j=i+1
        if ts[j]['text']=='[' and j in pm:j=pm[j]+1
        if j+1>=len(ts) or ts[j+1]['text']!='=':continue
        k=j+2;start=k
        while k<len(ts) and ts[k]['text']!=';':
            k=pm[k]+1 if ts[k]['text'] in {'(','[','{'} and k in pm else k+1
        if k>=len(ts):continue
        owner=next((m for m in methods if m['line']<=t['line']<=m['end_line']),None)
        declarations.append((i,k,ts[j]['text'],fragment(start,k-1),owner))
    # Multi-pass forward constant resolution is bounded and deterministic.
    for _ in range(4):
        for a,b,name,expr,owner in declarations:
            if owner is None:globals_[name]=ev(expr,globals_)
    for method in methods:
        body=''.join(lines[method['line']-1:method['end_line']])
        sig=re.search(r'\((.*?)\)',method['signature'],re.S)
        params=[re.sub(r'.*\s','',x.strip()) for x in split_top(sig[1])] if sig else []
        append=re.findall(r'(\w+)\.append\((.*?)\)\s*;',body,re.S)
        value=re.search(r'(\w+)\.append\((\w+)\.get\((\w+)\)\)',body)
        if value and append and not re.search(r'\b(?:for|while)\s*\(',body):
            receiver,map_name,key_name=value.groups()
            if map_name in params and key_name in params and all(a==receiver for a,b in append):
                prefix=ev(append[0][1],globals_)
                if isinstance(prefix,str) and prefix.strip()==',':
                    append_helpers[method['name']]=(receiver,params,map_name,key_name)
    queries=[]
    def capture(sql,line,owner,origin):
        if not isinstance(sql,str) or not re.search(r'\b(?:SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM|MERGE\s+INTO)\b',sql,re.I):return
        if not re.match(r'^\s*(?:SELECT|INSERT|UPDATE|DELETE|MERGE)\b',sql,re.I):return
        _,crud,_=sql_facts(sql,ddl=False)
        for op in crud:
            name=op['table']
            if '〈' in name:continue
            if re.search(r'\b'+re.escape(name)+r'〈',sql):continue
            queries.append({'table':name,'operation':op['operation'],'sql':sql,'path':path,
                            'line':line,'owner':owner,'origin':origin,
                            'resolution':'partial_expression' if '〈' in sql else 'static_expression'})
    for a,b,name,expr,owner in declarations:
        if owner is None:capture(globals_.get(name),ts[a]['line'],'<constant:'+name+'>','constant')
    for method in methods:
        env=dict(globals_);decl={a:(b,n,e) for a,b,n,e,o in declarations if o is method}
        indexes=[i for i,t in enumerate(ts) if method['line']<=t['line']<=method['end_line']]
        if not indexes:continue
        lo,hi=indexes[0],indexes[-1];i=lo
        while i<=hi:
            if i in decl:
                b,n,e=decl[i];env[n]=ev(e,env);capture(env[n],ts[i]['line'],method['name']+'@'+str(method['line']),'assignment')
                # Skip the assignment but allow chained append calls in the initializer below.
            if i+3<=hi and ts[i+1]['text']=='.' and ts[i+2]['text']=='append' and ts[i+3]['text']=='(' and i+3 in pm:
                receiver=ts[i]['text'];j=i+1;chunks=[]
                while j+2<=hi and ts[j]['text']=='.' and ts[j+1]['text']=='append' and j+2 in pm:
                    end=pm[j+2];chunks.append(str(ev(fragment(j+3,end-1),env)));j=end+1
                env[receiver]=str(env.get(receiver,''))+''.join(chunks)
                i=j;continue
            if ts[i]['text'] in append_helpers and i+1 in pm:
                receiver,params,map_name,key_name=append_helpers[ts[i]['text']]
                end=pm[i+1];args=split_top(fragment(i+2,end-1))
                if len(args)==len(params) and receiver in env:
                    bound=dict(zip(params,args));key=ev(bound[key_name],env)
                    env[receiver]=str(env[receiver])+',〈'+bound[map_name]+'.get('+str(key)+')：空値・NULLの条件付き設定〉'
            if ts[i]['text']=='prepareStatement' and i+1 in pm:
                end=pm[i+1];sql=ev(fragment(i+2,end-1),env)
                capture(sql,ts[i]['line'],method['name']+'@'+str(method['line']),'prepared_statement')
            i+=1
        for value in env.values():
            if isinstance(value,str) and value not in globals_.values():capture(value,method['line'],method['name']+'@'+str(method['line']),'builder_or_local')
    # Literal SQL passed directly to a JDBC/custom execution method also matters.
    for t in ts:
        if t['kind']!='string':continue
        value=literal(t['text'])
        if not isinstance(value,str) or not re.match(r'^\s*(SELECT|INSERT|UPDATE|DELETE|MERGE)\b',value,re.I):continue
        owner=next((m for m in methods if m['line']<=t['line']<=m['end_line']),None)
        if owner:capture(value,t['line'],owner['name']+'@'+str(owner['line']),'literal_sql')
    # Longest reconstruction per source method/table/op supersedes partial prefixes.
    best={}
    for q in queries:
        key=(q['owner'],q['table'],q['operation'])
        if key not in best or len(q['sql'])>len(best[key]['sql']):best[key]=q
    return {'queries':list(best.values()),'constants':{k:v for k,v in globals_.items() if isinstance(v,(str,list,int))},
            'methods':methods}


def sql_details(query: dict) -> dict:
    sql=query['sql'];op=query['operation'];columns=[];values=[]
    if op=='C':
        m=re.search(r'\bINSERT\s+INTO\s+'+QUALIFIED+r'\s*\((.*?)\)\s*(?:VALUES\s*\((.*)\)|SELECT\s+(.*))',sql,re.I|re.S)
        if m:
            columns=[identifier(x) for x in split_top(m[1])]
            values=split_top(m[2] or m[3] or '')
    elif op=='U':
        m=re.search(r'\bSET\s+(.*?)(?:\s+WHERE\b|$)',sql,re.I|re.S)
        if m:
            for a in split_top(m[1]):
                c=re.match(r'(.+?)\s*=\s*(.*)',a,re.S)
                if c:columns.append(identifier(c[1]));values.append(c[2].strip())
    if op=='C' and len(values)!=len(columns):
        # Never shift a later value into an earlier column when helpers are unresolved.
        values=['対応する設定式は追加解析が必要（仮定）']*len(columns)
    where=re.search(r'\bWHERE\s+(.+?)(?:\s+ORDER\s+BY|\s+GROUP\s+BY|$)',sql,re.I|re.S)
    return {'columns':columns,'values':values,'where':where[1].strip() if where else '',
            'sql':sql}
