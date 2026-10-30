from pathlib import Path
import asyncio,json,sys,importlib.util,time
from playwright.async_api import async_playwright,expect
import additional_runtime as rt
s=importlib.util.spec_from_file_location('cases',Path(__file__).with_name('additional-ui-cases.py'));h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
ROOT=rt.ROOT;OUT=h.OUT;SOURCES=[Path(__file__),Path(__file__).with_name('additional-ui-cases.py'),Path(__file__).with_name('additional_runtime.py'),ROOT/'tests/RuntimeObserver/Program.cs']
async def raw_ui(p):return await p.locator('[data-field],[data-career]').evaluate_all('(n)=>Object.fromEntries(n.map(e=>[e.id,e.value]))')
async def reload_explicit(p):
    p._additional_explicit_cleanup=True
    try:await p.reload();await h.ready(p)
    finally:p._additional_explicit_cleanup=False
def employee():return rt.rows("SELECT * FROM dbo.m_employee WHERE employee_no='000001'")[0]
async def transport(p,c,requests,dialogs):
    await h.search_page(p);capture={};start=len(requests)
    async def open_capture(route):
        response=await route.fetch(max_redirects=0);capture.update(status=response.status,contentType=response.headers.get('content-type'),body=await response.json(),requestContentType=route.request.headers.get('content-type'));await route.fulfill(response=response)
    await p.route('**/employees/open',open_capture);await h.go(p,'#employee-new',r'/employees/new(?:\?|$)');await p.unroute('**/employees/open',open_capture);ticket=capture['body']['navigation']['url'];normal_window=requests[start:];first_gets=sum(x['method']=='GET' and x['url']==rt.URL+ticket for x in normal_window);assert capture['status']==200 and first_gets==1
    consumed=await h.explicit_goto(p,rt.URL+ticket);await h.ready(p);assert consumed.status==410;ticket_once=consumed.status==410 and first_gets==1
    await h.edit_first(p);await p.locator('#f04-i02').fill('');before=await h.vm(p);url=p.url
    async with p.expect_response(lambda r:r.url.endswith('/employees/save')) as rejected_wait:await p.locator('#employee-save').click()
    rejected=await rejected_wait.value;assert rejected.status==422;await expect(p.locator('[data-ui=error-summary]')).to_be_visible();after=await h.vm(p);same_document=url==p.url and before['ui']['documentId']==after['ui']['documentId'];assert same_document
    reload_start=len(requests);await reload_explicit(p);reload_posts=sum(x['method']=='POST' and x['path']=='/employees/save' for x in requests[reload_start:]);assert reload_posts==0
    faults=[]
    for fault in ('redirect','malformed'):
        await h.edit_first(p);await p.locator('#f04-i02').fill('OBS_FAULT_'+fault);values=await raw_ui(p);before_db=employee();url=p.url;at=len(requests);marker='/menu?unexpected='+fault
        async def inject(route,kind=fault):
            if kind=='redirect':await route.fulfill(status=303,headers={'Location':marker},body='')
            else:await route.fulfill(status=200,content_type='application/json',body='{"invalid":')
        await p.route('**/employees/save',inject);await p.locator('#employee-save').click();await expect(p.locator('#message')).to_contain_text('保存結果を確認できません');await asyncio.sleep(.7);state=await h.vm(p);retained=values==await raw_ui(p);count=sum(x['method']=='POST' and x['path']=='/employees/save' for x in requests[at:]);followed=any(x['method']=='GET' and x['url']==rt.URL+marker for x in requests[at:]);assert retained and not followed and count==1 and p.url==url and employee()==before_db and not state['canSave'];await p.unroute('**/employees/save',inject)
        faults.append({'fault':fault,'rawRetained':retained,'followedRedirect':followed,'savePosts':count,'canSave':state['canSave'],'observedWindowMs':700,'outcome':state['outcome']})
    types={x['contentType'] for x in requests if x['method']=='POST' and x['path']!='/account/login'};assert types=={'application/json'}
    props={'protectedPostContentType':next(iter(types)),'navigationEnvelopeStatus':capture['status'],'navigationGetCount':first_gets,'ticketConsumedExactlyOnce':ticket_once,'unexpectedRedirectFollowed':faults[0]['followedRedirect'],'failedSaveKeepsCurrentGetDocument':same_document,'reloadSaveRequests':reload_posts,'malformedResponseKeepsRaw':faults[1]['rawRetained'],'automaticSaveRetries':max(x['savePosts']-1 for x in faults)}
    return {'adopt':{'DUI11.transport':props},'normalResponse':capture,'normalRequestWindow':normal_window,'consumedStatus':consumed.status,'validationHttp':rejected.status,'reloadWindow':requests[reload_start:],'faults':faults,'scope':'Real JSON success200/single GET/one-use410, real validation422 and GET reload, controlled303/malformed-response faults with no backend Save, counted request windows and DB/raw preservation. Retry0 is a finite700ms observation.'}

async def errors_and_commit(p,c,requests,dialogs):
    observed=[]
    async def inspect(response,case):
        await h.ready(p);m=await h.vm(p);error_part=await p.locator('[data-ui=error-message]').count();message_node=p.locator('[data-ui=error-message]' if error_part else '#message');text=await message_node.inner_text();message_visible=await message_node.is_visible();assert message_visible;shell=await p.locator('.header').is_visible() and await p.locator('nav').is_visible();is_json=(await p.locator('body').inner_text()).lstrip().startswith('{');assert response.headers['content-type'].startswith('text/html') and shell and not is_json and __import__('re').search('[\u3040-\u9fff]',text)
        await h.go(p,'[data-ui-error] .actions a[href="/employees"]' if error_part else 'nav a[href="/employees"]',r'/employees(?:\?|$)');completed=__import__('urllib.parse',fromlist=['urlsplit']).urlsplit(p.url).path=='/employees' and await p.locator('.sp2-ui').get_attribute('data-ready')=='true';assert completed;observed.append({'case':case,'status':response.status,'contentType':response.headers['content-type'],'message':text,'messageVisible':message_visible,'outcome':m['outcome'],'sharedShell':shell,'rawJsonVisible':is_json,'nextActionCompleted':completed,'view':'UiError' if error_part else 'SearchFallback'});return m,text
    missing=await p.goto(rt.URL+'/employees/9223372036854775807/edit');assert missing.status==404;await inspect(missing,'missing')
    await h.search_page(p);saved_ticket={}
    async def capture_open(route):
        response=await route.fetch(max_redirects=0);saved_ticket.update(await response.json());await route.fulfill(response=response)
    await p.route('**/employees/open',capture_open);await h.go(p,'#employee-new',r'/employees/new(?:\?|$)');await p.unroute('**/employees/open',capture_open);consumed=await h.explicit_goto(p,rt.URL+saved_ticket['navigation']['url']);assert consumed.status==410;await inspect(consumed,'consumed')
    staff=await c.browser.new_context(ignore_https_errors=True);await h.instrument_context(staff,requests,dialogs);sp=await staff.new_page();await h.login(sp,'staff');forbidden=await sp.goto(rt.URL+'/codes');await h.ready(sp);staff_vm=await h.vm(sp);assert forbidden.status==403 and await sp.locator('[data-ui=error-message]').is_visible();staff_message=await sp.locator('[data-ui=error-message]').inner_text();staff_message_visible=await sp.locator('[data-ui=error-message]').is_visible();staff_shell=await sp.locator('.header').is_visible() and await sp.locator('nav').is_visible();staff_json=(await sp.locator('body').inner_text()).lstrip().startswith('{');assert staff_shell and not staff_json and forbidden.headers['content-type'].startswith('text/html') and __import__('re').search('[\u3040-\u9fff]',staff_message);await h.go(sp,'[data-ui-error] .actions a[href="/employees"]',r'/employees(?:\?|$)');staff_recovered=__import__('urllib.parse',fromlist=['urlsplit']).urlsplit(sp.url).path=='/employees';observed.append({'case':'staff403','status':forbidden.status,'contentType':forbidden.headers['content-type'],'message':staff_message,'messageVisible':staff_message_visible,'outcome':staff_vm['outcome'],'sharedShell':staff_shell,'rawJsonVisible':staff_json,'nextActionCompleted':staff_recovered});await staff.close()
    await h.edit_first(p);state=await h.vm(p);edit_id=state['editStateId'];captured='OBS_KNOWN_COMMIT_'+str(int(time.time()));await p.locator('#f04-i02').fill(captured);save_result={};ticket_gets=[];start=len(requests)
    async def capture_save(route):
        response=await route.fetch(max_redirects=0);save_result.update(await response.json());await route.fulfill(response=response)
    async def abort_ticket_get(route):ticket_gets.append(route.request.url);await route.abort('failed')
    await p.route('**/employees/save',capture_save);await p.route(__import__('re').compile(r'https://localhost:5184/employees\?nav='),abort_ticket_get);await p.locator('#employee-save').click()
    for _ in range(100):
        if ticket_gets:break
        await asyncio.sleep(.05)
    assert ticket_gets and save_result['navigation']['commitState']=='Committed' and employee()['employee_name']==captured
    server_before=h.observer.snapshot(edit_id);assert server_before['fields']['CommitState']=='Committed';ticket=save_result['navigation']['url'];await p.unroute('**/employees/save',capture_save);await p.unroute(__import__('re').compile(r'https://localhost:5184/employees\?nav='),abort_ticket_get)
    wait_start=time.monotonic();await asyncio.sleep(61);elapsed=time.monotonic()-wait_start;expired=await h.explicit_goto(p,rt.URL+ticket);assert expired.status==410;expired_vm,text=await inspect(expired,'expired-known-commit');server_after=h.observer.snapshot(edit_id);assert server_after['fields']['CommitState']=='Committed' and expired_vm['outcome']['commitState']=='Committed' and '保存しました' in text and '失効' in text
    save_count=sum(x['method']=='POST' and x['path']=='/employees/save' for x in requests[start:]);assert save_count==1
    await h.edit_first(p);await p.locator('#f04-i02').fill('OBS_UNKNOWN_'+str(int(time.time())));unknown_capture={};unknown_start=len(requests)
    async def abort_save_after_commit(route):
        response=await route.fetch(max_redirects=0);unknown_capture.update(await response.json());await route.abort('failed')
    await p.route('**/employees/save',abort_save_after_commit);await p.locator('#employee-save').click();await expect(p.locator('#message')).to_contain_text('保存結果を確認できません');await asyncio.sleep(.7);unknown=await h.vm(p);assert unknown_capture['navigation']['commitState']=='Committed' and unknown['outcome']['commitState']=='Unknown' and not unknown['canSave'];assert sum(x['method']=='POST' and x['path']=='/employees/save' for x in requests[unknown_start:])==1;await p.unroute('**/employees/save',abort_save_after_commit)
    error_props={'ordinaryGetContentType':observed[0]['contentType'].split(';')[0],'staffCodesStatus':forbidden.status,'missingEmployeeStatus':missing.status,'expiredTicketStatus':expired.status,'consumedTicketStatus':consumed.status,'japaneseNoticeVisible':all(x['messageVisible'] and bool(x['message']) for x in observed),'sharedShellVisible':all(x['sharedShell'] for x in observed),'nextActionOperable':all(x['nextActionCompleted'] for x in observed),'rawJsonVisible':any(x['rawJsonVisible'] for x in observed),'knownCommitNoticeIncludes14And41':expired_vm['outcome']['messageId']=='MSG-041' and '保存しました' in text and '失効' in text,'unknownKeptDistinctFromKnownCommit':expired_vm['outcome']['commitState']=='Committed' and unknown['outcome']['commitState']=='Unknown'}
    commit_props={'knownCommittedRemainsCommitted':server_before['fields']['CommitState']==server_after['fields']['CommitState']=='Committed','saveRepostsAfterTicketFailure':save_count-1,'unknownNotAssumedRollback':unknown['outcome']['commitState']=='Unknown','unknownCanSave':unknown['canSave']}
    return {'adopt':{'DUI11.get-errors':error_props,'DUI11.commit-navigation':commit_props},'errors':observed,'staff403Message':staff_message,'committedBefore':server_before,'committedAfter':server_after,'ticketWaitSeconds':elapsed,'failedTicketGets':ticket_gets,'saveCountThroughTicketFailure':save_count,'knownSaveEnvelope':save_result,'unknownEnvelope':unknown_capture,'unknownVm':unknown,'scope':'Actual403/404/consumed410/real61sec expired410 Japanese document recovery, committed Save then aborted GET with server-state readback, and committed Save then lost response producing browser Unknown. No fake clock or ticket mutation.'}

async def main():
    start=rt.artifact();anchors={'contractSha256':rt.sha(ROOT/'tests/ui-contract.json'),'inputManifestSha256':rt.sha(ROOT/'build/generation/inputs.json')};assert start['sha256']==h.EXPECTED_ARTIFACT;hashes=[h.proof(p) for p in SOURCES];runner=rt.sha(ROOT/'.tmp/bin/RuntimeObserver/Release/net10.0/RuntimeObserver.dll');h.observer=rt.Observer()
    try:
        async with async_playwright() as pw:
            b=await pw.chromium.launch();selected=sys.argv[1:]
            if not selected or 'transport' in selected:await h.case(b,'protocol-transport',transport)
            if not selected or 'errors' in selected:await h.case(b,'protocol-errors-commit',errors_and_commit)
            await b.close()
    finally:stop=h.observer.stop()
    assert anchors=={'contractSha256':rt.sha(ROOT/'tests/ui-contract.json'),'inputManifestSha256':rt.sha(ROOT/'build/generation/inputs.json')};assert start==rt.artifact() and hashes==[h.proof(p) for p in SOURCES] and runner==rt.sha(ROOT/'.tmp/bin/RuntimeObserver/Release/net10.0/RuntimeObserver.dll')
    record={'runId':'sp2-ui-regenerate-20261029','artifact':start,'contractSha256':rt.sha(ROOT/'tests/ui-contract.json'),'inputManifestSha256':rt.sha(ROOT/'build/generation/inputs.json'),'anchorsAtStart':anchors,'anchorsAtEnd':{'contractSha256':rt.sha(ROOT/'tests/ui-contract.json'),'inputManifestSha256':rt.sha(ROOT/'build/generation/inputs.json')},'measurementSources':hashes,'observerRuntime':{'sha256':runner,'ownership':h.observer.ownership,'stop':stop},'results':h.results,'observations':list(h.observations.values()),'pageErrors':h.errors,'formalScore':None};(OUT/'protocol.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'pass':sum(x['status']=='PASS' for x in h.results),'fail':sum(x['status']=='FAIL' for x in h.results),'errors':h.errors}));return int(any(x['status']=='FAIL' for x in h.results) or bool(h.errors))
if __name__=='__main__':sys.exit(asyncio.run(main()))
