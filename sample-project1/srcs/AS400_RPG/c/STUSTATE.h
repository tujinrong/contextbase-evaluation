#ifndef STUSTATE_H
#define STUSTATE_H
#include <stdint.h>
/* Production gate: 0 OK, 1 legacy reset, 2 expired reset, 3 identity, 4 revision. */
int32_t StSearchStateCheck(int32_t, int64_t, int64_t, int32_t, int32_t, int32_t);
int32_t StSearchKeysValid(const char *, int32_t);
int32_t StSearchBlock(int32_t, int32_t);
#endif
