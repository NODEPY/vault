package com.appkaui.vault;

import android.content.Context;
import android.util.AtomicFile;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public final class VaultStore {
    final File file;
    private VaultCrypto.Session session;
    private JSONArray records;
    VaultStore(Context context){file=new File(context.getFilesDir(),"vault.bin");}
    public boolean exists(){return file.isFile()||new File(file.getPath()+".bak").isFile();}
    public InputStream encryptedInput()throws IOException{return new AtomicFile(file).openRead();}
    public boolean unlocked(){return session!=null;}
    public synchronized void lock(){if(session!=null)session.clear();session=null;records=null;}
    public static byte[] read(InputStream stream)throws Exception{
        ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buffer=new byte[8192];int n;
        while((n=stream.read(buffer))!=-1){if(out.size()+n>VaultCrypto.MAX_SIZE)throw new IOException("File too large");out.write(buffer,0,n);}return out.toByteArray();
    }
    public static JSONArray validate(byte[] plaintext)throws Exception{
        JSONArray data=new JSONArray(new String(plaintext,StandardCharsets.UTF_8));Set<String> ids=new HashSet<>();
        Set<String> keys=new HashSet<>(Arrays.asList("id","title","username","password","url","app_package","app_signature"));
        for(int i=0;i<data.length();i++){
            JSONObject entry=data.getJSONObject(i);
            for(String name:Arrays.asList("id","title","username","password"))if(!(entry.get(name)instanceof String))throw new IOException("Invalid entry");
            Iterator<String> iterator=entry.keys();while(iterator.hasNext()){String key=iterator.next();if(!keys.contains(key)||!(entry.get(key)instanceof String))throw new IOException("Invalid entry");}
            if(!entry.optString("url").isEmpty())entry.put("url",MainActivity.origin(entry.getString("url")));
            if(entry.getString("id").isEmpty()||entry.getString("title").trim().isEmpty()||!ids.add(entry.getString("id")))throw new IOException("Invalid entry");
        }return data;
    }
    public void open(String password)throws Exception{
        try(InputStream input=encryptedInput()){
            VaultCrypto.Opened opened=VaultCrypto.open(read(input),password);
            try{JSONArray loaded=validate(opened.plaintext);lock();session=opened.session;records=loaded;}
            catch(Exception error){opened.session.clear();throw error;}
            finally{Arrays.fill(opened.plaintext,(byte)0);}
        }
    }
    public void create(String password)throws Exception{
        if(exists())throw new IOException("Vault exists");
        VaultCrypto.Session candidate=VaultCrypto.create(password);
        try{write(candidate,new JSONArray());session=candidate;records=new JSONArray();}
        catch(Exception error){candidate.clear();throw error;}
    }
    private void write(VaultCrypto.Session cipher,JSONArray values)throws Exception{
        byte[] bytes=cipher.encrypt(values.toString().getBytes(StandardCharsets.UTF_8));
        AtomicFile atomic=new AtomicFile(file);FileOutputStream output=null;
        try{output=atomic.startWrite();output.write(bytes);atomic.finishWrite(output);}
        catch(Exception error){if(output!=null)atomic.failWrite(output);throw error;}
    }
    public synchronized JSONArray entries()throws Exception{if(!unlocked())throw new IllegalStateException("Locked");return new JSONArray(records.toString());}
    public synchronized void save(JSONObject entry)throws Exception{
        entry=validate(new JSONArray().put(entry).toString().getBytes(StandardCharsets.UTF_8)).getJSONObject(0);JSONArray next=entries();boolean replaced=false;
        for(int i=0;i<next.length();i++)if(next.getJSONObject(i).getString("id").equals(entry.getString("id"))){next.put(i,entry);replaced=true;break;}
        if(!replaced)next.put(entry);write(session,next);records=next;
    }
    public synchronized void delete(String id)throws Exception{
        JSONArray next=new JSONArray(),old=entries();for(int i=0;i<old.length();i++)if(!old.getJSONObject(i).getString("id").equals(id))next.put(old.getJSONObject(i));
        write(session,next);records=next;
    }
    public synchronized int importBackup(byte[] encrypted,String password)throws Exception{
        VaultCrypto.Opened opened=VaultCrypto.open(encrypted,password);
        try{
            JSONArray imported=validate(opened.plaintext),next=entries();int count=0;
            for(int i=0;i<imported.length();i++){
                JSONObject entry=imported.getJSONObject(i);boolean duplicate=false;
                for(int j=0;j<next.length();j++){
                    JSONObject old=next.getJSONObject(j);
                    if(old.getString("title").equals(entry.getString("title"))&&old.getString("username").equals(entry.getString("username"))&&old.getString("password").equals(entry.getString("password"))&&old.optString("url").equals(entry.optString("url"))&&old.optString("app_package").equals(entry.optString("app_package"))&&old.optString("app_signature").equals(entry.optString("app_signature"))) {duplicate=true;break;}
                }
                if(!duplicate){entry.put("id",UUID.randomUUID().toString().replace("-",""));next.put(entry);count++;}
            }
            write(session,next);records=next;return count;
        }finally{opened.session.clear();Arrays.fill(opened.plaintext,(byte)0);}
    }
    public synchronized void reset()throws Exception{lock();new AtomicFile(file).delete();if(file.exists()||new File(file.getPath()+".bak").exists()||new File(file.getPath()+".new").exists())throw new IOException("Cannot delete vault");}
}
