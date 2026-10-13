"""Exact old/new metadata and prompt comparison, with read-only integrity checks."""
import ast,difflib,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path.cwd().resolve(); REPORT=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def save(name,value):
    with (REPORT/name).open('x',encoding='utf-8') as file:json.dump(value,file,ensure_ascii=False,indent=2);file.write('\n')
old=ROOT/'agents/reverse-agent/test-report/20261013-session-pilot-01/focus-feedback-round-05/student-editor-feedback-v2.json'
folder=ROOT/'agents/reverse-agent/test-report/20261013-session-pilot-01/focus-writer-input-round-05-v2'
new=folder/'student-editor-feedback.json'; search=folder/'student-search-feedback.json'
previous_prompt=ROOT/'agents/reverse-agent/.tmp/20261013-session-pilot-01/prompts-before-focus06.py'
current_prompt=ROOT/'agents/reverse-agent/src/contextbase/ai/prompts.py'
paths=[old,new,search,folder/'format-transition.json',previous_prompt,current_prompt,ROOT/'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus_cycle.py']
before=[{'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path)} for path in paths]
assert sha(old)=='5d9ec5e0bc1e3a386c9be8a2df5094c34350644f00696c9fdf770f060713252d'
assert sha(new)=='208fd1cd14686652469869507d5bdf74bbed9ca5e34ed15ddf0fbe6ba3b29d07'
assert sha(search)=='337e80a2ecadb3c9081311f8f3b931849ea253a090fcbe8ebccff826ed701778'
old_value=read(old); new_value=read(new)
assert old_value.pop('classification')=='WRITER_SAFE_SOURCE_AND_AUTHORIZED_DESIGN_DOCUMENTATION'
assert new_value.pop('classification')=='GENERATION_SAFE_SOURCE_BACKED_FEEDBACK'
assert old_value==new_value
assert sha(previous_prompt)=='cd98649bde4e5a66bc36308dd5d263d0f33cc8c3d2eabffd665ed3ca8cedfe97'
assert sha(current_prompt)=='8135a2157fc127565baf5ec9d62c7c6616b0a12112385c61f5f30e09b467228e'
old_prompt=previous_prompt.read_text(encoding='utf-8').splitlines(); new_prompt=current_prompt.read_text(encoding='utf-8').splitlines()
opcodes=difflib.SequenceMatcher(None,old_prompt,new_prompt).get_opcodes()
changes=[{'kind':kind,'oldStart':a+1,'oldEnd':b,'newStart':c+1,'newEnd':d,'oldLines':old_prompt[a:b],'newLines':new_prompt[c:d]} for kind,a,b,c,d in opcodes if kind!='equal']
assert len(changes)==3 and all(item['kind']=='insert' and len(item['newLines'])==1 for item in changes)
ast.parse(current_prompt.read_text(encoding='utf-8'))
original_native=REPORT.parent/'focus-review-round-05/review-manifest.json'
native=read(original_native); unchanged=0
for item in native['inputPins']:
    for key in ['sourcePath','frozenPath']:
        path=ROOT/item[key]; assert sha(path)==item['sha256']; unchanged+=1
for document in native['documents']:assert sha(Path(document['reviewPath']))==document['reviewSha256']
after=[{'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path)} for path in paths]; assert before==after
save('transition-and-prompt-audit.json',{'schema':'independent-safe-input-transition-and-generic-prompt-audit/1','checkedAt':datetime.now(timezone.utc).isoformat(),'status':'PASS_METADATA_ONLY_TRANSITION_AND_GENERIC_PROMPT_SCOPE','oldV2FeedbackSha256':sha(old),'newV2FeedbackSha256':sha(new),'searchBytesShaUnchanged':sha(search),'onlyFeedbackFieldChanged':'classification','everyOtherJsonFieldDeepEqual':True,'bodyAndSourceConditionsUnchanged':True,'oldV1FeedbackIsSeparateHistory':True,'olderNormalizationRootIsUnusedHistory':'focus-writer-input-round-05','promptOldSha256':sha(previous_prompt),'promptNewSha256':sha(current_prompt),'promptChanges':changes,'promptMeaningAudit':'All three clauses ask AI to extract authorized design definitions, I/O direction/shared values and implementation/verification responsibilities with source evidence. They preserve observed/reference separation, prohibit invented verification and retain AI prose authorship. No application-specific names, business conditions, numeric answers or grading criteria are supplied by these added clauses.','generation5FrozenRuntimeUnchanged':sha(ROOT/'agents/reverse-agent/.tmp/20261013-session-pilot-01/focus-round-05/runtime-code/contextbase/ai/prompts.py')==sha(previous_prompt),'round5OriginalAndFrozenArtifactHashComparisonsUnchanged':unchanged,'round5NativeReviewJsonUnchanged':2,'inputPinsBefore':before,'inputPinsAfter':after,'protectedExpectationContentsRead':False,'sourceOrMdEdited':False,'AiOrRenderingStarted':False,'overallOrFormalPassClaimed':False})
print(json.dumps({'metadataOnlyFieldChange':True,'otherJsonDeepEqual':True,'genericPromptInsertions':3,'nativeOriginalFrozenHashComparisons':unchanged,'nativeReviewJsonUnchanged':2,'transitionInputPinsUnchanged':len(before)}))
