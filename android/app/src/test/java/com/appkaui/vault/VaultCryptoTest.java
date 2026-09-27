package com.appkaui.vault;
import org.junit.Test;
import static org.junit.Assert.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.io.InputStream;
import java.util.Arrays;

public class VaultCryptoTest {
    static final String MASTER="interop-only-пароль-🔐";
    static final byte[] PLAIN="[{\"id\":\"interop\",\"title\":\"Тест\",\"username\":\"demo\",\"password\":\"fake-🔑\"}]".getBytes(StandardCharsets.UTF_8);
    @Test public void decryptDesktopFixture()throws Exception{
        try(InputStream in=getClass().getResourceAsStream("/desktop.vault")){
            VaultCrypto.Opened opened=VaultCrypto.open(in.readAllBytes(),MASTER);assertArrayEquals(PLAIN,opened.plaintext);opened.session.clear();
        }
    }
    @Test public void randomizedRoundTripAndExport()throws Exception{
        VaultCrypto.Session session=VaultCrypto.create(MASTER);byte[] one=session.encrypt(PLAIN),two=session.encrypt(PLAIN);
        assertFalse(Arrays.equals(one,two));VaultCrypto.Opened opened=VaultCrypto.open(one,MASTER);assertArrayEquals(PLAIN,opened.plaintext);opened.session.clear();
        Path destination=Paths.get("build/interop-java.vault");Files.createDirectories(destination.getParent());Files.write(destination,one);session.clear();
        assertThrows(IllegalStateException.class,()->session.encrypt(PLAIN));
    }
    @Test public void wrongPasswordAndTamperRejected()throws Exception{
        VaultCrypto.Session session=VaultCrypto.create(MASTER);byte[] value=session.encrypt(PLAIN);session.clear();
        assertThrows(SecurityException.class,()->VaultCrypto.open(value,"wrong"));
        value[value.length-10]=(byte)(value[value.length-10]=='A'?'B':'A');
        assertThrows(Exception.class,()->VaultCrypto.open(value,MASTER));
    }
    @Test public void invalidEnvelopeRejected(){
        assertThrows(SecurityException.class,()->VaultCrypto.open(new byte[0],MASTER));
        assertThrows(SecurityException.class,()->VaultCrypto.open(new byte[VaultCrypto.MAX_SIZE+1],MASTER));
    }
}
