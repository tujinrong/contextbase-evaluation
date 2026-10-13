"""Audit supplied safe payload only; no grading files, application or external job execution."""
import ast, hashlib, json, sys
from copy import deepcopy
from pathlib import Path
from datetime import datetime, timezone
from contextbase.ai import capsule, workflow
ROOT=Path.cwd().resolve(); REPORT=Path(__file__).resolve().parent
SNAPSHOT=ROOT/'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted'
FEEDBACK=ROOT/'agents/reverse-agent/test-report/20261013-session-pilot-01/focus-writer-input-round-05-v2'
OUTPUT=ROOT/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-05/spec/detail'
DRIVER=ROOT/'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus_cycle.py'
STEMS=sys.argv[1:] or ['student-search']; assert set(STEMS)<= {'student-search','student-editor'}
observed={}
def data(path):
    content=path.read_bytes(); actual={'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content)}
    if path in observed: assert observed[path]==actual, 'Input drift'
    else: observed[path]=actual
    return content
def sha(path): return hashlib.sha256(data(path)).hexdigest()
def read(path): return json.loads(data(path).decode('utf-8-sig'))
def save(path,value):
    with path.open('x',encoding='utf-8') as out: json.dump(value,out,ensure_ascii=False,indent=2); out.write('\n')
def keys(value,allowed,required=None):
    assert isinstance(value,dict) and set(value)<=set(allowed) and set(required or allowed)<=set(value), ('Unexpected/missing payload keys',set(value))
def text(value): assert isinstance(value,str) and value.strip()
def raw_path(value):
    prefix=SNAPSHOT.relative_to(ROOT).as_posix()+'/'
    relative=value[len(prefix):] if value.startswith(prefix) else value
    assert relative.startswith(('sources/','reference-designs/')) and relative in materials
    path=(SNAPSHOT/relative).resolve(); assert path.is_relative_to(SNAPSHOT)
    if relative.startswith('reference-designs/'): assert relative in authorized_refs
    return relative
driver_content=data(DRIVER); sha(SNAPSHOT/'manifest.json')
for name in ('capsule.py','workflow.py','schemas.py','validation.py'):
    sha(ROOT/'agents/reverse-agent/src/contextbase/ai'/name)
manifest=capsule.verify(SNAPSHOT); materials=workflow._materials(manifest)
authorized_refs={entry['path'] for entry in manifest['referenceFiles']}
assert len(authorized_refs)==11 and capsule.reference_mode(manifest)=='training-assisted'
tree=ast.parse(driver_content.decode('utf-8'))
loop=next(node for node in tree.body if isinstance(node,ast.For) and ast.unparse(node.target)=='identity')
classification=next(node for node in loop.body if isinstance(node,ast.If) and "safe_feedback.get('classification')" in ast.unparse(node.test))
identity_gate=next(node for node in loop.body if isinstance(node,ast.If) and "safe_feedback.get('reviewDocumentId')" in ast.unparse(node.test))
alias_set=ast.literal_eval(classification.test.comparators[0])
assert alias_set=={'GENERATOR_SAFE_SOURCE_FEEDBACK','GENERATION_SAFE_SOURCE_BACKED_FEEDBACK','WRITER_SAFE_SOURCE_ONLY'}
gate_code=compile(ast.fix_missing_locations(ast.Module(body=[classification,identity_gate],type_ignores=[])),str(DRIVER),'exec')
def verify_v2(value,stem):
    identity={'student-search':'SM-DET-STUDENT-SEARCH','student-editor':'SM-DET-STUDENT-EDITOR'}[stem]
    doc=OUTPUT/(stem+'.md')
    keys(value,['schema','classification','reviewDocumentId','generatedVersion','authoring','functionalContradictionsFound','evidenceRoots','sourceBackedFindings','existingCorrectBehaviors','scope','notPerformed','provenance'])
    assert value['schema']=='source-backed-writer-feedback/2' and value['classification'] in alias_set and value['reviewDocumentId']==identity and value['generatedVersion']=='5.0'
    assert type(value['functionalContradictionsFound']) is int and value['functionalContradictionsFound']>=0
    text(value['authoring']); text(value['scope']); assert isinstance(value['notPerformed'],list) and all(isinstance(item,str) for item in value['notPerformed'])
    expected_roots={'generated':OUTPUT.relative_to(ROOT).as_posix(),'sources':(SNAPSHOT/'sources').relative_to(ROOT).as_posix(),'authorizedDesigns':(SNAPSHOT/'reference-designs').relative_to(ROOT).as_posix()}
    assert value['evidenceRoots']==expected_roots
    p=value['provenance']; keys(p,['generatedPath','generatedSha256','authorizedDesignInputsAlreadyAvailableToWriter','humanStatementsReviewed','semanticStatementsAssembledByProgram'])
    assert p['generatedPath']==doc.relative_to(ROOT).as_posix() and p['generatedSha256']==sha(doc)
    assert all(type(p[name]) is bool for name in ['authorizedDesignInputsAlreadyAvailableToWriter','humanStatementsReviewed','semanticStatementsAssembledByProgram'])
    assert p['authorizedDesignInputsAlreadyAvailableToWriter'] is True and p['semanticStatementsAssembledByProgram'] is False
    refs=[]; generated=[]
    for collection in ['sourceBackedFindings','existingCorrectBehaviors']:
        entries=value[collection]; assert isinstance(entries,list)
        id_key='findingId' if collection=='sourceBackedFindings' else 'behaviorId'
        allowed=['findingId','findingKind','severity','title','observed','suggestion','generatedEvidence','sourceEvidence','authorizedDesignEvidence'] if collection=='sourceBackedFindings' else ['behaviorId','behavior','generatedEvidence','sourceEvidence']
        assert len({entry[id_key] for entry in entries})==len(entries)
        for entry in entries:
            keys(entry,allowed)
            for name,item in entry.items():
                if name not in {'sourceEvidence','generatedEvidence','authorizedDesignEvidence'}: text(item)
            if collection=='sourceBackedFindings': assert entry['severity'] in {'critical','major','minor'}
            assert entry['sourceEvidence'] and entry['generatedEvidence']
            assert all(ref['root']=='sources' for ref in entry['sourceEvidence'])
            assert all(ref['root']=='authorizedDesigns' for ref in entry.get('authorizedDesignEvidence',[]))
            assert all(ref['root']=='generated' for ref in entry['generatedEvidence'])
            refs.extend(entry['sourceEvidence']+entry.get('authorizedDesignEvidence',[])); generated.extend(entry['generatedEvidence'])
    normalized=[]; distinct=set()
    for ref in refs+generated:
        keys(ref,['root','path','startLine','endLine','sha256']); assert ref['root'] in expected_roots
        relative=Path(ref['path']); assert not relative.is_absolute() and '\\' not in ref['path'] and str(relative.as_posix())==ref['path'] and '..' not in relative.parts
        base=ROOT/expected_roots[ref['root']]; path=(base/ref['path']).resolve(); assert path.is_relative_to(base)
        if ref['root']=='generated': assert path==doc
        else:
            material=path.relative_to(SNAPSHOT).as_posix(); raw_path(material); distinct.add(material)
            normalized.append(dict(path=material,startLine=ref['startLine'],endLine=ref['endLine'],sha256=ref['sha256']))
        assert sha(path)==ref['sha256'] and type(ref['startLine']) is int and type(ref['endLine']) is int
        assert 1<=ref['startLine']<=ref['endLine']<=len(data(path).decode('utf-8-sig').splitlines())
    workflow.references_valid({'findings':[{'references':normalized}]},manifest)
    return {'documentId':identity,'sourcePins':len(distinct),'sourceRanges':len(refs),'generatedRanges':len(generated),'authorizedReferenceRanges':sum(ref['root']=='authorizedDesigns' for ref in refs),'rawSourceRanges':sum(ref['root']=='sources' for ref in refs),'feedbackVariant':'v2-explicit-evidence-root-map','allCitedRangesAndHashesValid':True,'sourceRefs':normalized,'generatedRefs':generated}
def verify(value,stem):
    if value.get('schema')=='source-backed-writer-feedback/2': return verify_v2(value,stem)
    identity={'student-search':'SM-DET-STUDENT-SEARCH','student-editor':'SM-DET-STUDENT-EDITOR'}[stem]
    doc=OUTPUT/(stem+'.md'); document_data=data(doc); document_lines=document_data.decode('utf-8-sig').splitlines()
    compact='generatedVersion' in value
    compact_design=compact and 'authorizedDesignPins' in value['provenance']
    if compact:
        allowed_top=['schema','classification','reviewDocumentId','generatedVersion','sourceBackedFindings','existingCorrectBehaviors','scope','notPerformed','provenance']
        if compact_design: allowed_top.append('functionalContradictionsFound')
        keys(value,allowed_top)
        if compact_design: assert type(value['functionalContradictionsFound']) is int and value['functionalContradictionsFound']>=0
        assert value['generatedVersion']=='5.0'; text(value['scope'])
        assert isinstance(value['notPerformed'],list) and all(isinstance(item,str) for item in value['notPerformed'])
    else:
        keys(value,['schema','classification','reviewDocumentId','reviewDocumentVersion','reviewDate','projectId','profile','iteration','builderInputPolicy','provenance','sourceBackedFindings','existingCorrectBehaviors','limitations'])
        assert value['reviewDocumentVersion']=='5.0' and value['projectId']=='test-project1' and value['profile']=='CSharp_ASPNET'
        assert value['iteration']=='20261013-focus-round-05'; text(value['builderInputPolicy'])
        assert isinstance(value['limitations'],list) and all(isinstance(item,str) for item in value['limitations'])
    assert value['schema']=='source-backed-writer-feedback/1' and value['classification'] in alias_set and value['reviewDocumentId']==identity
    provenance=value['provenance']
    if compact:
        review_flag='statementsHumanReviewed' if compact_design else 'semanticJudgementsHumanReviewed'
        allowed_provenance=['generated','sourcePins','builder','lineAndShaChecksPassed',review_flag,'builderAssignsSemanticJudgements']
        if compact_design: allowed_provenance.append('authorizedDesignPins')
        keys(provenance,allowed_provenance)
        keys(provenance['generated'],['path','sha256']); generated=provenance['generated']; pins=provenance['sourcePins']+provenance.get('authorizedDesignPins',[])
        assert generated['path']==doc.relative_to(ROOT).as_posix() and generated['sha256']==sha(doc)
        keys(provenance['builder'],['path','sha256']); builder=(ROOT/provenance['builder']['path']).resolve()
        assert builder.parent==FEEDBACK and sha(builder)==provenance['builder']['sha256']
        assert all(type(provenance[name]) is bool for name in ['lineAndShaChecksPassed',review_flag,'builderAssignsSemanticJudgements'])
        assert provenance['builderAssignsSemanticJudgements'] is False
    else:
        keys(provenance,['generatedPath','generatedSha256','sourceInputRoot','sourceInputs','checks'])
        assert provenance['generatedPath']==doc.relative_to(ROOT).as_posix() and provenance['generatedSha256']==sha(doc)
        assert provenance['sourceInputRoot']==SNAPSHOT.relative_to(ROOT).as_posix(); pins=provenance['sourceInputs']
        keys(provenance['checks'],['everyEvidenceRangeWithinReferencedFile','pointOrExpectedCellContentIncluded','actualApplicationOrDbTestPerformed','actualRenderedImageReviewClaimed'])
        assert all(type(flag) is bool for flag in provenance['checks'].values())
        assert provenance['checks']['pointOrExpectedCellContentIncluded'] is False
        assert provenance['checks']['actualApplicationOrDbTestPerformed'] is False and provenance['checks']['actualRenderedImageReviewClaimed'] is False
    source_refs=[]; generated_refs=[]
    for collection in ['sourceBackedFindings','existingCorrectBehaviors']:
        entries=value[collection]; assert isinstance(entries,list)
        if collection=='sourceBackedFindings':
            id_key='findingId'
            if compact_design: allowed=['findingId','findingKind','severity','title','observed','suggestion','sourceEvidence','generatedEvidence','authorizedDesignEvidence']
            else: allowed=['findingId','severity','title','observed','sourceBehavior','suggestion','sourceEvidence','generatedEvidence'] if compact else ['findingId','kind','observation','suggestedAction','sourceEvidence','generatedEvidence']
        else:
            id_key='behaviorId' if compact else 'preserveId'; allowed=['behaviorId','behavior','sourceEvidence','generatedEvidence'] if compact else ['preserveId','behavior','sourceEvidence','generatedEvidence']
            if compact_design and 'authorizedDesignEvidence' in entries[0]: allowed.append('authorizedDesignEvidence')
        assert len({entry[id_key] for entry in entries})==len(entries)
        for entry in entries:
            keys(entry,allowed)
            for name,item in entry.items():
                if name not in {'sourceEvidence','generatedEvidence','authorizedDesignEvidence'}: text(item)
            assert entry['sourceEvidence'] and entry['generatedEvidence']
            source_refs.extend(entry['sourceEvidence']); generated_refs.extend(entry['generatedEvidence'])
            if compact_design:
                assert all(raw_path(ref['path']).startswith('sources/') for ref in entry['sourceEvidence'])
                assert all(raw_path(ref['path']).startswith('reference-designs/') for ref in entry.get('authorizedDesignEvidence',[]))
                source_refs.extend(entry.get('authorizedDesignEvidence',[]))
    for ref in source_refs:
        keys(ref,['path','startLine','endLine','sha256']); path=SNAPSHOT/raw_path(ref['path'])
        assert sha(path)==ref['sha256'] and type(ref['startLine']) is int and type(ref['endLine']) is int
        assert 1<=ref['startLine']<=ref['endLine']<=len(data(path).decode('utf-8-sig').splitlines())
    normalized=[dict(ref,path=raw_path(ref['path'])) for ref in source_refs]
    workflow.references_valid({'findings':[{'references':normalized}]},manifest)
    for ref in generated_refs:
        keys(ref,['path','startLine','endLine','sha256'])
        assert ref['path']==doc.relative_to(ROOT).as_posix() and ref['sha256']==sha(doc)
        assert type(ref['startLine']) is int and type(ref['endLine']) is int and 1<=ref['startLine']<=ref['endLine']<=len(document_lines)
    assert len({pin['path'] for pin in pins})==len(pins)
    assert {raw_path(ref['path']) for ref in source_refs}<={raw_path(pin['path']) for pin in pins}
    for pin in pins:
        keys(pin,['path','sha256'] if compact else ['path','sha256','bytes']); path=SNAPSHOT/raw_path(pin['path']); assert sha(path)==pin['sha256']
        if not compact: assert len(data(path))==pin['bytes']
    return {'documentId':identity,'sourcePins':len(pins),'sourceRanges':len(source_refs),'generatedRanges':len(generated_refs),'authorizedReferenceRanges':sum(raw_path(ref['path']).startswith('reference-designs/') for ref in source_refs),'rawSourceRanges':sum(raw_path(ref['path']).startswith('sources/') for ref in source_refs),'feedbackVariant':'compact-with-separated-design-evidence' if compact_design else 'compact' if compact else 'extended','allCitedRangesAndHashesValid':True,'sourceRefs':normalized,'generatedRefs':generated_refs}
documents=[]; cases=[]
for stem in STEMS:
    path=FEEDBACK/(stem+'-feedback.json'); value=read(path); entry=verify(value,stem); identity=entry['documentId']
    entry['feedbackPath']=path.relative_to(ROOT).as_posix(); entry['feedbackSha256']=sha(path); documents.append(entry)
    for name,alias,identity_value,rejected in [('new-explicit-alias','GENERATION_SAFE_SOURCE_BACKED_FEEDBACK',identity,False),('old-generator-alias','GENERATOR_SAFE_SOURCE_FEEDBACK',identity,False),('old-writer-alias','WRITER_SAFE_SOURCE_ONLY',identity,False),('unknown-classification','UNCLASSIFIED',identity,True),('wrong-document','GENERATION_SAFE_SOURCE_BACKED_FEEDBACK','MISMATCH',True)]:
        modified=deepcopy(value); modified['classification']=alias; modified['reviewDocumentId']=identity_value; error=None
        try: exec(gate_code,{'safe_feedback':modified,'identity':identity,'visual_review':{'documentId':identity},'text_review':{'documentId':identity}})
        except ValueError as exc: error=str(exc)
        assert bool(error)==rejected; cases.append({'documentId':identity,'scope':'exact-driver-AST-classification-and-identity','case':name,'rejected':rejected,'status':'PASS'})
    for name,edit in [('score-key',lambda v:v.update(score=1)),('grading-row-key',lambda v:v['sourceBackedFindings'][0].update(rowId='INJECTED')),('empty-source-evidence',lambda v:v['sourceBackedFindings'][0].update(sourceEvidence=[])),('unknown-source-path',lambda v:v['sourceBackedFindings'][0]['sourceEvidence'][0].update(path='sources/NOT_PRESENT.cs')),('zero-line',lambda v:v['sourceBackedFindings'][0]['sourceEvidence'][0].update(startLine=0)),('wrong-source-sha',lambda v:v['sourceBackedFindings'][0]['sourceEvidence'][0].update(sha256='0'*64))]:
        modified=deepcopy(value); edit(modified); rejected=False
        try: verify(modified,stem)
        except (AssertionError,ValueError,KeyError): rejected=True
        assert rejected; cases.append({'documentId':identity,'scope':'independent-auditor-contract-validator-not-production-driver','case':name,'rejected':True,'status':'PASS'})
before=list(observed.values()); after=[]
for item in before:
    path=ROOT/item['path']; content=path.read_bytes(); current={'path':item['path'],'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content)}
    assert current==item; after.append(current)
    name='search-audit.json' if STEMS==['student-search'] else 'combined-audit.json'
save(REPORT/name,{'schema':'independent-safe-feedback-contract-audit/1','createdAt':datetime.now(timezone.utc).isoformat(),'round':5,'nextRound':6,'status':'PASS_CONTRACT_AND_PROVENANCE_ONLY','documents':documents,'driverAliasSet':sorted(alias_set),'driverAstGateLines':[classification.lineno,identity_gate.lineno],'cases':cases,'authorizedReferenceCount':11,'inputPinsBefore':before,'inputPinsAfter':after,'inputsUnchanged':True,'evaluatorOnlyOrSpecEvalRead':False,'protectedExpectationsRead':False,'sourceOrMdOrFeedbackOrProductionEdited':False,'externalAiOrRenderJobsStarted':False,'historicalBuilderReaderBehaviorProven':False,'semanticReviewRecordedSeparately':True})
print(json.dumps({'documents':len(documents),'driverCases':5*len(documents),'auditorNegativeCases':6*len(documents),'sourceRanges':sum(d['sourceRanges'] for d in documents),'generatedRanges':sum(d['generatedRanges'] for d in documents),'inputPinsUnchanged':len(before),'contractStatus':'PASS'}))
