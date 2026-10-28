<script setup lang="ts">
import { onMounted,onBeforeUnmount,ref } from 'vue';
defineProps<{title:string;labelId:string;busy?:boolean}>();const emit=defineEmits<{cancel:[]}>();
const dialog=ref<HTMLDialogElement|null>(null);let trigger:HTMLElement|null=null;
onMounted(()=>{trigger=document.activeElement as HTMLElement;dialog.value?.showModal();dialog.value?.querySelector<HTMLButtonElement>('[data-cancel]')?.focus();});
onBeforeUnmount(()=>{dialog.value?.close();if(trigger?.isConnected)trigger.focus();});
function key(event:KeyboardEvent){if(event.key==='Enter'&&(event.target as HTMLElement).tagName!=='TEXTAREA'&&(event.target as HTMLElement).tagName!=='BUTTON')event.preventDefault();}
</script>
<template><dialog ref="dialog" class="modal-dialog" :aria-labelledby="labelId" @cancel.prevent="!busy&&emit('cancel')" @keydown="key"><h2 :id="labelId">{{title}}</h2><div class="dialog-content"><slot/></div></dialog></template>
