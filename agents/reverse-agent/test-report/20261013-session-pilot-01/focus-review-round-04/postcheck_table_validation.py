"""Check only the future generic validator against immutable actual Round4 Markdown."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from contextbase.ai.validation import validate_document

root=Path.cwd().resolve(); report=Path(__file__).resolve().parent/'postcheck-validation-01'
report.mkdir(exist_ok=True)
output=root/'test-project1/spec-analysis/CSharp_ASPNET/20261013-focus-round-04/spec/detail'
paths=[root/'agents/reverse-agent/src/contextbase/ai/validation.py',root/'agents/reverse-agent/src/contextbase/ai/prompts.py']
for stem in ('student-search','student-editor'):
    paths.extend([output/(stem+'.md'),root/'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-04/render'/stem/'manifest.json',Path(__file__).resolve().parent/(stem+'-review.json')])
def pin(p): return {'path':p.relative_to(root).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
before=[pin(p) for p in paths]
results=[]
for stem,document_id in [('student-search','SM-DET-STUDENT-SEARCH'),('student-editor','SM-DET-STUDENT-EDITOR')]:
    findings=validate_document((output/(stem+'.md')).read_text(encoding='utf-8'),'spec/detail/'+stem+'.md',expected_document_id=document_id)
    results.append({'documentId':document_id,'findings':findings})
assert results[0]['findings']==[],results[0]
editor=results[1]['findings']
assert len(editor)==1 and editor[0]['code']=='TABLE_CELL_OVERFLOW',editor
assert editor[0]['location']=='spec/detail/student-editor.md:1064',editor
after=[pin(p) for p in paths]; assert before==after
result={'schema':'independent-future-validator-postcheck/1','createdAt':datetime.now(timezone.utc).isoformat(),'status':'PASS','inputsUnchanged':True,'results':results,'pins':before,'oldRound4RenderResultsRewritten':False,'rawMdRewritten':False,'runningRound4RuntimePatched':False,'extraAiOrRenderJobsStarted':False,'originalSourceOrEvaluatorExpectationsRead':False,'scope':'Future generic structure validator only; no new source meaning or visual acceptance claim; original full native review remains unchanged.'}
(report/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','editorDetected':'TABLE_CELL_OVERFLOW','line':1064,'searchFindings':0,'inputsUnchanged':True}))
