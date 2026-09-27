package com.appkaui.vault;
import org.junit.Test;
import static org.junit.Assert.*;
public class OriginTest {
 @Test public void normalizesSafeOrigins() throws Exception {
  assertEquals("https://example.com",Origin.canonical("https://EXAMPLE.com:443/login"));
  assertEquals("https://xn--fa-hia.de",Origin.canonical("https://xn--fa-hia.de/path"));
  assertEquals("https://example.com:444",Origin.canonical("https://example.com:444/login"));
 }
 @Test public void rejectsAmbiguousOrigins(){
  for(String value:new String[]{"https://example.com:0","https://@example.com","https://faß.de","https://exam\nple.com","https://example.com.","http://example.com"})
   assertThrows(Exception.class,()->Origin.canonical(value));
 }
}
