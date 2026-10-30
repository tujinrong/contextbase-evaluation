"""Actual protected HTTP rejection boundaries on the author's new owned fixture."""
from pathlib import Path
import asyncio,json,hashlib,datetime,importlib.util
from playwright.async_api import async_playwright
import fixture_sql as db
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('h',Path(__file__).with_name('ui-regeneration-history.py'));h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
async def main():
    artifact=h.func.artifact();before=(db.employee(),db.careers());results=[]
    async with async_playwright() as pw:
        browser=await pw.chromium.launch();context=await browser.new_context(ignore_https_errors=True);p=await context.new_page();await h.h.login(p,'staff');await h.prepare(p);u=(await h.model(p))['ui']
        body={'stateId':u['stateId'],'stateRevision':u['stateRevision'],'tabId':u['tabId'],'documentLease':u['documentLease'],'clientSequence':0,'raw':await h.raw(p)}
        async def send(body,csrf):
            return await p.evaluate('''async ({body,csrf})=>{const headers={'Content-Type':'application/json','X-SP2-User-Action':'true'};if(csrf!==null)headers['X-SP2-CSRF']=csrf;const r=await fetch('/employees/search',{method:'POST',redirect:'error',credentials:'same-origin',headers,body});const t=await r.text();return{status:r.status,contentType:r.headers.get('Content-Type'),body:t?JSON.parse(t):null};}''',{'body':body,'csrf':csrf})
        for name,token in [('missing-csrf',None),('invalid-csrf','invalid-token')]:
            r=await send(json.dumps(body),token);assert r['status']==400,(name,r['status']);results.append({'id':name,'status':'PASS','httpStatus':r['status']})
        token=await p.locator('input[name="__RequestVerificationToken"]').input_value()
        exponent=json.dumps(body).replace('"stateRevision": '+str(u['stateRevision']),'"stateRevision": '+str(u['stateRevision'])+'e0')
        r=await send(exponent,token);assert r['status']==400;results.append({'id':'exponent-revision-rejected','status':'PASS','httpStatus':r['status'],'messageId':r['body']['outcome']['messageId'],'scope':'Transport rejection400/data unchanged; full technical error-message classification is not asserted.'})
        await context.close();await browser.close()
    assert before==(db.employee(),db.careers());assert artifact==h.func.artifact()
    target=ROOT/'build/test-results/ui-regeneration/security.json';target.write_text(json.dumps({'runId':'sp2-ui-regenerate-20261029','recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'artifactSha256':artifact,'status':'PASS_AT_HTTP_REJECTION_SCOPE','results':results,'database':db.DATABASE,'employeeAndCareersUnchanged':True,'testSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'formalScore':None},ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('PASS security HTTP rejection checks3; employee/careers unchanged')
if __name__=='__main__':asyncio.run(main())
