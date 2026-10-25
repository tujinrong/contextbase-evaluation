#define _POSIX_C_SOURCE 200809L
#include "student_abi.h"
#include <inttypes.h>
#include "fields.h"
#include "sql_catalog.h"
#ifdef _WIN32
#include <windows.h>
#endif
#include <sql.h>
#include <sqlext.h>
#include <unicode/ustring.h>
#include <unicode/unorm2.h>
#include <unicode/uchar.h>
#include <unicode/utf16.h>
#include <openssl/evp.h>
#include <openssl/hmac.h>
#include <openssl/rand.h>
#include <openssl/crypto.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <ctype.h>
#include <limits.h>
#ifdef _WIN32
#include <io.h>
#define ST_FILENO _fileno
#define ST_DUP _dup
#define ST_DUP2 _dup2
#define ST_CLOSE _close
#else
#include <unistd.h>
#define ST_FILENO fileno
#define ST_DUP dup
#define ST_DUP2 dup2
#define ST_CLOSE close
#endif
/* C boundary only: no student status, seat, duplicate, or audit decisions here. */
typedef struct {SQLHENV env;SQLHDBC db;int transaction;} Connection;
_Static_assert(sizeof(SQLWCHAR)==2,"ODBC SQLWCHAR must be UTF-16");
static int utf16(const char *s,int n,UChar *out,int cap,int *len){UErrorCode e=U_ZERO_ERROR;u_strFromUTF8(out,cap,len,s,n,&e);return U_SUCCESS(e)?0:-1;}
static int utf8(const UChar *s,int n,char *out,int cap,int *len){UErrorCode e=U_ZERO_ERROR;u_strToUTF8(out,cap,len,s,n,&e);return U_SUCCESS(e)?0:-1;}
static int scalar(const char *s,int n){UChar b[4096];int l;if(n<0||n>1024||utf16(s,n,b,4096,&l))return -1;return u_countChar32(b,l);}
static void value(ST_VALUE *v,const char *s,int n){memset(v,0,sizeof(*v));memset(v->data,32,sizeof v->data);if(n<0){v->null_flag=-1;return;}if(n>1024)n=1024;v->length=n;memcpy(v->data,s,(size_t)n);}
static int field(const char *s){for(int i=0;i<FIELD_COUNT;i++)if(!strcmp(s,field_names[i]))return i;return -1;}
static int hexdigit(char c){if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;if(c>='A'&&c<='F')return c-'A'+10;return -1;}
static int decode(const char *s,size_t n,char *out,size_t cap){size_t j=0;for(size_t i=0;i<n;i++){unsigned char c=(unsigned char)s[i];if(c=='%'){if(i+2>=n||hexdigit(s[i+1])<0||hexdigit(s[i+2])<0)return -1;c=(unsigned char)(hexdigit(s[i+1])*16+hexdigit(s[i+2]));i+=2;}else if(c=='+')c=' ';if(c==0||j+1>=cap)return -1;out[j++]=(char)c;}out[j]=0;if(scalar(out,(int)j)<0)return -1;return (int)j;}
static int parse(const char *s,ST_VALUE *fields,int http){int invalid=0;while(*s){const char *end=strchr(s,'&');if(!end)end=s+strlen(s);const char *eq=memchr(s,'=',(size_t)(end-s));if(!eq)return -1;char key[80],val[1025];int kn=decode(s,(size_t)(eq-s),key,sizeof key);int vn=decode(eq+1,(size_t)(end-eq-1),val,sizeof val);int f=field(key);if(kn<0||vn<0)return -1;
if(f<0||(http&&f>=41&&f<=44)){invalid=-2;s=*end?end+1:end;continue;}
if(http&&!strcmp(key,"statusCode")){if(vn!=2||val[0]!='0'||val[1]<'1'||val[1]>'4'){invalid=-2;s=*end?end+1:end;continue;}int target=41+val[1]-'1';if(fields[target].null_flag==0){invalid=-2;s=*end?end+1:end;continue;}value(fields+target,"1",1);value(fields+f,val,vn);}
else{if(fields[f].null_flag==0)return -1;value(fields+f,val,vn);}
s=*end?end+1:end;}return invalid;}
static int http_contract(const ST_VALUE *f){
  char action[17]={0};if(f[0].length>16)return -1;
  if(f[0].null_flag==0)memcpy(action,f[0].data,(size_t)f[0].length);
  const char *common="|action|contextId|contextRevision|tabId|csrfToken|flashId|";
  const char *search="|studentNo|name|classId|statusCode|page|pageSize|sortKey|sortDirection|openStudentId|pageTarget|studentId|navigation|";
  const char *editor="|studentId|expectedVersion|studentNo|studentName|studentNameKana|birthEra|birthYear|birthMonth|birthDay|genderCode|postalCode|prefectureCode|addressLine1|addressLine2|phoneNumber|emailAddress|admissionDate|enrollmentStatusCode|enrollmentEndDate|classId|emergencyContactName|relationshipCode|emergencyPhoneNumber|remarks|schoolYear|gradeCode|reason|editorId|confirmationToken|deleteReason|";
  const char *actions="|INITIAL|SEARCH|PAGE|RESUME|CLEAR|OPTIONS|NEW|EDIT|CREATE|UPDATE|DELETE|RESET|RELOAD|BACK|CONFIRM|CANCEL|";
  if(*action){char token[32];snprintf(token,sizeof token,"|%s|",action);if(!strstr(actions,token))return -1;}
  const char *method=getenv("REQUEST_METHOD");
  if(method&&!strcmp(method,"POST")&&!*action)return -1;
  if(method&&!strcmp(method,"POST")&&(!strcmp(action,"NEW")||!strcmp(action,"EDIT")||!strcmp(action,"RESUME")||!strcmp(action,"INITIAL")))return -1;
  int search_request=f[30].null_flag==-1 && (!*action||!strcmp(action,"INITIAL")||!strcmp(action,"SEARCH")||!strcmp(action,"PAGE")||!strcmp(action,"RESUME")||!strcmp(action,"CLEAR")||!strcmp(action,"OPTIONS")||!strcmp(action,"NEW")||!strcmp(action,"EDIT"));
  for(int i=0;i<FIELD_COUNT;i++)if(f[i].null_flag==0){
    if(search_request&&i>=41&&i<=44)continue;
    if(i==34)return -1;
    char token[96];snprintf(token,sizeof token,"|%s|",field_names[i]);
    if(!strstr(common,token)&&!strstr(search_request?search:editor,token))return search_request?-2:-1;
  }
  return 0;
}
int32_t STHTTP(ST_VALUE *f){
 for(int i=0;i<64;i++)value(f+i,NULL,-1);
 const char *method=getenv("REQUEST_METHOD");if(!method||(strcmp(method,"GET")&&strcmp(method,"POST")))return -1;
 const char *query=getenv("QUERY_STRING");if(query&&strlen(query)>8192)return -1;
 int invalid=0;if(query){int r=parse(query,f,1);if(r==-1)return -1;if(r)invalid=-2;}
 if(!strcmp(method,"POST")){
  const char *ct=getenv("CONTENT_TYPE"),*cl=getenv("CONTENT_LENGTH");if(!ct||strcmp(ct,"application/x-www-form-urlencoded")||!cl||!*cl)return -1;
  uint64_t n=0;for(const char *p=cl;*p;p++){if(*p<'0'||*p>'9'||n>65536)return -1;n=n*10+(uint64_t)(*p-'0');}if(n>65536)return -1;
  char *b=calloc((size_t)n+1,1);if(!b)return -1;size_t read=fread(b,1,(size_t)n,stdin);int extra=fgetc(stdin);
  int r=(read==n&&extra==EOF&&!memchr(b,0,(size_t)n))?parse(b,f,1):-1;OPENSSL_cleanse(b,(size_t)n);free(b);if(r==-1)return -1;if(r)invalid=-2;
 }else if(f[0].null_flag==0&&f[0].length==6&&!memcmp(f[0].data,"SEARCH",6))return -1;
 int contract=http_contract(f);if(contract)return contract;
 if(invalid){int search=f[30].null_flag==-1&&(f[0].null_flag==-1||!memcmp(f[0].data,"SEARCH",6)||!memcmp(f[0].data,"PAGE",4)||!memcmp(f[0].data,"CLEAR",5)||!memcmp(f[0].data,"OPTIONS",7)||!memcmp(f[0].data,"INITIAL",7)||!memcmp(f[0].data,"RESUME",6));return search?-2:-1;}
 if(f[61].null_flag==0)f[4]=f[61];return 0;
}
int32_t STCLIREAD(const char *path,int32_t length,ST_VALUE *f){if(length<1||length>4095)return -1;char name[4096];memcpy(name,path,(size_t)length);name[length]=0;FILE *file=fopen(name,"rb");if(!file)return -1;char body[65538];size_t n=fread(body,1,sizeof body-1,file);int bad=ferror(file)||n>65536||!feof(file);fclose(file);if(bad||memchr(body,0,n))return -1;while(n>0&&(body[n-1]=='\r'||body[n-1]=='\n'))n--;body[n]=0;for(int i=0;i<64;i++)value(f+i,NULL,-1);return parse(body,f,0);}
static int key(unsigned char out[32]){const char *v=getenv("STUDENT_STATE_KEY_HEX");if(!v||strlen(v)!=64)return -1;for(int i=0;i<32;i++){int a=hexdigit(v[2*i]),b=hexdigit(v[2*i+1]);if(a<0||b<0)return -1;out[i]=(unsigned char)(a*16+b);}return 0;}
int32_t STRANDOM(char *out){unsigned char b[32];if(RAND_bytes(b,32)!=1)return -1;const char *hex="0123456789abcdef";for(int i=0;i<32;i++){out[2*i]=hex[b[i]>>4];out[2*i+1]=hex[b[i]&15];}return 0;}
int32_t STIDENTITY(ST_VALUE *owner,ST_VALUE *session,int32_t *role,char *csrf){const char *u=getenv("REMOTE_USER"),*s=getenv("ST_LOGIN_SESSION_ID"),*r=getenv("ST_TRUSTED_ROLE");if(!u||!s||!r||!*u||scalar(u,(int)strlen(u))>64||scalar(u,(int)strlen(u))<1||strlen(s)<1||strlen(s)>64)return -1;for(const char *p=s;*p;p++)if(!(isalnum((unsigned char)*p)||*p=='-'))return -1;*role=!strcmp(r,"Viewer")?0:!strcmp(r,"Staff")?1:!strcmp(r,"Administrator")?2:-1;if(*role<0)return -1;value(owner,u,(int)strlen(u));value(session,s,(int)strlen(s));unsigned char k[32],digest[32];unsigned int length=0;char data[512];int n=snprintf(data,sizeof data,"csrf\n%s\n%s",u,s);if(key(k)||!HMAC(EVP_sha256(),k,32,(unsigned char*)data,(size_t)n,digest,&length)||length!=32)return -1;const char *hex="0123456789abcdef";for(int i=0;i<32;i++){csrf[i*2]=hex[digest[i]>>4];csrf[i*2+1]=hex[digest[i]&15];}OPENSSL_cleanse(k,32);return 0;}
int32_t STHEX(const ST_VALUE *v){if(v->null_flag!=0||v->length!=64)return -1;for(int i=0;i<64;i++)if(hexdigit(v->data[i])<0)return -1;return 0;}
int32_t STCSRF(const ST_VALUE *v,const char *expected){return v->length==64&&CRYPTO_memcmp(v->data,expected,64)==0?0:-1;}
int32_t STPOST(void){const char *m=getenv("REQUEST_METHOD");return m&&!strcmp(m,"POST")?1:0;}
int32_t STINTEGER(const ST_VALUE *v,int64_t *out){if(v->null_flag==-1||v->length<1||v->length>19)return -1;uint64_t n=0;for(int i=0;i<v->length;i++){unsigned c=(unsigned char)v->data[i];if(c<'0'||c>'9'||n>((uint64_t)INT64_MAX-(c-'0'))/10)return -1;n=n*10+c-'0';}*out=(int64_t)n;return 0;}
/* Generic NFKC/scalar operations. Policy selection remains in STNORM/STVALID. */
int32_t STUNICODE(int32_t mode,const ST_VALUE *src,ST_VALUE *dst,int32_t rawmax,int32_t savedmax){if(src->null_flag==-1){value(dst,NULL,-1);return 0;}if(scalar(src->data,src->length)<0||scalar(src->data,src->length)>rawmax)return -1;UChar in[4096],norm[4096],result[4096];int l,n=0,j=0;if(utf16(src->data,src->length,in,4096,&l))return -1;UErrorCode e=U_ZERO_ERROR;if(mode==2||mode==3||mode==4||mode==5||mode==6||mode==7){const UNormalizer2 *nfkc=unorm2_getNFKCInstance(&e);n=unorm2_normalize(nfkc,in,l,norm,4096,&e);if(U_FAILURE(e))return -1;}else{memcpy(norm,in,(size_t)l*sizeof(UChar));n=l;}
int pending=0;for(int i=0;i<n;){UChar32 c;U16_NEXT(norm,i,n,c);if(c==0||u_charType(c)==U_CONTROL_CHAR){if(mode==8&&(c==10||c==13)){if(c==13&&i<n&&norm[i]==10)i++;c=10;}else return -1;}int ws=u_isUWhiteSpace(c)||c==0x85;if(mode==2||mode==6||mode==7){if(ws)continue;}else if(mode==3){if(ws){pending=j>0;continue;}if(pending){result[j++]=' ';pending=0;}}else if(j==0&&ws)continue;if(mode==2||mode==4)c=u_toupper(c);if(mode==3&&((c>=0x3041&&c<=0x3096)||c==0x309D||c==0x309E))c+=0x60;if((mode==6||mode==7)&&(c=='-'||c==0x2010||c==0x2011||c==0x2212||(mode==7&&(c=='('||c==')'))))continue;UBool err=0;U16_APPEND(result,j,4096,c,err);if(err)return -1;}
if(mode!=2&&mode!=6&&mode!=7)while(j>0){int at=j;UChar32 c;U16_PREV(result,0,at,c);if(!u_isUWhiteSpace(c)&&c!=0x85)break;j=at;}if(u_countChar32(result,j)>savedmax)return -1;int bytes;if(utf8(result,j,dst->data,1024,&bytes))return -1;if(bytes<1024)memset(dst->data+bytes,32,(size_t)(1024-bytes));dst->length=bytes;dst->null_flag=bytes?0:-1;return 0;}
int32_t STPATTERN(ST_VALUE *v,int32_t prefix){char out[1024];int j=0;if(v->null_flag==-1)return 0;if(!prefix)out[j++]='%';for(int i=0;i<v->length;i++){char c=v->data[i];if(c=='!'||c=='%'||c=='_'||c=='[')out[j++]='!';if(j>=1022)return -1;out[j++]=c;}out[j++]='%';value(v,out,j);return 0;}
int32_t STKANA(const ST_VALUE *v){UChar b[4096];int n;if(utf16(v->data,v->length,b,4096,&n))return -1;for(int i=0;i<n;){UChar32 c;U16_NEXT(b,i,n,c);if(!((c>=0x30A1&&c<=0x30FA)||c==0x30FC||c==0x30FB||c==0x30FD||c==0x30FE||c==32))return -1;}return 0;}
int32_t STEMAIL(ST_VALUE *v){if(v->null_flag==-1)return 0;char b[1025];memcpy(b,v->data,(size_t)v->length);b[v->length]=0;char *at=strchr(b,'@');if(!at||strchr(at+1,'@')||at==b||at-b>64||b[0]=='.'||at[-1]=='.'||strstr(b,".."))return -1;for(char *p=b;p<at;p++)if(!isalnum((unsigned char)*p)&&!strchr(".!#$%&'*+-/=?^_`{|}~",*p))return -1;char *p=at+1;int labels=0;while(*p){char *end=strchr(p,'.');if(!end)end=p+strlen(p);int n=(int)(end-p);if(n<1||n>63||!isalnum((unsigned char)*p)||!isalnum((unsigned char)end[-1]))return -1;for(char *q=p;q<end;q++){if((unsigned char)*q>127||(!isalnum((unsigned char)*q)&&*q!='-'))return -1;*q=(char)tolower((unsigned char)*q);}labels++;p=*end?end+1:end;}if(labels<2||at[1]==0||b[v->length-1]=='.')return -1;value(v,b,v->length);return 0;}
int32_t STHASH(void *data,int32_t length,unsigned char out[32]){unsigned int n=0;return length>=0&&EVP_Digest(data,(size_t)length,out,&n,EVP_sha256(),NULL)==1&&n==32?0:-1;}
void *STHASHSTART(void){EVP_MD_CTX *ctx=EVP_MD_CTX_new();if(!ctx||EVP_DigestInit_ex(ctx,EVP_sha256(),NULL)!=1){EVP_MD_CTX_free(ctx);return NULL;}return ctx;}
int32_t STHASHADD(void *ctx,const ST_VALUE *v){int32_t n=v->null_flag==-1?-1:v->length;if(EVP_DigestUpdate(ctx,&n,sizeof n)!=1)return -1;return n>0&&EVP_DigestUpdate(ctx,v->data,(size_t)n)!=1?-1:0;}
int32_t STHASHEND(void *ctx,unsigned char out[32]){unsigned int n=0;int ok=EVP_DigestFinal_ex(ctx,out,&n)==1&&n==32;EVP_MD_CTX_free(ctx);return ok?0:-1;}
int32_t STDIAG(SQLSMALLINT kind,SQLHANDLE handle,ST_DB_RESULT *r){SQLWCHAR state[6],message[256];SQLSMALLINT len=0;SQLINTEGER native=0;if(SQL_SUCCEEDED(SQLGetDiagRecW(kind,handle,1,state,&native,message,256,&len))){for(int i=0;i<5;i++)r->sqlstate[i]=(char)state[i];r->native_error_code=native;}else memcpy(r->sqlstate,"HY000",5);r->error_class=1;return -1;}
void *STCONNECT(void){Connection *c=calloc(1,sizeof(*c));if(!c)return NULL;if(SQLAllocHandle(SQL_HANDLE_ENV,SQL_NULL_HANDLE,&c->env)!=SQL_SUCCESS)goto fail;if(SQLSetEnvAttr(c->env,SQL_ATTR_ODBC_VERSION,(SQLPOINTER)SQL_OV_ODBC3,0)!=SQL_SUCCESS)goto fail;if(SQLAllocHandle(SQL_HANDLE_DBC,c->env,&c->db)!=SQL_SUCCESS)goto fail;SQLSetConnectAttr(c->db,SQL_LOGIN_TIMEOUT,(SQLPOINTER)10,0);const char *dsn=getenv("STUDENT_ODBC_DSN");if(!dsn||strspn(dsn,"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")!=strlen(dsn)||!strlen(dsn))goto fail;char str[256];int n=snprintf(str,sizeof str,"DSN=%s;Encrypt=Yes;TrustServerCertificate=No;",dsn);SQLWCHAR wide[256];int l;if(utf16(str,n,(UChar*)wide,256,&l))goto fail;SQLRETURN rc=SQLDriverConnectW(c->db,NULL,wide,(SQLSMALLINT)l,NULL,0,NULL,SQL_DRIVER_NOPROMPT);if(!SQL_SUCCEEDED(rc))goto fail;return c;
fail:if(c->db)SQLFreeHandle(SQL_HANDLE_DBC,c->db);if(c->env)SQLFreeHandle(SQL_HANDLE_ENV,c->env);free(c);return NULL;}
int32_t STCLOSE(void *ptr){Connection *c=ptr;if(!c)return 0;if(c->transaction)SQLEndTran(SQL_HANDLE_DBC,c->db,SQL_ROLLBACK);SQLDisconnect(c->db);SQLFreeHandle(SQL_HANDLE_DBC,c->db);SQLFreeHandle(SQL_HANDLE_ENV,c->env);free(c);return 0;}
int32_t STBEGIN(void *ptr,int32_t snapshot,ST_DB_RESULT *r){Connection *c=ptr;memset(r,0,sizeof(*r));if(!c||c->transaction)return -1;if(SQLSetConnectAttr(c->db,SQL_ATTR_AUTOCOMMIT,(SQLPOINTER)SQL_AUTOCOMMIT_OFF,0)!=SQL_SUCCESS)return STDIAG(SQL_HANDLE_DBC,c->db,r);c->transaction=1;SQLHSTMT st;if(SQLAllocHandle(SQL_HANDLE_STMT,c->db,&st)!=SQL_SUCCESS)return -1;const char *q=snapshot?"SET XACT_ABORT ON; SET TRANSACTION ISOLATION LEVEL SNAPSHOT;":"SET XACT_ABORT ON; SET TRANSACTION ISOLATION LEVEL READ COMMITTED; DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=N'test-project1:student-write',@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=5000,@DbPrincipal='public'; SELECT @r;";SQLWCHAR w[1024];int l;utf16(q,(int)strlen(q),(UChar*)w,1024,&l);SQLRETURN rc=SQLExecDirectW(st,w,l);if(!SQL_SUCCEEDED(rc)){STDIAG(SQL_HANDLE_STMT,st,r);SQLFreeHandle(SQL_HANDLE_STMT,st);return -1;}if(!snapshot){SQLSMALLINT cols=0;SQLNumResultCols(st,&cols);while(cols==0&&SQLMoreResults(st)==SQL_SUCCESS)SQLNumResultCols(st,&cols);SQLINTEGER gate=-999;SQLLEN ind;if(cols!=1||SQLFetch(st)!=SQL_SUCCESS||SQLGetData(st,1,SQL_C_SLONG,&gate,sizeof gate,&ind)!=SQL_SUCCESS||gate<0){r->native_error_code=gate;r->error_class=2;SQLFreeHandle(SQL_HANDLE_STMT,st);return -1;}}SQLFreeHandle(SQL_HANDLE_STMT,st);return 0;}
int32_t STEND(void *ptr,int32_t commit,ST_DB_RESULT *r){Connection *c=ptr;if(!c||!c->transaction)return -1;SQLRETURN rc=SQLEndTran(SQL_HANDLE_DBC,c->db,commit?SQL_COMMIT:SQL_ROLLBACK);if(!SQL_SUCCEEDED(rc))return STDIAG(SQL_HANDLE_DBC,c->db,r);c->transaction=0;rc=SQLSetConnectAttr(c->db,SQL_ATTR_AUTOCOMMIT,(SQLPOINTER)SQL_AUTOCOMMIT_ON,0);return SQL_SUCCEEDED(rc)?0:STDIAG(SQL_HANDLE_DBC,c->db,r);}
int32_t STDBOP(void *ptr,const ST_DB_REQUEST *q,ST_DB_RESULT *r){Connection *c=ptr;memset(r,0,sizeof(*r));if(!c||q->parameter_count<0||q->parameter_count>40)return -1;char id[13];memcpy(id,q->command_id,12);id[12]=0;for(int i=11;i>=0&&id[i]==' ';i--)id[i]=0;const char *sql=NULL;int entry=-1;for(size_t i=0;i<sizeof(catalog)/sizeof(catalog[0]);i++)if(!strcmp(id,catalog[i].id)){sql=catalog[i].sql;entry=(int)i;break;}if(!sql||q->parameter_count!=catalog[entry].count)return -1;SQLHSTMT st;if(SQLAllocHandle(SQL_HANDLE_STMT,c->db,&st)!=SQL_SUCCESS)return -1;SQLSetStmtAttr(st,SQL_ATTR_QUERY_TIMEOUT,(SQLPOINTER)30,0);SQLWCHAR w[32768];int len;if(utf16(sql,(int)strlen(sql),(UChar*)w,32768,&len)||!SQL_SUCCEEDED(SQLPrepareW(st,w,len)))goto fail;
SQLLEN inds[40];SQLWCHAR text[40][2048];int64_t ints[40];SQL_DATE_STRUCT dates[40];unsigned char bits[40];
for(int i=0;i<q->parameter_count;i++){const ST_PARAM *p=&q->parameters[i];if(p->byte_length<0||p->byte_length>1048576||(p->null_flag!=-1&&p->null_flag!=0))goto fail;SQLSMALLINT ct,dt;SQLULEN size;SQLLEN buflen;void *data=p->data_pointer;inds[i]=p->null_flag==-1?SQL_NULL_DATA:p->byte_length;
if(p->type_id==1||p->type_id==2){int n;if(p->null_flag==-1)n=0;else if(p->byte_length>1024||utf16(data,p->byte_length,(UChar*)text[i],2048,&n))goto fail;ct=SQL_C_WCHAR;dt=p->type_id==1?SQL_WVARCHAR:SQL_VARCHAR;size=catalog[entry].sizes[i];buflen=(n+1)*(SQLLEN)sizeof(SQLWCHAR);data=text[i];if(p->null_flag==0)inds[i]=n*(SQLLEN)sizeof(SQLWCHAR);}
else if(p->type_id==3||p->type_id==5){ST_VALUE v={0};if(p->byte_length>19)goto fail;v.length=p->byte_length;v.null_flag=p->null_flag;if(p->null_flag==0)memcpy(v.data,data,(size_t)p->byte_length);ints[i]=0;if(p->null_flag==0&&STINTEGER(&v,&ints[i]))goto fail;ct=SQL_C_SBIGINT;dt=p->type_id==3?SQL_BIGINT:SQL_INTEGER;size=19;buflen=8;data=&ints[i];if(p->null_flag==0)inds[i]=8;}
else if(p->type_id==4){char b[11]={0};if(p->null_flag==0){if(p->byte_length!=10)goto fail;memcpy(b,data,10);int y,m,d;if(sscanf(b,"%4d-%2d-%2d",&y,&m,&d)!=3)goto fail;dates[i]=(SQL_DATE_STRUCT){(SQLSMALLINT)y,(SQLUSMALLINT)m,(SQLUSMALLINT)d};}ct=SQL_C_TYPE_DATE;dt=SQL_TYPE_DATE;size=10;buflen=sizeof dates[i];data=&dates[i];if(p->null_flag==0)inds[i]=sizeof dates[i];}
else if(p->type_id==6){ct=SQL_C_BINARY;dt=SQL_LONGVARBINARY;size=(SQLULEN)p->byte_length;buflen=p->byte_length;}
else if(p->type_id==7){bits[i]=p->byte_length==1&&((char*)data)[0]=='1';ct=SQL_C_BIT;dt=SQL_BIT;size=1;buflen=1;data=&bits[i];if(p->null_flag==0)inds[i]=1;}
else goto fail;if(!SQL_SUCCEEDED(SQLBindParameter(st,(SQLUSMALLINT)(i+1),SQL_PARAM_INPUT,ct,dt,size,0,data,buflen,&inds[i])))goto fail;}
{SQLRETURN rc=SQLExecute(st);if(!SQL_SUCCEEDED(rc))goto fail;if(rc==SQL_SUCCESS_WITH_INFO){STDIAG(SQL_HANDLE_STMT,st,r);if(!memcmp(r->sqlstate,"01004",5))goto fail;r->error_class=0;}SQLSMALLINT cols=0;SQLNumResultCols(st,&cols);SQLLEN affected=0;SQLRowCount(st,&affected);r->affected_rows=affected;while(!cols){rc=SQLMoreResults(st);if(rc==SQL_NO_DATA){SQLFreeHandle(SQL_HANDLE_STMT,st);return 0;}if(!SQL_SUCCEEDED(rc))goto fail;SQLNumResultCols(st,&cols);}r->cursor_handle=st;return 0;}
fail:STDIAG(SQL_HANDLE_STMT,st,r);SQLFreeHandle(SQL_HANDLE_STMT,st);return -1;}
int32_t STFETCH(ST_DB_RESULT *r){if(!r->cursor_handle)return 0;SQLRETURN rc=SQLFetch(r->cursor_handle);if(rc==SQL_NO_DATA)return 0;if(rc!=SQL_SUCCESS)return STDIAG(SQL_HANDLE_STMT,r->cursor_handle,r);return 1;}
int32_t STCOLUMN(ST_DB_RESULT *r,int32_t column,ST_VALUE *v){SQLWCHAR b[4096];SQLLEN n=0;SQLRETURN rc=SQLGetData(r->cursor_handle,(SQLUSMALLINT)column,SQL_C_WCHAR,b,sizeof b,&n);if(rc!=SQL_SUCCESS)return STDIAG(SQL_HANDLE_STMT,r->cursor_handle,r);if(n==SQL_NULL_DATA){value(v,NULL,-1);return 0;}if(n<0||n>=(SQLLEN)sizeof b)return -1;int bytes;if(utf8((UChar*)b,(int)(n/2),v->data,1024,&bytes))return -1;if(bytes<1024)memset(v->data+bytes,32,(size_t)(1024-bytes));v->length=bytes;v->null_flag=0;return 0;}
int32_t STCURSOR(ST_DB_RESULT *r){if(r->cursor_handle)SQLFreeHandle(SQL_HANDLE_STMT,r->cursor_handle);r->cursor_handle=NULL;return 0;}
/* Authenticated opaque state. AAD binds identity, session, kind, and tab. */
static int crypt(int encrypt,const unsigned char *src,int n,unsigned char *dst,int *out,const char *aad){unsigned char k[32];if(key(k)||n<0)return -1;EVP_CIPHER_CTX *c=EVP_CIPHER_CTX_new();int l=0,j=0,ok=0;if(!c)goto done;if(encrypt){if(RAND_bytes(dst,12)!=1)goto done;if(EVP_EncryptInit_ex(c,EVP_aes_256_gcm(),NULL,k,dst)!=1||EVP_EncryptUpdate(c,NULL,&l,(const unsigned char*)aad,(int)strlen(aad))!=1||EVP_EncryptUpdate(c,dst+28,&l,src,n)!=1)goto done;j=l;if(EVP_EncryptFinal_ex(c,dst+28+j,&l)!=1||EVP_CIPHER_CTX_ctrl(c,EVP_CTRL_GCM_GET_TAG,16,dst+12)!=1)goto done;*out=j+l+28;ok=1;}else{if(n<28||EVP_DecryptInit_ex(c,EVP_aes_256_gcm(),NULL,k,src)!=1||EVP_DecryptUpdate(c,NULL,&l,(const unsigned char*)aad,(int)strlen(aad))!=1||EVP_DecryptUpdate(c,dst,&l,src+28,n-28)!=1)goto done;j=l;if(EVP_CIPHER_CTX_ctrl(c,EVP_CTRL_GCM_SET_TAG,16,(void*)(src+12))!=1||EVP_DecryptFinal_ex(c,dst+j,&l)!=1)goto done;*out=j+l;ok=1;}done:EVP_CIPHER_CTX_free(c);OPENSSL_cleanse(k,32);return ok?0:-1;}
int32_t STSTATEIO(void *ptr,int32_t operation,char *id,const char *kind,const ST_VALUE *owner,const ST_VALUE *session,const char *tab,void *payload,int32_t capacity,int64_t *revision,int32_t minutes){Connection *c=ptr;if(!c||capacity<0||capacity>2097152)return -1;char knd[17]={0},own[1025]={0},ses[65]={0},tid[65]={0},sid[65]={0};memcpy(knd,kind,16);for(int i=15;i>=0&&knd[i]==' ';i--)knd[i]=0;memcpy(own,owner->data,(size_t)owner->length);memcpy(ses,session->data,(size_t)session->length);memcpy(tid,tab,64);for(int i=63;i>=0&&tid[i]==' ';i--)tid[i]=0;memcpy(sid,id,64);if(operation==1){if(STRANDOM(id))return -1;memcpy(sid,id,64);*revision=1;}for(int i=0;i<64;i++)if(hexdigit(sid[i])<0)return -1;char aad[1400];snprintf(aad,sizeof aad,"state1\n%s\n%s\n%s\n%s",own,ses,knd,tid);unsigned char *buf=malloc((size_t)capacity+28);if(!buf)return -1;int bytes=0;int32_t result=-1;SQLHSTMT st=SQL_NULL_HSTMT;if(SQLAllocHandle(SQL_HANDLE_STMT,c->db,&st)!=SQL_SUCCESS)goto done;const char *q=NULL;
if(operation==1)q="INSERT INTO dbo.t_runtime_state(state_id,owner_id,login_session_id,state_kind,encrypted_payload,expires_at,revision,consumed) VALUES (?,?,?,?,?,DATEADD(minute,?,SWITCHOFFSET(SYSDATETIMEOFFSET(),'+00:00')),1,0)";
if(operation==2)q="SELECT encrypted_payload,revision FROM dbo.t_runtime_state WHERE state_id=? AND owner_id=? AND login_session_id=? AND state_kind=? AND expires_at>SYSDATETIMEOFFSET() AND consumed=0";
if(operation==3)q="UPDATE dbo.t_runtime_state SET encrypted_payload=?,expires_at=DATEADD(minute,?,SWITCHOFFSET(SYSDATETIMEOFFSET(),'+00:00')),revision=revision+1 WHERE state_id=? AND owner_id=? AND login_session_id=? AND state_kind=? AND revision=? AND expires_at>SYSDATETIMEOFFSET() AND consumed=0 AND revision<9223372036854775807";
if(operation==4)q="UPDATE dbo.t_runtime_state SET consumed=1 WHERE state_id=? AND owner_id=? AND login_session_id=? AND state_kind=? AND revision=? AND expires_at>SYSDATETIMEOFFSET() AND consumed=0";
if(operation==5)q="SELECT encrypted_payload,revision FROM dbo.t_runtime_state WITH (UPDLOCK) WHERE state_id=? AND owner_id=? AND login_session_id=? AND state_kind=? AND expires_at>SYSDATETIMEOFFSET() AND consumed=0";
if(!q)goto done;SQLWCHAR w[2048],ow[256];int l,ol;if(utf16(q,(int)strlen(q),(UChar*)w,2048,&l)||utf16(own,owner->length,(UChar*)ow,256,&ol)||!SQL_SUCCEEDED(SQLPrepareW(st,w,l)))goto done;SQLLEN inds[8];int p=1;
#define BIND(ct,dt,size,data,len,ind) do{inds[p-1]=(ind);if(!SQL_SUCCEEDED(SQLBindParameter(st,(SQLUSMALLINT)p,SQL_PARAM_INPUT,(ct),(dt),(size),0,(data),(len),&inds[p-1])))goto done;p++;}while(0)
if(operation==3){if(crypt(1,payload,capacity,buf,&bytes,aad))goto done;BIND(SQL_C_BINARY,SQL_LONGVARBINARY,bytes,buf,bytes,bytes);BIND(SQL_C_SLONG,SQL_INTEGER,10,&minutes,sizeof minutes,sizeof minutes);}
BIND(SQL_C_CHAR,SQL_VARCHAR,64,sid,64,64);BIND(SQL_C_WCHAR,SQL_WVARCHAR,128,ow,ol*2,ol*2);BIND(SQL_C_CHAR,SQL_VARCHAR,64,ses,session->length,session->length);BIND(SQL_C_CHAR,SQL_VARCHAR,16,knd,strlen(knd),strlen(knd));
if(operation==1){if(crypt(1,payload,capacity,buf,&bytes,aad))goto done;BIND(SQL_C_BINARY,SQL_LONGVARBINARY,bytes,buf,bytes,bytes);BIND(SQL_C_SLONG,SQL_INTEGER,10,&minutes,sizeof minutes,sizeof minutes);}
if(operation==3||operation==4)BIND(SQL_C_SBIGINT,SQL_BIGINT,19,revision,8,8);
if(!SQL_SUCCEEDED(SQLExecute(st)))goto done;if(operation==2||operation==5){SQLLEN n=0,revind=0;if(SQLFetch(st)!=SQL_SUCCESS||SQLGetData(st,1,SQL_C_BINARY,buf,capacity+28,&n)!=SQL_SUCCESS||n<28||n>capacity+28||SQLGetData(st,2,SQL_C_SBIGINT,revision,8,&revind)!=SQL_SUCCESS)goto done;int written;if(crypt(0,buf,(int)n,payload,&written,aad))goto done;if(written!=capacity){if(strcmp(knd,"Search"))goto done;memset(payload,0,(size_t)capacity);}result=0;}else{SQLLEN affected=0;if(SQLRowCount(st,&affected)!=SQL_SUCCESS||affected!=1)goto done;if(operation==3)(*revision)++;result=0;}
done:if(st)SQLFreeHandle(SQL_HANDLE_STMT,st);OPENSSL_cleanse(buf,(size_t)capacity+28);free(buf);return result;
#undef BIND
}
int32_t STESC(const char *s,int32_t n){for(int i=0;i<n;i++){switch(s[i]){case '&':fputs("&amp;",stdout);break;case '<':fputs("&lt;",stdout);break;case '>':fputs("&gt;",stdout);break;case '"':fputs("&quot;",stdout);break;case '\'':fputs("&#39;",stdout);break;default:fputc((unsigned char)s[i],stdout);}}return 0;}
int32_t STEDITORREDIRECT(const char *context,const char *tab,const char *action,int64_t revision,int64_t student){
 const char *operation=!memcmp(action,"EDIT",4)?"EDIT":"NEW";
 printf("Status: 303\r\nCache-Control: no-store\r\nLocation: student.cgi?action=%s&contextId=%.*s&tabId=%.*s&contextRevision=%" PRId64,operation,64,context,64,tab,revision);
 if(student>0)printf("&studentId=%" PRId64,student);
 printf("\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n");return 0;
}
int32_t STHEADER(int32_t status){printf("Status: %d\r\nContent-Type: text/html; charset=UTF-8\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nReferrer-Policy: no-referrer\r\nContent-Security-Policy: default-src 'none'; style-src 'self'; script-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'\r\n\r\n",status);return 0;}
/* Rendering performs lookup I/O. Defer headers until that work has finished. */
static FILE *render_output;
static int render_saved_fd=-1;
static char render_path[2048];
int32_t STOUTPUTBEGIN(void){
 if(render_output)return -1;
 const char *dir=getenv("STUDENT_RENDER_DIR");if(!dir||!*dir)dir=".tmp";
 unsigned char random[16];if(RAND_bytes(random,16)!=1)return -1;
 char hex[33];for(int i=0;i<16;i++)snprintf(hex+i*2,3,"%02x",random[i]);
 int n=snprintf(render_path,sizeof render_path,"%s/render-%s.tmp",dir,hex);
 if(n<0||n>=(int)sizeof render_path)return -1;
 render_output=fopen(render_path,"w+b");if(!render_output)return -1;
 fflush(stdout);render_saved_fd=ST_DUP(ST_FILENO(stdout));
 if(render_saved_fd<0||ST_DUP2(ST_FILENO(render_output),ST_FILENO(stdout))<0){
  if(render_saved_fd>=0)ST_CLOSE(render_saved_fd);
  fclose(render_output);remove(render_path);render_output=NULL;render_saved_fd=-1;return -1;
 }
 return 0;
}
int32_t STOUTPUTEND(int32_t status){
 if(!render_output||render_saved_fd<0)return -1;
 fflush(stdout);ST_DUP2(render_saved_fd,ST_FILENO(stdout));ST_CLOSE(render_saved_fd);
 render_saved_fd=-1;clearerr(stdout);rewind(render_output);STHEADER(status);
 char block[8192];size_t n;while((n=fread(block,1,sizeof block,render_output))>0)fwrite(block,1,n,stdout);
 fclose(render_output);remove(render_path);render_output=NULL;return 0;
}
int32_t STREDIRECT(const char *context,const char *tab,const char *flash,int64_t revision){fputs("Status: 303 See Other\r\nCache-Control: no-store\r\nLocation: student.cgi?action=RESUME&contextId=",stdout);for(int i=0;i<64;i++)if(hexdigit(context[i])>=0)fputc(context[i],stdout);fputs("&tabId=",stdout);for(int i=0;i<64;i++)if(hexdigit(tab[i])>=0)fputc(tab[i],stdout);fputs("&flashId=",stdout);for(int i=0;i<64;i++)if(hexdigit(flash[i])>=0)fputc(flash[i],stdout);printf("&contextRevision=%" PRId64 "\r\n\r\n",revision);return 0;}
