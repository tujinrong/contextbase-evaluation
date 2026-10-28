#include "student_abi.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
extern int32_t STHTTP(ST_VALUE*);
extern int32_t STINTEGER(const ST_VALUE*,int64_t*);
extern int32_t STUNICODE(int32_t,const ST_VALUE*,ST_VALUE*,int32_t,int32_t);
extern int32_t STPATTERN(ST_VALUE*,int32_t);
extern int32_t STHEX(const ST_VALUE*);
extern int32_t STEDITORREDIRECT(const char*,const char*,const char*,int64_t,int64_t);
static ST_VALUE input(const char *s){ST_VALUE v={0};v.length=(int32_t)strlen(s);if(v.length>1024)exit(2);memcpy(v.data,s,(size_t)v.length);return v;}
int main(int argc,char **argv){
 if(argc<2)return 2;
 if(!strcmp(argv[1],"http")){ST_VALUE fields[64];int rc=STHTTP(fields);printf("%d\n",rc);return 0;}
 if(!strcmp(argv[1],"redirect")){char a[64],b[64];memset(a,'a',64);memset(b,'b',64);return STEDITORREDIRECT(a,b,"EDIT",6,123);}
 if(argc<3)return 2;
 ST_VALUE v;
 if(!strcmp(argv[2],"@stdin")){memset(&v,0,sizeof v);size_t n=fread(v.data,1,sizeof v.data,stdin);if(n==sizeof v.data&&fgetc(stdin)!=EOF)return 2;v.length=(int32_t)n;}
 else v=input(argv[2]);
 if(!strcmp(argv[1],"integer")){int64_t n=0;int rc=STINTEGER(&v,&n);printf("%d|%" PRId64 "\n",rc,n);}
 else if(!strcmp(argv[1],"unicode")){if(argc!=6)return 2;ST_VALUE out={0};int rc=STUNICODE(atoi(argv[3]),&v,&out,atoi(argv[4]),atoi(argv[5]));printf("%d|",rc);if(!rc&&out.null_flag==0)fwrite(out.data,1,(size_t)out.length,stdout);puts("");}
 else if(!strcmp(argv[1],"pattern")){int rc=STPATTERN(&v,argc>3?atoi(argv[3]):0);printf("%d|",rc);if(!rc)fwrite(v.data,1,(size_t)v.length,stdout);puts("");}
 else if(!strcmp(argv[1],"hex")){printf("%d\n",STHEX(&v));}
 else return 2;
 return 0;
}
