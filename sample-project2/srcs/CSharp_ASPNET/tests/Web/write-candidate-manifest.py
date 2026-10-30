"""Hash the completed candidate without replacing the rejected formal outputs manifest."""
from pathlib import Path
import json,hashlib,datetime,os,stat
ROOT=Path(__file__).resolve().parents[2];REPO=ROOT.parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def regular(p):
    s=p.lstat()
    if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&1024:raise RuntimeError('Linked/reparse candidate entry refused: '+str(p))
    return s
def walk(directory,excluded):
    regular(directory)
    for p in sorted(directory.iterdir()):
        if p.name in excluded:continue
        s=regular(p)
        if stat.S_ISDIR(s.st_mode):yield from walk(p,excluded)
        elif stat.S_ISREG(s.st_mode):yield p
        else:raise RuntimeError('Non-regular candidate entry: '+str(p))
def item(p):return {'file':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
def main():
    inputs=read(ROOT/'build/generation/inputs.json');run=inputs['runId'];assert run=='sp2-ui-regenerate-20261029'
    for entry in inputs['files']:assert sha(REPO/entry['file'])==entry['sha256'],'Frozen input changed: '+entry['file']
    final=read(ROOT/'build/test-results/final-verification.json');assert final['status']=='CANDIDATE_COMPLETE_UI_INCOMPLETE';assert not(ROOT/'build/generation/outputs.json').exists()
    for p in read(ROOT/'build/generation/source-freeze.json')['files']:assert sha(ROOT/p['file'])==p['sha256']
    source=[item(p) for p in walk(ROOT,{'build','.tmp','.git','.vs','node_modules','bin','obj','dist','__pycache__','.env','appsettings.Local.json'})]
    target=ROOT/'build/generation/candidate-manifest.json';artifacts=[]
    for p in walk(ROOT/'build',set()):
        if p==target or p.name=='outputs.json':continue
        record=item(p);record['scope']='current-publish-resource' if record['file'].startswith('build/publish/') else 'source-only-archive' if p.name=='source.zip' else 'recorded-scope-evidence'
        if p.suffix=='.json':
            try:
                data=read(p)
                if isinstance(data,dict):
                    record['recordRunId']=data.get('runId');record['recordStatus']=data.get('status');artifact=data.get('artifact');record['recordArtifactSha256']=data.get('artifactSha256') or (artifact.get('sha256') if isinstance(artifact,dict) else None)
                    record['currentRun']=record['recordRunId']==run if record['recordRunId'] else None;record['currentArtifact']=record['recordArtifactSha256']==final['artifact']['sha256'] if record['recordArtifactSha256'] else None
            except (ValueError,UnicodeError):record['metadataParse']='not-json-metadata'
        artifacts.append(record)
    result={'schemaVersion':1,'projectId':'sample-project2','profileId':'CSharp_ASPNET','runId':run,'recordedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'CANDIDATE_COMPLETE_UI_INCOMPLETE','formalOutputsManifest':False,'notEquivalentToOutputsJson':True,'inputManifest':item(ROOT/'build/generation/inputs.json'),'artifact':final['artifact'],'uiGateStatus':'FAIL','missingMandatoryInteractionRules':len(final['interaction']['notMeasured']),'sourceFiles':source,'artifacts':artifacts,'scope':'Exact current candidate/source/test/delivery hashes. Records explicitly marked old run/artifact retain only their recorded scope and are not current PASS evidence. This inventory does not override the formal UI gate.','selfReferenceHashPolicy':'This candidate-manifest file is intentionally excluded from its own hashed set.','formalScore':None}
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'status':result['status'],'sourceFiles':len(source),'artifacts':len(artifacts),'sha256':sha(target),'formalOutputsExists':False}))
if __name__=='__main__':main()
