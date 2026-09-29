package com.appkaui.vault;

import android.app.*;
import android.content.*;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.net.Uri;
import android.os.*;
import android.provider.Settings;
import android.service.autofill.*;
import android.text.*;
import android.text.method.PasswordTransformationMethod;
import android.view.*;
import android.view.autofill.*;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.net.IDN;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.*;
import java.util.concurrent.*;

public class MainActivity extends Activity {
    private VaultApp app;
    private SharedPreferences prefs;
    private JSONObject strings;
    private LinearLayout root, body;
    private int bg, panel, ink, muted, accent;
    private boolean lightTheme;
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private boolean active, external;
    private int generation;
    private String requestToken;
    private AutofillRequests.Request fillRequest;
    private AlertDialog currentDialog;
    private final Runnable lockListener=()->{if(active)showUnlock();};
    private static final int EXPORT=40, IMPORT=41;

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        app=(VaultApp)getApplication();prefs=getSharedPreferences("preferences",MODE_PRIVATE);
        if(this instanceof AutofillAuthActivity){
            requestToken=getIntent().getStringExtra("request_token");fillRequest=AutofillRequests.get(requestToken);
            if(fillRequest==null){finish();return;}
            app.lock(); // Every system autofill authentication requires the master password.
        }
        loadAppearance();
    }
    @Override protected void onResume(){super.onResume();active=true;app.onLock=lockListener;
        if(!prefs.getBoolean("setup",false))showSettings(true);else if(app.store.unlocked())showLibrary();else showUnlock();app.touch();}
    @Override protected void onStop(){
        active=false;generation++;if(currentDialog!=null){currentDialog.dismiss();currentDialog=null;}
        if(!external){app.lock();if(root!=null)root.removeAllViews();}super.onStop();
    }
    @Override protected void onDestroy(){if(app!=null&&app.onLock==lockListener)app.onLock=null;worker.shutdown();super.onDestroy();}
    @Override public void onUserInteraction(){super.onUserInteraction();if(app!=null)app.touch();}
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
    private String t(String key){return strings==null?key:strings.optString(key,key);}
    private void loadAppearance(){
        try(InputStream in=getAssets().open("locales/"+prefs.getString("language","en")+".json")){strings=new JSONObject(new String(VaultStore.read(in),StandardCharsets.UTF_8));}catch(Exception e){strings=new JSONObject();}
        String theme=prefs.getString("theme","dark");
        lightTheme=theme.equals("light")||theme.equals("sand");
        String[] c=switch(theme){case "light"->new String[]{"#F5F6F3","#FFFFFF","#242927","#636C66","#315F46"};case "sand"->new String[]{"#EFE7D9","#FBF7EE","#352E24","#796A56","#79603D"};case "forest"->new String[]{"#101D18","#192B22","#E4EFE6","#91AA99","#AED4A7"};case "midnight"->new String[]{"#121827","#1D263A","#E7ECF8","#9AA8C5","#B0C3E8"};default->new String[]{"#202325","#272B2D","#EEEFED","#A2A7A8","#A9C8B6"};};
        bg=Color.parseColor(c[0]);panel=Color.parseColor(c[1]);ink=Color.parseColor(c[2]);muted=Color.parseColor(c[3]);accent=Color.parseColor(c[4]);
    }
    private GradientDrawable surface(int color,int radius){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(radius));return d;}
    private LinearLayout column(){LinearLayout v=new LinearLayout(this);v.setOrientation(LinearLayout.VERTICAL);return v;}
    private void screen(String subtitle){
        root=column();root.setBackgroundColor(bg);root.setPadding(dp(24),dp(20),dp(24),dp(12));
        root.setOnApplyWindowInsetsListener((v,insets)->{int top=insets.getSystemWindowInsetTop(),bottom=insets.getSystemWindowInsetBottom();v.setPadding(dp(24),top+dp(16),dp(24),bottom+dp(12));return insets;});
        setContentView(root);root.requestApplyInsets();
        TextView brand=text("Vault",22,true);brand.setTextColor(ink);
        LinearLayout bar=new LinearLayout(this);bar.setGravity(Gravity.CENTER_VERTICAL);bar.addView(brand,new LinearLayout.LayoutParams(0,-2,1));
        if(app.store.unlocked()&&fillRequest==null){Button more=new Button(this);more.setText("···");more.setTextSize(24);more.setTextColor(ink);more.setBackgroundColor(Color.TRANSPARENT);more.setContentDescription(t("tools"));bar.addView(more,new LinearLayout.LayoutParams(dp(48),dp(48)));
            more.setOnClickListener(v->{PopupMenu menu=new PopupMenu(this,more);menu.getMenu().add(t("tools")).setOnMenuItemClickListener(item->{showTools();return true;});menu.getMenu().add(t("settings")).setOnMenuItemClickListener(item->{showSettings(false);return true;});menu.getMenu().add(t("lock")).setOnMenuItemClickListener(item->{app.lock();showUnlock();return true;});menu.show();});}
        root.addView(bar);
        TextView title=text(subtitle,28,true);LinearLayout.LayoutParams tp=new LinearLayout.LayoutParams(-1,-2);tp.setMargins(0,dp(18),0,dp(16));root.addView(title,tp);
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));body=column();scroll.addView(body);
    }
    private TextView text(String value,int size,boolean bold){TextView v=new TextView(this);v.setText(value);v.setTextSize(size);v.setTextColor(ink);v.setTypeface(Typeface.create("sans-serif",bold?Typeface.BOLD:Typeface.NORMAL));v.setPadding(0,dp(3),0,dp(3));return v;}
    private void hint(LinearLayout parent,String value){TextView v=text(value,14,false);v.setTextColor(muted);parent.addView(v);}
    private EditText input(LinearLayout parent,String label,String value,boolean secret){
        if(!label.isEmpty())hint(parent,label);EditText v=new EditText(this);v.setSingleLine(true);v.setTextColor(ink);v.setHintTextColor(muted);v.setTextSize(16);v.setPadding(dp(14),dp(12),dp(14),dp(12));v.setBackground(surface(panel,10));v.setMinHeight(dp(52));
        v.setInputType(secret?InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD:InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        v.setImportantForAutofill(View.IMPORTANT_FOR_AUTOFILL_NO);v.setSaveEnabled(false);v.setText(value);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(0,0,0,dp(12));parent.addView(v,lp);return v;
    }
    private Button button(LinearLayout parent,String label,Runnable action){
        Button b=new Button(this);b.setText(label);b.setAllCaps(false);b.setTextSize(14);b.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));b.setTextColor(ink);
        b.setBackground(new RippleDrawable(ColorStateList.valueOf(0x227F998B),surface(panel,10),null));b.setMinHeight(dp(48));b.setMinimumHeight(dp(48));b.setPadding(dp(14),dp(10),dp(14),dp(10));
        boolean horizontal=parent.getOrientation()==LinearLayout.HORIZONTAL;
        LinearLayout.LayoutParams lp=horizontal?new LinearLayout.LayoutParams(0,-2,1):new LinearLayout.LayoutParams(-1,-2);
        lp.setMargins(0,dp(6),horizontal?dp(6):0,dp(6));parent.addView(b,lp);b.setOnClickListener(v->action.run());return b;
    }
    private void primary(Button button){button.setBackground(new RippleDrawable(ColorStateList.valueOf(0x337F998B),surface(accent,10),null));button.setTextColor(bg);}
    private LinearLayout actionRow(LinearLayout parent){LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);parent.addView(row);return row;}
    private LinearLayout fieldSection(String label){
        LinearLayout section=column();section.setPadding(dp(16),dp(12),dp(16),dp(12));section.setBackground(surface(panel,12));
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(0,dp(6),0,dp(8));body.addView(section,lp);hint(section,label);return section;
    }
    private void error(String key){new AlertDialog.Builder(this).setTitle(t("error")).setMessage(t(key)).setPositiveButton("OK",null).show();}
    private void showUnlock(){
        if(!active)return; if(currentDialog!=null){currentDialog.dismiss();currentDialog=null;}
        boolean creating=!app.store.exists();screen(t(creating?"create_title":"unlock_title"));hint(body,t(creating?"create_hint":"unlock_hint"));
        EditText pw=input(body,t("master"),"",true);EditText repeat=creating?input(body,t("repeat"),"",true):null;
        Button unlock=button(body,t(creating?"create":"unlock"),()->{});primary(unlock);
        unlock.setOnClickListener(v->{
            String password=pw.getText().toString();
            if(password.isEmpty()){error("enter_master");return;}
            if(creating&&password.length()<12){error("short_master");return;}
            if(creating&&!password.equals(repeat.getText().toString())){error("mismatch");return;}
            unlock.setEnabled(false);pw.setText("");if(repeat!=null)repeat.setText("");int epoch=generation;
            worker.execute(()->{VaultStore candidate=new VaultStore(this);Exception failure=null;
                try{if(creating)candidate.create(password);else candidate.open(password);}catch(Exception e){failure=e;}
                boolean ok=failure==null;
                runOnUiThread(()->{if(!active||epoch!=generation){candidate.lock();return;}unlock.setEnabled(true);if(!ok){candidate.lock();error("unlock_error");return;}app.store.lock();app.store=candidate;app.touch();showLibrary();});
            });
        });
        if(!creating)button(body,t("forgot"),this::resetVault);
        button(body,t("settings"),()->showSettings(false));
    }
    private void showLibrary(){
        if(!app.store.unlocked()){showUnlock();return;}
        if(fillRequest!=null&&AutofillRequests.get(requestToken)==null){finish();return;}
        screen(t("passwords"));
        if(fillRequest!=null){hint(body,t("fill_for")+"\n"+fillRequest.label+"\n"+fillRequest.pkg);}
        EditText search=input(body,"","",false);search.setHint(t("search"));
        TextView count=text("",12,false);count.setTextColor(muted);count.setPadding(0,dp(6),0,dp(12));body.addView(count);
        LinearLayout list=column();body.addView(list);
        Runnable render=()->{list.removeAllViews();try{
            JSONArray entries=app.store.entries();ArrayList<JSONObject> sorted=new ArrayList<>();for(int i=0;i<entries.length();i++)sorted.add(entries.getJSONObject(i));sorted.sort(Comparator.comparing(o->o.optString("title").toLowerCase(Locale.ROOT)));
            String query=search.getText().toString().toLowerCase(Locale.ROOT);int found=0;
            for(JSONObject entry:sorted){if(!(entry.optString("title")+" "+entry.optString("username")).toLowerCase(Locale.ROOT).contains(query))continue;
                if(fillRequest!=null&&!entry.optString("app_package").isEmpty()&&(!entry.optString("app_package").equals(fillRequest.pkg)||!entry.optString("app_signature").equals(fillRequest.signature)))continue;
                found++;entryRow(list,entry,()->{if(fillRequest!=null)confirmFill(entry);else showEntry(entry);});}
            count.setText(t("entry_total").replace("{count}",String.valueOf(found)));
            if(found==0)hint(list,t(entries.length()==0?"empty":"no_results"));
        }catch(Exception e){showUnlock();}};
        search.addTextChangedListener(new TextWatcher(){public void beforeTextChanged(CharSequence s,int st,int c,int a){}public void onTextChanged(CharSequence s,int st,int b,int c){render.run();}public void afterTextChanged(Editable e){}});render.run();
        if(fillRequest==null){Button add=button(root,t("add"),()->editEntry(null));primary(add);}
        else button(body,t("lock"),()->{app.lock();showUnlock();});
    }
    private void entryRow(LinearLayout parent,JSONObject entry,Runnable action){
        LinearLayout row=new LinearLayout(this);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(dp(14),dp(15),dp(14),dp(15));row.setBackground(new RippleDrawable(ColorStateList.valueOf(0x227F998B),surface(panel,12),null));
        TextView avatar=text(entry.optString("title").substring(0,Math.min(1,entry.optString("title").length())).toUpperCase(Locale.ROOT),16,true);avatar.setGravity(Gravity.CENTER);avatar.setTextColor(accent);avatar.setBackground(surface(bg,8));row.addView(avatar,new LinearLayout.LayoutParams(dp(44),dp(44)));
        LinearLayout names=column();LinearLayout.LayoutParams np=new LinearLayout.LayoutParams(0,-2,1);np.setMargins(dp(14),0,dp(10),0);row.addView(names,np);
        TextView title=text(entry.optString("title"),16,true);title.setSingleLine(true);title.setEllipsize(TextUtils.TruncateAt.END);names.addView(title);
        TextView username=text(entry.optString("username"),13,false);username.setTextColor(muted);username.setSingleLine(true);username.setEllipsize(TextUtils.TruncateAt.END);names.addView(username);
        TextView arrow=text("›",24,false);arrow.setTextColor(muted);row.addView(arrow);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(0,dp(5),0,dp(5));parent.addView(row,lp);row.setClickable(true);row.setFocusable(true);row.setContentDescription(entry.optString("title")+", "+entry.optString("username"));row.setOnClickListener(v->action.run());
    }
    private void showEntry(JSONObject entry){
        if(!app.store.unlocked()){showUnlock();return;}screen(entry.optString("title"));
        hint(body,entry.optString("url").isEmpty()?t("local_entry"):entry.optString("url"));
        LinearLayout username=fieldSection(t("username"));TextView user=text(entry.optString("username"),17,false);user.setTextIsSelectable(true);username.addView(user);
        button(username,t("copy_username"),()->copy(entry.optString("username")));
        LinearLayout secret=fieldSection(t("password"));TextView password=text("••••••••••••",20,false);password.setTypeface(Typeface.MONOSPACE);secret.addView(password);
        LinearLayout access=actionRow(secret);
        button(access,t("reveal"),()->{password.setText(entry.optString("password"));app.handler.postDelayed(()->password.setText("••••••••••••"),10000);});
        button(access,t("copy_password"),()->copy(entry.optString("password")));
        hint(body,t("security_note"));
        LinearLayout actions=actionRow(body);button(actions,t("edit"),()->editEntry(entry));
        Button delete=button(actions,t("delete"),()->confirm(t("delete_entry_body"),()->{try{app.store.delete(entry.optString("id"));showLibrary();}catch(Exception e){error("save_failed");}}));delete.setTextColor(lightTheme?Color.parseColor("#A43535"):Color.parseColor("#EDA7A2"));
        button(root,t("close"),this::showLibrary);
    }
    private void copy(String value){
        android.content.ClipboardManager manager=(android.content.ClipboardManager)getSystemService(CLIPBOARD_SERVICE);String token="Vault-"+UUID.randomUUID();ClipData clip=ClipData.newPlainText(token,value);
        PersistableBundle extras=new PersistableBundle();extras.putBoolean("android.content.extra.IS_SENSITIVE",true);clip.getDescription().setExtras(extras);manager.setPrimaryClip(clip);Toast.makeText(this,t("copied"),Toast.LENGTH_SHORT).show();
        app.handler.postDelayed(()->{if(manager.hasPrimaryClip()&&manager.getPrimaryClipDescription()!=null&&token.equals(String.valueOf(manager.getPrimaryClipDescription().getLabel()))){if(Build.VERSION.SDK_INT>=28)manager.clearPrimaryClip();else manager.setPrimaryClip(ClipData.newPlainText("",""));}},20000);
    }
    static String origin(String value)throws Exception{return Origin.canonical(value);}
    private void editEntry(JSONObject original){
        if(!app.store.unlocked()){showUnlock();return;}screen(t(original==null?"new_entry":"edit_entry"));
        EditText title=input(body,t("service"),original==null?"":original.optString("title"),false),user=input(body,t("username"),original==null?"":original.optString("username"),false),url=input(body,t("website"),original==null?"":original.optString("url"),false),password=input(body,t("password"),original==null?"":original.optString("password"),true);
        button(body,t("generator"),()->password.setText(randomPassword()));
        Button save=button(body,t("save"),()->{if(title.getText().toString().trim().isEmpty()){error("enter_title");return;}if(password.length()==0){error("enter_password");return;}
            String site;try{site=origin(url.getText().toString());}catch(Exception e){error("invalid_website");return;}
            try{JSONObject entry=original==null?new JSONObject():new JSONObject(original.toString());if(original==null)entry.put("id",UUID.randomUUID().toString().replace("-",""));entry.put("title",title.getText().toString().trim()).put("username",user.getText().toString()).put("password",password.getText().toString()).put("url",site);app.store.save(entry);password.setText("");showLibrary();}catch(Exception e){error("save_failed");}
        });primary(save);button(body,t("cancel"),this::showLibrary);
    }
    private String randomPassword(){String chars="ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%&*+-_";SecureRandom rng=new SecureRandom();StringBuilder value=new StringBuilder();for(int i=0;i<24;i++)value.append(chars.charAt(rng.nextInt(chars.length())));return value.toString();}
    private void confirm(String message,Runnable action){currentDialog=new AlertDialog.Builder(this).setMessage(message).setNegativeButton(t("cancel"),null).setPositiveButton(t("continue"),(d,w)->{if(app.store.unlocked())action.run();}).create();currentDialog.show();}
    private void resetVault(){
        EditText confirm=new EditText(this);confirm.setSingleLine(true);confirm.setHint("DELETE");
        currentDialog=new AlertDialog.Builder(this).setTitle(t("reset_title")).setMessage(t("reset_body")+"\n\n"+t("reset_instruction")).setView(confirm).setNegativeButton(t("cancel"),null).setPositiveButton(t("delete_all"),null).create();
        currentDialog.setOnShowListener(d->currentDialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{if(!"DELETE".equals(confirm.getText().toString()))return;try{app.store.reset();currentDialog.dismiss();showUnlock();}catch(Exception e){error("reset_error");}}));currentDialog.show();
    }
    private void showSettings(boolean setup){
        screen(t(setup?"welcome":"settings"));hint(body,t(setup?"welcome_hint":"settings_hint"));
        String[] languages={"English","Українська","Polski","Deutsch","Español"},codes={"en","uk","pl","de","es"},themes={"Graphite","Paper","Dune","Pine","Ink"},themeCodes={"dark","light","sand","forest","midnight"};
        Spinner language=spinner(body,t("language"),languages,Arrays.asList(codes).indexOf(prefs.getString("language","en"))),theme=spinner(body,t("theme"),themes,Arrays.asList(themeCodes).indexOf(prefs.getString("theme","dark")));
        button(body,t(setup?"continue":"save"),()->{prefs.edit().putString("language",codes[language.getSelectedItemPosition()]).putString("theme",themeCodes[theme.getSelectedItemPosition()]).putBoolean("setup",true).apply();loadAppearance();if(app.store.unlocked())showLibrary();else showUnlock();});
        if(!setup)button(body,t("cancel"),()->{if(app.store.unlocked())showLibrary();else showUnlock();});
    }
    private Spinner spinner(LinearLayout parent,String label,String[] values,int selected){hint(parent,label);Spinner s=new Spinner(this);ArrayAdapter<String> adapter=new ArrayAdapter<String>(this,android.R.layout.simple_spinner_dropdown_item,values){@Override public View getView(int p,View v,android.view.ViewGroup group){TextView row=(TextView)super.getView(p,v,group);row.setTextColor(ink);row.setPadding(dp(10),dp(12),dp(10),dp(12));return row;}};s.setAdapter(adapter);s.setSelection(Math.max(0,selected));parent.addView(s);return s;}
    private void showTools(){
        screen(t("tools"));hint(body,t("android_transfer"));
        button(body,t("export_backup"),()->{external=true;try{Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("application/octet-stream").addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_TITLE,"vault-backup.vault");startActivityForResult(i,EXPORT);}catch(Exception e){external=false;error("file_error");}});
        button(body,t("import_backup"),()->{external=true;try{startActivityForResult(new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE),IMPORT);}catch(Exception e){external=false;error("file_error");}});
        button(body,t("enable_autofill"),()->{try{startActivity(new Intent(Settings.ACTION_REQUEST_SET_AUTOFILL_SERVICE,Uri.parse("package:"+getPackageName())));}catch(Exception e){error("file_error");}});
        hint(body,t("android_autofill_hint"));hint(body,"0.1.0-beta.1 · "+t("about_body"));button(body,t("close"),this::showLibrary);
    }
    @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);external=false;
        if(result!=RESULT_OK||data==null||data.getData()==null)return;Uri uri=data.getData();
        if(request==EXPORT){try(InputStream in=app.store.encryptedInput();OutputStream out=getContentResolver().openOutputStream(uri,"wt")){if(out==null)throw new IOException();out.write(VaultStore.read(in));Toast.makeText(this,t("backup_saved"),Toast.LENGTH_LONG).show();}catch(Exception e){error("file_error");}}
        if(request==IMPORT){app.handler.post(()->{if(!app.store.unlocked()){showUnlock();return;}EditText password=new EditText(this);password.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);password.setSaveEnabled(false);
            currentDialog=new AlertDialog.Builder(this).setTitle(t("backup_password")).setView(password).setNegativeButton(t("cancel"),null).setPositiveButton(t("import_backup"),(d,w)->{String master=password.getText().toString();password.setText("");int epoch=generation;
                worker.execute(()->{int count=-1;try(InputStream in=getContentResolver().openInputStream(uri)){if(in==null)throw new IOException();synchronized(app.store){if(app.store.unlocked())count=app.store.importBackup(VaultStore.read(in),master);}}catch(Exception ignored){}int added=count;
                    runOnUiThread(()->{if(!active||epoch!=generation)return;if(added<0)error("backup_error");else{showLibrary();Toast.makeText(this,t("backup_imported").replace("{count}",""+added),Toast.LENGTH_LONG).show();}});
                });}).create();currentDialog.show();});}
    }
    private void confirmFill(JSONObject entry){
        if(fillRequest==null||AutofillRequests.get(requestToken)==null){finish();return;}
        confirm(t("fill_confirm")+"\n\n"+fillRequest.label+"\n"+fillRequest.pkg+"\n\n"+entry.optString("title")+" · "+entry.optString("username"),()->{try{
            if(AutofillRequests.get(requestToken)==null){finish();return;}
            if(!entry.optString("app_package").isEmpty()&&(!entry.optString("app_package").equals(fillRequest.pkg)||!entry.optString("app_signature").equals(fillRequest.signature)))throw new SecurityException();
            entry.put("app_package",fillRequest.pkg).put("app_signature",fillRequest.signature);app.store.save(entry);
            RemoteViews presentation=new RemoteViews(getPackageName(),android.R.layout.simple_list_item_1);presentation.setTextViewText(android.R.id.text1,entry.optString("title"));Dataset.Builder dataset=new Dataset.Builder(presentation);dataset.setValue(fillRequest.password,AutofillValue.forText(entry.getString("password")));if(fillRequest.username!=null)dataset.setValue(fillRequest.username,AutofillValue.forText(entry.getString("username")));
            FillResponse response=new FillResponse.Builder().addDataset(dataset.build()).build();setResult(RESULT_OK,new Intent().putExtra(AutofillManager.EXTRA_AUTHENTICATION_RESULT,response));AutofillRequests.remove(requestToken);app.lock();finish();
        }catch(Exception e){error("save_failed");}});
    }
}
