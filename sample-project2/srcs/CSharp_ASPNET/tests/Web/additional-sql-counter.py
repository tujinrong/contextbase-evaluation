from pathlib import Path
import asyncio,json,sys,importlib.util
from playwright.async_api import async_playwright,expect
import additional_runtime as rt
s=importlib.util.spec_from_file_location('cases',Path(__file__).with_name('additional-ui-cases.py'));h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
ROOT=rt.ROOT;OUT=h.OUT;SOURCES=[Path(__file__),Path(__file__).with_name('additional-ui-cases.py'),Path(__file__).with_name('additional_runtime.py'),ROOT/'tests/RuntimeObserver/Program.cs']
async def new_save(p,c,requests,dialogs):
    await h.search_page(p);zero=h.observer.sql_counters();await h.search(p);positive=h.observer.sql_counters();assert positive['listenerCount']>0 and positive['searchBefore']-zero['searchBefore']==positive['searchAfter']-zero['searchAfter']==1 and positive['callbackFailures']==0
    await h.clear(p);await p.locator('#f03-i01').fill('000002');await p.locator('#f03-i02').fill(' 未適用の値 ');await p.locator('#f03-i03').select_option('02');await p.locator('#f03-i04').select_option('');before_raw=await h.raw(p);origin=await h.vm(p);assert origin['resultStatus']=='Unapplied';await h.go(p,'#employee-new',r'/employees/new(?:\?|$)')
    occupied={x['employee_no'] for x in rt.rows("SELECT employee_no FROM dbo.m_employee")};number=next(str(i) for i in range(900010,900100) if str(i) not in occupied)
    for id,value in [('f04-i01',number),('f04-i02','カウンタ確認 社員'),('f04-i03','カウンタ カクニン'),('f04-i06','2020-01-01')]:await p.locator('#'+id).fill(value)
    await p.locator('#f04-i04').select_option('01');before=h.observer.sql_counters();at=len(requests);await h.go(p,'#employee-save',r'/employees(?:\?|$)');after=h.observer.sql_counters();count=after['searchBefore']-before['searchBefore'];assert before['listenerCount']==after['listenerCount']>0 and before['callbackFailures']==after['callbackFailures']==0 and count==0 and after['commandCallbacks']>before['commandCallbacks']
    saved=rt.rows("SELECT * FROM dbo.m_employee WHERE employee_no='"+number+"'");v=await h.vm(p);props={'dbSavedEmployee':len(saved)==1 and saved[0]['employee_name']=='カウンタ確認 社員','rawFourValuesPreserved':before_raw==await h.raw(p),'originStatusPreserved':v['resultStatus']==origin['resultStatus'],'automaticSearchRequests':count,'savedNoticeVisible':'保存しました' in await p.locator('#message').inner_text()};assert all(value for key,value in props.items() if key!='automaticSearchRequests')
    return {'adopt':{'DUI05.new-save-return':props},'positiveBefore':zero,'positiveAfter':positive,'beforeSaveCounters':before,'afterSaveCounters':after,'httpSearchCount':sum(x['path']=='/employees/search' for x in requests[at:]),'savedEmployeeNo':number,'rawBefore':before_raw,'rawAfter':await h.raw(p),'scope':'Unchanged final publish SqlClient DiagnosticListener CommandBefore/After filtered to the new exact database+SQL-SEARCH fingerprint, positive explicit-search1 control and listener/callback health, followed by actual NewSave return0. No provider/server settings or clock changed.'}
async def main():
    start=rt.artifact();assert start['sha256']==h.EXPECTED_ARTIFACT;hashes=[h.proof(p) for p in SOURCES];runner=rt.sha(ROOT/'.tmp/bin/RuntimeObserver/Release/net10.0/RuntimeObserver.dll');h.observer=rt.Observer()
    try:
        async with async_playwright() as pw:
            b=await pw.chromium.launch();await h.case(b,'new-save-diagnostic-counter',new_save);await b.close()
    finally:stop=h.observer.stop()
    assert start==rt.artifact() and hashes==[h.proof(p) for p in SOURCES] and runner==rt.sha(ROOT/'.tmp/bin/RuntimeObserver/Release/net10.0/RuntimeObserver.dll')
    record={'runId':'sp2-ui-regenerate-20261029','artifact':start,'contractSha256':rt.sha(ROOT/'tests/ui-contract.json'),'inputManifestSha256':rt.sha(ROOT/'build/generation/inputs.json'),'measurementSources':hashes,'observerRuntime':{'sha256':runner,'ownership':h.observer.ownership,'stop':stop},'results':h.results,'observations':list(h.observations.values()),'pageErrors':h.errors,'technicalSources':['https://learn.microsoft.com/en-us/dotnet/api/microsoft.data.sqlclient.diagnostics?view=sqlclient-dotnet-core-6.1'],'formalScore':None};(OUT/'sql-diagnostic.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'pass':sum(x['status']=='PASS' for x in h.results),'fail':sum(x['status']=='FAIL' for x in h.results)}));return int(any(x['status']=='FAIL' for x in h.results))
if __name__=='__main__':sys.exit(asyncio.run(main()))
