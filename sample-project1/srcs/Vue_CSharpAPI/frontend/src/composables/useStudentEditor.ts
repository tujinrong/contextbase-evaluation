import { computed, ref, watch } from 'vue';
import { studentApi } from '../api/studentApi';
import { ApiFailure } from '../api/apiClient';
import { clone, type ApiError, type SaveResult, type StudentEditData } from '../api/contracts';
export function useStudentEditor(){const data=ref<StudentEditData|null>(null),original=ref(''),busy=ref(false),error=ref<ApiError|null>(null),message=ref(''),duplicate=ref<SaveResult|null>(null);const withoutToken=(f:StudentEditData['form'])=>JSON.stringify({...f,duplicateToken:null});const dirty=computed(()=>!!data.value&&withoutToken(data.value.form)!==original.value);let lookupSeq=0,loadSeq=0,abort:AbortController|null=null,loadAbort:AbortController|null=null;
  const fail=(e:unknown)=>{if(e instanceof ApiFailure){error.value=e.detail;if(e.detail.outcome==='confirmationRequired'){duplicate.value=e.detail as SaveResult;if(data.value)data.value.form.duplicateToken=String(e.detail.duplicateToken);}}else{error.value={outcome:'systemError',messageId:'E-COM-004',message:'処理できませんでした。',fieldErrors:{},correlationId:'',retryBySearch:true};}};
  async function load(id:string|null,context:string):Promise<boolean>{
    abort?.abort();++lookupSeq;loadAbort?.abort();loadAbort=new AbortController();const own=++loadSeq;
    busy.value=true;error.value=null;
    try{const loaded=await studentApi.get(id,context,loadAbort.signal);if(own!==loadSeq)return false;data.value=loaded;original.value=withoutToken(loaded.form);duplicate.value=null;return true;}
    catch(e){if(own===loadSeq&&!(e instanceof DOMException&&e.name==='AbortError'))fail(e);return false;}
    finally{if(own===loadSeq)busy.value=false;}
  }
  async function save(reason?:string):Promise<boolean>{if(!data.value||busy.value)return false;busy.value=true;error.value=null;if(reason)data.value.form.operationReason=reason;try{const r=await studentApi.save(data.value.studentId,clone(data.value.form));message.value=r.message||'';if(r.outcome==='saved'){original.value=withoutToken(data.value.form);duplicate.value=null;return true;}if(r.outcome==='noChange'){message.value='変更はありません。';original.value=withoutToken(data.value.form);duplicate.value=null;}return false;}catch(e){if(e instanceof ApiFailure&&e.detail.outcome!=='confirmationRequired')duplicate.value=null;fail(e);return false;}finally{busy.value=false;} }
  async function remove(reason:string):Promise<boolean>{const d=data.value;if(!d?.studentId||!d.form.expectedVersion||busy.value)return false;busy.value=true;error.value=null;try{const r=await studentApi.remove(d.studentId,d.form.expectedVersion,reason,d.form.returnContextId||'');if(r.outcome==='saved'){original.value=withoutToken(d.form);return true;}return false;}catch(e){fail(e);return false;}finally{busy.value=false;} }
  function reset(){if(!data.value)return;data.value.form=JSON.parse(original.value) as StudentEditData['form'];duplicate.value=null;error.value=null;message.value='入力を読込時の値へ戻しました。';}
  async function options(){if(!data.value)return;abort?.abort();abort=new AbortController();const own=++lookupSeq;const d=data.value;try{const found=await studentApi.options({usage:'register',schoolYear:d.form.schoolYear,gradeCode:d.form.gradeCode,studentId:d.studentId,enrollmentStatusCode:d.form.enrollmentStatusCode,admissionDate:d.form.admissionDate,enrollmentEndDate:d.form.enrollmentEndDate},abort.signal);if(own===lookupSeq){d.codes=found.codes;d.classes=found.classes;d.years=found.years;if(d.form.classId&&!found.classes.some(c=>c.classId===d.form.classId)){d.form.classId=null;message.value='年度・学年に合わないクラスを解除しました。';}}}catch(e){if(own===lookupSeq&&e instanceof ApiFailure)fail(e);} }
  function cancelDuplicate(){duplicate.value=null;if(data.value)data.value.form.duplicateToken=null;error.value=null;}
  watch(()=>data.value?JSON.stringify({...data.value.form,duplicateToken:null,operationReason:null,schoolYear:null,gradeCode:null}):'',()=>{if(data.value)data.value.form.duplicateToken=null;});
  return {data,dirty,busy,error,message,duplicate,load,save,remove,reset,options,cancelDuplicate};
}
