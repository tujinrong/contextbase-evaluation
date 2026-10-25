#ifndef STUNICODE_H
#define STUNICODE_H
#include <stdint.h>
int32_t StUnicodeScalars(const uint16_t *, int32_t);
int32_t StUnicodeNormalize(const uint16_t *, int32_t, int32_t, int32_t, int32_t, int32_t, uint16_t *, int32_t, int32_t *);
int32_t StUnicodeToJob(const uint16_t *, int32_t, int32_t, char *, int32_t, int32_t *);
int32_t StUnicodeFromJob(const char *, int32_t, int32_t, uint16_t *, int32_t, int32_t *);
int32_t StUnicodeEscape(const uint16_t *, int32_t, int32_t, uint16_t *, int32_t, int32_t *);
void StUnicodeDigest(const uint16_t *, int32_t, char [64]);
/* Physical window lengths include SI/SO. Offsets/counts are UTF16 units. */
int32_t StTextWindow(const uint16_t *,int32_t,int32_t,int32_t,char *,int32_t,int32_t *,int32_t *);
int32_t StTextSplice(const uint16_t *,int32_t,int32_t,int32_t,const uint16_t *,int32_t,uint16_t *,int32_t,int32_t *);
int32_t StTextEscapeWindow(const uint16_t *,int32_t,int32_t,uint16_t *,int32_t,int32_t *,int32_t *);
int32_t StTextLimit(const uint16_t *,int32_t,int32_t,int32_t);
#endif
