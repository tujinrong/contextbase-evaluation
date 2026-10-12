"""Explicit query/placeholder/property lineage; no physical schema guessing."""
from __future__ import annotations
from collections import defaultdict
import re
from .refine import split_args, RESERVED


def parenthesized(text,opening):
    depth=0;quoted=False;i=opening
    while i<len(text):
        c=text[i]
        if c=='"':
            if quoted and i+1<len(text) and text[i+1]=='"':i+=2;continue
            quoted=not quoted
        elif not quoted:
            if c=='(':depth+=1
            elif c==')':
                depth-=1
                if depth==0:return text[opening+1:i],i
        i+=1
    return None,len(text)


def placeholder_properties(method):
    result=defaultdict(set)
    for st in method.get('statements',[]):
        for hit in re.finditer(r'\bSqlParameter\s*\(',st['text'],re.I):
            content,_=parenthesized(st['text'],hit.end()-1)
            if content is None:continue
            args=split_args(content)
            if len(args)<2 or not re.fullmatch(r'"\w+"',args[0]):continue
            properties=re.findall(r'\b(?:_?Model|order|mOrder|mChild)\.(\w+)',args[1],re.I)
            if len(set(properties))==1:result[args[0].strip('"').casefold()].add(properties[0])
    return result


def query_bindings(method):
    params=placeholder_properties(method);out=[]
    def add(obj,col,value,direction):
        for param in re.findall(r':(\w+)',value):
            for prop in params.get(param.casefold(),[]):
                out.append({'property':prop,'object':obj,'column':col,'direction':direction,'line':method['line']})
    for fragment in method.get('sql_fragments',[]):
        sql=fragment['sql']
        for hit in re.finditer(r'\bINSERT\s+INTO\s+([\w.]+)\s*\(([^)]+)\)\s*VALUES\s*\(',sql,re.I):
            body,_=parenthesized(sql,hit.end()-1)
            if body is None:continue
            cols=split_args(hit.group(2));vals=split_args(body)
            if len(cols)!=len(vals):continue
            for col,value in zip(cols,vals):
                if re.fullmatch(r'\w+',col):add(hit.group(1),col,value,'write')
        for hit in re.finditer(r'\bUPDATE\s+([\w.]+)\s+SET\s+([\s\S]*?)(?=\bWHERE\b|;|$)',sql,re.I):
            for assignment in split_args(hit.group(2)):
                pair=re.match(r'(\w+)\s*=\s*(.+)',assignment,re.S)
                if pair:add(hit.group(1),pair.group(1),pair.group(2),'write')
        # WHERE keys are selection, not writable columns.
        for hit in re.finditer(r'\b(?:UPDATE|DELETE\s+FROM)\s+([\w.]+)([\s\S]*?)(?=;|$)',sql,re.I):
            if 'WHERE' in hit.group(2).upper():
                tail=re.split(r'\bWHERE\b',hit.group(2),maxsplit=1,flags=re.I)[1]
                for pair in re.finditer(r'(?:\w+\.)?(\w+)\s*=\s*:(\w+)',tail):add(hit.group(1),pair.group(1),':'+pair.group(2),'key')
    return list({(x['property'],x['object'],x['column'],x['direction']):x for x in out}.values())


def enrich(data):
    methods=data['methods'];records=data['records']
    lineage=[]
    for mid,m in methods.items():
        for mapping in query_bindings(m):lineage.append(dict(mapping,path=m['path'],method=m['name']))
        objects=sorted({x['object'] for x in m.get('db',[]) if x['operation']=='R' and x['object'].upper() not in RESERVED})
        if len(objects)!=1:continue
        declared={p['name'].casefold():p['name'] for p in records[m['path']].get('fields',[])}
        for st in m.get('statements',[]):
            for hit in re.finditer(r'(?<!\w)(?:_?Model\.)?(\w+)\s*=\s*(?:(?:[\w.]+)\(\s*)?(?:drd|dr|row)\("(\w+)"\)',st['text'],re.I):
                prop=hit.group(1).lstrip('_');prop=declared.get(prop.casefold(),prop)
                lineage.append({'property':prop,'object':objects[0],'column':hit.group(2),'direction':'read','line':st['line'],'path':m['path'],'method':m['name']})
    for f in data['features']:
        related={f.get('code'),*f.get('models',[])}
        for item in f['items']:
            if item['role']=='operation' or not item.get('binding'):continue
            prop=item['binding'].split('.')[-1]
            item['db'] += [x for x in lineage if x['property'].casefold()==prop.casefold() and x['path'] in related]
            item['db']=list({(x['object'],x['column'],x.get('direction','read')):x for x in item['db']}.values())
            if item['db']:item['db_status']='source_mapping'
    data['lineage']=lineage
    return data
