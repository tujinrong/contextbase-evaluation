"""Independent actual plan/routing metadata audit. No helpers/core imported.
Read only identities, IDs/kinds/paths, routing/schema metadata and pinned code hashes.
No source business content, spec MD/eval, old output, pilot, delivered-file probes.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import hashlib, json, re, unicodedata
ROOT=Path(r'D:/開発/contextbase-evaluation/agents/spec-agent')
WORK=ROOT/'.tmp/20261014-nenkin-high-01'
REPORT=ROOT/'report/20261014-nenkin-high-01'
META=REPORT/'execution-metadata'; AUDIT=REPORT/'independent-audit'
PLAN=WORK/'jobs/plan-04/plan-verified.json'
HANDOFF=WORK/'jobs/plan-04/plan-handoff.json'
CAP=WORK/'snapshot-input-02/manifest.json'
CTX=WORK/'execution-context-input-02.json'
PROJECTION=WORK/'delivery/html_routing_projection_r01.py'
WRITER=WORK/'nenkin_writer_driver_r05.py'
SCHEMA=WORK/'nenkin_execution_metadata_routing_schema_r01.json'
PRIMARY=META/'final-four-folder-routing-plan04-r01.json'
RECORD=META/'author-four-folder-routing-plan04-r01.json'
PREPARATION=AUDIT/'final-routing-plan04-preparation-r01.json'
PREPARER=WORK/'delivery/prepare_final_routing_plan04_r01.py'
EXPECTED={str(PLAN):'e14b5e5acd96aed44c800209efbe452d094cb595f7d57da097b8c9a4a7bc9ee3',
str(HANDOFF):'2815a418a728f5ba8e71ec8a8d0cf7308b1920ecdf283b6ec9288e0831b68660',
str(CAP):'f074529043ff1c25ea53be34c16ae3a4788f137a1e3afb33c6214de7bf4c7445',
str(CTX):'8966757e00954241029817027efa85bafeb859beee5105b05c7c939c84470605',
str(PROJECTION):'542a396124d25f2d279a32430405f336055a4327a46207ef95ce856eff3c5829',
str(WRITER):'6b8e5456d96fabfda1bf43b6c17b6155167726492b10c0f9145473f243ee102c',
str(SCHEMA):'de28dbd6b0b72a1f7dbfb8932579197c61a728cca52abb62193183d0e60d609b',
str(PRIMARY):'82edc7401fcc69cfbac9c17382208745066578e8545ef3588211bf295fcfef85',
str(RECORD):'035fc9f7dcc8aefa6b80702eab14591870da8b5334036d6a4d90856db3cd8cb6',
str(PREPARATION):'ed0148cd3dcb1afef57dd20ac7cb1946f6ac91743d3fa089a2992080f30bbc40',
str(PREPARER):'a2e025e9f9946ff8d8178718079fadca709d5b3c0bfd1b68b1354362117642b0'}
def require(ok,message):
    if not ok:raise ValueError(message)
def safe(path):
    original=Path(path).absolute()
    for node in (original,*original.parents):
        require(not node.is_symlink() and not(node.exists() and getattr(node.lstat(),'st_file_attributes',0)&0x400),'Linked metadata path refused')
    value=original.resolve()
    require(value!=ROOT.resolve() and value.is_relative_to(ROOT.resolve()),'Audit input leaves owned selected agent')
    return value
def sha(path):return hashlib.sha256(safe(path).read_bytes()).hexdigest()
def pairs(items):
    result={}
    for key,value in items:
        require(key not in result,'Duplicate raw JSON member');result[key]=value
    return result
def load(path):return json.loads(safe(path).read_bytes().decode('utf-8-sig'),object_pairs_hook=pairs,
    parse_constant=lambda value:require(False,'Nonfinite raw JSON constant'))
checks=[]
def checked(name,condition):
    require(condition,name);checks.append({'name':name,'passed':True})
checked('all eleven exact before hashes match',all(sha(path)==value for path,value in EXPECTED.items()))
plan=load(PLAN)
# Only document identity/routing metadata is used or included in the audit.
defs=[{'id':d['id'],'kind':d['kind'],'path':d['path']} for d in plan['documents']]
checked('exact plan total and unique IDs',len(defs)==63 and len({d['id'] for d in defs})==63)
excluded=[d for d in defs if d['kind']=='analysis-report']
specs=[d for d in defs if d['kind']!='analysis-report']
checked('exact two analysis reports excluded and 61 specifications selected',len(specs)==61 and excluded==[
    {'id':'ANL-COVERAGE','kind':'analysis-report','path':'analysis/coverage-and-limitations.md'},
    {'id':'ANL-TRACEABILITY','kind':'analysis-report','path':'analysis/identity-reachability-and-differences.md'}])
reserved={'CON','PRN','AUX','NUL','CLOCK$','CONIN$','CONOUT$',*('COM'+n for n in '123456789¹²³'),*('LPT'+n for n in '123456789¹²³')}
def canonical(value):
    require(isinstance(value,str) and value and value==unicodedata.normalize('NFC',value),'Path string/NFC differs')
    segments=value.split('/')
    require(all(part and part not in {'.','..'} and not part.endswith((' ','.')) and
        not any(ord(c)<32 or ord(c)==127 or c in '<>:"\\|?*' for c in part) and part.split('.',1)[0].upper() not in reserved
        for part in segments),'Path is not Windows-safe normalized relative')
    path=PurePosixPath(value)
    require(not path.is_absolute() and path.as_posix()==value,'Canonical relative path differs')
    return path
expected_documents=[]
allpaths=[]
for definition in specs:
    path=canonical(definition['path']);require(path.suffix=='.md','Plan path not .md')
    stem=path.with_suffix('')
    locations={'md':'md/'+path.as_posix(),'html':'html/'+stem.as_posix()+'/'+stem.name+'.html',
        'pdf':'PDF/'+stem.as_posix()+'.pdf','xlsx':'Excel/'+stem.as_posix()+'.xlsx'}
    for location in locations.values():canonical(location);allpaths.append(location)
    expected_documents.append({'documentId':definition['id'],'kind':definition['kind'],'canonicalMarkdownPath':definition['path'],'locations':locations})
checked('244 Windows-safe four-folder paths without case collisions',len(allpaths)==244 and len({p.casefold() for p in allpaths})==244)
identity={'runId':'20261014-nenkin-high-01','projectId':'nenkin','capsuleManifestSha256':EXPECTED[str(CAP)],
    'executionContextSha256':EXPECTED[str(CTX)],'planSha256':EXPECTED[str(PLAN)],'sourceOnly':True}
expected_primary={'schema':'spec-agent-html-publication-routing/1',**identity,'originalApplicationExecuted':False,
    'formalPercentage':None,'published':False,'documents':expected_documents}
primary=load(PRIMARY)
checked('actual primary equals complete independent plan-derived model including order and fields',primary==expected_primary)
checked('primary booleans and null are exact types',type(primary['sourceOnly']) is bool and primary['sourceOnly'] is True and
    type(primary['originalApplicationExecuted']) is bool and primary['originalApplicationExecuted'] is False and
    type(primary['published']) is bool and primary['published'] is False and primary['formalPercentage'] is None)
expected_record={'schema':'spec-agent-same-run-routing-record/1',**identity,
    'businessEvidenceAuthority':False,'originalAppExecuted':False,'originalSpecificationsAuthorized':False,
    'evaluationExpectationsAuthorized':False,'newSourceReadPermissions':False,'documents':[
        {'documentId':d['documentId'],'kind':d['kind'],'path':d['canonicalMarkdownPath'],'disposition':'specification',
            'locations':[{'scope':'specification-bundle','format':format_name,'relativePath':path}
                for format_name,path in d['locations'].items()]} for d in expected_documents],
    'formalPercentage':None,'published':False}
record=load(RECORD)
checked('actual writer record exactly equivalent to complete primary mapping including order',record==expected_record)
checked('writer authority and runtime booleans exact false with percentage null',all(type(record[key]) is bool and record[key] is False
    for key in ['businessEvidenceAuthority','originalAppExecuted','originalSpecificationsAuthorized','evaluationExpectationsAuthorized','newSourceReadPermissions','published'])
    and type(record['sourceOnly']) is bool and record['sourceOnly'] is True and record['formalPercentage'] is None)
# An independent validator for the exact simple schema vocabulary present in the
# pinned actual writer routing schema. No library/helper/pipeline import.
vocabulary={'$schema','type','additionalProperties','required','properties','const','minLength','pattern','minItems','items','enum'}
def validate(schema,value,path='$'):
    require(isinstance(schema,dict) and not(set(schema)-vocabulary),'Unsupported schema vocabulary')
    if 'const' in schema:require(type(value) is type(schema['const']) and value==schema['const'],'Schema const '+path)
    if 'enum' in schema:require(any(type(value) is type(item) and value==item for item in schema['enum']),'Schema enum '+path)
    type_name=schema.get('type')
    if type_name is not None:
        require(type_name in {'object','array','string'},'Unsupported schema type')
        require(type(value) is {'object':dict,'array':list,'string':str}[type_name],'Schema type '+path)
    if isinstance(value,dict):
        require(set(schema.get('required',[]))<=set(value),'Schema required '+path)
        properties=schema.get('properties',{})
        if schema.get('additionalProperties') is False:require(set(value)<=set(properties),'Schema extra '+path)
        for key,item in value.items():
            if key in properties:validate(properties[key],item,path+'.'+key)
    if isinstance(value,list):
        require(len(value)>=schema.get('minItems',0),'Schema minItems '+path)
        if 'items' in schema:
            for index,item in enumerate(value):validate(schema['items'],item,path+'['+str(index)+']')
    if isinstance(value,str):
        require(len(value)>=schema.get('minLength',0),'Schema minLength '+path)
        if 'pattern' in schema:require(re.search(schema['pattern'],value) is not None,'Schema pattern '+path)
validate(load(SCHEMA),record)
checks.append({'name':'actual record validated against exact pinned writer schema vocabulary independently','passed':True})
prep=load(PREPARATION)
checked('preparation output paths and raw hashes exact',prep['projectionAllowlist']=={'path':str(PRIMARY),'sha256':EXPECTED[str(PRIMARY)]}
    and prep['reservedIndexRoutingRecord']=={'path':str(RECORD),'sha256':EXPECTED[str(RECORD)]})
prep_expected={str(path):EXPECTED[str(path)] for path in (PLAN,HANDOFF,CAP,CTX,PROJECTION,SCHEMA)}
checked('preparation exact six input pins and preparer hash',prep['inputPins']==prep_expected and prep['script']=={'path':str(PREPARER),'sha256':EXPECTED[str(PREPARER)]})
checked('preparation counts exclusions order and metadata-only boundaries exact',prep['approvedPlanDocumentCount']==63 and
    prep['specificationRoutingCount']==61 and prep['declaredFormatLocationCount']==244 and prep['excludedReports']==excluded and
    prep['planOrderPreserved'] is True and prep['routingRecordEquivalence'] is True and prep['inputsBeforeAfterUnchanged'] is True and
    all(prep[key] is False for key in ['businessProseAssembled','completedQualifiedOrExistenceClaimsEmitted','actualFilesExistenceVerified',
        'sourceBusinessOrSpecificationOrOldOutputRead','coreHelperProviderRendererBrowserMarkerAuthoringOrPublicationRun','newSyntheticSuitesRun','nativeApproval','published'])
    and prep['formalPercentage'] is None)
checked('all eleven exact after hashes remain unchanged',all(sha(path)==value for path,value in EXPECTED.items()))
audit={'schema':'spec-agent-plan-derived-routing-independent-metadata-audit/1',
    'createdAt':datetime.now(timezone.utc).isoformat(),'reviewer':'/root/delivery_root_review/supplement_collector_review',
    'status':'APPROVED_DESCRIPTIVE_ROUTING_METADATA_ONLY','pinnedFilesBeforeAfter':EXPECTED,
    'inputHashesBeforeAfterUnchanged':True,'planDocumentCount':63,'specificationDocumentCount':61,
    'declaredLocationCount':244,'excludedReports':excluded,'completePlanNonReportSetAndOrderVerified':True,
    'twoRoutingRecordMappingsEquivalent':True,'checks':checks,'checkCount':len(checks),'findings':[],
    'schemaValidationMethod':'Independent recursive exact supported vocabulary of pinned writer routing JSON schema; no helper or core import.',
    'publicationLimit':'Descriptive intended locations only. Not evidence of completed generation, file existence, reviewer acceptance, native approval, formal percentage or actual publication.',
    'limitations':{'actualHelperOrCoreImported':False,'newSyntheticSuitesRun':False,'actualSourceBusinessOrSpecEvalOrOldOutputRead':False,
        'actualMarkdownBusinessBodyRead':False,'actualDeliveredFileExistenceChecked':False,'actualSourceCapsuleVerifiedBeyondManifestHash':False,
        'pilotPolledOrTouched':False,'providerOrApplicationOrBrowserOrMarkersRun':False,'actualStageAuthoringOrPublicationRun':False,
        'nativeQualification':False,'formalPercentage':None,'published':False,'atomicOrRaceFreeProof':False},
    'script':{'path':str(Path(__file__)),'sha256':sha(Path(__file__))}}
target=AUDIT/'final-routing-plan04-independent-metadata-audit-r01.json'
require(not safe(target).exists(),'Fresh own audit output required')
with safe(target).open('x',encoding='utf-8',newline='\n') as stream:json.dump(audit,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'status':audit['status'],'checks':len(checks),'specifications':61,'locations':244,'report':str(target),'sha256':sha(target)}))
