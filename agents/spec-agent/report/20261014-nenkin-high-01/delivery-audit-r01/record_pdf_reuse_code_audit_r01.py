"""Read-only code/tool reuse audit; no old document contents, logs, or writers."""
import hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
A=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
D=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01\delivery')
OLD=Path(r'D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\delivery')
B=Path(r'C:\Users\tujin\.cache\codex-runtimes\codex-primary-runtime\dependencies')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
expected={
 'export_pdf.py':'4d9a08b648db6bbc54807d175f19a6b2a5211edead25cced32bcddc19375a750',
 'export_pdf_r18.py':'29c8d125034bf73c0739e2b594c2b179955f07639529b30a56a58e23a88e25bb',
 'export_pdf_minimum_columns_r19.py':'220b6d38bc719bc912f472fe1d6a00e5fe25d60666af1d719e1f3eddc3493d88',
 'prepare_pdf_screen_r18.py':'27ce2c3d41ba0d9b53dc48b814e8db9f7da4b73f3c53cdf7636763a0caaa7c9b',
 'prepare_registration_detail_pdf_r19_r01.py':'6c4218c6b5659c46510a3b2d053a405ee1b9ca757629bdb428b92585cc4b8408',
 'prepare_pdf_native_tiles_r01.py':'1d24382df3888e9a84f13b4e8368621583c71bed8fff8b06aacf4d08f2bb4976',
}
before={str(OLD/name):sha(OLD/name) for name in expected}
assert all(before[str(OLD/name)]==h for name,h in expected.items())
old_code=(OLD/'export_pdf.py').read_text(encoding='utf-8')
assert '.add_style_tag(' not in old_code
assert 'page.set_content(' in old_code and "context.route('**/*'" in old_code
modules={}
for name,module,metadata in (
 ('pypdf',B/'python/Lib/site-packages/pypdf/__init__.py',B/'python/Lib/site-packages/pypdf-6.10.0.dist-info/METADATA'),
 ('Pillow',B/'python/Lib/site-packages/PIL/__init__.py',B/'python/Lib/site-packages/pillow-12.3.0.dist-info/METADATA'),
):
 text=metadata.read_text(encoding='utf-8');version=re.findall(r'^Version: (.+)$',text,re.M)
 assert len(version)==1
 modules[name]={'entryPath':str(module),'entrySha256':sha(module),'distributionMetadata':str(metadata),'distributionMetadataSha256':sha(metadata),'version':version[0]}
 before[str(module)]=sha(module);before[str(metadata)]=sha(metadata)
chrome=Path(r'C:\Users\tujin\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe')
chromium={'path':str(chrome),'exists':chrome.is_file(),'metadataOnly':True,'launched':False,'compatibilityVerified':False}
if chrome.is_file():chromium.update(sha256=sha(chrome),size=chrome.stat().st_size);before[str(chrome)]=sha(chrome)
receipts={}
for name in ('pdf-runtime-deps-metadata-r01.json','pdf-runtime-deps-metadata-r02.json','pdf-projection-offset-independent-blocker-r01.json','pdf-projection-r04-driver-r05-independent-probes-r01.json'):
 p=A/name;receipts[name]={'path':str(p),'sha256':sha(p)};before[str(p)]=sha(p)
for filename in ('pdf_projection_r04.py','export_pdf_bound_r05.py'):
 before[str(D/filename)]=sha(D/filename)
after={p:sha(Path(p)) for p in before}
assert after==before
record={
 'schema':'spec-agent-pdf-reuse-independent-code-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'scope':'READ_ONLY_CODE_TOOL_METADATA_REUSE_AUDIT','status':'REUSE_IDENTIFIED_CURRENT_FUNCTIONS_QUALIFIED_ACTUAL_PENDING',
 'bundledRuntimeVersion':'26.1011.11113','python':str(B/'python/python.exe'),
 'popplerBin':str(B/'native/poppler/Library/bin'),'modules':modules,'chromiumCandidate':chromium,
 'oldCodePins':{str(OLD/name):expected[name] for name in expected},'newReceipts':receipts,
 'minimumReusePath':[
   {'code':str(OLD/'export_pdf.py'),'lines':[106,112,149,200,208,241,246,253,259],
    'reusable':'Owned worker stage/timeout shape; JS disabled/SW blocked/all routes aborted; set_content with head-inline CSS; pypdf full literal inclusion; Poppler first-to-last page rasterization.',
    'doNotReuseUnchanged':['Old expired deadline, old delivery model/body assumptions, top-level import resolution, taskkill PID supervision, and table/image transformations.']},
   {'code':str(OLD/'prepare_pdf_screen_r18.py'),'lines':[12,19,23,26],
    'reusable':'Mechanical print geometry/head CSS projection pattern only.',
    'doNotRunPreparation':'Contains old document-specific pin assumptions and additional XLSX preparation.'},
   {'code':str(OLD/'export_pdf_minimum_columns_r19.py'),'lines':[240,265,269,272,285],
    'reusable':'Native-size paper geometry and original-size CSS width strategy as a separate optional projection.',
    'limit':'Old adaptive paper/column settings are not the new A3 candidate; no previous review qualifies the new candidate.'},
   {'code':str(OLD/'prepare_pdf_native_tiles_r01.py'),'lines':[34,42,53,61,66,72,75,76],
    'reusable':'Every manifest page count, saved RGBA crop equality, all-row coverage, and before/after pin audit.',
    'limit':'Replace old model/safe_path/binding routing; old actual-review receipts must never substitute for new pages.'},
 ],
 'failureHistoryBoundary':{'currentSourceContainsAddStyleTag':False,'currentCssApplication':'head-inline insertion then set_content(domcontentloaded,45000ms)',
    'oldActualAddStyleTagWaitCauseOrElapsedVerified':False,'reason':'Old logs, business data, and rendering outputs were outside this read-only code scope.',
    'currentStageOwnershipSource':'Old exporter writes flush stages with owned-Popen stage90s/wall900s; new candidate adds READY creationTime→public time comparison→Windows Job assignment→GO.',
    'actualJobOwnershipOrTimeoutTestExecuted':False},
 'coverageBoundary':{'oldCompleteLiteralStringsNotPrefixes':True,'newMinimumDuplicatesAndCanonicalOrderSyntheticVerified':True,
    'normalization':'WHITESPACE_ONLY in current candidate','sourcePopulationCompletenessAssessed':False,
    'graphLabelsReadFromPixelsOrPDFImages':False,'formalQualityAssessed':False,'visualApproval':False},
 'currentKnownLimits':['Inline CSS @import/url is accepted by pure parser and must fail if runtime requests are observed.',
   'Text substring/multiplicity/order evidence does not prove exact cell alignment, graph-label legibility, or all source facts.',
   'GEOMETRY_JS measures whole ASCII tokens only; no actual DOM was executed in this audit.',
   'Approved Python Playwright1.57.0 requires explicit pinned analysisdeps resolution; default isolated Python did not find it.',
   'Browser/PDF/Poppler/Windows Job execution remains untested; every new PDF page still requires original-size visual inspection.'],
 'beforeHashes':before,'afterHashes':after,'allPinnedBytesUnchanged':True,
 'oldCodeExecuted':False,'oldBusinessBodyRead':False,'oldLogsRead':False,'oldOutputsRead':False,
 'actualPdfCreated':False,'actualBrowserStarted':False,'actualPlaywrightImported':False,'markerExecuted':False,
 'providerExecuted':False,'businessInputRead':False,'sourceApplicationExecuted':False,
 'semanticApproval':False,'formalQualityAssessed':False,'stateApproval':False,'wholeApproval':False,'adoption':False,'published':False,
}
p=A/'pdf-reuse-code-only-audit-r01.json'
with p.open('x',encoding='utf-8') as h:json.dump(record,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'path':str(p),'sha256':sha(p),'chromiumMetadata':chromium,'pypdfVersion':modules['pypdf']['version'],'PillowVersion':modules['Pillow']['version']},ensure_ascii=False))
