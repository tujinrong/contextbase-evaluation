#include "student_abi.h"
#include <string.h>
#include <stdio.h>
#include <inttypes.h>
#include <stdlib.h>
/* Server state fixture only. Production SQL, encryption and expiry are not simulated as PASS. */
static int mode,search_writes,editor_writes,editor_minutes;
static int64_t search_revision=5,editor_revision=7;
static void *saved_search,*saved_editor;static int search_capacity,editor_capacity;
int32_t STFIXMODE(int32_t m){free(saved_search);free(saved_editor);saved_search=saved_editor=NULL;search_capacity=editor_capacity=0;mode=m;search_writes=editor_writes=editor_minutes=0;search_revision=5;editor_revision=7;return 0;}
static void val(ST_VALUE *v,const char *s){memset(v,0,sizeof *v);memset(v->data,' ',sizeof v->data);v->length=(int32_t)strlen(s);memcpy(v->data,s,(size_t)v->length);}
int32_t STSTATEIO(void *db,int32_t op,char *id,const char *kind,const ST_VALUE *owner,const ST_VALUE *session,const char *tab,void *payload,int32_t capacity,int64_t *revision,int32_t minutes){
 (void)db;(void)id;(void)owner;(void)session;
 int search=!memcmp(kind,"Search",6);int64_t *current=search?&search_revision:&editor_revision;
 if(op==2){
  if(mode==3&&!search)return -1;
  void *saved=search?saved_search:saved_editor;int stored=search?search_capacity:editor_capacity;
  if(saved&&stored==capacity){memcpy(payload,saved,(size_t)capacity);*revision=*current;return 0;}
  memset(payload,0,(size_t)capacity);*revision=*current;
  if(search){memcpy(payload,"search-compact-1",16);memcpy((char*)payload+20,tab,64);
   if(mode!=4&&mode!=6&&mode!=17&&mode!=16){const char *kind=(mode>=12&&mode<=15)||mode>=18?"DUPLICATE":mode==5?"RESET":"DELETE";memset((char*)payload+capacity-80,'a',64);memset((char*)payload+capacity-16,' ',16);memcpy((char*)payload+capacity-16,kind,strlen(kind));}
  }
  else{
   char *p=payload;memset(p,' ',16);if(mode!=4&&mode!=6){const char *pending=(mode>=12&&mode<=15)||mode>=18?"DUPLICATE":mode==5?"RESET":"DELETE";memcpy(p,pending,strlen(pending));}
   ST_VALUE draft[64];memset(draft,0,sizeof draft);for(int i=0;i<64;i++)draft[i].null_flag=-1;
   val(draft+4,"draft-value");val(draft+29,"5");val(draft+0,"RESET");
   char token[65];memset(token,'a',64);token[64]=0;val(draft+28,token);val(draft+30,token);val(draft+32,token);
   val(draft+1,"1");val(draft+2,"1");memset(token,'b',64);val(draft+31,token);
   memcpy(p+16,draft,sizeof draft);memcpy(p+66144,draft,sizeof draft);int64_t target=1;memcpy(p+66064,&target,8);memcpy(p+66072,&target,8);memcpy(p+66080,tab,64);
  }
  return 0;
 }
 if(op==3){
  if(*revision!=*current)return -1;
  void **saved=search?&saved_search:&saved_editor;int *stored=search?&search_capacity:&editor_capacity;
  void *next=realloc(*saved,(size_t)capacity);if(!next)return -1;*saved=next;*stored=capacity;memcpy(next,payload,(size_t)capacity);
  (*current)++;*revision=*current;
  if(search)search_writes++;else{editor_writes++;editor_minutes=minutes;}
  return 0;
 }
 return -1;
}
int32_t STFIXREPORT(void){printf("FIX|%" PRId64 "|%d|%d|%d\n",search_revision,search_writes,editor_writes,editor_minutes);return 0;}
