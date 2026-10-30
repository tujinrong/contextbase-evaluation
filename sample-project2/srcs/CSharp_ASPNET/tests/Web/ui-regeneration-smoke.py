from pathlib import Path
import asyncio,json,hashlib,datetime,re,sys,subprocess
from playwright.async_api import async_playwright,expect

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.tmp/build-agent/browser-smoke';OUT.mkdir(parents=True,exist_ok=True)
runtime=json.loads((ROOT/'.tmp/ui-regenerate-runtime/profile.json').read_text(encoding='utf-8-sig'))
assert runtime['database']=='SP2_WebFixture_UI_R20261029' and runtime['url']=='https://localhost:5182'
results=[];errors=[];requests=[];observed={}
def artifact():
    return subprocess.check_output(['node','--input-type=module','-e',"import {hashArtifact} from './agents/builds/build-agent/scripts/ui-conformance.mjs';console.log(hashArtifact('sample-project2/srcs/CSharp_ASPNET/build/publish').sha256);"],cwd=ROOT.parents[2],text=True).strip()
async def ready(page):
    await page.wait_for_selector('.sp2-ui[data-ready="true"]',timeout=15000)
    assert await page.locator('.sp2-ui').evaluate('(e)=>!e.inert&&!e.hasAttribute("data-pending-init")')
async def type_text(page,selector,value):
    await page.locator(selector).click();await page.keyboard.press('Control+A');await page.keyboard.press('Backspace');await page.keyboard.type(value)
async def login(page,user):
    await page.goto(runtime['url']+'/account/login');await type_text(page,'[data-item-id="F01-I01"]',user);await type_text(page,'[data-item-id="F01-I02"]','123')
    await page.locator('[data-item-id="F01-I04"]').click();await page.wait_for_url('**/menu');await ready(page)
async def go(page,selector,url):
    await page.locator(selector).click();await page.wait_for_url(re.compile(url));await ready(page)
async def shot(page,name):
    file=OUT/(name+'.png');await page.screenshot(path=str(file),full_page=True);return {'file':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
async def check(id,fn):
    try:
        detail=await fn();results.append({'id':id,'status':'PASS','detail':detail});print('PASS',id,flush=True)
    except Exception as e:
        results.append({'id':id,'status':'FAIL','error':str(e)});print('FAIL',id,str(e),flush=True)
async def main():
    frozen_artifact=artifact()
    async with async_playwright() as p:
        browser=await p.chromium.launch(ignore_default_args=['--disable-back-forward-cache'])
        ctx=await browser.new_context(ignore_https_errors=True,viewport={'width':1366,'height':768})
        page=await ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append({'method':r.method,'url':r.url.split('?')[0]}))
        await login(page,'staff')
        await go(page,'a[href="/employees"]',r'/employees(?:\?|$)')
        async def ph05():
            await type_text(page,'#f03-i01','000002');await type_text(page,'#f03-i02',' 佐藤 ')
            await page.locator('#f03-i03').select_option('02');await page.locator('#f03-i04').select_option('02')
            before=[await page.locator('#f03-i0'+str(i)).input_value() for i in range(1,5)]
            start=len(requests);await go(page,'#employee-new',r'/employees/new(?:\?|$)')
            await go(page,'#employee-cancel',r'/employees(?:\?|$)')
            after=[await page.locator('#f03-i0'+str(i)).input_value() for i in range(1,5)]
            assert before==after,(before,after)
            count=sum(r['url'].endswith('/employees/search') for r in requests[start:]);assert count==0,count
            saves=sum(r['url'].endswith('/employees/save') for r in requests[start:]);status=await page.locator('[data-initial]').evaluate('(e)=>JSON.parse(e.dataset.initial).resultStatus');assert saves==0 and status=='Unapplied'
            observed['DUI05.ph05-untouched']={'rawEmployeeNoPreserved':before[0]==after[0],'rawNamePreserved':before[1]==after[1],'rawDepartmentPreserved':before[2]==after[2],'rawEmploymentPreserved':before[3]==after[3],'statusPreserved':status=='Unapplied','automaticSearchRequests':count,'saveRequests':saves,'confirmationDialogs':0}
            return {'before':before,'after':after,'searchRequests':count,'image':await shot(page,'F03-ph05')}
        await check('PH05-UNTOUCHED',ph05)
        async def reload_raw():
            before=[await page.locator('#f03-i0'+str(i)).input_value() for i in range(1,5)]
            old=await page.locator('[data-initial]').evaluate('(e)=>JSON.parse(e.dataset.initial).ui.stateId');await page.reload();await ready(page)
            after=[await page.locator('#f03-i0'+str(i)).input_value() for i in range(1,5)]
            new=await page.locator('[data-initial]').evaluate('(e)=>JSON.parse(e.dataset.initial).ui.stateId')
            assert before==after and old!=new,(before,after,old==new)
            return {'rawPreserved':True,'newState':old!=new}
        await check('HISTORY-RELOAD-UNAPPLIED',reload_raw)
        async def row_edit():
            await page.locator('#search-clear').click();await expect(page.locator('#f03-i01')).to_have_value('')
            await page.locator('#search-run').click();await page.wait_for_selector('[data-item-id="F03-I11"]')
            assert await page.locator('#search-rows input:checked').count()==0
            await shot(page,'F03-normal');await go(page,'[data-item-id="F03-I11"] >> nth=0',r'/employees/[0-9]+/edit(?:\?|$)')
            assert '000001' in await page.locator('[data-ui="employee-identity"]').inner_text()
            basic=await shot(page,'F04-basic');await page.locator('#careers-tab').click();await page.wait_for_selector('#careers-pane:not([hidden])')
            await page.locator('#career-rows button').first.click();await expect(page.locator('#f04-i14')).to_be_enabled()
            career=await shot(page,'F04-career');assert '000001' in await page.locator('[data-ui="employee-identity"]').inner_text()
            return {'basic':basic,'career':career,'target':'000001'}
        await check('ROW-EDIT-NO-RADIO',row_edit)
        async def staff_forbidden():
            r=await page.goto(runtime['url']+'/codes');assert r.status==403,r.status;await ready(page)
            assert await page.locator('[data-ui="error-message"]').is_visible()
            assert '権限' in await page.locator('[data-ui="error-message"]').inner_text()
            assert await page.locator('#code-new').count()==0
            await go(page,'[data-ui-error] a[href="/employees"]',r'/employees(?:\?|$)')
            return {'status':403,'japaneseShell':True,'nextAction':True}
        await check('GET-FORBIDDEN-SHELL',staff_forbidden)
        await ctx.close()
        admin=await browser.new_context(ignore_https_errors=True,viewport={'width':1366,'height':768});ap=await admin.new_page();ap.on('pageerror',lambda e:errors.append(str(e)));await login(ap,'admin');await go(ap,'a[href="/codes"]',r'/codes(?:\?|$)')
        async def code_view():
            await ap.locator('#code-rows button').first.click();await expect(ap.locator('#f06-i04')).to_be_enabled()
            image=await shot(ap,'F06-normal');await ap.set_viewport_size({'width':390,'height':768});narrow=await shot(ap,'F06-narrow')
            return {'normal':image,'narrow':narrow}
        await check('CODE-MASTER',code_view)
        await admin.close();await browser.close()
    assert frozen_artifact==artifact()
    result={'runId':'sp2-ui-regenerate-20261029','scope':'Author browser smoke; not full UI gate','recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'artifactSha256':frozen_artifact,'testSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'results':results,'observed':observed,'pageErrors':errors,'requestCount':len(requests),'formalScore':None}
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'passed':sum(r['status']=='PASS' for r in results),'failed':sum(r['status']=='FAIL' for r in results),'pageErrors':errors},ensure_ascii=True))
    return int(any(r['status']=='FAIL' for r in results) or bool(errors))
if __name__=='__main__':sys.exit(asyncio.run(main()))
