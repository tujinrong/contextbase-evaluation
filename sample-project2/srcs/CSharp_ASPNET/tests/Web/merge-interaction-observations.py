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
    for folder in ('browser-smoke','history','functional','boundaries'):
        path=ROOT/'build/test-results/ui-regeneration'/folder/'result.json';record=read(path);records[folder]=record
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
    missing=[{'ruleId':id,'properties':sorted(d['properties']-set(collected.get(id,{}).get('properties',{}))),'reason':exclusions.get(id,'Not independently observed in the completed records. Native BFCache was not entered; physical IME/clipboard and remaining branches are not inferred.')} for id,d in descriptors.items() if d['properties']-set(collected.get(id,{}).get('properties',{}))]
    result={'schemaVersion':1,'projectId':'sample-project2','profileId':'CSharp_ASPNET','runId':contract['runId'],'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PARTIAL_ACTUAL_INTERACTION_COLLECTION','artifactSha256':artifact,'contractSha256':sha(ROOT/'tests/ui-contract.json'),'inputManifestSha256':sha(ROOT/'build/generation/inputs.json'),'measurementSources':[proof(ROOT/'tests/Web'/name) for name in ('merge-interaction-observations.py','ui-regeneration-smoke.py','ui-regeneration-history.py','ui-regeneration-scenarios.py','ui-regeneration-boundaries.py','fixture_sql.py')],'executionRecords':sources,'observations':list(collected.values()),'notMeasured':missing,'excludedPartialRuleRecords':excluded_partials,'independentAuditCorrection':'Unmeasured zero counters, lease-only state assertions, unprepared EditDraft isolation and insufficient automatic-query counting are not adopted as actual conformance values. Original execution records are retained at their partial scope.','formalScore':None}
    target=ROOT/'build/test-results/ui-regeneration/interaction-observations.json';target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'observedRules':len(collected),'incompleteRules':len(missing),'artifactSha256':artifact}))
if __name__=='__main__':main()
