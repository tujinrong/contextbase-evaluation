import { computed,reactive,ref } from 'vue';
import { ApiFailure,setCsrfToken } from '../api/apiClient';
import { studentApi } from '../api/studentApi';
import { clone,initialCriteria,type ApiError,type Bootstrap,type Lookups,type SearchResult } from '../api/contracts';
export function useStudentSearch(){
  const draft=reactive(initialCriteria()),bootstrap=ref<Bootstrap|null>(null),lookups=ref<Lookups>({codes:[],classes:[],years:[]}),result=ref<SearchResult|null>(null),busy=ref(false),error=ref<ApiError|null>(null),message=ref(''),pageSize=ref(20),sortKey=ref('studentNo'),sortDirection=ref('asc');
  const signature=(c:ReturnType<typeof initialCriteria>)=>JSON.stringify([c.studentNo,c.name,c.classId,[...c.statusCodes].sort()]);
  const changed=computed(()=>!!result.value&&result.value.outcome!=='unsearched'&&signature(draft)!==signature(result.value.criteria));
  let sequence=0,bootstrapSequence=0,bootstrapAbort:AbortController|null=null;
  async function run(operation:()=>Promise<SearchResult>){
    if(busy.value)return;busy.value=true;error.value=null;const own=++sequence;
    try{const value=await operation();if(own!==sequence)return;result.value=value;
      if(bootstrap.value)bootstrap.value.contextRevision=value.contextRevision;
      pageSize.value=value.pageSize;sortKey.value=value.sortKey;sortDirection.value=value.sortDirection;
      if(value.outcome==='unsearched')Object.assign(draft,initialCriteria());
      message.value=value.message|| (value.outcome==='tooMany'?'10,000件を超えました。条件を追加してください。':value.outcome==='empty'?'該当する学生はありません。':'');
    }catch(e){result.value=null;if(e instanceof ApiFailure&&e.status===409&&e.detail.messageId==='W-SRC-002'){Object.assign(draft,initialCriteria());pageSize.value=20;sortKey.value='studentNo';sortDirection.value='asc';await initialize();message.value='検索状態の期限が切れたため初期化しました。条件を再指定してください。';}else error.value=e instanceof ApiFailure?e.detail:{outcome:'systemError',messageId:'E-COM-004',message:'検索できませんでした。',fieldErrors:{},correlationId:'',retryBySearch:false};}
    finally{if(own===sequence)busy.value=false;}
  }
  async function initialize(){bootstrapAbort?.abort();bootstrapAbort=new AbortController();const own=++bootstrapSequence;busy.value=true;try{const value=await studentApi.bootstrap(bootstrapAbort.signal);if(own!==bootstrapSequence)return;bootstrap.value=value;setCsrfToken(value.csrfToken);lookups.value=value;}catch(e){if(own===bootstrapSequence&&e instanceof ApiFailure)error.value=e.detail;}finally{if(own===bootstrapSequence)busy.value=false;}}
  async function search(){const b=bootstrap.value;if(b)await run(()=>studentApi.search(b.contextId,b.contextRevision,clone(draft),pageSize.value,sortKey.value,sortDirection.value));}
  async function page(target:number){const b=bootstrap.value;if(b&&result.value?.outcome==='found')await run(()=>studentApi.page(b.contextId,b.contextRevision,target,pageSize.value,sortKey.value,sortDirection.value));}
  async function clear(){const b=bootstrap.value;if(b)await run(()=>studentApi.clear(b.contextId,b.contextRevision));}
  async function resume(){const b=bootstrap.value;if(b)await run(()=>studentApi.resume(b.contextId,b.contextRevision));}
  return{draft,bootstrap,lookups,result,busy,error,message,pageSize,sortKey,sortDirection,changed,initialize,search,page,clear,resume};
}
