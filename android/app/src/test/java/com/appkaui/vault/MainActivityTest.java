package com.appkaui.vault;
import org.junit.*;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;
import org.robolectric.*;
import org.robolectric.android.controller.ActivityController;
import org.robolectric.annotation.Config;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.util.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk=35)
public class MainActivityTest {
    VaultApp app;
    @Before public void prepare()throws Exception{
        app=(VaultApp)RuntimeEnvironment.getApplication();app.store.reset();app.getSharedPreferences("preferences",0).edit().clear().commit();
    }
    private static <T extends View> List<T> views(View root,Class<T> type){
        List<T> result=new ArrayList<>();if(type.isInstance(root))result.add(type.cast(root));
        if(root instanceof ViewGroup){ViewGroup group=(ViewGroup)root;for(int i=0;i<group.getChildCount();i++)result.addAll(views(group.getChildAt(i),type));}return result;
    }
    private View root(MainActivity activity){return activity.findViewById(android.R.id.content);}
    private void click(MainActivity activity,String label){Button button=views(root(activity),Button.class).stream().filter(v->label.equals(v.getText().toString())).findFirst().orElseThrow();button.performClick();}
    private boolean text(MainActivity activity,String label){return views(root(activity),TextView.class).stream().anyMatch(v->label.equals(v.getText().toString()));}
    @Test public void englishOnboardingThenCreateScreen(){
        try(ActivityController<MainActivity> controller=Robolectric.buildActivity(MainActivity.class).setup()){
            MainActivity activity=controller.get();assertTrue(text(activity,"Welcome to Vault"));click(activity,"Continue");assertTrue(text(activity,"Create your vault"));assertEquals(2,views(root(activity),EditText.class).size());
            assertTrue((activity.getWindow().getAttributes().flags&WindowManager.LayoutParams.FLAG_SECURE)!=0);
        }
    }
    @Test public void addEditAndStopLocks()throws Exception{
        app.getSharedPreferences("preferences",0).edit().putBoolean("setup",true).commit();app.store.create("test-only-long-master");
        try(ActivityController<MainActivity> controller=Robolectric.buildActivity(MainActivity.class).setup()){
            MainActivity activity=controller.get();click(activity,"+ Add entry");List<EditText> inputs=views(root(activity),EditText.class);assertEquals(4,inputs.size());
            inputs.get(0).setText("Demo");inputs.get(1).setText("demo-user");inputs.get(2).setText("https://example.com/login");inputs.get(3).setText("fake-password");click(activity,"Save");
            assertEquals(1,app.store.entries().length());assertEquals("https://example.com",app.store.entries().getJSONObject(0).getString("url"));assertTrue(text(activity,"Demo"));
            controller.pause().stop();assertFalse(app.store.unlocked());
        }
    }
    @Test public void everyLanguageAndThemeCanOpenSettings(){
        String[] languages={"en","uk","pl","de","es"},themes={"dark","light","sand","forest","midnight"};
        for(int i=0;i<languages.length;i++){
            app.getSharedPreferences("preferences",0).edit().putString("language",languages[i]).putString("theme",themes[i]).commit();
            try(ActivityController<MainActivity> controller=Robolectric.buildActivity(MainActivity.class).setup()){
                assertEquals(2,views(root(controller.get()),Spinner.class).size());
            }
        }
    }
    @Test public void failedImportPreservesFileAndResetAllowsNewMaster()throws Exception{
        app.store.create("first-long-test-master");byte[] before=java.nio.file.Files.readAllBytes(app.store.file.toPath());
        assertThrows(Exception.class,()->app.store.importBackup(before,"wrong"));assertArrayEquals(before,java.nio.file.Files.readAllBytes(app.store.file.toPath()));
        app.store.reset();assertFalse(app.store.exists());app.store.create("another-long-test-master");app.store.lock();app.store.open("another-long-test-master");assertEquals(0,app.store.entries().length());
    }
    @Test @org.robolectric.annotation.GraphicsMode(org.robolectric.annotation.GraphicsMode.Mode.NATIVE)
    @Config(sdk=35,qualifiers="w400dp-h840dp-xhdpi")
    public void renderMobilePreview()throws Exception{
        app.getSharedPreferences("preferences",0).edit().putBoolean("setup",true).commit();app.store.create("preview-only-long-master");
        app.store.save(new JSONObject().put("id","preview1").put("title","GitHub").put("username","alex@example.com").put("password","fictional-password").put("url","https://github.com"));
        app.store.save(new JSONObject().put("id","preview2").put("title","Proton").put("username","alex.demo@proton.me").put("password","fictional-password").put("url","https://account.proton.me"));
        try(ActivityController<MainActivity> controller=Robolectric.buildActivity(MainActivity.class).setup()){
            View content=root(controller.get());content.measure(View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(1680,View.MeasureSpec.EXACTLY));content.layout(0,0,800,1680);
            android.graphics.Bitmap bitmap=android.graphics.Bitmap.createBitmap(800,1680,android.graphics.Bitmap.Config.ARGB_8888);content.draw(new android.graphics.Canvas(bitmap));
            java.io.File destination=new java.io.File("build/preview-android.png");destination.getParentFile().mkdirs();try(java.io.OutputStream out=new java.io.FileOutputStream(destination)){assertTrue(bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG,100,out));}
            TextView account=views(content,TextView.class).stream().filter(v->"GitHub".equals(v.getText().toString())).findFirst().orElseThrow();
            ((View)account.getParent().getParent()).performClick();
            assertTrue(text(controller.get(),"Copy password"));assertFalse(text(controller.get(),"fictional-password"));
            content=root(controller.get());content.measure(View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(1680,View.MeasureSpec.EXACTLY));content.layout(0,0,800,1680);
            bitmap=android.graphics.Bitmap.createBitmap(800,1680,android.graphics.Bitmap.Config.ARGB_8888);content.draw(new android.graphics.Canvas(bitmap));
            try(java.io.OutputStream out=new java.io.FileOutputStream("build/preview-android-detail.png")){assertTrue(bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG,100,out));}

        }
    }

    @Test public void interruptedAtomicWriteRecoversPreviousVault()throws Exception{
        app.store.create("recovery-only-master");byte[] saved=java.nio.file.Files.readAllBytes(app.store.file.toPath());app.store.lock();
        java.nio.file.Files.move(app.store.file.toPath(),java.nio.file.Path.of(app.store.file.getPath()+".bak"));
        java.nio.file.Files.write(app.store.file.toPath(),new byte[]{1,2,3});
        app.store.open("recovery-only-master");assertEquals(0,app.store.entries().length());assertArrayEquals(saved,java.nio.file.Files.readAllBytes(app.store.file.toPath()));
    }


    @Test public void savedEntryIsNormalizedAndIndependent()throws Exception{
        app.store.create("test-only-long-master");
        JSONObject entry=new JSONObject().put("id","regression").put("title","Demo").put("username","user").put("password","fake").put("url","https://EXAMPLE.com:443/login");
        app.store.save(entry);entry.put("password","changed");
        assertEquals("fake",app.store.entries().getJSONObject(0).getString("password"));
        assertEquals("https://example.com",app.store.entries().getJSONObject(0).getString("url"));
    }
    @Test public void oldActivityCannotRemoveNewLockListener(){
        ActivityController<MainActivity> old=Robolectric.buildActivity(MainActivity.class).setup();
        ActivityController<MainActivity> current=Robolectric.buildActivity(MainActivity.class).setup();
        Runnable listener=app.onLock;assertNotNull(listener);
        old.pause().stop().destroy();assertSame(listener,app.onLock);
        current.pause().stop().destroy();assertNull(app.onLock);
    }
}
