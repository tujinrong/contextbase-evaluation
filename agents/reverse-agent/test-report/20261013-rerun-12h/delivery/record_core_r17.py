"""Fresh evidence for conservative valid long-label lexer extension."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re

HERE=Path(__file__).resolve().parent
AGENT=HERE.parents[2]
SOURCE=AGENT/'src'
RECEIPT=HERE.parent/'training-assisted/runtime-code-assisted-08.json'
RECEIPT_SHA='e899df4800147e4ecb1cf29d5bde52999ac07f074b6b71d34fa7a48e5d9645aa'
PUBLIC_SOURCE=AGENT/'.tmp/render-tools/node_modules/mermaid/dist/chunks/mermaid.core/chunk-EU5HNXII.mjs'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inventory(root):return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*'))
    if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}

def main():
    assert sha(RECEIPT)==RECEIPT_SHA
    receipt=json.loads(RECEIPT.read_text(encoding='utf8'))
    old=inventory(Path(receipt['destination']));assert old==receipt['files'] and len(old)==126
    current=inventory(SOURCE)
    log=HERE/'core-r17-full-r02.log';text=log.read_text(encoding='utf-8-sig')
    count=re.search(r'Ran (\d+) tests in ([0-9.]+)s',text)
    assert count and int(count[1])==404 and '\nOK' in text and 'FAILED (' not in text
    run=HERE/'core-r17-full-r02'
    names=['edge-whole-token','edge-oversized','edge-semantic-reject','edge-unknown-label',
           'edge-markdown-baseline','edge-markdown-collision-reject','edge-dotted-thick-bidir']
    cases=[]
    for name in names:
        path=run/name/'diagram-001.projection.json'
        value=json.loads(path.read_text(encoding='utf8'))
        cases.append({'name':name,'receipt':str(path),'sha256':sha(path),'status':value['status'],
                      'sourceSha256':value['sourceSha256'],'projectedSha256':value['projectedSha256'],
                      'semanticSignatureEqual':value.get('semanticSignatureEqual',False),
                      'wholeVisibleTokensVerified':value.get('wholeVisibleTokensVerified',False),
                      'authorRevisionRequired':value.get('authorRevisionRequired',False),'error':value.get('error')})
    assert not (run/'edge-dotted-ambiguous/diagram-001.png').exists()
    files=['contextbase/ai/edge_label_projection.py','contextbase/ai/rendering.py',
           'contextbase/tests/test_ai_edge_label_projection.py','contextbase/tests/test_ai_rendering.py','contextbase/ai/prompts.py']
    report={'schema':'core-edge-lexer-long-label-regression/1','createdUtc':datetime.now(timezone.utc).isoformat(),
            'status':'PASS_ENGINEERING_REGRESSION_ONLY','revision':'r17',
            'suite':{'testCount':int(count[1]),'seconds':float(count[2]),'log':str(log),'logSha256':sha(log),'freshRunRoot':str(run)},
            'mainFileCount':len(current),'mainInventory':current,'candidateFileSha256':{p:current[p] for p in files},
            'frozenR16':{'receipt':str(RECEIPT),'sha256':RECEIPT_SHA,'fileCount':126,'inventoryUnchanged':True},
            'addedComparedWithFrozenR16':sorted(set(current)-set(old)),
            'modifiedComparedWithFrozenR16':{p:{'old':old[p],'new':current[p]} for p in old if current.get(p)!=old[p]},
            'primaryMermaidSource':{'path':str(PUBLIC_SOURCE),'sha256':sha(PUBLIC_SOURCE),'version':'12.1.0',
                                    'lexerRuleLines':[2234,2265,2421,2422],
                                    'publicDocs':'https://mermaid.js.org/syntax/flowchart.html',
                                    'docsMayRepresentNewerVersion':True},
            'nativeCases':cases,
            'unsupportedAmbiguousNativeCase':{'root':str(run/'edge-dotted-ambiguous'),'finalPngAbsent':True},
            'failedPriorCandidates':[
                {'path':str(HERE/'core-r17-native-r01.log'),'sha256':sha(HERE/'core-r17-native-r01.log'),
                 'reason':'synthetic unquoted decimal dot is not valid bundled dotted long-label syntax; corrected synthetic quote only'},
                {'path':str(HERE/'core-r17-full-r01.log'),'sha256':sha(HERE/'core-r17-full-r01.log'),
                 'reason':'existing 1-second child timeout assertion lacked partial started event; code unmodified, isolated provider suite and fresh full passed'}],
            'isolatedProviderRepeat':{'path':str(HERE/'core-r17-provider-repeat-r01.log'),'sha256':sha(HERE/'core-r17-provider-repeat-r01.log'),'status':'PASS'},
            'scope':{'businessSourceRead':False,'originalSpecificationRead':False,'canonicalMarkdownEdited':False,
                     'dependencyPackageEdited':False,'oldRuntimeEdited':False,'providerCalls':0,
                     'applicationExecuted':False,'wholeSpecificationQualityApproved':False,'published':False},
            'limits':['Engineering regression only; original-size derived-document QA remains required.',
                      'Ambiguous quotes, unmapped labels and oversized indivisible tokens remain errors.',
                      'No original document semantics or formal scores were changed.']}
    out=HERE/'core-r17-result.json';assert not out.exists()
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'path':str(out),'sha256':sha(out),'tests':int(count[1]),'files':len(current),'candidates':report['candidateFileSha256']},ensure_ascii=False))

if __name__=='__main__':main()
