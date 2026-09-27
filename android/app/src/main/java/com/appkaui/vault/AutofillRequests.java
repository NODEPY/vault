package com.appkaui.vault;
import android.view.autofill.AutofillId;
import android.os.SystemClock;
import java.util.*;

final class AutofillRequests {
    static final Map<String,Request> requests=new HashMap<>();
    static final class Request {
        String pkg,signature,label;
        AutofillId username,password;
        long created=SystemClock.elapsedRealtime();
    }
    static synchronized String put(Request request){
        requests.entrySet().removeIf(e->SystemClock.elapsedRealtime()-e.getValue().created>120000);
        String key=UUID.randomUUID().toString();requests.put(key,request);return key;
    }
    static synchronized Request get(String key){Request r=requests.get(key);return r!=null&&SystemClock.elapsedRealtime()-r.created<120000?r:null;}
    static synchronized void remove(String key){requests.remove(key);}
}
