"""Code-only isolated added guard tests; production main and data are not read."""
import ast,copy,hashlib,json,types
from pathlib import Path
from datetime import datetime,timezone
H=Path(__file__).resolve().parent;B=H.parents[3]/'.tmp/20261013-rerun-12h/training-assisted'
V3=B/'prepare_fidelity_reuse_v3.py';V4=B/'prepare_fidelity_reuse_v4.py'
FIXED='6828db849bfed64ae4964b99a50168857bf4ce9b47fcf326ed22980126e06691';SEARCH='CSHARP_ASPNET-BAS-STU-01';HS='45ad4c9e8cb3702b24a85afd7cef2f10e140ecf4654897e5130104ef29539edd'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins={str(p):sha(p) for p in [V3,V4,B/'review_search_basic_fidelity_v3.py']};assert pins[str(V4)]==FIXED
t3,t4=[ast.parse(p.read_text(encoding='utf-8-sig')) for p in [V3,V4]]
def dump(n):return ast.dump(n,include_attributes=False)
def get(tree,name):return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
def reg(tree):return ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='HELPERS' for x in n.targets)))
m3,m4=get(t3,'main'),get(t4,'main');r3,r4=reg(t3),reg(t4)
bind=next(n for n in m4.body if isinstance(n,ast.If) and 'module.bind_previous_raw' in ast.unparse(n))
cover=next(n for n in m4.body if isinstance(n,ast.If) and 'module.validate_coverage' in ast.unparse(n))
oldcover=next(n for n in m3.body if isinstance(n,ast.If) and 'module.validate_coverage' in ast.unparse(n))
checks=[]
def check(n,c):checks.append({'name':n,'passed':bool(c)});assert c,n
check('fixed helper SHA',sha(V4)==FIXED)
check('registry role set unchanged',set(r3)==set(r4))
check('search binds independently inspected v3 helper exact SHA',r4[SEARCH]==('review_search_basic_fidelity_v3.py',HS) and sha(B/r4[SEARCH][0])==HS)
check('table and operation mappings unchanged',all(r3[n]==r4[n] for n in r3 if n!=SEARCH))
for n in ['sha','load','canonical_material']:check(n+' AST same',dump(get(t3,n))==dump(get(t4,n)))
normalized=copy.deepcopy(t4)
for n in normalized.body:
 if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='HELPERS' for x in n.targets):
  n.value=copy.deepcopy(next(x.value for x in t3.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=='HELPERS' for y in x.targets)))
 if isinstance(n,ast.FunctionDef) and n.name=='main':
  n.body=[copy.deepcopy(oldcover) if isinstance(x,ast.If) and 'module.validate_coverage' in ast.unparse(x) else x for x in n.body if not(isinstance(x,ast.If) and 'module.bind_previous_raw' in ast.unparse(x))]
check('all other guards prompts output and imports AST same after three deltas',dump(normalized)==dump(t3))
expected=ast.parse("args.document_id=='CSHARP_ASPNET-BAS-STU-01'",mode='eval').body
check('both added gates are search-only',dump(bind.test)==dump(expected)==dump(cover.test))
check('coverage validator precedes old binding assertions',ast.unparse(cover.body[0])=='module.validate_coverage(review, manifest, old)')
check('old assert follows exact parent inheritance comparisons',ast.unparse(cover.body[-1])=='module.state.assert_unchanged(old)')
check('bind after fixed role prepare before raw fidelity files',m4.body.index(bind)>next(i for i,n in enumerate(m4.body) if 'module.prepare()' in ast.unparse(n)) and m4.body.index(bind)<next(i for i,n in enumerate(m4.body) if 'args.fidelity_job' in ast.unparse(n)))
check('new coverage old binding before resume reference read outputs',m4.body.index(cover)<next(i for i,n in enumerate(m4.body) if 'workflow._resume_analysis' in ast.unparse(n))<next(i for i,n in enumerate(m4.body) if 'capsule.safe_path(reference).read_text' in ast.unparse(n)))
def code(n):return compile(ast.fix_missing_locations(ast.Module([copy.deepcopy(n)],[])),'<isolated-v4-added-guard>','exec')
bc,cc=code(bind),code(cover)
def probe(name,role=SEARCH,mutator=None,validator_error=False,pin_error=False,accepted=True):
 helper=Path('own-toy/helper.py');metadata={'previousRawReview':{'job':'toy-rejected-raw','rawReviewNotAccepted':True,'oldApprovalReused':False},'materialClosure':['sources/toy.txt','reference-designs/toy.md'],'completedAnalysisCheckpointSha256':'toy-checkpoint'}
 old={'pinnedFiles':{str(helper):HS},**copy.deepcopy(metadata)};review={'toy':'review'};manifest={'toy':'manifest'};calls=[]
 def bindprevious(m):calls.append(('bind',m));return {'toy':'raw'}, {'toy':'diagnostic'}
 def coverage(a,b,c):
  calls.append(('coverage',a,b,c))
  if validator_error:raise ValueError('toy invalid coverage')
 def assertunchanged(m):
  calls.append(('old-pins',m))
  if pin_error:raise ValueError('toy old input byte drift')
 ns={'args':types.SimpleNamespace(document_id=role),'metadata':metadata,'old':old,'helper':helper,'expected':HS,'review':review,'manifest':manifest,
  'module':types.SimpleNamespace(bind_previous_raw=bindprevious,validate_coverage=coverage,state=types.SimpleNamespace(assert_unchanged=assertunchanged))}
 if mutator:mutator(ns)
 outcome=True;error=None
 try:exec(bc,ns);exec(cc,ns)
 except (ValueError,KeyError,TypeError,AttributeError) as e:outcome=False;error=f'{type(e).__name__}: {e}'
 ok=outcome==accepted
 if accepted:
  if role==SEARCH:ok=ok and [c[0] for c in calls]==['bind','coverage','old-pins'] and calls[0][1] is metadata and calls[1][1] is review and calls[1][2] is manifest and calls[1][3] is old and calls[2][1] is old
  else:ok=ok and calls==[]
 checks.append({'name':name,'passed':bool(ok),'accepted':outcome,'error':error,'calls':[c[0] for c in calls]});assert ok,name
probe('positive exact inherited binding object identity and order')
for role in r4:
 if role!=SEARCH:probe('non-search '+role,role=role,validator_error=True,pin_error=True)
probe('coverage failure propagates before old assert',validator_error=True,accepted=False)
probe('old hash validator failure propagates',pin_error=True,accepted=False)
for field,val in [('previousRawReview',{}),('materialClosure',[]),('completedAnalysisCheckpointSha256','wrong')]:
 probe('old '+field+' mismatch',mutator=lambda ns,k=field,v=val:ns['old'].__setitem__(k,v),accepted=False)
probe('inherited raw approval claim drift',mutator=lambda n:n['old']['previousRawReview'].__setitem__('oldApprovalReused',True),accepted=False)
probe('old v3 pinned helper wrong SHA',mutator=lambda n:n['old']['pinnedFiles'].__setitem__(str(n['helper']),'0'*64),accepted=False)
probe('old pinned helper omitted',mutator=lambda n:n['old']['pinnedFiles'].clear(),accepted=False)
probe('old pinnedFiles wrong type',mutator=lambda n:n['old'].__setitem__('pinnedFiles',None),accepted=False)
probe('previousRawReview absent',mutator=lambda n:n['old'].pop('previousRawReview'),accepted=False)
probe('old closure absent',mutator=lambda n:n['old'].pop('materialClosure'),accepted=False)
probe('old checkpoint absent',mutator=lambda n:n['old'].pop('completedAnalysisCheckpointSha256'),accepted=False)
probe('closure order and additions not silently equivalent',mutator=lambda n:n['old'].__setitem__('materialClosure',list(reversed(n['old']['materialClosure']))),accepted=False)
check('code pins unchanged after audit',all(sha(Path(p))==s for p,s in pins.items()))
out={'schema':'code-only-independent-delta-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),'scope':'HELPER_CODE_AST_AND_ISOLATED_TOY_BINDING_GUARDS_ONLY','subject':str(V4),'subjectSha256':FIXED,'codePins':pins,'passedCount':sum(c['passed'] for c in checks),'testCount':len(checks),'tests':checks,'findings':[],'allOtherGuardFlowAstSame':True,'productionCanonicalSourceReferenceRawDiagnosticScoreExpectedReads':0,'actualMainPrepareProviderApplicationRuns':0,'limitations':['Production state.assert_unchanged and validate_coverage executed as spies/toy failures; actual production data and main were not exercised.','Scope establishes exact inheritance binding dispatch and rejection, not semantic unit completeness or repaired review approval.']}
p=H/'review.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'testCount':len(checks),'passedCount':out['passedCount'],'sha256':sha(p),'findings':[]}))
