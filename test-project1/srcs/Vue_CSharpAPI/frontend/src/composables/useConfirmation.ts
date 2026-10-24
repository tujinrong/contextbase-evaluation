import { shallowRef } from 'vue';
export const confirmation = shallowRef<{message:string;resolve:(answer:boolean)=>void}|null>(null);
export function askConfirmation(message:string):Promise<boolean>{
  return new Promise(resolve=>{confirmation.value?.resolve(false);confirmation.value={message,resolve};});
}
export function answerConfirmation(answer:boolean){const pending=confirmation.value;confirmation.value=null;pending?.resolve(answer);}
