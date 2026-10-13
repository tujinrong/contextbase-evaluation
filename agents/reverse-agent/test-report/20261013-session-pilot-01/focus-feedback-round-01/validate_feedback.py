"""Verify safe feedback without reading any reference/checklist/score output."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
OUT=Path(__file__).resolve().parent
ROOT=OUT
while not (ROOT/'test-project1/srcs/CSharp_ASPNET').is_dir():
    assert ROOT.parent!=ROOT
    ROOT=ROOT.parent
SRC=ROOT/'agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted/sources'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
forbidden=('evaluationId','awardedPoints','expectedSpecification','spec-eval/','evaluator-only/','originalCells','confirmedAwardedPoints')
validated=[]
for name,identity in [('student-search-feedback.json','SM-DET-STUDENT-SEARCH'),('student-editor-feedback.json','SM-DET-STUDENT-EDITOR')]:
    path=OUT/name
    text=path.read_text(encoding='utf-8')
    assert all(k not in text for k in forbidden)
    report=json.loads(text)
    assert report['classification']=='WRITER_SAFE_SOURCE_ONLY'
    assert report['reviewDocumentId']==identity
    assert report['provenance']['sourceExecutionPerformed'] is False
    assert report['provenance']['criteriaOrOriginalExpectedCellsUsedAsFeedback'] is False
    n=0
    for entry in report['sourceBackedFindings']+report['existingCorrectBehaviors']:
        assert entry['generatedEvidence'] and entry['sourceEvidence']
        for kind in ['generatedEvidence','sourceEvidence']:
            for ref in entry[kind]:
                if kind=='sourceEvidence':
                    assert ref['path'].startswith('sources/')
                    p=SRC/ref['path'][8:]
                else:
                    assert ref['path'].startswith('test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-01/')
                    p=ROOT/ref['path']
                assert sha(p)==ref['sha256']
                assert 1<=ref['startLine']<=ref['endLine']<=len(p.read_text(encoding='utf-8-sig').splitlines())
                n+=1
    validated.append(dict(path=name,sha256=sha(path),reviewDocumentId=identity,
      generatedSha256=report['provenance']['generatedSha256'],sourceBackedFindings=len(report['sourceBackedFindings']),
      existingCorrectBehaviors=len(report['existingCorrectBehaviors']),evidenceReferencesValidated=n))
result=dict(schema='writer-safe-feedback-validation/1',classification='WRITER_SAFE_SOURCE_ONLY',
 validatedAt=datetime.now(timezone.utc).isoformat(),status='SOURCE_GENERATED_PROVENANCE_AND_NO_PROTECTED_KEYS_VERIFIED',
 criteriaOrOriginalExpectedCellsReadByValidator=False,files=validated)
(OUT/'feedback-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'feedback-manifest.json').write_text(json.dumps(dict(schema='writer-feedback-handoff/1',classification='WRITER_SAFE_SOURCE_ONLY',
 iteration='20261013-focus-round-01',files=validated),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
