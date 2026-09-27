(() => {
  if (window.top !== window || globalThis.__vaultCompanion) return;
  globalThis.__vaultCompanion=true;
  function visible(input) {
    const style=getComputedStyle(input),rect=input.getBoundingClientRect();
    for(let element=input.parentElement;element;element=element.parentElement){
      const ancestor=getComputedStyle(element);
      if(ancestor.display==='none'||ancestor.visibility==='hidden'||Number(ancestor.opacity)===0)return false;
    }
    return !input.disabled && !input.readOnly && input.type!=='hidden' && style.visibility!=='hidden' && style.display!=='none' && Number(style.opacity)!==0 && rect.width>0 && rect.height>0 && rect.bottom>0 && rect.right>0 && rect.top<innerHeight && rect.left<innerWidth;
  }
  function formFields(root=document) {
    const passwords=[...root.querySelectorAll('input[type="password"]')].filter(visible);
    const password=passwords.find(input=>input.autocomplete==='current-password') || passwords[0];
    if (!password) return null;
    const form=password.form;
    if (form && new URL(form.action || location.href,location.href).origin!==location.origin) return null;
    const scope=form || root;
    const fields=[...scope.querySelectorAll('input')].filter(input=>visible(input)&&['text','email','tel'].includes(input.type)&&input.autocomplete!=='one-time-code');
    const username=fields.find(input=>['username','email'].includes(input.autocomplete)) || fields.filter(input=>input.compareDocumentPosition(password)&Node.DOCUMENT_POSITION_FOLLOWING).at(-1);
    return {password,username};
  }
  async function capture(root=document) {
    const fields=formFields(root);
    if (!fields || !fields.password.value) return false;
    try {const result=await chrome.runtime.sendMessage({action:'candidate',username:fields.username?.value || '',password:fields.password.value});return result?.ok===true;} catch{return false;}
  }
  document.addEventListener('submit',event=>{
    if (event.isTrusted && event.target instanceof HTMLFormElement) capture(event.target);
  },true);
  chrome.runtime.onMessage.addListener((message,sender,respond)=>{
    if(sender.id!==chrome.runtime.id || message.origin!==location.origin || location.protocol!=='https:') return;
    if(message.action==='capture') {capture().then(ok=>respond({ok}));return true;}
    if(message.action!=='fill') return;
    const fields=formFields();
    if(!fields) {respond({ok:false,error:'No visible same-origin login form found.'});return;}
    const set=(input,value)=>{
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input,value);
      input.dispatchEvent(new Event('input',{bubbles:true}));
      input.dispatchEvent(new Event('change',{bubbles:true}));
    };
    if(fields.username) set(fields.username,message.username);
    set(fields.password,message.password);
    respond({ok:true});
    // Never submit a form on the user's behalf.
  });
})();
