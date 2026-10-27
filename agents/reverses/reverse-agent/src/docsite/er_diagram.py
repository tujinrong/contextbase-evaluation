"""Strict, non-executable Mermaid ER subset -> the shared static graph model."""
from __future__ import annotations
import json,re

NAME=r'([A-Za-z_]\w*|"[^"\n]+")'
CARD_LEFT={'||':'1','|o':'0..1','o|':'0..1','}|':'1..n','}o':'0..n'}
CARD_RIGHT={'||':'1','o|':'0..1','|o':'0..1','|{':'1..n','o{':'0..n'}

def parse_er(source:str)->dict:
    lines=[x.strip() for x in source.splitlines() if x.strip() and not x.strip().startswith('%%')]
    if not lines or lines.pop(0)!='erDiagram':raise ValueError('Expected erDiagram')
    nodes={};edges=[];active=None
    def name(x):return json.loads(x) if x.startswith('"') else x
    def ensure(key):
        nodes.setdefault(key,{'label':key,'shape':'box','declared':True,'attributes':[]})
    for line in lines:
        if active is not None:
            if line=='}':active=None;continue
            m=re.fullmatch(r'(\w+)\s+(\w+)(?:\s+(PK|FK|UK))?(?:\s+"([^"\n]*)")?',line)
            if not m:raise ValueError('Unsupported ER attribute: '+line)
            nodes[active]['attributes'].append({'type':m[1],'name':m[2],'key':m[3] or '', 'comment':m[4] or ''})
            continue
        if line.startswith('direction '):
            if line not in {'direction LR','direction TB','direction RL','direction BT'}:raise ValueError('Invalid ER direction')
            direction=line.split()[1];continue
        m=re.fullmatch(NAME+r'(?:\["([^"\n]+)"\])?\s*\{',line)
        if m:
            key=name(m[1]);ensure(key)
            if nodes[key]['attributes']:raise ValueError('Duplicate ER entity: '+key)
            if m[2]:nodes[key]['label']=m[2]
            active=key;continue
        m=re.fullmatch(NAME+r'\s+(\|\||\|o|o\||\}\||\}o)(--|\.\.)(\|\||o\||\|o|\|\{|o\{)\s+'+NAME+r'\s*:\s*"([^"\n]+)"',line)
        if not m:raise ValueError('Unsupported ER declaration: '+line)
        a,b=name(m[1]),name(m[5]);ensure(a);ensure(b)
        edges.append({'from':a,'to':b,'label':m[6],'dashed':m[3]=='..',
                      'tail_cardinality':CARD_LEFT[m[2]],'head_cardinality':CARD_RIGHT[m[4]]})
    if active:raise ValueError('Unclosed ER entity')
    if not nodes:raise ValueError('Empty ER diagram')
    for n in nodes.values():
        if n['attributes']:
            n['label']+='\n────────────\n'+'\n'.join((a['key']+'  ' if a['key'] else '')+a['name']+('  '+a['comment'] if a['comment'] else '') for a in n['attributes'])
    return {'kind':'er','direction':locals().get('direction','LR'),'nodes':nodes,'edges':edges}

def edge_attributes(e:dict)->str:
    markers={'1':'teetee','0..1':'teeodot','1..n':'crowtee','0..n':'crowodot'}
    return ', dir=both, arrowtail='+markers[e['tail_cardinality']]+', arrowhead='+markers[e['head_cardinality']]+', taillabel='+json.dumps(e['tail_cardinality'])+', headlabel='+json.dumps(e['head_cardinality'])
