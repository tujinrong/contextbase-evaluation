'use strict';
// Observe the final published site. Expectations are the previously authored
// tests/ui-contract.json; this executable never rewrites that contract.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.SP2_PLAYWRIGHT_MODULE||'playwright-core');
const root=path.resolve(__dirname,'../..'),repo=path.resolve(root,'../../..');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const runId=process.env.SP2_RUN_ID||'20261029-sp2-ui-conformance';
assert.match(runId,/^[A-Za-z0-9_-]+$/);
const profilePath=path.join(root,'.tmp/ui-runtime/profile.json'),profile=read(profilePath);
assert.match(profile.database,/^SP2_WebFixture_UI_[a-f0-9]{12}$/);assert.equal(profile.url,'https://localhost:7445');
const contractPath=path.join(root,'tests/ui-contract.json'),contract=read(contractPath),contractHash=sha(contractPath);
const inputPath=path.join(root,'build/generation/inputs.json'),inputHash=sha(inputPath);
assert.equal(read(inputPath).runId,runId,'Current frozen inputs are required.');
const validatorPath=path.join(repo,'agents/builds/build-agent/scripts/ui-conformance.mjs'),validatorHash=sha(validatorPath);
const out=path.join(root,'build/test-results/ui'),recordPath=path.join(root,'build/test-results/ui-observations.json');
fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(recordPath,JSON.stringify({schemaVersion:1,projectId:'sample-project2',profileId:'CSharp_ASPNET',runId,status:'RUNNING',formalScore:null})+'\n');
const states=new Map(contract.states.map(s=>[s.id,s])),snapshots=new Map(),failures=[],operations=[],errors=[];
const redact=s=>String(s).replaceAll(profile.adminPassword,'[redacted]').replaceAll(profile.staffPassword,'[redacted]').replaceAll(profile.certificatePassword,'[redacted]');
const inventorySource=()=>['tests/Web/ui-observations.cjs','tests/ui-contract.json','tools/Start-Fixture.ps1'].map(file=>({file,sha256:sha(path.join(root,file))}));
const sourceBefore=inventorySource();
const measurementBefore=sourceBefore.filter(s=>s.file!=='tests/ui-contract.json');
let browser,context,page,artifactBefore,artifactAfter,renderer,fatal;
const startedAt=new Date().toISOString();
const collectorProbes=[];
async function apiClick(selector,route){
  const wait=page.waitForResponse(r=>new URL(r.url()).pathname===route&&r.request().method()==='POST');
  await page.locator(selector).click();const response=await wait;
  await page.waitForTimeout(50);return response;
}
async function navigate(url){await page.goto(profile.url+url);await page.waitForLoadState('domcontentloaded');await page.waitForTimeout(75);}
async function measure(state){
 return await page.evaluate(({id,scope,panel})=>{
  const root=document.querySelector(scope);if(!root)throw Error('Missing state surface '+id);
  const visible=node=>node.getClientRects().length>0&&getComputedStyle(node).display!=='none'&&getComputedStyle(node).visibility!=='hidden'&&!node.closest('[hidden]');
  // Keep known semantic nodes, and independently discover new text-owning or
  // focusable elements. New tags become unknown inventory instead of disappearing.
  const candidate=n=>!n.matches('script,style,noscript,template,input[type=hidden]')&&(n.matches('h1,p,label,input,select,textarea,button,a,th,td,legend,span,[role=status],[tabindex],[contenteditable=true],[role=button],[role=link],[role=checkbox],[role=radio],[role=combobox],[role=listbox],[role=menuitem]')||Array.from(n.childNodes).some(c=>c.nodeType===Node.TEXT_NODE&&c.textContent.trim()));
  const nodes=Array.from(root.querySelectorAll('*')).filter(n=>visible(n)&&candidate(n));
  const counts={},components=[],values={};let clippedTextCount=0;
  const keyOf=new Map();
  if(Array.from(root.childNodes).some(n=>n.nodeType===Node.TEXT_NODE&&n.textContent.trim())){
   const k=id+'/surface-direct-text',style=getComputedStyle(root);components.push({id:k,kind:'text',textCapable:true});values[k]={fontFamily:style.fontFamily.split(',')[0].trim().replace(/^['"]|['"]$/g,''),fontSize:parseFloat(style.fontSize),fontUnit:'px'};
  }
  for(const node of nodes){
   const tag=node.matches('[role=status]')?'status':node.tagName.toLowerCase(),index=counts[tag]||0;counts[tag]=index+1;
   const key=id+'/'+tag+'/'+index,textCapable=!(tag==='input'&&['radio','checkbox'].includes(node.type));keyOf.set(node,key);
   components.push({id:key,kind:tag,textCapable});
   const style=getComputedStyle(node),r=node.getBoundingClientRect(),parent=node.parentElement.getBoundingClientRect();
   const fontFamily=style.fontFamily.split(',')[0].trim().replace(/^['"]|['"]$/g,'');
   values[key]={fontFamily,fontSize:parseFloat(style.fontSize),fontUnit:'px',cssFontFamily:style.fontFamily,width:r.width,height:r.height,unit:'css-px-border-box',narrowWithinParent:r.width<=parent.width+1,htmlTag:node.tagName,color:style.color,backgroundColor:style.backgroundColor};
   if(['h1','p','label','button','a','legend','span','status'].includes(tag)){
    let clipped=false;
    for(const child of node.childNodes){
     if(child.nodeType!==Node.TEXT_NODE||!child.textContent.trim())continue;
     const range=document.createRange();range.selectNodeContents(child);
     for(const t of range.getClientRects())if(t.left<r.left-1||t.right>r.right+1||t.top<r.top-2||t.bottom>r.bottom+2)clipped=true;
    }
    if(clipped)clippedTextCount++;
   }
  }
  const focusables=nodes.filter(n=>n.matches('input,select,textarea,button,a[href],[tabindex],[contenteditable=true],[role=button],[role=link],[role=checkbox],[role=radio],[role=combobox],[role=listbox],[role=menuitem]')&&!n.matches(':disabled'));
  const radios=new Map();
  for(const n of focusables.filter(n=>n.type==='radio')){const k=n.name||keyOf.get(n);if(!radios.has(k)||n.checked)radios.set(k,n);}
  const tabbable=focusables.filter(n=>n.type!=='radio'||radios.get(n.name||keyOf.get(n))===n).map(n=>keyOf.get(n));
  let overlaps=0;
  const controls=nodes.filter(n=>n.matches('input,select,textarea,button,a[href]'));
  for(let i=0;i<controls.length;i++)for(let j=i+1;j<controls.length;j++){
   const a=controls[i].getBoundingClientRect(),b=controls[j].getBoundingClientRect();
   if(Math.min(a.right,b.right)-Math.max(a.left,b.left)>1&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1)overlaps++;
  }
  const surface=id+'/surface',r=root.getBoundingClientRect(),style=getComputedStyle(root);
  components.unshift({id:surface,kind:'page',textCapable:false});
  values[surface]={viewportWidth:innerWidth,viewportHeight:innerHeight,unit:'css-px-border-box',horizontalOverflowPixels:Math.max(0,document.documentElement.scrollWidth-innerWidth),clippedTextCount,overlappingControls:overlaps,htmlTag:root.tagName,color:style.color,backgroundColor:style.backgroundColor};
  if(panel){const n=root.querySelector('.panel');if(!n)throw Error('Missing declared panel');const p=n.parentElement.getBoundingClientRect(),b=n.getBoundingClientRect();const k=id+'/panel';components.push({id:k,kind:'container',textCapable:false});values[k]={width:b.width,height:b.height,unit:'css-px-border-box',narrowWithinParent:b.width<=p.width+1};}
  const active=document.activeElement;
  const initialFocus=active?.id||(active?.dataset.field?'[data-field='+active.dataset.field+']':null);
  return {components,values,counts,tabbable,initialFocus,devicePixelRatio,viewport:{width:innerWidth,height:innerHeight},documentHeight:document.documentElement.scrollHeight};
 },state);
}
async function keyboardReachability(state,measured){
 const visited=new Set();
 const active=await page.evaluate(({scope,id})=>{
  const root=document.querySelector(scope);const n=document.activeElement;if(!root?.contains(n))return null;
  const visible=x=>x.getClientRects().length>0&&getComputedStyle(x).display!=='none'&&getComputedStyle(x).visibility!=='hidden'&&!x.closest('[hidden]');
  const candidate=n=>!n.matches('script,style,noscript,template,input[type=hidden]')&&(n.matches('h1,p,label,input,select,textarea,button,a,th,td,legend,span,[role=status],[tabindex],[contenteditable=true],[role=button],[role=link],[role=checkbox],[role=radio],[role=combobox],[role=listbox],[role=menuitem]')||Array.from(n.childNodes).some(c=>c.nodeType===Node.TEXT_NODE&&c.textContent.trim()));
  const nodes=Array.from(root.querySelectorAll('*')).filter(n=>visible(n)&&candidate(n)),counts={};
  for(const x of nodes){const tag=x.matches('[role=status]')?'status':x.tagName.toLowerCase(),index=counts[tag]||0;counts[tag]=index+1;if(x===n)return id+'/'+tag+'/'+index;}return null;
 },state);
 if(active)visited.add(active);
 for(let i=0;i<Math.max(8,measured.tabbable.length*2+6);i++){
  await page.keyboard.press('Tab');
  const focused=await page.evaluate(({scope,id})=>{
   const root=document.querySelector(scope),n=document.activeElement;if(!root?.contains(n))return null;
   const candidate=x=>!x.matches('script,style,noscript,template,input[type=hidden]')&&(x.matches('h1,p,label,input,select,textarea,button,a,th,td,legend,span,[role=status],[tabindex],[contenteditable=true],[role=button],[role=link],[role=checkbox],[role=radio],[role=combobox],[role=listbox],[role=menuitem]')||Array.from(x.childNodes).some(c=>c.nodeType===Node.TEXT_NODE&&c.textContent.trim()));
   const nodes=Array.from(root.querySelectorAll('*')).filter(x=>x.getClientRects().length>0&&getComputedStyle(x).display!=='none'&&getComputedStyle(x).visibility!=='hidden'&&!x.closest('[hidden]')&&candidate(x));
   const counts={};for(const x of nodes){const tag=x.matches('[role=status]')?'status':x.tagName.toLowerCase(),index=counts[tag]||0;counts[tag]=index+1;if(x===n)return id+'/'+tag+'/'+index;}return null;
  },state);if(focused)visited.add(focused);
  if(measured.tabbable.every(id=>visited.has(id)))break;
 }
 const missing=measured.tabbable.filter(id=>!visited.has(id));
 operations.push({state:state.id,method:'Tab keys on actual published controls',expected:measured.tabbable,visited:[...visited],missing});
 return missing.length===0;
}
async function horizontalTableReachability(state,viewport){
 const grids=page.locator(state.scope+' .grid');let checked=0;
 for(let i=0;i<await grids.count();i++){
  const grid=grids.nth(i);if(!await grid.isVisible())continue;
  const before=await grid.evaluate(n=>({scrollWidth:n.scrollWidth,clientWidth:n.clientWidth,scrollLeft:n.scrollLeft}));if(before.scrollWidth<=before.clientWidth+1)continue;
  await grid.hover();await page.mouse.wheel(before.scrollWidth*2,0);await page.waitForTimeout(100);
  const actual=await grid.evaluate(n=>{const r=n.getBoundingClientRect(),last=n.querySelector('th:last-child')?.getBoundingClientRect();return{scrollLeft:n.scrollLeft,max:n.scrollWidth-n.clientWidth,lastColumnReachable:!!last&&last.right<=r.right+1&&last.left>=r.left-1};});
  assert.ok(actual.scrollLeft>0&&actual.lastColumnReachable,'Native horizontal wheel must reach the last table column');
  operations.push({state:state.id,viewport,action:'Native horizontal mouse wheel reaches final table column',...before,...actual,status:'PASS'});checked++;
  await grid.evaluate((n,left)=>{n.scrollLeft=left;},before.scrollLeft);
 }
 return checked;
}
async function capture(id){
 const state=states.get(id);assert.ok(state,'Known authored state required.');
 await page.setViewportSize({width:1366,height:768});await page.waitForTimeout(50);
 const base=await measure(state);base.keyboardReachability=await keyboardReachability(state,base);
 await page.evaluate(()=>scrollTo(0,0));
 const files=[];
 for(const viewport of [{width:1366,height:768},{width:1024,height:768},{width:390,height:844}]){
  await page.setViewportSize(viewport);await page.waitForTimeout(50);await page.evaluate(()=>scrollTo(0,0));
  const measured=viewport.width===1366?base:await measure(state);
  await horizontalTableReachability(state,viewport);
  if(viewport.width!==1366){measured.keyboardReachability=await keyboardReachability(state,measured);base.narrow??=[];base.narrow.push(measured);}
  const name=id+'.'+viewport.width+'.png',file=path.join(out,name);await page.screenshot({path:file,fullPage:true});
  files.push({file:'build/test-results/ui/'+name,sha256:sha(file),viewport});
 }
 base.evidence=files;snapshots.set(id,base);
 await page.setViewportSize({width:1366,height:768});await page.waitForTimeout(30);
 console.log('Observed '+id);
}
async function collectorRegressionProbes(){
 const state={...states.get('F01.Login'),id:'HARNESS-Unknown'};
 await page.evaluate(()=>{for(const tag of ['h2','div']){const n=document.createElement(tag);n.dataset.collectorProbe='true';n.textContent='Unexpected rendered text';n.style.fontSize='11px';document.querySelector('main').append(n);}document.querySelector('main').append(document.createTextNode('Unexpected root text'));});
 const unknown=await measure(state);for(const tag of ['h2','div']){const c=unknown.components.find(c=>c.kind===tag);assert.ok(c,'New text tag must be discovered');assert.equal(unknown.values[c.id].fontSize,11);}
 assert.ok(unknown.components.some(c=>c.id==='HARNESS-Unknown/surface-direct-text'),'Direct surface text must be discovered');
 await page.evaluate(()=>{document.querySelectorAll('[data-collector-probe]').forEach(n=>n.remove());document.querySelector('main').childNodes.forEach(n=>{if(n.nodeType===Node.TEXT_NODE&&n.textContent==='Unexpected root text')n.remove();});});
 collectorProbes.push({id:'unlisted-h2-and-direct-div-text',status:'PASS',result:'Both new text-owning tags and direct main text are discovered as unknown components; the tag probes retain their 11px computed font.'});
 const tabState={...states.get('F01.Login'),id:'HARNESS-NegativeTabIndex'};
 const previous=await page.locator('#sp2-login-id').getAttribute('tabindex');
 await page.locator('#sp2-login-id').evaluate(n=>n.setAttribute('tabindex','-1'));await page.locator('#sp2-login-pw').focus();
 const negative=await measure(tabState);assert.ok(negative.tabbable.includes('HARNESS-NegativeTabIndex/input/0'));assert.equal(await keyboardReachability(tabState,negative),false,'Negative tabindex cannot silently remove a required native input from Tab checks');
 await page.locator('#sp2-login-id').evaluate((n,old)=>{if(old===null)n.removeAttribute('tabindex');else n.setAttribute('tabindex',old);},previous);await page.locator('#sp2-login-id').focus();
 collectorProbes.push({id:'required-input-tabindex-minus-one',status:'PASS',result:'Required enabled input stays in expected candidates; real Tab traversal fails until the test mutation is reverted.'});
}
async function login(){
 await page.locator('#sp2-login-id').fill('admin');await page.locator('#sp2-login-pw').fill(profile.adminPassword);
 await Promise.all([page.waitForURL('**/menu'),page.locator('button[type=submit]').filter({hasText:'ログイン'}).click()]);
}
(async()=>{
 const {hashArtifact}=await import(pathToFileURL(validatorPath).href);
 artifactBefore=hashArtifact(path.join(root,'build/publish'));
 const host=read(path.join(root,'.tmp/ui-runtime/owned-host.json'));
 assert.equal(host.profileSha256.toLowerCase(),sha(profilePath));assert.equal(path.resolve(host.productFile),path.join(root,'build/publish/CareerManagement.Web.dll'));assert.equal(host.productSha256.toLowerCase(),sha(host.productFile));
 const metadata=Buffer.from(path.join(root,'.tmp/ui-runtime/owned-host.json'),'utf8').toString('base64');
 const ownership=`$m=Get-Content -LiteralPath ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('${metadata}'))) -Raw|ConvertFrom-Json;$p=Get-Process -Id $m.pid -ErrorAction Stop;$n=Get-NetTCPConnection -LocalPort 7445 -RemotePort 0 -ErrorAction Stop;if($p.StartTime.ToUniversalTime().Ticks -ne ([DateTimeOffset]$m.startedAt).UtcDateTime.Ticks -or $m.pid -notin @($n.OwningProcess)){exit 1}`;
 try{execFileSync('pwsh',['-NoProfile','-EncodedCommand',Buffer.from(ownership,'utf16le').toString('base64')],{stdio:'pipe'});}catch{throw Error('Published host process and TCP endpoint ownership verification failed.');}
 try{
  browser=await chromium.launch({executablePath:process.env.SP2_EDGE_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});renderer='Edge '+browser.version();
  context=await browser.newContext({ignoreHTTPSErrors:true,viewport:{width:1366,height:768}});page=await context.newPage();
  page.on('pageerror',e=>errors.push(redact(e.message)));
  for(const asset of ['app.css','site.css']){const response=await context.request.get(profile.url+'/css/'+asset);assert.equal(response.status(),200);const actual=crypto.createHash('sha256').update(await response.body()).digest('hex');assert.equal(actual,sha(path.join(root,'build/publish/wwwroot/css',asset)),'Served stylesheet must match published bytes.');}
  await navigate('/account/login');await collectorRegressionProbes();await capture('F01.Login');
  await page.locator('#sp2-login-id').fill('unregistered-ui');await page.locator('#sp2-login-pw').fill('invalid-ui-password');
  await Promise.all([page.waitForNavigation(),page.locator('button[type=submit]').filter({hasText:'ログイン'}).click()]);await capture('F01.Error');
  await login();await capture('F02.Menu');await navigate('/employees');await capture('F03.Initial');
  let release,seen;const held=new Promise(r=>release=r),observed=new Promise(r=>seen=r);
  await page.route('**/employees/search',async route=>{seen();await held;await route.continue();},{times:1});
  const searched=page.waitForResponse(r=>new URL(r.url()).pathname==='/employees/search'&&r.request().method()==='POST');
  await page.locator('#search-run').click();await observed;
  try{assert.ok(await page.locator('#search-run').isDisabled());assert.ok(await page.locator('#employee-new').isDisabled());await capture('F03.Busy');}finally{release();await searched;}
  await page.waitForFunction(()=>document.querySelectorAll('#search-rows tr').length===2);await capture('F03.Results');
  await page.locator('#search-rows tr').filter({hasText:'000001'}).locator('input[type=radio]').check();
  await Promise.all([page.waitForURL('**/employees/edit?state=*'),page.locator('#employee-edit').click()]);await capture('F04.Edit.Basic');
  assert.ok(await page.locator('#employee-no').isEditable()===false);
  await apiClick('#careers-tab','/employees/draft');await capture('F04.Edit.Careers');
  await Promise.all([page.waitForResponse(r=>new URL(r.url()).pathname==='/employees/draft'),page.locator('#career-rows input[type=radio]').first().check()]);
  await page.waitForFunction(()=>!document.querySelector('[data-career=duties]').matches(':disabled'));
  await page.locator('[data-career=duties]').fill('画面の未保存確認');await apiClick('#career-add','/employees/draft');await page.locator('dialog[open]').waitFor();await capture('F04.PendingConfirmation');
  await page.locator('dialog[open]').getByRole('button',{name:'取消',exact:true}).click();await page.waitForTimeout(100);
  const pendingRawPreserved=await page.locator('[data-career=duties]').inputValue()==='画面の未保存確認';operations.push({state:'F04.PendingConfirmation',action:'Cancel pending action',rawPreserved:pendingRawPreserved});assert.equal(pendingRawPreserved,true,'Cancel keeps the pending career raw edit');
  await page.locator('#employee-cancel').click();
  const returned=await Promise.race([page.waitForURL('**/employees?state=*').then(()=>true),page.locator('dialog[open]').waitFor().then(()=>false)]);
  if(!returned){await page.locator('dialog[open]').getByRole('button',{name:'はい',exact:true}).click();await page.waitForURL('**/employees?state=*');}
  await Promise.all([page.waitForURL('**/employees/edit?state=*'),page.locator('#employee-new').click()]);await capture('F04.New.Basic');
  const invalid=await apiClick('#employee-save','/employees/save');assert.equal(invalid.status(),422);await capture('F04.Error.Basic');
  await page.locator('#employee-no').pressSequentially('000004');await page.locator('[data-field=name]').fill('検証氏名'.repeat(10));await page.locator('[data-field=kana]').fill('カナ'.repeat(40));await page.locator('[data-field=careerSummary]').fill(('長文確認\n').repeat(100));await capture('F04.Long.Basic');
  assert.equal(await page.locator('[data-field=name]').inputValue(),'検証氏名'.repeat(10));assert.equal(await page.locator('[data-field=kana]').inputValue(),'カナ'.repeat(40));
  await page.locator('#employee-cancel').click();await page.locator('dialog[open]').waitFor();await capture('F04.Discard');
  await page.locator('dialog[open]').getByRole('button',{name:'いいえ',exact:true}).click();assert.equal(await page.locator('#employee-no').inputValue(),'000004');
  await page.locator('#employee-cancel').click();await Promise.all([page.waitForURL('**/employees?state=*'),page.locator('dialog[open]').getByRole('button',{name:'はい',exact:true}).click()]);
  await navigate('/codes');await capture('F06.Initial');await apiClick('#code-new','/codes/open');await capture('F06.New');
  await page.locator('#code-value').pressSequentially('04');await page.locator('#code-cancel').click();await page.locator('dialog[open]').waitFor();await capture('F06.Discard');
  await page.locator('dialog[open]').getByRole('button',{name:'いいえ',exact:true}).click();assert.equal(await page.locator('#code-value').inputValue(),'04');
  await page.locator('#code-cancel').click();await page.locator('dialog[open]').getByRole('button',{name:'はい',exact:true}).click();
  await page.waitForTimeout(100);await Promise.all([page.waitForResponse(r=>new URL(r.url()).pathname==='/codes/open'),page.locator('#code-rows tr').filter({hasText:'01'}).first().locator('input[type=radio]').check()]);
  await page.waitForFunction(()=>document.querySelector('#code-value').value==='01'&&!document.querySelector('#code-enabled').matches(':disabled'));
  await page.locator('#code-enabled').uncheck();await page.locator('#code-save').click();await page.locator('dialog[open]').waitFor();await capture('F06.StopConfirmation');
  await page.locator('dialog[open]').getByRole('button',{name:'いいえ',exact:true}).click();await page.locator('#code-cancel').click();await page.locator('dialog[open]').getByRole('button',{name:'はい',exact:true}).click();
  const exitContext=await browser.newContext({ignoreHTTPSErrors:true,viewport:{width:1366,height:768}});page=await exitContext.newPage();page.on('pageerror',e=>errors.push(redact(e.message)));await navigate('/account/login');
  await Promise.all([page.waitForNavigation(),page.locator('button[formaction="/account/exit"]').click()]);await capture('F01.Exited');
  assert.deepEqual(errors,[]);
 }catch(e){fatal=redact(e.message);console.error('UI observation failed: '+redact(e.name));}
 finally{
  if(browser)await browser.close();artifactAfter=hashArtifact(path.join(root,'build/publish'));
  const observations=[],components=[];
  for(const [stateId,base] of snapshots){
   components.push(...base.components);const narrow=base.narrow||[];
   const expectedIds=new Set(base.components.map(c=>c.id));
   const missing=narrow.reduce((n,x)=>n+base.components.filter(c=>!x.components.some(v=>v.id===c.id)).length,0);
   const unknown=narrow.reduce((n,x)=>n+x.components.filter(c=>!expectedIds.has(c.id)).length,0);
   for(const component of base.components){
    const v=base.values[component.id],nv=narrow.map(x=>x.values[component.id]).filter(Boolean);
    if(v){v.narrowMinFontSize=Math.min(...nv.map(x=>x.fontSize).filter(Number.isFinite),v.fontSize??Infinity);v.narrowWithinParent=nv.every(x=>x.narrowWithinParent!==false);}
   }
   const surface=base.values[stateId+'/surface'];Object.assign(surface,{narrowMissingComponents:missing,narrowUnknownComponents:unknown,narrowHorizontalOverflowPixels:Math.max(0,...narrow.map(x=>x.values[stateId+'/surface'].horizontalOverflowPixels)),narrowClippedTextCount:narrow.reduce((n,x)=>n+x.values[stateId+'/surface'].clippedTextCount,0),narrowOverlappingControls:narrow.reduce((n,x)=>n+x.values[stateId+'/surface'].overlappingControls,0),keyboardReachability:base.keyboardReachability&&narrow.every(x=>x.keyboardReachability),initialFocus:base.initialFocus,browserErrorCount:errors.length,collectorComplete:!fatal&&snapshots.size===states.size});
   for(const rule of contract.rules.filter(r=>r.target.startsWith(stateId+'/'))){
    const value=base.values[rule.target];if(!value)continue;
    const properties={};for(const property of Object.keys(rule.properties))properties[property]=value[property]??null;
    observations.push({ruleId:rule.id,target:rule.target,method:{font:'computed-style',dimensions:'layout-measurement',appearance:'computed-style',render:'layout-measurement',interaction:'keyboard-operation'}[rule.kind],properties,evidence:base.evidence});
   }
  }
  const unchanged=artifactBefore.sha256===artifactAfter.sha256&&contractHash===sha(contractPath)&&inputHash===sha(inputPath)&&validatorHash===sha(validatorPath)&&JSON.stringify(sourceBefore)===JSON.stringify(inventorySource());
  const record={schemaVersion:1,projectId:'sample-project2',profileId:'CSharp_ASPNET',runId,status:!fatal&&unchanged&&snapshots.size===states.size?'OBSERVED_FOR_INDEPENDENT_CONFORMANCE_GATE':'FAILED',startedAt,completedAt:new Date().toISOString(),contractSha256:contractHash,frozenInputManifestSha256:inputHash,validatorSha256:validatorHash,artifact:{file:'build/publish',sha256:artifactBefore.sha256,kind:artifactBefore.kind,files:artifactBefore.files},artifactAfterSha256:artifactAfter.sha256,environment:{platform:'Windows 11',renderer:renderer||'Edge unavailable',dpi:96,scale:1,viewport:{width:1366,height:768,unit:'px'},narrowViewports:contract.basis.narrowViewports,dpiMeaning:'CSS renderer at devicePixelRatio1; desktop settings were not changed'},components,observations,keyboardOperations:operations,collectorRegressionProbes:collectorProbes,measurementSources:measurementBefore,sourceFiles:sourceBefore,sourcesUnchanged:unchanged,observedStates:[...snapshots.keys()],browserErrors:errors,fixtureDatabase:profile.database,databaseWrites:'No employee/code saves; one rejected login and normal login authentication counters only. Dedicated fixture.',notExecuted:['physical keyboard and Japanese IME composition','physical browser zoom and other desktop DPI','production database','user acceptance and formal scoring'],formalScore:null,fatal};
  fs.writeFileSync(recordPath,JSON.stringify(record,null,2)+'\n');
  console.log(JSON.stringify({status:record.status,states:snapshots.size,components:components.length,observations:observations.length,sourcesUnchanged:unchanged,fatal}));
  process.exitCode=record.status==='FAILED'?1:0;
 }
})().catch(e=>{const fatal=redact(e.message);fs.writeFileSync(recordPath,JSON.stringify({schemaVersion:1,projectId:'sample-project2',profileId:'CSharp_ASPNET',runId,status:'FAILED',fatal,formalScore:null},null,2)+'\n');console.error('UI harness did not reach observation finalization: '+fatal);process.exitCode=1;});
