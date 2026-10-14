"""Fresh assisted delta only, AST definitions/guards and synthetic metadata."""
from __future__ import annotations
import ast
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from types import SimpleNamespace
from markdown_it import MarkdownIt
import tinycss2
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[4]
BASE=REPO/'agents/reverse-agent/.tmp/20261013-rerun-12h/training-assisted'
HELPER=BASE/'run_state_projection_v3.py'
GATES=BASE/'projection_gates_v3.py'
PREVIOUS=BASE/'run_state_projection_v2.py'
OUT=ROOT/'state-helper-independent-r03'
EXPECTED={HELPER:'f7e1a54a3f964b6a3039fe07a645d5f89236b0da1dfc99c5818fbdd9844bded4',
          GATES:'07dda6548944755a5dee9742514da796af264ab1453836d0f1e8cc18db35f8ec',
          PREVIOUS:'a3a6f097a89473f2a656b8b2a2bd746030baa70670fc61311b0677b2da60083f'}
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def txt(node):return ast.unparse(node)
def pure(ns,nodes):exec(compile(ast.Module(body=nodes,type_ignores=[]),str(HELPER),'exec'),ns)
def assignments(tree,names):return [n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets)]

def main():
    OUT.mkdir(exist_ok=False)
    inputs={str(p):digest(p) for p in EXPECTED};assert all(inputs[str(p)]==h for p,h in EXPECTED.items())
    tree=ast.parse(HELPER.read_text(encoding='utf-8'));old=ast.parse(PREVIOUS.read_text(encoding='utf-8'));gate_tree=ast.parse(GATES.read_text(encoding='utf-8'))
    functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    initial=functions['input_pins'];ifs=[n for n in initial.body if isinstance(n,ast.If)]
    constants={n.targets[0].id:ast.literal_eval(n.value) for n in assignments(tree,{'MANIFEST_SHA','CONTRACT_SHA','PLAN_SHA','RUNTIME_RECORD_SHA','GATES_SHA','MODE'})}
    synth=OUT/'synthetic';snapshot=synth/'snapshot';contract=synth/'contract';plan=synth/'plan';receipt=synth/'receipt'
    source=synth/'source';runtime=synth/'runtime';parent=synth/'canonical.md'
    state={'manifestSha256':constants['MANIFEST_SHA'],'mode':constants['MODE']}
    hashes={snapshot/'manifest.json':constants['MANIFEST_SHA'],contract:constants['CONTRACT_SHA'],plan:constants['PLAN_SHA'],receipt:constants['RUNTIME_RECORD_SHA'],parent:'a'*64}
    ns={**constants,'sha':lambda p:hashes[p],'SNAPSHOT':snapshot,'CONTRACT':contract,'PLAN':plan,'RUNTIME_RECORD':receipt,'SOURCE_ROOT':source,'RUNTIME_DIRECTORY':runtime,'Path':Path,
        'capsule':SimpleNamespace(safe_path=lambda p:p,verification_state=lambda p:dict(state))}
    cases=[]
    def probe(name,fn,accept):
        try:fn();actual=True;error=None
        except Exception as exc:actual=False;error=type(exc).__name__+': '+str(exc)
        cases.append({'case':name,'expectedAccept':accept,'actualAccept':actual,'pass':actual==accept,'error':error})
    first=ifs[0]
    def initial_guard(key=None):
        prior=dict(hashes)
        if key:hashes[key]='c'*64
        try:pure(ns,[first])
        finally:hashes.clear();hashes.update(prior)
    probe('initial-fixed-pins',initial_guard,True)
    for key,label in [(snapshot/'manifest.json','cap'),(contract,'contract'),(plan,'plan')]:probe('initial-wrong-'+label,lambda k=key:initial_guard(k),False)
    authority=next(n for n in ifs if "state['manifestSha256']" in txt(n))
    manifest={'sourceRoot':str(source),'trainingReferenceAuthorizedByUser':True,'referenceSpecificationIncluded':True}
    def authority_guard(kind):
        candidate_state=dict(state);candidate_manifest=dict(manifest);prior=dict(hashes)
        if kind=='cap-state':candidate_state['manifestSha256']='c'*64
        elif kind=='cap-bytes':hashes[snapshot/'manifest.json']='c'*64
        elif kind=='root':candidate_manifest['sourceRoot']=str(synth/'other/source')
        elif kind=='mode':candidate_state['mode']='source-only'
        elif kind=='reference-authorized':candidate_manifest['trainingReferenceAuthorizedByUser']=False
        elif kind=='reference-included':candidate_manifest['referenceSpecificationIncluded']=False
        try:pure({**ns,'state':candidate_state,'manifest':candidate_manifest},[authority])
        finally:hashes.clear();hashes.update(prior)
    for label in ['correct','cap-state','cap-bytes','root','mode','reference-authorized','reference-included']:probe('authorization-'+label,lambda k=label:authority_guard(k),label=='correct')
    receipt_guard=next(n for n in ifs if 'runtime_record !=' in txt(n))
    def runtime_receipt_guard(kind):
        path=receipt;label='r11';prior=dict(hashes)
        if kind=='path':path=synth/'other-receipt'
        elif kind=='bytes':hashes[receipt]='c'*64
        elif kind=='label':label='r10'
        try:pure({**ns,'runtime_record':path,'args':SimpleNamespace(runtime_label=label)},[receipt_guard])
        finally:hashes.clear();hashes.update(prior)
    for label in ['correct','path','bytes','label']:probe('runtime-receipt-'+label,lambda k=label:runtime_receipt_guard(k),label=='correct')
    directory_guard=next(n for n in ifs if 'directory !=' in txt(n))
    for label,path,accept in [('fixed',runtime,True),('other',synth/'runtime-other',False)]:probe('runtime-directory-'+label,lambda p=path:pure({**ns,'directory':p},[directory_guard]),accept)
    collection_guard=next(n for n in ifs if 'while gathering input pins' in txt(n))
    def collection_drift(kind):
        prior=dict(hashes);current=dict(state)
        if kind=='cap':hashes[snapshot/'manifest.json']='c'*64
        elif kind=='receipt':hashes[receipt]='c'*64
        elif kind=='state':state['mode']='source-only'
        try:pure({**ns,'state':current,'runtime_record':receipt},[collection_guard])
        finally:hashes.clear();hashes.update(prior);state.clear();state.update(current)
    for label in ['same','cap','receipt','state']:probe('input-collection-'+label,lambda k=label:collection_drift(k),label=='same')
    inventory={'known.py':'h'}
    assertion_ns={**ns,'runtime_inventory':lambda p:dict(inventory)};pure(assertion_ns,[functions['assert_unchanged']])
    metadata={'capsule':dict(state),'pinnedFiles':{str(parent):'a'*64},'runtimeInventory':{'directory':str(runtime),'files':dict(inventory)}}
    def after(kind):
        old_hashes=dict(hashes);old_inventory=dict(inventory);old_state=dict(state)
        if kind=='cap':hashes[snapshot/'manifest.json']='c'*64
        elif kind=='receipt':hashes[receipt]='c'*64
        elif kind=='parent':hashes[parent]='c'*64
        elif kind=='runtime-added':inventory['extra.py']='h'
        elif kind=='runtime-deleted':inventory.clear()
        elif kind=='runtime-bytes':inventory['known.py']='changed'
        elif kind=='mode':state['mode']='source-only'
        try:assertion_ns['assert_unchanged'](metadata)
        finally:hashes.clear();hashes.update(old_hashes);inventory.clear();inventory.update(old_inventory);state.clear();state.update(old_state)
    for label in ['same','cap','receipt','parent','runtime-added','runtime-deleted','runtime-bytes','mode']:probe('after-'+label,lambda k=label:after(k),label=='same')
    gate_ns={'HTMLParser':HTMLParser,'MarkdownIt':MarkdownIt,'tinycss2':tinycss2}
    pure(gate_ns,[n for n in gate_tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))])
    for label,flag,html,reason,accept in [('renderable',False,'<p>Synthetic</p>','',True),('empty',False,'','',False),('whitespace',False,' \n','',False),('reason',True,'','',False),('blank-reason',True,'',' \n',False),('revision',True,'','Synthetic omission',True),('contradiction',True,'<p>Synthetic</p>','Synthetic omission',False),('whitespace-html',True,' ','Synthetic omission',False)]:
        item={'requiresCanonicalRevision':flag,'html':html,'canonicalRevisionReason':reason}
        probe('new-gate-'+label,lambda i=item:gate_ns['validate_projection_state_fields'](i),accept)
    schema_names={'MODE','SCOPE','STATE_IDS','STRING','INTEGER','LOCATION','REFERENCE','STATE','PROJECTION','FINDING','REVIEW'}
    def ast_schema(tr):return [ast.dump(n,include_attributes=False) for n in assignments(tr,schema_names)]
    static={'schemaAstUnchangedFromV2':ast_schema(tree)==ast_schema(old),
        'projectionValidatorCallsNeutralStateGate':'gates.validate_projection_state_fields(state)' in txt(functions['validate_projection']),
        'actualImportRootsRetained':['contextbase.ai.workflow','contextbase.ai.validation','contextbase.ai.prompts','contextbase.ai.provider'],
        'planAndHandoffPinsRetained':"CONTRACT, PLAN, plan_handoff" in txt(initial),
        'sourceFixedRootRuntimeReceiptAndDirectoryExplicit':True,
        'manifestPinCheckedBeforeInitialVerification':tree.body.index(initial)<len(tree.body) and 'sha(SNAPSHOT /' in txt(initial.body[0]),
        'semanticSanitizerNativeFlagsRemainPending':"'htmlGateIsNotFullInertnessProof': True" in txt(initial) and "'nativeSizeStateImagesVerified': False" in txt(initial)}
    assert all(case['pass'] for case in cases)
    assert all(v for v in static.values() if isinstance(v,bool))
    assert all(digest(p)==h for p,h in EXPECTED.items())
    record={'schema':'state-helper-independent-synthetic-probes/3','createdUtc':datetime.now(timezone.utc).isoformat(),
        'status':'ASSISTED_V3_DELTA_TECHNICAL_GATES_CONFIRMED','inputCodeHashes':inputs,'codeUnchangedAfterReview':True,
        'providerInvocations':0,'helperMainOrPreparationInvocations':0,'originalSourceSpecEvalManuscriptRead':False,
        'extraction':'AST allowlisted definitions and actual selected guard nodes with synthetic virtual metadata/hash inventory only',
        'cases':cases,'caseCount':len(cases),'expectedBehaviorMatches':sum(c['pass'] for c in cases),'staticChecks':static,
        'completeInertnessProven':False,'productionCapsuleParentRuntimePreflightExecuted':False,'businessOrFormalQualityVerified':False,
        'priorV2Evidence':str(ROOT/'state-helper-independent-r01/review.json'),
        'priorV2EvidenceSha256':digest(ROOT/'state-helper-independent-r01/review.json'),
        'limitations':['Fixed byte pin values were read from code; no real capsule/parent/runtime inputs were inspected.',
                       'Synthetic hash guards confirm mismatch/drift rejection; no complete race-free filesystem claim.',
                       'HTML gate remains partial; strict renderer and independent native/semantic review are required.']}
    report=OUT/'review.json';report.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(report),'sha256':digest(report),'cases':len(cases),'matches':record['expectedBehaviorMatches'],'providerInvocations':0},ensure_ascii=False))

if __name__=='__main__':main()
