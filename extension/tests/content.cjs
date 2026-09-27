// Requires Playwright and its Chromium browser, or CHROMIUM_EXECUTABLE.
const {chromium}=require('playwright');
const path=require('node:path');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_EXECUTABLE||undefined});
 const page=await browser.newPage();
 await page.route('https://vault-test.example/**',route=>route.fulfill({contentType:'text/html',body:`<form action='/login'><input id='user' autocomplete='username'><input id='password' type='password' autocomplete='current-password'><button>Sign in</button></form><input id='hidden' type='password' style='display:none'>`}));
 await page.goto('https://vault-test.example/login');
 await page.evaluate(()=>{window.candidates=[];window.chrome={runtime:{id:'test-extension',onMessage:{addListener:fn=>window.listener=fn},sendMessage:async value=>{window.candidates.push(value);return {ok:true};}}};window.submitted=false;document.querySelector('form').addEventListener('submit',e=>{e.preventDefault();window.submitted=true;});});
 await page.addScriptTag({path:path.resolve(__dirname,'../content.js')});
 const send=message=>page.evaluate(message=>new Promise(resolve=>{window.listener(message,{id:'test-extension'},resolve);}),{origin:'https://vault-test.example',...message});
 assert.deepEqual(await send({action:'fill',username:'demo',password:'fake-test-password'}),{ok:true});
 assert.equal(await page.inputValue('#user'),'demo');assert.equal(await page.inputValue('#password'),'fake-test-password');assert.equal(await page.inputValue('#hidden'),'');assert.equal(await page.evaluate(()=>window.submitted),false);
 assert.deepEqual(await send({action:'capture'}),{ok:true});assert.equal(await page.evaluate(()=>window.candidates[0].password),'fake-test-password');
 await page.evaluate(()=>{document.querySelector('form').action='https://evil.example/login';});
 assert.equal((await send({action:'fill',username:'bad',password:'bad'})).ok,false);
 assert.equal(await page.inputValue('#password'),'fake-test-password');
 await page.evaluate(()=>{document.querySelector('form').action='/login';document.querySelector('#password').style.display='none';});
 assert.equal((await send({action:'fill',username:'bad',password:'bad'})).ok,false);
 await page.evaluate(()=>{document.querySelector('#password').style.display='';document.querySelector('form').style.opacity='0';});
 assert.equal((await send({action:'fill',username:'bad',password:'bad'})).ok,false);
 await browser.close();console.log('PASS: visible fields, exact origin, cross-origin form rejection, capture, no auto-submit');
})().catch(e=>{console.error(e);process.exit(1);});
