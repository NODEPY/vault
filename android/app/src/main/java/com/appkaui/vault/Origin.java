package com.appkaui.vault;
import java.net.URI;
import java.util.Locale;

/** Conservative HTTPS origins; international domains must use ASCII/punycode. */
final class Origin {
    static String canonical(String value)throws Exception{
        if(value==null||value.length()>2048)throw new IllegalArgumentException("Invalid address");
        for(char c:value.toCharArray())if(c<32||c==127)throw new IllegalArgumentException("Control character");
        if(value.trim().isEmpty())return "";
        URI uri=new URI(value.trim());
        if(!"https".equalsIgnoreCase(uri.getScheme())||uri.getRawUserInfo()!=null||uri.getHost()==null)throw new IllegalArgumentException("HTTPS required");
        String host=uri.getHost().toLowerCase(Locale.ROOT);
        if(host.startsWith("[")){
            if(!host.matches("\\[[0-9a-f:.]+\\]"))throw new IllegalArgumentException("Invalid IP address");
        }else{
            if(host.length()>253)throw new IllegalArgumentException("Invalid host");
            for(String label:host.split("\\.",-1))if(!label.matches("[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"))throw new IllegalArgumentException("Use ASCII/punycode host");
        }
        int port=uri.getPort();if(port==0||port>65535)throw new IllegalArgumentException("Invalid port");
        return "https://"+host+(port==-1||port==443?"":":"+port);
    }
}
