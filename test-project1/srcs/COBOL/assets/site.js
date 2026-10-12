"use strict";
let dirty=false;const editor=document.querySelector("form.editor");
editor?.addEventListener("input",()=>dirty=true);editor?.addEventListener("change",()=>dirty=true);
window.addEventListener("beforeunload",e=>{if(dirty){e.preventDefault();e.returnValue="";}});
for(const form of document.forms)form.addEventListener("submit",e=>{
 const text=form.dataset.confirm||(form.dataset.leave&&dirty?"変更を破棄して戻りますか。":null);
 if(text&&!window.confirm(text)){e.preventDefault();return;}
 dirty=false;setTimeout(()=>{for(const b of form.querySelectorAll("button"))b.disabled=true;},0);
});
document.querySelector(".cancel-duplicate")?.addEventListener("click",()=>{
 document.querySelector('[name="confirmationToken"]')?.remove();document.querySelector(".duplicates")?.remove();
});
const unassigned=document.querySelector('[name="unassignedOnly"]');
const upper=["schoolYear","gradeCode","classId"];
function assignControls(){if(!unassigned)return;for(const name of upper){const el=document.querySelector(`[name="${name}"]`);if(el){el.disabled=unassigned.checked;if(unassigned.checked)el.value="";}}}
unassigned?.addEventListener("change",assignControls);assignControls();
for(const name of ["schoolYear","gradeCode"])document.querySelector(`form.editor [name="${name}"]`)?.addEventListener("change",()=>{const c=document.querySelector('form.editor [name="classId"]');if(c)c.value="";});
