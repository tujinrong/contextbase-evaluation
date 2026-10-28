#include "student_abi.h"
#include <string.h>
int32_t STABIVERIFY(const ST_DB_REQUEST *q,ST_DB_RESULT *r,ST_VALUE *v){
 if(((uintptr_t)q%8)||((uintptr_t)r%8)||((uintptr_t)v%4))return -1;
 if(memcmp(q->command_id,"ABI-PROBE",9)||q->parameter_count!=2||
 q->parameters[0].type_id!=3||q->parameters[0].null_flag!=-1||
 q->parameters[1].type_id!=5||q->parameters[1].byte_length!=3||
 memcmp(q->parameters[1].data_pointer,"123",3)||v->length!=3)return -1;
 memcpy(r->sqlstate,"23000",5);r->native_error_code=2601;r->affected_rows=123;
 r->cursor_handle=(void*)q;r->error_class=7;v->null_flag=-1;return 0;
}
