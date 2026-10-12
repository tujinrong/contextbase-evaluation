// Real Vue/Edge workflow with isolated API responses. No business DB is opened.
import {chromium,expect} from '@playwright/test';
import {createServer} from 'vite';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const frontend=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const runId=process.argv[2];if(!/^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$/.test(runId??''))throw new Error('Pass unique run ID.');
const report=path.resolve(process.argv[3]??path.join(frontend,'test-report'));fs.mkdirSync(report,{recursive:true});
const prefix=path.join(report,runId+'-vue-browser');
for(const suffix of ['.json','.raw.log','.png'])if(fs.existsSync(prefix+suffix))throw new Error('Report exists.');
const checks=[],requests=[],errors=[];let failure=null;
const server=await createServer({root:frontend,server:{host:'127.0.0.1',port:0,strictPort:true,watch:{ignored:['**/build/**']}},logLevel:'error'});await server.listen();
const address=server.httpServer.address();
const browser=await chromium.launchPersistentContext(path.join(frontend,'build/browser-profile',runId),{channel:'msedge',headless:true,viewport:{width:1440,height:1100},artifactsDir:path.join(frontend,'build/browser-artifacts',runId)});
const page=await browser.newPage();page.on('pageerror',e=>errors.push(String(e)));
const check=(ok,name)=>{if(!ok)throw new Error('FAILED: '+name);checks.push(name);};
const assert=async(name,operation)=>{await operation();checks.push(name);};
const context='a'.repeat(64);let revision=1,lastCriteria=null;const permissions={read:true,create:true,update:true,delete:false,maintain:false};
const lookups={years:[2026],codes:[['GENDER','0','未回答'],['PREFECTURE','13','東京都'],['GRADE','00','学年なし'],['ENROLLMENT_STATUS','01','在学'],['ENROLLMENT_STATUS','02','休学'],['ENROLLMENT_STATUS','03','卒業'],['RELATIONSHIP','01','父']].map(([categoryId,value,name])=>({categoryId,value,name,selectable:true})),classes:[{classId:'9007199254740993',schoolYear:2026,gradeCode:'00',gradeName:'学年なし',classCode:'C-A',className:'Aクラス',selectable:true,note:'',occupancy:0,capacity:30}]};
const initial={studentNo:'',name:'',kana:'',schoolYear:null,gradeCode:null,classId:null,unassignedOnly:false,statusCodes:['01','02'],prefectureCode:null,phoneNumber:'',admissionFrom:null,admissionTo:null};
const row={studentId:'9007199254740993',studentNo:'S2026-0001',studentName:'見本 太郎',studentNameKana:'ミホン タロウ',birthDateWareki:'平成20年05月15日',schoolYear:2026,gradeName:'学年なし',classCode:'C-A',className:'Aクラス',enrollmentName:'在学',addressDisplay:'東京都試験町',phoneNumber:null,updatedAt:'2026/10/12 10:00:00'};
const draft={studentNo:'',studentName:'',studentNameKana:'',birthDateInput:{era:'',year:'',month:'',day:''},genderCode:'0',postalCode:'',prefectureCode:'',addressLine1:'',addressLine2:null,phoneNumber:null,emailAddress:null,admissionDate:'',enrollmentStatusCode:'01',enrollmentEndDate:null,classId:null,emergencyContactName:null,relationshipCode:null,emergencyPhoneNumber:null,remarks:null,schoolYear:null,gradeCode:null,expectedVersion:null,duplicateToken:null,operationReason:null,returnContextId:context};
const result=(criteria,unsearched=false)=>({outcome:unsearched?'unsearched':'found',totalCount:unsearched?null:1,items:unsearched?[]:[row],page:1,pageSize:20,sortKey:'studentNo',sortDirection:'asc',searchedAt:unsearched?null:'2026/10/12 10:00:00',contextId:context,contextRevision:String(++revision),criteria});
await page.route('**/api/students**',async route=>{
 const request=route.request(),url=new URL(request.url()),body=request.method()==='GET'?null:request.postDataJSON();requests.push({path:url.pathname,method:request.method(),body,csrf:request.headers()['requestverificationtoken'],tab:request.headers()['x-tab-id']});
 let data,status=200;
 if(url.pathname.endsWith('/bootstrap'))data={...lookups,csrfToken:'test-csrf',user:'browser-test',permissions,businessDate:'2026-10-12',schoolYear:2026,contextId:context,contextRevision:String(revision)};
 else if(url.pathname.endsWith('/options'))data=lookups;
 else if(url.pathname.endsWith('/search')){lastCriteria=structuredClone(body.criteria);data=result(lastCriteria);}
 else if(url.pathname.endsWith('/page')){data={...result(lastCriteria),pageSize:body.pageSize};}
 else if(url.pathname.endsWith('/clear')){lastCriteria=structuredClone(initial);data=result(lastCriteria,true);}
 else if(url.pathname.endsWith('/resume'))data=result(lastCriteria,true);
 else if(url.pathname.endsWith('/new'))data={...lookups,studentId:null,form:structuredClone(draft),updatedAt:null,updatedBy:null,permissions};
 else if(url.pathname==='/api/students'&&request.method()==='POST'){
  if(body.birthDateInput.day==='31'){status=422;data={outcome:'validationFailed',messageId:'E-STU-005',message:'日付が正しくありません。',fieldErrors:{'REG-005':['日付が正しくありません。']},correlationId:'browser-fixture',retryBySearch:false};}
  else data={outcome:'saved',studentId:'9007199254740993',rowVersion:'1',message:'保存しました。'};
 }else{status=404;data={outcome:'notFound',message:'Test route absent',fieldErrors:{}};}
 await route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
});
try{
 await page.goto(`http://127.0.0.1:${address.port}`);
 await assert('search page initializes',()=>expect(page.getByRole('heading',{name:'学生検索'})).toBeVisible());
 await assert('new registration enabled after bootstrap',()=>expect(page.getByRole('button',{name:'新規登録'})).toBeEnabled());
 await page.getByRole('button',{name:'検索',exact:true}).click();await assert('list renders wareki',()=>expect(page.getByRole('cell',{name:'平成20年05月15日'})).toBeVisible());
 check(requests.find(r=>r.path.endsWith('/search')).body.contextRevision==='1','first received revision is sent');
 await page.locator('#SRC-002').fill('変更');await assert('draft change warning shown',()=>expect(page.getByText('条件を変更しました。',{exact:false})).toBeVisible());
 await assert('applied results remain while editing criteria',()=>expect(page.getByRole('cell',{name:'見本 太郎',exact:true})).toBeVisible());
 await page.getByLabel('表示件数').selectOption('50');await assert('page size update finishes',()=>expect(page.getByLabel('表示件数')).toHaveValue('50'));
 await expect.poll(()=>requests.filter(r=>r.path.endsWith('/page')).length).toBe(1);const paged=requests.find(r=>r.path.endsWith('/page'));check(paged.body.contextRevision==='2'&&!('criteria' in paged.body),'paging uses received revision and applied server criteria');
 await page.getByLabel('在学',{exact:true}).uncheck();await page.getByLabel('休学',{exact:true}).uncheck();await page.getByRole('button',{name:'検索',exact:true}).click();await expect.poll(()=>requests.filter(r=>r.path.endsWith('/search')).length).toBe(2);check(requests.filter(r=>r.path.endsWith('/search'))[1].body.criteria.statusCodes.length===0,'all-off statuses serialized as empty array');
 await page.locator('#SRC-004').selectOption('2026');await page.locator('#SRC-005').selectOption('00');await page.locator('#SRC-006').selectOption('9007199254740993');await page.locator('#SRC-007').check();
 await assert('unassigned clears year',()=>expect(page.locator('#SRC-004')).toHaveValue('すべて'));await assert('unassigned disables class',()=>expect(page.locator('#SRC-006')).toBeDisabled());
 await page.getByRole('button',{name:'検索',exact:true}).click();await expect.poll(()=>requests.filter(r=>r.path.endsWith('/search')).length).toBe(3);const unassigned=requests.filter(r=>r.path.endsWith('/search'))[2].body.criteria;check(unassigned.unassignedOnly&&unassigned.schoolYear===null&&unassigned.gradeCode===null&&unassigned.classId===null,'unassigned sends null hierarchy without precision conversion');
 await page.getByRole('button',{name:'クリア',exact:true}).click();await assert('clear resets raw name',()=>expect(page.locator('#SRC-002')).toHaveValue(''));
 await page.getByRole('button',{name:'新規登録'}).click();await assert('registration renders all fields',()=>expect(page.locator('#REG-024')).toBeVisible());
 await page.locator('#REG-002').fill('T-0001');await page.locator('#REG-003').fill('試験 太郎');await page.locator('#REG-004').fill('シケン タロウ');await page.locator('#REG-007').fill('1000001');await page.locator('#REG-009').fill('試験町');await page.locator('#REG-011').fill('0312345678');await page.locator('#REG-008').selectOption('13');await page.locator('#REG-013').fill('2026-04-01');
 await page.getByLabel('元号',{exact:true}).selectOption('HEISEI');await page.getByLabel('元号年',{exact:true}).fill('20');await page.getByLabel('月',{exact:true}).fill('02');await page.getByLabel('日',{exact:true}).fill('31');
 await page.getByRole('button',{name:'登録',exact:true}).click();await assert('server validation is displayed',()=>expect(page.locator('.message.error')).toContainText('日付が正しくありません。'));
 await assert('invalid day remains raw',()=>expect(page.getByLabel('日',{exact:true})).toHaveValue('31'));
 const firstSave=requests.find(r=>r.path==='/api/students'&&r.method==='POST');check(firstSave.body.birthDateInput.month==='02'&&firstSave.body.birthDateInput.day==='31'&&!('birthDate' in firstSave.body),'raw four-component birth input sent without normalized birthDate');check(!('relationshipCategory' in firstSave.body)&&!('updatedBy' in firstSave.body),'derived and management fields not accepted from UI');
 page.once('dialog',dialog=>dialog.dismiss());await page.getByRole('button',{name:'入力クリア',exact:true}).click();await assert('reset cancellation preserves draft',()=>expect(page.locator('#REG-003')).toHaveValue('試験 太郎'));
 await page.getByLabel('月',{exact:true}).fill('05');await page.getByLabel('日',{exact:true}).fill('15');await page.getByRole('button',{name:'登録',exact:true}).click();await assert('successful save returns to search',()=>expect(page.getByRole('heading',{name:'学生検索'})).toBeVisible());
 check(requests.filter(r=>r.path==='/api/students'&&r.method==='POST').length===2,'one explicit retry after correction');
 const postRequests=requests.filter(r=>r.method!=='GET');check(postRequests.every(r=>r.csrf==='test-csrf'&&/^[0-9a-f]{64}$/.test(r.tab)),'all API commands carry CSRF and tab identity');check(errors.length===0,'no browser JavaScript errors');
 await page.screenshot({path:prefix+'.png',fullPage:true});
}catch(e){failure=String(e.stack??e);process.exitCode=1;await page.screenshot({path:prefix+'.png',fullPage:true});}
finally{
 const browserVersion=browser.browser()?.version()??'Edge';await browser.close();await server.close();
 fs.writeFileSync(prefix+'.raw.log',checks.map(n=>'PASS '+n).join('\n')+'\n'+(failure??'PASS all browser workflow checks')+'\n',{flag:'wx'});
 fs.writeFileSync(prefix+'.json',JSON.stringify({runId,recordedAt:new Date().toISOString(),status:failure?'FAILED':'PASSED',browserVersion,checks:checks.length,assertions:checks,failure,scope:'real Vue UI and Edge; mocked API responses',notExecuted:['SQL Server integration','production authentication'],documentation:['https://playwright.dev/docs/api/class-browsertype','https://playwright.dev/docs/mock']},null,2)+'\n',{flag:'wx'});
 console.log(JSON.stringify({status:failure?'FAILED':'PASSED',checks:checks.length,report:prefix+'.json',failure}));
}
