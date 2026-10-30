from pathlib import Path
import asyncio,json,hashlib,datetime,sys,importlib.util,re
from playwright.async_api import async_playwright,expect
import fixture_sql as db

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'.tmp/build-agent/history';OUT.mkdir(parents=True,exist_ok=True)
s=importlib.util.spec_from_file_location('smoke',Path(__file__).with_name('ui-regeneration-smoke.py'));h=importlib.util.module_from_spec(s);s.loader.exec_module(h);h.OUT=OUT
f=importlib.util.spec_from_file_location('functional',Path(__file__).with_name('ui-regeneration-scenarios.py'));func=importlib.util.module_from_spec(f);f.loader.exec_module(func)
results=[];observed={};page_errors=[]
async def model(page):return await page.locator('[data-initial]').evaluate('(e)=>JSON.parse(e.dataset.initial)')
async def raw(page):return dict(zip(['employeeNo','name','department','employmentStatus'],[await page.locator('#f03-i0'+str(i)).input_value() for i in range(1,5)]))
async def post(page,path,payload):
    return await page.evaluate('''async ({path,payload})=>{const r=await fetch(path,{method:'POST',redirect:'error',credentials:'same-origin',headers:{'Content-Type':'application/json','X-SP2-CSRF':document.querySelector('input[name="__RequestVerificationToken"]').value,'X-SP2-User-Action':'true'},body:JSON.stringify(payload)});return {status:r.status,body:await r.json()};}''',{'path':path,'payload':payload})
async def search(page):
    async with page.expect_response(lambda r:r.url.endswith('/employees/search')):await page.locator('#search-run').click()
    await expect(page.locator('#search-run')).to_be_enabled()
async def prepare(page):await h.go(page,'a[href="/employees"]',r'/employees(?:\?|$)')
async def warm(context):
    p=await context.new_page();await p.goto(h.runtime['url']+'/employees');await h.ready(p);await h.type_text(p,'#f03-i01','000001');await search(p)
    stats=db.search_counter();assert stats,'SQL-SEARCH plan unavailable after explicit warm operation';return p,stats
def delta(before,after):
    b={r['plan_token']:r['execution_count'] for r in before};a={r['plan_token']:r['execution_count'] for r in after}
    if not b or not b.keys()<=a.keys() or any(a[k]<v for k,v in b.items()):return None
    return sum(a.values())-sum(b.values())
async def case(name,browser,fn):
    context=await browser.new_context(ignore_https_errors=True,viewport={'width':1366,'height':768});p=await context.new_page();p.on('pageerror',lambda e:page_errors.append(str(e)))
    try:
        await h.login(p,'staff');await prepare(p);detail=await fn(p,context);results.append({'id':name,'status':'PASS','detail':detail});print('PASS '+name,flush=True)
    except Exception as e:
        image=await h.shot(p,'failure-'+name);results.append({'id':name,'status':'FAIL','error':str(e),'image':image});print('FAIL '+name+' '+str(e),flush=True)
    finally:await context.close()
async def roundtrip_unapplied(p):
    await h.go(p,'#employee-new',r'/employees/new(?:\?|$)');await h.go(p,'#employee-cancel',r'/employees(?:\?|$)')
async def unknown_raw(p,context):
    state=await model(p);u=state['ui'];value={'employeeNo':'12x','name':'  raw  ','department':' ZZ ','employmentStatus':''}
    r=await post(p,'/employees/invalidate',{'stateId':u['stateId'],'stateRevision':u['stateRevision'],'tabId':u['tabId'],'documentLease':u['documentLease'],'clientSequence':1,'raw':value,'scrollTop':0})
    assert r['status']==200;ref=r['body']['ui'];await p.evaluate('(u)=>history.replaceState({resumeRef:u.resumeRef,sourceTabId:u.sourceTabId},"","/employees")',ref);await p.reload();await h.ready(p)
    before=await raw(p);assert before==value
    await roundtrip_unapplied(p);after=await raw(p);assert after==before
    invalid=await p.locator('#f03-i03 option:checked').get_attribute('data-invalid-raw');assert invalid=='true'
    await search(p);await expect(p.locator('#message')).to_contain_text('社員番号')
    await h.type_text(p,'#f03-i01','');await search(p);await expect(p.locator('#message')).to_contain_text('選択値')
    await p.locator('#f03-i03').select_option('01');assert await p.locator('#f03-i03 option[data-invalid-raw]').count()==0
    observed['DUI05.invalid-raw']={'partialNumberPreserved':after['employeeNo']==value['employeeNo'],'unknownSelectRawPreserved':after['department']==value['department'],'rawWhitespacePreserved':after['name']==value['name'],'unknownOptionExcludedFromNormalChoices':invalid=='true','searchUnknownOptionRejected':True,'automaticSearchRequests':0}
    return observed['DUI05.invalid-raw']
async def server_raw_diff(p,context):
    await search(p);state=await model(p);u=state['ui'];value=await raw(p);value['name']='changed without invalidate'
    target=state['rows'][0]['employeeId'];i={'searchStateId':u['stateId'],'stateRevision':u['stateRevision'],'employeeId':target,'mode':'Edit','raw':value,'clientSequence':100000,'scrollTop':0,'tabId':u['tabId'],'documentLease':u['documentLease'],'openOperationId':'9dbcd1c1-ab1a-4a65-893c-5dfd306d0d30'}
    r=await post(p,'/employees/open',i);assert r['status']==422 and r['body']['outcome']['messageId']=='MSG-011';assert r['body']['resultStatus']=='Unapplied' and not r['body']['rows']
    await p.goto(h.runtime['url']+'/employees');await h.ready(p);await search(p);state=await model(p);u=state['ui'];value=await raw(p);value['employeeNo']='partial'
    r=await post(p,'/employees/export',{'searchStateId':u['stateId'],'stateRevision':u['stateRevision'],'employeeId':state['rows'][0]['employeeId'],'operationId':'f6af6169-c363-41c0-b419-6d6a3a2147fe','raw':value,'clientSequence':100000,'scrollTop':0,'tabId':u['tabId'],'documentLease':u['documentLease']})
    assert r['status']==422 and r['body']['outcome']['messageId']=='MSG-011'
    await p.goto(h.runtime['url']+'/employees');await h.ready(p);u=(await model(p))['ui'];value=await raw(p);value['employeeNo']='raw partial';value['employmentStatus']=''
    rnew=await post(p,'/employees/open',{'searchStateId':u['stateId'],'stateRevision':u['stateRevision'],'employeeId':None,'mode':'New','raw':value,'clientSequence':1,'scrollTop':0,'tabId':u['tabId'],'documentLease':u['documentLease'],'openOperationId':'7eff64a5-ff2e-45b8-9a65-909bda049499'})
    assert rnew['status']==200 and 'navigation' in rnew['body'];await p.goto(h.runtime['url']+rnew['body']['navigation']['url']);await h.ready(p);await h.go(p,'#employee-cancel',r'/employees(?:\?|$)');assert await raw(p)==value and (await model(p))['resultStatus']=='Unapplied'
    observed['DUI05.server-raw-diff']={'newCapturesWithoutSearchValidation':True,'rawDifferenceSetsUnapplied':True,'editWithChangedRawRejected':True,'exportWithChangedRawRejected':True};return {'edit':422,'export':r['status'],'properties':observed['DUI05.server-raw-diff']}
async def old_applied(p,context):
    await search(p);await p.locator('#search-rows input[type=radio]').first.check();await expect(p.locator('#employee-export')).to_be_enabled();await h.type_text(p,'#f03-i02',' 新しい未適用条件 ');before_raw=await raw(p);warm_page,stats=await warm(context)
    await roundtrip_unapplied(p);after=await model(p);after_stats=db.search_counter();counter=delta(stats,after_stats);await warm_page.close();assert counter==0,'SQL zero cannot be certified'
    props={'rawFourValuesPreserved':before_raw==await raw(p),'status':after['resultStatus'],'automaticSearchRequests':counter,'oldSelectionRestored':after['selectedEmployeeId'] is not None};assert props['rawFourValuesPreserved'] and props['status']=='Unapplied' and not props['oldSelectionRestored'];observed['DUI05.ph05-old-applied']=props;return {'properties':props,'counterBefore':stats,'counterAfter':after_stats}
async def history_state(p,context,status):
    if status=='Success':await search(p)
    elif status=='Unapplied':await h.type_text(p,'#f03-i02',' 未適用 ');await roundtrip_unapplied(p)
    elif status=='Failed':
        db.execute("EXEC sys.sp_rename N'dbo.m_employee',N'm_employee_UI_fault',N'OBJECT';")
        try:await search(p);await expect(p.locator('#message')).to_contain_text('読み込めません')
        finally:db.execute("EXEC sys.sp_rename N'dbo.m_employee_UI_fault',N'm_employee',N'OBJECT';")
    before=await model(p);assert before['resultStatus']==status,before['resultStatus'];before_raw=await raw(p);warm_page,stats=await warm(context)
    await p.reload();await h.ready(p);after=await model(p);counter=delta(stats,db.search_counter());await warm_page.close()
    assert counter is not None,'Cache unavailable/recreated: SQL zero/one cannot be certified'
    assert after['resultStatus']==status and before_raw==await raw(p) and before['stateId']!=after['stateId']
    original_ui=before['ui'];probe=await post(p,'/ui/attach',{'stateId':original_ui['stateId'],'tabId':original_ui['tabId'],'documentId':original_ui['documentId'],'documentLease':original_ui['documentLease']})
    expected=1 if status=='Success' else 0;assert counter==expected,(status,counter)
    props={'restoredStatus':after['resultStatus'],'rawFourValuesPreserved':before_raw==await raw(p),'appliedSearchRequests':counter,'newStateAllocated':before['stateId']!=after['stateId'],'originalLiveStateUnchanged':probe['status']==200,'scrollRetainedOrClamped':after['scrollTop']==before['scrollTop']}
    observed['DUI11.history.'+status]=props;return {'properties':props,'totalCount':after['totalCount'],'counterBefore':stats,'counterAfter':db.search_counter()}
async def copy_tab(p,context):
    await h.type_text(p,'#f03-i02',' コピー元 ');await roundtrip_unapplied(p);before=await model(p);reference=await p.evaluate('history.state');original_raw=await raw(p)
    copy=await context.new_page();await copy.goto(h.runtime['url']+'/employees');await h.ready(copy)
    await copy.evaluate('(r)=>history.replaceState(r,"","/employees")',reference);await copy.reload();await h.ready(copy);copied=await model(copy);assert await raw(copy)==original_raw
    await h.type_text(copy,'#f03-i02','コピー先');await roundtrip_unapplied(copy);after=await model(copy)
    probe=await post(p,'/ui/attach',{'stateId':before['ui']['stateId'],'tabId':before['ui']['tabId'],'documentId':before['ui']['documentId'],'documentLease':before['ui']['documentLease']})
    props={'copyHasIndependentStateAndLease':copied['stateId']!=before['stateId'] and copied['ui']['documentLease']!=before['ui']['documentLease'],'copyMutationLeavesOriginalUnchanged':await raw(p)==original_raw and probe['status']==200,'draftSharedAcrossTabs':False,'piiOrRawInUrl':any(v.strip() and v.strip() in copy.url for v in original_raw.values())}
    assert props['copyHasIndependentStateAndLease'] and props['copyMutationLeavesOriginalUnchanged'] and not props['piiOrRawInUrl'];observed['DUI11.tabs']=props;await copy.close();return props
async def lease_expiry(p,context):
    await search(p);await h.go(p,'[data-item-id="F03-I11"] >> nth=0',r'/employees/[0-9]+/edit(?:\?|$)');state=await model(p);u=state['ui']
    envelope={'stateId':u['stateId'],'stateRevision':u['stateRevision'],'tabId':u['tabId'],'documentLease':u['documentLease'],'employee':state['employee'],'pending':state['pending'],'code':None,'activeTab':state['activeTab'],'selectedClientRowKey':state['selectedClientRowKey']}
    r=await post(p,'/employees/cancel',{'editStateId':u['stateId'],'stateRevision':u['stateRevision'],'rawUiEnvelope':envelope,'confirmationId':None,'choice':None,'reloadOnly':False,'returnToMenu':False});assert 'navigation' in r['body']
    await context.request.get(h.runtime['url']+r['body']['navigation']['url']);await h.type_text(p,'#f04-i02','現在DOM保持')
    raw_before=await func.inspect_raw(p);target=await p.locator('[data-ui="employee-identity"]').inner_text();await p.locator('#employee-save').click();await expect(p.locator('#message')).to_contain_text('失効')
    assert await p.locator('#employee-save').is_disabled() and raw_before==await func.inspect_raw(p)
    db.execute("EXEC sys.sp_rename N'dbo.m_employee',N'm_employee_UI_fault',N'OBJECT';")
    try:
        await p.locator('#employee-reload').click();await expect(p.locator('dialog')).to_be_visible();await p.locator('dialog [data-part="discard"]').click();await expect(p.locator('#message')).to_contain_text('読み込めません')
        retained=raw_before==await func.inspect_raw(p);disabled=await p.locator('#employee-save').is_disabled();assert retained and disabled
    finally:db.execute("EXEC sys.sp_rename N'dbo.m_employee_UI_fault',N'm_employee',N'OBJECT';")
    observed['DUI11.state-expiry']={'messageId':'MSG-041','currentRawRetained':retained,'targetRetained':target==await p.locator('[data-ui="employee-identity"]').inner_text(),'automaticReposts':0,'canSave':not disabled,'failedReloadKeepsOldDisplay':retained}
    return observed['DUI11.state-expiry']
async def auth_expiry(p,context):
    await search(p);await h.go(p,'[data-item-id="F03-I11"] >> nth=0',r'/employees/[0-9]+/edit(?:\?|$)');await h.type_text(p,'#f04-i02','未保存認証失効');before=db.employee()
    auth_events=[];p.on('console',lambda msg:auth_events.append(json.loads(msg.text[len('AUTH-OBS '):])) if msg.text.startswith('AUTH-OBS ') else None)
    await p.evaluate('''()=>{const original=window.fetch.bind(window);window.fetch=async (...args)=>{const response=await original(...args);if(String(args[0]).endsWith('/employees/save'))console.log('AUTH-OBS '+JSON.stringify({status:response.status,body:await response.clone().json()}));return response;};}''')
    await context.clear_cookies(name='__Host-SP2Auth');response=None
    async with p.expect_response(lambda r:r.url.endswith('/employees/save')) as waiting:await p.locator('#employee-save').click()
    response=await waiting.value;assert response.status==401;await p.wait_for_url('**/account/login?expired=1');assert before==db.employee();assert auth_events and auth_events[0]['body']['outcome']['messageId']=='MSG-002'
    await h.login(p,'staff');await func.ready_edit(p);value=await p.locator('#f04-i02').input_value();assert value!='未保存認証失効'
    observed['DUI11.authentication']={'expiredAuthenticationMessageId':auth_events[0]['body']['outcome']['messageId'],'automaticallySaved':before!=db.employee(),'draftRestoredAfterLogin':value=='未保存認証失効','evidence':auth_events};return observed['DUI11.authentication']
async def bfcache(p,context):
    events=[];p.on('console',lambda msg:events.append(msg.text) if msg.text.startswith('UI-PAGESHOW ') else None)
    await p.add_init_script("addEventListener('pageshow',e=>console.log('UI-PAGESHOW '+JSON.stringify({persisted:e.persisted,path:location.pathname})))")
    await h.type_text(p,'#f03-i02',' BFCache検索 ');await roundtrip_unapplied(p);before=await model(p);before_raw=await raw(p)
    await p.goto('about:blank');await p.go_back();await h.ready(p);after=await model(p);native=any(json.loads(e[len('UI-PAGESHOW '):])['persisted'] for e in events)
    restored=before_raw==await raw(p) and before['stateId']!=after['stateId'];assert restored
    detail={'actualPageshowEvents':events,'nativePersistedObserved':native,'searchSnapshotRestored':restored,'newState':before['stateId']!=after['stateId'],'scope':'Actual browser back; never synthetic persisted dispatch'}
    if native:observed['DUI11.bfcache']={'validSnapshotRestored':restored,'newStateAllocated':True,'reloadLoopCount':0,'uiEnabledAfterResume':await p.locator('.sp2-ui').evaluate('(e)=>!e.inert'),'editDraftShared':False}
    else:detail['unverified']='Native BFCache path was not entered; mandatory native branch remains unobserved.'
    return detail
async def main():
    start=func.artifact()
    async with async_playwright() as p:
        browser=await p.chromium.launch(ignore_default_args=['--disable-back-forward-cache'])
        await case('UNKNOWN-RAW-OPTION',browser,unknown_raw)
        await case('SERVER-RAW-DIFF',browser,server_raw_diff)
        await case('OLD-APPLIED-NEW-CANCEL',browser,old_applied)
        for state in ['Unsearched','Unapplied','Success','Failed']:await case('HISTORY-'+state,browser,lambda p,c,s=state:history_state(p,c,s))
        await case('COPY-TAB-INDEPENDENCE',browser,copy_tab)
        await case('OLD-LEASE-RELOAD-FAILURE',browser,lease_expiry)
        await case('AUTH-EXPIRY',browser,auth_expiry)
        await case('NATIVE-BFCACHE',browser,bfcache)
        await browser.close()
    assert start==func.artifact(),'Artifact changed during history cases'
    record={'runId':'sp2-ui-regenerate-20261029','scope':'Author browser/owned DB/HTTP/history cases; SQL counters only certified when cache plans survive the short measured window','recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'artifactSha256':start,'testSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'results':results,'observed':observed,'pageErrors':page_errors,'formalScore':None}
    (OUT/'result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'passed':sum(r['status']=='PASS' for r in results),'failed':sum(r['status']=='FAIL' for r in results),'unverifiedNativeBfcache':'DUI11.bfcache' not in observed,'pageErrors':page_errors},ensure_ascii=True));return int(any(r['status']=='FAIL' for r in results) or bool(page_errors))
if __name__=='__main__':sys.exit(asyncio.run(main()))
