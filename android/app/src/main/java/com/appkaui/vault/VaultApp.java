package com.appkaui.vault;
import android.app.Application;
import android.os.Handler;
import android.os.Looper;

public class VaultApp extends Application {
    VaultStore store;
    final Handler handler=new Handler(Looper.getMainLooper());
    Runnable onLock;
    final Runnable idle=()->{store.lock();if(onLock!=null)onLock.run();};
    @Override public void onCreate(){super.onCreate();store=new VaultStore(this);}
    void touch(){handler.removeCallbacks(idle);handler.postDelayed(idle,5*60*1000);}
    void lock(){handler.removeCallbacks(idle);store.lock();}
}
