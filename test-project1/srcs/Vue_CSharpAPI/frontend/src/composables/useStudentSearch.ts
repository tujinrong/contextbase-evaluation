import { computed, reactive, ref } from 'vue';
import { ApiFailure, setCsrfToken } from '../api/apiClient';
import { studentApi } from '../api/studentApi';
import { clone, initialCriteria, type ApiError, type Bootstrap, type Lookups, type SearchResult } from '../api/contracts';
export function useStudentSearch() {
  const draft=reactive(initialCriteria()), bootstrap=ref<Bootstrap|null>(null),lookups=ref<Lookups>({codes:[],classes:[],years:[]}),result=ref<SearchResult|null>(null),busy=ref(false),error=ref<ApiError|null>(null),message=ref(''),pageSize=ref(20),sortKey=ref('studentNo'),sortDirection=ref('asc');
  const changed=computed(()=>result.value!==null&&JSON.stringify(draft)!==JSON.stringify(result.value.criteria));
  let sequence=0,lookupSequence=0,lookupAbort:AbortController|null=null;
  async function run(operation:()=>Promise<SearchResult>) { if(busy.value)return;busy.value=true;error.value=null;const own=++sequence;try {const value=await operation();if(own!==sequence)return;result.value=value;if(bootstrap.value){bootstrap.value.contextRevision=value.contextRevision;}message.value=value.outcome==='tooMany'?'10,000件を超えました。条件を追加してください。':value.outcome==='empty'?'該当する学生はありません。':'';}catch(e){if(e instanceof ApiFailure)error.value=e.detail;else error.value={outcome:'systemError',messageId:'E-COM-004',message:'検索できませんでした。',fieldErrors:{},correlationId:'',retryBySearch:false};result.value=null;}finally{if(own===sequence)busy.value=false;} }
  async function initialize(){busy.value=true;try{bootstrap.value=await studentApi.bootstrap();setCsrfToken(bootstrap.value.csrfToken);lookups.value=bootstrap.value;}catch(e){if(e instanceof ApiFailure)error.value=e.detail;}finally{busy.value=false;} }
  async function search(){const b=bootstrap.value;if(!b)return;await run(()=>studentApi.search(b.contextId,b.contextRevision,clone(draft),pageSize.value,sortKey.value,sortDirection.value));}
  async function page(target:number){const b=bootstrap.value;if(!b||!result.value||result.value.outcome==='tooMany')return;await run(()=>studentApi.page(b.contextId,b.contextRevision,target,pageSize.value,sortKey.value,sortDirection.value));}
  async function clear(){const b=bootstrap.value;if(!b)return;await run(()=>studentApi.clear(b.contextId,b.contextRevision));if(!error.value){Object.assign(draft,initialCriteria());pageSize.value=20;sortKey.value='studentNo';sortDirection.value='asc';message.value='';}}
  async function resume(){const b=bootstrap.value;if(!b)return;await run(()=>studentApi.resume(b.contextId,b.contextRevision));}
  async function options(){lookupAbort?.abort();lookupAbort=new AbortController();const own=++lookupSequence;try{const found=await studentApi.options({usage:'search',schoolYear:draft.schoolYear,gradeCode:draft.gradeCode},lookupAbort.signal);if(own===lookupSequence){lookups.value=found;if(draft.classId&&!found.classes.some(c=>c.classId===draft.classId)){draft.classId=null;message.value='上位条件に合わないクラスを解除しました。';}}}catch(e){if(own===lookupSequence&&e instanceof ApiFailure)error.value=e.detail;} }
  function unassigned(){if(draft.unassignedOnly){draft.schoolYear=null;draft.gradeCode=null;draft.classId=null;} }
  return {draft,bootstrap,lookups,result,busy,error,message,pageSize,sortKey,sortDirection,changed,initialize,search,page,clear,resume,options,unassigned};
}
