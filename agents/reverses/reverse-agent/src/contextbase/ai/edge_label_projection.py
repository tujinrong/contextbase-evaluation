"""Conservative insertion-only flowchart edge-label layout projection.

This is not a Mermaid grammar replacement. Unsupported/ambiguous label syntax
fails closed. Source characters are never changed or removed. Only recorded
<br/> insertions occur inside recognized plain edge labels, never in canonical
Markdown. The caller must render with trusted Mermaid, compare SVG semantic
signatures, then validate visible rows and perform native image QA.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,re

BREAK='<br/>'
LATIN=re.compile(r'(?:[+-](?=[0-9]))?[A-Za-z0-9_$]+(?:[.:/\\-][A-Za-z0-9_$]+)*')
ENTITY=re.compile(r'(?:&(?:#[0-9]+|#x[0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9]*);|#[A-Za-z0-9]+;)')
BR=re.compile(r'<br\s*/?\s*>',re.I)
TAG=re.compile(r'<[^<>]*>')
# Mermaid 12.1's public bundled lexer families (START_LINK / LINK). Complete
# operators are tested first; only a remaining opener starts a long label.
ARROW=re.compile(r'(?:[xo<]?--+[-xo>]|[xo<]?==+[=xo>]|[xo<]?-?\.+-[xo>]?)')
LONG_START=re.compile(r'(?P<marker>[xo<]?)(?P<family>--|==|-\.)')
LONG_END={'--':re.compile(r'--+[-xo>]'),'==':re.compile(r'==+[=xo>]'),
          '-.':re.compile(r'-?\.+-[xo>]?')}
META={'subgraph','end','style','class','classDef','linkStyle','click','direction','accTitle','accDescr'}

class ProjectionError(ValueError):pass
class IndivisibleTokenError(ProjectionError):pass

def sha(text):return hashlib.sha256(text.encode('utf8')).hexdigest()

@dataclass(frozen=True)
class Label:
 start:int
 end:int
 contentStart:int
 contentEnd:int
 form:str
 quoted:bool
 markdown:bool

@dataclass(frozen=True)
class Insertion:
 sourceOffset:int
 outputOffset:int
 text:str=BREAK

@dataclass(frozen=True)
class Projection:
 sourceSha256:str
 projectedSha256:str
 text:str
 labels:tuple[Label,...]
 insertions:tuple[Insertion,...]
 supportedDiagram:bool

 def receipt(self):
  return {'sourceSha256':self.sourceSha256,'projectedSha256':self.projectedSha256,
   'supportedDiagram':self.supportedDiagram,'labels':[asdict(x) for x in self.labels],
   'insertions':[asdict(x) for x in self.insertions],'sourceChanged':False,
   'svgSignatureAndVisibleRowValidationRequired':True}

def _quote_end(text,i):
 quote=text[i];i+=1
 while i<len(text):
  if text[i]=='\\':i+=2;continue
  if text[i]==quote:return i+1
  i+=1
 raise ProjectionError('Unterminated quote; projection refused')

def _shape_end(text,i):
 pairs={'[':']','(':')','{':'}'};stack=[pairs[text[i]]];i+=1
 while i<len(text):
  if text[i] in '"\'`':i=_quote_end(text,i);continue
  tag=TAG.match(text,i)
  if tag:i=tag.end();continue
  if text[i] in pairs:stack.append(pairs[text[i]])
  elif text[i]==stack[-1]:
   stack.pop()
   if not stack:return i+1
  i+=1
 raise ProjectionError('Unterminated node shape; projection refused')

def _directive_end(text,i):
 # Public init/directive syntax is ignored as a complete opaque region.
 end=text.find('}%%',i+3)
 if end<0:raise ProjectionError('Unterminated Mermaid directive')
 return end+3

def _next_line(text,i):
 end=text.find('\n',i)
 return len(text) if end<0 else end+1

def _header_end(text):
 i=1 if text.startswith('\ufeff') else 0
 if text[i:].startswith('---') and re.match(r'---(?:\r?\n)',text[i:]):
  first=_next_line(text,i);match=re.search(r'^---\s*\r?$',text[first:],re.M)
  if not match:raise ProjectionError('Unterminated YAML front matter')
  i=_next_line(text,first+match.start())
 while i<len(text):
  if text[i].isspace():i+=1;continue
  if text.startswith('%%{',i):i=_directive_end(text,i);continue
  if text.startswith('%%',i):i=_next_line(text,i);continue
  match=re.match(r'(?:flowchart|graph)(?:[ \t]+(?:TB|TD|BT|LR|RL))?(?=[\s;]|$)',text[i:])
  return i+match.end() if match else None
 return None

def _label(text,start,end,form):
 a=start;b=end
 while a<b and text[a].isspace():a+=1
 while b>a and text[b-1].isspace():b-=1
 quoted=a<b and text[a]=='"'
 if quoted:
  q=_quote_end(text,a)
  if q!=b:raise ProjectionError('Partly quoted/ambiguous edge label')
  a+=1;b-=1
 markdown=b-a>=2 and text[a]=='`' and text[b-1]=='`'
 if not quoted and ('"' in text[a:b] or '`' in text[a:b]):
  raise ProjectionError('Mixed quoted/markdown edge label is unsupported')
 return Label(start,end,a,b,form,quoted,markdown)

def _pipe_label(text,pipe):
 i=pipe+1
 while i<len(text):
  if text[i]=='"':i=_quote_end(text,i);continue
  if text[i]=='\\':i+=2;continue
  tag=TAG.match(text,i)
  if tag:i=tag.end();continue
  if text[i]=='|':return _label(text,pipe+1,i,'pipe'),i+1
  if text[i] in '\r\n':raise ProjectionError('Unquoted multiline pipe label unsupported')
  i+=1
 raise ProjectionError('Unterminated pipe edge label')

def _long_label(text,start,family='--'):
 i=start
 while i<len(text):
  if text[i]=='"':i=_quote_end(text,i);continue
  if text[i]=='\\':i+=2;continue
  opaque=TAG.match(text,i) or ENTITY.match(text,i)
  if opaque:i=opaque.end();continue
  if text.startswith('%%',i):raise ProjectionError('Comment/directive before long edge label terminator')
  match=LONG_END[family].match(text,i)
  if match:return _label(text,start,i,{'--':'long-solid','==':'long-thick','-.':'long-dotted'}[family]),match.end()
  if text[i] in '\r\n;':return None,start
  i+=1
 return None,start

def _metadata_end(text,i,word):
 if word=='accDescr':
  start=re.match(r'accDescr\s*\{',text[i:])
  if start:return _shape_end(text,i+start.end()-1)
 if word=='subgraph':
  while i<len(text) and text[i] not in '\r\n':
   if text[i] in '"\'`':i=_quote_end(text,i)
   elif text[i] in '[({':i=_shape_end(text,i)
   else:i+=1
  return i
 return _next_line(text,i)

def flowchart_labels(text):
 i=_header_end(text)
 if i is None:return None
 labels=[];statement_start=True
 while i<len(text):
  c=text[i]
  if c.isspace() or c==';':
   if c in '\r\n;':statement_start=True
   i+=1;continue
  if text.startswith('%%{',i):i=_directive_end(text,i);continue
  if text.startswith('%%',i):i=_next_line(text,i);statement_start=True;continue
  if statement_start:
   word=re.match(r'[A-Za-z]+\b',text[i:])
   if word and word.group() in META:
    i=_metadata_end(text,i,word.group());statement_start=True;continue
  statement_start=False
  if c in '"\'`':i=_quote_end(text,i);continue
  if c in '[({':i=_shape_end(text,i);continue
  arrow=ARROW.match(text,i)
  if arrow:
   i=arrow.end();j=i
   while j<len(text) and text[j] in ' \t':j+=1
   if j<len(text) and text[j]=='|':
    label,i=_pipe_label(text,j);labels.append(label)
   continue
  opener=LONG_START.match(text,i)
  if opener:
   label,end=_long_label(text,opener.end(),opener['family'])
   if label:labels.append(label);i=end;continue
   i=opener.end();continue
  i+=1
 return tuple(labels)

def _atoms(text,label):
 i=label.contentStart;atoms=[]
 while i<label.contentEnd:
  match=BR.match(text,i) or TAG.match(text,i) or ENTITY.match(text,i)
  if match:
   atoms.append((i,match.end(),'break' if BR.fullmatch(match.group()) else 'opaque'));i=match.end();continue
  if text[i]=='\\' and i+1<label.contentEnd:
   atoms.append((i,i+2,'opaque'));i+=2;continue
  match=LATIN.match(text,i)
  if match:
   atoms.append((i,match.end(),'latin'));i=match.end();continue
  atoms.append((i,i+1,'space' if text[i].isspace() else 'other'));i+=1
 return atoms

def label_tokens(text,label):
 if label.markdown:return []
 return [text[a:b] for a,b,kind in _atoms(text,label) if kind=='latin']

def project_flowchart_edges(text):
 labels=flowchart_labels(text)
 if labels is None:return Projection(sha(text),sha(text),text,(),(),False)
 offsets=set()
 for label in labels:
  if label.markdown:continue # Markdown text has different layout semantics.
  atoms=_atoms(text,label)
  for k,(a,b,kind) in enumerate(atoms):
   if kind!='latin':continue
   if k and atoms[k-1][2] not in {'space','break'}:offsets.add(a)
   if k+1<len(atoms) and atoms[k+1][2] not in {'space','break'}:offsets.add(b)
 parts=[];insertions=[];last=0
 for ordinal,offset in enumerate(sorted(offsets)):
  parts.extend([text[last:offset],BREAK]);insertions.append(Insertion(offset,offset+ordinal*len(BREAK)));last=offset
 parts.append(text[last:]);projected=''.join(parts)
 result=Projection(sha(text),sha(projected),projected,labels,tuple(insertions),True)
 if reverse_projection(result)!=text:raise ProjectionError('Insert-only reversibility failed')
 return result

def reverse_projection(projection):
 text=projection.text
 if sha(text)!=projection.projectedSha256:raise ProjectionError('Projected bytes changed')
 for insert in reversed(projection.insertions):
  if text[insert.outputOffset:insert.outputOffset+len(insert.text)]!=insert.text:raise ProjectionError('Insertion receipt mismatch')
  text=text[:insert.outputOffset]+text[insert.outputOffset+len(insert.text):]
 if sha(text)!=projection.sourceSha256:raise ProjectionError('Recovered source SHA mismatch')
 return text

def validate_visible_rows(tokens,rows):
 """Reject a token that trusted Mermaid split between its actual SVG rows."""
 from collections import Counter
 for token,count in Counter(tokens).items():
  whole=re.compile(r'(?<![A-Za-z0-9_$])'+re.escape(token)+r'(?![A-Za-z0-9_$])')
  seen=sum(len(whole.findall(row)) for row in rows)
  if seen<count:raise IndivisibleTokenError('Indivisible label token does not fit a visible SVG row: '+token)
 return True

def validate_semantic_signature(original,projected):
 """The trusted renderer owns the structured node/edge/label signature."""
 if original!=projected:raise ProjectionError('View projection changes visible SVG node/edge/label semantics')
 return True

def _normalize(value):
 return ''.join(value.split())

def source_label_variants(text,label):
 """Match both Mermaid's escaped literal spelling and decoded entity spelling."""
 import html
 raw=text[label.contentStart:label.contentEnd]
 raw=BR.sub(' ',raw)
 encoded=re.sub(r'#(\d+);',lambda m:'&#'+m[1]+';',raw)
 encoded=re.sub(r'(?<!&)#([A-Za-z]+);',lambda m:'&'+m[1]+';',encoded)
 return {_normalize(v) for v in (raw,encoded,html.unescape(raw),html.unescape(encoded))}

def source_markdown_label_variants(text,label):
 """Bind unchanged Markdown labels to their literal text, never by count alone."""
 import html
 from markdown_it import MarkdownIt
 raw=text[label.contentStart+1:label.contentEnd-1]
 encoded=re.sub(r'#(\d+);',lambda m:'&#'+m[1]+';',raw)
 encoded=re.sub(r'(?<!&)#([A-Za-z]+);',lambda m:'&'+m[1]+';',encoded)
 values=set()
 for value in (raw,encoded):
  parts=[]
  for parent in MarkdownIt('commonmark',{'html':True}).parseInline(value):
   for token in parent.children or []:
    if token.type in {'text','code_inline'}:parts.append(token.content)
    elif token.type in {'softbreak','hardbreak'}:parts.append(' ')
    elif token.type=='html_inline':parts.append(TAG.sub('',BR.sub(' ',token.content)))
  plain=''.join(parts)
  values.update({_normalize(plain),_normalize(html.unescape(plain))})
 return values

def validate_svg_label_rows(source,projection,labels):
 """Bind source spans to actual SVG labels; reject unknown plain label mapping.

Markdown labels retain their baseline display and are outside token projection,
but still require literal text binding. No unknown SVG label is ignored. Plain
labels require exact literal mapping and whole visible tokens.
"""
 if not projection.supportedDiagram:return []
 matched=set();checks=[]
 for label in projection.labels:
  if label.markdown:
   variants=source_markdown_label_variants(source,label)
   candidates=[item for item in labels if _normalize(item['text']) in variants]
   if not candidates:raise ProjectionError('Author revision required: unchanged Markdown edge label literal mapping is unknown')
   for item in candidates:
    matched.add(item['id'])
    checks.append({'sourceRange':[label.contentStart,label.contentEnd],'edgeId':item['id'],
     'status':'MARKDOWN_BASELINE_DISPLAY_UNMODIFIED'})
   continue
  variants=source_label_variants(source,label)
  if variants=={''}:
   checks.append({'sourceRange':[label.contentStart,label.contentEnd],'status':'EMPTY_LABEL_UNMODIFIED'})
   continue
  candidates=[item for item in labels if _normalize(item['text']) in variants]
  if not candidates:raise ProjectionError('Author revision required: edge label literal mapping is unknown')
  tokens=label_tokens(source,label)
  for item in candidates:
   if _normalize(''.join(item['rows']))!=_normalize(item['text']):
    raise ProjectionError('Author revision required: an edge label has hidden or clipped SVG rows')
   try:validate_visible_rows(tokens,item['rows'])
   except IndivisibleTokenError as exc:
    raise IndivisibleTokenError('Author revision required: '+str(exc)) from exc
   matched.add(item['id'])
   checks.append({'sourceRange':[label.contentStart,label.contentEnd],'edgeId':item['id'],
    'tokens':tokens,'actualSvgRows':item['rows'],'status':'PASS_WHOLE_TOKENS'})
 unknown=[item for item in labels if item['id'] not in matched]
 if unknown:
  raise ProjectionError('Author revision required: an unparsed plain edge label has unknown literal mapping')
 return checks
