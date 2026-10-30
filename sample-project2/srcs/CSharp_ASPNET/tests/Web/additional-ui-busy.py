from pathlib import Path
import asyncio,json,sys,importlib.util
from playwright.async_api import async_playwright,expect
import additional_runtime as rt
s=importlib.util.spec_from_file_location('cases',Path(__file__).with_name('additional-ui-cases.py'));h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
b=importlib.util.spec_from_file_location('behavior',Path(__file__).with_name('additional-ui-behavior.py'));behavior=importlib.util.module_from_spec(b);b.loader.exec_module(behavior)
ROOT=rt.ROOT;OUT=h.OUT;SOURCES=[Path(__file__),Path(__file__).with_name('additional-ui-cases.py'),Path(__file__).with_name('additional-ui-behavior.py'),Path(__file__).with_name('additional_runtime.py'),ROOT/'tests/RuntimeObserver/Program.cs']
async def flags(p,selector):return await p.locator(selector).evaluate_all('(n)=>Object.fromEntries(n.map(e=>[e.id,{disabled:e.disabled,readOnly:!!e.readOnly,value:e.value}]))')
async def pause(p,path,trigger,during):
    arrived=asyncio.Event();release=asyncio.Event();finished=asyncio.Event()
    async def route(r):
        try:arrived.set();await release.wait();await r.continue_()
        finally:finished.set()
    await p.route('**'+path,route)
    try:
        await trigger();await asyncio.wait_for(arrived.wait(),10);result=await during();release.set();await asyncio.wait_for(finished.wait(),10);return result
    finally:release.set();await asyncio.wait_for(finished.wait(),10);await p.unroute('**'+path,route)
async def busy(p,c,requests,dialogs):
    await h.edit_first(p);await p.locator('#f04-i02').fill('');await p.locator('#careers-tab').click();await expect(p.locator('#careers-tab')).to_have_attribute('aria-selected','true');await p.locator('#career-rows button').first.click();await expect(p.locator('#f04-i14')).to_be_enabled();selector='#edit input:not([type=hidden]),#edit select,#edit textarea';before=await flags(p,selector);before_raw=await behavior.all_raw(p);db_before=behavior.dbhash()
    async def employee_wait():
        current=await flags(p,selector);assert current and all(x['disabled'] for x in current.values());await p.keyboard.press('Tab');await p.keyboard.type('LATE');retained=await behavior.all_raw(p)==before_raw;assert retained;return {'during':current,'allDisabled':all(x['disabled'] for x in current.values()),'rawRetained':retained}
    async with p.expect_response(lambda r:r.url.endswith('/employees/save')) as response:
        employee=await pause(p,'/employees/save',lambda:p.locator('#employee-save').click(),employee_wait)
    assert (await response.value).status==422;await expect(p.locator('#employee-save')).to_be_enabled();restored=await flags(p,selector);restore_flags={k:(v['disabled'],v['readOnly']) for k,v in restored.items()}=={k:(v['disabled'],v['readOnly']) for k,v in before.items()};assert restore_flags and behavior.dbhash()==db_before and before_raw==await behavior.all_raw(p)
    captured='OBS_BUSY_EMP_'+str(rt.rows("SELECT revision FROM dbo.m_employee WHERE employee_no='000001'")[0]['revision']+1);await p.locator('#f04-i02').fill(captured)
    async def success_wait():
        f=await flags(p,selector);assert all(x['disabled'] for x in f.values());await p.keyboard.type('LATE');assert await p.locator('#f04-i02').input_value()==captured;return f
    await pause(p,'/employees/save',lambda:p.locator('#employee-save').click(),success_wait);await p.wait_for_url(__import__('re').compile(r'/employees(?:\?|$)'));await h.ready(p);employee_db=rt.rows("SELECT employee_name FROM dbo.m_employee WHERE employee_no='000001'")[0]['employee_name'];assert employee_db==captured
    await h.go(p,'nav a[href="/codes"]',r'/codes(?:\?|$)');await p.locator('#code-rows button').first.click();await expect(p.locator('#f06-i04')).to_be_enabled();code_selector='#codes input:not([type=hidden]),#codes select,#codes textarea';code_before=await flags(p,code_selector);name='OBS_BUSY_CODE_'+str(rt.rows("SELECT revision FROM dbo.m_code WHERE category_id='DEPARTMENT' AND code='01'")[0]['revision']+1);await p.locator('#f06-i04').fill(name)
    async def code_wait():
        f=await flags(p,code_selector);assert f and all(x['disabled'] for x in f.values());await p.keyboard.type('LATE');assert await p.locator('#f06-i04').input_value()==name;return f
    code_during=await pause(p,'/codes/save',lambda:p.locator('#code-save').click(),code_wait);await expect(p.locator('#code-save')).to_be_enabled();code_after=await flags(p,code_selector);code_restore=all((v['disabled'],v['readOnly'])==(code_after[k]['disabled'],code_after[k]['readOnly']) for k,v in code_before.items());code_db=rt.rows("SELECT code_name FROM dbo.m_code WHERE category_id='DEPARTMENT' AND code='01'")[0]['code_name'];assert code_restore and code_db==name
    await h.search_page(p);await p.locator('#f03-i01').fill('000001');await h.search(p);start=len(requests)
    async def link_wait():
        a=await p.locator('#employee-new').get_attribute('aria-disabled');rows=await p.locator('#search-rows a').evaluate_all('(n)=>n.map(e=>e.getAttribute("aria-disabled"))');assert a=='true' and rows and all(x=='true' for x in rows)
        await p.locator('#employee-new').click(force=True);await p.locator('#search-rows a').first.click(force=True);await asyncio.sleep(.2);assert not any(x['path']=='/employees/open' for x in requests[start:]);return {'newAria':a,'rowArias':rows,'openRequests':sum(x['path']=='/employees/open' for x in requests[start:])}
    links=await pause(p,'/employees/search',lambda:p.locator('#search-run').click(),link_wait);await expect(p.locator('#search-run')).to_be_enabled()
    props={'employeeInputsDisabledDuringWait':employee['allDisabled'],'careerInputsDisabledDuringWait':employee['allDisabled'],'codeInputsDisabledDuringWait':all(x['disabled'] for x in code_during.values()),'busyInputEditsAccepted':not employee['rawRetained'],'preRequestRawPreserved':employee['rawRetained'],'previousDisabledAndReadonlyRestored':restore_flags and code_restore,'savedDbEqualsCapturedValues':employee_db==captured and code_db==name,'newLinkAriaDisabledWhileBusy':links['newAria']=='true','rowEditLinksAriaDisabledWhileBusy':all(x=='true' for x in links['rowArias'])}
    return {'adopt':{'DUI09.busy-input':props},'employeeBefore':before,'employeeDuring':employee,'employeeRestored':restored,'codeBefore':code_before,'codeDuring':code_during,'codeRestored':code_after,'employeeSavedDb':employee_db,'codeSavedDb':code_db,'links':links,'scope':'Actual outbound request barriers, keyboard late typing, rejection/success readback, original disabled/readonly restoration including code classification, real forced pointer attempts on aria-disabled links with counted Open0.'}
async def main():
    start=rt.artifact();assert start['sha256']==h.EXPECTED_ARTIFACT;hashes=[h.proof(p) for p in SOURCES];runner=rt.sha(ROOT/'.tmp/bin/RuntimeObserver/Release/net10.0/RuntimeObserver.dll');h.observer=rt.Observer()
    try:
        async with async_playwright() as pw:
            browser=await pw.chromium.launch();await h.case(browser,'busy-all-controls',busy,'admin');await browser.close()
    finally:stop=h.observer.stop()
    assert start==rt.artifact() and hashes==[h.proof(p) for p in SOURCES] and runner==rt.sha(ROOT/'.tmp/bin/RuntimeObserver/Release/net10.0/RuntimeObserver.dll')
    record={'runId':'sp2-ui-regenerate-20261029','artifact':start,'contractSha256':rt.sha(ROOT/'tests/ui-contract.json'),'inputManifestSha256':rt.sha(ROOT/'build/generation/inputs.json'),'measurementSources':hashes,'observerRuntime':{'sha256':runner,'ownership':h.observer.ownership,'stop':stop},'results':h.results,'observations':list(h.observations.values()),'pageErrors':h.errors,'formalScore':None};(OUT/'busy.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'pass':sum(x['status']=='PASS' for x in h.results),'fail':sum(x['status']=='FAIL' for x in h.results),'errors':h.errors}));return int(any(x['status']=='FAIL' for x in h.results) or bool(h.errors))
if __name__=='__main__':sys.exit(asyncio.run(main()))
