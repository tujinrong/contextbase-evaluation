"""Code-only clone of the reviewed renderer wrapper, with metadata-only role pins."""
import ast,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPORT=HERE.parents[1]
REPO=HERE.parents[5]
SOURCE=REPORT/'delivery/render_assisted_screen_r18.py'
TARGET=HERE/'render_r04.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not TARGET.exists()
text=SOURCE.read_text(encoding='utf-8');tree=ast.parse(text)
cases={
 'table-index':{'root':'revision-table-index-r04','path':'基本設計書/03_テーブル仕様書.md',
  'sha':'d328d6a6f42f201b8d4026aa091b123a84ecd36fe8ae70729fd20b8dd6872eb7',
  'id':'CSHARP_ASPNET-BAS-STU-03','job':'revision-table-index-r04','destination':'assisted-table-index-r04-delivery-r18',
  'reviewedPin':'reviewed-table-index-r04-r11-pin.json','reviewedPinSha256':'a35d6145a5f056fdca062f2e5b18a47a8405b0041c9ef029300a8455c0ba71c4'},
 'operation-log':{'root':'revision-operation-log-r04','path':'基本設計書/テーブル/05_t_operation_log.md',
  'sha':'7067c165e324756fb909048d2f3c6735ed3824bb6512c66155015ba6c5703b48',
  'id':'CSHARP_ASPNET-BAS-STU-03-T_OPERATION_LOG','job':'revision-operation-log-r04','destination':'assisted-operation-log-r04-delivery-r18',
  'reviewedPin':'reviewed-operation-log-r04-r11-pin.json','reviewedPinSha256':'34af4227c5b28000427376f7f6c454783c712d010222d581333bdce43888d73a'}}
lines=text.splitlines(keepends=True)
assignment=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CASES' for t in n.targets))
lines[assignment.lineno-1:assignment.end_lineno]=['CASES='+repr(cases)+'\n']
text=''.join(lines)
old='AGENT=HERE.parents[2];REPO=HERE.parents[4];REPORT=HERE.parent'
assert text.count(old)==1
text=text.replace(old,'AGENT=HERE.parents[3];REPO=HERE.parents[5];REPORT=HERE.parents[1]')
needle=" assert before[str(source)]==case['sha']\n"
assert text.count(needle)==1
addition=""" rootpin=safe(REPORT/'training-assisted'/case['reviewedPin'])
 assert sha(rootpin)==case['reviewedPinSha256']
 approved_pin=json.loads(rootpin.read_text(encoding='utf8'))
 assert approved_pin['sha256']==case['sha'] and approved_pin['documentId']==case['id'] and approved_pin['path']==case['path']
 assert safe(approved_pin['canonicalMarkdown'])==source and safe(approved_pin['draftResult'])==draft
 assert approved_pin['independentReviewApproved'] is True and approved_pin['structureStatus']=='STRUCTURE_VALID'
 assert approved_pin['noFurtherTextRevisionPlanned'] is True and approved_pin['capsule']['manifestSha256']==CAP_SHA
 verified=safe(approved_pin['independentReview']);handoff=safe(verified.with_name('review-handoff.json'))
 assert sha(verified)==approved_pin['independentReviewSha256'] and sha(draft)==approved_pin['draftResultSha256']
 handoff_meta=json.loads(handoff.read_text(encoding='utf8'))
 assert handoff_meta['approved'] is True and handoff_meta['documentSha256']==case['sha']
 assert handoff_meta['referenceMode']=='training-assisted' and handoff_meta['snapshot']['manifestSha256']==CAP_SHA
 assert handoff_meta['reviewSha256']==sha(verified) and safe(handoff_meta['documentFile'])==source
 for pin in (rootpin,verified,handoff):before[str(pin)]=sha(pin)
"""
text=text.replace(needle,needle+addition)
ast.parse(text)
TARGET.write_text(text,encoding='utf-8')
receipt={'schema':'trusted-render-wrapper-clone/1','source':str(SOURCE),'sourceSha256':sha(SOURCE),'target':str(TARGET),'targetSha256':sha(TARGET),
 'cases':cases,'runtimeReceiptSha256':'54e693b2382e1520710d192e8a8b0b6b6eb97bbae1e70c1dbc36ff1e36f279be',
 'changes':['path constants for fresh owned QA directory','two fixed metadata-only r04 cases','approved pin and review handoff binding before read-only derivation'],
 'canonicalOrBusinessContentModified':False,'originalDesignRubricExpectedAnswerReads':0}
(HERE/'clone.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'path':str(TARGET),'sha256':sha(TARGET),'cases':list(cases)},ensure_ascii=False))
