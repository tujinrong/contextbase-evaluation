/* Only the terminal transport is simulated. COBOL rendering/events/request checks
 * and the sample/UTF8 boundary are the production programs. No SQL is simulated. */
#include "windows_terminal.h"
#include <string.h>
typedef struct {int32_t id,row,col,width,flags,changed;ST_VALUE value;} TestField;
static TestField fields[128];
static int count,key,focus,full_result;
static ST_VALUE full_value;
static TestField *find(int id){for(int i=0;i<count;i++)if(fields[i].id==id)return fields+i;return 0;}
int32_t STTERMOPEN(const int32_t *cols,const int32_t *rows){return *cols==132&&*rows==27?0:-1;}
int32_t STTERMCLOSE(void){return 0;}
int32_t STTERMBEGIN(const ST_VALUE *panel,const ST_VALUE *title){(void)panel;(void)title;count=0;return 0;}
int32_t STTERMADD(const int32_t *id,const int32_t *row,const int32_t *col,const int32_t *width,const int32_t *height,const int32_t *flags,const int32_t *max,const ST_VALUE *value){
 (void)max;if(count==128||find(*id)||*row<1||*col<1||*width<1||*height<1||*row+*height-1>27||*col+*width-1>132)return -7;
 fields[count++]=(TestField){*id,*row,*col,*width,*flags,0,*value};return 0;
}
int32_t STTERMNEXT(int32_t *out,int32_t *current){*out=key;*current=focus;return 0;}
int32_t STTERMGET(const int32_t *id,ST_VALUE *value,int32_t *changed){TestField *f=find(*id);if(!f)return -7;*value=f->value;*changed=f->changed;f->changed=0;return 0;}
int32_t STTERMFULL(ST_VALUE *value,const ST_VALUE *title,const int32_t *flags,const int32_t *max){(void)title;(void)max;if(full_result==1&&(*flags&1))*value=full_value;return full_result;}
int32_t STTESTKEY(const int32_t *new_key,const int32_t *new_focus){key=*new_key;focus=*new_focus;return 0;}
int32_t STTESTSET(const int32_t *id,const ST_VALUE *value){TestField *f=find(*id);if(!f)return -7;f->value=*value;f->changed=1;return 0;}
int32_t STTESTFIELD(const int32_t *id,ST_VALUE *value,int32_t *row,int32_t *col,int32_t *flags){TestField *f=find(*id);if(!f)return -7;*value=f->value;*row=f->row;*col=f->col;*flags=f->flags;return 0;}
int32_t STTESTFULL(const int32_t *result,const ST_VALUE *value){full_result=*result;full_value=*value;return 0;}
