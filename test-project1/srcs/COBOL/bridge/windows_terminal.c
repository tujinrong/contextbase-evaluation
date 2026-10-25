#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "windows_terminal.h"

_Static_assert(sizeof(STTERM_VALUE)==1032 && offsetof(STTERM_VALUE,data)==8,"terminal value ABI");
_Static_assert(sizeof(wchar_t)==2 && sizeof(KEY_EVENT_RECORD)==16,"Windows Unicode ABI");
extern int32_t STSAMPLECHECK(void);
extern int32_t STSAMPLETOUCH(void);
#define FIELD_LIMIT 128
#define CELL_LIMIT (132*27)
#define EDIT_LIMIT 8192
typedef struct {
 int32_t id,row,col,width,height,flags,maximum;
 STTERM_VALUE original,value;
 size_t cursor,left;
} Field;
typedef struct { uint32_t cp; int32_t key; unsigned repeat; } Event;
static struct {
 HANDLE input,output,original_output;
 DWORD input_mode;
 int open,begun,count,focus,columns,rows;
 Field fields[FIELD_LIMIT];
 Field previous[FIELD_LIMIT];
 int previous_count;
 CHAR_INFO cells[CELL_LIMIT];
 unsigned char down[256],blocked[256];
 WCHAR high;
 STTERM_VALUE panel,title;
 const wchar_t *notice;
} terminal;
#ifdef STTERM_TEST
/* Unit harness queues INPUT_RECORDs here; actual product decoder still reads
 * them using ReadConsoleInputW. This hook is absent from the product build. */
static void (*terminal_test_wait_hook)(int full);
#endif

/* Strict scalar codec, independent of ANSI code pages. Never replacement-decode. */
static int decode(const STTERM_VALUE *v,uint32_t *out,size_t capacity,size_t *count){
 size_t n=0;int32_t i=0;
 if(!v||v->length<0||v->length>1024||(v->null_flag!=0&&v->null_flag!=-1)||
    (v->null_flag==-1&&v->length!=0))return STTERM_E_ARGUMENT;
 while(i<v->length){
  const unsigned char *s=(const unsigned char *)v->data;
  unsigned c=s[i++],need=0;uint32_t cp;unsigned minimum;
  if(c<0x80){cp=c;minimum=0;}
  else if(c>=0xc2&&c<=0xdf){cp=c&31;need=1;minimum=0x80;}
  else if(c>=0xe0&&c<=0xef){cp=c&15;need=2;minimum=0x800;}
  else if(c>=0xf0&&c<=0xf4){cp=c&7;need=3;minimum=0x10000;}
  else return STTERM_E_ENCODING;
  if((uint32_t)(v->length-i)<need)return STTERM_E_ENCODING;
  for(unsigned j=0;j<need;j++){c=s[i++];if((c&0xc0)!=0x80)return STTERM_E_ENCODING;cp=(cp<<6)|(c&63);}
  if(cp<minimum||cp==0||cp>0x10ffff||(cp>=0xd800&&cp<=0xdfff))return STTERM_E_ENCODING;
  if(n>=capacity)return STTERM_E_CAPACITY;
  if(out)out[n]=cp;n++;
 }
 *count=n;return 0;
}
static int encode(const uint32_t *cp,size_t count,STTERM_VALUE *v){
 STTERM_VALUE result;size_t at=0;memset(&result,0,sizeof result);
 for(size_t i=0;i<count;i++){
  uint32_t c=cp[i];unsigned char b[4];size_t n;
  if(c==0||c>0x10ffff||(c>=0xd800&&c<=0xdfff))return STTERM_E_ENCODING;
  if(c<0x80){b[0]=(unsigned char)c;n=1;}
  else if(c<0x800){b[0]=(unsigned char)(0xc0|(c>>6));b[1]=(unsigned char)(0x80|(c&63));n=2;}
  else if(c<0x10000){b[0]=(unsigned char)(0xe0|(c>>12));b[1]=(unsigned char)(0x80|((c>>6)&63));b[2]=(unsigned char)(0x80|(c&63));n=3;}
  else{b[0]=(unsigned char)(0xf0|(c>>18));b[1]=(unsigned char)(0x80|((c>>12)&63));b[2]=(unsigned char)(0x80|((c>>6)&63));b[3]=(unsigned char)(0x80|(c&63));n=4;}
  if(at+n>sizeof result.data)return STTERM_E_CAPACITY;
  memcpy(result.data+at,b,n);at+=n;
 }
 result.length=(int32_t)at;*v=result;return 0;
}
static int equal_value(const STTERM_VALUE *a,const STTERM_VALUE *b){
 return a->length==b->length&&a->null_flag==b->null_flag&&
        (!a->length||memcmp(a->data,b->data,(size_t)a->length)==0);
}
static int flags_ok(int32_t f){return f>=0&&(f&~15)==0&&!(f&STTERM_HEADER&&f&STTERM_EDIT);}
static int editable(int flags){return (flags&STTERM_EDIT)&&!(flags&STTERM_HEADER);}
static int focusable(const Field *f){return !(f->flags&STTERM_HEADER)&&(f->flags&(STTERM_EDIT|STTERM_READONLY_FOCUS));}
static int find_field(int32_t id){for(int i=0;i<terminal.count;i++)if(terminal.fields[i].id==id)return i;return -1;}
static int select_focus(int32_t id){
 int i=find_field(id);if(i>=0&&focusable(terminal.fields+i))return i;
 for(i=0;i<terminal.count;i++)if(focusable(terminal.fields+i))return i;return -1;
}
static void move_focus(int direction){
 if(!terminal.count){terminal.focus=-1;return;}
 int i=terminal.focus;
 for(int n=0;n<terminal.count;n++){i=(i+direction+terminal.count)%terminal.count;if(focusable(terminal.fields+i)){terminal.focus=i;return;}}
 terminal.focus=-1;
}
static int dimensions(void){
 CONSOLE_SCREEN_BUFFER_INFO info;
 if(!GetConsoleScreenBufferInfo(terminal.output,&info)||info.dwSize.X<terminal.columns||info.dwSize.Y<terminal.rows||
    info.srWindow.Right-info.srWindow.Left+1<terminal.columns||info.srWindow.Bottom-info.srWindow.Top+1<terminal.rows)return STTERM_E_CONSOLE;
 return 0;
}
static int check_session(void){return STSAMPLECHECK()==0?0:STTERM_E_SESSION;}
/* Remove queued actions from the old panel while preserving observed releases.
 * Held initiating keys stay blocked until key-up; no timer or drain touches TTL. */
static int transition(void){
 DWORD n,got;INPUT_RECORD input[64];
 while(GetNumberOfConsoleInputEvents(terminal.input,&n)&&n){
  if(!ReadConsoleInputW(terminal.input,input,n>64?64:n,&got))return STTERM_E_CONSOLE;
  for(DWORD i=0;i<got;i++)if(input[i].EventType==KEY_EVENT){
   KEY_EVENT_RECORD *k=&input[i].Event.KeyEvent;
   if(k->wVirtualKeyCode>0&&k->wVirtualKeyCode<256)terminal.down[k->wVirtualKeyCode]=(unsigned char)!!k->bKeyDown;
  }
 }
 memcpy(terminal.blocked,terminal.down,sizeof terminal.blocked);terminal.high=0;return 0;
}
static int next_event(Event *event,int full){
 for(;;){
  int rc=check_session();if(rc)return rc;
  rc=dimensions();if(rc)return rc;
#ifdef STTERM_TEST
  if(terminal_test_wait_hook)terminal_test_wait_hook(full);
#else
  (void)full;
#endif
  DWORD wait=WaitForSingleObject(terminal.input,1000);
  if(wait==WAIT_TIMEOUT)continue;
  if(wait!=WAIT_OBJECT_0)return STTERM_E_CONSOLE;
  INPUT_RECORD input;DWORD n;
  if(!ReadConsoleInputW(terminal.input,&input,1,&n)||n!=1)return STTERM_E_CONSOLE;
  if(input.EventType!=KEY_EVENT)continue;
  KEY_EVENT_RECORD *k=&input.Event.KeyEvent;unsigned vk=k->wVirtualKeyCode;
  if(vk>=256)return STTERM_E_ARGUMENT;
  int was_down=vk?terminal.down[vk]:0;
  if(vk)terminal.down[vk]=(unsigned char)!!k->bKeyDown;
  if(!k->bKeyDown){if(vk)terminal.blocked[vk]=0;continue;}
  if(vk&&terminal.blocked[vk])continue;
  if(k->wRepeatCount==0)return STTERM_E_ARGUMENT;
  rc=check_session();if(rc)return rc;
  if(STSAMPLETOUCH()!=0)return STTERM_E_SESSION;
  int mods=0;
  if(k->dwControlKeyState&SHIFT_PRESSED)mods|=STTERM_SHIFT;
  if(k->dwControlKeyState&(LEFT_CTRL_PRESSED|RIGHT_CTRL_PRESSED))mods|=STTERM_CTRL;
  if(k->dwControlKeyState&(LEFT_ALT_PRESSED|RIGHT_ALT_PRESSED))mods|=STTERM_ALT;
  WCHAR c=k->uChar.UnicodeChar;
  event->cp=0;event->key=(int32_t)vk|mods;event->repeat=k->wRepeatCount;
  if(c>=0xd800&&c<=0xdbff){if(terminal.high)return STTERM_E_ENCODING;terminal.high=c;continue;}
  if(c>=0xdc00&&c<=0xdfff){
   if(!terminal.high)return STTERM_E_ENCODING;
   event->cp=0x10000+(((uint32_t)terminal.high-0xd800)<<10)+(c-0xdc00);terminal.high=0;return 0;
  }
  if(terminal.high){terminal.high=0;return STTERM_E_ENCODING;}
  if(c>=32&&!(mods&(STTERM_CTRL|STTERM_ALT))){event->cp=c;return 0;}
  /* Function/navigation/commit keys cannot be repeated into another action. */
  if(was_down)continue;
  if(vk==VK_SHIFT||vk==VK_CONTROL||vk==VK_MENU)continue;
  return 0;
 }
}
/* Projection only: original UTF8 remains separate. Controls are visible symbols,
 * never VT sequences. Supplementary scalars occupy two UTF16 cells. */
static int cell_width(uint32_t cp){
 if(cp>0xffff)return 2;
 WORD type=0;WCHAR c=(WCHAR)cp;
 if(GetStringTypeW(CT_CTYPE3,&c,1,&type)&&(type&(C3_FULLWIDTH|C3_IDEOGRAPH)))return 2;
 return 1;
}
static void clear_cells(void){
 for(int i=0;i<terminal.columns*terminal.rows;i++){terminal.cells[i].Char.UnicodeChar=L' ';terminal.cells[i].Attributes=7;}
}
static void put_cell(int row,int col,WCHAR ch,WORD attr){
 if(row>=0&&row<terminal.rows&&col>=0&&col<terminal.columns){CHAR_INFO *cell=terminal.cells+row*terminal.columns+col;cell->Char.UnicodeChar=ch;cell->Attributes=attr;}
}
static void draw_scalar(int row,int col,uint32_t cp,WORD attr){
 if(cp<32)cp=0x2400+cp;else if(cp==127)cp=0x2421;
 if(cp>0xffff){cp-=0x10000;put_cell(row,col,(WCHAR)(0xd800+(cp>>10)),attr);put_cell(row,col+1,(WCHAR)(0xdc00+(cp&1023)),attr);}
 else{put_cell(row,col,(WCHAR)cp,attr);if(cell_width(cp)==2)put_cell(row,col+1,L' ',attr);}
}
static void draw_wide(int row,int col,const wchar_t *s,WORD attr){
 for(;*s&&col<terminal.columns;s++,col++)put_cell(row,col,*s,attr);
}
static void draw_value(int row,int col,int width,int height,const STTERM_VALUE *v,WORD attr){
 uint32_t text[1024];size_t count;if(decode(v,text,1024,&count))return;
 int x=0,y=0;
 for(size_t i=0;i<count&&y<height;i++){
  if(text[i]==10){x=0;y++;continue;}
  int w=cell_width(text[i]);if(x+w>width){x=0;y++;}if(y>=height)break;
  draw_scalar(row+y,col+x,text[i],attr);x+=w;
 }
}
static int flush_cells(int cursor_row,int cursor_col,int show){
 SMALL_RECT rect={0,0,(SHORT)(terminal.columns-1),(SHORT)(terminal.rows-1)};
 COORD size={(SHORT)terminal.columns,(SHORT)terminal.rows},zero={0,0};
 if(!WriteConsoleOutputW(terminal.output,terminal.cells,size,zero,&rect))return STTERM_E_CONSOLE;
 CONSOLE_CURSOR_INFO ci={20,(BOOL)show};
 if(!SetConsoleCursorInfo(terminal.output,&ci))return STTERM_E_CONSOLE;
 if(show){COORD pos={(SHORT)cursor_col,(SHORT)cursor_row};if(!SetConsoleCursorPosition(terminal.output,pos))return STTERM_E_CONSOLE;}
 return 0;
}
static int render_frame(void){
 clear_cells();draw_value(0,0,terminal.columns,1,&terminal.title,0x70);
 int cursor_row=0,cursor_col=0,show=0;
 for(int i=0;i<terminal.count;i++){
  Field *f=terminal.fields+i;WORD attr=f->flags&STTERM_ERROR?0x0c:(f->flags&STTERM_HEADER?0x70:7);
  if(i==terminal.focus)attr=f->flags&STTERM_ERROR?0x4f:0x1f;
  for(int r=0;r<f->height;r++)for(int c=0;c<f->width;c++)put_cell(f->row-1+r,f->col-1+c,L' ',attr);
  uint32_t text[1024];size_t count;if(decode(&f->value,text,1024,&count))return STTERM_E_ENCODING;
  if(f->cursor>count)f->cursor=count;
  if(f->left>f->cursor)f->left=f->cursor;
  size_t visible=0;for(size_t j=f->left;j<f->cursor;j++)visible+=(size_t)cell_width(text[j]);
  while(visible>=(size_t)(f->width*f->height)&&f->left<f->cursor){visible-=(size_t)cell_width(text[f->left]);f->left++;}
  int x=0,y=0;
  for(size_t j=f->left;j<=count&&y<f->height;j++){
   if(j==f->cursor&&i==terminal.focus){cursor_row=f->row-1+y;cursor_col=f->col-1+x;show=1;}
   if(j==count)break;
   if(text[j]==10){x=0;y++;continue;}
   int w=cell_width(text[j]);if(x+w>f->width){x=0;y++;}if(y>=f->height)break;
   draw_scalar(f->row-1+y,f->col-1+x,text[j],attr);x+=w;
   if(x>=f->width){x=0;y++;}
  }
 }
 if(terminal.notice)draw_wide(terminal.rows-1,0,terminal.notice,0x4f);
 return flush_cells(cursor_row,cursor_col,show);
}
static int edit_field(Field *f,const Event *event){
 uint32_t cp[1025];size_t n;int rc=decode(&f->value,cp,1024,&n);if(rc)return rc;
 if(f->cursor>n)f->cursor=n;
 unsigned key=(unsigned)event->key&0xffff;
 if(key==VK_LEFT){f->cursor=f->cursor>event->repeat?f->cursor-event->repeat:0;return 0;}
 if(key==VK_RIGHT){f->cursor=f->cursor+event->repeat<n?f->cursor+event->repeat:n;return 0;}
 if(key==VK_HOME){f->cursor=0;return 0;}
 if(key==VK_END){f->cursor=n;return 0;}
 if(!editable(f->flags))return 0;
 if(event->cp){
  if(event->repeat>1024-n)return STTERM_E_CAPACITY;
  memmove(cp+f->cursor+event->repeat,cp+f->cursor,(n-f->cursor)*sizeof *cp);
  for(unsigned j=0;j<event->repeat;j++)cp[f->cursor+j]=event->cp;n+=event->repeat;
 }else if(key==VK_BACK&&f->cursor){memmove(cp+f->cursor-1,cp+f->cursor,(n-f->cursor)*sizeof *cp);n--;}
 else if(key==VK_DELETE&&f->cursor<n){memmove(cp+f->cursor,cp+f->cursor+1,(n-f->cursor-1)*sizeof *cp);n--;}
 else return 0;
 STTERM_VALUE value;rc=encode(cp,n,&value);if(rc)return rc;
 f->value=value;if(event->cp)f->cursor+=event->repeat;else if(key==VK_BACK)f->cursor--;
 return 0;
}

int32_t STTERMOPEN(const int32_t *columns,const int32_t *rows){
 if(!columns||!rows||*columns!=132||*rows!=27)return STTERM_E_ARGUMENT;
 if(terminal.open)return STTERM_E_STATE;
 if(check_session())return STTERM_E_SESSION;
 memset(&terminal,0,sizeof terminal);terminal.focus=-1;
 terminal.input=CreateFileW(L"CONIN$",GENERIC_READ|GENERIC_WRITE,FILE_SHARE_READ|FILE_SHARE_WRITE,NULL,OPEN_EXISTING,0,NULL);
 terminal.original_output=CreateFileW(L"CONOUT$",GENERIC_READ|GENERIC_WRITE,FILE_SHARE_READ|FILE_SHARE_WRITE,NULL,OPEN_EXISTING,0,NULL);
 terminal.output=CreateConsoleScreenBuffer(GENERIC_READ|GENERIC_WRITE,FILE_SHARE_READ|FILE_SHARE_WRITE,NULL,CONSOLE_TEXTMODE_BUFFER,NULL);
 if(terminal.input==INVALID_HANDLE_VALUE||terminal.original_output==INVALID_HANDLE_VALUE||terminal.output==INVALID_HANDLE_VALUE)goto failure;
 if(!GetConsoleMode(terminal.input,&terminal.input_mode))goto failure;
 terminal.open=1;terminal.columns=*columns;terminal.rows=*rows;
 SMALL_RECT small={0,0,0,0},window={0,0,131,26};COORD size={132,27};
 if(!SetConsoleWindowInfo(terminal.output,TRUE,&small)||!SetConsoleScreenBufferSize(terminal.output,size)||
    !SetConsoleWindowInfo(terminal.output,TRUE,&window)||!SetConsoleActiveScreenBuffer(terminal.output)||
    !SetConsoleMode(terminal.input,ENABLE_WINDOW_INPUT|ENABLE_EXTENDED_FLAGS)||dimensions())goto failure;
 return 0;
failure:
 STTERMCLOSE();return STTERM_E_CONSOLE;
}
int32_t STTERMCLOSE(void){
 int failed=0;
 if(terminal.open){if(!SetConsoleMode(terminal.input,terminal.input_mode))failed=1;if(!SetConsoleActiveScreenBuffer(terminal.original_output))failed=1;}
 HANDLE handles[]={terminal.output,terminal.original_output,terminal.input};
 for(size_t i=0;i<3;i++)if(handles[i]&&handles[i]!=INVALID_HANDLE_VALUE)if(!CloseHandle(handles[i]))failed=1;
 memset(&terminal,0,sizeof terminal);terminal.focus=-1;return failed?STTERM_E_CONSOLE:0;
}
int32_t STTERMBEGIN(const STTERM_VALUE *panel,const STTERM_VALUE *title){
 size_t n;int rc;
 if(!terminal.open)return STTERM_E_STATE;
 if((rc=decode(panel,NULL,1024,&n))||(rc=decode(title,NULL,1024,&n)))return rc;
 if((rc=check_session()))return rc;
 int same=terminal.begun&&equal_value(panel,&terminal.panel);
 if(!same&&(rc=transition()))return rc;
 terminal.previous_count=same?terminal.count:0;
 if(same)memcpy(terminal.previous,terminal.fields,(size_t)terminal.count*sizeof *terminal.fields);
 terminal.count=0;terminal.focus=-1;terminal.panel=*panel;terminal.title=*title;terminal.begun=1;terminal.notice=NULL;return 0;
}
int32_t STTERMADD(const int32_t *id,const int32_t *row,const int32_t *col,const int32_t *width,const int32_t *height,
 const int32_t *flags,const int32_t *maximum,const STTERM_VALUE *value){
 size_t n;int rc;
 if(!terminal.open||!terminal.begun)return STTERM_E_STATE;
 if(!id||!row||!col||!width||!height||!flags||!maximum||!value)return STTERM_E_ARGUMENT;
 if(*id<=0||*row<1||*col<1||*width<1||*height<1||*row>terminal.rows||*col>terminal.columns||
    *width>terminal.columns-*col+1||*height>terminal.rows-*row+1||!flags_ok(*flags)||*maximum<0)return STTERM_E_ARGUMENT;
 if(find_field(*id)>=0)return STTERM_E_FIELD;
 if(terminal.count>=FIELD_LIMIT)return STTERM_E_CAPACITY;
 if((rc=decode(value,NULL,1024,&n)))return rc;
 Field *f=terminal.fields+terminal.count++;memset(f,0,sizeof *f);
 f->id=*id;f->row=*row;f->col=*col;f->width=*width;f->height=*height;f->flags=*flags;f->maximum=*maximum;
 f->value=f->original=*value;f->cursor=n;
 for(int i=0;i<terminal.previous_count;i++){
  Field *old=terminal.previous+i;
  if(old->id==*id&&equal_value(value,&old->value)){f->cursor=old->cursor;f->left=old->left;break;}
 }
 return 0;
}
int32_t STTERMGET(const int32_t *id,STTERM_VALUE *value,int32_t *changed){
 if(!terminal.open||!terminal.begun)return STTERM_E_STATE;
 if(!id||!value||!changed)return STTERM_E_ARGUMENT;
 int i=find_field(*id);if(i<0)return STTERM_E_FIELD;
 Field *f=terminal.fields+i;*changed=!equal_value(&f->value,&f->original);
 *value=*changed?f->value:f->original;return 0;
}
int32_t STTERMNEXT(int32_t *key,int32_t *focus){
 if(!terminal.open||!terminal.begun)return STTERM_E_STATE;
 if(!key||!focus)return STTERM_E_ARGUMENT;
 terminal.focus=select_focus(*focus);
 for(;;){
  int rc=check_session();if(rc)return rc;
  if((rc=render_frame()))return rc;
  Event event;if((rc=next_event(&event,0)))return rc;
  unsigned vk=(unsigned)event.key&0xffff;
  if(vk==VK_TAB){move_focus(event.key&STTERM_SHIFT?-1:1);*key=event.key;*focus=terminal.focus<0?0:terminal.fields[terminal.focus].id;return 0;}
  if(terminal.focus>=0&&!(event.key&(STTERM_CTRL|STTERM_ALT))){
   rc=edit_field(terminal.fields+terminal.focus,&event);
   terminal.notice=rc==STTERM_E_CAPACITY?L"Input exceeds the 1024-byte capacity; the original value is retained.":NULL;
   if(rc&&rc!=STTERM_E_CAPACITY)return rc;
  }
  if(event.cp&&vk!=VK_SPACE)continue;
  if(!event.cp&&!(event.key&(STTERM_CTRL|STTERM_ALT))&&(vk==VK_LEFT||vk==VK_RIGHT||vk==VK_HOME||vk==VK_END||vk==VK_BACK||vk==VK_DELETE))continue;
  *key=event.key;*focus=terminal.focus<0?0:terminal.fields[terminal.focus].id;return 0;
 }
}

typedef struct {uint32_t text[EDIT_LIMIT];size_t count,cursor,first;int codepoints,dirty;const wchar_t *notice;} Full;
static int parse_points(const Full *view,uint32_t *raw,size_t *count){
 size_t i=0,n=0;
 while(i<view->count){
  while(i<view->count&&view->text[i]==' ')i++;if(i==view->count)break;
  if(i+2>=view->count||view->text[i]!='U'||view->text[i+1]!='+')return STTERM_E_ENCODING;i+=2;
  uint32_t cp=0;unsigned digits=0;
  while(i<view->count&&view->text[i]!=' '){
   uint32_t c=view->text[i++];unsigned d;
   if(c>='0'&&c<='9')d=c-'0';else if(c>='A'&&c<='F')d=c-'A'+10;else if(c>='a'&&c<='f')d=c-'a'+10;else return STTERM_E_ENCODING;
   if(++digits>6)return STTERM_E_ENCODING;cp=(cp<<4)|d;
  }
  if(digits<4||cp==0||cp>0x10ffff||(cp>=0xd800&&cp<=0xdfff))return STTERM_E_ENCODING;
  if(n>=1024)return STTERM_E_CAPACITY;raw[n++]=cp;
 }
 *count=n;return 0;
}
static int full_value(const Full *view,int maximum,STTERM_VALUE *value){
 uint32_t raw[1024];size_t n=view->count;int rc;
 if(view->codepoints){if((rc=parse_points(view,raw,&n)))return rc;}
 else{if(n>1024)return STTERM_E_CAPACITY;memcpy(raw,view->text,n*sizeof *raw);}
 if(maximum>0&&n>(size_t)maximum)return STTERM_E_CAPACITY;
 return encode(raw,n,value);
}
static int full_toggle(Full *view){
 if(view->codepoints){
  uint32_t raw[1024];size_t n;int rc=parse_points(view,raw,&n);if(rc)return rc;
  memcpy(view->text,raw,n*sizeof *raw);view->count=n;view->codepoints=0;
 }else{
  uint32_t text[EDIT_LIMIT];size_t n=0;
  for(size_t i=0;i<view->count;i++){
   char token[16];int len=snprintf(token,sizeof token,"%sU+%04X",i?" ":"",(unsigned)view->text[i]);
   if(len<0||n+(size_t)len>EDIT_LIMIT)return STTERM_E_CAPACITY;
   for(int j=0;j<len;j++)text[n++]=(unsigned char)token[j];
  }
  memcpy(view->text,text,n*sizeof *text);view->count=n;view->codepoints=1;
 }
 view->cursor=view->count;view->first=0;return 0;
}
static void full_edit(Full *view,const Event *event,int can_edit){
 unsigned key=(unsigned)event->key&0xffff;
 if(key==VK_LEFT){if(view->cursor)view->cursor--;return;}
 if(key==VK_RIGHT){if(view->cursor<view->count)view->cursor++;return;}
 if(key==VK_HOME){view->cursor=0;return;}
 if(key==VK_END){view->cursor=view->count;return;}
 if(key==VK_UP||key==VK_PRIOR){size_t step=key==VK_PRIOR?128*18:128;view->cursor=view->cursor>step?view->cursor-step:0;return;}
 if(key==VK_DOWN||key==VK_NEXT){size_t step=key==VK_NEXT?128*18:128;view->cursor=view->cursor+step<view->count?view->cursor+step:view->count;return;}
 if(!can_edit)return;
 if(event->cp){
  if(event->repeat>EDIT_LIMIT-view->count){view->notice=L"Editor capacity exceeded; draft retained.";return;}
  memmove(view->text+view->cursor+event->repeat,view->text+view->cursor,(view->count-view->cursor)*sizeof *view->text);
  for(unsigned j=0;j<event->repeat;j++)view->text[view->cursor+j]=event->cp;
  view->cursor+=event->repeat;view->count+=event->repeat;view->dirty=1;
 }else if(key==VK_BACK&&view->cursor){memmove(view->text+view->cursor-1,view->text+view->cursor,(view->count-view->cursor)*sizeof *view->text);view->cursor--;view->count--;view->dirty=1;}
 else if(key==VK_DELETE&&view->cursor<view->count){memmove(view->text+view->cursor,view->text+view->cursor+1,(view->count-view->cursor-1)*sizeof *view->text);view->count--;view->dirty=1;}
}
static int full_render(Full *view,const STTERM_VALUE *title,int can_edit){
 clear_cells();draw_value(0,0,132,1,title,0x70);
 draw_wide(1,0,view->codepoints?L"CODE POINTS: U+XXXX separated by spaces; LF = U+000A":L"TEXT: literal input; Enter validates only",7);
 draw_wide(25,0,can_edit?L"F2 mode   F5 Apply to original field   F12 Cancel   arrows/Home/End/PgUp/PgDn":L"READ ONLY   F2 mode   F12 Return",0x70);
 if(view->notice)draw_wide(26,0,view->notice,0x4f);
 /* Start at a scalar boundary. Scroll as a projection, never insert a raw LF. */
 if(view->first>view->cursor)view->first=view->cursor;
 for(;;){
  int x=0,y=0,cx=0,cy=0,found=0;
  for(int r=2;r<25;r++)for(int c=0;c<132;c++)put_cell(r,c,L' ',7);
  for(size_t i=view->first;i<=view->count;i++){
   if(i==view->cursor){cx=x;cy=y;found=1;}
   if(i==view->count||y>=23)break;
   uint32_t cp=view->text[i];
   if(cp==10){x=0;y++;continue;}
   int width=cell_width(cp);if(x+width>132){x=0;y++;}if(y>=23)break;
   draw_scalar(y+2,x,cp,7);x+=width;if(x>=132){x=0;y++;}
  }
  if(found&&cy<23)return flush_cells(cy+2,cx,1);
  if(view->first>=view->cursor)return flush_cells(2,0,1);
  view->first++; /* Finite: at most EDIT_LIMIT scalars. */
 }
}
int32_t STTERMFULL(STTERM_VALUE *raw,const STTERM_VALUE *title,const int32_t *flags,const int32_t *maximum){
 if(!terminal.open)return STTERM_E_STATE;
 if(!raw||!title||!flags||!maximum||!flags_ok(*flags)||*maximum<0)return STTERM_E_ARGUMENT;
 size_t n;int rc=decode(title,NULL,1024,&n);if(rc)return rc;
 Full *view=(Full *)calloc(1,sizeof *view);if(!view)return STTERM_E_CAPACITY;
 rc=decode(raw,view->text,EDIT_LIMIT,&view->count);if(rc){free(view);return rc;}
 view->cursor=view->count;
 if((rc=check_session())||(rc=transition())){free(view);return rc;}
 STTERM_VALUE original=*raw;
 for(;;){
  if((rc=check_session())||(rc=full_render(view,title,editable(*flags))))break;
  Event event;if((rc=next_event(&event,1)))break;
  unsigned key=(unsigned)event.key&0xffff;
  if(key==VK_F12||key==VK_ESCAPE){rc=0;break;}
  if(key==VK_F2){rc=full_toggle(view);view->notice=rc?L"Invalid code-point sequence: draft retained.":NULL;rc=0;continue;}
  if(key==VK_F5||key==VK_RETURN){
   if(key==VK_F5&&!editable(*flags)){view->notice=L"Read only: Apply is disabled.";continue;}
   STTERM_VALUE value;int valid=full_value(view,*maximum,&value);
   if(valid){view->notice=valid==STTERM_E_CAPACITY?L"Raw length limit exceeded: draft retained.":L"Invalid Unicode scalar sequence: draft retained.";continue;}
   view->notice=L"Input is valid; F5 applies, F12 cancels.";
   if(key==VK_F5){if(view->dirty&&!equal_value(&original,&value))*raw=value;rc=1;break;}continue;
  }
  full_edit(view,&event,editable(*flags));
 }
 free(view);terminal.high=0;
 if(rc>=0){int barrier=transition();if(barrier)return barrier;}
 /* Caller re-renders its panel; retain its focus and cursor internally too. */
 if(terminal.begun&&rc>=0){int draw=render_frame();if(draw)return draw;}
 return rc;
}
