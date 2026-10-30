"""Bind independent actual inventories/metrics and partial actual operations to one final artifact."""
from pathlib import Path
import json,hashlib,datetime,subprocess
ROOT=Path(__file__).resolve().parents[2];REPO=ROOT.parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def proof(p):return {'file':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
    non=read(ROOT/'build/test-results/independent-ui/noninteraction/partial-observations.json');operations=read(ROOT/'build/test-results/ui-regeneration/interaction-observations.json');inventory=read(ROOT/'build/test-results/independent-ui/component-inventory-supplement.json')
    code="import {hashArtifact} from './agents/builds/build-agent/scripts/ui-conformance.mjs';console.log(JSON.stringify(hashArtifact('sample-project2/srcs/CSharp_ASPNET/build/publish')));"
    artifact=json.loads(subprocess.check_output(['node','--input-type=module','-e',code],cwd=REPO,text=True));contract_sha=sha(ROOT/'tests/ui-contract.json');input_sha=sha(ROOT/'build/generation/inputs.json')
    for record in (non,inventory):
        assert record['artifact']==artifact and record['contractSha256']==contract_sha and record['inputManifestSha256']==input_sha and not record['errors']
    assert operations['artifactSha256']==artifact['sha256'] and operations['contractSha256']==contract_sha and operations['inputManifestSha256']==input_sha
    assert not non['notMeasured'] and not inventory['notMeasured'];assert all(not x.get('preparationFailed') and not x.get('unresolved') for x in inventory['states'])
    sources={}
    for record in (non,operations,inventory):
        for item in record['measurementSources']:
            assert sha(ROOT/item['file'])==item['sha256'];assert item['file'] not in sources or sources[item['file']]['sha256']==item['sha256'];sources[item['file']]=item
    for p in (Path(__file__),ROOT/'tests/Web/final-candidate-record.py'):sources[p.relative_to(ROOT).as_posix()]=proof(p)
    observations=non['observations']+operations['observations'];assert len({x['ruleId'] for x in observations})==len(observations)
    for observed in observations:
        assert observed.get('evidence')
        for item in observed['evidence']:assert sha(ROOT/item['file'])==item['sha256']
    for component in inventory['components']:
        assert component['matchedCount'] and component['visibleCount'] and component.get('members') and component.get('evidence')
        for item in component['evidence']:assert sha(ROOT/item['file'])==item['sha256']
    result={'schemaVersion':1,'projectId':'sample-project2','profileId':'CSharp_ASPNET','runId':non['runId'],'recordedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'contractSha256':contract_sha,'frozenInputManifestSha256':input_sha,'validatorSha256':sha(REPO/'agents/builds/build-agent/scripts/ui-conformance.mjs'),'artifact':{'file':'build/publish',**artifact},'artifactAfterSha256':artifact['sha256'],'sourcesUnchanged':True,'environment':inventory['environment'],'components':inventory['components'],'observations':observations,'measurementSources':list(sources.values()),'supportingRecords':[proof(ROOT/'build/test-results/independent-ui/noninteraction/partial-observations.json'),proof(ROOT/'build/test-results/independent-ui/component-inventory-supplement.json'),proof(ROOT/'build/test-results/ui-regeneration/interaction-observations.json')],'notMeasured':operations['notMeasured'],'scope':'Actual final-publish independent DOM/CSS/native-kind inventory plus explicitly partial browser/HTTP/SQL operations. No expected value is copied. Logical child ownership is separately proven by containment and measured equal font tuple; no other-state coverage is granted. Browser CSS DPI is measured, physical monitor DPI/IME/clipboard/native BFCache are not assumed.','formalScore':None}
    (ROOT/'build/test-results/ui-observations.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'components':len(result['components']),'observations':len(observations),'notMeasuredRules':len(result['notMeasured']),'artifactSha256':artifact['sha256']}))
if __name__=='__main__':main()
