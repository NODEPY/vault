import test from 'node:test';
import assert from 'node:assert/strict';
import {originOf,hostPattern,validCandidate} from '../policy.js';
test('HTTPS origins are exact, with explicit non-default ports',()=>{
 assert.equal(originOf('https://EXAMPLE.com:443/login'),'https://example.com');
 assert.equal(originOf('https://example.com:444/login'),'https://example.com:444');
 for(const value of ['http://example.com','file:///passwords','https://user:pass@example.com','javascript:alert(1)']) assert.throws(()=>originOf(value));
 assert.equal(hostPattern('https://example.com:444'),'https://example.com/*');
});
test('Only bounded string credentials are accepted',()=>{
 assert.ok(validCandidate({username:'demo',password:'fake'}));
 for(const value of [{username:5,password:'p'},{username:'u',password:''},{username:'u',password:'a'.repeat(4097)}])assert.equal(validCandidate(value),false);
});
