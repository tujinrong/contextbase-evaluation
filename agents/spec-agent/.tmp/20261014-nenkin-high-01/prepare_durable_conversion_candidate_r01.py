"""Bounded metadata-only packaging plan. No converter import/export/marker/promotion."""
from pathlib import Path
import ast, hashlib, json, sys
sys.dont_write_bytecode=True
ROOT=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
REPORT=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
REPO=Path(r'D:/開発/contextbase-evaluation')
CANDIDATE=ROOT/'durable-candidate/conversion-scope-r01'
assert not CANDIDATE.exists()
EXPECTED={
    'delivery_model_v2_62_r06.py':'f8bacc711c751659ef0a6497c46e76a496833d20e311cd234111baa7042a1c31',
    'build_xlsx_v2_62_r06.mjs':'33aa7166fbce79874576408ae682a471b52fbaa43269de1dcfe51f401dca0cfd',
    'fs_preflight_v2_62_r02.py':'4c03b060269ee36dbbb1b8368fbb6cde9a95a6f7e91849e376c40919b61c567c',
    'connect_print_metadata_v2_62_r03.py':'4e16de6949f8cf4175904d5d8523ac842c64c7dea2b782e27ed96403dc388f2c',
    'verify_xlsx_v2_62_r02.py':'bf6f59881cd0377dca8dada139f47b000688019683dc07203629558e4c12ab09',
    'format-profile-v2-62-r04.json':'744feb6495adb9b7d25414f678faecacd4c43f767692b9a6fb97c1d3870eef0b',
    'export_pdf_bound_r05.py':'03a6fb7f445b52211c07d50cbd1a07bff413e5a1f91b1b5bfd38fb7d924d84e3',
    'pdf_projection_r04.py':'7bcd51255ceddc0e07e03ff4e26102a9b8689246aab8408f119c89cdf6f13394'}
def ref(path,expected=None):
    value={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    assert expected is None or value['sha256']==expected
    return value
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2)
        f.write('\n')
pins={name:ref(ROOT/'delivery'/name,expected) for name,expected in EXPECTED.items()}
docs={name:ref(REPO/name) for name in ['AGENTS.md','agents/spec-agent/AGENT.md',
    'docs/MD構造・Excel変換規約.md','docs/リポジトリ構成.md']}
source_profile=json.loads((ROOT/'delivery/format-profile-v2-62-r04.json').read_bytes())
profile={'schema':'spec-agent-delivery-format-definition/1','id':'v2-62-preserved-reference',
    'selectionBasis':'INTERPRETATION_OF_REQUEST_TO_PRESERVE_EXISTING_V2_FORMAT',
    'userExplicitlySpecified62':False,
    **{key:source_profile[key] for key in ['cover','normal','itemList','table','generalList','preamble',
        'formulaAuthoring','literalStringStorage','businessContentAuthored','artifactToolPublicApiOnly']}}
assert profile['normal']['columns']==62 and profile['normal']['columnWidth']==3
assert profile['cover']['expectedMergedRegions']==14 and profile['cover']['printArea']=='O6:AU36'
assert profile['itemList']['columns']==10 and profile['table']['declaredContentColumns']==9
profile_path=CANDIDATE/'format-v2-preserved-r01.json'
write(profile_path,profile)
sha_schema={'type':'string','pattern':'^[0-9a-f]{64}$'}
absolute={'type':'string','minLength':3,'pattern':r'^(?:[A-Za-z]:[\\/]|/)[^\r\n\u0000]*$'}
file_ref={'type':'object','additionalProperties':False,'required':['path','sha256'],
    'properties':{'path':absolute,'sha256':sha_schema}}
roots={'type':'object','additionalProperties':False,'required':['workspace','work','report','delivery'],
    'properties':{name:absolute for name in ['workspace','work','report','delivery']}}
runtime={'type':'object','additionalProperties':False,
    'required':['kind','discoveryReceipt','node','python','artifactPublicEntry','artifactPackageJson','analysisDependencies','chromium','poppler'],
    'properties':{'kind':{'const':'bundled-codex-workspace-runtime'},
        'discoveryReceipt':file_ref,'node':file_ref,'python':file_ref,
        'artifactPublicEntry':file_ref,'artifactPackageJson':file_ref,
        'analysisDependencies':file_ref,'chromium':file_ref,'poppler':file_ref}}
schema={'$schema':'https://json-schema.org/draft/2020-12/schema',
    'title':'Candidate structural schema only; does not implement resolved-root or qualification guards',
    'type':'object','additionalProperties':False,
    'required':['schema','agentRole','runId','projectId','referenceMode','businessContentAuthored','applicationExecuted',
        'roots','packageManifest','profile','executionContext','binding','runtime','authoringReceipts','timeouts'],
    'properties':{'schema':{'const':'spec-agent-delivery-execution-contract/1'},'agentRole':{'const':'AG-SPEC'},
        'runId':{'type':'string','minLength':1,'maxLength':128},'projectId':{'type':'string','minLength':1,'maxLength':128},
        'referenceMode':{'const':'source-only'},'businessContentAuthored':{'const':False},'applicationExecuted':{'const':False},
        'roots':roots,'packageManifest':file_ref,
        'profile':{'type':'object','additionalProperties':False,'required':['id','path','sha256'],
            'properties':{'id':{'const':'v2-62-preserved-reference'},'path':absolute,
                'sha256':{'const':ref(profile_path)['sha256']}}},
        'executionContext':file_ref,'binding':file_ref,'runtime':runtime,
        'authoringReceipts':{'type':'object','additionalProperties':False,'required':['xlsx','pdf'],
            'properties':{name:{'anyOf':[file_ref,{'type':'null'}]} for name in ['xlsx','pdf']}},
        'timeouts':{'type':'object','additionalProperties':False,'required':['fsPreflightSeconds','pdfStageSeconds','pdfTotalSeconds'],
            'properties':{'fsPreflightSeconds':{'const':30},'pdfStageSeconds':{'type':'integer','minimum':30,'maximum':300},
                'pdfTotalSeconds':{'type':'integer','minimum':30,'maximum':3600}}}}}
schema_path=CANDIDATE/'execution-config.schema-r01.json'
write(schema_path,schema)
baseline={'schema':'spec-agent-delivery-package-baseline/1','status':'CODE_REVIEW_BASELINE_ONLY_NOT_QUALIFIED',
    'components':pins,'routingRulesRead':docs,'activeFilesModified':False,
    'profileDataSource':pins['format-profile-v2-62-r04.json'],
    'pureProfile':ref(profile_path),'profileExtraction':'Copy only format fields; current run component paths, preparation flags and actualQualification fields are left in this separate baseline audit record.',
    'sourceRuntimeCountsInConversionCore':False,'durableCandidatePrepared':True,'durablyPromoted':False}
baseline_path=CANDIDATE/'baseline-code-pins-r01.json'
write(baseline_path,baseline)
package_plan={
    'schema':'spec-agent-delivery-package-candidate-plan/1','status':'DESIGN_ONLY_REAL_OUTPUT_QA_REQUIRED',
    'candidateRoot':str(CANDIDATE),'intendedPromotionRoot':'agents/spec-agent/tools/delivery',
    'minimalPackage':['run_contract.py','markdown_model.py','artifact_xlsx.mjs','fs_preflight.py',
        'print_metadata.py','verify_xlsx.py','pdf_projection.py','offline_pdf.py',
        'profiles/v2-preserved.json','package-manifest.json'],
    'outsideImmediatePackage':['AI author/plan/review engine','collector/renderer','binding_from_review','publication/backup/swap'],
    'parameterization':[
        {'component':'markdown_model','source':pins['delivery_model_v2_62_r06.py'],
            'change':'Replace OWN_RUN_ROOTS with an explicitly validated run contract passed to load_bound and main IO guards. Keep parse/projection/layout and geometry invariants unchanged.'},
        {'component':'artifact_xlsx','source':pins['build_xlsx_v2_62_r06.mjs'],
            'change':'Replace OWN_TMP/bundled Node/Python/helper/public entry paths and duplicated bootstrap expected paths with the validated pinned contract/package manifest. Keep exactly the same public Artifact methods, cell/merge/border/image/literal operations, read/write preflight and raw receipts.'},
        {'component':'fs_preflight','source':pins['fs_preflight_v2_62_r02.py'],
            'change':'Receive work/report roots from the pinned contract instead of fixed WORKSPACE/run strings. Retain forbidden input/spec/eval components, canonical absolute paths, lstat/reparse checks and hash/freshness/disjointness gates.'},
        {'component':'print_metadata','source':pins['connect_print_metadata_v2_62_r03.py'],
            'change':'Parameterize RUN_DELIVERY and replace exact temporary __file__ equality with installed package origin/SHA equality. Keep connect_bytes/raw XML inverse/ZIP local-record logic byte-for-byte unchanged.'},
        {'component':'verify_xlsx','source':pins['verify_xlsx_v2_62_r02.py'],
            'change':'No format/equality function changes. Only a package caller performs pinned guarded input reads, calls verify(data,document), and records the current native-QA receipt separately.'},
        {'component':'pdf_projection','source':pins['pdf_projection_r04.py'],
            'change':'No projection function/CSS/pixel-window/coverage changes. Keep A3 landscape12mm, 900x600/60px exact RGBA annex windows and HTML inverse restoration.'},
        {'component':'offline_pdf','source':pins['export_pdf_bound_r05.py'],
            'change':'Pass validated run contract through owned() and worker/supervisor and resolve pinned sibling package modules. Retain JavaScript-disabled/network-aborted browser, owned Windows Job handshake, deadline/timeout bounds, canonical byte copies and all-page/text coverage.'}],
    'bootstrapRules':[
        'Configuration is metadata, never Python/JS source or an executable expression. Do not patch globals, synthesize code strings with user data, or replace the active temporary modules.',
        'One configuration path plus exact SHA; reject duplicate JSON/nonfinite numbers/unknown members. Schema validation alone is insufficient: compare resolved workspace-derived work/report/delivery roots, current run/project context and source-only binding identity.',
        'Installed code origin and every package-manifest code SHA must match before and after actual use. New parameterized code gets its own audit and qualification record.',
        'Use the runtime discovery receipt from the bundled dependency tool; enforce actual bundled Node/Python, public @oai/artifact-tool/dist/artifact_tool.mjs and package.json, all current package/dependency/tool pins. Config must not authorize an arbitrary JS entry or private package submodule.',
        'Keep input source/spec/eval directories forbidden, exact Markdown/render permissions, fresh outputs, source/output disjointness, Windows symlink/reparse gates, and caller ownership limitations.',
        'Authoring marker receipts are per new run, actual format/count/ID set and operation. Null means that authoring stage is unavailable; a boolean or an old receipt never creates authorization.',
        'No default based on projectName, no fallback to old output/body, no inferred business column values. 62 is the selected preserved V2 format; docs default120 remains distinct.'
    ],
    'runtimeBridgeBoundary':{
        'observation':'Source13/128 files/13 imports/7 critical module assertions are in the upstream binding bridge, not the converter core.',
        'immediateAction':'Keep upstream validated collection/render/runtime chain and binding receipt immutable; do not promote or weaken the bridge as part of this small converter package.',
        'laterParameterization':'If bridge is promoted separately, take the root-approved exact runtime receipt/root/full inventory/import identities/critical module identities from an immutable execution profile; validate complete actual equality. Derive counts from that accepted manifest plus actual membership, never replace exact inventory checks with arbitrary configured counts.'},
    'firstTwoRequiredReplay':[
        'Use the exact current run two independently approved canonical MD files and their complete same-cap/context/plan text pins, collection/binding/render manifests, canonical HTML and every native PNG SHA. Bind original and parameterized runs to those same inputs; compare all source bytes before/after.',
        'Complete original temporary conversion first and retain actual Artifact author receipts, model value/type/order/blank/literal/sheet-name/merge/image mapping checks. The package candidate may not inherit that qualification.',
        'Review every actual full-size workbook range/native capture for both documents: cover14 ranges O6:AU36, blank approvals/company band top-only, normal A:BJ width3 medium outer/double header, item LIST10 header1 with no data merges/splits, original preamble, all native images and page/row visibility.',
        'For print metadata, retain before/after complete XLSX payload/local-record/raw XML inverse equality plus read-only verifier results; inspect actual landscapeA4 fit-width1 print pages for legibility/clipping. This differs from the authored PDF A3 projection.',
        'For PDF, retain owned READY/PID creationTime/Job assignment/GO evidence, blocked-request/JavaScript-disabled records, exact canonical MD/HTML/source PNG hashes, insertion inverse equality, literal multiplicity and DOM order, every tile RGBA/source extent, and every actual Poppler page hash/native-view index.',
        'Replay the parameterized fresh candidate for the same two sealed documents in a disjoint current-run output root and its own authoring receipts. Repeat the same equality and native gates; compare value/type/order/images/layout constraints rather than demand identical ZIP/PDF bytes with volatile metadata.',
        'Inspect the actual configuration-only diff and pinned module origins; run only meaningful changed-boundary rejection checks (other roots/project/cap/context, stale code/dependency SHA, reparse, wrong public entry, output overlap, stale marker). Avoid rerunning unchanged mirrored suites.'
    ],
    'branchCoverageLimit':'If the first two documents do not use TABLE9 or other non-item LIST widths, those branches remain native-unqualified. Use the first actual reviewed TABLE document and relevant general LIST from this run before claiming those branches qualify; do not fabricate or import business fixtures.',
    'adoptionGate':'Only after baseline actual QA, separate parameterized-code audit, same-input replay equality/native checks and explicit root adoption record, write tools package/profile/manifest and registration docs. Keep old candidates/rejections/receipts. Final output publication is a separate validated gate.',
    'references':{'baseline':ref(baseline_path),'structuralConfigSchema':ref(schema_path),'pureProfile':ref(profile_path)},
    'configurationGuardImplemented':False,'candidateExecutablePrepared':False,'nativeQualified':False,
    'actualXlsxOrPdfAuthored':False,'authoringMarkersExecuted':False,'durablyPromoted':False,
    'AIProvidersExecuted':False,'sourceOrOriginalSpecOrEvaluationOrOldOutputRead':False,
    'businessProseAssembled':False,'formalQualityOr95PercentClaimed':False}
plan_path=CANDIDATE/'package-plan-r01.json'
write(plan_path,package_plan)
sys.path.insert(0,str(REPO/'agents/reverse-agent/.tmp/20261013-rerun-12h/engine-runtime-deps'))
from jsonschema import Draft202012Validator
Draft202012Validator.check_schema(schema)
assert all(ref(ROOT/'delivery'/name)['sha256']==expected for name,expected in EXPECTED.items())
result={'schema':'spec-agent-durable-conversion-candidate-preparation/1','status':'DESIGN_AND_CONFIG_SCHEMA_ONLY',
    'candidate':ref(plan_path),'baseline':ref(baseline_path),'configSchema':ref(schema_path),'pureProfile':ref(profile_path),
    'schemaMetaValidationPassed':True,'runtimeRootGuardImplemented':False,'nativeOrEqualityReplayExecuted':False,
    'activeComponentShaBeforeAfterUnchanged':True,'originalReadSet':'current converter/code metadata and global routing rules only',
    'authoringMarkersExecuted':False,'converterImportsOrCallsExecuted':False,'AIProvidersExecuted':False,'durablyPromoted':False}
report_path=REPORT/'durable-conversion-candidate-preparation-r01.json'
write(report_path,result)
print(json.dumps({'preparation':ref(report_path),'plan':ref(plan_path),'activeComponents':len(EXPECTED),'authoringPerformed':False},ensure_ascii=False))
