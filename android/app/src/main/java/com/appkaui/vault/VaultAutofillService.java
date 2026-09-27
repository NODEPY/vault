package com.appkaui.vault;

import android.app.PendingIntent;
import android.app.assist.AssistStructure;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.os.CancellationSignal;
import android.service.autofill.*;
import android.text.InputType;
import android.view.View;
import android.widget.RemoteViews;
import java.security.MessageDigest;
import java.util.*;

public class VaultAutofillService extends AutofillService {
    @Override public void onFillRequest(FillRequest request,CancellationSignal signal,FillCallback callback){
        try{
            AssistStructure structure=request.getFillContexts().get(request.getFillContexts().size()-1).getStructure();
            String pkg=structure.getActivityComponent().getPackageName();
            if(pkg.equals(getPackageName())||signal.isCanceled()){callback.onSuccess(null);return;}
            ArrayList<AssistStructure.ViewNode> passwords=new ArrayList<>(),users=new ArrayList<>();boolean[] web={false};
            for(int i=0;i<structure.getWindowNodeCount();i++)walk(structure.getWindowNodeAt(i).getRootViewNode(),passwords,users,web);
            // Do not trust a WebView's self-reported domain for website credentials.
            if(web[0]||passwords.size()!=1||users.size()>1){callback.onSuccess(null);return;}
            PackageInfo info=getPackageManager().getPackageInfo(pkg,PackageManager.GET_SIGNATURES);
            if(info.signatures==null||info.signatures.length!=1){callback.onSuccess(null);return;}
            byte[] digest=MessageDigest.getInstance("SHA-256").digest(info.signatures[0].toByteArray());StringBuilder signature=new StringBuilder();for(byte b:digest)signature.append(String.format(Locale.ROOT,"%02x",b&255));
            AutofillRequests.Request target=new AutofillRequests.Request();target.pkg=pkg;target.signature=signature.toString();target.label=getPackageManager().getApplicationLabel(getPackageManager().getApplicationInfo(pkg,0)).toString();target.password=passwords.get(0).getAutofillId();target.username=users.isEmpty()?null:users.get(0).getAutofillId();
            String token=AutofillRequests.put(target);
            Intent intent=new Intent(this,AutofillAuthActivity.class).putExtra("request_token",token);
            int flags=PendingIntent.FLAG_CANCEL_CURRENT;if(android.os.Build.VERSION.SDK_INT>=31)flags|=PendingIntent.FLAG_MUTABLE;
            PendingIntent pending=PendingIntent.getActivity(this,token.hashCode(),intent,flags);
            RemoteViews presentation=new RemoteViews(getPackageName(),android.R.layout.simple_list_item_1);presentation.setTextViewText(android.R.id.text1,"Unlock Vault · "+target.label);
            android.view.autofill.AutofillId[] ids=target.username==null?new android.view.autofill.AutofillId[]{target.password}:new android.view.autofill.AutofillId[]{target.username,target.password};
            callback.onSuccess(new FillResponse.Builder().setAuthentication(ids,pending.getIntentSender(),presentation).build());
        }catch(Exception error){callback.onSuccess(null);}
    }
    private void walk(AssistStructure.ViewNode node,List<AssistStructure.ViewNode> passwords,List<AssistStructure.ViewNode> users,boolean[] web){
        if(node.getWebDomain()!=null)web[0]=true;
        if(node.getAutofillId()!=null&&node.getVisibility()==View.VISIBLE&&node.isEnabled()){
            List<String> hints=node.getAutofillHints()==null?Collections.emptyList():Arrays.asList(node.getAutofillHints());
            int type=node.getInputType(),variation=type&InputType.TYPE_MASK_VARIATION;
            if(hints.contains(View.AUTOFILL_HINT_PASSWORD)||variation==InputType.TYPE_TEXT_VARIATION_PASSWORD||variation==InputType.TYPE_TEXT_VARIATION_WEB_PASSWORD)passwords.add(node);
            else if(hints.contains(View.AUTOFILL_HINT_USERNAME)||hints.contains(View.AUTOFILL_HINT_EMAIL_ADDRESS)||variation==InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS)users.add(node);
        }
        for(int i=0;i<node.getChildCount();i++)walk(node.getChildAt(i),passwords,users,web);
    }
    @Override public void onSaveRequest(SaveRequest request,SaveCallback callback){callback.onFailure("Save this account in Vault first.");}
}
