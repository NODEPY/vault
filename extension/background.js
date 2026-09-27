import {originOf, hostPattern, validCandidate} from './policy.js';
const HOST = 'com.appkaui.vault';
const pending = new Map();
const popupUrl = chrome.runtime.getURL('popup.html');
async function allowed(origin) {
  const {allowedOrigins = []} = await chrome.storage.local.get('allowedOrigins');
  return allowedOrigins.includes(origin) && await chrome.permissions.contains({origins:[hostPattern(origin)]});
}
async function active() {
  const [tab] = await chrome.tabs.query({active:true,currentWindow:true});
  if (!tab?.id || !tab.url) throw new Error('Open an HTTPS website.');
  return {tab, origin:originOf(tab.url)};
}
async function native(message) {
  try {
    const reply = await chrome.runtime.sendNativeMessage(HOST,message);
    if (!reply?.ok) throw new Error(reply?.error || 'Vault did not answer.');
    return reply;
  } catch (error) {
    throw new Error(error.message.includes('host') ? 'Open Vault → Tools → Connect Chrome, then unlock your vault.' : error.message);
  }
}
function getPending(tabId, origin) {
  const value = pending.get(tabId);
  if (!value || value.origin !== origin || performance.now()-value.time > 120000) {
    pending.delete(tabId); chrome.action.setBadgeText({tabId,text:''}); return null;
  }
  return value;
}
async function capture(message, sender) {
  if (!sender.tab?.id || sender.frameId !== 0 || !validCandidate(message)) return {ok:false};
  const origin = originOf(sender.url);
  if (!(await allowed(origin))) return {ok:false};
  const candidate={origin,username:message.username,password:message.password,title:sender.tab.title || new URL(origin).hostname,time:performance.now()};
  pending.set(sender.tab.id,candidate);
  await chrome.action.setBadgeText({tabId:sender.tab.id,text:'+'});
  await chrome.action.setBadgeBackgroundColor({color:'#315f46'});
  const tabId=sender.tab.id;
  setTimeout(()=>{if(pending.get(tabId)===candidate){pending.delete(tabId);chrome.action.setBadgeText({tabId,text:''});}},120000);
  return {ok:true};
}
async function register(origin) {
  if (!(await chrome.permissions.contains({origins:[hostPattern(origin)]}))) throw new Error('Site permission is required.');
  const {allowedOrigins=[]}=await chrome.storage.local.get('allowedOrigins');
  await chrome.storage.local.set({allowedOrigins:[...new Set([...allowedOrigins,origin])]});
  const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(origin));
  const id='vault-'+[...new Uint8Array(bytes)].map(b=>b.toString(16).padStart(2,'0')).join('').slice(0,24);
  const scripts=await chrome.scripting.getRegisteredContentScripts({ids:[id]});
  if (!scripts.length) await chrome.scripting.registerContentScripts([{id,js:['content.js'],matches:[hostPattern(origin)],allFrames:false,runAt:'document_idle',persistAcrossSessions:true}]);
}
async function handle(message, sender) {
  if (sender.id !== chrome.runtime.id) throw new Error('Invalid sender.');
  if (message?.action === 'candidate') return capture(message,sender);
  if (sender.url !== popupUrl) throw new Error('Use the Vault popup for this action.');
  const {tab,origin}=await active();
  if (message.action==='enable') {
    await register(origin);
    await chrome.scripting.executeScript({target:{tabId:tab.id,frameIds:[0]},files:['content.js']});
    return {ok:true};
  }
  if (message.action==='state') {
    let locked=true,connectionError='';
    try { locked=(await native({action:'status'})).locked; } catch(error) {connectionError=error.message;}
    const candidate=getPending(tab.id,origin);
    return {ok:true,origin,enabled:await allowed(origin),locked,connectionError,pending:candidate?{username:candidate.username}:null};
  }
  if (!(await allowed(origin))) throw new Error('Enable Vault on this site first.');
  if (message.action==='list') return native({action:'list',origin});
  if (message.action==='fill') {
    if (typeof message.id!=='string') throw new Error('Select an account.');
    const result=await native({action:'fill',origin,id:message.id});
    const current=await chrome.tabs.get(tab.id);
    if (originOf(current.url)!==origin) throw new Error('The page changed. Try again.');
    await chrome.scripting.executeScript({target:{tabId:tab.id,frameIds:[0]},files:['content.js']});
    const reply=await chrome.tabs.sendMessage(tab.id,{action:'fill',origin,username:result.username,password:result.password},{frameId:0});
    if (!reply?.ok) throw new Error(reply?.error || 'No safe login form found.');
    return {ok:true};
  }
  if (message.action==='capture') {
    await chrome.scripting.executeScript({target:{tabId:tab.id,frameIds:[0]},files:['content.js']});
    const reply=await chrome.tabs.sendMessage(tab.id,{action:'capture',origin},{frameId:0});
    if (!reply?.ok) throw new Error('Enter a username and password in a visible login form first.');
    return reply;
  }
  if (message.action==='save') {
    const candidate=getPending(tab.id,origin);
    if (!candidate) throw new Error('The captured login expired. Capture the form again.');
    const reply=await native({action:'save',origin,username:candidate.username,password:candidate.password,title:candidate.title});
    if(pending.get(tab.id)===candidate){pending.delete(tab.id);await chrome.action.setBadgeText({tabId:tab.id,text:''});}return reply;
  }
  if (message.action==='discard') {
    pending.delete(tab.id);await chrome.action.setBadgeText({tabId:tab.id,text:''});return {ok:true};
  }
  throw new Error('Unknown action.');
}
chrome.runtime.onMessage.addListener((message,sender,sendResponse)=>{
  handle(message,sender).then(sendResponse).catch(error=>sendResponse({ok:false,error:error.message}));return true;
});
chrome.tabs.onRemoved.addListener(id=>pending.delete(id));
chrome.permissions.onRemoved.addListener(async()=>{
  const {allowedOrigins=[]}=await chrome.storage.local.get('allowedOrigins');
  const remaining=[];
  for (const origin of allowedOrigins) if(await allowed(origin)) remaining.push(origin);
  await chrome.storage.local.set({allowedOrigins:remaining});
  for(const [tabId,candidate] of pending){if(!remaining.includes(candidate.origin)){pending.delete(tabId);await chrome.action.setBadgeText({tabId,text:''});}}
});
