"""Strict flowchart-to-SVG adapter. Unknown syntax fails explicitly.

Graphviz renders only quoted labels and enumerated attributes; no application
source, URLs or arbitrary DOT is executed.
"""
from __future__ import annotations
import functools, html, json, re, shutil, subprocess
from bs4 import BeautifulSoup
from .common import sha

LABEL=r'((?:[^"\\]|\\.)*)'
NODE=re.compile(r'([A-Za-z_]\w*)(?:\[\("'+LABEL+r'"\)\]|\["'+LABEL+r'"\]|\{"'+LABEL+r'"\}|\("'+LABEL+r'"\)|\[([^\]\"]+)\])?')


def parse(source:str) -> dict:
    if source.lstrip().startswith('erDiagram'):
        from .er_diagram import parse_er
        return parse_er(source)
    lines=[line.strip().rstrip(';') for line in source.splitlines() if line.strip() and not line.lstrip().startswith('%%')]
    if not lines or not re.fullmatch(r'(?:flowchart|graph)\s+(?:LR|RL|TD|TB|BT)',lines[0]):
        raise ValueError('Static diagrams support flowchart LR/RL/TD/TB/BT only; unsupported syntax is not discarded')
    nodes={};edges=[]
    def node(value):
        m=NODE.match(value)
        if not m:raise ValueError('Unsupported node declaration: '+value)
        key=m[1];found=[(i,v) for i,v in enumerate(m.groups()[1:],2) if v is not None]
        if found:
            slot,label=found[0];label=html.unescape(json.loads('"'+label+'"') if slot<6 else label)
            shape={2:'cylinder',3:'box',4:'diamond',5:'ellipse',6:'box'}[slot]
            old=nodes.get(key)
            if old and old['declared'] and (old['label']!=label or old['shape']!=shape):raise ValueError('Conflicting diagram node: '+key)
            nodes[key]={'label':label,'shape':shape,'declared':True}
        else:nodes.setdefault(key,{'label':key,'shape':'box','declared':False})
        return key,value[m.end():].strip()
    for line in lines[1:]:
        left,rest=node(line)
        if not rest:continue
        match=re.match(r'-->(?:\|([^|]*)\|)?\s*',rest)
        dashed=False
        if match:label=match[1] or ''
        else:
            match=re.match(r'-\.\s*(.*?)\s*\.->\s*',rest);dashed=True
            if not match:raise ValueError('Unsupported flowchart edge: '+rest)
            label=match[1]
        right,tail=node(rest[match.end():])
        if tail:raise ValueError('Unsupported trailing diagram syntax: '+tail)
        edges.append({'from':left,'to':right,'label':html.unescape(label),'dashed':dashed})
    if not nodes:raise ValueError('Diagram contains no nodes')
    return {'direction':lines[0].split()[1].replace('TD','TB'),'nodes':nodes,'edges':edges}


@functools.lru_cache(maxsize=2048)
def _svg(source:str) -> tuple[str,dict]:
    graph=parse(source);dot=shutil.which('dot')
    if not dot:raise ValueError('Graphviz dot is required to regenerate diagrams. Install Graphviz and add dot to PATH. Published HTML needs no installation.')
    q=lambda s:json.dumps(s,ensure_ascii=False)
    lines=['digraph spec {','graph [rankdir='+graph['direction']+', bgcolor="transparent", pad="0.12", nodesep="0.28", ranksep="0.5"];',
        'node [fontname="Noto Sans CJK JP", fontsize=12, color="#7792a3", fillcolor="#f5f8fb", style="filled", margin="0.16,0.09"];',
        'edge [fontname="Noto Sans CJK JP", fontsize=10, color="#526f80", fontcolor="#344e5e", arrowsize=0.7];']
    for key,n in graph['nodes'].items():lines.append(q(key)+' [label='+q(n['label'])+', shape='+n['shape']+'];')
    for e in graph['edges']:
        extra=''
        if graph.get('kind')=='er':
            from .er_diagram import edge_attributes
            extra=edge_attributes(e)
        lines.append(q(e['from'])+' -> '+q(e['to'])+' [label='+q(e['label'])+', style='+('dashed' if e['dashed'] else 'solid')+extra+'];')
    lines.append('}')
    result=subprocess.run([dot,'-Tsvg'],input='\n'.join(lines),text=True,encoding='utf-8',capture_output=True,timeout=30)
    if result.returncode:raise ValueError('Diagram rendering failed: '+result.stderr[:500])
    svg=result.stdout[result.stdout.index('<svg'):];svg=svg[:svg.rfind('</svg>')+6]
    return svg,graph


def render(source:str,prefix:str) -> str:
    raw,graph=_svg(source)
    soup=BeautifulSoup(raw,'html.parser');svg=soup.find('svg')
    for node in soup.find_all(id=True):node['id']=prefix+'-'+node['id']
    svg['class']='flowchart-svg';svg['role']='img';svg['aria-label']='仕様の関連図・遷移図'
    svg['data-engine']='graphviz-er' if graph.get('kind')=='er' else 'graphviz-flowchart';svg['data-source-sha256']=sha(source)
    svg['data-node-count']=str(len(graph['nodes']));svg['data-edge-count']=str(len(graph['edges']))
    if len(svg.select('g.node'))!=len(graph['nodes']) or len(svg.select('g.edge'))!=len(graph['edges']):
        raise ValueError('SVG node or edge count changed during rendering')
    return str(svg)
