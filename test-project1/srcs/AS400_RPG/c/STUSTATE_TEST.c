#include "STUSTATE.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static int tests,failed;
static void check(int ok,const char *name) {++tests;printf("%s %s\n",ok?"PASS":"FAIL",name);if(!ok)++failed;}
int main(void) {
 int64_t authoritative=1,first=1,second=1;
 check(StSearchStateCheck(7,first,authoritative,2,2,0)==0,"first current request admitted");
 ++authoritative;
 check(StSearchStateCheck(7,second,authoritative,2,2,0)==4,"second same-revision request rejected after first commit");
 check(StSearchStateCheck(7,authoritative,authoritative,2,2,0)==0,"latest acknowledgment admitted");
 for(int flags=0;flags<7;++flags)check(StSearchStateCheck(flags,2,2,2,2,0)==3,"owner-job-window identity boundary");
 check(StSearchStateCheck(6,1,2,1,1,1)==3,"identity checked before stale or reset");
 check(StSearchStateCheck(7,1,2,1,1,1)==4,"stale revision cannot trigger destructive reset");
 check(StSearchStateCheck(7,2,2,1,2,0)==1,"stored legacy format resets");
 check(StSearchStateCheck(7,2,2,2,1,0)==1,"request legacy format resets");
 check(StSearchStateCheck(7,2,2,2,0,0)==1,"missing format resets");
 check(StSearchStateCheck(7,2,2,2,2,1)==2,"expiry resets");
 check(StSearchStateCheck(7,0,0,2,2,0)==4,"unissued revision denied");
 check(StSearchStateCheck(7,INT64_MAX,INT64_MAX,2,2,0)==4,"revision overflow fails closed");
 check(StSearchStateCheck(7,9007199254740993LL,9007199254740993LL,2,2,0)==0,"revision retains full Int64 precision");
 const char *good="studentNo,name,classId,statusCodes";
 check(StSearchKeysValid(good,(int32_t)strlen(good)),"four native keys accepted");
 const char *reordered="statusCodes,classId,name,studentNo";
 check(StSearchKeysValid(reordered,(int32_t)strlen(reordered)),"key order irrelevant");
 const char *bad[]={"studentNo,name,classId,statusCodes,kana","studentNo,name,classId,statusCodes,schoolYear","studentNo,name,classId,statusCodes,gradeCode","studentNo,name,classId,statusCodes,unassignedOnly","studentNo,name,classId,statusCodes,prefectureCode","studentNo,name,classId,statusCodes,phone","studentNo,name,classId,statusCodes,admissionFrom","studentNo,name,classId,statusCodes,admissionTo","studentNo,name,classId,statusCodes,unknown","studentNo,name,classId,name","studentNo,name,classId","","studentNo,name,classId,statusCodes,"};
 for(unsigned i=0;i<sizeof(bad)/sizeof(*bad);++i)check(!StSearchKeysValid(bad[i],(int32_t)strlen(bad[i])),"obsolete-unknown-duplicate-invalid native keys rejected");
 check(!StSearchKeysValid(0,1),"null key buffer rejected");
 check(!StSearchKeysValid(good,129),"oversized key buffer rejected before read");
 check(StSearchBlock(16,16)==8,"delete or filter change clamps last empty block");
 check(StSearchBlock(16,17)==16,"valid partial last block preserved");
 check(StSearchBlock(96,0)==0,"empty result starts at zero");
 check(StSearchBlock(-8,20)==0,"negative block corrected");
 check(StSearchBlock(99,100)==96,"last page block rounded");
 check(StSearchBlock(8,20)==8,"middle block preserved");
 printf("RESULT tests=%d failures=%d\n",tests,failed);return failed?1:0;
}
