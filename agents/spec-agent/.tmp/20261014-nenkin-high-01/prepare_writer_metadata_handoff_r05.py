"""Fresh code-only handoff; no activation, source/provider read or author execution."""
from pathlib import Path
import hashlib, json
ROOT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
REPORT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
def ref(path):
    return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2)
        f.write('\n')
driver = ref(ROOT / 'nenkin_writer_driver_r05.py')
assert driver['sha256'] == '6b8e5456d96fabfda1bf43b6c17b6155167726492b10c0f9145473f243ee102c'
base = ref(ROOT / 'nenkin_writer_driver_r04.py')
assert base['sha256'] == 'ce836766e61f5abad0fc4d2abfe11b3c6e6588f4dc8b9d46f62f913f0cd8e664'
probe = ref(REPORT / 'independent-audit/writer-metadata-r05-bounded-probes-r02.json')
assert probe['sha256'] == 'a864df9a065feb8cd50b59217249271419d29d9e2530005766c63e3293b7f66d'
schema_refs = {name:ref(ROOT / ('nenkin_execution_metadata_' + name + '_schema_r01.json'))
    for name in ['supplement','routing','completion']}
recipe = {'schema':'spec-agent-author-execution-metadata-recipes/1',
    'candidate':driver,'baseUnchanged':base,'activationSchema':ref(ROOT / 'nenkin_author_activation_schema_r03.json'),
    'supplementSchemas':schema_refs,
    'requirementsBeforeAnyAuthorStart':['Root code audit and a separate activation grant pinned to r05 driver SHA',
        'Independently approved current plan and plan-review pins',
        'Typed supplemental JSON plus routing/completion references in this run execution-metadata folders',
        'All reserved selected document IDs exactly match supplemental target IDs'],
    'prepareArgumentList':['-X','utf8',driver['path'],'prepare','--activation','ROOT_R05_ACTIVATION_PATH',
        '--activation-sha256','ROOT_R05_ACTIVATION_SHA','--wave','FRESH_AUTHOR_WAVE',
        '--document-id','APPROVED_INDEX_OR_ANALYSIS_REPORT_ID','--workers','2','--timeout','2400',
        '--execution-metadata','OWNED_EXECUTION_METADATA_SUPPLEMENT_PATH',
        '--execution-metadata-sha256','EXACT_SUPPLEMENT_SHA'],
    'runArgumentList':['-X','utf8',driver['path'],'run','--preparation','RETURNED_PREPARATION_PATH',
        '--preparation-sha256','RETURNED_PREPARATION_SHA'],
    'revisionExtension':['--revision-from','SAME_RUN_AUTHOR_DOCUMENT_RESULT_PATH','EXACT_RESULT_SHA'],
    'metadataRecordLocations':['WORK/execution-metadata/**/*.json','REPORT/execution-metadata/**/*.json'],
    'recordConstraints':['No free business prose members; schemas reject unknown fields',
        'Current run/project/capsule/context/plan identity must match all referenced routing/completion records',
        'Business-evidence authority and additional source-reading permissions remain false',
        'Completion metadata records state and immutable evidence SHA; formalPercentage is null and published is false',
        'Only index and analysis-report author waves can receive supplemental context'],
    'contextBehavior':'Original full executionContext remains a separate unchanged member; supplement full typed JSON and routing/completion records are appended as sameRunExecutionMetadata.',
    'revisionBehavior':'Complete current-run MD and independent review objects remain preserved; optional mode also preserves raw AI review text and previous supplemental context, with all references pinned.',
    'boundaryCoverage':['before/after composite frozen generation (fresh analysis/repair/draft inside)',
        'before/after separate scoped independent review','before final text pin','wave completion'],
    'internalAnalysisDraftCallbackChecksPerformed':False,'atomicOrRaceFreeProof':False,
    'frozenWorkflowDocumentUnchanged':True,'providerStarts':0,'actualPreparationExecuted':False,'activated':False}
recipe_path = REPORT / 'author-execution-metadata-recipes-r05.json'
write(recipe_path,recipe)
preparation = {'schema':'spec-agent-author-execution-metadata-preparation/1','status':'CODE_ONLY_CANDIDATE_REQUIRES_ROOT_AUDIT',
    'agentRole':'AG-SPEC','projectId':'nenkin','runId':'20261014-nenkin-high-01','mode':'source-only',
    'driver':driver,'baseUnchanged':base,'schemas':schema_refs,'recipe':ref(recipe_path),'boundedProbes':probe,
    'boundedProbeCount':40,'boundedProbesPassed':40,
    'priorInvalidProbe':ref(REPORT / 'independent-audit/writer-metadata-r05-bounded-probes-r01.json'),
    'priorInvalidProbeReason':'jsonschema absent under -I; negative cases also stopped at import, so r01 results are invalidated and are not behavioral evidence',
    'collectorChanged':False,'collectorCompatibilityNote':'Existing collector pins complete wave input.pinnedFiles, but it does not specifically assert supplemental raw prompt context/provenance. Root should decide any supplementary collector verification before adopting r05; no collector change was made here.',
    'boundaryCoverage':recipe['boundaryCoverage'],'internalAnalysisDraftCallbackChecksPerformed':False,
    'atomicOrRaceFreeProof':False,'frozenWorkflowDocumentUnchanged':True,
    'frozenCoreOrLoadedPromptModified':False,'businessProseAssembledByPython':False,'providerStarts':0,
    'originalSourceOrExpectedSpecificationRead':False,'oldOutputRead':False,
    'actualActivationBindingVerified':False,'actualPreviousProviderArtifactsVerified':False,
    'actualGenerationExecuted':False,'actualIndependentReviewExecuted':False,
    'actualNativeOrFormalQualification':False,'durablePromotionPerformed':False,'outputChanged':False,'activated':False}
path = REPORT / 'author-execution-metadata-preparation-r05.json'
write(path,preparation)
print(json.dumps({'preparation':ref(path),'recipe':ref(recipe_path),'providerStarts':0},ensure_ascii=False))
