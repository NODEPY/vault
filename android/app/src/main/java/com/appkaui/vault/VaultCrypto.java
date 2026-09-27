package com.appkaui.vault;

import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Arrays;
import java.util.Base64;
import javax.crypto.Cipher;
import javax.crypto.Mac;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import org.bouncycastle.crypto.generators.Argon2BytesGenerator;
import org.bouncycastle.crypto.params.Argon2Parameters;

/** The desktop VAULT1 envelope: salt + authenticated Fernet token. */
public final class VaultCrypto {
    static final byte[] HEADER = new byte[]{'V','A','U','L','T','1',0};
    static final SecureRandom RANDOM = new SecureRandom();
    public static final int MAX_SIZE = 16 * 1024 * 1024;

    public static final class Session {
        final byte[] salt;
        private byte[] key;
        Session(byte[] salt, byte[] key) { this.salt = salt.clone(); this.key = key; }
        public void clear() { if (key != null) Arrays.fill(key, (byte)0); key = null; }
        public byte[] encrypt(byte[] data) throws Exception {
            if (key == null) throw new IllegalStateException("Locked");
            byte[] iv = new byte[16]; RANDOM.nextBytes(iv);
            Cipher aes = Cipher.getInstance("AES/CBC/PKCS5Padding");
            aes.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(Arrays.copyOfRange(key,16,32),"AES"),new IvParameterSpec(iv));
            byte[] ciphertext = aes.doFinal(data);
            byte[] signed = ByteBuffer.allocate(25+ciphertext.length).put((byte)0x80).putLong(System.currentTimeMillis()/1000).put(iv).put(ciphertext).array();
            Mac mac = Mac.getInstance("HmacSHA256");mac.init(new SecretKeySpec(Arrays.copyOfRange(key,0,16),"HmacSHA256"));
            byte[] token = Base64.getUrlEncoder().encode(ByteBuffer.allocate(signed.length+32).put(signed).put(mac.doFinal(signed)).array());
            byte[] result = ByteBuffer.allocate(HEADER.length+16+token.length).put(HEADER).put(salt).put(token).array();
            if (result.length>MAX_SIZE) throw new IllegalArgumentException("Vault too large");
            return result;
        }
    }
    public static final class Opened {
        public final Session session;
        public final byte[] plaintext;
        Opened(Session session, byte[] plaintext) { this.session=session;this.plaintext=plaintext; }
    }
    public static Session create(String password) { byte[] salt=new byte[16];RANDOM.nextBytes(salt);return derive(password,salt); }
    static Session derive(String password, byte[] salt) {
        if(password.isEmpty()) throw new IllegalArgumentException("Empty master password");
        Argon2Parameters parameters = new Argon2Parameters.Builder(Argon2Parameters.ARGON2_id)
            .withVersion(Argon2Parameters.ARGON2_VERSION_13).withSalt(salt).withParallelism(4).withIterations(3).withMemoryAsKB(65536).build();
        Argon2BytesGenerator generator=new Argon2BytesGenerator();generator.init(parameters);
        byte[] key=new byte[32],input=password.getBytes(StandardCharsets.UTF_8);
        try { generator.generateBytes(input,key); } finally { Arrays.fill(input,(byte)0); }
        return new Session(salt,key);
    }
    public static Opened open(byte[] data,String password) throws Exception {
        if(data.length>MAX_SIZE||data.length<24||!Arrays.equals(HEADER,Arrays.copyOfRange(data,0,7)))throw new SecurityException("Invalid vault");
        Session session=derive(password,Arrays.copyOfRange(data,7,23));
        try {
            byte[] token=Base64.getUrlDecoder().decode(Arrays.copyOfRange(data,23,data.length));
            if(token.length<73||token[0]!=(byte)0x80||(token.length-57)%16!=0)throw new SecurityException("Invalid token");
            byte[] signed=Arrays.copyOfRange(token,0,token.length-32);
            Mac mac=Mac.getInstance("HmacSHA256");mac.init(new SecretKeySpec(Arrays.copyOfRange(session.key,0,16),"HmacSHA256"));
            if(!MessageDigest.isEqual(mac.doFinal(signed),Arrays.copyOfRange(token,token.length-32,token.length)))throw new SecurityException("Incorrect password or damaged vault");
            Cipher aes=Cipher.getInstance("AES/CBC/PKCS5Padding");
            aes.init(Cipher.DECRYPT_MODE,new SecretKeySpec(Arrays.copyOfRange(session.key,16,32),"AES"),new IvParameterSpec(Arrays.copyOfRange(token,9,25)));
            return new Opened(session,aes.doFinal(Arrays.copyOfRange(token,25,token.length-32)));
        } catch(Exception error) { session.clear();throw error; }
    }
}
