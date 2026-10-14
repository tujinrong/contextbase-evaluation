"""Combine only own code-only synthetic audit receipts, without production material access."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone

root=Path(__file__).resolve().parent
hash_file=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks={
 'collector-v4-independent-r01/review.json':'dfb2b45f19b43fd57f35ec51b30cb8cbf22fdac64052ec2cf32c10c27707476d',
 'collector-v4-independent-r02/review.json':'dca4e3db3545e0c173b7296324f6d04729a2fb67a6e16fd5e0f65e350adcda52',
 'collector-v4-independent-r03/review.json':'51e6578eef5a6e8d1b6b97908b83a41677d540ee409a892f9c125f5a6d67068c'}
reports={}
for relative,expected in checks.items():
 path=root/relative
 if hash_file(path)!=expected:raise ValueError('Prior own report bytes changed')
 reports[relative]=json.loads(path.read_text(encoding='utf-8'))
helper=Path(r'D:\開発\contextbase-evaluation\agents\reverse-agent\.tmp\20261013-rerun-12h\training-assisted\collect_reviewed_v4.py')
if hash_file(helper)!='1df7864264b5b4e5bf65f295eda5655c468b392fd8020c3e307121fbfd139666':
 raise ValueError('Approved code-only helper changed')
runtime_file=root/'collector-v4-independent-r02/audit-runtime-after.json'
runtime=json.loads(runtime_file.read_text(encoding='utf-8'))
if runtime['receiptSha256']!='a38c4efa878dc4c6a47967a39b99494ddc3818d63db953e00058e7eab80b1083' or not runtime['byteIdenticalToReceipt']:
 raise ValueError('Own technical audit runtime mismatch')
payload={
 'schema':'collector-independent-technical-audit-summary/1','createdAt':datetime.now(timezone.utc).isoformat(),
 'helper':str(helper),'helperSha256':hash_file(helper),'oldHelperUnchanged':True,
 'status':'CHANGES_REQUIRED_FOR_ANALYSIS_CHECKPOINT_GUARD',
 'auditMethod':'Approved helper code FunctionDefs extracted into owned synthetic namespace; valid GRID manuscript fixtures; capsule/reference/module resolution mocked; actual frozen safe_path and validate_document used',
 'reports':[{'file':str(root/name),'sha256':digest,'cases':reports[name]['total']} for name,digest in checks.items()],
 'caseCount':61,
 'checkpointGuardFindings':reports['collector-v4-independent-r02/review.json']['findings'],
 'capsuleStateHardening':{
  'isolatedVerifyCapsuleDoesNotTieStateToFixedManifestAndMode':True,
  'fixedPlanHandoffIndependentlyRejectsMismatchBeforeCopy':True,
  'productionFixedPlanHandoffBypassEstablished':False,
  'r01StateCounterexampleAssumption':'Toy fixed plan-handoff itself created with matching erroneous state and its toy SHA fixed; r03 preserves fixed handoff and rejects drift'},
 'verifiedTechnicalGuards':[
  'fresh output and report; exact eleven document IDs; fixed manifest/contract/plan/handoff hashes',
  'review/draft/canonical byte SHA bindings; approved/major/unresolved rejection; input root restrictions',
  'registered 124-file author runtimes; full membership and byte drift; exact thirteen resolved and six loaded module files/spec origins',
  'copy byte identity and pinned inputs before/after; provider/evidence path traversal and hashes',
  'actual owned Windows junctions refused before selection read and runtime descent; zero linked-target reads'],
 'recommendedFreshVersionScope':'Explicit complete checkpoint contract plus existing frozen workflow.select_document/_resume_analysis read-only revalidation; isolated capsule-state pin as defense in depth',
 'ownAuditRuntime':{'receiptSha256':runtime['receiptSha256'],'files':runtime['fileCount'],
                   'resolvedImports':len(runtime['actualImports']),'afterReceipt':str(runtime_file),'afterReceiptSha256':hash_file(runtime_file)},
 'actualBusinessMaterialsRead':0,'originalSpecificationsRead':0,'evaluationMaterialsRead':0,
 'actualCollections':0,'providers':0,'applications':0,'databases':0,
 'syntheticMainAndCopyOnly':True,'nativeReviewPerformed':False,'semanticApproval':False,
 'finalCollectionApproved':False,'newDocumentAdoption':False,
 'limitations':['Production eleven inputs/selection not opened or collected; no claim that actual checkpoint files are malformed',
                'Reference semantics and actual loaded assisted runtime were mocked; only code guards tested',
                'Synthetic state mismatch does not establish bypass of existing production fixed plan-handoff',
                'No atomic-open hostile concurrent filesystem race guarantee']}
out=root/'collector-v4-independent-summary-r01.json'
with out.open('x',encoding='utf-8',newline='\n') as stream:
 json.dump(payload,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'file':str(out),'sha256':hash_file(out),'checkpointFindings':len(payload['checkpointGuardFindings']),
                  'caseCount':payload['caseCount']},ensure_ascii=False))
