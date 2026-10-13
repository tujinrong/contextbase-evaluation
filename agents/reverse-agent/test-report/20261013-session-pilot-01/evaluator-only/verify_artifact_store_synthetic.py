"""Bounded synthetic artifact-integrity checks; no business criteria or scores."""
from pathlib import Path
import datetime,hashlib,json
from artifact_store import EVALUATOR_ROOT,exclusive_bytes,exclusive_json,corrected_json

OUT=EVALUATOR_ROOT/'artifact-store-synthetic-01'
assert not OUT.exists(),'Use a new synthetic run directory; do not overwrite evidence.'
OUT.mkdir()
old=OUT/'fixture-original.json'
raw='{"fixture":"synthetic 原文", "padding":"keep"}\r\n'.encode('utf-8')
original=exclusive_bytes(old,raw)
checks=[]
try:exclusive_bytes(old,b'overwritten')
except FileExistsError:checks.append('existing-write-refused-and-exact-old-bytes-unchanged')
else:raise AssertionError('Existing write was not refused.')
assert old.read_bytes()==raw
new=OUT/'fixture-version-02.json';transition=OUT/'fixture-transition-02.json'
saved=corrected_json(old,new,transition,{'fixture':'synthetic new'},
 reason='Synthetic persistence check only.',change_summary=['A synthetic value changed; no semantic decision.'])
assert Path(saved['previousSnapshot']['path']).read_bytes()==raw
assert old.read_bytes()==raw and new.read_bytes()!=raw
record=json.loads(transition.read_text(encoding='utf-8'))
assert record['exactPreviousBytesPreserved'] and not record['previousArtifactOverwritten']
checks.append('explicit-correction-keeps-old-snapshot-new-version-and-transition')
new_raw=new.read_bytes();transition_raw=transition.read_bytes()
try:corrected_json(old,new,OUT/'unused-transition.json',{'fixture':'third'},reason='Synthetic',change_summary=['Synthetic'])
except FileExistsError:checks.append('occupied-new-version-refused-before-creating-transition')
else:raise AssertionError('Occupied new version was not refused.')
assert not (OUT/'unused-transition.json').exists()
assert new.read_bytes()==new_raw and transition.read_bytes()==transition_raw and old.read_bytes()==raw
try:corrected_json(old,old,OUT/'alias-transition.json',{},reason='Synthetic',change_summary=['Synthetic'])
except ValueError:checks.append('alias-correction-refused')
else:raise AssertionError('Aliased correction was not refused.')
outside=EVALUATOR_ROOT.parent/'synthetic-outside-evaluator.json'
assert not outside.exists()
try:exclusive_json(outside,{'fixture':'outside'})
except ValueError:checks.append('outside-evaluator-path-refused-before-write')
else:raise AssertionError('Outside evaluator path was not refused.')
assert not outside.exists()
result={'schema':'evaluator-artifact-store-synthetic-validation/1','classification':'EVALUATOR_ONLY',
 'generatorMayRead':False,'validatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'status':'PASS','checks':checks,'checksPassed':len(checks),'businessRulesOrExpectedAnswersEmbedded':False,
 'semanticScoreAssigned':False,'inputProgramOrDbExecuted':False,
 'helperSha256':hashlib.sha256((EVALUATOR_ROOT/'artifact_store.py').read_bytes()).hexdigest(),
 'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'initialLostEditorBytesRecovered':False,'previousArtifact':original,'transitionArtifacts':saved,
 'limitation':'Exclusive-create and explicit history preservation are checked; filesystem group transactionality is not claimed.'}
proof=exclusive_json(OUT/'validation.json',result)
print(json.dumps({'status':'PASS','checks':len(checks),'validationSha256':proof['sha256'],'helperSha256':result['helperSha256']}))
