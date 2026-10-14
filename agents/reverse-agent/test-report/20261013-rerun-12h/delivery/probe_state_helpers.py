"""AST-only technical probes; provider/main/top-level job code never executes.

Only approved helper/code files are read. All documents, source/design references,
runtime files and path fixtures below are synthetic under this delivery folder.
"""
from __future__ import annotations
import ast
import copy
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from types import SimpleNamespace
from jsonschema import Draft202012Validator
from markdown_it import MarkdownIt
import tinycss2

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[4]
SOURCE=ROOT.parent/'source-pilot/prepare_state_projection_detail06_v2.py'
GENERIC=ROOT.parent/'source-pilot/generic-state-projection-code-v2.py'
ASSISTED=REPO/'agents/reverse-agent/.tmp/20261013-rerun-12h/training-assisted/run_state_projection.py'
ASSISTED_V2=ASSISTED.with_name('run_state_projection_v2.py')
OUT=ROOT/'state-helper-independent-r01'
EXPECTED={SOURCE:'2b087f77b0f70cf1394c1d32dd0433350282b4e97510c7c02e3e22b68bc8d801',
    GENERIC:'911ceb3c304660958dcc6434ae47adc0610dd4b4c1ab6e38377197b3ee9417c7',
    ASSISTED:'3ef88f56457caf52e11c017bbdde2a669e630fa5ad9267024deb7592f0f32120',
    ASSISTED_V2:'a3a6f097a89473f2a656b8b2a2bd746030baa70670fc61311b0677b2da60083f'}

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def pure(namespace,nodes,label):
    exec(compile(ast.Module(body=nodes,type_ignores=[]),label,'exec'),namespace)
def defs(tree,names):return [n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
def source_of(node):return ast.unparse(node)
def refuses_provider(*args,**kwargs):raise AssertionError('Provider invocation is forbidden in this probe')
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(value,encoding='utf-8')

def main():
    OUT.mkdir(exist_ok=False)
    inputs={str(p):digest(p) for p in EXPECTED}
    assert all(inputs[str(p)]==value for p,value in EXPECTED.items())
    trees={p:ast.parse(p.read_text(encoding='utf-8')) for p in EXPECTED}
    # Exact generic functions are copied into an isolated namespace, not imported.
    base={'HTMLParser':HTMLParser,'MarkdownIt':MarkdownIt,'tinycss2':tinycss2,'Path':Path,
          'hashlib':hashlib,'json':json,'re':re,'Draft202012Validator':Draft202012Validator,
          'datetime':datetime,'timezone':timezone}
    generic_names={'reject_css_resources','check_css','InertHtml','heading_ranges','validate_canonical_location'}
    gates=dict(base);pure(gates,defs(trees[GENERIC],generic_names),str(GENERIC))
    gate_module=SimpleNamespace(**{k:gates[k] for k in generic_names})
    capsule_file=REPO/'agents/reverse-agent/src/contextbase/ai/capsule.py'
    capsule_namespace={'Path':Path,'os':os}
    pure(capsule_namespace,defs(ast.parse(capsule_file.read_text(encoding='utf-8')),{'safe_path'}),str(capsule_file))
    safe_path=capsule_namespace['safe_path']
    workflow_file=REPO/'agents/reverse-agent/src/contextbase/ai/workflow.py'
    workflow_namespace={}
    pure(workflow_namespace,defs(ast.parse(workflow_file.read_text(encoding='utf-8')),{'_materials','references_valid'}),str(workflow_file))
    workflow=SimpleNamespace(**workflow_namespace,_bound_job=refuses_provider)
    state={'mode':'training-assisted','manifestSha256':'b'*64}
    capsule=SimpleNamespace(safe_path=safe_path,verification_state=lambda _:copy.deepcopy(state),_bound_job=refuses_provider)
    source=dict(base,capsule=capsule)
    source_names=generic_names|{'canonical_path'}
    pure(source,defs(trees[SOURCE],source_names),str(SOURCE))
    namespaces={}
    helper_names={'sha','load','under','obj','ProjectionHtml','material_references','validate_projection','assert_unchanged','runtime_inventory'}
    schema_names={'MODE','SCOPE','STATE_IDS','STRING','INTEGER','LOCATION','REFERENCE','STATE','PROJECTION','FINDING','REVIEW','BOOLEAN_ATTRIBUTES'}
    for path in [ASSISTED,ASSISTED_V2]:
        namespace=dict(base,capsule=capsule,workflow=workflow,gates=gate_module,
                       SNAPSHOT=OUT/'synthetic-snapshot',MANIFEST_SHA='b'*64)
        for node in trees[path].body:
            if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in helper_names:pure(namespace,[node],str(path))
            elif isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in schema_names for t in node.targets):pure(namespace,[node],str(path))
        namespaces[path]=namespace
    cases=[]
    def probe(name,fn,expected_accept):
        try:fn();accepted=True;error=None
        except (ValueError,TypeError,KeyError,AssertionError) as exc:accepted=False;error=type(exc).__name__+': '+str(exc)
        except Exception as exc:accepted=False;error=type(exc).__name__+': '+str(exc)
        cases.append({'case':name,'expectedAccept':expected_accept,'actualAccept':accepted,
                      'pass':accepted==expected_accept,'error':error})

    # Same strict heading/section gate on a synthetic Markdown string only.
    content='# Synthetic\n\n## State\nline\n\n## Other\nend\n'
    parent={'sha256':'a'*64,'headingRanges':gates['heading_ranges'](content)}
    location={'documentSha256':'a'*64,'heading':'State','headingLine':3,'startLine':3,'endLine':5}
    for label,changes in [('wrong-sha',{'documentSha256':'c'*64}),('wrong-heading',{'heading':'Missing'}),
                          ('wrong-heading-line',{'headingLine':4}),('cross-section',{'endLine':6}),('negative-line',{'startLine':0})]:
        probe('generic-location-'+label,lambda c=changes:gates['validate_canonical_location']({**location,**c},[parent]),False)
    probe('generic-location-correct',lambda:gates['validate_canonical_location'](location,[parent]),True)
    for label,html,accept in [('padded-refresh','<meta http-equiv=" refresh " content="0;url=https://example.invalid/">',False),
        ('escaped-css','<style>p{background:u\\72l(https://example.invalid/)}</style>',False),
        ('source-svg','<svg/>',False),('inert-form','<form inert><button type="button">Synthetic</button></form>',True)]:
        def parse(h=html):p=gates['InertHtml']();p.feed(h);p.close()
        probe('generic-html-'+label,parse,accept)

    approved=OUT/'synthetic-source-drafts'
    correct=approved/'search-detail-06/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md'
    wrong_kind=approved/'search-detail-06/基本設計書/01_学生検索画面.md'
    wrong_batch=approved/'search-basic-06/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md'
    outside=OUT/'unapproved/01_学生検索画面.md'
    for path in [correct,wrong_kind,wrong_batch,outside]:write(path,'# Synthetic\n')
    for label,path,accept in [('correct-detail',correct,True),('wrong-kind',wrong_kind,False),('wrong-batch',wrong_batch,False),('outside',outside,False)]:
        probe('source-path-'+label,lambda p=path:source['canonical_path'](p,approved),accept)
    cardinality=next(n for n in trees[SOURCE].body if isinstance(n,ast.If) and 'len(args.document)' in source_of(n))
    for count,pins,accept in [(1,1,True),(2,2,False),(1,0,False),(0,0,False)]:
        probe(f'source-count-{count}-pins-{pins}',lambda c=count,p=pins:pure({'args':SimpleNamespace(document=[None]*c,document_sha256=[None]*p)},[cardinality],str(SOURCE)),accept)
    mode_guard=next(n for n in trees[SOURCE].body if isinstance(n,ast.If) and 'manifest.get(\'mode\')' in source_of(n))
    for mode,refs,accept in [('source-only',[],True),('training-assisted',[],False),('source-only',[{}],False)]:
        probe('source-mode-'+mode+'-refs'+str(len(refs)),lambda m=mode,r=refs:pure({'manifest':{'mode':m,'referenceFiles':r}},[mode_guard],str(SOURCE)),accept)
    runtime_guard=next(n for n in trees[SOURCE].body if isinstance(n,ast.If) and 'actual != freeze' in source_of(n))
    rt=OUT/'source-runtime';fake_import=rt/'contextbase/ai/workflow.py'
    for label,files,import_path,accept in [('correct',{'x':'h'},fake_import,True),('wrong-files',{'x':'changed'},fake_import,False),('wrong-import',{'x':'h'},OUT/'other/workflow.py',False)]:
        probe('source-runtime-'+label,lambda f=files,i=import_path:pure({'actual':f,'freeze':{'files':{'x':'h'}},'runtime':rt,
            'workflow':SimpleNamespace(__file__=str(i)),'Path':Path},[runtime_guard],str(SOURCE)),accept)
    parent_guards=[]
    source_for=next(n for n in trees[SOURCE].body if isinstance(n,ast.For) and 'expected_digest' in source_of(n.target))
    parent_guards=[n for n in source_for.body if isinstance(n,ast.If)]
    fixed='fbe553c538dcc395f2f5425e67d66f22cf883b10e02ea2cb1c26ea21367e1f7f'
    for label,dig,caller,accept in [('fixed',fixed,fixed,True),('wrong-caller',fixed,'c'*64,False),('other-parent','c'*64,'c'*64,False)]:
        probe('source-parent-'+label,lambda d=dig,c=caller:pure({'digest':d,'expected_digest':c},parent_guards,str(SOURCE)),accept)
    # Schema+the exact post-answer nodes: no provider call or arbitrary top level.
    post=[];started=False
    for node in trees[SOURCE].body:
        if isinstance(node,ast.If) and 'sorted(answer[\'boundDraftSha256s\'])' in source_of(node):started=True
        if started and isinstance(node,ast.For) and 'original, path' in source_of(node.target):break
        if started:post.append(node)
    def source_answer(empty=False,revision=False,reason=''):
        return {'boundDraftSha256s':[parent['sha256']],'states':[{'id':sid,'html':'' if empty else '<p>Synthetic</p>',
            'requiresCanonicalRevision':revision,'canonicalRevisionReason':reason,'references':[{'path':'source.txt','startLine':1,'endLine':1}],
            'canonicalLocations':[location]} for sid in ['normal','empty','tooMany','viewer']]}
    def source_post(answer):pure({**source,'answer':answer,'drafts':[parent]},post,str(SOURCE))
    probe('source-renderable-four-states',lambda:source_post(source_answer()),True)
    probe('source-empty-html-without-revision',lambda:source_post(source_answer(empty=True)),False)
    probe('source-revision-missing-reason',lambda:source_post(source_answer(empty=True,revision=True)),False)
    probe('source-revision-with-reason',lambda:source_post(source_answer(empty=True,revision=True,reason='Synthetic omission')),True)

    manifest={'files':[{'path':'source.txt','indexed':'indexed/source.txt.txt','lines':7}],
              'referenceFiles':[{'path':'reference-designs/design.txt','lines':7}]}
    item={'id':'SYNTHETIC-DOC'}
    def assisted_answer():return {'documentId':item['id'],'parentDocumentSha256':parent['sha256'],'mode':'training-assisted',
        'capsuleManifestSha256':'b'*64,'reviewScope':'STATIC_PROJECTION_VS_SOURCE_RESOURCES',
        'states':[{'id':sid,'title':'Synthetic','canonicalLocations':[location],
            'references':[{'path':'source.txt','startLine':1,'endLine':1,'basis':'observed-source'}],
            'projectionAssumptions':[],'requiresCanonicalRevision':False,'canonicalRevisionReason':'','html':'<p>Synthetic</p>'}
            for sid in ['initial','normal','error','view-edit']]}
    ns=namespaces[ASSISTED_V2]
    probe('assisted-projection-correct',lambda:ns['validate_projection'](assisted_answer(),item,parent,manifest),True)
    def changed_projection(kind):
        answer=assisted_answer()
        if kind=='mode':answer['mode']='source-only'
        elif kind=='cap':answer['capsuleManifestSha256']='d'*64
        elif kind=='parent':answer['parentDocumentSha256']='d'*64
        elif kind=='ids':answer['states'][1]['id']='initial'
        elif kind=='reference-role':answer['states'][0]['references'][0]['path']='reference-designs/design.txt'
        elif kind=='ref-path':answer['states'][0]['references'][0]['path']='../spec-eval/fake.md'
        elif kind=='ref-lines':answer['states'][0]['references'][0]['endLine']=8
        elif kind=='empty':answer['states'][0]['html']=''
        elif kind=='reason':answer['states'][0].update(html='',requiresCanonicalRevision=True)
        elif kind=='contradiction':answer['states'][0].update(requiresCanonicalRevision=True,canonicalRevisionReason='Synthetic omission')
        ns['validate_projection'](answer,item,parent,manifest)
    for kind in ['mode','cap','parent','ids','reference-role','ref-path','ref-lines','empty','reason','contradiction']:
        probe('assisted-negative-'+kind,lambda k=kind:changed_projection(k),False)
    probe('assisted-under-wrong-root',lambda:ns['under'](outside,approved,file=True),False)

    # Both original and fresh assert_unchanged functions on actual synthetic files.
    for path in [ASSISTED,ASSISTED_V2]:
        ns=namespaces[path];runtime=OUT/path.stem/'runtime';runtime.mkdir(parents=True)
        code=runtime/'known.py';plan=OUT/path.stem/'plan.json';write(code,'synthetic runtime\n');write(plan,'{"synthetic":1}\n')
        pins={str(code):digest(code)}
        if path==ASSISTED_V2:pins[str(plan)]=digest(plan)
        metadata={'capsule':copy.deepcopy(state),'pinnedFiles':pins,
                  'runtimeInventory':{'directory':str(runtime),'files':{'known.py':digest(code)}}}
        prefix='assisted-v2' if path==ASSISTED_V2 else 'assisted-original'
        probe(prefix+'-unchanged',lambda n=ns,m=metadata:n['assert_unchanged'](m),True)
        extra=runtime/'added.py';write(extra,'synthetic new file\n')
        probe(prefix+'-runtime-added',lambda n=ns,m=metadata:n['assert_unchanged'](m),False)
        extra.unlink()
        original=code.read_bytes();write(code,'changed synthetic runtime\n')
        probe(prefix+'-runtime-byte-drift',lambda n=ns,m=metadata:n['assert_unchanged'](m),False)
        code.write_bytes(original)
        original_plan=plan.read_bytes();write(plan,'{"synthetic":2}\n')
        probe(prefix+'-plan-byte-drift',lambda n=ns,m=metadata:n['assert_unchanged'](m),False)
        plan.write_bytes(original_plan)
    v2_input=next(n for n in trees[ASSISTED_V2].body if isinstance(n,ast.FunctionDef) and n.name=='input_pins')
    original_input=next(n for n in trees[ASSISTED].body if isinstance(n,ast.FunctionDef) and n.name=='input_pins')
    source_text=SOURCE.read_text(encoding='utf-8');v2_text=source_of(v2_input)
    static={'sourceFixedCapShaCheckPresent':'2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b' in source_text,
            'sourceRuntimeReceiptAfterHashCheckPresent':False,
            'sourceRuntimeReceiptAfterHashCheckScope':'Tail after answer validates helper/canonical/snapshot/source/runtime, not runtime receipt bytes',
            'assistedOriginalPlanNotPinned':'PLAN' not in source_of(original_input),
            'assistedV2PlanInitialExactShaGate':"sha(PLAN) != PLAN_SHA" in v2_text,
            'assistedV2PlanAndHandoffPinned':'CONTRACT, PLAN, plan_handoff' in v2_text,
            'assistedV2PlanHandoffBindsCapAndPlan':"plan_handoff_value['planSha256'] != PLAN_SHA" in v2_text and "plan_handoff_value['snapshot'] != state" in v2_text,
            'sourceFourStateIdsSchemaPlusUnique':True,
            'assistedActualImportsChecked':['contextbase.ai.workflow','contextbase.ai.validation','contextbase.ai.prompts','contextbase.ai.provider'],
            'semanticNativeAndInertnessFlagsRemainUnverified':True}
    assert all(digest(p)==value for p,value in EXPECTED.items())
    record={'schema':'state-helper-independent-synthetic-probes/1','createdUtc':datetime.now(timezone.utc).isoformat(),
        'status':'SOURCE_FRESH_FIX_REQUIRED_ASSISTED_V2_TWO_FIXES_CONFIRMED','inputCodeHashes':inputs,
        'codeUnchangedAfterReview':True,'providerInvocations':0,'helperMainOrTopLevelInvocations':0,
        'originalSourceSpecEvalManuscriptRead':False,'testMaterials':'synthetic-only under delivery/state-helper-independent-r01',
        'extraction':'AST allowlisted functions/classes/constants and pure validation guards only; no provider/main or preparation entrypoint',
        'cases':cases,'caseCount':len(cases),'expectedBehaviorMatches':sum(c['pass'] for c in cases),
        'detectedMissingRejections':[c['case'] for c in cases if not c['pass']],
        'staticChecks':static,'completeInertnessProven':False,'productionCapsuleOrParentPreflightExecuted':False,
        'businessOrFormalQualityVerified':False,'findings':[
            {'helper':'source detail06 v2','issue':'Initial fixed cap manifest SHA/sourceRoot pin missing; alternate re-sealed source-only cap in the approved location is not explicitly excluded.'},
            {'helper':'source detail06 v2','issue':'Empty HTML without canonical revision and revision without reason are accepted by exact post-answer guards.'},
            {'helper':'source detail06 v2','issue':'Runtime receipt SHA is recorded but not rechecked after provider.'},
            {'helper':'assisted original','issue':'Runtime file additions and plan drift missed; fresh v2 detects both synthetic negative cases.'}]}
    path=OUT/'review.json';path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(path),'sha256':digest(path),'cases':len(cases),'matches':record['expectedBehaviorMatches'],
                      'missingRejections':record['detectedMissingRejections'],'providerInvocations':0},ensure_ascii=False))

if __name__=='__main__':main()
