"""Record immutable technical test evidence; never read business specifications."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re
HERE=Path(__file__).resolve().parent
AGENT=HERE.parents[2]
SOURCE=AGENT/'src'
FROZEN_RECEIPT=HERE.parent/'training-assisted/runtime-code-assisted-06.json'
EXPECTED_RECEIPT='9ef12bc2f6412bddfd9f4d8de45d25f9e5eff1ab31402808d97023aaf6a846e3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(root):
 return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*'))
  if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}
def main():
 assert sha(FROZEN_RECEIPT)==EXPECTED_RECEIPT
 receipt=json.loads(FROZEN_RECEIPT.read_text(encoding='utf8'))
 old=inventory(Path(receipt['destination']))
 assert old==receipt['files'] and len(old)==124
 current=inventory(SOURCE)
 log=HERE/'core-r16-full-r01.log'
 text=log.read_text(encoding='utf-8-sig')
 count=re.search(r'Ran (\d+) tests in ([0-9.]+)s',text)
 assert count and re.search(r'\nOK(?:\r?\n|$)',text) and 'FAILED (' not in text,text[-1000:]
 candidate_files=['contextbase/ai/edge_label_projection.py','contextbase/ai/rendering.py',
  'contextbase/tests/test_ai_edge_label_projection.py','contextbase/tests/test_ai_rendering.py','contextbase/ai/prompts.py']
 diagrams=[]
 for name in ['edge-whole-token','edge-oversized','edge-semantic-reject','edge-unknown-label','edge-markdown-baseline']:
  root=HERE/'core-r16-full-r01'/name
  p=root/'diagram-001.projection.json'
  value=json.loads(p.read_text(encoding='utf8'))
  diagrams.append({'name':name,'receipt':str(p),'receiptSha256':sha(p),
   'status':value['status'],'authorRevisionRequired':value.get('authorRevisionRequired',False),
   'error':value.get('error'),'sourceSha256':value['sourceSha256'],'projectedSha256':value['projectedSha256'],
   'applied':value['applied'],'semanticSignatureEqual':value.get('semanticSignatureEqual',False),
   'wholeVisibleTokensVerified':value['wholeVisibleTokensVerified'],
   'png':str(root/'diagram-001.png') if (root/'diagram-001.png').exists() else None})
 report={'schema':'core-edge-label-projection-regression/1','createdUtc':datetime.now(timezone.utc).isoformat(),
  'status':'PASS_ENGINEERING_REGRESSION_ONLY','suite':{'testCount':int(count[1]),'seconds':float(count[2]),
   'log':str(log),'logSha256':sha(log),'testRunDirectory':str(HERE/'core-r16-full-r01'),'freshRun':True},
  'mainFileCount':len(current),'mainInventory':current,'candidateFileSha256':{p:current[p] for p in candidate_files},
  'addedComparedWithFrozenR14':sorted(set(current)-set(old)),
  'modifiedComparedWithFrozenR14':{p:{'old':old[p],'new':current[p]} for p in old if current.get(p)!=old[p]},
  'frozenR14':{'receipt':str(FROZEN_RECEIPT),'receiptSha256':EXPECTED_RECEIPT,'fileCount':124,'inventoryUnchanged':True},
  'nativeRegressionCases':diagrams,'targetedPriorRun':{'tests':50,'status':'PASS','log':str(HERE/'core-r16-native-r01.log'),'logSha256':sha(HERE/'core-r16-native-r01.log')},
  'visualReview':{'actuallyViewed':['core-r16-native-r01/edge-whole-token/diagram-001.png'],
   'positiveWholeIdentifiersAndNumbersReadable':True,'clusterTitleVisible':True,'negativeCandidatesNotRenderedAsPass':True},
  'projectionRules':{'canonicalMmdBytePreserved':True,'viewOnlyInsertions':'<br/> at whole Latin/number boundaries',
   'reversibleAndIdempotent':True,'semanticSignature':'nodes/shapes/edge IDs/LS-LE endpoints/connection classes/markers/all edge labels/clusters',
   'actualVisibleRowsRequired':True,'unknownPlainLabelMapping':'ERROR','oversizedIndivisibleToken':'ERROR with authorRevisionRequired',
   'markdownLabels':'baseline display unchanged; excluded from whole-token projection','nonFlowDiagrams':'baseline display unchanged'},
  'scope':{'businessSourceOrOriginalSpecRead':False,'canonicalMarkdownEdited':False,'dependencyPackagesEdited':False,
   'oldRuntimeEdited':False,'providerCalls':0,'applicationExecuted':False,'formalGradeAssessed':False,'published':False},
  'limits':['The pass is renderer engineering regression, not formal specification quality or application testing.',
   'Pure Japanese auto wrapping and truly oversized indivisible tokens still need native review or author revision.',
   'Artifact/PDF/XLSX delivery QA must be repeated for current canonical draft and renderer version.',
   'Prompts.py is parent-owned; this task did not edit it.']}
 path=HERE/'core-r16-result.json'
 assert not path.exists()
 path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'path':str(path),'sha256':sha(path),'tests':int(count[1]),'files':len(current),'candidates':report['candidateFileSha256']},ensure_ascii=False))
if __name__=='__main__':main()
