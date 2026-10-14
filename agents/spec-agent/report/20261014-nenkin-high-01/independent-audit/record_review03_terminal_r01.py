"""Saved metadata and tool-output observations only. No command replay or AI answer mutation."""
from pathlib import Path
from datetime import datetime,timezone
import collections,hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
R=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
P=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
A=P/'independent-audit'
helper=R/'review_plan_with_scope_r03.py'
assert hashlib.sha256(helper.read_bytes()).hexdigest()=='cec73d552fa2ae35f14f9b6151f4552ca0c8d7a3c451bcba92fef8f43b0944c2'
spec=importlib.util.spec_from_file_location('terminal_scoped_guard_r03',helper);g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
job=R/'jobs/independent-plan-review-03'
prep=P/'independent-plan-review/independent-plan-review-03/preparation.json'
assert g.sha(prep)=='d214eb0f2cada55b65e3ed7906792c11e770b3f87b24c60ce7a843077e162369'
bp=R/'jobs/independent-plan-review-03-plan-review-before.json';ap=R/'jobs/independent-plan-review-03-plan-review-after.json'
before,after=g.load(bp),g.load(ap)
assert after['status']=='REVIEW_NOT_VERIFIED' and before['input']==after['input'] and before['preparationSha256']==after['preparationSha256']==g.sha(prep)
runtime=g.bootstrap();assert runtime==before['runtime']
pin,_,plan,manifest,_=g.current_pin(R/'jobs/plan-03/plan-verified.json','f302f6d345e87add5a9ac4ef6b0d19f9708dfcb9bdd3c92e3d411795e9d8146d','b446a321d7e584202a6aa2f86e1748db0b65f93098716e91b3442951dfcef590')
assert pin==before['input']
sb=g.load(R/'jobs/independent-plan-review-03-snapshot-before.json');sa=g.load(R/'jobs/independent-plan-review-03-snapshot-after.json')
assert sa=={'status':'UNCHANGED','before':sb,'after':sb} and sb==pin['snapshot']
answer=g.load(job/'answer.txt');raw_sha=g.sha(job/'answer.txt')
assert not (job/'plan-review-verified.json').exists() and not (job/'plan-review-handoff.json').exists()
commands=[];eventtypes=collections.Counter()
for line in g.safe(job/'events.jsonl').read_text(encoding='utf-8-sig').splitlines():
 event=json.loads(line);eventtypes[event.get('type','unknown')]+=1;item=event.get('item',{})
 if event.get('type')=='item.completed' and item.get('type')=='command_execution':commands.append(item)
entries={e['path']:e for e in manifest['files']};alias={p:p for p in entries}
for p,e in entries.items():alias['sources/'+p]=p;alias[e['indexed']]=p
canonical_declared={alias[p] for p in answer['sourcePathsRead'] if p in alias}
observations=[];returned=set();mentioned=set();families=collections.Counter()
for c in commands:
 cmd=c['command'];out=c.get('aggregated_output','');body=cmd.split('-Command ',1)[-1].strip().lstrip('"\'');family=body.split(None,1)[0] if body else 'unknown';families[family]+=1
 listing=family=='rg' and '--files' in body
 cmdmentions={p for a,p in alias.items() if a in cmd and ('sources/'+p in cmd or entries[p]['indexed'] in cmd)}
 content=set()
 if not listing:
  for p,e in entries.items():
   if any(re.search(r'(?m)^'+re.escape(a)+r':\d+:',out) for a in ['sources/'+p,e['indexed']]):content.add(p)
 if not listing and family=='rg' and '-n' in body and len(cmdmentions)==1 and c.get('exit_code')==0 and re.search(r'(?m)^\d+:',out):content.update(cmdmentions)
 returned.update(content);mentioned.update(cmdmentions)
 observations.append({'eventItemId':c.get('id'),'exitCode':c.get('exit_code'),'status':c.get('status'),'commandFamily':family,'inventoryOnly':listing,'commandSha256':hashlib.sha256(cmd.encode()).hexdigest(),'outputSha256':hashlib.sha256(out.encode()).hexdigest(),'literalSourcePathMentions':sorted(cmdmentions),'returnedContentPathObservations':sorted(content)})
failed=[{'group':group,'id':v.get('id',v.get('documentId')),'basis':v['basis'],'referenceCount':len(v['references'])} for group in ['subjects','documentCoverage','reachability','findings','blockingUnresolved','scopeLimits'] for v in answer[group] if v['basis']!='plan-structure' and not v['references']]
assert failed==[{'group':'reachability','id':'REACH-JSON-DISPATCH','basis':'observed-source','referenceCount':0},{'group':'reachability','id':'REACH-PDF-GET','basis':'observed-source','referenceCount':0}]
files=[*g.safe(job).iterdir(),bp,ap,prep,helper,R/'jobs/independent-plan-review-03-snapshot-before.json',R/'jobs/independent-plan-review-03-snapshot-after.json']
artifacts={str(g.safe(p)):g.sha(p) for p in files if p.is_file()}
obs={'schema':'spec-agent-plan-review-tool-observations/1','createdUtc':datetime.now(timezone.utc).isoformat(),'job':str(job),'eventsSha256':g.sha(job/'events.jsonl'),'rawAnswerSha256':raw_sha,'declaredReadPathCount':len(answer['sourcePathsRead']),'declaredUniqueCanonicalSourceCount':len(canonical_declared),'manifestTextSourceCount':179,'completedCommandCount':len(commands),'exitCounts':dict(collections.Counter(str(c.get('exit_code')) for c in commands)),'commandFamilyCounts':dict(families),'eventTypes':dict(eventtypes),'literalSourcePathMentionCount':len(mentioned),'returnedContentPathObservationCount':len(returned),'returnedContentPaths':sorted(returned),'declaredCanonicalWithoutReturnedPathObservation':sorted(canonical_declared-returned),'commands':observations,'commandsReplayed':False,'allDeclaredSourcesFullyReadProven':False,'semanticComprehensionProven':False,'limitations':['Literal command/path mentions are not proof file contents were read.','Returned path-qualified rg lines or single-file rg line output indicate partial returned source content only; this parser does not prove complete file coverage or source semantics.','Directory-scoped searches and long/truncated outputs may return source content without a matched path; absence is not proof no read occurred.','The three exit1 commands require separate interpretation; this report does not equate all exit1 to a source-read failure.','No captured command or original source program was replayed.']}
obsfile=A/'plan-review-03-tool-observations-r01.json'
with g.safe(obsfile).open('x',encoding='utf8',newline='\n') as f:json.dump(obs,f,ensure_ascii=False,indent=2);f.write('\n')
terminal={'schema':'spec-agent-independent-plan-review-terminal/1','createdUtc':datetime.now(timezone.utc).isoformat(),'ownedUnifiedSessionId':72384,'observedTerminalExitCode':1,'status':'AI_RAW_FALSE_REVIEW_PROTOCOL_REJECTED','rawAnswerSha256':raw_sha,'job':str(job),'input':pin,'preparationSha256':g.sha(prep),'rawApproved':answer['approved'],'rawFindingCount':len(answer['findings']),'rawFindingSeverities':dict(collections.Counter(v['severity'] for v in answer['findings'])),'rawBlockingUnresolvedCount':len(answer['blockingUnresolved']),'rawScopeLimitsCount':len(answer['scopeLimits']),'rawSubjectCount':len(answer['subjects']),'rawDocumentCoverageCount':len(answer['documentCoverage']),'rawReachabilityCount':len(answer['reachability']),'rawDeclaredReadCount':len(answer['sourcePathsRead']),'failingEvidenceObjects':failed,'errorType':after['errorType'],'error':after['error'],'providerSnapshotBeforeAfterUnchanged':True,'scopeInputCurrentEqualsBefore':True,'runtime128Files13Imports7CriticalCurrentEqualsBefore':True,'verifiedReviewAbsent':True,'handoffAbsent':True,'artifacts':artifacts,'toolObservations':str(obsfile),'toolObservationsSha256':g.sha(obsfile),'aiResponseBytesModified':False,'adoptionOrApprovalTransferred':False,'targetApplicationOrDatabaseExecutedByAuditor':False,'schemaFailureIsOnlyIssue':False,'sourceScopeClaimCorrectedInFreshR05':True,'findingStatus':'Unverified raw major F-001 partly relies on inaccurate inherited claim that downstream lacks full execution-scope metadata; requires fresh code-grounded reassessment, not blind adoption.','correctionRecord':str(A/'scoped-plan-wrapper-review-r05.json'),'correctionRecordSha256':g.sha(A/'scoped-plan-wrapper-review-r05.json'),'limitations':['Raw approved=false and major1 are original AI judgments; protocol validation failed so they are not a verified review/handoff.','Initial terminal message incorrectly localized evidence failure to documentCoverage; the two failing records are reachability groups.','Coordinate/reference validation and declared-read lists do not establish semantic completeness.','Omitted n2framework IDE declarations and compiled artifacts remain unassessed; all345 semantic analysis is not claimed.']}
assert all(g.sha(p)==h for p,h in artifacts.items()) and g.bootstrap()==runtime
g.recheck(pin,runtime)
t=A/'plan-review-03-terminal-r01.json'
with g.safe(t).open('x',encoding='utf8',newline='\n') as f:json.dump(terminal,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'terminal':str(t),'terminalSha256':g.sha(t),'toolObservationsSha256':g.sha(obsfile),'rawAnswerSha256':raw_sha,'declaredPaths':len(answer['sourcePathsRead']),'declaredCanonicalSources':len(canonical_declared),'returnedContentObservedPaths':len(returned),'completedCommands':len(commands),'families':dict(families)}))
