'use strict';
// Preserve evidence of a missing HTTP raw-state contract; do not invent an API in the product.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {chromium}=require(process.env.SP2_PLAYWRIGHT_MODULE||'playwright-core');
const root=path.resolve(__dirname,'../..'),profile=JSON.parse(fs.readFileSync(path.join(root,'.tmp/runtime/profile.json'),'utf8'));
if(profile.url!=='https://localhost:7443'||!/^SP2_WebFixture_/.test(profile.database))throw new Error('Owned local fixture required');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 let actual,record;
 try{
  const context=await browser.newContext({ignoreHTTPSErrors:true,viewport:{width:1366,height:768}}),page=await context.newPage();
  await page.goto(profile.url+'/account/login');await page.locator('#sp2-login-id').fill('demoadmin');await page.locator('#sp2-login-pw').fill(profile.adminPassword);
  await Promise.all([page.waitForURL('**/menu'),page.locator('button[type=submit]').filter({hasText:'ログイン'}).click()]);
  await page.goto(profile.url+'/employees');await page.locator('#search-no').fill('777777');
  await Promise.all([page.waitForURL('**/employees/edit?state=*'),page.locator('#employee-new').click()]);
  await Promise.all([page.waitForURL('**/employees?state=*'),page.locator('#employee-cancel').click()]);
  actual=await page.locator('#search-no').inputValue();
  record={runId:'20261029-sp2-build',recordedAt:new Date().toISOString(),reviewer:'/root',id:'PH-05',status:actual==='777777'?'PASS':'REQUIRES_DETAIL_DESIGN_FIX',expectedRaw:'777777',actualRaw:actual,scenario:'Unsearched conditions edited -> New -> Cancel without employee edits',databaseWrites:0,criteria:'F03 return retains conditions; F04 unsearched origin returns unsearched',contractGap:'StateCommand and OpenInput do not carry unapplied raw search conditions. Save return using AppliedCriteria is separately specified and is not this defect.',implementationSha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'src/CareerManagement.Web/Controllers/EmployeesController.cs'))).digest('hex'),formalScore:null};
 }finally{await browser.close();}
 const out=path.join(root,'build/test-results/design-boundary.json');fs.writeFileSync(out,JSON.stringify(record,null,2)+'\n');
 console.log(JSON.stringify({id:record.id,status:record.status,actualRaw:actual,databaseWrites:0}));process.exitCode=record.status==='PASS'?0:2;
})().catch(e=>{console.error(e.name);process.exitCode=1;});
