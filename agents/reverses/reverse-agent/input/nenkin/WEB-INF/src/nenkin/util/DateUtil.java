package nenkin.util;

import java.text.Normalizer;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** 和暦・西暦表示と内部 ISO 日付の変換。 */
public final class DateUtil {
    private static final Pattern ERA_DATE = Pattern.compile(
            "^(\u4ee4\u548c|\u5e73\u6210|\u662d\u548c|\u5927\u6b63|\u660e\u6cbb|R|H|S|T|M)\\s*"
            + "(\u5143|[0-9]{1,3})[\\./\\-\u5e74]\\s*([0-9]{1,2})[\\./\\-\u6708]\\s*"
            + "([0-9]{1,2})\u65e5?$", Pattern.CASE_INSENSITIVE);
    private static final Pattern GREGORIAN_DATE = Pattern.compile(
            "^([0-9]{4})[\\./\\-]([0-9]{1,2})[\\./\\-]([0-9]{1,2})$");
    private static final Pattern COMPACT_DATE = Pattern.compile("^([0-9]{4})([0-9]{2})([0-9]{2})$");

    private static final Era[] ERAS = {
        new Era("M", "明治", 1868, "1868-09-08", "1912-07-29"),
        new Era("T", "大正", 1912, "1912-07-30", "1926-12-24"),
        new Era("S", "昭和", 1926, "1926-12-25", "1989-01-07"),
        new Era("H", "平成", 1989, "1989-01-08", "2019-04-30"),
        new Era("R", "令和", 2019, "2019-05-01", null)
    };

    private DateUtil() {
    }

    /** yyyy-MM-dd、yyyy/MM/dd、yyyyMMdd、和暦を yyyy-MM-dd に正規化する。 */
    public static String toIsoDate(String value) {
        String input = normalizeInput(value);
        if (input.length() == 0) {
            return "";
        }

        Matcher eraMatcher = ERA_DATE.matcher(input);
        if (eraMatcher.matches()) {
            Era era = findEra(eraMatcher.group(1));
            int eraYear = "元".equals(eraMatcher.group(2))
                    ? 1 : Integer.parseInt(eraMatcher.group(2));
            if (eraYear <= 0) {
                throw invalid(value);
            }
            int year = era.baseYear + eraYear - 1;
            String iso = formatIso(year, Integer.parseInt(eraMatcher.group(3)),
                    Integer.parseInt(eraMatcher.group(4)), value);
            Date date = parseIso(iso, value);
            if (date.before(era.start) || (era.end != null && date.after(era.end))) {
                throw invalid(value);
            }
            return iso;
        }

        Matcher western = GREGORIAN_DATE.matcher(input);
        if (western.matches()) {
            return formatIso(Integer.parseInt(western.group(1)),
                    Integer.parseInt(western.group(2)), Integer.parseInt(western.group(3)), value);
        }

        Matcher compact = COMPACT_DATE.matcher(input);
        if (compact.matches()) {
            return formatIso(Integer.parseInt(compact.group(1)),
                    Integer.parseInt(compact.group(2)), Integer.parseInt(compact.group(3)), value);
        }

        throw invalid(value);
    }

    public static String toGregorianDisplay(String value) {
        String iso = toIsoDate(value);
        return iso.length() == 0 ? "" : iso.replace('-', '/');
    }

    /** R 08/06/11 形式の表示値を返す。 */
    public static String toWarekiDisplay(String value) {
        String iso = toIsoDate(value);
        if (iso.length() == 0) {
            return "";
        }
        Date date = parseIso(iso, value);
        Era era = eraFor(date);
        Calendar calendar = new GregorianCalendar();
        calendar.setTime(date);
        int eraYear = calendar.get(Calendar.YEAR) - era.baseYear + 1;
        return era.code + " " + twoOrMoreDigits(eraYear) + "/"
                + twoDigits(calendar.get(Calendar.MONTH) + 1) + "/"
                + twoDigits(calendar.get(Calendar.DAY_OF_MONTH));
    }

    /** Access Format(..., "ge.mm.dd") に近い R8.06.11 形式。 */
    public static String toAccessWareki(String value) {
        String display = toWarekiDisplay(value);
        if (display.length() == 0) {
            return "";
        }
        String[] fields = display.substring(2).split("/");
        int year = Integer.parseInt(fields[0]);
        return display.substring(0, 1) + year + "." + fields[1] + "." + fields[2];
    }

    public static boolean isValid(String value) {
        try {
            return toIsoDate(value).length() > 0;
        } catch (IllegalArgumentException e) {
            return false;
        }
    }

    public static String todayIso() {
        return new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT).format(new Date());
    }

    public static String currentTime() {
        return new SimpleDateFormat("HH:mm:ss.SSS", Locale.ROOT).format(new Date());
    }

    public static String firstDayOfMonth(String value) {
        String iso = toIsoDate(value);
        return iso.length() == 0 ? "" : iso.substring(0, 8) + "01";
    }

    public static String lastDayOfMonth(String value) {
        String iso = toIsoDate(value);
        if (iso.length() == 0) {
            return "";
        }
        Date date = parseIso(iso, value);
        Calendar calendar = new GregorianCalendar();
        calendar.setTime(date);
        int lastDay = calendar.getActualMaximum(Calendar.DAY_OF_MONTH);
        return iso.substring(0, 8) + twoDigits(lastDay);
    }

    private static String normalizeInput(String value) {
        if (value == null) {
            return "";
        }
        String result = Normalizer.normalize(value, Normalizer.Form.NFKC).trim();
        result = result.replace('　', ' ');
        return result;
    }

    private static Era findEra(String token) {
        Era[] values = ERAS;
        for (int i = 0; i < values.length; i++) {
            if (values[i].code.equalsIgnoreCase(token) || values[i].name.equals(token)) {
                return values[i];
            }
        }
        throw new IllegalArgumentException("未対応の元号です: " + token);
    }

    private static Era eraFor(Date date) {
        for (int i = ERAS.length - 1; i >= 0; i--) {
            if (!date.before(ERAS[i].start)) {
                return ERAS[i];
            }
        }
        throw new IllegalArgumentException("明治元年より前の日付は和暦変換できません。");
    }

    private static String formatIso(int year, int month, int day, String original) {
        String iso = fourDigits(year) + "-" + twoDigits(month) + "-" + twoDigits(day);
        parseIso(iso, original);
        return iso;
    }

    private static Date parseIso(String value, String original) {
        SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT);
        format.setLenient(false);
        try {
            return format.parse(value);
        } catch (ParseException e) {
            throw invalid(original);
        }
    }

    private static String twoDigits(int value) {
        return value < 10 ? "0" + value : Integer.toString(value);
    }

    private static String twoOrMoreDigits(int value) {
        return value < 10 ? "0" + value : Integer.toString(value);
    }

    private static String fourDigits(int value) {
        String result = Integer.toString(value);
        while (result.length() < 4) {
            result = "0" + result;
        }
        return result;
    }

    private static IllegalArgumentException invalid(String value) {
        return new IllegalArgumentException("日付の形式または実在性が不正です: " + value);
    }

    private static final class Era {
        private final String code;
        private final String name;
        private final int baseYear;
        private final Date start;
        private final Date end;

        private Era(String code, String name, int baseYear, String start, String end) {
            this.code = code;
            this.name = name;
            this.baseYear = baseYear;
            this.start = parseIso(start, start);
            this.end = end == null ? null : parseIso(end, end);
        }
    }
}
