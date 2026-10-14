"""Pure AST guard/definition probes for the fresh source helper; no entrypoint."""
from __future__ import annotations
import ast
import copy
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from types import SimpleNamespace
from markdown_it import MarkdownIt
import tinycss2

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'source-pilot/prepare_state_projection_detail06_v4.py'
OUT=ROOT/'state-helper-independent-r02'
SHA='82c6bc13be740d0a0b67cc8c969b8fa2318a08e323e6745691abc0363d415caf'
CAP='2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b'
RECEIPT='ba00e60167417923a2630677374b67963ae09155aa647d0a7dfc02ac9d380c8f'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def text(node):return ast.unparse(node)
def pure(namespace,nodes):exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SOURCE),'exec'),namespace)

def main():
    OUT.mkdir(exist_ok=False)
    assert digest(SOURCE)==SHA
    tree=ast.parse(SOURCE.read_text(encoding='utf-8'))
    allowed={'reject_css_resources','check_css','InertHtml','heading_ranges','validate_canonical_location','validate_projection_state_fields'}
    namespace={'HTMLParser':HTMLParser,'MarkdownIt':MarkdownIt,'tinycss2':tinycss2}
    pure(namespace,[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in allowed])
    cases=[]
    def probe(name,fn,accept):
        try:fn();actual=True;error=None
        except Exception as exc:actual=False;error=type(exc).__name__+': '+str(exc)
        cases.append({'case':name,'expectedAccept':accept,'actualAccept':actual,'pass':actual==accept,'error':error})
    def select_if(fragment):return next(n for n in tree.body if isinstance(n,ast.If) and fragment in text(n))
    # Extract only the pin assignment, guard and verify assignment. Synthetic spy
    # supplies manifest bytes; none of the real files in the capsule are read.
    pin_index=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='pinned_manifest_before' for t in n.targets))
    before_verify=tree.body[pin_index:pin_index+3]
    assert isinstance(before_verify[0],ast.Assign) and isinstance(before_verify[1],ast.If)
    assert 'capsule.verify(args.snapshot)' in text(before_verify[2])
    spy_runs=[]
    def cap_spy(pin,accept):
        calls=[]
        cap=SimpleNamespace(sha256=lambda _:pin,material_path=lambda *_:SimpleNamespace(read_bytes=lambda:b'synthetic manifest'),
                            verify=lambda snapshot:calls.append(str(snapshot)) or {'mode':'source-only'})
        ns={'capsule':cap,'args':SimpleNamespace(snapshot='synthetic snapshot')}
        accepted=True;error=None
        try:pure(ns,before_verify)
        except ValueError as exc:accepted=False;error=str(exc)
        expected_calls=1 if accept else 0
        spy_runs.append({'pin':pin,'accepted':accepted,'verifyCalls':len(calls),'expectedVerifyCalls':expected_calls,'error':error})
        if accepted!=accept or len(calls)!=expected_calls:raise AssertionError('initial cap gate or no-read-before-pin failed')
    probe('fixed-cap-mismatch-rejects-before-verify',lambda:cap_spy('c'*64,False),True)
    probe('fixed-cap-authorized-reaches-verify-once',lambda:cap_spy(CAP,True),True)
    cap_after=select_if("state['manifestSha256']")
    for pin,accept in [(CAP,True),('c'*64,False)]:
        probe('cap-verification-state-'+('fixed' if accept else 'wrong'),lambda p=pin:pure({'state':{'manifestSha256':p}},[cap_after]),accept)
    src_root=select_if('original_root != capsule.safe_path')
    repo=OUT/'synthetic-repo';approved=repo/'test-project1/srcs/CSharp_ASPNET'
    for label,path,accept in [('correct',approved,True),('wrong-project',repo/'test-project2/srcs/CSharp_ASPNET',False),('wrong-mode',repo/'assisted/source',False)]:
        probe('source-root-'+label,lambda p=path:pure({'original_root':p,'capsule':SimpleNamespace(safe_path=lambda p:p),'repo':repo},[src_root]),accept)
    receipt=select_if('runtime_receipt_sha256 !=')
    for value,accept in [(RECEIPT,True),('c'*64,False)]:
        probe('receipt-initial-'+('fixed' if accept else 'wrong'),lambda p=value:pure({'runtime_receipt_sha256':p},[receipt]),accept)
    runtime_root=select_if('runtime != approved_base')
    base=repo/'source-only';approved_runtime=base/'runtime-code/source-06/src'
    for label,path,accept in [('correct',approved_runtime,True),('source-05',base/'runtime-code/source-05/src',False),('other-mode',repo/'training-assisted/runtime-code/source-06/src',False)]:
        probe('runtime-fixed-root-'+label,lambda p=path:pure({'runtime':p,'approved_base':base},[runtime_root]),accept)
    after_receipt=select_if('runtime_receipt_after_sha256 !=')
    for after,accept in [(RECEIPT,True),('c'*64,False)]:
        probe('receipt-after-'+('same' if accept else 'drift'),lambda p=after:pure({'runtime_receipt_after_sha256':p,'runtime_receipt_sha256':RECEIPT},[after_receipt]),accept)
    # Exact new field validator: strings are never normalized into accepted HTML.
    fields=[('renderable',False,'<p>Synthetic</p>','',True),('empty-no-revision',False,'','',False),
            ('whitespace-no-revision',False,' \n\t','',False),('revision-empty-reason',True,'','',False),
            ('revision-whitespace-reason',True,'',' \n',False),('revision-reason',True,'','Synthetic missing state',True),
            ('revision-html',True,'<p>Synthetic</p>','Synthetic missing state',False),
            ('revision-whitespace-html',True,' ','Synthetic missing state',False),
            ('bad-flag',1,'<p>Synthetic</p>','',False),('bad-html',False,None,'',False),('bad-reason',False,'<p>Synthetic</p>',None,False)]
    for label,flag,html,reason,accept in fields:
        item={'requiresCanonicalRevision':flag,'html':html,'canonicalRevisionReason':reason}
        probe('state-fields-'+label,lambda i=item:namespace['validate_projection_state_fields'](i),accept)
    # Run exact post-answer guard nodes with synthetic canonical heading evidence.
    post=[];started=False
    for node in tree.body:
        if isinstance(node,ast.If) and "sorted(answer['boundDraftSha256s'])" in text(node):started=True
        if started and isinstance(node,ast.For) and 'original, path' in text(node.target):break
        if started:post.append(node)
    parent={'sha256':'a'*64,'headingRanges':namespace['heading_ranges']('# Synthetic\n\n## State\nline\n\n## Other\nend\n')}
    location={'documentSha256':'a'*64,'heading':'State','headingLine':3,'startLine':3,'endLine':5}
    def answer():return {'boundDraftSha256s':['a'*64],'states':[{'id':sid,'html':'<p>Synthetic</p>',
        'requiresCanonicalRevision':False,'canonicalRevisionReason':'','references':[{'path':'synthetic-source.txt','startLine':1,'endLine':1}],
        'canonicalLocations':[copy.deepcopy(location)]} for sid in ['normal','empty','tooMany','viewer']]}
    def run_post(kind):
        obj=answer()
        if kind=='empty':obj['states'][0]['html']=''
        elif kind=='reason':obj['states'][0].update(html='',requiresCanonicalRevision=True)
        elif kind=='revision':obj['states'][0].update(html='',requiresCanonicalRevision=True,canonicalRevisionReason='Synthetic missing state')
        elif kind=='source-ref':obj['states'][0]['references']=[]
        elif kind=='canonical-ref':obj['states'][0]['canonicalLocations']=[]
        elif kind=='parent-sha':obj['boundDraftSha256s']=['c'*64]
        elif kind=='duplicate-id':obj['states'][1]['id']='normal'
        elif kind=='section-range':obj['states'][0]['canonicalLocations'][0]['endLine']=6
        pure({**namespace,'answer':obj,'drafts':[parent]},post)
    for kind,accept in [('normal',True),('empty',False),('reason',False),('revision',True),('source-ref',False),('canonical-ref',False),('parent-sha',False),('duplicate-id',False),('section-range',False)]:
        probe('post-answer-'+kind,lambda k=kind:run_post(k),accept)
    # Tail inventory guard requires exact maps, so byte drift, additions/deletions
    # are rejected. We run only this comparison, never the production scan.
    inventory=select_if('original_after != original_before')
    baseline={'known.py':'h'}
    for label,files,accept in [('same',baseline,True),('added',{**baseline,'new.py':'h'},False),('deleted',{},False),('bytes',{'known.py':'changed'},False)]:
        probe('runtime-inventory-after-'+label,lambda f=files:pure({'original_after':{'source':'h'},'original_before':{'source':'h'},'runtime_after':f,'actual':baseline},[inventory]),accept)
    static={
        'initialCapPinPrecedesVerify':pin_index<next(i for i,n in enumerate(tree.body) if 'manifest = capsule.verify' in text(n)),
        'receiptInitialFixedShaGate':RECEIPT in text(receipt),
        'receiptAfterComparedBeforeHandoff':next(i for i,n in enumerate(tree.body) if n is after_receipt)<next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='handoff' for t in n.targets)),
        'postAnswerCallsNewFieldValidator':any('validate_projection_state_fields(item)' in text(n) for n in post),
        'allFourStateSchemaPlusUniqueIds':'"normal", "empty", "tooMany", "viewer"' in SOURCE.read_text(encoding='utf-8') and any("len({item['id']" in text(n) for n in post),
        'sourceRootAndRuntimeFixedRootChecked':True,
        'runtimeCountBoundByFixedReceiptAndExactInventory':True,
        'directRuntimeModuleLocationCheck':'workflow.__file__ only; no blanket all-module provenance claim',
        'strictRendererAndIndependentSemanticNativeReviewRemainRequired':True,
    }
    assert digest(SOURCE)==SHA
    assert all(case['pass'] for case in cases)
    assert all(v for k,v in static.items() if isinstance(v,bool))
    record={'schema':'state-helper-independent-synthetic-probes/2','createdUtc':datetime.now(timezone.utc).isoformat(),
        'status':'SOURCE_V4_DELTA_TECHNICAL_GATES_CONFIRMED','inputCode':str(SOURCE),'inputSha256':SHA,'codeUnchangedAfterReview':True,
        'providerInvocations':0,'helperEntrypointOrTopLevelInvocations':0,'originalSourceSpecEvalManuscriptRead':False,
        'productionCapsuleParentOrRuntimePreflightExecuted':False,'completeInertnessProven':False,'businessOrFormalQualityVerified':False,
        'extraction':'AST allowlisted definitions and selected pure guard nodes only; no helper imports, preparation or provider',
        'cases':cases,'caseCount':len(cases),'expectedBehaviorMatches':sum(c['pass'] for c in cases),'initialManifestSpy':spy_runs,'staticChecks':static,
        'limitations':['Fixed parent SHA is still detail06 fbe553; detail07 requires a separately pinned fresh version and corresponding review.',
                       'No real parent/capsule/source/runtime files were read; 124-file count is not independently rescanned here.',
                       'Generic HTML gate is not a complete inertness proof; strict sanitizer and independent rendered visual/semantic review remain.'],
        'previousReport':str(ROOT/'state-helper-independent-r01/review.json'),
        'previousReportSha256':digest(ROOT/'state-helper-independent-r01/review.json')}
    report=OUT/'review.json';report.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(report),'sha256':digest(report),'cases':len(cases),'matches':record['expectedBehaviorMatches'],'providerInvocations':0},ensure_ascii=False))

if __name__=='__main__':main()
