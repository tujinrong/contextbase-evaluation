"""Join actual browser records. No rule expectation values are read or synthesized."""
from pathlib import Path
import json,hashlib,datetime
ROOT=Path(__file__).resolve().parents[2]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def proof(p):return {'file':str(Path(p).relative_to(ROOT)).replace('\\','/'),'sha256':sha(p)}
def main():
    contract=read(ROOT/'tests/ui-contract.json')
    # Only identifiers/target/property names cross the expectation/observation boundary.
    descriptors={r['id']:{'target':r['target'],'properties':set(r['properties'])} for r in contract['rules'] if r['kind']=='interaction'}
    exclusions={
        'DUI05.invalid-raw':'automaticSearchRequests=0 was recorded without a request/SQL counter for that operation window.',
        'DUI11.state-expiry':'automaticReposts=0 was not backed by a counted request window.',
        'DUI11.tabs':'Search-state copying was exercised; unsaved EditDraft versus another tab saved-value isolation was not prepared.',
        'DUI08.cancel':'Invalid/dirty existing-edit cancel was exercised; untouchedNewPrompts was not measured in this rule execution record.',
        'DUI05.ph05-untouched':'HTTP /employees/search requests were counted; internal SearchReturnCoordinator/SQL-SEARCH0 was not measured.',
        'DUI05.new-save-return':'HTTP /employees/search requests were counted; internal SearchReturnCoordinator/SQL-SEARCH0 was not measured.',
    }
    for status in ('Unsearched','Unapplied','Success','Failed','LimitExceeded'):
        exclusions['DUI11.history.'+status]='Old /ui/attach HTTP200 proves lease validity; it does not compare all old live raw/applied/result/selection/scroll fields.'
    collected={};sources=[];records={};artifact=None;excluded_partials=[]
    base_test_sources={'browser-smoke':'ui-regeneration-smoke.py','history':'ui-regeneration-history.py','functional':'ui-regeneration-scenarios.py','boundaries':'ui-regeneration-boundaries.py'}
    for folder in ('browser-smoke','history','functional','boundaries'):
        path=ROOT/'build/test-results/ui-regeneration'/folder/'result.json';record=read(path);records[folder]=record
        assert record['testSha256']==sha(ROOT/'tests/Web'/base_test_sources[folder]),'Base measurement source changed'
        assert all(r['status']=='PASS' for r in record['results']) and not record['pageErrors'];assert artifact is None or artifact==record['artifactSha256'];artifact=record['artifactSha256'];sources.append(proof(path))
        for id,actual in record.get('observed',{}).items():
            if id not in descriptors:continue
            if id in exclusions:
                excluded_partials.append({'ruleId':id,'reason':exclusions[id],'recordedButNotAdoptedProperties':actual,'evidence':[proof(path)],'notConformanceObservation':True});continue
            properties={key:value for key,value in actual.items() if key in descriptors[id]['properties']}
            collected[id]={'ruleId':id,'target':descriptors[id]['target'],'method':'keyboard-operation','properties':properties,'evidence':[proof(path)]}
    # These values are computed only from independently recorded actual counts/statuses.
    boundaries=records['boundaries']['observed'];history=records['history'];states={r['id']:r for r in history['results']}
    zero=boundaries['DUI06.zero'];limit=boundaries['DUI06.201'];two=boundaries['DUI06.200']
    actual={'zeroIsSuccessfulEmpty':zero['resultStatus']=='Success' and zero['totalCount']==0 and zero['rows']==0,'twoHundredRowsReturned':two['displayedRows'],'employeeNumbersStrictlyAscending':two['stableSort']=='employeeNo ASC','twoHundredAndOneHasPartialRows':limit['rows']!=0,'unsearchedCountIsNull':states['HISTORY-Unsearched']['detail']['totalCount'] is None,'failedCountIsNull':states['HISTORY-Failed']['detail']['totalCount'] is None,'pageSizeControlCount':two['pagingControls']}
    collected['DUI06.boundaries']={'ruleId':'DUI06.boundaries','target':descriptors['DUI06.boundaries']['target'],'method':'keyboard-operation','properties':actual,'evidence':[proof(ROOT/'build/test-results/ui-regeneration/boundaries/result.json'),proof(ROOT/'build/test-results/ui-regeneration/history/result.json')]}
    missing=[]
    for id,d in descriptors.items():
        absent=sorted(d['properties']-set(collected.get(id,{}).get('properties',{})))
        if absent:missing.append({'ruleId':id,'properties':absent,'reason':'Not independently observed in the completed browser/HTTP/SQL records. Native BFCache was not entered; physical IME/clipboard and full remaining branches are not inferred.'})
    # LimitExceeded was assembled separately from the boundary record and is subject to the same old-live-state limitation.
    if 'DUI11.history.LimitExceeded' in collected:
        excluded_partials.append({'ruleId':'DUI11.history.LimitExceeded','reason':exclusions['DUI11.history.LimitExceeded'],'recordedButNotAdoptedProperties':collected['DUI11.history.LimitExceeded']['properties'],'evidence':collected['DUI11.history.LimitExceeded']['evidence'],'notConformanceObservation':True});del collected['DUI11.history.LimitExceeded']
    additional_sources={};property_sources={};partial_rules=[]
    paths=[ROOT/'build/test-results/ui-regeneration-additional'/name for name in ('author.json','behavior.json','sql-diagnostic.json','busy.json','protocol.json','export.json')]
    paths.append(ROOT/'build/test-results/independent-additional-interactions/partial-observations.json')
    paths.append(ROOT/'build/test-results/independent-native-bfcache/partial-observations.json')
    for path in paths:
        record=read(path);assert record['artifact']['sha256']==artifact and record['contractSha256']==sha(ROOT/'tests/ui-contract.json') and record['inputManifestSha256']==sha(ROOT/'build/generation/inputs.json')
        assert not record.get('pageErrors',record.get('errors',[]))
        assert all(x['status']=='PASS' for x in record.get('results',[]))
        for source in record['measurementSources']:
            assert sha(ROOT/source['file'])==source['sha256'],'Additional measurement source changed: '+source['file']
            assert source['file'] not in additional_sources or additional_sources[source['file']]==source
            additional_sources[source['file']]=source
        sources.append(proof(path))
        for actual in record['observations']:
            id=actual['ruleId'];assert id in descriptors;assert actual.get('evidence')
            if 'target' in actual:assert actual['target']==descriptors[id]['target'],'Actual target conflicts with rule descriptor'
            for evidence in actual['evidence']:assert sha(ROOT/evidence['file'])==evidence['sha256']
            item=collected.setdefault(id,{'ruleId':id,'target':descriptors[id]['target'],'method':'keyboard-operation','properties':{},'evidence':[]})
            for key,value in actual['properties'].items():
                if key not in descriptors[id]['properties']:continue
                if key in item['properties']:assert item['properties'][key]==value and type(item['properties'][key]) is type(value),(id,key,'Conflicting actual values')
                item['properties'][key]=value;property_sources.setdefault(id,{}).setdefault(key,[]).append({'executionRecord':proof(path),'evidence':actual['evidence']})
            for evidence in actual['evidence']+[proof(path)]:
                if evidence not in item['evidence']:item['evidence'].append(evidence)
    for id,item in list(collected.items()):
        if descriptors[id]['properties']-set(item['properties']):partial_rules.append(item);del collected[id]
    partial_by_id={x['ruleId']:x for x in partial_rules}
    missing=[{'ruleId':id,'properties':sorted(d['properties']-set(collected.get(id,partial_by_id.get(id,{})).get('properties',{}))),'reason':'Individual properties remain unobserved. The measured portion is preserved separately; physical IME/clipboard or a native BFCache path are not inferred.'} for id,d in descriptors.items() if id not in collected]
    result={'schemaVersion':1,'projectId':'sample-project2','profileId':'CSharp_ASPNET','runId':contract['runId'],'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PARTIAL_ACTUAL_INTERACTION_COLLECTION','artifactSha256':artifact,'contractSha256':sha(ROOT/'tests/ui-contract.json'),'inputManifestSha256':sha(ROOT/'build/generation/inputs.json'),'measurementSources':[proof(ROOT/'tests/Web'/name) for name in ('merge-interaction-observations.py','ui-regeneration-smoke.py','ui-regeneration-history.py','ui-regeneration-scenarios.py','ui-regeneration-boundaries.py','fixture_sql.py')]+list(additional_sources.values()),'executionRecords':sources,'observations':list(collected.values()),'partialRuleObservations':partial_rules,'propertySources':property_sources,'notMeasured':missing,'excludedPartialRuleRecords':excluded_partials,'independentAuditCorrection':'Old unsupported zero/lease-only/unprepared claims remain excluded. New actual properties are joined only from exact current-artifact records, stable measurement sources and individual evidence. Physical IME/clipboard and an unentered native BFCache branch are never inferred.','formalScore':None}
    target=ROOT/'build/test-results/ui-regeneration/interaction-observations.json';target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'observedRules':len(collected),'incompleteRules':len(missing),'artifactSha256':artifact}))
if __name__=='__main__':main()
