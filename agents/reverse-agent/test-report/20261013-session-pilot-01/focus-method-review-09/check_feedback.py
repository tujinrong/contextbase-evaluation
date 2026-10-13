"""Read-only contract audit of safe feedback; reads no protected expectations/frozen tree."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from contextbase.ai import capsule, workflow

ROOT=Path.cwd().resolve(); REPORT=Path(__file__).resolve().parent
DIRECTORY=ROOT/'agents/reverse-agent/test-report/20261013-session-pilot-01/focus-feedback-round-04'
SNAPSHOT=ROOT/'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
DRIVER=ROOT/'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus_cycle.py'
OUTPUT=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-04/spec/detail'
STEMS=sys.argv[1:] or ['student-search']
assert set(STEMS)<= {'student-search','student-editor'} and len(set(STEMS))==len(STEMS)
observed={}
def observed_bytes(p):
    data=p.read_bytes()
    observed.setdefault(p,{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
    return data
def read(p): return json.loads(observed_bytes(p).decode('utf-8-sig'))
def sha(p): return hashlib.sha256(observed_bytes(p)).hexdigest()
def pin(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def keys(value,allowed,required=None):
    assert isinstance(value,dict)
    assert set(value)<=set(allowed),(set(value)-set(allowed))
    assert set(required or allowed)<=set(value),(set(required or allowed)-set(value))
def text(value): assert isinstance(value,str) and value.strip()
def raw_path(value):
    prefix=SNAPSHOT.relative_to(ROOT).as_posix()+'/'
    relative=value[len(prefix):] if value.startswith(prefix) else value
    assert relative.startswith(('sources/','reference-designs/')) and relative in materials
    return relative
pin(DRIVER); pin(SNAPSHOT/'manifest.json')
manifest=capsule.verify(SNAPSHOT); materials=workflow._materials(manifest)
assert capsule.reference_mode(manifest)=='training-assisted'
tree=ast.parse(DRIVER.read_text(encoding='utf-8'))
loop=next(n for n in tree.body if isinstance(n,ast.For) and ast.unparse(n.target)=='identity')
classification=next(n for n in loop.body if isinstance(n,ast.If) and "safe_feedback.get('classification')" in ast.unparse(n.test))
identity_gate=next(n for n in loop.body if isinstance(n,ast.If) and "safe_feedback.get('reviewDocumentId')" in ast.unparse(n.test))
alias_set=ast.literal_eval(classification.test.comparators[0])
assert alias_set=={'GENERATOR_SAFE_SOURCE_FEEDBACK','GENERATION_SAFE_SOURCE_BACKED_FEEDBACK','WRITER_SAFE_SOURCE_ONLY'}
gate_code=compile(ast.fix_missing_locations(ast.Module(body=[classification,identity_gate],type_ignores=[])),str(DRIVER),'exec')
paths=[DRIVER,SNAPSHOT/'manifest.json']; reports=[]; cases=[]
for stem in STEMS:
    identity={'student-search':'SM-DET-STUDENT-SEARCH','student-editor':'SM-DET-STUDENT-EDITOR'}[stem]
    path=DIRECTORY/(stem+'-feedback.json'); doc=OUTPUT/(stem+'.md'); value=read(path)
    compact=value['classification']=='WRITER_SAFE_SOURCE_ONLY'
    if compact:
        keys(value,['schema','classification','reviewDocumentId','generatedVersion','sourceBackedFindings','existingCorrectBehaviors','scope','notPerformed','provenance'])
        assert value['generatedVersion']=='4.0'
        text(value['scope']); assert isinstance(value['notPerformed'],list) and all(isinstance(x,str) for x in value['notPerformed'])
    else:
        keys(value,['schema','classification','reviewDocumentId','reviewDocumentVersion','reviewDate','projectId','profile','iteration','builderInputPolicy','provenance','sourceBackedFindings','existingCorrectBehaviors','validationScope'])
        assert value['reviewDocumentVersion']=='4.0'
        assert value['projectId']=='test-project1' and value['profile']=='CSharp_ASPNET' and value['iteration']=='20261013-focus-round-04'
    assert value['schema']=='source-backed-writer-feedback/1'
    assert value['reviewDocumentId']==identity
    assert value['classification'] in alias_set
    provenance=value['provenance']
    if compact:
        keys(provenance,['generated','sourcePins','builder','lineAndShaChecksPassed','semanticJudgementsHumanReviewed','builderAssignsSemanticJudgements'])
        keys(provenance['generated'],['path','sha256'])
        assert provenance['generated']['path']==doc.relative_to(ROOT).as_posix() and provenance['generated']['sha256']==sha(doc)
        assert provenance['builderAssignsSemanticJudgements'] is False
        assert all(type(provenance[k]) is bool for k in ['lineAndShaChecksPassed','semanticJudgementsHumanReviewed','builderAssignsSemanticJudgements'])
        keys(provenance['builder'],['path','sha256'])
        builder=ROOT/provenance['builder']['path']
        assert builder.parent==DIRECTORY and sha(builder)==provenance['builder']['sha256']; paths.append(builder)
    else:
        keys(provenance,['generatedPath','generatedSha256','sourceInputRoot','sourceInputs','checks'])
        assert provenance['generatedPath']==doc.relative_to(ROOT).as_posix() and provenance['generatedSha256']==sha(doc)
        assert provenance['sourceInputRoot']==SNAPSHOT.relative_to(ROOT).as_posix()
        checks=provenance['checks']
        keys(checks,['publishedEqualsFrozen','everyReferencedSourceEqualsAuthorizedCapsule','pointOrExpectedCellContentIncluded','actualApplicationOrDbTestPerformed'])
        assert all(type(v) is bool for v in checks.values())
        assert checks['pointOrExpectedCellContentIncluded'] is False
        assert checks['actualApplicationOrDbTestPerformed'] is False
    refs=[]; generated=[]
    finding_fields=['findingId','severity','title','observed','sourceBehavior','suggestion','sourceEvidence','generatedEvidence'] if compact else ['findingId','kind','observation','suggestedAction','sourceEvidence','generatedEvidence']
    preserve_fields=['behaviorId','behavior','sourceEvidence','generatedEvidence'] if compact else ['behaviorId','behavior','preserve','sourceEvidence','generatedEvidence']
    for name,idkey,allowed in [('sourceBackedFindings','findingId',finding_fields),('existingCorrectBehaviors','behaviorId',preserve_fields)]:
        entries=value[name]; assert isinstance(entries,list)
        assert len({e[idkey] for e in entries})==len(entries)
        for entry in entries:
            keys(entry,allowed)
            for k,v in entry.items():
                if k not in {'sourceEvidence','generatedEvidence'}: text(v)
            assert entry['sourceEvidence'] and entry['generatedEvidence']
            refs.extend(entry['sourceEvidence']); generated.extend(entry['generatedEvidence'])
    for ref in refs:
        keys(ref,['path','startLine','endLine','sha256'])
        original=SNAPSHOT/raw_path(ref['path']); assert sha(original)==ref['sha256']
        paths.append(original)
    normalized_refs=[dict(r,path=raw_path(r['path'])) for r in refs]
    workflow.references_valid({'findings':[{'references':normalized_refs}]},manifest)
    for ref in generated:
        keys(ref,['path','startLine','endLine','sha256'])
        assert ref['path']==doc.relative_to(ROOT).as_posix() and ref['sha256']==sha(doc)
        assert type(ref['startLine']) is int and type(ref['endLine']) is int
        assert 1<=ref['startLine']<=ref['endLine']<=len(doc.read_text(encoding='utf-8').splitlines())
    source_pins=provenance['sourcePins' if compact else 'sourceInputs']; assert len({p['path'] for p in source_pins})==len(source_pins)
    assert {raw_path(r['path']) for r in refs}<={raw_path(p['path']) for p in source_pins}
    if not compact: assert {p['path'] for p in source_pins}=={r['path'] for r in refs}
    for p in source_pins:
        keys(p,['path','sha256'] if compact else ['path','sha256','bytes']); raw=SNAPSHOT/raw_path(p['path']); assert sha(raw)==p['sha256']; paths.append(raw)
        if not compact: assert raw.stat().st_size==p['bytes']
    for label,alias,document_id,reject in [('new-explicit-alias','GENERATION_SAFE_SOURCE_BACKED_FEEDBACK',identity,False),('legacy-alias','GENERATOR_SAFE_SOURCE_FEEDBACK',identity,False),('legacy-writer-alias','WRITER_SAFE_SOURCE_ONLY',identity,False),('unknown-classification','UNCLASSIFIED',identity,True),('wrong-identity','GENERATION_SAFE_SOURCE_BACKED_FEEDBACK','MISMATCH',True)]:
        modified=deepcopy(value); modified['classification']=alias; modified['reviewDocumentId']=document_id
        error=None
        try: exec(gate_code,{'safe_feedback':modified,'identity':identity,'visual_review':{'documentId':identity},'text_review':{'documentId':identity}})
        except ValueError as exc: error=str(exc)
        assert bool(error)==reject
        cases.append({'document':identity,'case':label,'rejected':bool(error),'error':error,'status':'PASS'})
    paths.extend([path,doc])
    reports.append({'documentId':identity,'feedback':pin(path),'generatedMd':pin(doc),'sourcePinsVerified':len(source_pins),'sourceEvidenceRangesVerified':len(refs),'generatedEvidenceRangesVerified':len(generated),'authorizedReferenceRanges':sum(raw_path(r['path']).startswith('reference-designs/') for r in refs),'payloadVariant':'compact-root-relative-evidence' if compact else 'extended-snapshot-relative-evidence','feedbackFieldsStrictlySourceBacked':True,'scoreOrExpectationPayloadFieldsPresent':False,'originalContentsRewritten':False})
paths=list(dict.fromkeys(paths)); before=[observed[p] for p in paths]
after=[pin(p) for p in paths]; assert before==after
name='search-audit.json' if STEMS==['student-search'] else 'combined-audit.json'
(REPORT/name).write_text(json.dumps({'schema':'independent-safe-feedback-contract-audit/1','createdAt':datetime.now(timezone.utc).isoformat(),'status':'PASS','documents':reports,'driverAliasSet':sorted(alias_set),'gateLines':[classification.lineno,identity_gate.lineno],'cases':cases,'pins':before,'inputsUnchanged':True,'evaluatorOnlyOrSpecEvalRead':False,'originalSpecRead':False,'protectedExpectationsRead':False,'referenceDesignSemanticContentsRead':False,'sourceOrMdOrFeedbackOrProductionEdited':False,'externalAiOrRenderJobsStarted':False,'historicalBuilderReaderBehaviorProven':False,'scope':'Actual supplied safe JSON schema/identity/source-reference provenance and exact driver classification/identity gates, using capsule hash/range checks only. No scores or historical unseen reads inferred.'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','documents':len(reports),'cases':len(cases),'inputPins':len(before),'sourceRanges':sum(r['sourceEvidenceRangesVerified'] for r in reports),'generatedRanges':sum(r['generatedEvidenceRangesVerified'] for r in reports),'inputsUnchanged':True}))
