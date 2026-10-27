const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const method=path.resolve(__dirname,'..');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE??path.join(method,'.tmp/browser/node_modules/playwright-core'));
const base=process.env.TARGET_URL??'http://127.0.0.1:5091';
const iteration=Number(process.env.TRAINING_ITERATION??'1');
const result={schema:'access-web-browser-tests/0.2',iteration,provider:process.env.TEST_PROVIDER??'VerificationMemory',sourceHash:JSON.parse(fs.readFileSync(path.join(method,'build/generation/inputs.json'),'utf8')).source.sha256,checks:[],failures:[],consoleErrors:[]};
let browser;
async function step(name,action){try{await action();result.checks.push({name,status:'PASS'});}catch(error){result.checks.push({name,status:'FAIL',message:error.message});throw error;}}
(async()=>{
 const local=process.env.LOCALAPPDATA;let exe=process.env.CHROMIUM_EXECUTABLE;
 if(!exe&&local){const cache=path.join(local,'ms-playwright');if(fs.existsSync(cache))for(const name of fs.readdirSync(cache).filter(n=>/^chromium-\d+$/.test(n)).sort().reverse()){const p=path.join(cache,name,'chrome-win64/chrome.exe');if(fs.existsSync(p)){exe=p;break;}}}
 browser=await chromium.launch({headless:true,...(exe?{executablePath:exe}:{})});
 const page=await browser.newPage({viewport:{width:1280,height:900}});page.on('pageerror',e=>result.consoleErrors.push(e.message));page.on('dialog',d=>d.accept());
 await step('search screen and real keyboard query',async()=>{await page.goto(base);await page.getByRole('heading',{name:'学生検索',exact:true}).waitFor();await page.locator('#StudentNo').fill('TRN');await page.getByRole('button',{name:'検索',exact:true}).click();assert.match(await page.locator('#result-count').innerText(),/[2-9]件/);assert.equal(await page.locator('tbody tr').filter({hasText:'検証太郎'}).count(),1);await page.screenshot({path:path.join(method,'.tmp/search.png'),fullPage:true});});
 const key=process.env.BROWSER_KEY??`WEB${iteration}${require('node:crypto').randomBytes(3).toString('hex').toUpperCase()}`; result.testStudentNo=key;
 await step('new student actual form input and save',async()=>{
  await page.getByRole('link',{name:'新規登録',exact:true}).click();
  await Promise.all([page.waitForNavigation(),page.locator('#Input_GradeCode').selectOption('01')]);
  await Promise.all([page.waitForNavigation(),page.locator('#Input_ClassId').selectOption('1')]);
  const values={StudentNo:key,StudentName:'画面確認',StudentNameKana:'ガメンカクニン',BirthYear:'12',BirthMonth:'6',BirthDay:'3',PostalCode:'001-0001',AddressLine1:'架空住所三丁目',PhoneNumber:'0311112222',AdmissionDate:'2026-04-01',Remarks:'架空のブラウザー検証データ'};
  await page.locator('#Input_BirthEra').selectOption('HEISEI');await page.locator('#Input_GenderCode').selectOption('0');await page.locator('#Input_PrefectureCode').selectOption('13');
  for(const [name,value]of Object.entries(values))await page.locator(`#Input_${name}`).fill(value);
  await page.screenshot({path:path.join(method,'.tmp/editor.png'),fullPage:true});
  await page.getByRole('button',{name:'保存',exact:true}).click();
  if(await page.getByRole('heading',{name:'重複候補の確認',exact:true}).count()){result.duplicateConfirmationExercised=true;await page.locator('#reason').fill('架空の別人として確認したブラウザー試験');await page.getByRole('button',{name:'確認して保存',exact:true}).click();}
  assert.match(await page.locator('body').innerText(),/登録しました|登録しました。|学生を登録/);
 });
 await step('saved search, leading zero and key protection',async()=>{await page.goto(`${base}/Students?Searched=true&StudentNo=${key}&Statuses=01&SortKey=studentNo&SortDirection=asc`);const row=page.locator('tbody tr').filter({hasText:key});await row.getByRole('link',{name:'編集',exact:true}).click();assert.equal(await page.locator('#Input_StudentNo').getAttribute('readonly'),'readonly');assert.match(await page.locator('#Input_PostalCode').inputValue(),/^001-?0001$/);});
 await step('edit cancel preserves stored value',async()=>{await page.locator('#Input_PhoneNumber').fill('0399999999');await page.getByRole('button',{name:'最新再読込',exact:true}).click();assert.equal(await page.locator('#Input_PhoneNumber').inputValue(),'0311112222');});
 await step('edit persists and version increases',async()=>{const version=Number(await page.locator('#Input_ExpectedVersion').inputValue());await page.locator('#Input_PhoneNumber').fill('0355556666');await page.getByRole('button',{name:'保存',exact:true}).click();if(await page.getByRole('heading',{name:'重複候補の確認',exact:true}).count()){result.duplicateConfirmationExercised=true;await page.locator('#reason').fill('架空の別人として確認した編集試験');await page.getByRole('button',{name:'確認して保存',exact:true}).click();}await page.goto(`${base}/Students?Searched=true&StudentNo=${key}&Statuses=01`);await page.locator('tbody tr').filter({hasText:key}).getByRole('link',{name:'編集',exact:true}).click();assert.equal(await page.locator('#Input_PhoneNumber').inputValue(),'0355556666');assert.equal(Number(await page.locator('#Input_ExpectedVersion').inputValue()),version+1);});
 await step('delete confirmation cancel and delete',async()=>{await page.getByRole('link',{name:'論理削除',exact:true}).click();await page.getByRole('button',{name:'戻る',exact:true}).click();assert.equal(await page.locator('#Input_StudentNo').inputValue(),key);await page.getByRole('link',{name:'論理削除',exact:true}).click();await page.locator('#reason').fill('架空の試験データを論理削除');await page.getByRole('button',{name:'確認して論理削除',exact:true}).click();await page.goto(`${base}/Students?Searched=true&StudentNo=${key}&Statuses=01`);assert.equal(await page.locator('#result-count').innerText(),'0件');});
 await step('forged POST without antiforgery is rejected',async()=>{const response=await page.request.post(`${base}/Students/Save`,{form:{'Input.StudentNo':'FORGED'}});assert.equal(response.status(),400);});
 await step('no horizontal overflow at 1280px',async()=>{await page.goto(base);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true);});
 if(result.consoleErrors.length)throw Error(result.consoleErrors.join(';'));
})().catch(error=>{result.failures.push(error.stack??error.message);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();result.status=result.failures.length?'FAIL':'PASS';const report=process.env.BROWSER_REPORT??path.join(method,'build/test-results/browser.json');fs.mkdirSync(path.dirname(report),{recursive:true});fs.writeFileSync(report,JSON.stringify(result,null,2)+'\n');process.stdout.write(JSON.stringify({status:result.status,checks:result.checks,failures:result.failures},null,2)+'\n');});

