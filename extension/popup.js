import {hostPattern} from './policy.js';
const $=id=>document.getElementById(id);
let origin='';
async function call(action,extra={}) {
  const reply=await chrome.runtime.sendMessage({action,...extra});
  if(!reply?.ok)throw new Error(reply?.error || 'Vault did not answer.');return reply;
}
function message(text,error=false){$('message').textContent=text;$('message').classList.toggle('error',error);}
async function state(){
  const value=await call('state');origin=value.origin;
  $('site').textContent=origin;
  $('status').textContent=value.connectionError?'Not connected':value.locked?'Locked':'Unlocked';
  $('enable').hidden=value.enabled;$('accounts').hidden=!value.enabled;
  $('pending').hidden=!value.pending;
  $('username').textContent=value.pending?.username || '(no username)';
  if(value.connectionError)message(value.connectionError,true);
  else if(value.locked)message('Open the Vault app and enter your master password.');
  else message(value.enabled?'Choose an account to fill. Approve access in the desktop app if asked.':'Allow Vault on this website to save and fill logins.');
  return value;
}
async function list(){
  const reply=await call('list');$('entries').replaceChildren();
  if(!reply.entries.length){const p=document.createElement('p');p.textContent='No accounts saved for this website.';$('entries').append(p);}
  for(const entry of reply.entries){
    const row=document.createElement('div');row.className='entry';const text=document.createElement('div');text.className='text';
    const title=document.createElement('strong');title.textContent=entry.title;const user=document.createElement('small');user.textContent=entry.username;
    text.append(title,user);const button=document.createElement('button');button.textContent='Fill';
    button.onclick=()=>run(button,async()=>{await call('fill',{id:entry.id});message('Filled. Review the form and sign in when ready.');});
    row.append(text,button);$('entries').append(row);
  }
}
async function run(button,fn){button.disabled=true;try{await fn();}catch(error){message(error.message,true);}finally{button.disabled=false;}}
$('enable').onclick=()=>run($('enable'),async()=>{
  const granted=await chrome.permissions.request({origins:[hostPattern(origin)]});
  if(!granted)return;
  await call('enable');const current=await state();if(!current.locked)await list();
});
$('refresh').onclick=()=>run($('refresh'),list);
$('capture').onclick=()=>run($('capture'),async()=>{await call('capture');await new Promise(resolve=>setTimeout(resolve,100));await state();});
$('save').onclick=()=>run($('save'),async()=>{await call('save');await state();await list();message('Saved to your encrypted vault.');});
$('discard').onclick=()=>run($('discard'),async()=>{await call('discard');await state();});
state().then(value=>{if(value.enabled&&!value.locked&&!value.connectionError)return list();}).catch(error=>message(error.message,true));
