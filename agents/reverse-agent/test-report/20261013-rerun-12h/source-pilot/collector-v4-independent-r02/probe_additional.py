"""Supplement v4 with synthetic checkpoint omissions and real owned junction negatives."""
from __future__ import annotations
import hashlib,json,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
ORIGINAL=HERE.parent/'collector-v4-independent-r01/probe_collector.py'
source=ORIGINAL.read_text(encoding='utf-8')
prefix=source.split('\nRESULTS=[]\n',1)[0]
space={'__file__':str(__file__),'__name__':'synthetic_fixture_definitions_only'}
exec(compile(prefix,str(ORIGINAL)+' [definitions only]','exec'),space)
Fixture=space['Fixture']; store=space['store']; disk_sha=space['disk_sha']
RESULTS=[]

def run(name,mutate=None,accepted=False):
    fixture=Fixture(name)
    if mutate:mutate(fixture)
    error=None
    try:fixture.collect()
    except Exception as exc:error={'type':type(exc).__name__,'message':str(exc)}
    actual=error is None
    row={'name':name,'expected':'ACCEPT' if accepted else 'REJECT','actual':'ACCEPT' if actual else 'REJECT',
         'pass':actual==accepted,'error':error,'capsuleVerifyCalls':fixture.verify_calls,
         'syntheticCopiedFileCount':len(list(fixture.output.rglob('*.md'))) if fixture.output.exists() else 0,
         'linkReads':[x for x in fixture.trace if x['op'].startswith('read_') and '/linked/' in x['path'].replace('\\','/')],
         'reportExists':fixture.outreport.exists()}
    RESULTS.append(row);store(fixture.root/'trace.json',fixture.trace)
    print(json.dumps(row,ensure_ascii=False),flush=True)

def cp_change(fixture,**fields):fixture.change(fixture.documents[0]['checkpoint'],**fields)

def junction(path,target):
    if path.exists():raise FileExistsError(path)
    path.parent.mkdir(parents=True,exist_ok=True);target.mkdir(parents=True,exist_ok=True)
    # Both paths are fixed owned fixture paths. No deleting or moving filesystem entries.
    quoted=lambda p:"'"+str(p).replace("'","''")+"'"
    command='New-Item -ItemType Junction -Path '+quoted(path)+' -Target '+quoted(target)+' | Out-Null'
    result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],
                          capture_output=True,text=True,encoding='utf-8',errors='replace')
    if result.returncode:raise RuntimeError('Owned junction fixture unavailable: '+result.stderr)

def linked_selection(fixture):
    target=fixture.report/'link-target';target.mkdir()
    store(target/'selection.json',fixture.read(fixture.selection))
    junction(fixture.report/'linked',target)
    fixture.selection=fixture.report/'linked/selection.json'

def linked_runtime(fixture):
    target=fixture.root/'link-target';target.mkdir()
    store(target/'never-read.txt',b'owned synthetic linked file')
    junction(fixture.base/'runtime-code/assisted-06/src/linked',target)

run('checkpoint-provider-map-empty',lambda f:cp_change(f,providerArtifactsSha256={}))
run('checkpoint-evidence-map-empty',lambda f:cp_change(f,snapshotEvidenceSha256={}))
run('checkpoint-provider-map-incomplete',lambda f:cp_change(f,providerArtifactsSha256={'answer.txt':disk_sha(f.documents[0]['job']/'provider/answer.txt')}))
run('checkpoint-unrecognized-schema',lambda f:cp_change(f,schema='unexpected'))
run('checkpoint-ai-response-marked-modified',lambda f:cp_change(f,aiResponseBytesModified=True))
run('checkpoint-analysis-documentid-wrong',lambda f:(f.change(f.documents[0]['analysis'],documentId='OTHER'),
    cp_change(f,analysisSha256=disk_sha(f.documents[0]['analysis']))))
run('actual-junction-selection-read-refused',linked_selection)
run('actual-junction-runtime-descend-refused',linked_runtime)

result={'schema':'collector-independent-technical-synthetic-supplement/1','createdAt':datetime.now(timezone.utc).isoformat(),
        'helper':str(space['HELPER']),'helperSha256':space['EXPECTED_SHA'],
        'cases':RESULTS,'total':len(RESULTS),'passed':sum(row['pass'] for row in RESULTS),
        'findings':[row for row in RESULTS if not row['pass']],
        'mockedCapsule':True,'realOwnedJunctions':True,'actualBusinessMaterialsRead':0,
        'actualCollections':0,'providers':0,'applications':0,'oldHelperModified':False,
        'semanticOrVisualApproval':False}
store(HERE/'review.json',result)
print(json.dumps({'review':str(HERE/'review.json'),'sha256':disk_sha(HERE/'review.json'),
                  'total':result['total'],'passed':result['passed'],'findings':result['findings']},ensure_ascii=False),flush=True)
