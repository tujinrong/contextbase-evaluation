"use strict";
// Same-origin MVC enhancement. Raw values stay in the current document/server owner;
// history contains only opaque immutable search references, never employee content.
(() => {
const $=s=>document.querySelector(s), all=s=>Array.from(document.querySelectorAll(s));
const host=$('[data-initial]'), root=$('.sp2-ui'), screen=root?.dataset.screenId;
const isError=host?.dataset.uiError==='true';
const csrf=()=>$('input[name="__RequestVerificationToken"]')?.value||"";
let vm=host?JSON.parse(host.dataset.initial):null, ui=vm?.ui, blocked=false, busy=false, suppressLeave=false;
let bootstrapping=true;
const initialHistory=historyRef();
let dirty=()=>false, capture=()=>({stateId:ui.stateId,stateRevision:ui.stateRevision,tabId:ui.tabId,documentLease:ui.documentLease,
  employee:null,pending:null,code:null,activeTab:null,selectedClientRowKey:null});
let apply=()=>{}, beforeNavigate=async()=>{}, reloadSaved=async()=>{};
const controlLocks=new WeakMap();
function lockControls(selector,value){
 for(const c of all(selector+' input,'+selector+' select,'+selector+' textarea,'+selector+' button')){
  if(value){if(!controlLocks.has(c))controlLocks.set(c,c.disabled);c.disabled=true;}
  else if(controlLocks.has(c)){c.disabled=controlLocks.get(c);controlLocks.delete(c);}
 }
}
function busyLinks(value){
 for(const a of all('a[data-destination],#employee-new,.rowaction')){a.setAttribute('aria-disabled',String(value||blocked));a.tabIndex=value||blocked?-1:0;}
 const logout=$('[data-action="logout"]');if(logout)logout.disabled=value||blocked;
 if(host)host.setAttribute('aria-busy',String(value));
}
const text=(selector,value)=>{const node=$(selector);if(node)node.textContent=value??"";};
function notice(value){text('#message',value);}
function updateUi(next){if(next){ui=next;if(vm){vm.ui=next;vm.stateRevision=next.stateRevision;}publish();}}
function publish(){if(host&&vm)host.dataset.initial=JSON.stringify(vm);}
function historyRef(){const h=history.state;return h&&typeof h.resumeRef==="string"&&typeof h.sourceTabId==="string"?h:null;}
function checkpointHistory(){
 if(!ui||bootstrapping)return;
 const value=ui.resumeRef&&ui.sourceTabId?{resumeRef:ui.resumeRef,sourceTabId:ui.sourceTabId}:null;
 history.replaceState(value,"",ui.canonicalUrl);
}
function stop(message,unknown=false){
 blocked=true;if(vm){vm.canSave=false;if(unknown)vm.outcome={kind:"ResultUnknown",messageId:"MSG-034",commitState:"Unknown",message};publish();}
 busyLinks(false);
 all('button').filter(b=>!b.closest('dialog')&&b.dataset.action!=="reload").forEach(b=>b.disabled=true);
 notice(message);
}
function outcome(result){
 const o=result?.outcome;if(!o)return;
 notice(o.message);
 if(o.kind==="Expired") {suppressLeave=true;location.assign('/account/login?expired=1');return;}
 if(o.kind==="Forbidden"){stop(o.message);return;}
 if(o.messageId==="MSG-041"&&result.ui?.canOperate!==true||o.commitState==="Unknown"){
  const unknown=vm?.outcome?.commitState==="Unknown"||o.commitState==="Unknown";
  stop(unknown?"保存結果を確認できません。再保存せず、入力をコピーするか現在値を再読込してください。 "+o.message:o.message,unknown);
 }
 showErrors(o.fieldErrors||[]);
}
function showErrors(errors){
 all('[aria-invalid]').forEach(e=>e.removeAttribute('aria-invalid'));
 all('[data-ui="field-error"]').forEach(e=>e.textContent="");
 const box=$('[data-ui="error-summary"]');if(!box)return;
 const list=box.querySelector('ul');list.replaceChildren();box.hidden=!errors.length;
 for(const e of errors){
  const field=$('[data-item-id="'+e.itemId+'"]');if(!field)continue;
  const li=document.createElement('li'),a=document.createElement('a');a.href='#'+field.id;a.textContent=e.message;
  a.addEventListener('click',event=>{event.preventDefault();field.focus();});li.append(a);list.append(li);
  field.setAttribute('aria-invalid','true');const hint=$('[data-error-for="'+e.itemId+'"]');
  if(hint){hint.id=field.id+'-error';hint.textContent=e.message;field.setAttribute('aria-describedby',hint.id);}
 }
 if(errors.length){if(screen==="F04")setTab(/^F04-I(1[4-9]|2[0-4])$/.test(errors[0].itemId)?"Careers":"Basic");box.focus();}
}
async function api(path,data,{userAction=true,headers={}}={}){
 const r=await fetch(path,{method:'POST',credentials:'same-origin',cache:'no-store',redirect:'error',headers:{'Content-Type':'application/json','X-SP2-CSRF':csrf(),'X-SP2-User-Action':String(userAction),...headers},body:JSON.stringify(data)});
 if(![200,400,401,403,404,409,410,413,415,422,503].includes(r.status)||!r.headers.get('Content-Type')?.toLowerCase().startsWith('application/json'))throw new Error('Unexpected JSON response');
 const value=await r.json();if(!value||Array.isArray(value)||typeof value!=='object')throw new Error('Invalid JSON shape');
 if(value.navigation){
  const n=value.navigation;if(Object.keys(value).some(k=>k!=="navigation")||r.status!==200||typeof n.url!=="string"||!['NotStarted','RolledBack','Committed','Unknown'].includes(n.commitState))throw new Error('Invalid navigation envelope');
 }else if(!('outcome'in value||'ui'in value||'stateId'in value||'editStateId'in value||'attached'in value||'phase'in value))throw new Error('Unknown response');
 return value;
}
function navigate(envelope){
 if(!envelope)return false;
 if(blocked||envelope.commitState==="Unknown")throw new Error('Navigation blocked');
 const allowed=/^\/(menu|employees|employees\/new|employees\/[1-9][0-9]*\/edit|codes)\?nav=[a-f0-9]{64}$/;
 if(envelope.url!=="/account/login"&&!allowed.test(envelope.url))throw new Error('Unapproved destination');
 suppressLeave=true;location.assign(envelope.url);return true;
}
async function ask(message,{discard=false,choices=['Yes','No']}={}){
 const dialog=$('dialog[data-ui="discard"]'),title=dialog.querySelector('[data-part="title"]'),p=dialog.querySelector('[data-part="message"]');
 title.textContent=discard?'未保存の変更':'操作の確認';p.textContent=message;
 const bar=dialog.querySelector('.actions');bar.replaceChildren();
 return await new Promise(resolve=>{
  const finish=value=>{dialog.close();dialog.oncancel=null;resolve(value);};
  if(discard){
   for(const [value,label,part]of[['Continue','編集を続ける','continue'],['Discard','変更を破棄して移動','discard']]){
    const b=document.createElement('button');b.type='button';b.textContent=label;b.dataset.part=part;b.addEventListener('click',()=>finish(value));bar.append(b);
   }
  }else for(const choice of choices){
   const b=document.createElement('button');b.type='button';b.textContent=({Yes:'はい',No:'いいえ',Cancel:'取消'})[choice];b.addEventListener('click',()=>finish(choice));bar.append(b);
  }
  dialog.oncancel=e=>{e.preventDefault();finish(discard?'Continue':choices.includes('Cancel')?'Cancel':'No');};
  dialog.showModal();(discard?bar.querySelector('[data-part="continue"]'):bar.lastElementChild).focus();
 });
}
function option(select,value,label,invalid=false){const o=document.createElement('option');o.value=value;o.textContent=label;if(invalid)o.dataset.invalidRaw='true';select.append(o);return o;}
function choices(select,codes,category,current,{allValues=false,emptyLabel='選択してください',invalidHint=null}={}){
 select.replaceChildren();option(select,'',emptyLabel);
 codes.filter(c=>c.category===category&&(allValues||c.enabled||c.code===current)).forEach(c=>option(select,c.code,c.code+' '+c.name+(c.enabled?'':'（停止）')));
 if(current&&!Array.from(select.options).some(o=>o.value===current))option(select,current,'未確認の値：'+current,true);
 select.value=current??'';if(invalidHint)text(invalidHint,select.selectedOptions[0]?.dataset.invalidRaw?'元の値：'+current:'');
}
function td(row,value,col){const cell=document.createElement('td');cell.dataset.col=col;cell.textContent=value??'';row.append(cell);return cell;}
function context(){return {stateId:ui.stateId,stateRevision:ui.stateRevision,tabId:ui.tabId,documentLease:ui.documentLease};}
function activeLink(e){return e.button===0&&!e.ctrlKey&&!e.metaKey&&!e.shiftKey&&!e.altKey;}
function setTab(name){
 if(screen!=="F04")return;
 for(const [tab,pane,key]of[['#basic-tab','#basic-pane','Basic'],['#careers-tab','#careers-pane','Careers']]){
  const b=$(tab),selected=name===key;$(pane).hidden=!selected;b.setAttribute('aria-selected',String(selected));b.tabIndex=selected?0:-1;b.classList.toggle('tabon',selected);
 }
}

const login=$('#login-form');if(login)login.addEventListener('submit',()=>login.querySelectorAll('button').forEach(b=>b.disabled=true));
if(host?.tagName==='FORM')host.addEventListener('submit',e=>e.preventDefault());
if(!vm||!ui)return;
root.inert=true;
const disclosure=$('.nav details');function adjustNav(){if(disclosure)disclosure.open=innerWidth>767;}adjustNav();addEventListener('resize',adjustNav);

if(screen==="F03"&&!isError){
 const controls=['#f03-i01','#f03-i02','#f03-i03','#f03-i04'].map($), list=$('[data-item-id="F03-I08"]');
 let sequence=vm.clientSequence,epoch=0,queue=Promise.resolve(),syncFailed=false,unacknowledged=0,exportOp=null,scrollTimer=null,rendering=false;
 const raw=()=>({employeeNo:controls[0].value,name:controls[1].value,department:controls[2].value,employmentStatus:controls[3].value});
 const scroll=()=>Math.max(0,list.scrollTop);
 function setBusy(value){busy=value;busyLinks(value);controls.forEach(c=>c.disabled=value);all('#search-rows input').forEach(c=>c.disabled=value||blocked);$('#search-run').disabled=value||blocked;$('#search-clear').disabled=value||blocked;$('#employee-export').disabled=value||blocked||!vm.selectedEmployeeId||vm.resultStatus!=="Success";}
 function accept(r,showRaw=false){
  if(r.ui)updateUi(r.ui);if(r.stateId){vm=r;ui=r.ui;sequence=Math.max(sequence,r.clientSequence);render(showRaw);}else outcome(r);
 }
 function render(showRaw=false){
  rendering=true;
  if(showRaw){controls[0].value=vm.raw.employeeNo;controls[1].value=vm.raw.name;choices(controls[2],vm.codes,'DEPARTMENT',vm.raw.department,{allValues:true,emptyLabel:'すべて',invalidHint:'[data-invalid-hint="department"]'});choices(controls[3],vm.codes,'EMPLOYMENT_STATUS',vm.raw.employmentStatus,{allValues:true,emptyLabel:'すべて',invalidHint:'[data-invalid-hint="employmentStatus"]'});}
  const body=$('#search-rows');body.replaceChildren();
  for(const r of vm.rows){
   const row=document.createElement('tr');row.classList.toggle('selected',r.employeeId===vm.selectedEmployeeId);
   const radio=document.createElement('input');radio.type='radio';radio.name='employee';radio.checked=r.employeeId===vm.selectedEmployeeId;radio.setAttribute('aria-label',r.employeeNo+' '+r.name+'を選択');
   radio.addEventListener('change',()=>enqueue(async()=>{accept(await api('/employees/select',{...context(),employeeId:r.employeeId}));}));td(row,'','select').append(radio);
   [['employeeNo',r.employeeNo],['name',r.name],['kana',r.kana],['department',r.departmentName],['status',r.employmentName],['joinDate',r.joinDate]].forEach(([c,v])=>td(row,v,c));
   const link=document.createElement('a');link.href='/employees/'+r.employeeId+'/edit';link.className='rowaction';link.dataset.itemId='F03-I11';link.dataset.employeeId=r.employeeId;link.textContent='編集';link.setAttribute('aria-label',r.employeeNo+' '+r.name+'を編集');
   link.addEventListener('click',e=>{if(busy||blocked){e.preventDefault();return;}if(activeLink(e)){e.preventDefault();open('Edit',r.employeeId);}});td(row,'','edit').append(link);body.append(row);
  }
  const stateText=({Unsearched:'未検索',Unapplied:'条件が未適用です。検索し直してください。',Loading:'検索中',Success:'検索済み',LimitExceeded:'200件を超えています。条件を絞り込んでください。',Failed:'取得に失敗しました。条件を保持しています。'})[vm.resultStatus];
  text('#search-count',vm.totalCount===null?stateText:'検索結果：'+vm.totalCount+'件 ／ '+(vm.totalCount?'1～'+vm.totalCount+'件を表示':'0件'));
  text('[data-ui="criteria-state"]',stateText);text('[data-ui="selection"]',vm.selectionText||'社員を選択してください。行の編集は事前の選択なしで開けます。');
  const a=vm.appliedCriteria;text('[data-ui="applied-criteria"]',a?'直前の適用条件：番号 '+(a.employeeNo||'すべて')+' ／ 氏名 '+(a.name||'すべて')+' ／ 部署 '+(a.department||'すべて')+' ／ 在籍 '+(a.employmentStatus||'すべて'):'適用済みの条件はありません。');
  list.scrollTop=Math.min(vm.scrollTop,Math.max(0,list.scrollHeight-list.clientHeight));setBusy(busy);outcome(vm);publish();checkpointHistory();rendering=false;
 }
 function enqueue(work){
  unacknowledged++;const run=queue.then(work);queue=run.then(()=>{unacknowledged--;},()=>{unacknowledged--;syncFailed=true;notice('通信を確認できません。現在の条件を保持しています。再読込前に必要な値をコピーしてください。');});return run;
 }
 function invalidate(){
  if(blocked||busy)return;const captured=raw(),current=++sequence;epoch++;vm.rows=[];vm.selectedEmployeeId=null;vm.selectionText=null;vm.totalCount=null;vm.resultStatus='Unapplied';vm.outcome=null;render();
  enqueue(async()=>{const r=await api('/employees/invalidate',{...context(),clientSequence:current,raw:captured,scrollTop:scroll()});if(r.ui){updateUi(r.ui);checkpointHistory();}outcome(r);}).catch(()=>{});
 }
 controls.forEach(c=>c.addEventListener(c.tagName==='SELECT'?'change':'input',invalidate));
 controls.slice(2).forEach((c,i)=>c.addEventListener('change',()=>{
  if(!c.selectedOptions[0]?.dataset.invalidRaw){c.querySelectorAll('option[data-invalid-raw]').forEach(o=>o.remove());text('[data-invalid-hint="'+(i===0?'department':'employmentStatus')+'"]','');}
 }));
 async function search(){if(busy||blocked)return;setBusy(true);const at=epoch;try{await queue;if(syncFailed)throw new Error('Unsynchronized raw');const r=await api('/employees/search',{...context(),clientSequence:sequence,raw:raw()});if(at===epoch)accept(r);$('#results-heading').focus();}catch{notice('条件を保持しています。通信と画面の状態を確認してから再読込してください。');}finally{setBusy(false);}}
 $('#search-run').addEventListener('click',search);
 controls.forEach(c=>c.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.isComposing&&e.keyCode!==229&&!e.repeat){e.preventDefault();search();}}));
 $('#search-clear').addEventListener('click',async()=>{if(busy||blocked)return;setBusy(true);try{await queue;if(syncFailed)throw new Error();accept(await api('/employees/clear',context()),true);controls[0].focus();}catch{notice('条件を保持しています。再読込前に必要な値をコピーしてください。');}finally{setBusy(false);}});
 async function open(mode,id=null){
  if(busy||blocked)return;setBusy(true);try{await queue;if(syncFailed)throw new Error('Unsynchronized raw');const r=await api('/employees/open',{searchStateId:ui.stateId,stateRevision:ui.stateRevision,employeeId:id,mode,raw:raw(),clientSequence:sequence,scrollTop:scroll(),tabId:ui.tabId,documentLease:ui.documentLease,openOperationId:crypto.randomUUID()});if(!navigate(r.navigation))accept(r);}catch{notice('移動できませんでした。現在の条件を保持しています。');}finally{setBusy(false);}
 }
 $('#employee-new').addEventListener('click',e=>{if(busy||blocked){e.preventDefault();return;}if(activeLink(e)){e.preventDefault();open('New');}});
 list.addEventListener('scroll',()=>{
  if(rendering||busy||blocked)return;clearTimeout(scrollTimer);scrollTimer=setTimeout(()=>{const captured=raw(),current=sequence;enqueue(async()=>{const r=await api('/employees/checkpoint',{...context(),clientSequence:current,raw:captured,scrollTop:scroll()});if(r.ui){updateUi(r.ui);checkpointHistory();}outcome(r);}).catch(()=>{});},100);
 });
 $('#employee-export').addEventListener('click',async()=>{
  if(busy||blocked||exportOp)return;setBusy(true);await queue;if(syncFailed){setBusy(false);return;}
  const op={operationId:crypto.randomUUID(),abort:new AbortController()};exportOp=op;$('#export-cancel').hidden=false;
  try{
   const r=await fetch('/employees/export',{method:'POST',credentials:'same-origin',redirect:'error',headers:{'Content-Type':'application/json','X-SP2-CSRF':csrf(),'X-SP2-User-Action':'true'},body:JSON.stringify({searchStateId:ui.stateId,stateRevision:ui.stateRevision,employeeId:vm.selectedEmployeeId,operationId:op.operationId,raw:raw(),clientSequence:sequence,scrollTop:scroll(),tabId:ui.tabId,documentLease:ui.documentLease}),signal:op.abort.signal});
   if(!r.ok||!r.headers.get('Content-Type')?.startsWith('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')){if(r.headers.get('Content-Type')?.startsWith('application/json'))accept(await r.json());else throw new Error('Invalid export response');return;}
   const revision=Number(r.headers.get('X-SP2-State-Revision'));if(Number.isInteger(revision)&&revision>0)updateUi({...ui,stateRevision:revision,resumeRef:r.headers.get('X-SP2-Resume-Ref'),sourceTabId:r.headers.get('X-SP2-Source-Tab')});checkpointHistory();
   notice('ダウンロードを開始しました。');const blob=await r.blob(),encoded=r.headers.get('Content-Disposition')?.match(/filename\*=UTF-8''([^;]+)/i)?.[1];
   const name=encoded?decodeURIComponent(encoded):'career.xlsx',url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }catch{notice('ダウンロードが完了しなかった場合は、もう一度作成してください。');}
  finally{if(exportOp===op){exportOp=null;$('#export-cancel').hidden=true;setBusy(false);}}
 });
 $('#export-cancel').addEventListener('click',async()=>{const op=exportOp;if(!op)return;try{const r=await api('/employees/export/cancel',{searchStateId:ui.stateId,operationId:op.operationId});notice(r.message);}finally{op.abort.abort();}});
 beforeNavigate=async()=>{clearTimeout(scrollTimer);await queue;if(syncFailed)throw new Error('Unsynchronized raw');const r=await api('/employees/checkpoint',{...context(),clientSequence:sequence,raw:raw(),scrollTop:scroll()});if(r.ui)updateUi(r.ui);outcome(r);checkpointHistory();};
 dirty=()=>unacknowledged>0||syncFailed;apply=r=>accept(r,true);render(true);
}

if(screen==="F04"&&!isError){
 const parent=all('[data-field]'),career=all('[data-career]');
 let originalEmployee=JSON.stringify(vm.employee),originalCareers=JSON.stringify(vm.careers);
 const employee=()=>Object.fromEntries(parent.map(c=>[c.dataset.field,['careerSummary','skills','qualifications','selfPr'].includes(c.dataset.field)&&c.value===''?null:c.value]));
 const pending=()=>{if(!vm.pending)return null;const p={...vm.pending};career.forEach(c=>p[c.dataset.career]=['endMonthRaw','achievements','technologies','phases'].includes(c.dataset.career)&&c.value===''?null:c.value);return p;};
 dirty=()=>{const p=pending(),applied=p?vm.careers.find(c=>c.clientRowKey===p.clientRowKey):null;return JSON.stringify(employee())!==originalEmployee||JSON.stringify(vm.careers)!==originalCareers||vm.removedCareerIds.length>0||!!p&&(!applied||JSON.stringify(p)!==JSON.stringify(applied));};
 capture=()=>({...context(),employee:employee(),pending:pending(),code:null,activeTab:vm.activeTab,selectedClientRowKey:vm.selectedClientRowKey});
 function identity(){const e=employee();text('[data-ui="identity-number"]',e.employeeNo||'社員番号 未入力');text('[data-ui="identity-name"]',e.name||'氏名 未入力');}
 function setBusy(value){busy=value;lockControls('#edit',value);busyLinks(value);all('#edit button').forEach(b=>{if(b.dataset.action!=='reload')b.disabled=value||blocked||b.dataset.reservation==='true';});if(!value&&!blocked){$('#employee-save').disabled=!vm.canSave;$('#career-add').disabled=!vm.canAdd;$('#career-apply').disabled=!vm.pending;$('#career-remove').disabled=!vm.selectedClientRowKey||!vm.careers.some(c=>c.clientRowKey===vm.selectedClientRowKey);}}
 function render(parentValues=false){
  setBusy(false);
  if(parentValues){for(const c of parent){if(c.tagName==='SELECT')choices(c,vm.codes,c.dataset.field==='departmentCode'?'DEPARTMENT':'EMPLOYMENT_STATUS',vm.employee[c.dataset.field]);else c.value=vm.employee[c.dataset.field]??'';}$('#f04-i01').readOnly=!vm.isNew;}
  const rows=$('#career-rows');rows.replaceChildren();
  const values=vm.careers.slice();if(vm.pending&&!values.some(c=>c.clientRowKey===vm.pending.clientRowKey))values.push(vm.pending);
  for(const c of values){const li=document.createElement('li'),b=document.createElement('button');b.type='button';b.dataset.rowKey=c.clientRowKey;li.classList.toggle('selected',c.clientRowKey===vm.selectedClientRowKey);b.textContent=c.projectName||'追加中の経歴';const period=document.createElement('span');period.textContent=(c.startMonthRaw||'開始年月 未入力')+' ～ '+(c.endMonthRaw||'継続中');b.prepend(period);if(vm.careers.some(x=>x.clientRowKey===c.clientRowKey))b.addEventListener('click',()=>draft('Select',c.clientRowKey));else{b.disabled=true;b.dataset.reservation='true';}li.append(b);rows.append(li);}
  if(!values.length){const li=document.createElement('li');li.className='help';li.textContent='経歴はありません。経歴追加から登録できます。';rows.append(li);}
  for(const c of career){if(c.tagName==='SELECT')choices(c,vm.codes,'PROJECT_ROLE',vm.pending?.roleCode);else c.value=vm.pending?.[c.dataset.career]??'';c.disabled=!vm.pending;}
  text('[data-ui="career-mode"]',vm.pending?'編集中の経歴です。反映は一時一覧へ、保存は社員と全経歴へ適用します。':'一覧で選択するか、経歴を追加してください。');
  setTab(vm.activeTab);identity();setBusy(false);outcome(vm);publish();
 }
 async function draft(action,targetClientRowKey=null,targetTab=null,confirm={kind:'None',choice:'None',confirmationId:null}){
  if(busy||blocked)return;const fields=pending();setBusy(true);
  try{const r=await api('/employees/draft',{editStateId:ui.stateId,stateRevision:ui.stateRevision,action,fields,targetClientRowKey,targetTab,confirm,tabId:ui.tabId,documentLease:ui.documentLease});
   if(r.editStateId){const retain=!!r.confirmation||confirm.choice==='Cancel'||confirm.kind==='DiscardPending'&&confirm.choice==='No'||r.outcome?.kind==='Validation';if(retain&&fields)r.pending=fields;vm=r;ui=r.ui;render();}
   else outcome(r);
   if(vm.confirmation){const q=vm.confirmation,answer=await ask(vm.outcome.message,{choices:q.allowedChoices});setBusy(false);await draft(action,targetClientRowKey,targetTab,{kind:q.kind,choice:answer,confirmationId:q.confirmationId});}
  }catch{notice('入力を保持しています。通信と画面の状態を確認してください。');}finally{setBusy(false);}
 }
 for(const [id,tab]of[['#basic-tab','Basic'],['#careers-tab','Careers']])$(id).addEventListener('click',async()=>{
  if(vm.activeTab!==tab){await draft('SwitchTab',null,tab);if(!blocked&&vm.outcome?.kind!=="Validation")$(vm.activeTab==="Careers"?'#careers-tab':'#basic-tab').focus();}
 });
 const tabs=all('[role="tab"]');tabs.forEach((b,i)=>b.addEventListener('keydown',e=>{if(e.isComposing)return;let n;if(e.key==='ArrowRight')n=(i+1)%tabs.length;else if(e.key==='ArrowLeft')n=(i+tabs.length-1)%tabs.length;else if(e.key==='Home')n=0;else if(e.key==='End')n=tabs.length-1;if(n!==undefined){e.preventDefault();tabs[n].focus();}}));
 parent.concat(career).forEach(c=>c.addEventListener('input',()=>{identity();c.removeAttribute('aria-invalid');}));
 $('#career-add').addEventListener('click',()=>draft('Add'));$('#career-apply').addEventListener('click',()=>draft('Apply'));$('#career-remove').addEventListener('click',()=>draft('Remove',vm.selectedClientRowKey));
 $('#employee-save').addEventListener('click',async()=>{
  if(busy||blocked||!vm.canSave)return;setBusy(true);
  try{const r=await api('/employees/save',{editStateId:ui.stateId,stateRevision:ui.stateRevision,employee:employee(),careers:vm.careers,removedCareerIds:vm.removedCareerIds,pending:pending(),tabId:ui.tabId,documentLease:ui.documentLease});
   if(navigate(r.navigation))return;if(r.editStateId){vm=r;ui=r.ui;render();if(vm.outcome?.kind==='NoChange'){originalEmployee=JSON.stringify(employee());originalCareers=JSON.stringify(vm.careers);}}else outcome(r);
  }catch{stop('保存結果を確認できません。再保存せず、入力をコピーするか現在値を再読込してください。',true);}finally{setBusy(false);}
 });
 async function cancel(reloadOnly=false,question=null,choice=null){
  if(busy)return;if(blocked&&!reloadOnly)return;setBusy(true);
  try{const r=await api('/employees/cancel',{editStateId:ui.stateId,stateRevision:ui.stateRevision,rawUiEnvelope:capture(),confirmationId:question?.confirmationId??null,choice,reloadOnly,returnToMenu:false});
   if(navigate(r.navigation))return;if(r.editStateId){const oldBlocked=blocked;vm=r;ui=r.ui;if(reloadOnly&&!r.discardConfirmation&&r.canSave){blocked=false;render(true);originalEmployee=JSON.stringify(vm.employee);originalCareers=JSON.stringify(vm.careers);checkpointHistory();}else{render();blocked=oldBlocked||blocked;}}
   else outcome(r);
   if(r.discardConfirmation){const answer=await ask(r.discardConfirmation.message,{discard:true});setBusy(false);await cancel(reloadOnly,r.discardConfirmation,answer);}
  }catch{if(reloadOnly)stop('データを読み込めませんでした。現在の入力を保持しています。',vm.outcome?.commitState==='Unknown');else notice('入力を保持しています。画面の状態を確認してください。');}finally{setBusy(false);}
 }
 $('#employee-cancel').addEventListener('click',()=>cancel());reloadSaved=()=>cancel(true);$('#employee-reload').addEventListener('click',reloadSaved);
 apply=r=>{if(r.editStateId){vm=r;ui=r.ui;render(true);}else outcome(r);};render(true);
}

if(screen==="F06"&&!isError){
 let baseline='';
 function codeBusy(value){busy=value;lockControls('#codes',value);busyLinks(value);}
 const payload=()=>({...context(),category:vm.category,code:$('#f06-i03').value,name:$('#f06-i04').value,sortOrderRaw:$('#f06-i05').value,enabled:$('#f06-i06').checked,expectedRevision:vm.draft?.expectedRevision??null});
 const values=p=>JSON.stringify([p?.category,p?.code,p?.name,p?.sortOrderRaw,p?.enabled]);
 dirty=()=>!!vm.draft&&values(payload())!==baseline;
 capture=()=>({...context(),employee:null,pending:null,code:vm.draft?payload():null,activeTab:null,selectedClientRowKey:null});
 function render(clean=false){
  $('#f06-i01').value=vm.category;const body=$('#code-rows');body.replaceChildren();
  for(const r of vm.rows){const row=document.createElement('tr');row.classList.toggle('selected',r.code===vm.selectedCode);const b=document.createElement('button');b.type='button';b.textContent=r.code;b.setAttribute('aria-label',r.code+' '+r.name+'を選択');b.addEventListener('click',()=>open(false,r.code));td(row,'','code').append(b);td(row,r.name,'name');td(row,r.sortOrder,'sortOrder');td(row,r.enabled?'〇':'停止','enabled');body.append(row);}
  $('#f06-i03').value=vm.draft?.code??'';$('#f06-i04').value=vm.draft?.name??'';$('#f06-i05').value=vm.draft?.sortOrderRaw??'';$('#f06-i06').checked=vm.draft?.enabled??false;
  const fixed=vm.category==='EMPLOYMENT_STATUS';all('#code-fields input').forEach(c=>{c.disabled=!vm.draft||c.type==='checkbox'&&fixed;if(c.type!=='checkbox')c.readOnly=fixed||c.id==='f06-i03'&&vm.draft?.expectedRevision!=null;});
  $('#code-save').disabled=blocked||busy||!vm.canSave||!vm.draft;$('#code-new').disabled=blocked||busy||fixed||vm.rows.length>=99;$('#code-cancel').disabled=blocked||busy||!vm.draft;
  text('[data-ui="code-mode"]',fixed?'在籍区分は固定です。値は参照・コピーできます。':vm.draft?(vm.draft.expectedRevision==null?'新規コード':'選択中：'+vm.draft.code+' '+vm.draft.name):'一覧から選択するか、新規コードを追加してください。');
  outcome(vm);publish();if(clean)baseline=vm.draft?values(payload()):'';
 }
 async function open(isNew,code=null,category=vm.category,q=null,choice=null){
  if(busy||blocked)return;codeBusy(true);
  try{const r=await api('/codes/open',{category,code,new:isNew,stateId:ui.stateId,stateRevision:ui.stateRevision,rawUiEnvelope:capture(),confirmationId:q?.confirmationId??null,choice,tabId:ui.tabId,documentLease:ui.documentLease});if(r.stateId){vm=r;ui=r.ui;render(!r.discardConfirmation&&choice!=='Continue');}else outcome(r);
   if(r.discardConfirmation){const answer=await ask(r.discardConfirmation.message,{discard:true});codeBusy(false);await open(isNew,code,category,r.discardConfirmation,answer);}
  }catch{notice('入力を保持しています。通信と画面の状態を確認してください。');}finally{codeBusy(false);render();}
 }
 $('#code-new').addEventListener('click',()=>open(true));$('#f06-i01').addEventListener('change',e=>open(false,null,e.target.value));
 async function save(q=null,choice='Yes'){if(busy||blocked)return;codeBusy(true);try{const r=await api('/codes/save',payload(),{headers:q?{'X-SP2-Confirm-Stop':choice,'X-SP2-Confirmation-Id':q.confirmationId}:{}});if(r.stateId){vm=r;ui=r.ui;render(vm.outcome?.kind==='Success'||vm.outcome?.kind==='NoChange');}else outcome(r);if(r.confirmation){const answer=await ask(r.outcome.message,{choices:r.confirmation.allowedChoices});codeBusy(false);await save(r.confirmation,answer);}}catch{stop('保存結果を確認できません。再保存せず現在値を再読込してください。',true);}finally{codeBusy(false);render();}}
 $('#code-save').addEventListener('click',()=>save());
 async function cancel(reloadOnly=false,q=null,choice=null){if(busy||blocked&&!reloadOnly)return;codeBusy(true);try{const r=await api('/codes/cancel',{stateId:ui.stateId,stateRevision:ui.stateRevision,rawUiEnvelope:capture(),confirmationId:q?.confirmationId??null,choice,reloadOnly,returnToMenu:false});if(r.stateId){vm=r;ui=r.ui;if(reloadOnly&&!r.discardConfirmation&&r.canSave)blocked=false;render(!r.discardConfirmation&&choice!=='Continue');}else outcome(r);if(r.discardConfirmation){const answer=await ask(r.discardConfirmation.message,{discard:true});codeBusy(false);await cancel(reloadOnly,r.discardConfirmation,answer);}}catch{stop('現在の入力を保持しています。データを再読込できませんでした。');}finally{codeBusy(false);render();}}
 $('#code-cancel').addEventListener('click',()=>cancel());reloadSaved=()=>cancel(true);$('[data-action="reload"]').addEventListener('click',reloadSaved);
 apply=r=>{if(r.stateId){vm=r;ui=r.ui;render(true);}else outcome(r);};render(true);
}

async function move(destination,q=null,choice=null){
 if(busy||blocked)return;busy=true;lockControls('[data-initial]',true);busyLinks(true);
 try{await beforeNavigate();const r=await api('/ui/navigate',{destination,rawUiEnvelope:capture(),confirmationId:q?.confirmationId??null,choice});if(r.ui)updateUi(r.ui);if(navigate(r.navigation))return;outcome(r);if(r.discardConfirmation){const answer=await ask(r.discardConfirmation.message,{discard:true});busy=false;await move(destination,r.discardConfirmation,answer);}}
 catch{notice('現在の入力を保持しています。移動できませんでした。');}finally{busy=false;lockControls('[data-initial]',false);busyLinks(false);}
}
 all('a[data-destination]').forEach(a=>a.addEventListener('click',e=>{if(busy||blocked){e.preventDefault();return;}if(activeLink(e)){e.preventDefault();move(a.dataset.destination);}}));
$('[data-action="logout"]')?.addEventListener('click',()=>move('Logout'));
addEventListener('beforeunload',e=>{if(!suppressLeave&&dirty()){e.preventDefault();e.returnValue='';}});
let initialized=false,bfcacheReloading=false;
addEventListener('pageshow',async event=>{
 const reference=event.persisted?historyRef():initialHistory;
 if(event.persisted&&screen==='F03'&&reference&&!blocked&&!busy&&!bfcacheReloading){
  bfcacheReloading=true;root.inert=true;root.dataset.pendingInit='true';history.replaceState(reference,'','/employees');location.reload();return;
 }
 if(initialized&&!event.persisted)return;initialized=true;root.inert=true;
 try{
  const ticket=new URL(location.href).searchParams.has('nav');
  if(!isError&&!ticket&&reference&&(screen==='F03'||screen==='F04')){
   const r=await api('/employees/resume',{resumeRef:reference.resumeRef,sourceTabId:reference.sourceTabId,currentStateId:ui.stateId,currentTabId:ui.tabId,documentLease:ui.documentLease},{userAction:false});apply(r);
  }
  const r=await api('/ui/attach',{stateId:ui.stateId,tabId:ui.tabId,documentId:ui.documentId,documentLease:ui.documentLease},{userAction:false});
  if(!r.attached)outcome(r);else checkpointHistory();
 }catch{stop('画面の状態を確認できません。現在の入力を保持しています。入力をコピーするか、破棄して保存済み値を再読込してください。');}
 finally{bootstrapping=false;root.inert=false;delete root.dataset.pendingInit;root.dataset.ready='true';if(!blocked)checkpointHistory();
  if(!blocked&&!isError){if(screen==='F03')$('#f03-i01').focus();else if(screen==='F04')$(vm.isNew?'#f04-i01':'#f04-i02').focus();else if(screen==='F06')$('#f06-i01').focus();}}
});
})();
