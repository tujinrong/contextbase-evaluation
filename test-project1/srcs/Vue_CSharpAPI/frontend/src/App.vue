<script setup lang="ts">
import { onMounted,onUnmounted,ref } from 'vue';import StudentSearchPage from './pages/StudentSearchPage.vue';import StudentEditPage from './pages/StudentEditPage.vue';import { useStudentSearch } from './composables/useStudentSearch';import { useStudentEditor } from './composables/useStudentEditor';import { useDirtyGuard } from './composables/useDirtyGuard';const search=useStudentSearch(),editor=useStudentEditor(),editing=ref(false);const canLeave=useDirtyGuard(editor.dirty);
async function open(id:string|null){const b=search.bootstrap.value;if(!b||search.busy.value)return;await editor.load(id,b.contextId);if(editor.data.value){editing.value=true;history.pushState({editing:true},'',id?`/students/${encodeURIComponent(id)}`:'/students/new');}}
async function back(saved=false){if(!saved&&!canLeave())return;editing.value=false;editor.data.value=null;history.replaceState({},'','/students');await search.resume();}
const pop=()=>{if(editing.value){if(canLeave())void back(true);else history.pushState({editing:true},'',location.pathname);} };
onMounted(async()=>{await search.initialize();history.replaceState({},'','/students');window.addEventListener('popstate',pop);});onUnmounted(()=>window.removeEventListener('popstate',pop));
</script>
<template><header><strong>学生管理システム</strong><span>利用者 {{search.bootstrap.value?.user||'未認証'}}　業務日 {{search.bootstrap.value?.businessDate||'－'}}</span></header><main><StudentSearchPage v-if="!editing" :state="search" @open="open"/><StudentEditPage v-else :state="editor" @back="back()" @saved="back(true)"/></main></template>
