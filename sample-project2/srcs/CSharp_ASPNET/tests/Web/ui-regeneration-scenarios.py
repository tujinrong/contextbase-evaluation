from pathlib import Path
import asyncio,json,hashlib,datetime,sys,importlib.util,subprocess,re
from playwright.async_api import async_playwright,expect
import fixture_sql as db

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'.tmp/build-agent/functional';OUT.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('ui_smoke',Path(__file__).with_name('ui-regeneration-smoke.py'));h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h);h.OUT=OUT
results=[];observed={};page_errors=[]
def artifact():
    code="import {hashArtifact} from './agents/builds/build-agent/scripts/ui-conformance.mjs';console.log(hashArtifact('sample-project2/srcs/CSharp_ASPNET/build/publish').sha256);"
    return subprocess.check_output(['node','--input-type=module','-e',code],cwd=ROOT.parents[2],text=True).strip()
async def inspect_raw(page):return await page.locator('[data-field],[data-career]').evaluate_all('(els)=>Object.fromEntries(els.map(e=>[e.dataset.itemId,e.value]))')
async def data(page):return await page.locator('[data-initial]').evaluate('(e)=>JSON.parse(e.dataset.initial)')
async def ready_edit(page):
    await h.go(page,'a[href="/employees"]',r'/employees(?:\?|$)');await page.locator('#search-run').click();await page.wait_for_selector('[data-item-id="F03-I11"]')
    await h.go(page,'[data-item-id="F03-I11"] >> nth=0',r'/employees/[0-9]+/edit(?:\?|$)')
async def select_career(page):
    await page.locator('#careers-tab').click();await page.wait_for_selector('#careers-pane:not([hidden])');await page.locator('#career-rows button').first.click();await expect(page.locator('#f04-i14')).to_be_enabled()
async def set_field(page,id,value):await h.type_text(page,'[data-item-id="'+id+'"]',value)
async def wait_message(page,value):await expect(page.locator('#message')).to_contain_text(value)
async def case(name,browser,fn,user='staff'):
    context=await browser.new_context(ignore_https_errors=True,viewport={'width':1366,'height':768});page=await context.new_page();page.on('pageerror',lambda e:page_errors.append(str(e)))
    requests=[];page.on('request',lambda r:requests.append((r.method,r.url.split('?')[0])))
    try:
        await h.login(page,user);detail=await fn(page,requests);results.append({'id':name,'status':'PASS','detail':detail});print('PASS '+name,flush=True)
    except Exception as e:
        image=await h.shot(page,'failure-'+name);results.append({'id':name,'status':'FAIL','error':str(e),'image':image});print('FAIL '+name+' '+str(e),flush=True)
    finally:await context.close()
async def pending_save(page,requests):
    await ready_edit(page);await select_career(page);before=db.careers();parent_before=db.employee()
    await set_field(page,'F04-I17','UI-BUFFER');await page.locator('#career-apply').click();await wait_message(page,'')
    await expect(page.locator('#career-apply')).to_be_enabled();await asyncio.sleep(.1)
    reflected_db=db.careers();assert reflected_db==before
    await set_field(page,'F04-I17','UI-PENDING-SAVE-'+str(parent_before['revision']+1));captured=await page.locator('#f04-i17').input_value()
    await h.go(page,'#employee-save',r'/employees(?:\?|$)');saved=db.careers();parent_after=db.employee()
    matches=[c for c in saved if c['project_name']==captured]
    assert len(matches)==1 and len(saved)==len(before) and parent_after['revision']==parent_before['revision']+1
    observed['DUI07.pending-save']={'currentUnappliedCareerSaved':len(matches)==1,'careerSavedExactlyOnce':len(matches)==1 and len(saved)==len(before),'parentAndAllCareersAtomic':False,'reflectWritesDb':reflected_db!=before}
    return {'beforeRevision':parent_before['revision'],'afterRevision':parent_after['revision'],'children':len(saved),'pendingMatches':len(matches),'reflectDbUnchanged':True}
async def rollback(page,requests):
    await ready_edit(page);await set_field(page,'F04-I02','山田 太郎 取消確認');await select_career(page);parent_before=db.employee();children_before=db.careers();await set_field(page,'F04-I17','__FAIL_ROLLBACK__')
    raw_before=await inspect_raw(page);state_before=await data(page)
    trigger="CREATE TRIGGER dbo.SP2_UI_ROLLBACK ON dbo.t_career AFTER INSERT,UPDATE AS BEGIN SET NOCOUNT ON; IF EXISTS(SELECT 1 FROM inserted WHERE project_name=N'__FAIL_ROLLBACK__') RAISERROR(N'Owned rollback fixture',16,1); END;"
    db.execute("EXEC(N'"+trigger.replace("'","''")+"');")
    try:
        await page.locator('#employee-save').click();await wait_message(page,'保存できませんでした');await expect(page.locator('#employee-save')).to_be_enabled()
        raw_after=await inspect_raw(page);after=await data(page);unchanged=parent_before==db.employee() and children_before==db.careers()
        props={'rollbackLeavesParentAndChildrenUnchanged':unchanged,'rawAllInputsRetained':raw_before==raw_after,'activeTabRetained':after['activeTab']==state_before['activeTab'],'selectedCareerRetained':after['selectedClientRowKey']==state_before['selectedClientRowKey'],'navigatedAway':'/edit' not in page.url}
        assert all(v for k,v in props.items() if k!='navigatedAway') and not props['navigatedAway'],props
        observed['DUI07.failure-preserve']=props
        observed['DUI07.pending-save']['parentAndAllCareersAtomic']=unchanged
        image=await h.shot(page,'F04-rollback');return {'properties':props,'image':image}
    finally:db.execute('DROP TRIGGER dbo.SP2_UI_ROLLBACK;')
async def invalid_cancel(page,requests):
    await ready_edit(page);before=db.employee();await set_field(page,'F04-I06','20-');await select_career(page);await set_field(page,'F04-I14','202-');raw=await inspect_raw(page)
    await page.locator('#employee-cancel').click();await expect(page.locator('dialog[data-ui="discard"]')).to_be_visible();await page.keyboard.press('Escape')
    await expect(page.locator('dialog[data-ui="discard"]')).not_to_be_visible();assert raw==await inspect_raw(page)
    await page.locator('#employee-cancel').click();await page.locator('dialog [data-part="discard"]').click();await page.wait_for_url(re.compile(r'/employees(?:\?|$)'));await h.ready(page)
    observed['DUI08.cancel']={'invalidFieldsDoNotBlockCancel':True,'continuePreservesAllRaw':True,'discardWritesDb':db.employee()!=before,'dirtyIncludesCurrentUnsentRaw':True,'untouchedNewPrompts':0}
    assert not observed['DUI08.cancel']['discardWritesDb'];return observed['DUI08.cancel']
async def new_save(page,requests):
    await h.go(page,'a[href="/employees"]',r'/employees(?:\?|$)');await set_field(page,'F03-I01','12x');await set_field(page,'F03-I02',' 未適用 ');await page.locator('#f03-i03').select_option('02');await page.locator('#f03-i04').select_option('02')
    before=[await page.locator('#f03-i0'+str(i)).input_value() for i in range(1,5)];start=len(requests);await h.go(page,'#employee-new',r'/employees/new(?:\?|$)')
    existing={r['employee_no'] for r in db.rows("SELECT employee_no FROM dbo.m_employee WHERE employee_no BETWEEN '900001' AND '900099'")};number=next(str(n) for n in range(900001,900100) if str(n) not in existing)
    for id,value in [('F04-I01',number),('F04-I02','検証 社員'),('F04-I03','ケンショウ シャイン'),('F04-I06','2020-01-01')]:await set_field(page,id,value)
    await page.locator('#f04-i04').select_option('01');await h.go(page,'#employee-save',r'/employees(?:\?|$)')
    after=[await page.locator('#f03-i0'+str(i)).input_value() for i in range(1,5)];state=await data(page);count=sum(url.endswith('/employees/search') for method,url in requests[start:])
    props={'dbSavedEmployee':db.employee(number)['employee_name']=='検証 社員','rawFourValuesPreserved':before==after,'originStatusPreserved':state['resultStatus']=='Unapplied','automaticSearchRequests':count,'savedNoticeVisible':'保存しました' in await page.locator('#message').inner_text()};assert props['dbSavedEmployee'] and props['rawFourValuesPreserved'] and props['originStatusPreserved'] and count==0 and props['savedNoticeVisible'];observed['DUI05.new-save-return']=props;return {'employeeNo':number,'properties':props}
async def busy_draft(page,requests):
    await ready_edit(page);await select_career(page);before=await inspect_raw(page);flags=await page.locator('[data-field],[data-career]').evaluate_all('(els)=>Object.fromEntries(els.map(e=>[e.id,[e.disabled,e.readOnly||false]]))')
    started=asyncio.Event()
    async def delay(route):
        response=await route.fetch();started.set();await asyncio.sleep(1);await route.fulfill(response=response)
    await page.route('**/employees/draft',delay);await page.locator('#career-apply').click();await started.wait()
    during=await page.locator('[data-field],[data-career]').evaluate_all('(els)=>els.every(e=>e.disabled)');await page.keyboard.type('LATE');same=before==await inspect_raw(page)
    await expect(page.locator('#career-apply')).to_be_enabled();after_flags=await page.locator('[data-field],[data-career]').evaluate_all('(els)=>Object.fromEntries(els.map(e=>[e.id,[e.disabled,e.readOnly||false]]))')
    assert during and same and flags==after_flags
    observed['busyEmployee']={'employeeInputsDisabledDuringWait':during,'careerInputsDisabledDuringWait':during,'busyInputEditsAccepted':not same,'preRequestRawPreserved':same,'previousDisabledAndReadonlyRestored':flags==after_flags}
    return observed['busyEmployee']
async def lost_save_response(page,requests):
    await ready_edit(page);await set_field(page,'F04-I02','山田 太郎 通信確認'+str(db.employee()['revision']+1));captured=await page.locator('#f04-i02').input_value();start=len(requests);committed={}
    async def abort_after_commit(route):
        response=await route.fetch();body=await response.json();committed.update(body['navigation']);await route.abort('failed')
    await page.route('**/employees/save',abort_after_commit);await page.locator('#employee-save').click();await wait_message(page,'保存結果を確認できません');await asyncio.sleep(.3)
    saved=db.employee()['employee_name']==captured;count=sum(url.endswith('/employees/save') for method,url in requests[start:]);state=await data(page)
    assert saved and committed['commitState']=='Committed' and state['outcome']['commitState']=='Unknown' and await page.locator('#employee-save').is_disabled() and count==1
    return {'serverKnownCommit':committed['commitState'],'browserOutcome':state['outcome']['commitState'],'savedDbEqualsCaptured':saved,'saveRequests':count,'inputRetained':await page.locator('#f04-i02').input_value()==captured}
async def busy_code(page,requests):
    await h.go(page,'a[href="/codes"]',r'/codes(?:\?|$)');await page.locator('#code-rows button').first.click();await expect(page.locator('#f06-i04')).to_be_enabled();before=await page.locator('#f06-i04').input_value();start=asyncio.Event()
    async def delay(route):
        response=await route.fetch();start.set();await asyncio.sleep(1);await route.fulfill(response=response)
    await page.route('**/codes/save',delay);await page.locator('#code-save').click();await start.wait()
    disabled=await page.locator('#codes input:not([type=hidden]),#codes select').evaluate_all('(els)=>els.every(e=>e.disabled)');category=await page.locator('#f06-i01').is_disabled();await page.keyboard.type('LATE');assert before==await page.locator('#f06-i04').input_value()
    await expect(page.locator('#code-save')).to_be_enabled();readonly=await page.locator('#f06-i03').evaluate('(e)=>e.readOnly');assert disabled and category and readonly
    observed['busyCode']={'codeInputsDisabledDuringWait':disabled and category,'readonlyCodeRestored':readonly};return observed['busyCode']
async def main():
    original=artifact()
    async with async_playwright() as p:
        browser=await p.chromium.launch(ignore_default_args=['--disable-back-forward-cache'])
        await case('PENDING-SAVE',browser,pending_save)
        await case('ATOMIC-ROLLBACK',browser,rollback)
        await case('INVALID-CANCEL',browser,invalid_cancel)
        await case('NEW-SAVE-UNAPPLIED',browser,new_save)
        await case('BUSY-DRAFT-INPUTS',browser,busy_draft)
        await case('BUSY-CODE-INPUTS',browser,busy_code,'admin')
        await case('LOST-SAVE-RESPONSE',browser,lost_save_response)
        await browser.close()
    current=artifact();assert original==current,'Artifact changed while executing scenarios'
    record={'runId':'sp2-ui-regenerate-20261029','scope':'Author real browser/owned SQL scenarios; preliminary cycle2, not final UI gate','recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'artifactSha256':original,'contractSha256':hashlib.sha256((ROOT/'tests/ui-contract.json').read_bytes()).hexdigest(),'testSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'results':results,'observed':observed,'pageErrors':page_errors,'formalScore':None}
    (OUT/'result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'passed':sum(x['status']=='PASS' for x in results),'failed':sum(x['status']=='FAIL' for x in results),'pageErrors':page_errors},ensure_ascii=True));return int(any(x['status']=='FAIL' for x in results) or bool(page_errors))
if __name__=='__main__':sys.exit(asyncio.run(main()))
