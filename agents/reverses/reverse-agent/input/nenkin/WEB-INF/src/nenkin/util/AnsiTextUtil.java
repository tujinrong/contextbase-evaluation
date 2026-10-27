package nenkin.util;

import java.nio.ByteBuffer;
import java.nio.CharBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.Charset;
import java.nio.charset.CharsetDecoder;
import java.nio.charset.CharsetEncoder;
import java.nio.charset.CodingErrorAction;

/** Access StrConv(..., vbFromUnicode) 相当の Windows-31J バイト長検証。 */
public final class AnsiTextUtil {
    public static final int NOTES_MAX_BYTES = 56;

    private static final Charset WINDOWS_31J = Charset.forName("Windows-31J");

    private AnsiTextUtil() {
    }

    public static int byteLength(String value) {
        return toAnsiBytes(value).length;
    }

    public static boolean isEncodable(String value) {
        return WINDOWS_31J.newEncoder().canEncode(value == null ? "" : value);
    }

    public static boolean isWithinBytes(String value, int maxBytes) {
        if (maxBytes < 0) {
            throw new IllegalArgumentException("最大バイト数は0以上で指定してください。");
        }
        return isEncodable(value) && byteLength(value) <= maxBytes;
    }

    public static boolean isValidNotes(String value) {
        return isWithinBytes(value, NOTES_MAX_BYTES);
    }

    public static void validateNotes(String value) {
        if (!isEncodable(value)) {
            throw new IllegalArgumentException("備考にWindows-31Jへ変換できない文字が含まれています。");
        }
        int length = byteLength(value);
        if (length > NOTES_MAX_BYTES) {
            throw new IllegalArgumentException("備考はANSI換算"
                    + NOTES_MAX_BYTES + "バイト以内で入力してください。現在: " + length);
        }
    }

    public static String truncate(String value, int maxBytes) {
        String source = value == null ? "" : value;
        if (maxBytes <= 0 || source.length() == 0) {
            return "";
        }
        StringBuilder result = new StringBuilder();
        int offset = 0;
        while (offset < source.length()) {
            int codePoint = source.codePointAt(offset);
            String next = new String(Character.toChars(codePoint));
            if (!isEncodable(next) || byteLength(result.toString() + next) > maxBytes) {
                break;
            }
            result.append(next);
            offset += Character.charCount(codePoint);
        }
        return result.toString();
    }

    public static byte[] toAnsiBytes(String value) {
        CharsetEncoder encoder = WINDOWS_31J.newEncoder();
        encoder.onMalformedInput(CodingErrorAction.REPORT);
        encoder.onUnmappableCharacter(CodingErrorAction.REPORT);
        try {
            ByteBuffer buffer = encoder.encode(CharBuffer.wrap(value == null ? "" : value));
            byte[] bytes = new byte[buffer.remaining()];
            buffer.get(bytes);
            return bytes;
        } catch (CharacterCodingException e) {
            throw new IllegalArgumentException("Windows-31Jへ変換できない文字が含まれています。", e);
        }
    }

    public static String fromAnsiBytes(byte[] value) {
        CharsetDecoder decoder = WINDOWS_31J.newDecoder();
        decoder.onMalformedInput(CodingErrorAction.REPORT);
        decoder.onUnmappableCharacter(CodingErrorAction.REPORT);
        try {
            return decoder.decode(ByteBuffer.wrap(value == null ? new byte[0] : value)).toString();
        } catch (CharacterCodingException e) {
            throw new IllegalArgumentException("不正なWindows-31Jバイト列です。", e);
        }
    }
}
