#include "STUNICODE.h"
#include <stdio.h>
#include <string.h>
#include <unicode/ustring.h>
static int tests=0, failures=0;
int32_t StApprovedOpen(const char *,int32_t);
static int open_path(const char *p){return StApprovedOpen(p,(int32_t)strlen(p));}
static void check(const char *name,int ok) {
 ++tests; printf("%s %s\n",ok?"PASS":"FAIL",name); if(!ok) ++failures;
}
static int convert(const char *s,uint16_t *out) {
 UErrorCode e=U_ZERO_ERROR;int32_t n=0;
 u_strFromUTF8(out,1024,&n,s,-1,&e); return U_FAILURE(e)?-1:n;
}
static void normal(const char *name,const char *s,int raw,int saved,int mode,int req,int expected,const char *want) {
 uint16_t in[1024],out[1024],w[1024];int32_t n=convert(s,in),written=-1;
 int rc=StUnicodeNormalize(in,n,raw,saved,mode,req,out,1024,&written);
 int ok=rc==expected;
 if(!expected&&want) { int len=convert(want,w);ok=ok&&written==len&&!memcmp(out,w,len*2); }
 check(name,ok);
}
int main(void) {
 uint16_t a[1024],b[3200],out[1024];int32_t n,m,r;char bytes[4096],digest[65];
 check("supplementary_scalar",StUnicodeScalars((uint16_t[]){0x41,0xd83d,0xde00},3)==2);
 check("unpaired_surrogate",StUnicodeScalars((uint16_t[]){0xd800},1)==-1);
 normal("required_unicode_whitespace","\xe3\x80\x80",8,8,0,1,1,0);
 normal("name_preserves_compatibility","\xef\xbc\xa1",8,8,0,1,0,"\xef\xbc\xa1");
 normal("student_number_nfkc_upper"," \xef\xbd\x81\xef\xbc\x91-2 ",15,15,5,1,0,"A1-2");
 normal("student_number_invalid_symbol","A_1",15,15,5,1,3,0);
 normal("name_key_nfkc_upper_no_space","\xef\xbd\x81\xe3\x80\x80" "b",8,320,2,1,0,"AB");
 normal("kana_nfkc_hiragana_spaces","\xef\xbe\x94\xef\xbe\x8f  \xe3\x81\xa0",36,18,3,1,0,"\xe3\x83\xa4\xe3\x83\x9e \xe3\x83\x80");
 normal("kana_key_removes_space","\xe3\x82\x84\xe3\x80\x80\xe3\x81\xbe",36,36,4,1,0,"\xe3\x83\xa4\xe3\x83\x9e");
 normal("kana_invalid_latin","ABC",36,18,3,1,3,0);
 normal("raw_limit_before_nfkc","123456789",8,8,0,1,2,0);
 normal("saved_scalar_limit","123456789",12,8,0,1,2,0);
 normal("control_rejected","a\tb",12,12,0,1,2,0);
 normal("remarks_crlf_to_lf"," a\r\nb\rc ",120,120,1,0,0,"a\nb\nc");
 normal("postal_remove_hyphen","\xef\xbc\x91\xef\xbc\x92\xef\xbc\x93-4567",10,7,7,1,0,"1234567");
 normal("phone_parentheses_hyphens","(03) 1234-5678",20,16,8,0,0,"0312345678");
 normal("phone_international","+81 90-1234-5678",20,16,8,0,0,"+819012345678");
 normal("phone_invalid_international_zero","+01234567",20,16,8,0,3,0);
 normal("email_domain_only_lowercase","User+X@EXAMPLE.JP",60,60,9,0,0,"User+X@example.jp");
 normal("email_no_nfkc","\xef\xbc\xa1@example.jp",60,60,9,0,3,0);
 normal("email_double_dot","a..b@example.jp",60,60,9,0,3,0);
 normal("optional_blank","   ",60,60,9,0,0,"");
 n=convert("A\\u{41}\xf0\x9f\x98\x80",a);
 r=StUnicodeEscape(a,n,0,b,3200,&m);check("escape_encode",r==0&&m>n);
 r=StUnicodeEscape(b,m,1,out,1024,&m);check("escape_roundtrip_literal_backslash",r==0&&m==n&&!memcmp(a,out,n*2));
 n=convert("\\u{D800}",a);r=StUnicodeEscape(a,n,1,out,1024,&m);check("escape_surrogate_rejected",r==3);
 n=convert("\\u{110000}",a);r=StUnicodeEscape(a,n,1,out,1024,&m);check("escape_out_of_range_rejected",r==3);
 n=convert("\\u{1F600}",a);r=StUnicodeEscape(a,n,1,out,1,&m);check("escape_capacity_atomic_scalar",r!=0);
 n=convert("ABC",a);r=StUnicodeToJob(a,n,1399,bytes,4096,&m);
 check("job_ccsid1399_encode",r==0);
 if(r==0) { r=StUnicodeFromJob(bytes,m,1399,out,1024,&m);check("job_ccsid1399_roundtrip",r==0&&m==n&&!memcmp(a,out,n*2)); }
 n=convert("\xf0\x9f\x98\x80",a);r=StUnicodeToJob(a,n,37,bytes,4096,&m);check("unrepresentable_no_substitution",r==4&&m==0);
 StUnicodeDigest(0,0,digest);digest[64]=0;
 check("sha256_empty",!strcmp(digest,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"));
 check("approved_path_outside_prefix",open_path("/other/input.txt")!=0);
 check("approved_path_traversal",open_path("/stuapp/approved/../input.txt")!=0);
 check("approved_path_nested",open_path("/stuapp/approved/sub/input.txt")!=0);
 check("approved_path_command_chars",open_path("/stuapp/approved/a;cmd.txt")!=0);
 printf("RESULT tests=%d failures=%d\n",tests,failures);return failures?1:0;
}
