"""Pin prepared offline PDF code and its limited evidence; no writer is invoked."""
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
D=Path(__file__).parent;O=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
pins={
 'projection':(D/'pdf_projection_r04.py','7bcd51255ceddc0e07e03ff4e26102a9b8689246aab8408f119c89cdf6f13394'),
 'driver':(D/'export_pdf_bound_r05.py','03a6fb7f445b52211c07d50cbd1a07bff413e5a1f91b1b5bfd38fb7d924d84e3'),
 'model':(D/'delivery_model_v2_62_r06.py','f8bacc711c751659ef0a6497c46e76a496833d20e311cd234111baa7042a1c31'),
 'independentSynthetic':(O/'pdf-projection-r04-driver-r05-independent-probes-r01.json','5d598a8f118a869a5a95ff19ad3a6ad3bd7095b6a23524ce020afa166c53c323'),
 'runtimeMetadata':(O/'pdf-runtime-deps-metadata-r02.json','41d00ec3f677e476d4bd8ee985558e338c59959fefb3cd86a93991fef8a0a048'),
 'reuseAudit':(O/'pdf-reuse-code-only-audit-r01.json','21ada17ca87d8a479ef776bfb83bd9bcda74ff058eec46430c1dc7e3bb7e076d'),
 'historicalOffsetFailure':(O/'pdf-projection-offset-independent-blocker-r01.json','c96d389839cbbfd275f0d62ec3d70b387363df977110d129dea5428dee158210'),
}
for path,pin in pins.values():assert digest(path)==pin
deps=json.loads(pins['runtimeMetadata'][0].read_bytes());reuse=json.loads(pins['reuseAudit'][0].read_bytes())
chromium=reuse['chromiumCandidate'];poppler=deps['tools']['pdftoppm']
record={
 'schema':'spec-agent-offline-pdf-preparation-handoff/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'status':'PREPARED_CODE_AND_SYNTHETIC_ONLY_ACTUAL_PDF_PENDING','role':'AG-SPEC','referenceMode':'source-only',
 'pins':{key:{'path':str(path),'sha256':pin} for key,(path,pin) in pins.items()},
 'basis':{'method':'Trusted bound renderer HTML printed with source JavaScript disabled and all requests aborted; no ReportLab business-prose reconstruction.','canonicalStemAndHierarchyPreserved':True,'sourceCapsuleShaDynamicFromBinding':True,'old92FileCapsuleNotHardcoded':True,'excelA4V2PolicyUnchanged':True},
 'paperProjection':{'paper':'A3 landscape','marginMm':12,'scale':1,'tableRecordDrop':0,'cssOnlyInCanonicalBody':True,'insertionsReverseToCanonicalHtmlBytes':True,'nativePixelAnnex':'900x600 windows,60px overlap, no white or transparent tile dropped; small non-inline assets also annexed','sourceMarkdownBOMRetained':True,'retain':['original Markdown bytes','canonical HTML bytes','all original native PNG bytes','separate print projection HTML','exact RGBA tile records','PDF pages and all native Poppler page PNGs']},
 'runtime':{'bundledPython':deps['tools']['bundledPython'],'approvedAnalysisDependencies':deps['approvedAnalysisDependencyRoot'],'pythonPlaywrightVersion':deps['pythonPlaywrightVersion'],'pypdf':reuse['modules']['pypdf'],'Pillow':reuse['modules']['Pillow'],'poppler':poppler,'chromiumCandidate':chromium,'inputMustNeverBeAddedToPythonPath':True,'actualModulePathAndFullNoncacheInventoryCheckRequired':True},
 'boundedOwnership':{'WindowsPublicJobApi':'kill-on-close owned Job Object','workerIdentity':'READY pid+GetProcessTimes creationTime checked before assignment','startOrder':'READY -> matching public process handle -> Job assignment -> GO -> browser launch','stageTimeoutDefaultSeconds':90,'totalTimeoutDefaultSeconds':900,'hiddenWorkerConsole':True,'actualJobAssignmentTested':False,'actualBrowserDescendantsTested':False},
 'qaPrepared':{'independentSyntheticCases':43,'independentStaticChecks':15,'testsInclude':['head/body comments and insertion inverse','active markup/URL/event/meta-refresh/inline-image pin negatives','non-inline small layout included','all-row exact RGBA tile coverage including white/transparent pixels','diagram duplicate multiplicity','literal Unicode/numeric/era/formula-like text','missing/repeated/reordered extracted strings'],'actualPypdfAndPopplerPagesGenerated':False,'allActualNativePagesViewed':False},
 'mustPrecedeActualWriter':['Root final specification count and exactly one NEW-run PDF authoring marker immediately before first actual PDF writer.','Final reviewed source-only Markdown/render binding SHA, per-document source/runtime/render receipts and caller approval must be fixed.','Pin dependency metadata/full non-cache bytes and actual loaded module origins; PYTHONPATH only the approved parser/Playwright dependencies.','Verify trusted Chromium compatibility and owned Windows Job identity/descendant shutdown; current metadata is not an execution test.'],
 'actualQaRequired':['pypdf title/heading/full literal minimum multiplicity and canonical DOM order coverage, including visible original Mermaid code.','Source Markdown/HTML/all PNG bindings and sourcecap rechecked after each document.','Poppler every PDF page captured as PNG; all page hashes/counts and complete image coverage.','An identified actor must view every original-size page and save exact seen-page indices, defects and before/after pins.','Do not equate captures or code/synthetic PASS with visual/source/formal/95percent quality.','Adoption/publication/output replacement remains root-only after all gates.'],
 'recipe':{'environment':{'PYTHONPATH':deps['approvedAnalysisDependencyRoot'],'PYTHONDONTWRITEBYTECODE':'1'},'argv':[deps['tools']['bundledPython']['path'],'-B','-X','utf8',str(pins['driver'][0]),'--binding','<OWN_REVIEWED_BINDING_JSON>','--binding-sha256','<EXACT_BINDING_SHA256>','--output-root','<FRESH_OWN_NEW_RUN_PDF_ROOT>','--chromium',chromium['path'],'--chromium-sha256',chromium['sha256'],'--poppler',poppler['path'],'--poppler-sha256',poppler['sha256'],'--stage-timeout','90','--total-timeout','900','--pdf-marker-completed'],'executeNow':False},
 'knownLimits':['Inline CSS @import/url is not rejected by pure parser; any actual request triggers abort and HOLD. Canonical renderer safety is independently pinned.','Text normalization ignores whitespace only; no Unicode punctuation/era/numeric literal rewrite. The PDF skill ASCII-hyphen preference is subordinate to exact source-character preservation.','Conservative extracted text order may HOLD a visually reordered CSS layout; no silent guard weakening.','ASCII token DOM measurement alone does not prove Japanese clipping, colors, effective visibility, table cell alignment or graph label legibility.','Subprocess/Job/browser/font/Poppler output remain unexecuted; actual native QA is mandatory.','File metadata check/use remains non-atomic; input/runtime/package pins and complete final binding remain required.'],
 'notExecuted':{'businessInputRead':0,'providerCalls':0,'actualPdfWriter':0,'chromiumLaunch':0,'windowsJob':0,'marker':0,'actualPdf':0,'pdfNativePageViews':0,'outputOverwrite':0,'sourceApplicationExecution':0,'formalPercentQualified':False,'sourceUnknownsQualified':False,'wholeApproval':False,'adoption':False,'published':False}
}
out=O/'pdf-preparation-handoff-r01.json'
with out.open('x',encoding='utf-8',newline='\n') as h:json.dump(record,h,ensure_ascii=False,indent=2);h.write('\n')
for path,pin in pins.values():assert digest(path)==pin
print(json.dumps({'path':str(out),'sha256':digest(out)}))
