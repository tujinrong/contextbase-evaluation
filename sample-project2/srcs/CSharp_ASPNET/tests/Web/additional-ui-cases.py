from pathlib import Path
import asyncio,json,hashlib,datetime,sys,traceback,re,uuid
from playwright.async_api import async_playwright,expect
import additional_runtime as runtime
ROOT=runtime.ROOT;OUT=ROOT/'build/test-results/ui-regeneration-additional';OUT.mkdir(parents=True,exist_ok=True)
EXPECTED_ARTIFACT='aad4998ca745296c2b670bc2a1f2fdc3159ec5e4112c4f9123088521f24deca4'
results=[];observations={};observer=None;errors=[]
SOURCES=[Path(__file__),Path(__file__).with_name('additional_runtime.py'),ROOT/'tests/RuntimeObserver/Program.cs']
def proof(path):return {'file':Path(path).relative_to(ROOT).as_posix(),'sha256':runtime.sha(path)}
async def vm(p):return await p.locator('[data-initial]').evaluate('(n)=>JSON.parse(n.dataset.initial)')
async def raw(p):return dict(zip(['employeeNo','name','department','employmentStatus'],[await p.locator('#f03-i0'+str(i)).input_value() for i in range(1,5)]))
async def ready(p):await p.wait_for_selector('.sp2-ui[data-ready="true"]');assert await p.locator('.sp2-ui').evaluate('(n)=>!n.inert&&!n.hasAttribute("data-pending-init")')
async def explicit_goto(p,url):
    p._additional_explicit_cleanup=True
    try:return await p.goto(url)
    finally:p._additional_explicit_cleanup=False
async def login(p,user='staff'):
    await p.goto(runtime.URL+'/account/login');await p.locator('[data-item-id="F01-I01"]').fill(user);await p.locator('[data-item-id="F01-I02"]').fill('123');await p.locator('[data-item-id="F01-I04"]').click();await p.wait_for_url('**/menu');await ready(p)
async def go(p,selector,route):
    async with p.expect_navigation(wait_until='domcontentloaded'):await p.locator(selector).click()
    await p.wait_for_url(re.compile(route));await ready(p)
async def search(p):
    async with p.expect_response(lambda r:r.url.endswith('/employees/search')):await p.locator('#search-run').click()
    await expect(p.locator('#search-run')).to_be_enabled()
async def clear(p):await p.locator('#search-clear').click();await expect(p.locator('#search-clear')).to_be_enabled()
async def search_page(p):await explicit_goto(p,runtime.URL+'/employees');await ready(p);await clear(p)
async def edit_first(p):
    await search_page(p);await p.locator('#f03-i01').fill('000001');await search(p);await go(p,'#search-rows a',r'/employees/[0-9]+/edit(?:\?|$)')
async def post(p,path,payload):
    return await p.evaluate('''async ({path,payload})=>{const r=await fetch(path,{method:'POST',redirect:'error',credentials:'same-origin',headers:{'Content-Type':'application/json','X-SP2-CSRF':document.querySelector('input[name="__RequestVerificationToken"]').value,'X-SP2-User-Action':'true'},body:JSON.stringify(payload)});return{status:r.status,body:await r.json(),contentType:r.headers.get('Content-Type')};}''',{'path':path,'payload':payload})
async def warm(context):
    p=await context.new_page();await p.goto(runtime.URL+'/employees');await ready(p);await clear(p);await p.locator('#f03-i01').fill('000001');await search(p);c=runtime.counter();assert c;return p,c
def add_rows(count):
    assert count in (60,201)
    runtime.sql("IF EXISTS(SELECT 1 FROM dbo.m_employee WHERE employee_no BETWEEN '840001' AND '840201') THROW 51000,'Additional range occupied',1; ;WITH N AS(SELECT TOP("+str(count)+") ROW_NUMBER() OVER(ORDER BY object_id) n FROM sys.all_objects) INSERT dbo.m_employee(employee_no,employee_name,employee_kana,department_code,employment_status,join_date,updated_at,updated_by) SELECT RIGHT('000000'+CONVERT(varchar(6),840000+n),6),N'OBS_SCROLL-'+CONVERT(nvarchar(3),n),N'テスト','01','01','20200101',SYSUTCDATETIME(),N'SP2STAFF' FROM N;")
def remove_rows():
    runtime.sql("IF EXISTS(SELECT 1 FROM dbo.t_career c JOIN dbo.m_employee e ON e.employee_id=c.employee_id WHERE e.employee_no BETWEEN '840001' AND '840201') THROW 51000,'Unexpected child in own range',1;DELETE dbo.m_employee WHERE employee_no BETWEEN '840001' AND '840201';")
async def shot(p,name):
    file=OUT/(name+'.png');await p.screenshot(path=str(file),full_page=True);return proof(file)
def adopt(id,properties,detail,file):
    observations[id]={'ruleId':id,'method':'keyboard-operation','properties':properties,'evidence':[proof(file)],'details':detail}
async def case(browser,id,fn,user='staff'):
    context=await browser.new_context(ignore_https_errors=True,viewport={'width':1366,'height':768},accept_downloads=True);requests=[];dialogs=[];await instrument_context(context,requests,dialogs);p=await context.new_page()
    try:
        await login(p,user);data=await fn(p,context,requests,dialogs);record={'id':id,'status':'PASS','data':data,'requests':requests,'dialogs':dialogs};print('PASS '+id,flush=True)
    except Exception as error:
        record={'id':id,'status':'FAIL','error':str(error),'traceback':traceback.format_exc(),'requests':requests,'dialogs':dialogs,'image':await shot(p,'failure-'+id)};print('FAIL '+id+' '+json.dumps(str(error),ensure_ascii=True),flush=True)
    finally:await context.close()
    file=OUT/(id+'.json');file.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8');results.append({**record,'evidence':proof(file)})
    if record['status']=='PASS':
        for rule,props in record['data'].get('adopt',{}).items():adopt(rule,props,record['data'].get('scope'),file)

async def instrument_context(context,requests,dialogs):
    await context.add_init_script("(()=>{const old=HTMLDialogElement.prototype.showModal;HTMLDialogElement.prototype.showModal=function(){console.log('ACTUAL-DIALOG '+JSON.stringify({title:this.querySelector('h2')?.textContent}));return old.apply(this,arguments);};})()")
    def wire(p):
        p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:requests.append({'method':r.method,'path':__import__('urllib.parse',fromlist=['urlsplit']).urlsplit(r.url).path,'url':r.url,'contentType':r.headers.get('content-type')}))
        p.on('console',lambda m:dialogs.append({'kind':'html','value':m.text}) if m.text.startswith('ACTUAL-DIALOG ') else None)
        async def native_dialog(d):
            cleanup=d.type=='beforeunload' and getattr(p,'_additional_explicit_cleanup',False);dialogs.append({'kind':d.type,'explicitPreparationCleanup':cleanup})
            if cleanup:await d.accept()
            else:errors.append('Unexpected native dialog dismissed: '+d.type);await d.dismiss()
        p.on('dialog',native_dialog)
    context.on('page',wire)

async def history(p,context,requests,dialogs,status):
    await search_page(p);added=status in ('Success','LimitExceeded')
    if added:add_rows(60 if status=='Success' else 201);await p.locator('#f03-i02').fill(' OBS_SCROLL ')
    try:
        if status in ('Success','LimitExceeded'):await search(p)
        elif status=='Unapplied':
            await p.locator('#f03-i02').fill(' 未適用 ');await go(p,'#employee-new',r'/employees/new(?:\?|$)');await go(p,'#employee-cancel',r'/employees(?:\?|$)')
        elif status=='Failed':
            runtime.sql("EXEC sys.sp_rename N'dbo.m_employee',N'm_employee_OBS_fault',N'OBJECT';")
            try:await search(p);await expect(p.locator('#message')).to_contain_text('読み込めません')
            finally:runtime.sql("EXEC sys.sp_rename N'dbo.m_employee_OBS_fault',N'm_employee',N'OBJECT';")
        if status=='Success':
            async with p.expect_response(lambda r:r.url.endswith('/employees/select')):await p.locator('#search-rows input[type=radio]').last.check()
            await p.locator('[data-item-id="F03-I08"]').hover();await p.mouse.wheel(0,9000)
            await asyncio.sleep(.4)
        before_vm=await vm(p);assert before_vm['resultStatus']==status;before_raw=await raw(p);old=observer.snapshot(before_vm['stateId']);before_scroll=await p.locator('[data-item-id="F03-I08"]').evaluate('(n)=>n.scrollTop');assert abs(old['fields']['ScrollTop']-before_scroll)<1;warm_page,stats=await warm(context)
        await p.reload();await ready(p);after_vm=await vm(p);after_counter=runtime.counter();count=runtime.delta(stats,after_counter);await warm_page.close();after_old=observer.snapshot(before_vm['stateId'])
        assert old['fields']==after_old['fields'] and old['sha256']==after_old['sha256'],'Old live state changed: '+str([k for k in old['fields'] if old['fields'][k]!=after_old['fields'].get(k)])
        assert after_vm['resultStatus']==status and before_raw==await raw(p) and count==(1 if status=='Success' else 0)
        scroll=await p.locator('[data-item-id="F03-I08"]').evaluate('(n)=>({value:n.scrollTop,max:Math.max(0,n.scrollHeight-n.clientHeight)})');clamped=abs(scroll['value']-min(before_scroll,scroll['max']))<1;assert clamped
        if status=='Success':assert before_scroll>0 and after_vm['selectedEmployeeId']==before_vm['selectedEmployeeId']
        props={'restoredStatus':after_vm['resultStatus'],'rawFourValuesPreserved':before_raw==await raw(p),'appliedSearchRequests':count,'newStateAllocated':before_vm['stateId']!=after_vm['stateId'],'originalLiveStateUnchanged':old['fields']==after_old['fields'],'scrollRetainedOrClamped':clamped}
        return {'adopt':{'DUI11.history.'+status:props},'oldBefore':old,'oldAfter':after_old,'counterBefore':stats,'counterAfter':after_counter,'beforeDomScrollTop':before_scroll,'scroll':scroll,'beforeVm':before_vm,'afterVm':after_vm,'scope':'Actual final-publish Kestrel plus Gate-protected read-only complete old-state comparison; no clock/setter/test middleware.'}
    finally:
        if added:remove_rows()

async def copy_server(p,context,requests,dialogs):
    await search_page(p);await p.locator('#f03-i02').fill(' 元の未適用 ');await go(p,'#employee-new',r'/employees/new(?:\?|$)');await go(p,'#employee-cancel',r'/employees(?:\?|$)');original=await vm(p);old=observer.snapshot(original['stateId']);reference=await p.evaluate('history.state');before_raw=await raw(p)
    copy=await context.new_page();await copy.goto(runtime.URL+'/employees');await ready(copy);await copy.evaluate('(x)=>history.replaceState(x,"","/employees")',reference);await copy.reload();await ready(copy);copied=await vm(copy);assert await raw(copy)==before_raw
    await copy.locator('#f03-i02').fill(' 別Tabの変更 ');await go(copy,'#employee-new',r'/employees/new(?:\?|$)');await go(copy,'#employee-cancel',r'/employees(?:\?|$)');after=observer.snapshot(original['stateId']);assert old['fields']==after['fields']
    props={'copyHasIndependentStateAndLease':original['stateId']!=copied['stateId'] and original['ui']['documentLease']!=copied['ui']['documentLease'],'copyMutationLeavesOriginalUnchanged':old['fields']==after['fields'],'piiOrRawInUrl':any(v.strip() and v.strip() in copy.url for v in before_raw.values())};assert props['copyHasIndependentStateAndLease'] and not props['piiOrRawInUrl'];await copy.close()
    return {'adopt':{'DUI11.tabs':props},'oldBefore':old,'oldAfter':after,'copyVm':copied,'scope':'Property-level actual search copy proof; unsaved EditDraft isolation is measured by the independent audit fixture and must be joined separately.'}

async def searched_return(p,context,requests,dialogs):
    add_rows(60)
    try:
        await search_page(p);await p.locator('#f03-i02').fill(' OBS_SCROLL ');await search(p);before_raw=await raw(p)
        async with p.expect_response(lambda r:r.url.endswith('/employees/select')):await p.locator('#search-rows input[type=radio]').last.check()
        await p.locator('[data-item-id="F03-I08"]').hover();await p.mouse.wheel(0,9000);await asyncio.sleep(.4);original=await vm(p);original_scroll=await p.locator('[data-item-id="F03-I08"]').evaluate('(n)=>n.scrollTop');assert observer.snapshot(original['stateId'])['fields']['ScrollTop']==original_scroll
        await go(p,'#search-rows tr:last-child a',r'/employees/[0-9]+/edit(?:\?|$)');warm_page,stats=await warm(context);await go(p,'#employee-cancel',r'/employees(?:\?|$)');count1=runtime.delta(stats,runtime.counter());await warm_page.close();returned=await vm(p);scroll=await p.locator('[data-item-id="F03-I08"]').evaluate('(n)=>({value:n.scrollTop,max:Math.max(0,n.scrollHeight-n.clientHeight)})');member=returned['selectedEmployeeId']==original['selectedEmployeeId'];clamped=abs(scroll['value']-min(original_scroll,scroll['max']))<1;assert count1==1 and member and clamped and before_raw==await raw(p)
        await go(p,'#search-rows tr:last-child a',r'/employees/[0-9]+/edit(?:\?|$)');await p.locator('#f04-i02').fill('OUT_OF_SEARCH_RESULT');warm_page,stats=await warm(context);await go(p,'#employee-save',r'/employees(?:\?|$)');count2=runtime.delta(stats,runtime.counter());await warm_page.close();nonmember=await vm(p);assert count2==1 and nonmember['selectedEmployeeId'] is None and before_raw==await raw(p)
        props={'appliedSearchRequests':count2,'rawFourValuesPreserved':before_raw==await raw(p),'memberSelectionRestored':member,'nonmemberSubstituted':nonmember['selectedEmployeeId'] is not None,'scrollClampedAndRestored':clamped}
        return {'adopt':{'DUI06.searched-return':props},'memberQueryCount':count1,'nonmemberQueryCount':count2,'memberVm':returned,'nonmemberVm':nonmember,'originalVm':original,'scope':'Actual selected/scrolled60-row member Cancel and saved nonmember return, both owned SQL query windows certified.'}
    finally:remove_rows()

async def main():
    global observer
    start=runtime.artifact();assert start['sha256']==EXPECTED_ARTIFACT;source_hashes=[proof(p) for p in SOURCES];runner_sha=runtime.sha(ROOT/'.tmp/bin/RuntimeObserver/Release/net10.0/RuntimeObserver.dll');observer=runtime.Observer();stop=None
    try:
        async with async_playwright() as pw:
            browser=await pw.chromium.launch();
            choices={'history':lambda:None,'copy':lambda:None,'return':lambda:None};selected=sys.argv[1:]
            if not selected or 'history' in selected:
                for status in ('Unsearched','Unapplied','Success','Failed','LimitExceeded'):await case(browser,'history-'+status,lambda p,c,r,d,s=status:history(p,c,r,d,s))
            if not selected or 'copy' in selected:await case(browser,'copy-server',copy_server)
            if not selected or 'return' in selected:await case(browser,'searched-return',searched_return)
            await browser.close()
    finally:stop=observer.stop()
    assert start==runtime.artifact();assert runner_sha==runtime.sha(ROOT/'.tmp/bin/RuntimeObserver/Release/net10.0/RuntimeObserver.dll');assert source_hashes==[proof(p) for p in SOURCES]
    record={'runId':'sp2-ui-regenerate-20261029','recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'artifact':start,'contractSha256':runtime.sha(ROOT/'tests/ui-contract.json'),'inputManifestSha256':runtime.sha(ROOT/'build/generation/inputs.json'),'measurementSources':source_hashes,'observerRuntime':{'file':'.tmp/bin/RuntimeObserver/Release/net10.0/RuntimeObserver.dll','sha256':runner_sha,'host':observer.ownership,'stopped':stop},'results':results,'observations':list(observations.values()),'pageErrors':errors,'formalScore':None}
    (OUT/'author.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'pass':sum(x['status']=='PASS' for x in results),'fail':sum(x['status']=='FAIL' for x in results),'pageErrors':errors}));return int(any(x['status']=='FAIL' for x in results) or bool(errors))
if __name__=='__main__':sys.exit(asyncio.run(main()))
