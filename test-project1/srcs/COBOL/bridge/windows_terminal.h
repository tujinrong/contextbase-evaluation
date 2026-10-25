#ifndef WINDOWS_TERMINAL_H
#define WINDOWS_TERMINAL_H
#include "student_abi.h"
typedef ST_VALUE STTERM_VALUE;
enum {
 STTERM_EDIT=1, STTERM_HEADER=2, STTERM_ERROR=4, STTERM_READONLY_FOCUS=8,
 STTERM_SHIFT=0x10000, STTERM_CTRL=0x20000, STTERM_ALT=0x40000,
 STTERM_E_ARGUMENT=-701, STTERM_E_ENCODING=-702, STTERM_E_CAPACITY=-703,
 STTERM_E_CONSOLE=-704, STTERM_E_SESSION=-705, STTERM_E_STATE=-706,
 STTERM_E_FIELD=-707
};
/* cdecl, signed native int32 BY REFERENCE; coordinates start at (1,1).
 * NULL is int16 -1 with length0, empty text is int16 0 with length0.
 * BEGIN replaces the frame: callers GET changed raw values before BEGIN.
 * Same panel identity preserves queued input/cursor; different identities mark
 * a purpose/modal boundary and block queued or held old-panel action keys.
 * NEXT returns VK in low16 plus modifiers above, focus is in/out.
 * FULL returns1 only for explicit successful Apply; Cancel returns0.
 * No function authenticates, queries a database, or makes a business decision.
 */
int32_t STTERMOPEN(const int32_t *columns,const int32_t *rows);
int32_t STTERMBEGIN(const STTERM_VALUE *panel,const STTERM_VALUE *title);
int32_t STTERMADD(const int32_t *id,const int32_t *row,const int32_t *column,
 const int32_t *width,const int32_t *height,const int32_t *flags,
 const int32_t *max_scalars,const STTERM_VALUE *value);
int32_t STTERMNEXT(int32_t *key,int32_t *focus);
int32_t STTERMGET(const int32_t *id,STTERM_VALUE *value,int32_t *changed);
int32_t STTERMFULL(STTERM_VALUE *raw,const STTERM_VALUE *title,
 const int32_t *flags,const int32_t *max_scalars);
int32_t STTERMCLOSE(void);
#endif
