#include "STUSTATE.h"
#include <string.h>
#include <stdint.h>
int32_t StSearchStateCheck(int32_t identity, int64_t expected, int64_t actual,
                         int32_t stored_format, int32_t request_format, int32_t expired) {
    if(identity != 7) return 3;
    if(actual <= 0 || expected != actual || actual == INT64_MAX) return 4;
    if(expired) return 2;
    if(stored_format != 2 || request_format != 2) return 1;
    return 0;
}
int32_t StSearchKeysValid(const char *keys, int32_t length) {
    static const char *allowed[] = {"studentNo", "name", "classId", "statusCodes"};
    unsigned mask = 0; int32_t start = 0;
    if(!keys || length <= 0 || length > 128) return 0;
    for(int32_t end = 0; end <= length; ++end) {
        if(end != length && keys[end] != ',') continue;
        int found = -1;
        for(int i=0; i<4; ++i) if(end-start == (int32_t)strlen(allowed[i]) &&
            !memcmp(keys+start,allowed[i],(size_t)(end-start))) found=i;
        if(found < 0 || (mask & (1u << found))) return 0;
        mask |= 1u << found; start=end+1;
    }
    return mask == 15;
}
int32_t StSearchBlock(int32_t block, int32_t count) {
    if(count <= 0 || block < 0) return 0;
    if(block >= count) return ((count-1)/8)*8;
    return (block/8)*8;
}
