/* Test-only stdin adapter to the unchanged production Unicode helper. */
#include "STUNICODE.h"
#include <stdio.h>
#include <stdlib.h>
#include <unicode/ustring.h>

int main(int argc, char **argv) {
    if (argc != 5) return 2;
    char bytes[4096], utf8[4096];
    uint16_t input[2048], output[2048];
    size_t count = fread(bytes, 1, sizeof(bytes), stdin);
    if (count == sizeof(bytes)) return 2;
    UErrorCode error = U_ZERO_ERROR;
    int32_t length = 0, written = 0, utf8_length = 0;
    u_strFromUTF8((UChar *)input, 2048, &length, bytes, (int32_t)count, &error);
    if (U_FAILURE(error)) return 2;
    int32_t result = StUnicodeNormalize(input, length, atoi(argv[1]), atoi(argv[2]),
        atoi(argv[3]), atoi(argv[4]), output, 2048, &written);
    printf("%d|", result);
    if (result == 0) {
        error = U_ZERO_ERROR;
        u_strToUTF8(utf8, sizeof(utf8), &utf8_length, (const UChar *)output, written, &error);
        if (U_FAILURE(error)) return 2;
        fwrite(utf8, 1, (size_t)utf8_length, stdout);
    }
    puts("");
    return 0;
}
