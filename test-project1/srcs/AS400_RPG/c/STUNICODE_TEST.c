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

 {int32_t used=0,advance=0,w=0;
 n=convert("ABCDE",a);r=StTextWindow(a,n,0,37,bytes,3,&used,&advance);
 check("text_window_bounded_prefix",r==0&&used==3&&advance==3);
 r=StUnicodeFromJob(bytes,3,37,out,1024,&m);
 check("text_window_roundtrip_prefix",r==0&&m==3&&!memcmp(a,out,6));
 n=convert("AB\\nCD",a); /* literal backslash-n is ordinary text */
 r=StTextWindow(a,n,0,37,bytes,128,&used,&advance);
 check("text_normal_backslash_literal",r==0&&used==n&&advance==n);
 n=convert("AB\nCD",a);a[2]=0x0a;a[3]='C';a[4]='D';n=5;
 r=StTextWindow(a,n,0,37,bytes,128,&used,&advance);
 check("text_original_lf_boundary",r==0&&used==2&&advance==3);
 m=convert("X",b);r=StTextSplice(a,n,0,used,b,m,out,1024,&w);
 check("text_splice_preserves_lf_and_tail",r==0&&w==4&&out[0]=='X'&&out[1]==10&&out[2]=='C'&&out[3]=='D');
 /* Explicit supplementary scalar to test UTF16 boundary preservation. */
 a[0]='A';a[1]=0xd83d;a[2]=0xde00;a[3]='B';n=4;
 r=StTextWindow(a,n,2,37,bytes,128,&used,&advance);
 check("text_window_rejects_surrogate_midpoint",r!=0);
 r=StTextSplice(a,n,1,1,b,m,out,1024,&w);
 check("text_splice_rejects_partial_surrogate",r!=0);
 r=StTextWindow(a,n,0,37,bytes,128,&used,&advance);
 check("text_unrepresentable_retains_raw",r==4&&a[1]==0xd83d&&a[2]==0xde00);
 r=StTextEscapeWindow(a,n,1,out,8,&used,&w);
 check("text_escape_no_partial_token",r==0&&used==0&&w==0);
 r=StTextEscapeWindow(a,n,1,out,9,&used,&w);
 check("text_escape_complete_scalar_token",r==0&&used==2&&w==9);
 r=StUnicodeEscape(out,w,1,b,3200,&m);
 check("text_escape_window_roundtrip",r==0&&m==2&&b[0]==0xd83d&&b[1]==0xde00);
 a[0]=10;n=1;r=StUnicodeEscape(a,n,0,b,3200,&m);
 check("text_unicode_lf_explicit_token",r==0&&m==2&&b[0]==0x5c&&b[1]=='n');
 r=StUnicodeEscape(b,m,1,out,1024,&w);
 check("text_unicode_lf_roundtrip",r==0&&w==1&&out[0]==10);
 r=StTextSplice(a,n,0,0,b,2,out,1,&w);
 check("text_splice_capacity_refusal",r!=0&&a[0]==10);
 }

 n=convert("123456789",a);check("text_apply_year_capacity_refused",StTextLimit(a,n,8,4)!=0);
 n=convert("12345",a);check("text_apply_year_scalar_limit_refused",StTextLimit(a,n,8,4)!=0);
 n=convert("1234",a);check("text_apply_year_exact_limit",StTextLimit(a,n,8,4)==0);
 a[0]=0xd83d;a[1]=0xde00;a[2]=0xd83d;a[3]=0xde00;a[4]=0xd83d;a[5]=0xde00;a[6]=0xd83d;a[7]=0xde00;
 check("text_apply_supplementary_exact_raw_budget",StTextLimit(a,8,8,4)==0);
 a[0]=0xd800;check("text_apply_invalid_utf16_refused",StTextLimit(a,1,8,4)!=0);
 for(n=0;n<61;n++)a[n]='A';
 check("text_apply_reason_scalar_limit_refused",StTextLimit(a,61,120,60)!=0);
 check("text_apply_reason_exact_limit",StTextLimit(a,60,120,60)==0);
 check("text_apply_invalid_target_capacity_refused",StTextLimit(a,60,-1,60)!=0);
 printf("RESULT tests=%d failures=%d\n",tests,failures);return failures?1:0;
}
