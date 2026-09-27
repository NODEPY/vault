import test from 'node:test';
import assert from 'node:assert/strict';
let removed, permission=true, timers=[];
let listener,store={allowedOrigins:['https://example.com']},current={id:1,url:'https://example.com/login'},nativeCalls=[],sent=[];
const event={addListener(){}};
global.chrome={
 runtime:{id:'extension',getURL:file=>'chrome-extension://extension/'+file,onMessage:{addListener:fn=>listener=fn},sendNativeMessage:async(_host,request)=>{nativeCalls.push(request);return request.action==='fill'?{ok:true,username:'u',password:'fake'}:{ok:true,locked:false,entries:[]};}},
 storage:{local:{get:async()=>store,set:async value=>{store={...store,...value};}}},permissions:{contains:async()=>permission,onRemoved:{addListener:fn=>removed=fn}},
 tabs:{query:async()=>[current],get:async()=>current,sendMessage:async(...args)=>{sent.push(args);return {ok:true};},onRemoved:event},
 scripting:{executeScript:async()=>{},getRegisteredContentScripts:async()=>[],registerContentScripts:async()=>{}},
 action:{setBadgeText:async()=>{},setBadgeBackgroundColor:async()=>{}}
};
// Timers must not keep a Node test process alive for candidate expiry.
global.setTimeout=(fn,ms)=>{timers.push(fn);return 1;};
await import('../background.js');
const popup={id:'extension',url:'chrome-extension://extension/popup.html'};
const send=(message,sender=popup)=>new Promise(resolve=>listener(message,sender,resolve));
test('content scripts cannot request secrets or forge the target origin',async()=>{
 const sender={id:'extension',url:'https://example.com/login',tab:{id:1},frameId:0};
 assert.equal((await send({action:'fill',id:'secret',origin:'https://evil.test'},sender)).ok,false);
 assert.equal(nativeCalls.length,0);
 assert.equal((await send({action:'list',origin:'https://evil.test'})).ok,true);
 assert.equal(nativeCalls.at(-1).origin,'https://example.com');
});
test('unapproved websites and subframes cannot save credentials',async()=>{
 assert.equal((await send({action:'candidate',username:'u',password:'p'},{id:'extension',url:'https://evil.test/',tab:{id:1},frameId:0})).ok,false);
 assert.equal((await send({action:'candidate',username:'u',password:'p'},{id:'extension',url:'https://example.com/',tab:{id:1},frameId:3})).ok,false);
 current={id:1,url:'https://evil.test/'};assert.equal((await send({action:'list'})).ok,false);current={id:1,url:'https://example.com/'};
});
test('candidate passwords remain memory-only and clear after save',async()=>{
 assert.equal((await send({action:'candidate',username:'u',password:'fake-memory-secret'},{id:'extension',url:current.url,tab:{id:1,title:'Demo'},frameId:0})).ok,true);
 assert.equal(JSON.stringify(store).includes('fake-memory-secret'),false);
 const state=await send({action:'state'});assert.deepEqual(state.pending,{username:'u'});assert.equal(JSON.stringify(state).includes('fake-memory-secret'),false);
 assert.equal((await send({action:'save'})).ok,true);assert.equal(nativeCalls.at(-1).password,'fake-memory-secret');assert.equal((await send({action:'state'})).pending,null);
});
test('a page navigation during native approval prevents filling',async()=>{
 chrome.runtime.sendNativeMessage=async()=>{current={id:1,url:'https://evil.test'};return {ok:true,username:'u',password:'p'};};
 assert.equal((await send({action:'fill',id:'id'})).ok,false);assert.equal(sent.length,0);
});

test('old expiry cannot erase a newer candidate and revoked permission clears it',async()=>{
 current={id:1,url:'https://example.com/'};
 chrome.runtime.sendNativeMessage=async()=>({ok:true,locked:false});
 const sender={id:'extension',url:current.url,tab:{id:1},frameId:0};
 await send({action:'candidate',username:'old',password:'fake'},sender);
 const oldTimer=timers.at(-1);
 await send({action:'candidate',username:'new',password:'fake'},sender);
 oldTimer();assert.deepEqual((await send({action:'state'})).pending,{username:'new'});
 permission=false;await removed();assert.equal((await send({action:'state'})).pending,null);
});
