#ifndef STUDENT_ABI_H
#define STUDENT_ABI_H
#include <stdint.h>
#include <stddef.h>
typedef struct {int32_t type_id;int16_t null_flag;char pad1[2];int32_t byte_length;char pad2[4];void *data_pointer;} ST_PARAM;
typedef struct {char command_id[12];int32_t parameter_count;ST_PARAM parameters[40];} ST_DB_REQUEST;
typedef struct {char sqlstate[5];char pad1[3];int32_t native_error_code;char pad2[4];int64_t affected_rows;void *cursor_handle;int32_t error_class;char pad3[4];} ST_DB_RESULT;
typedef struct {int32_t length;int16_t null_flag;char pad[2];char data[1024];} ST_VALUE;
_Static_assert(sizeof(void*)==8,"64bit Linux ABI required");
_Static_assert(sizeof(ST_PARAM)==24 && offsetof(ST_PARAM,data_pointer)==16,"parameter ABI");
_Static_assert(sizeof(ST_DB_REQUEST)==976,"request ABI");
_Static_assert(sizeof(ST_DB_RESULT)==40 && offsetof(ST_DB_RESULT,cursor_handle)==24,"result ABI");
_Static_assert(sizeof(ST_VALUE)==1032,"value ABI");
int32_t STDBOP(void*,const ST_DB_REQUEST*,ST_DB_RESULT*);
#endif
