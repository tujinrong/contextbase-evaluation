/* Synthetic native-console unit tests. Session stubs are test-only; the real
 * student_bridge session is exercised separately by the integration fixture. */
#define STTERM_TEST
#include "../bridge/windows_terminal.c"
#include <time.h>
static int session_live=1,touches,checks_until_expiry,touch_failure;
int32_t STSAMPLECHECK(void){if(checks_until_expiry>0&&--checks_until_expiry==0)session_live=0;return session_live?0:-1;}
int32_t STSAMPLETOUCH(void){touches++;if(touch_failure){session_live=0;return -1;}return STSAMPLECHECK();}
typedef struct {WORD vk;uint32_t cp;DWORD mods;WORD repeat;} Step;
static Step script[10000];static size_t script_count,script_at;
static unsigned passed,failed;
static FILE *report;
static int first=1;
static void check(int value,const char *name){
 if(!first)fprintf(report,",\n");first=0;
 fprintf(report,"{\"name\":\"%s\",\"passed\":%s}",name,value?"true":"false");
 if(value)passed++;else{failed++;fprintf(stderr,"FAIL: %s\n",name);}fflush(report);
}
static STTERM_VALUE val(const char *s){STTERM_VALUE v;memset(&v,0x5a,sizeof v);v.length=(int32_t)strlen(s);v.null_flag=0;memcpy(v.data,s,(size_t)v.length);return v;}
static STTERM_VALUE nullval(void){STTERM_VALUE v=val("");v.null_flag=-1;return v;}
static void queue_event(WORD vk,WCHAR c,DWORD mods,WORD repeat,int down){
 INPUT_RECORD r;DWORD wrote;memset(&r,0,sizeof r);r.EventType=KEY_EVENT;
 r.Event.KeyEvent.bKeyDown=down;r.Event.KeyEvent.wVirtualKeyCode=vk;
 r.Event.KeyEvent.wRepeatCount=repeat;r.Event.KeyEvent.uChar.UnicodeChar=c;r.Event.KeyEvent.dwControlKeyState=mods;
 if(!WriteConsoleInputW(terminal.input,&r,1,&wrote)||wrote!=1){fprintf(stderr,"Queue failed\n");exit(3);}
}
static void feed(int full){
 (void)full;DWORD n;if(!GetNumberOfConsoleInputEvents(terminal.input,&n)||n||script_at>=script_count)return;
 Step s=script[script_at++];
 if(s.cp>0xffff){uint32_t c=s.cp-0x10000;queue_event(0,(WCHAR)(0xd800+(c>>10)),s.mods,s.repeat,1);queue_event(0,0,0,1,0);queue_event(0,(WCHAR)(0xdc00+(c&1023)),s.mods,s.repeat,1);queue_event(0,0,0,1,0);}
 else{queue_event(s.vk,(WCHAR)s.cp,s.mods,s.repeat,1);queue_event(s.vk,0,0,1,0);}
}
static void prepare(void){
 FlushConsoleInputBuffer(terminal.input);memset(terminal.down,0,sizeof terminal.down);memset(terminal.blocked,0,sizeof terminal.blocked);terminal.high=0;
 script_at=script_count=0;touches=0;touch_failure=0;checks_until_expiry=0;session_live=1;terminal_test_wait_hook=feed;
}
static void step(WORD vk,uint32_t cp,DWORD mods,WORD repeat){script[script_count++]=(Step){vk,cp,mods,repeat};}
static void key(WORD vk){step(vk,0,0,1);}
static void text(const char *s){for(;*s;s++)step(0,(unsigned char)*s,0,1);}
static void erase_token(void){key(VK_HOME);for(int i=0;i<6;i++)key(VK_DELETE);}
static int begin(void){STTERM_VALUE p=val("UNIT"),t=val("Native console unit");return STTERMBEGIN(&p,&t);}
static int begin_other(void){STTERM_VALUE p=val("CONFIRM"),t=val("Confirmation unit");return STTERMBEGIN(&p,&t);}
static int add(int id,int flags,const STTERM_VALUE *value){int row=id+2,col=2,width=40,height=1,max=8;return STTERMADD(&id,&row,&col,&width,&height,&flags,&max,value);}
static STTERM_VALUE get(int id,int *changed){STTERM_VALUE result;memset(&result,0,sizeof result);check(STTERMGET(&id,&result,changed)==0,"GET succeeds");return result;}
static int next(int *focus){int keycode=-1;int rc=STTERMNEXT(&keycode,focus);check(rc==0,"NEXT succeeds");return keycode;}

static void codec_tests(void){
 uint32_t cp[1024];size_t n;STTERM_VALUE out;
 check(sizeof(STTERM_VALUE)==1032&&offsetof(STTERM_VALUE,null_flag)==4&&offsetof(STTERM_VALUE,data)==8,"fixed value ABI1032 offsets");
 const char *valid[]={"","ASCII","\xe5\xad\xa6\xe7\x94\x9f","\xe3\x81\x8b\xe3\x82\x99\x65\xcc\x81","\xf0\xa0\xae\xb7\xf0\x9f\x98\x80","\xf4\x8f\xbf\xbf"};
 for(size_t i=0;i<sizeof valid/sizeof *valid;i++){STTERM_VALUE v=val(valid[i]);int rc=decode(&v,cp,1024,&n);check(rc==0&&encode(cp,n,&out)==0&&equal_value(&v,&out),"strict UTF8 scalar roundtrip");}
 const unsigned char bad[][5]={{0xc0,0xaf},{0xe0,0x80,0xaf},{0xed,0xa0,0x80},{0xf4,0x90,0x80,0x80},{0xe3,0x81},{0x80},{0x61,0,0x62}};
 const int lengths[]={2,3,3,4,2,1,3};
 for(size_t i=0;i<sizeof lengths/sizeof *lengths;i++){STTERM_VALUE v=val("");v.length=lengths[i];memcpy(v.data,bad[i],(size_t)v.length);check(decode(&v,cp,1024,&n)==STTERM_E_ENCODING,"invalid UTF8 or NUL rejected");}
 STTERM_VALUE v=val("x");v.length=1025;check(decode(&v,cp,1024,&n)<0,"length1025 rejected");
 v.length=-1;check(decode(&v,cp,1024,&n)<0,"negative length rejected");v=val("x");v.null_flag=-1;check(decode(&v,cp,1024,&n)<0,"NULL with nonzero length rejected");
 v=nullval();check(decode(&v,cp,1024,&n)==0&&n==0,"NULL minus1 accepted separately from empty");
 Full view;memset(&view,0,sizeof view);const char *tokens[]={"U+000A U+20BB7","U+D800","U+110000","U+0000","U+123","U+XXXX","U+0041x"};
 for(size_t i=0;i<sizeof tokens/sizeof *tokens;i++){view.count=strlen(tokens[i]);for(size_t j=0;j<view.count;j++)view.text[j]=(unsigned char)tokens[i][j];int rc=parse_points(&view,cp,&n);check(i==0?(rc==0&&n==2&&cp[0]==10&&cp[1]==0x20bb7):rc<0,"codepoint grammar and scalar boundary");}
}
static void frame_tests(void){
 int col=132,row=27;check(STTERMOPEN(&col,&row)==0,"native132x27 OPEN");check(!IsWindowVisible(GetConsoleWindow()),"test console stays hidden");
 check(dimensions()==0,"real native buffer and visible rectangle132x27");check(STTERMOPEN(&col,&row)==STTERM_E_STATE,"double OPEN rejected");
 prepare();check(begin()==0,"BEGIN frame");STTERM_VALUE original=val("M");check(add(1,1,&original)==0,"ADD editable projection");
 check(add(1,1,&original)==STTERM_E_FIELD,"duplicate field ID rejected");
 int id=2,r=0,c=2,w=10,h=1,f=1,m=8;check(STTERMADD(&id,&r,&c,&w,&h,&f,&m,&original)<0,"row0 rejected");r=27;h=2;check(STTERMADD(&id,&r,&c,&w,&h,&f,&m,&original)<0,"row overflow rejected");r=2;h=1;c=132;w=2;check(STTERMADD(&id,&r,&c,&w,&h,&f,&m,&original)<0,"column overflow rejected");
 int changed;STTERM_VALUE result=get(1,&changed);check(changed==0&&memcmp(&result,&original,sizeof result)==0,"unchanged projection preserves every original byte");
 prepare();text("X");key(VK_BACK);key(VK_F1);int focus=1;check(next(&focus)==VK_F1,"ordinary editing returns only explicit action");result=get(1,&changed);check(changed==0&&memcmp(&result,&original,sizeof result)==0,"reverted edit restores original raw and padding");
 prepare();step(0,'x',0,3);key(VK_F1);next(&focus);result=get(1,&changed);check(changed==1&&result.length==4&&memcmp(result.data,"Mxxx",4)==0,"coalesced repeat count retains all typed characters");
 prepare();begin();original=val("P");for(int i=1;i<=6;i++){int flags[]={1,0,2,4,8,5};check(add(i,flags[i-1],&original)==0,"register protected and styled fields");}
 key(VK_TAB);focus=1;check(next(&focus)==VK_TAB&&focus==5,"Tab skips protected labels and error-only fields");
 step(VK_TAB,0,SHIFT_PRESSED,1);check(next(&focus)==(VK_TAB|STTERM_SHIFT)&&focus==1,"ShiftTab reverses focusable order");
 for(int i=2;i<=5;i++){
  prepare();text("X");key(VK_BACK);key(VK_F1);focus=i;next(&focus);
  result=get(i,&changed);check(changed==0&&memcmp(&result,&original,sizeof result)==0,"protected fields cannot be edited");
 }
 prepare();begin();original=val("\xf0\xa0\xae\xb7\xf0\x9f\x98\x80");add(1,1,&original);key(VK_BACK);key(VK_F1);focus=1;next(&focus);result=get(1,&changed);check(result.length==4&&memcmp(result.data,"\xf0\xa0\xae\xb7",4)==0,"backspace removes whole supplementary scalar");
 prepare();begin();original=val("\xe3\x81\x8b\xe3\x82\x99");add(1,1,&original);key(VK_BACK);key(VK_F1);focus=1;next(&focus);result=get(1,&changed);check(result.length==3&&memcmp(result.data,"\xe3\x81\x8b",3)==0,"combining mark remains separate without normalization");
 prepare();begin();original=val("A");add(1,1,&original);queue_event(VK_F5,0,0,5,1);check(begin_other()==0,"new panel drains old queued keydown");add(1,1,&original);key(VK_F5);key(VK_F5);focus=1;check(next(&focus)==VK_F5&&script_at==2&&touches==1,"held F5 cannot commit until release and fresh press");
 prepare();queue_event(VK_RETURN,0,0,1,1);queue_event(VK_RETURN,0,0,1,0);queue_event(VK_F5,0,0,1,1);queue_event(VK_F5,0,0,1,0);begin();add(1,1,&original);key(VK_F12);focus=1;check(next(&focus)==VK_F12,"queued Enter and save key do not carry into confirmation panel");
 prepare();terminal.high=0xd842;begin_other();add(1,1,&original);step(0,0xdfb7,0,1);focus=1;int keycode;check(STTERMNEXT(&keycode,&focus)==STTERM_E_ENCODING,"surrogate cannot join across panel boundary");result=get(1,&changed);check(changed==0,"invalid UTF16 never mutates raw");
}
static void full_tests(void){
 STTERM_VALUE title=val("Full helper"),original=val("A"),raw;int editable_flags=1,readonly_flags=8,maximum=8;
 prepare();raw=original;text("Z");key(VK_F12);check(STTERMFULL(&raw,&title,&editable_flags,&maximum)==0&&memcmp(&raw,&original,sizeof raw)==0,"FULL Cancel keeps all1032 original bytes");
 prepare();raw=nullval();STTERM_VALUE old=raw;key(VK_F5);check(STTERMFULL(&raw,&title,&editable_flags,&maximum)==1&&memcmp(&raw,&old,sizeof raw)==0,"unchanged FULL Apply preserves NULL minus1");
 prepare();raw=original;text("Z");key(VK_F5);key(VK_F12);check(STTERMFULL(&raw,&title,&readonly_flags,&maximum)==0&&memcmp(&raw,&original,sizeof raw)==0,"readonly FULL ignores input and Apply");
 prepare();raw=val("U+0041");old=raw;key(VK_F5);check(STTERMFULL(&raw,&title,&editable_flags,&maximum)==1&&memcmp(&raw,&old,sizeof raw)==0,"normal mode never interprets literal codepoint text");
 prepare();raw=val("\xe3\x81\x8b\xe3\x82\x99\xf0\xa0\xae\xb7");old=raw;key(VK_F2);key(VK_F2);key(VK_F5);check(STTERMFULL(&raw,&title,&editable_flags,&maximum)==1&&memcmp(&raw,&old,sizeof raw)==0,"mode toggles preserve combining and supplementary raw");
 prepare();raw=original;key(VK_F2);erase_token();text("U+000A U+20BB7");key(VK_F5);check(STTERMFULL(&raw,&title,&editable_flags,&maximum)==1&&raw.length==5&&memcmp(raw.data,"\n\xf0\xa0\xae\xb7",5)==0,"explicit codepoint LF and supplementary Apply");
 prepare();raw=original;key(VK_F2);erase_token();text("U+D800");key(VK_F2);erase_token();text("U+0042");key(VK_F5);check(STTERMFULL(&raw,&title,&editable_flags,&maximum)==1&&raw.length==1&&raw.data[0]=='B'&&script_at==script_count,"invalid codepoint toggle retains draft for correction");
 prepare();raw=original;text("B");key(VK_RETURN);key(VK_F12);check(STTERMFULL(&raw,&title,&editable_flags,&maximum)==0&&memcmp(&raw,&original,sizeof raw)==0,"FULL Enter validates without Apply or automatic LF");
 prepare();raw=original;maximum=1;text("B");key(VK_F5);key(VK_BACK);key(VK_F5);check(STTERMFULL(&raw,&title,&editable_flags,&maximum)==1&&memcmp(&raw,&original,sizeof raw)==0&&script_at==script_count,"scalar overflow retains editable draft until corrected");
 prepare();raw=val("");memset(raw.data,'A',1024);raw.length=1024;old=raw;maximum=0;text("X");key(VK_F5);key(VK_BACK);key(VK_F5);check(STTERMFULL(&raw,&title,&editable_flags,&maximum)==1&&memcmp(&raw,&old,sizeof raw)==0&&script_at==script_count,"byte1025 Apply rejected without losing1024-byte original");
 prepare();raw=val("A\x1b" "[31mB");old=raw;key(VK_F12);check(STTERMFULL(&raw,&title,&readonly_flags,&maximum)==0&&memcmp(&raw,&old,sizeof raw)==0,"ESC sequence is data and raw remains unchanged");
}
static void queued_input_tests(void){
 STTERM_VALUE a=val("A"),b=val("B");int changed,focus=1;
 prepare();begin();add(1,1,&a);add(2,1,&b);
 queue_event(VK_TAB,9,0,1,1);queue_event(VK_TAB,0,0,1,0);
 queue_event(0,'X',0,1,1);queue_event(0,0,0,1,0);
 queue_event(VK_F1,0,0,1,1);queue_event(VK_F1,0,0,1,0);key(VK_F12);
 check(next(&focus)==VK_TAB&&focus==2,"queued Tab returns next field");
 a=get(1,&changed);b=get(2,&changed);begin();add(1,1,&a);add(2,1,&b);
 check(next(&focus)==VK_F1&&script_at==0,"same-panel BEGIN retains queued next-field characters");
 b=get(2,&changed);check(b.length==2&&memcmp(b.data,"BX",2)==0,"queued character survives Tab redraw without truncation");
 prepare();begin();a=val("AB");add(1,1,&a);focus=1;
 queue_event(VK_HOME,0,0,1,1);queue_event(VK_HOME,0,0,1,0);
 queue_event(VK_RIGHT,0,0,1,1);queue_event(VK_RIGHT,0,0,1,0);
 queue_event(VK_SPACE,32,0,1,1);queue_event(VK_SPACE,0,0,1,0);
 queue_event(0,'X',0,1,1);queue_event(0,0,0,1,0);
 queue_event(VK_F1,0,0,1,1);queue_event(VK_F1,0,0,1,0);key(VK_F12);
 check(next(&focus)==VK_SPACE,"Space returns after insertion");a=get(1,&changed);begin();add(1,1,&a);
 check(next(&focus)==VK_F1&&script_at==0,"same-panel Space redraw retains following input");
 a=get(1,&changed);check(a.length==4&&memcmp(a.data,"A XB",4)==0,"same-panel redraw preserves insertion cursor");
 prepare();begin();a=val("A");add(1,1,&a);
 for(int i=VK_F1;i<=VK_F12;i++){
  prepare();key((WORD)i);focus=1;check(next(&focus)==i,"function key decoded from native INPUT_RECORD");
 }
 prepare();step(VK_HOME,0,LEFT_CTRL_PRESSED,1);focus=1;
 check(next(&focus)==(VK_HOME|STTERM_CTRL),"CtrlHome returned for COBOL first-page action");
 prepare();step(VK_END,0,LEFT_CTRL_PRESSED,1);
 check(next(&focus)==(VK_END|STTERM_CTRL),"CtrlEnd returned for COBOL last-page action");
 prepare();step(VK_F4,0,SHIFT_PRESSED,1);
 check(next(&focus)==(VK_F4|STTERM_SHIFT),"Shift modifier retained");
 prepare();step('X',0,LEFT_ALT_PRESSED,1);
 check(next(&focus)==('X'|STTERM_ALT),"Alt modifier retained without editing");
 prepare();begin();a=val("");add(1,1,&a);step(0,0x20bb7,0,1);step(0,0x3099,0,1);key(VK_F1);focus=1;next(&focus);
 a=get(1,&changed);check(a.length==7&&memcmp(a.data,"\xf0\xa0\xae\xb7\xe3\x82\x99",7)==0,"synthetic UTF16 pair and combining input retain exact UTF8");
 prepare();begin();a=val("123456789");check(add(1,1,&a)==0,"existing scalar-overlimit raw remains displayable");
 b=get(1,&changed);check(!changed&&memcmp(&a,&b,sizeof a)==0,"existing scalar-overlimit raw is not truncated");
 prepare();begin();a=val("A\x1b" "[31mB");add(1,1,&a);key(VK_F1);focus=1;next(&focus);
 CHAR_INFO cell;SMALL_RECT region={2,2,2,2};COORD size={1,1},zero={0,0};
 check(ReadConsoleOutputW(terminal.output,&cell,size,zero,&region)&&cell.Char.UnicodeChar==0x241b,"ESC is a safe visible cell, not an executed sequence");
}
static void full_cursor_test(void){
 STTERM_VALUE raw=val("AB"),title=val("Full cursor");int flags=1,maximum=8,focus=1,changed;
 prepare();begin();add(1,1,&raw);key(VK_HOME);key(VK_RIGHT);key(VK_F8);
 check(next(&focus)==VK_F8,"F8 preserves scalar insertion cursor");
 prepare();text("X");key(VK_F12);
 check(STTERMFULL(&raw,&title,&flags,&maximum)==0,"FULL cursor fixture cancels");
 begin();add(1,1,&raw);prepare();text("X");key(VK_F1);next(&focus);
 raw=get(1,&changed);check(raw.length==3&&memcmp(raw.data,"AXB",3)==0,"FULL Cancel and same-panel redraw restore original cursor");
}
static void session_tests(void){
 prepare();begin();STTERM_VALUE v=val("A");add(1,1,&v);int focus=1,keycode;checks_until_expiry=3;ULONGLONG start=GetTickCount64();
 check(STTERMNEXT(&keycode,&focus)==STTERM_E_SESSION&&GetTickCount64()-start<=1500&&touches==0,"idle poll expires within1second without TOUCH");
 prepare();begin();add(1,1,&v);touch_failure=1;text("X");check(STTERMNEXT(&keycode,&focus)==STTERM_E_SESSION,"TOUCH race cannot revive expired session");int changed;STTERM_VALUE out=get(1,&changed);check(changed==0&&equal_value(&out,&v),"expiry race never accepts pending text");
 prepare();int flags=1,max=8;session_live=0;STTERM_VALUE raw=v;check(STTERMFULL(&raw,&v,&flags,&max)==STTERM_E_SESSION&&memcmp(&raw,&v,sizeof raw)==0,"expired FULL retains raw");
 check(STTERMCLOSE()==0,"CLOSE restores buffers and modes after expiry");check(STTERMCLOSE()==0,"CLOSE is idempotent");
}
int main(int argc,char **argv){
 if(argc!=2)return 3;report=fopen(argv[1],"wb");if(!report)return 3;
 fprintf(report,"{\"scope\":\"native-unit-synthetic-input\",\"session\":\"test-only CHECK/TOUCH stubs\",\"checks\":[\n");
 codec_tests();frame_tests();full_tests();queued_input_tests();full_cursor_test();session_tests();
 fprintf(report,"\n],\"passed\":%u,\"failed\":%u,\"status\":\"%s\",\"manualGlyphImeKeyboard\":\"NOT_RUN\"}\n",passed,failed,failed?"Failed":"Passed");fclose(report);
 printf("native terminal unit: %u passed, %u failed\n",passed,failed);return failed?1:0;
}
