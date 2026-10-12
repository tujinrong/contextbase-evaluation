import { onMounted, onUnmounted, type Ref } from 'vue';
export function useDirtyGuard(dirty:Ref<boolean>){const unload=(e:BeforeUnloadEvent)=>{if(dirty.value){e.preventDefault();e.returnValue='';}};onMounted(()=>window.addEventListener('beforeunload',unload));onUnmounted(()=>window.removeEventListener('beforeunload',unload));return ()=>!dirty.value||window.confirm('保存していない変更を破棄しますか。');}
