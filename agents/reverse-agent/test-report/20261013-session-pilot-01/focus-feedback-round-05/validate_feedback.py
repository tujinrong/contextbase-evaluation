"""Generic safe JSON hash/range/authorized-input validation; no prose derivation."""
from pathlib import Path
import argparse, datetime, hashlib, json, re

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def walk(value):
    if isinstance(value,dict):
        yield value
        for item in value.values():yield from walk(item)
    elif isinstance(value,list):
        for item in value:yield from walk(item)

parser=argparse.ArgumentParser()
parser.add_argument('--workspace',required=True,type=Path)
parser.add_argument('--capsule',required=True,type=Path)
parser.add_argument('--feedback',required=True,nargs='+',type=Path)
parser.add_argument('--output',required=True,type=Path)
args=parser.parse_args()
SAFE=Path(__file__).resolve().parent
ROOT=args.workspace.resolve()
assert SAFE.is_relative_to(ROOT)
CAP=args.capsule.resolve()
manifest=read(CAP/'manifest.json')
assert manifest['mode']=='training-assisted'
assert manifest['trainingReferenceAuthorizedByUser'] and manifest['referenceSpecificationIncluded']
allowed={'sources/'+e['path']:e for e in manifest['files']}
allowed.update({e['path']:e for e in manifest['referenceFiles']})
checks=[]
for input_path in args.feedback:
    path=input_path.resolve()
    assert path.is_relative_to(SAFE) and path!=SAFE
    body=read(path)
    assert body['classification']=='GENERATION_SAFE_SOURCE_BACKED_FEEDBACK'
    project_root=(ROOT/body['projectId']).resolve()
    assert project_root.is_relative_to(ROOT)
    assert Path(manifest['sourceRoot']).resolve().is_relative_to(project_root/'srcs')
    provenance=body['provenance']
    candidate=(ROOT/provenance['generatedPath']).resolve()
    assert candidate.is_relative_to(project_root/'spec-analysis')
    assert sha(candidate)==provenance['generatedSha256']
    first=candidate.read_text(encoding='utf-8-sig').splitlines()[0]
    metadata=json.loads(re.fullmatch(r'<!-- spec-meta: (.+) -->',first).group(1))
    assert metadata['documentId']==body['reviewDocumentId']
    assert str(metadata['version'])==str(body['reviewDocumentVersion'])
    referenced={};count=0
    forbidden={'evaluationId','originalExpectation','originalExpectationSha256','expectedCells',
      'expectedAnswer','expectedAnswers','originalPoints','awardedPoints','confirmedPoints',
      'maximumPoints','completeScore','completePercent','judgement','criticalFinding','selectedRows'}
    for obj in walk(body):
        assert not forbidden.intersection(obj),('Protected payload key',forbidden.intersection(obj))
        if {'path','startLine','endLine','sha256'}<=obj.keys():
            relative=obj['path']
            if relative==provenance['generatedPath']:
                source=candidate;expected=provenance['generatedSha256']
            else:
                assert relative in allowed,('Unauthorized input reference',relative)
                source=(CAP/relative).resolve()
                assert source.is_relative_to(CAP)
                expected=allowed[relative]['sha256']
                referenced[relative]=expected
            assert sha(source)==obj['sha256']==expected
            line_count=len(source.read_text(encoding='utf-8-sig').splitlines())
            assert 1<=obj['startLine']<=obj['endLine']<=line_count
            count+=1
    assert count>0
    for pin in provenance.get('sourceInputs',[]):
        assert pin['path'] in allowed and sha(CAP/pin['path'])==pin['sha256']==allowed[pin['path']]['sha256']
        if 'bytes' in pin:assert (CAP/pin['path']).stat().st_size==pin['bytes']
    for relative,expected in referenced.items():assert sha(CAP/relative)==expected
    checks.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),
      'generatedSha256':sha(candidate),'documentId':metadata['documentId'],'documentVersion':metadata['version'],
      'sourceOrAuthorizedReferencePinsVerified':len(referenced),'numberedEvidenceRangesVerified':count,
      'protectedPayloadKeysAbsent':True,'sourceInputDrift':[]})
target=args.output.resolve()
assert target.is_relative_to(SAFE) and target!=SAFE
payload={'schema':'safe-feedback-input-validation/1','classification':'GENERATION_SAFE_VALIDATION',
 'validatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'status':'HASH_RANGE_IDENTITY_AND_AUTHORIZED_INPUTS_VERIFIED',
 'capsuleManifestSha256':sha(CAP/'manifest.json'),'mode':manifest['mode'],
 'authorizedSourceFiles':len(manifest['files']),'authorizedReferenceFiles':len(manifest['referenceFiles']),
 'feedbackFiles':checks,'semanticAcceptanceInferred':False,'expectedCellLeakageInferredFromMechanicalCheck':False,
 'limitation':'This checker verifies paths, hashes, numbered ranges, identities and protected key absence. An independent source reviewer must assess prose and evidence meaning.',
 'feedbackProseDerivedByPython':False,'outputWriteMode':'exclusive-create'}
with target.open('xb') as stream:stream.write((json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps({'path':target.relative_to(ROOT).as_posix(),'sha256':sha(target),'feedbackFiles':len(checks),
 'numberedEvidenceRangesVerified':sum(c['numberedEvidenceRangesVerified'] for c in checks)},ensure_ascii=False))
