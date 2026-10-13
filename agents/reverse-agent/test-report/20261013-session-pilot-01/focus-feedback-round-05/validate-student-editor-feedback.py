"""Generic read-only identity, digest, range and path-boundary checks."""
from pathlib import Path
import hashlib
import json
import re

root=Path(__file__).resolve().parents[5]
safe=Path(__file__).resolve().parent
candidate=(safe/'student-editor-feedback-v2.json').resolve()
assert candidate.is_relative_to(safe)
raw=candidate.read_bytes()
payload=json.loads(raw.decode('utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for forbidden in ('evaluationId','originalPoints','awardedPoints','expectedCells','spec-eval','evaluator-only'):
 assert forbidden not in raw.decode('utf-8')
roots={k:(root/v).resolve() for k,v in payload['evidenceRoots'].items()}
for value in roots.values():assert value.is_relative_to(root)
files={}
ranges=0

def inspect(value):
 global ranges
 if isinstance(value,dict):
  if all(key in value for key in ('root','path','startLine','endLine','sha256')):
   base=roots[value['root']]
   path=(base/value['path']).resolve()
   assert path.is_relative_to(base) and path!=base
   assert re.fullmatch('[0-9a-f]{64}',value['sha256'])
   assert sha(path)==value['sha256']
   count=len(path.read_text(encoding='utf-8-sig').splitlines())
   assert 1<=value['startLine']<=value['endLine']<=count
   files[path.as_posix()]=value['sha256']
   ranges+=1
  for child in value.values():inspect(child)
 elif isinstance(value,list):
  for child in value:inspect(child)

inspect(payload)
assert len(payload['sourceBackedFindings'])==3
assert len(payload['existingCorrectBehaviors'])==8
assert sha(root/payload['provenance']['generatedPath'])==payload['provenance']['generatedSha256']
print(json.dumps({'payloadSha256':sha(candidate),'validatorSha256':sha(Path(__file__)),'checkedEvidenceRanges':ranges,'checkedInputFiles':len(files),'evidencePathsRemainWithinDeclaredRoots':True,'semanticStatementsDerivedByValidator':False,'classification':payload['classification'],'classificationNormalizationOwnedByParent':True},ensure_ascii=False))
