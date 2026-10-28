/* Execute the production boundary in this test translation unit so idle and
   encryption lifetime can be tested without changing the OS clock or exposing
   a test clock through the application API. No database is contacted. */
#include "../bridge/student_bridge.c"
static int checks, failures;
#define CHECK(expr,label) do { ++checks; if(!(expr)){++failures;fprintf(stderr,"FAIL %s\n",label);} } while(0)
static int zero(const void *data,size_t size){const unsigned char *p=data;for(size_t i=0;i<size;i++)if(p[i])return 0;return 1;}
int main(void){
  ST_VALUE owner={0},session={0},fields[64];int32_t role=-1;char binding[64],first[64];
  CHECK(STSAMPLECHECK()!=0,"no session before open");
  CHECK(STIDENTITY(&owner,&session,&role,binding)!=0,"identity requires live sample window");
  CHECK(STSAMPLEOPEN()==0,"sample window open");
  _putenv("REMOTE_USER=forged");_putenv("ST_TRUSTED_ROLE=Viewer");_putenv("ST_LOGIN_SESSION_ID=forged");
  CHECK(STIDENTITY(&owner,&session,&role,binding)==0,"no login or environment identity required");
  CHECK(owner.length==11 && owner.null_flag==0 && !memcmp(owner.data,"sample-user",11),"fixed sample actor ignores environment");
  CHECK(role==2,"fixed sample operation role");
  CHECK(session.length==64 && STHEX(&session)==0,"independent 256-bit sample session");
  memcpy(first,session.data,64);
  CHECK(STSAMPLECHECK()==0,"live session");
  uint64_t previous=sample_last_activity;
  CHECK(STSAMPLETOUCH()==0 && sample_last_activity>=previous,"real input activity touch");
  const unsigned char plain[]="raw\n\xe6\x97\xa5\xe6\x9c\xac\xf0\x9f\x98\x80";
  unsigned char sealed[256],decoded[256];int bytes=0,decoded_bytes=0;
  CHECK(crypt(1,plain,sizeof plain-1,sealed,&bytes,"window-kind-owner")==0,"production AES GCM encryption");
  CHECK(crypt(0,sealed,bytes,decoded,&decoded_bytes,"window-kind-owner")==0 &&
        decoded_bytes==(int)sizeof plain-1 && !memcmp(decoded,plain,sizeof plain-1),"raw encryption roundtrip");
  CHECK(crypt(0,sealed,bytes,decoded,&decoded_bytes,"other-window")!=0,"window purpose AAD mismatch");
  sealed[12]^=1;
  CHECK(crypt(0,sealed,bytes,decoded,&decoded_bytes,"window-kind-owner")!=0,"tampered ciphertext rejected");
  sealed[12]^=1;
  CHECK(STSAMPLEOPEN()==0,"new sample window lifetime");
  CHECK(STIDENTITY(&owner,&session,&role,binding)==0 && memcmp(first,session.data,64)!=0,"same actor has a different window session");
  CHECK(crypt(0,sealed,bytes,decoded,&decoded_bytes,"window-kind-owner")!=0,"old process key cannot decrypt after new window");
  sample_last_activity=(uint64_t)GetTickCount64()-UINT64_C(1800001);
  CHECK(STSAMPLECHECK()!=0,"30-minute idle invalidates session");
  CHECK(STSAMPLETOUCH()!=0,"activity cannot revive expired session");
  CHECK(zero(sample_key,sizeof sample_key) && zero(sample_session,sizeof sample_session),"expired secrets cleared");
  CHECK(STSAMPLEOPEN()==0 && STSAMPLECLOSE()==0,"normal close");
  CHECK(STIDENTITY(&owner,&session,&role,binding)!=0 && STSAMPLECHECK()!=0,"closed sample session invalid");
  CHECK(zero(sample_key,sizeof sample_key) && zero(sample_binding,sizeof sample_binding),"normal close clears secrets");

  memset(fields,0,sizeof fields);
  for(int i=0;i<64;i++)fields[i].null_flag=-1;
  CHECK(STTEXTCHECK(fields)==0,"NULL fields preserve zero length");
  fields[0].null_flag=0;
  CHECK(STTEXTCHECK(fields)==0,"empty value distinct from NULL");
  value(fields,"\xe6\x97\xa5\xe6\x9c\xac" "e\xcc\x81\xf0\x9f\x98\x80",13);
  /* Use explicit bytes, including supplementary and combining characters. */
  CHECK(STTEXTCHECK(fields)==0,"UTF8 Japanese combining supplementary raw");
  fields[0].data[0]=0;
  CHECK(STTEXTCHECK(fields)!=0,"embedded NUL rejected");
  fields[0].data[0]=(char)0xc0;fields[0].data[1]=(char)0x80;fields[0].length=2;
  CHECK(STTEXTCHECK(fields)!=0,"overlong UTF8 rejected");
  fields[0].data[0]=(char)0xed;fields[0].data[1]=(char)0xa0;fields[0].data[2]=(char)0x80;fields[0].length=3;
  CHECK(STTEXTCHECK(fields)!=0,"UTF8 surrogate rejected");
  fields[0].length=0;fields[0].null_flag=7;
  CHECK(STTEXTCHECK(fields)!=0,"invalid NULL indicator rejected");
  fields[0].length=1;fields[0].null_flag=-1;
  CHECK(STTEXTCHECK(fields)!=0,"NULL must have zero real length");
  fields[0].null_flag=0;fields[0].length=-1;
  CHECK(STTEXTCHECK(fields)!=0,"negative real length rejected");
  fields[0].length=1025;
  CHECK(STTEXTCHECK(fields)!=0,"field capacity overflow rejected");
  for(int i=0;i<64;i++){fields[i].length=1024;fields[i].null_flag=0;memset(fields[i].data,'A',1024);}
  CHECK(STTEXTCHECK(fields)==0,"65536 raw bytes represented exactly");
  CHECK(fields[0].length==1024 && fields[63].data[1023]=='A',"boundary does not normalise or truncate raw");
  CHECK(STTEXTCHECK(NULL)!=0,"null message rejected");
  printf("%s sample boundary %d/%d\n",failures?"FAIL":"PASS",checks-failures,checks);
  return failures?1:0;
}
