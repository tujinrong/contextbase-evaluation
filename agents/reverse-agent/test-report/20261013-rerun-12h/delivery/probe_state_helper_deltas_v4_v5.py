"""Two mode-isolated, code-only AST delta probes. No helper top level/provider."""
from __future__ import annotations
import ast, copy, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from html.parser import HTMLParser
from markdown_it import MarkdownIt
import tinycss2
from jsonschema import Draft202012Validator
HERE=Path(__file__).resolve().parent; REPO=HERE.parents[4]
A=REPO/'agents/reverse-agent/.tmp/20261013-rerun-12h/training-assisted'
S=HERE.parent/'source-pilot'
FILES={A/'run_state_projection_v4.py':'e94820ea65bb2734be542f090946525e5bd1e3fdf8d1967a3aa38ab1be9d2f4b',
 A/'run_state_projection_v3.py':'f7e1a54a3f964b6a3039fe07a645d5f89236b0da1dfc99c5818fbdd9844bded4',
 A/'projection_gates_v3.py':'07dda6548944755a5dee9742514da796af264ab1453836d0f1e8cc18db35f8ec',
 S/'prepare_state_projection_detail07_v5.py':'6fb6aaabaea7822aa6e74a7847c1d175f7d0b949f4df32b68f9b21b1c868237e',
 S/'prepare_state_projection_detail06_v4.py':'82c6bc13be740d0a0b67cc8c969b8fa2318a08e323e6745691abc0363d415caf'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(ns,nodes):exec(compile(ast.Module(body=nodes,type_ignores=[]),'<isolated-ast>','exec'),ns)
def assigns(tree,names):return [n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets)]
def dump(n):return ast.dump(n,include_attributes=False)
def main():
 out=HERE/'state-helper-independent-r04';out.mkdir(exist_ok=False)
 assert all(sha(p)==v for p,v in FILES.items())
 trees={p:ast.parse(p.read_text(encoding='utf-8')) for p in FILES};cases=[]
 def probe(mode,name,fn,accept=True):
  try:fn();actual=True;error=None
  except Exception as exc:actual=False;error=type(exc).__name__+': '+str(exc)
  cases.append({'mode':mode,'case':name,'expectedAccept':accept,'actualAccept':actual,'pass':accept==actual,'error':error})
 # Assisted only. Definitions and schema values only, no imports/main/preflight.
 at=trees[A/'run_state_projection_v4.py'];old=trees[A/'run_state_projection_v3.py'];g=trees[A/'projection_gates_v3.py']
 funcs={n.name:n for n in at.body if isinstance(n,ast.FunctionDef)}
 ns={};run(ns,[funcs['obj']]);names={'MODE','SCOPE','STATE_IDS','STRING','INTEGER','LOCATION','REFERENCE','STATE','PROJECTION','FINDING','REVIEW','BOOLEAN_ATTRIBUTES'};run(ns,assigns(at,names))
 def transport(schema):
  Draft202012Validator.check_schema(schema);pending=[schema]
  while pending:
   v=pending.pop()
   if isinstance(v,dict):
    if ('enum' in v or 'const' in v) and 'type' not in v:raise ValueError('Untyped fixed value')
    pending.extend(v.values())
   elif isinstance(v,list):pending.extend(v)
  assert json.loads(json.dumps(schema))==schema
 for name in ['PROJECTION','REVIEW']:probe('training-assisted',name+' typed-transport',lambda n=name:transport(ns[n]))
 for key,schema,value in [('mode','PROJECTION',ns['MODE']),('reviewScope','PROJECTION',ns['SCOPE']),('reviewScope','REVIEW',ns['SCOPE'])]:
  validator=Draft202012Validator(ns[schema]['properties'][key])
  probe('training-assisted',schema+'-'+key+'-fixed',lambda v=value:validator.validate(v))
  probe('training-assisted',schema+'-'+key+'-other',lambda:validator.validate('OTHER'),False)
  probe('training-assisted',schema+'-'+key+'-wrongtype',lambda:validator.validate(1),False)
 gate_ns={'HTMLParser':HTMLParser,'MarkdownIt':MarkdownIt,'tinycss2':tinycss2};run(gate_ns,[n for n in g.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))]);ns['gates']=SimpleNamespace(**gate_ns);run(ns,[n for n in at.body if isinstance(n,ast.ClassDef) and n.name=='ProjectionHtml'])
 for name,html,accept in [('bare','<input disabled>',True),('empty','<input readonly="">',True),('uppercase','<input disabled="DISABLED">',True),('mixed','<input checked="ChEcKeD">',True),('false','<input disabled="false">',False),('spaces','<input disabled=" disabled ">',False),('wrongname','<input readonly="disabled">',False),('javascript','<input checked onclick="alert(1)">',False)]:
  probe('training-assisted','boolean-'+name,lambda h=html:ns['ProjectionHtml']().feed(h),accept)
 old_funcs={n.name:dump(n) for n in old.body if isinstance(n,ast.FunctionDef)}
 assert all(dump(n)==old_funcs[n.name] for n in at.body if isinstance(n,ast.FunctionDef))
 # Source only. New pure approval/transport functions and selected top-level guards.
 st=trees[S/'prepare_state_projection_detail07_v5.py'];sv4=trees[S/'prepare_state_projection_detail06_v4.py'];sf={n.name:n for n in st.body if isinstance(n,ast.FunctionDef)}
 sns={'hashlib':hashlib,'json':json};run(sns,[sf['validate_approved_review'],sf['validate_transport_schema']])
 parent='a'*64;cap='b'*64;document='C:/synthetic/detail07.md'
 verified={'approved':True,'findings':[]};rv=json.dumps(verified).encode();rvh=hashlib.sha256(rv).hexdigest()
 handoff={'schema':'reverse-ai-review-handoff/1','approved':True,'reviewScope':'text-source-and-structure','referenceMode':'source-only','snapshot':{'mode':'source-only','manifestSha256':cap},'documentFile':document,'documentSha256':parent,'reviewSha256':rvh}
 hb=json.dumps(handoff).encode();hh=hashlib.sha256(hb).hexdigest()
 def approval(kind):
  h=copy.deepcopy(handoff);r=copy.deepcopy(verified);expected_hh=hh;expected_rh=rvh
  if kind=='mode':h['referenceMode']='training-assisted'
  elif kind=='snapshot-mode':h['snapshot']['mode']='training-assisted'
  elif kind=='cap':h['snapshot']['manifestSha256']='c'*64
  elif kind=='parent':h['documentSha256']='c'*64
  elif kind=='path':h['documentFile']='C:/synthetic/other.md'
  elif kind=='scope':h['reviewScope']='OTHER'
  elif kind=='approved':h['approved']=False
  elif kind=='verified-approved':r['approved']=False
  elif kind=='finding':r['findings']=[{'severity':'synthetic'}]
  rbytes=json.dumps(r).encode()
  if kind not in ['review-byte-drift','handoff-byte-drift']:expected_rh=hashlib.sha256(rbytes).hexdigest();h['reviewSha256']=expected_rh
  hbytes=json.dumps(h).encode()
  if kind not in ['review-byte-drift','handoff-byte-drift']:expected_hh=hashlib.sha256(hbytes).hexdigest()
  if kind=='review-byte-drift':rbytes+=b' '
  if kind=='handoff-byte-drift':hbytes+=b' '
  return sns['validate_approved_review'](hbytes,rbytes,expected_handoff_sha256=expected_hh,expected_review_sha256=expected_rh,document_file=document,document_sha256=parent,snapshot_sha256=cap)
 for kind in ['correct','mode','snapshot-mode','cap','parent','path','scope','approved','verified-approved','finding','review-byte-drift','handoff-byte-drift']:probe('source-only','approved-'+kind,lambda k=kind:approval(k),kind=='correct')
 schema_ns={**sns,'drafts':[{'sha256':parent}],'state':{'manifestSha256':cap}};run(schema_ns,assigns(st,{'ref_schema','location_schema','schema'}));probe('source-only','actual-schema-typed-transport',lambda:sns['validate_transport_schema'](schema_ns['schema']))
 probe('source-only','untyped-nested-enum',lambda:sns['validate_transport_schema']({'type':'object','properties':{'x':{'enum':['fixed']}}}),False)
 sv4func={n.name:dump(n) for n in sv4.body if isinstance(n,ast.FunctionDef)}
 assert all(dump(sf[name])==value for name,value in sv4func.items())
 path_guard=next(n for n in st.body if isinstance(n,ast.If) and 'exact reviewed detail07 canonical path' in ast.unparse(n))
 digest_guard=next(n for n in ast.walk(st) if isinstance(n,ast.If) and 'pinned exclusively to detail07' in ast.unparse(n))
 for label,path,accept in [('correct',Path(document),True),('other',Path('C:/synthetic/other.md'),False)]:probe('source-only','canonical-path-'+label,lambda p=path:run({'args':SimpleNamespace(document=[p]),'expected_document':Path(document)},[path_guard]),accept)
 for label,digest,accept in [('correct','85cddae02cf89e6e92d84ecc7709a118f298ca114bf104115f1be8ae47d62b82',True),('old','fbe553c538dcc395f2f5425e67d66f22cf883b10e02ea2cb1c26ea21367e1f7f',False)]:probe('source-only','canonical-pin-'+label,lambda d=digest:run({'digest':d},[digest_guard]),accept)
 post=next(n for n in st.body if isinstance(n,ast.If) and 'approved canonical review bytes changed during projection' in ast.unparse(n))
 for label,h,r,accept in [('same',hb,rv,True),('handoff',hb+b' ',rv,False),('review',hb,rv+b' ',False)]:probe('source-only','review-after-'+label,lambda h=h,r=r:run({'review_handoff_file':SimpleNamespace(read_bytes=lambda:h),'review_verified_file':SimpleNamespace(read_bytes=lambda:r),'review_handoff_before':hb,'review_verified_before':rv},[post]),accept)
 assert all(c['pass'] for c in cases) and all(sha(p)==v for p,v in FILES.items())
 record={'schema':'state-helper-independent-code-deltas/1','createdUtc':datetime.now(timezone.utc).isoformat(),'status':'TECHNICAL_DELTAS_EXPECTED_BEHAVIOR_MATCHED','codeHashes':{str(p):v for p,v in FILES.items()},'cases':cases,'caseCount':len(cases),'matches':sum(c['pass'] for c in cases),'providerInvocations':0,'topLevelInvocations':0,'originalSourceSpecEvalManuscriptRead':False,'codeUnchanged':True,'inheritedGuardsAstUnchanged':True,'completeInertnessProven':False,'providerTransportAcceptanceVerified':False,'businessOrFormalQualityVerified':False,'limitations':['Synthetic metadata only. Fixed files and provider CLI transport were not run.','Every source/assisted namespace is independent; no business input is shared.','HTML gates are partial; strict sanitizer and semantic/native QA remain necessary.']}
 path=out/'review.json';path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'report':str(path),'sha256':sha(path),'cases':len(cases),'matches':record['matches'],'providerInvocations':0}))
if __name__=='__main__':main()
