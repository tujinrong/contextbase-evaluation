"use strict";
// Same-origin UI only. Never persist employee values or tokens to localStorage/URL.
(() => {
const $ = s => document.querySelector(s);
const all = s => Array.from(document.querySelectorAll(s));
const initial = root => JSON.parse(root.dataset.initial);
const csrf = () => $("input[name='__RequestVerificationToken']")?.value || "";
const message = (text) => { const box=$("#message")||$(".message"); if(box)box.textContent=text||""; };
const show = result => {
  const o=result?.outcome; message(o?.message||"");
  if(o?.kind==="Expired") {window.onbeforeunload=null;location.assign("/account/login?expired=1");}
  if(o?.kind==="Forbidden"&&$("#codes")){window.onbeforeunload=null;location.assign("/menu?denied=1");}
  if(o?.fieldErrors?.length) {
    const error=o.fieldErrors[0]; const item=$("[data-item-id='"+error.itemId+"']");
    if(item){const pane=item.closest("[role=tabpanel]");if(pane){all("[role=tabpanel]").forEach(p=>p.hidden=p!==pane);}item.focus();item.setAttribute("aria-invalid","true");}
  }
};
async function api(path, data, headers={}) {
  const response=await fetch(path,{method:"POST",headers:{"Content-Type":"application/json","X-SP2-CSRF":csrf(),"X-SP2-User-Action":"true",...headers},body:JSON.stringify(data),credentials:"same-origin",cache:"no-store"});
  let result;
  try{result=await response.json();}catch{result={outcome:{message:response.status===400?"要求を確認できません。再読込みしてください。":"通信を確認できません。保存の結果は再読込みで確認してください。",kind:response.status===401?"Expired":"Failed"}};}
  if(result.redirect){window.onbeforeunload=null;location.assign(result.redirect);return result;}
  show(result);return result;
}
function option(select,value,text,selected=false){const o=document.createElement("option");o.value=value;o.textContent=text;o.selected=selected;select.append(o);}
function choices(select,codes,category,current,empty=true){select.replaceChildren();if(empty)option(select,"","選択してください");codes.filter(x=>x.category===category&&(x.enabled||x.code===current)).forEach(x=>option(select,x.code,x.code+" "+x.name+(x.enabled?"":"（停止）"),x.code===current));select.value=current||"";}
function cell(row,text){const td=document.createElement("td");td.textContent=text;row.append(td);return td;}
function radio(row,checked,handler,name){const input=document.createElement("input");input.type="radio";input.name=name;input.checked=checked;input.setAttribute("aria-label","この行を選択");input.addEventListener("change",handler);cell(row,"").append(input);row.addEventListener("dblclick",()=>{input.checked=true;handler();});}
async function ask(text,allowed=["Yes","No"]){
  const dialog=document.createElement("dialog");const p=document.createElement("p");p.textContent=text;dialog.append(p);
  const values={Yes:"はい",No:"いいえ",Cancel:"取消"};
  return await new Promise(resolve=>{
    const finish=choice=>{dialog.close();dialog.remove();resolve(choice);};
    allowed.forEach(choice=>{const b=document.createElement("button");b.type="button";b.textContent=values[choice];b.addEventListener("click",()=>finish(choice));dialog.append(b);});
    dialog.addEventListener("cancel",e=>{e.preventDefault();finish(allowed.includes("Cancel")?"Cancel":"No");});document.body.append(dialog);dialog.showModal();
  });
}
const login=$("#login-form");if(login){login.addEventListener("submit",()=>{login.querySelectorAll("button").forEach(b=>{b.disabled=true;});});}
const logout=$("#logout");if(logout)logout.addEventListener("click",()=>api("/account/logout",{confirmDiscard:true}));

const searchRoot=$("#search");
if(searchRoot){
 let vm=initial(searchRoot), selected=vm.selectedEmployeeId,epoch=0,queue=Promise.resolve(),exportOp=null,busy=false;
 const inputs=[$("#search-no"),$("#search-name"),$("#search-dep"),$("#search-status")];
 const actionButtons=()=>{$("#employee-edit").disabled=busy||!selected||vm.resultStatus!=="Success";$("#employee-export").disabled=busy||!selected||vm.resultStatus!=="Success"||!!exportOp;};
 function searchBusy(value){busy=value;inputs.forEach(i=>i.disabled=value);["#search-run","#search-clear","#employee-new"].forEach(s=>$(s).disabled=value);all("#search-rows input").forEach(i=>i.disabled=value);actionButtons();}
 function render(updateCriteria=false){
   if(updateCriteria){inputs[0].value=vm.criteria.employeeNo||"";inputs[1].value=vm.criteria.name||"";choices(inputs[2],vm.codes,"DEPARTMENT",vm.criteria.department);inputs[2].options[0].textContent="すべて";choices(inputs[3],vm.codes,"EMPLOYMENT_STATUS",vm.criteria.employmentStatus);inputs[3].options[0].textContent="すべて";}
   const body=$("#search-rows");body.replaceChildren();
   vm.rows.forEach(r=>{const tr=document.createElement("tr");if(r.employeeId===selected)tr.classList.add("selected");radio(tr,r.employeeId===selected,()=>{selected=r.employeeId;render();message("選択："+r.employeeNo+" "+r.name);},"employee");[r.employeeNo,r.name,r.kana,r.departmentName,r.employmentName,r.joinDate].forEach(v=>cell(tr,v));body.append(tr);});
   $("#search-count").textContent=vm.totalCount===null?"未検索":"検索結果："+vm.totalCount+"件";actionButtons();show(vm);
 }
 function invalidate(){
   epoch++;selected=null;vm.rows=[];vm.totalCount=null;vm.resultStatus="Unsearched";vm.outcome=null;render();
   queue=queue.then(async()=>{const r=await api("/employees/invalidate",{stateId:vm.stateId,stateRevision:vm.stateRevision});if(r.stateRevision)vm.stateRevision=r.stateRevision;}).catch(()=>message("通信を確認できません。再読込みしてください。"));
 }
 inputs.forEach(input=>input.addEventListener(input.tagName==="SELECT"?"change":"input",invalidate));
 $("#search-run").addEventListener("click",async()=>{
   if(busy)return;searchBusy(true);const requestedEpoch=epoch;
   try{await queue;const r=await api("/employees/search",{stateId:vm.stateId,stateRevision:vm.stateRevision,employeeNo:inputs[0].value,name:inputs[1].value,department:inputs[2].value,employmentStatus:inputs[3].value});
     if(r.stateRevision)vm.stateRevision=r.stateRevision;if(requestedEpoch===epoch&&r.rows){vm=r;selected=null;render();}}
   finally{searchBusy(false);}
 });
 $("#search-clear").addEventListener("click",async()=>{if(busy)return;searchBusy(true);try{epoch++;await queue;const r=await api("/employees/clear",{stateId:vm.stateId,stateRevision:vm.stateRevision});if(r.rows){vm=r;selected=null;render(true);}}finally{searchBusy(false);}});
 async function open(mode){if(busy)return;searchBusy(true);try{await queue;await api("/employees/open",{searchStateId:vm.stateId,stateRevision:vm.stateRevision,employeeId:mode==="New"?null:selected,mode});}finally{searchBusy(false);}}
 $("#employee-new").addEventListener("click",()=>open("New"));$("#employee-edit").addEventListener("click",()=>open("Edit"));
 $("#employee-export").addEventListener("click",async()=>{
   if(exportOp||busy)return;searchBusy(true);await queue;const operationId=crypto.randomUUID(),abort=new AbortController();exportOp={operationId,abort};actionButtons();$("#export-cancel").hidden=false;
   try{
     const response=await fetch("/employees/export",{method:"POST",headers:{"Content-Type":"application/json","X-SP2-CSRF":csrf(),"X-SP2-User-Action":"true"},body:JSON.stringify({searchStateId:vm.stateId,stateRevision:vm.stateRevision,employeeId:selected,operationId}),signal:abort.signal,credentials:"same-origin",cache:"no-store"});
     if(!response.ok||!response.headers.get("Content-Type")?.includes("spreadsheetml")){show(await response.json());return;}
     message("ダウンロードを開始しました。");const blob=await response.blob();
     const encoded=response.headers.get("Content-Disposition")?.match(/filename\*=UTF-8''([^;]+)/i)?.[1];const filename=encoded?decodeURIComponent(encoded):"career.xlsx";
     const url=URL.createObjectURL(blob);try{const a=document.createElement("a");a.href=url;a.download=filename;a.click();}finally{setTimeout(()=>URL.revokeObjectURL(url),1000);}
   }catch{message("ダウンロードが完了しなかった場合は、もう一度作成してください。");}
   finally{if(exportOp?.operationId===operationId){exportOp=null;$("#export-cancel").hidden=true;searchBusy(false);}}
 });
 $("#export-cancel").addEventListener("click",async()=>{const op=exportOp;if(!op)return;try{const r=await api("/employees/export/cancel",{searchStateId:vm.stateId,operationId:op.operationId});message(r.message);}finally{op.abort.abort();}});
 render(true);inputs[0].focus();
}

const editRoot=$("#edit");
if(editRoot){
 let vm=initial(editRoot),dirty=false,busy=false;const existing=!vm.isNew;
 let originalEmployee=JSON.stringify(vm.employee),originalCareers=JSON.stringify(vm.careers);
 const employeeControls=all("[data-field]");const careerControls=all("[data-career]");
 function employee(){const raw={};employeeControls.forEach(i=>raw[i.dataset.field]=["careerSummary","skills","qualifications","selfPr"].includes(i.dataset.field)&&i.value===""?null:i.value);return raw;}
 function pending(){if(!vm.pending)return null;const raw={...vm.pending};careerControls.forEach(i=>raw[i.dataset.career]=["endMonthRaw","achievements","technologies","phases"].includes(i.dataset.career)&&i.value===""?null:i.value);return raw;}
 function hasDirty(){const p=pending(),applied=p?vm.careers.find(c=>c.clientRowKey===p.clientRowKey):null;return JSON.stringify(employee())!==originalEmployee||JSON.stringify(vm.careers)!==originalCareers||(vm.removedCareerIds?.length||0)>0||!!p&&(!applied||JSON.stringify(p)!==JSON.stringify(applied));}
 function setBusy(value){busy=value;all("#edit button").forEach(b=>b.disabled=value);if(!value){$("#employee-save").disabled=!vm.canSave;$("#career-add").disabled=!vm.canAdd;$("#career-apply").disabled=!vm.pending;$("#career-remove").disabled=!vm.selectedClientRowKey||!vm.careers.some(x=>x.clientRowKey===vm.selectedClientRowKey);}}
 function tab(name){$("#basic-pane").hidden=name!=="Basic";$("#careers-pane").hidden=name!=="Careers";$("#basic-tab").setAttribute("aria-selected",String(name==="Basic"));$("#careers-tab").setAttribute("aria-selected",String(name==="Careers"));}
 function render(parent=false){
   if(parent){employeeControls.forEach(i=>{if(i.tagName==="SELECT")choices(i,vm.codes,i.dataset.field==="departmentCode"?"DEPARTMENT":"EMPLOYMENT_STATUS",vm.employee[i.dataset.field]);else i.value=vm.employee[i.dataset.field]||"";});$("#employee-no").readOnly=!vm.isNew;}
   const body=$("#career-rows");body.replaceChildren();vm.careers.forEach(c=>{const tr=document.createElement("tr");radio(tr,c.clientRowKey===vm.selectedClientRowKey,()=>draft("Select",c.clientRowKey),"career");[c.startMonthRaw+"～"+(c.endMonthRaw||"継続中"),c.companyName,c.projectName].forEach(v=>cell(tr,v));body.append(tr);});
   careerControls.forEach(i=>{if(i.tagName==="SELECT")choices(i,vm.codes,"PROJECT_ROLE",vm.pending?.roleCode);else i.value=vm.pending?.[i.dataset.career]||"";});$("#career-fields").disabled=!vm.pending;
   tab(vm.activeTab);setBusy(false);show(vm);
 }
 async function draft(action,targetClientRowKey=null,targetTab=null,confirm={kind:"None",choice:"None",confirmationId:null}){
   if(busy)return;const fields=pending();setBusy(true);
   try{
     const r=await api("/employees/draft",{editStateId:vm.editStateId,stateRevision:vm.stateRevision,action,fields,targetClientRowKey,targetTab,confirm});
     if(r.editStateId){
       const retain=r.confirmation||confirm.choice==="Cancel"||(confirm.kind==="DiscardPending"&&confirm.choice==="No")||r.outcome?.kind==="Validation";
       if(retain&&fields)r.pending=fields;
       vm=r;render();dirty=hasDirty();
     }
     if(vm.confirmation){const q=vm.confirmation;const answer=await ask(vm.outcome.message,q.allowedChoices);setBusy(false);await draft(action,targetClientRowKey,targetTab,{kind:q.kind,choice:answer,confirmationId:q.confirmationId});}
   }finally{setBusy(false);}
 }
 employeeControls.concat(careerControls).forEach(i=>i.addEventListener("input",()=>{dirty=hasDirty();i.removeAttribute("aria-invalid");}));
 $("#basic-tab").addEventListener("click",()=>draft("SwitchTab",null,"Basic"));$("#careers-tab").addEventListener("click",()=>draft("SwitchTab",null,"Careers"));
 $("#career-add").addEventListener("click",()=>draft("Add"));$("#career-apply").addEventListener("click",()=>draft("Apply"));$("#career-remove").addEventListener("click",()=>draft("Remove",vm.selectedClientRowKey));
 $("#employee-save").addEventListener("click",async()=>{
   if(busy)return;const careers=vm.careers.map(c=>({...c}));const p=pending();if(p){const index=careers.findIndex(c=>c.clientRowKey===p.clientRowKey);if(index<0)careers.push(p);else careers[index]=p;}
   const removed=(vm.removedCareerIds||[]);setBusy(true);
   try{const r=await api("/employees/save",{editStateId:vm.editStateId,stateRevision:vm.stateRevision,employee:employee(),careers,removedCareerIds:removed});if(r.editStateId){vm=r;render();if(vm.outcome?.kind==="NoChange"){originalEmployee=JSON.stringify(employee());originalCareers=JSON.stringify(vm.careers);dirty=false;}}}
   catch{message("保存結果を確認できません。再保存せず再読込みで確認してください。");vm.canSave=false;}
   finally{setBusy(false);}
 });
 async function cancel(reloadOnly){if(busy)return;if(dirty||reloadOnly){if(await ask("入力内容を破棄しますか。")!=="Yes")return;}setBusy(true);try{const r=await api("/employees/cancel",{editStateId:vm.editStateId,stateRevision:vm.stateRevision,confirmDiscard:true,reloadOnly,returnToMenu:false});if(r.editStateId){vm=r;render(true);originalEmployee=JSON.stringify(employee());originalCareers=JSON.stringify(vm.careers);dirty=false;}}finally{setBusy(false);}}
 $("#employee-cancel").addEventListener("click",()=>cancel(false));$("#employee-reload").addEventListener("click",()=>cancel(true));
 window.onbeforeunload=e=>{if(dirty){e.preventDefault();e.returnValue="";}};render(true);$(existing?"[data-field=name]":"#employee-no").focus();
}

const codeRoot=$("#codes");
if(codeRoot){
 let vm=initial(codeRoot),dirty=false,busy=false;
 function payload(){return {stateId:vm.stateId,stateRevision:vm.stateRevision,category:vm.category,code:$("#code-value").value,name:$("#code-name").value,sortOrderRaw:$("#code-sort").value,enabled:$("#code-enabled").checked,expectedRevision:vm.draft?.expectedRevision??null};}
 function render(){
   $("#code-category").value=vm.category;const body=$("#code-rows");body.replaceChildren();vm.rows.forEach(r=>{const tr=document.createElement("tr");radio(tr,r.code===vm.selectedCode,()=>open(false,r.code),"code");[r.code,r.name,String(r.sortOrder),r.enabled?"有効":"停止"].forEach(v=>cell(tr,v));body.append(tr);});
   $("#code-value").value=vm.draft?.code||"";$("#code-value").readOnly=vm.draft?.expectedRevision!=null;$("#code-name").value=vm.draft?.name||"";$("#code-sort").value=vm.draft?.sortOrderRaw||"";$("#code-enabled").checked=vm.draft?.enabled??false;$("#code-fields").disabled=!vm.draft||vm.category==="EMPLOYMENT_STATUS";$("#code-save").disabled=!vm.canSave||!vm.draft;$("#code-new").disabled=vm.category==="EMPLOYMENT_STATUS"||vm.rows.length>=99;show(vm);
 }
 async function discard(){return !dirty||await ask("入力内容を破棄しますか。")==="Yes";}
 async function open(isNew,code=null,category=vm.category){
   if(busy||!await discard()){render();return;}busy=true;
   try{const r=await api("/codes/open",{category,code,new:isNew,stateId:vm.stateId,stateRevision:vm.stateRevision});if(r.stateId){vm=r;dirty=false;render();if(isNew)$("#code-value").focus();}}
   finally{busy=false;}
 }
 $("#code-category").addEventListener("change",e=>open(false,null,e.target.value));all("#code-fields input").forEach(i=>i.addEventListener("input",()=>dirty=true));
 $("#code-new").addEventListener("click",()=>open(true));
 async function save(confirmed=false){
   if(busy)return;busy=true;
   try{const r=await api("/codes/save",payload(),confirmed?{"X-SP2-Confirm-Stop":"Yes"}:{});if(r.stateId){vm=r;render();if(vm.outcome?.messageId==="MSG-038"){const yes=await ask(vm.outcome.message);if(yes==="Yes"){busy=false;await save(true);}}else if(vm.outcome?.kind==="Success"||vm.outcome?.kind==="NoChange")dirty=false;}}
   catch{message("保存結果を確認できません。再読込みしてください。");vm.canSave=false;}
   finally{busy=false;}
 }
 $("#code-save").addEventListener("click",()=>save());
 async function cancel(menu){if(busy||!await discard())return;busy=true;try{const unknown=vm.outcome?.commitState==="Unknown";const r=await api("/codes/cancel",{stateId:vm.stateId,stateRevision:vm.stateRevision,confirmDiscard:true,reloadOnly:unknown||!menu,returnToMenu:menu});if(r.stateId){vm=r;dirty=false;render();}}finally{busy=false;}}
 $("#code-cancel").addEventListener("click",()=>cancel(false));$("#codes-menu").addEventListener("click",()=>cancel(true));window.onbeforeunload=e=>{if(dirty){e.preventDefault();e.returnValue="";}};render();
}
})();
