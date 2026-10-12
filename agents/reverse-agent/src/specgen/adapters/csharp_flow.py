"""Bounded static C#/Java brace analysis with explicit branches and state effects.

This adapter does not compile or execute input. Overloads, dynamic dispatch,
reflection and arbitrary expressions are retained as unresolved, not guessed.
"""
from __future__ import annotations
import re
from specgen.common import tokens, pairs, snippet, TOKEN


def semantic_text(value: str, limit: int = 4000) -> str:
    """Compact code whitespace without changing string/character literal values."""
    value=re.sub(r"(?i)((?:password|passwd|secret|api_?key|access_?token|connectionstring)\s*[=:]\s*)([\"'])(.*?)\2", r"\1'[REDACTED]'", value)
    result=[];end=0
    for match in TOKEN.finditer(value):
        gap=value[end:match.start()]
        if gap:result.append(' ')
        result.append(' ' if match.lastgroup=='comment' else match.group())
        end=match.end()
    text=''.join(result).strip()
    return text if len(text)<=limit else text[:limit]+' …（省略）'

CONTROLS = {'if','for','foreach','while','switch','catch','using','lock','synchronized'}


def analyze_flow(source: str, path: str) -> dict:
    ts = tokens(source)
    pm = pairs(ts)
    classes = []
    class_braces = set()
    for i, token in enumerate(ts[:-1]):
        if token['kind'] != 'word' or token['text'] not in {'class','interface','record','struct'}:
            continue
        j = i + 1
        if ts[j]['text'] in {'class','struct'}:
            j += 1
        if j >= len(ts):
            continue
        name = ts[j]['text']
        k = j + 1
        while k < len(ts) and ts[k]['text'] not in {'{',';'}:
            k = pm[k] + 1 if ts[k]['text'] in {'(', '['} and k in pm else k + 1
        if k < len(ts) and ts[k]['text'] == '{' and k in pm:
            class_braces.add(k)
            classes.append({'name':name, 'kind':token['text'], 'line':token['line'], 'body':k, 'end':pm[k]})
        else:
            classes.append({'name':name, 'kind':token['text'], 'line':token['line'], 'body':None, 'end':None})
    enclosing = {}
    stack = []
    for i,t in enumerate(ts):
        enclosing[i] = stack[-1] if stack else None
        if t['kind'] == 'symbol':
            if t['text'] == '{':
                stack.append(i)
            elif t['text'] == '}' and stack:
                stack.pop()

    def raw(a,b):
        return source[ts[a]['start']:ts[b-1]['end']] if a < b else ''

    def statement_end(a,limit):
        k=a
        while k < limit:
            if ts[k]['kind']=='symbol' and ts[k]['text'] in {'(', '[', '{'} and k in pm:
                k=pm[k]+1
            elif ts[k]['text']==';':
                return k+1
            else:
                k+=1
        return limit

    def statement(a,b,guards):
        value=semantic_text(raw(a,b).rstrip(';'))
        kind='statement'
        if ts[a]['text']=='return':kind='return'
        elif ts[a]['text']=='throw':kind='throw'
        elif re.search(r'(?<![=!<>])=(?!=|>)',value):kind='assignment'
        elif '(' in value:kind='call'
        node={'kind':kind, 'expression':value, 'line':ts[a]['line'], 'end_line':ts[b-1]['line'], 'guards':list(guards)}
        calls=[]
        for k in range(a,b-1):
            if ts[k]['kind']=='word' and ts[k+1]['text']=='(' and ts[k]['text'] not in CONTROLS | {'nameof','typeof','sizeof'}:
                start=k
                while start >= a+2 and ts[start-1]['text'] in {'.','?.'} and ts[start-2]['kind']=='word':start-=2
                close_call=pm.get(k+1)
                args=raw(k+2,close_call) if close_call is not None else ''
                calls.append({'name':raw(start,k+1), 'arguments':args, 'line':ts[k]['line'], 'guards':list(guards)})
        node['calls']=calls
        assignment=re.match(r'(?:var\s+)?([\w.]+)\s*=(?!=|>)(.*)',value,re.S)
        if kind=='assignment' and assignment:node.update(target=assignment[1],value=assignment[2].strip())
        if kind=='return':node['value']=value.removeprefix('return').strip()
        return node

    def one(a,limit,guards):
        word=ts[a]['text']
        if word=='{':
            end=pm.get(a,limit-1)
            return sequence(a+1,end,guards),end+1
        if word in CONTROLS and a+1<limit and ts[a+1]['text']=='(' and a+1 in pm:
            close=pm[a+1];condition=semantic_text(raw(a+2,close))
            condition_calls=statement(a+2,close,guards)['calls'] if close>a+2 else []
            branch={'kind':word,'condition':condition,'line':ts[a]['line'],'guards':list(guards),'calls':condition_calls}
            body,after=one(close+1,limit,guards+[condition]) if close+1<limit else ([],limit)
            branch['body']=body
            if word=='if' and after<limit and ts[after]['text']=='else':
                alternative,after=one(after+1,limit,guards+['NOT ('+condition+')'])
                branch['else']=alternative
            return [branch],after
        if word in {'try','finally','else','do'} and a+1<limit and ts[a+1]['text']=='{':
            body,after=one(a+1,limit,guards+[word])
            return [{'kind':word,'line':ts[a]['line'],'guards':list(guards),'body':body}],after
        if word==';':return [],a+1
        end=statement_end(a,limit)
        return [statement(a,end,guards)],max(a+1,end)

    def exits(nodes):
        if not nodes:return False
        n=nodes[-1]
        return n['kind'] in {'return','throw'} or (n['kind']=='if' and exits(n.get('body',[])) and exits(n.get('else',[])))

    def sequence(a,b,guards):
        result=[];active=list(guards)
        while a < b:
            group,a=one(a,b,active)
            result.extend(group)
            if group and group[-1]['kind']=='if':
                n=group[-1]
                if exits(n.get('body',[])) and not exits(n.get('else',[])):
                    active.append('NOT ('+n['condition']+')')
                elif n.get('else') and exits(n['else']) and not exits(n.get('body',[])):
                    active.append(n['condition'])
        return result

    methods=[]
    for i,t in enumerate(ts):
        if t['text']!='(' or i not in pm or i==0 or ts[i-1]['kind']!='word':continue
        if enclosing.get(i) not in class_braces:continue
        name=ts[i-1]['text']
        if name in CONTROLS | {'nameof','typeof','new'}:continue
        if i>1 and ts[i-2]['text'] in {'.','?.','new'}:continue
        close=pm[i];j=close+1
        while j<len(ts) and j<close+40 and ts[j]['text'] not in {'{','=>',';','=','}',',',')'}:j+=1
        if j>=len(ts) or ts[j]['text'] not in {'{','=>'}:continue
        start=i-1
        while start>0 and ts[start-1]['text'] not in {'{','}',';'}:start-=1
        prefix=raw(start,i-1)
        if re.search(r'\b(?:return|new|class|record|interface)\b|(?<![=!<>])=(?!=|>)',prefix):continue
        owner=next(c['name'] for c in classes if c['body']==enclosing[i])
        if ts[j]['text']=='{':
            end=pm.get(j)
            if end is None:continue
            flow=sequence(j+1,end,[])
        else:
            end=statement_end(j+1,len(ts))-1
            flow=[statement(j+1,end+1,[])]
            flow[0]['kind']='return'
        flattened=[]
        def walk(nodes):
            for n in nodes:
                flattened.append({k:v for k,v in n.items() if k not in {'body','else'}})
                walk(n.get('body',[]));walk(n.get('else',[]))
        walk(flow)
        methods.append({'name':name,'owner':owner,'path':path,'line':ts[start]['line'],'end_line':ts[end]['line'],
                        'signature':snippet(raw(start,j),1800),'flow':flow,'steps':flattened,
                        'calls':[c for n in flattened for c in n.get('calls',[])],
                        'status':'static_partial'})
    return {'types':[{k:v for k,v in c.items() if k not in {'body','end'}} for c in classes],
            'methods':methods,'limitations':['静的な構文・分岐・呼出候補の抽出。型解決、反射、例外伝播、到達可能性の完全解析ではない。']}
