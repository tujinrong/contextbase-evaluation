package nenkin.util;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;

public final class HtmlUtil {
	private HtmlUtil() { }

	public static String escape(Object value) {
		String text = value == null ? "" : String.valueOf(value);
		return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
			.replace("\"", "&quot;").replace("'", "&#39;");
	}

	public static String value(Object value) { return value == null ? "" : String.valueOf(value); }
	public static String checked(boolean value) { return value ? " checked" : ""; }
	public static String selected(String actual, String expected) { return expected.equals(actual) ? " selected" : ""; }
	public static String selected(int actual, int expected) { return actual == expected ? " selected" : ""; }

	public static String formatWesternDate(String value) {
		Date date = parseIso(value);
		return date == null ? value(value) : new SimpleDateFormat("yyyy/MM/dd").format(date);
	}

	public static String formatJapaneseDate(String value) {
		Date date = parseIso(value);
		if (date == null) return value(value);
		Calendar target = Calendar.getInstance();
		target.setTime(date);
		int year = target.get(Calendar.YEAR);
		int month = target.get(Calendar.MONTH) + 1;
		int day = target.get(Calendar.DAY_OF_MONTH);
		String symbol;
		int eraYear;
		if (!date.before(parseIso("2019-05-01"))) { symbol = "R"; eraYear = year - 2018; }
		else if (!date.before(parseIso("1989-01-08"))) { symbol = "H"; eraYear = year - 1988; }
		else if (!date.before(parseIso("1926-12-25"))) { symbol = "S"; eraYear = year - 1925; }
		else if (!date.before(parseIso("1912-07-30"))) { symbol = "T"; eraYear = year - 1911; }
		else if (!date.before(parseIso("1868-09-08"))) { symbol = "M"; eraYear = year - 1867; }
		else return formatWesternDate(value);
		return symbol + " " + two(eraYear) + "/" + two(month) + "/" + two(day);
	}

	/** Access帳票の g ee. mm. dd に近い短い和暦表示。 */
	public static String formatReportDate(String value) {
		return formatJapaneseDate(value).replace("/", ". ");
	}

	public static String json(String value) {
		if (value == null) return "";
		StringBuilder result = new StringBuilder();
		for (int i = 0; i < value.length(); i++) {
			char c = value.charAt(i);
			switch (c) {
			case '\\': result.append("\\\\"); break;
			case '"': result.append("\\\""); break;
			case '\r': result.append("\\r"); break;
			case '\n': result.append("\\n"); break;
			case '\t': result.append("\\t"); break;
			case '\b': result.append("\\b"); break;
			case '\f': result.append("\\f"); break;
			case '<': result.append("\\u003c"); break;
			case '>': result.append("\\u003e"); break;
			default:
				if (c < 0x20 || c == '\u2028' || c == '\u2029') result.append(String.format("\\u%04x", Integer.valueOf(c)));
				else result.append(c);
			}
		}
		return result.toString();
	}

	private static Date parseIso(String value) {
		if (value == null || value.trim().length() == 0) return null;
		SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd");
		format.setLenient(false);
		try { return format.parse(value.trim()); } catch (ParseException e) { return null; }
	}

	private static String two(int value) { return value < 10 ? "0" + value : String.valueOf(value); }
}
