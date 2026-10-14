package nenkin.util;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.Charset;
import java.util.List;
import java.util.Locale;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

/**
 * 外部ライブラリを使わず、単1シートの Open XML (.xlsx) を生成する。
 */
public final class OpenXmlWorkbookWriter {
    private static final Charset UTF8 = Charset.forName("UTF-8");
    private static final String SPREADSHEET_NS =
            "http://schemas.openxmlformats.org/spreadsheetml/2006/main";
    private static final String RELATIONSHIP_NS =
            "http://schemas.openxmlformats.org/package/2006/relationships";
    private static final String OFFICE_RELATIONSHIP_NS =
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships";

    private OpenXmlWorkbookWriter() {
    }

    public static byte[] buildWorkbook(String sheetName, List<String> headers,
            List<Object[]> rows) {
        return buildWorkbook(sheetName, headers, rows, null, null, 100);
    }

    /**
     * ヘッダーより前にタイトル等を置く帳票用レイアウト。
     * leadingRows の要素数がそのまま上部行数になる。
     */
    public static byte[] buildWorkbook(String sheetName, List<String> headers,
            List<Object[]> rows, List<Object[]> leadingRows, List<String> mergedRanges,
            int printScale) {
        if (headers == null || headers.isEmpty()) {
            throw new IllegalArgumentException("ヘッダーは1列以上必要です。");
        }
        if (rows == null) {
            throw new IllegalArgumentException("明細リストはnullにできません。");
        }

        ByteArrayOutputStream output = new ByteArrayOutputStream();
        ZipOutputStream zip = new ZipOutputStream(output);
        try {
            write(zip, "[Content_Types].xml", contentTypes());
            write(zip, "_rels/.rels", rootRelationships());
            write(zip, "xl/workbook.xml", workbookXml(sanitizeSheetName(sheetName)));
            write(zip, "xl/_rels/workbook.xml.rels", workbookRelationships());
            write(zip, "xl/styles.xml", stylesXml());
            write(zip, "xl/worksheets/sheet1.xml",
                    sheetXml(headers, rows, leadingRows, mergedRanges, printScale));
            zip.finish();
            return output.toByteArray();
        } catch (IOException e) {
            throw new IllegalStateException("Excelファイルの生成に失敗しました。", e);
        } finally {
            try {
                zip.close();
            } catch (IOException e) {
                // ByteArrayOutputStream の close 失敗は発生しない。
            }
        }
    }

    private static String contentTypes() {
        return "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
                + "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
                + "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
                + "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
                + "<Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>"
                + "<Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>"
                + "<Override PartName=\"/xl/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml\"/>"
                + "</Types>";
    }

    private static String rootRelationships() {
        return "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
                + "<Relationships xmlns=\"" + RELATIONSHIP_NS + "\">"
                + "<Relationship Id=\"rId1\" Type=\"" + OFFICE_RELATIONSHIP_NS
                + "/officeDocument\" Target=\"xl/workbook.xml\"/>"
                + "</Relationships>";
    }

    private static String workbookXml(String sheetName) {
        return "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
                + "<workbook xmlns=\"" + SPREADSHEET_NS + "\" xmlns:r=\""
                + OFFICE_RELATIONSHIP_NS + "\"><sheets><sheet name=\""
                + xml(sheetName) + "\" sheetId=\"1\" r:id=\"rId1\"/></sheets></workbook>";
    }

    private static String workbookRelationships() {
        return "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
                + "<Relationships xmlns=\"" + RELATIONSHIP_NS + "\">"
                + "<Relationship Id=\"rId1\" Type=\"" + OFFICE_RELATIONSHIP_NS
                + "/worksheet\" Target=\"worksheets/sheet1.xml\"/>"
                + "<Relationship Id=\"rId2\" Type=\"" + OFFICE_RELATIONSHIP_NS
                + "/styles\" Target=\"styles.xml\"/>"
                + "</Relationships>";
    }

    private static String stylesXml() {
        return "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
                + "<styleSheet xmlns=\"" + SPREADSHEET_NS + "\">"
                + "<fonts count=\"4\"><font><sz val=\"10\"/><name val=\"メイリオ\"/></font>"
                + "<font><b/><sz val=\"10\"/><name val=\"メイリオ\"/></font>"
                + "<font><b/><sz val=\"22\"/><name val=\"メイリオ\"/></font>"
                + "<font><sz val=\"16\"/><name val=\"メイリオ\"/></font></fonts>"
                + "<fills count=\"3\"><fill><patternFill patternType=\"none\"/></fill>"
                + "<fill><patternFill patternType=\"gray125\"/></fill>"
                + "<fill><patternFill patternType=\"solid\"><fgColor rgb=\"FFFFFF96\"/>"
                + "<bgColor indexed=\"64\"/></patternFill></fill></fills>"
                + "<borders count=\"2\"><border><left/><right/><top/><bottom/><diagonal/></border>"
                + "<border><left style=\"thin\"/><right style=\"thin\"/><top style=\"thin\"/>"
                + "<bottom style=\"thin\"/><diagonal/></border></borders>"
                + "<cellStyleXfs count=\"1\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\"/></cellStyleXfs>"
                + "<cellXfs count=\"5\">"
                + "<xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"1\" xfId=\"0\" applyBorder=\"1\"/>"
                + "<xf numFmtId=\"0\" fontId=\"1\" fillId=\"2\" borderId=\"1\" xfId=\"0\" applyFont=\"1\" applyFill=\"1\" applyBorder=\"1\" applyAlignment=\"1\"><alignment horizontal=\"center\" vertical=\"center\" wrapText=\"1\"/></xf>"
                + "<xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"1\" xfId=\"0\" applyBorder=\"1\" applyAlignment=\"1\"><alignment horizontal=\"right\" vertical=\"top\"/></xf>"
                + "<xf numFmtId=\"0\" fontId=\"2\" fillId=\"0\" borderId=\"0\" xfId=\"0\" applyFont=\"1\" applyAlignment=\"1\"><alignment horizontal=\"center\" vertical=\"center\"/></xf>"
                + "<xf numFmtId=\"0\" fontId=\"3\" fillId=\"0\" borderId=\"0\" xfId=\"0\" applyFont=\"1\" applyAlignment=\"1\"><alignment horizontal=\"center\" vertical=\"center\"/></xf>"
                + "</cellXfs><cellStyles count=\"1\"><cellStyle name=\"Normal\" xfId=\"0\" builtinId=\"0\"/></cellStyles>"
                + "</styleSheet>";
    }

    private static String sheetXml(List<String> headers, List<Object[]> rows,
            List<Object[]> leadingRows, List<String> mergedRanges, int printScale) {
        StringBuilder xml = new StringBuilder(4096 + rows.size() * headers.size() * 40);
        int leadingCount = leadingRows == null ? 0 : leadingRows.size();
        int headerRow = leadingCount + 1;
        int lastRow = rows.size() + headerRow;
        String lastColumn = columnName(headers.size());
        xml.append("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>");
        xml.append("<worksheet xmlns=\"").append(SPREADSHEET_NS).append("\">");
        xml.append("<dimension ref=\"A1:").append(lastColumn).append(lastRow).append("\"/>");
        xml.append("<sheetViews><sheetView workbookViewId=\"0\"><pane ySplit=\"")
                .append(headerRow).append("\" topLeftCell=\"A").append(headerRow + 1)
                .append("\" activePane=\"bottomLeft\" state=\"frozen\"/></sheetView></sheetViews>");
        appendColumns(xml, headers, rows);
        xml.append("<sheetData>");
        if (leadingRows != null) {
            for (int rowIndex = 0; rowIndex < leadingRows.size(); rowIndex++) {
                int excelRow = rowIndex + 1;
                Object[] row = leadingRows.get(rowIndex);
                xml.append("<row r=\"").append(excelRow).append("\"");
                if (excelRow == 1) {
                    xml.append(" ht=\"28\" customHeight=\"1\"");
                }
                xml.append('>');
                if (row != null) {
                    for (int column = 0; column < Math.min(headers.size(), row.length); column++) {
                        Object value = row[column];
                        if (value != null) {
                            appendTextCell(xml, columnName(column + 1) + excelRow,
                                    String.valueOf(value), excelRow == 1 ? 3 : 4);
                        }
                    }
                }
                xml.append("</row>");
            }
        }
        xml.append("<row r=\"").append(headerRow)
                .append("\" ht=\"45\" customHeight=\"1\">");
        for (int column = 0; column < headers.size(); column++) {
            appendTextCell(xml, columnName(column + 1) + headerRow, headers.get(column), 1);
        }
        xml.append("</row>");

        for (int rowIndex = 0; rowIndex < rows.size(); rowIndex++) {
            int excelRow = rowIndex + headerRow + 1;
            Object[] row = rows.get(rowIndex);
            xml.append("<row r=\"").append(excelRow).append("\">");
            for (int column = 0; column < headers.size(); column++) {
                Object value = row != null && column < row.length ? row[column] : null;
                String reference = columnName(column + 1) + excelRow;
                if (value instanceof Number) {
                    appendNumberCell(xml, reference, (Number) value);
                } else {
                    appendTextCell(xml, reference, value == null ? "" : String.valueOf(value), 0);
                }
            }
            xml.append("</row>");
        }

        xml.append("</sheetData><autoFilter ref=\"A").append(headerRow).append(':')
                .append(lastColumn).append(lastRow).append("\"/>");
        if (mergedRanges != null && !mergedRanges.isEmpty()) {
            xml.append("<mergeCells count=\"").append(mergedRanges.size()).append("\">");
            for (int i = 0; i < mergedRanges.size(); i++) {
                xml.append("<mergeCell ref=\"").append(xml(mergedRanges.get(i))).append("\"/>");
            }
            xml.append("</mergeCells>");
        }
        xml.append("<printOptions horizontalCentered=\"1\"/>")
                .append("<pageMargins left=\"0\" right=\"0\" top=\"0.3937\" bottom=\"0.3937\" header=\"0.1181\" footer=\"0.1181\"/>")
                .append("<pageSetup paperSize=\"9\" orientation=\"portrait\" scale=\"")
                .append(Math.max(10, Math.min(400, printScale))).append("\"/>")
                .append("</worksheet>");
        return xml.toString();
    }

    private static void appendColumns(StringBuilder xml, List<String> headers, List<Object[]> rows) {
        xml.append("<cols>");
        for (int column = 0; column < headers.size(); column++) {
            int width = displayLength(headers.get(column)) + 2;
            int inspectCount = Math.min(rows.size(), 100);
            for (int row = 0; row < inspectCount; row++) {
                Object[] values = rows.get(row);
                Object value = values != null && column < values.length ? values[column] : null;
                width = Math.max(width, displayLength(value == null ? "" : String.valueOf(value)) + 2);
            }
            width = Math.max(5, Math.min(40, width));
            xml.append("<col min=\"").append(column + 1).append("\" max=\"")
                    .append(column + 1).append("\" width=\"").append(width)
                    .append("\" customWidth=\"1\"/>");
        }
        xml.append("</cols>");
    }

    private static void appendTextCell(StringBuilder xml, String reference, String value, int style) {
        String clean = validXmlText(value);
        xml.append("<c r=\"").append(reference).append("\" s=\"").append(style)
                .append("\" t=\"inlineStr\"><is><t");
        if (clean.length() > 0
                && (Character.isWhitespace(clean.charAt(0))
                        || Character.isWhitespace(clean.charAt(clean.length() - 1)))) {
            xml.append(" xml:space=\"preserve\"");
        }
        xml.append(">").append(xml(clean)).append("</t></is></c>");
    }

    private static void appendNumberCell(StringBuilder xml, String reference, Number value) {
        xml.append("<c r=\"").append(reference).append("\" s=\"2\"><v>")
                .append(String.format(Locale.ROOT, "%s", value)).append("</v></c>");
    }

    private static int displayLength(String value) {
        int length = 0;
        for (int offset = 0; offset < value.length();) {
            int codePoint = value.codePointAt(offset);
            length += codePoint <= 0x7f ? 1 : 2;
            offset += Character.charCount(codePoint);
        }
        return length;
    }

    private static String columnName(int column) {
        StringBuilder name = new StringBuilder();
        int value = column;
        while (value > 0) {
            value--;
            name.insert(0, (char) ('A' + value % 26));
            value /= 26;
        }
        return name.toString();
    }

    private static String sanitizeSheetName(String value) {
        String name = value == null || value.trim().length() == 0 ? "Sheet1" : value.trim();
        name = name.replaceAll("[\\\\/\\?\\*\\[\\]:]", "_");
        if (name.length() > 31) {
            name = name.substring(0, 31);
        }
        return name;
    }

    private static String validXmlText(String value) {
        StringBuilder result = new StringBuilder(value == null ? 0 : value.length());
        String source = value == null ? "" : value;
        for (int offset = 0; offset < source.length();) {
            int codePoint = source.codePointAt(offset);
            if (codePoint == 0x9 || codePoint == 0xA || codePoint == 0xD
                    || (codePoint >= 0x20 && codePoint <= 0xD7FF)
                    || (codePoint >= 0xE000 && codePoint <= 0xFFFD)
                    || (codePoint >= 0x10000 && codePoint <= 0x10FFFF)) {
                result.appendCodePoint(codePoint);
            }
            offset += Character.charCount(codePoint);
        }
        return result.toString();
    }

    private static String xml(String value) {
        return value.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace("\"", "&quot;")
                .replace("'", "&apos;");
    }

    private static void write(ZipOutputStream zip, String path, String content) throws IOException {
        ZipEntry entry = new ZipEntry(path);
        entry.setTime(0L);
        zip.putNextEntry(entry);
        zip.write(content.getBytes(UTF8));
        zip.closeEntry();
    }
}
