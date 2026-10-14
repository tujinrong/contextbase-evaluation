package nenkin.service;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

import nenkin.model.AuditType;
import nenkin.model.PensionAuditRecord;
import nenkin.model.PensionReservation;
import nenkin.util.DateUtil;
import nenkin.util.OpenXmlWorkbookWriter;

/** Access form処理データの日次・月次 Excel 出力。 */
public final class PensionBatchExportService {
    public static final String EXCEL_CONTENT_TYPE =
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
    public static final String ZIP_CONTENT_TYPE = "application/zip";

    private static final Charset UTF8 = Charset.forName("UTF-8");
    private static final List<String> NEW_HEADERS = Arrays.asList(
            "No", "予約徴求日", "カナ氏名", "漢字氏名", "性\n別", "住所", "生年月日",
            "電話番号", "年金\n種類", "予定\n年齢", "請求予定日", "備考", "配偶者名",
            "配偶者\n生年月日", "店番", "顧客番号", "担\n当");
    private static final List<String> CHANGE_DELETE_HEADERS = Arrays.asList(
            "No", "店番", "顧客番号", "漢字氏名", "カナ氏名", "性\n別", "住所",
            "電話番号", "生年月日", "年金\n種類", "裁定\n請求", "請求予定日",
            "予定\n年齢", "配偶者名", "配偶者\n生年月日", "受給\n有無",
            "予約徴求日", "担\n当", "備考", "６ヶ月\n先確認");

    private static final PensionBatchExportService INSTANCE =
            new PensionBatchExportService(PensionRepository.getInstance());

    private final PensionRepository repository;

    public PensionBatchExportService() {
        this(PensionRepository.getInstance());
    }

    public PensionBatchExportService(PensionRepository repository) {
        if (repository == null) {
            throw new IllegalArgumentException("repositoryはnullにできません。");
        }
        this.repository = repository;
    }

    public static PensionBatchExportService getInstance() {
        return INSTANCE;
    }

    public PensionBatchExportResult build(PensionBatchExportRequest request) {
        if (request == null) {
            throw new IllegalArgumentException("出力条件がありません。");
        }
        if (!request.isIncludeNew() && !request.isIncludeChanged()
                && !request.isIncludeDeleted()) {
            throw new IllegalArgumentException(
                    "新規分、変更分、削除分のいずれかを選択してください。");
        }

        DateRange range = resolveRange(request);
        Integer updatedBy = parseStaffNo(request.getStaffNo());
        if (request.getDeleteCutoffDate().trim().length() > 0) {
            repository.purgeDeletedAuditsThrough(request.getDeleteCutoffDate());
        }

        List<ExportSpec> specs = selectedSpecs(request, updatedBy != null);
        List<GeneratedFile> generated = new ArrayList<GeneratedFile>();
        List<String> messages = new ArrayList<String>();
        for (int i = 0; i < specs.size(); i++) {
            ExportSpec spec = specs.get(i);
            List<PensionAuditRecord> audits = repository.findAuditRecords(spec.type,
                    range.from, range.to, updatedBy);
            if (audits.isEmpty()) {
                messages.add(emptyMessage(spec.type, request.getRunMode(), updatedBy != null));
                continue;
            }
            sortAudits(audits);
            List<String> headers = spec.type == AuditType.NEW
                    ? NEW_HEADERS : CHANGE_DELETE_HEADERS;
            List<Object[]> rows = toRows(audits, spec.type);
            WorkbookLayout layout = buildLayout(spec, request, range, headers.size());
            byte[] content = OpenXmlWorkbookWriter.buildWorkbook(spec.sheetName, headers, rows,
                    layout.leadingRows, layout.mergedRanges, layout.printScale);
            generated.add(new GeneratedFile(spec, rows.size(), content));
        }

        List<PensionBatchExportFileResult> files = toFileResults(generated);
        PensionBatchExportResult result;
        if (generated.isEmpty()) {
            result = new PensionBatchExportResult("", EXCEL_CONTENT_TYPE, new byte[0],
                    files, messages);
        } else if (generated.size() == 1) {
            GeneratedFile file = generated.get(0);
            result = new PensionBatchExportResult(file.spec.fileName, EXCEL_CONTENT_TYPE,
                    file.content, files, messages);
        } else {
            String zipName = request.getRunMode() == PensionBatchRunMode.DAILY
                    ? "年金予約データ明細リスト（日次）.zip"
                    : "年金予約データ明細リスト（月次）.zip";
            result = new PensionBatchExportResult(zipName, ZIP_CONTENT_TYPE,
                    buildZip(generated, messages), files, messages);
        }

        return result;
    }

    private static DateRange resolveRange(PensionBatchExportRequest request) {
        if (request.getRunMode() == null) {
            throw new IllegalArgumentException("日次または月次を指定してください。");
        }
        if (request.getRunMode() == PensionBatchRunMode.DAILY) {
            String day = requiredDate(request.getDailyDate(), "年月日を入力してください。");
            return new DateRange(day, day);
        }
        String from = requiredDate(request.getMonthStart(), "月初日を入力してください。");
        String to = requiredDate(request.getMonthEnd(), "月末日を入力してください。");
        if (from.compareTo(to) > 0) {
            throw new IllegalArgumentException("月初日は月末日以前で指定してください。");
        }
        return new DateRange(from, to);
    }

    private static String requiredDate(String value, String message) {
        if (value == null || value.trim().length() == 0) {
            throw new IllegalArgumentException(message);
        }
        return DateUtil.toIsoDate(value);
    }

    private static Integer parseStaffNo(String value) {
        String text = value == null ? "" : value.trim();
        if (text.length() == 0 || "ALL".equalsIgnoreCase(text)) {
            return null;
        }
        try {
            return Integer.valueOf(text);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("職員番号は数値で入力してください。", e);
        }
    }

    private static List<ExportSpec> selectedSpecs(PensionBatchExportRequest request,
            boolean staffSpecified) {
        List<ExportSpec> specs = new ArrayList<ExportSpec>();
        if (request.isIncludeNew()) {
            specs.add(buildSpec(AuditType.NEW, request.getRunMode(), staffSpecified));
        }
        if (request.isIncludeChanged()) {
            specs.add(buildSpec(AuditType.CHANGED, request.getRunMode(), staffSpecified));
        }
        if (request.isIncludeDeleted()) {
            specs.add(buildSpec(AuditType.DELETED, request.getRunMode(), staffSpecified));
        }
        return specs;
    }

    private static ExportSpec buildSpec(AuditType type, PensionBatchRunMode mode,
            boolean staffSpecified) {
        int base;
        if (mode == PensionBatchRunMode.DAILY) {
            base = staffSpecified ? 10 : 40;
        } else {
            base = staffSpecified ? 70 : 100;
        }
        int queryNumber = base + (type == AuditType.NEW ? 0
                : type == AuditType.CHANGED ? 10 : 20);
        String number = queryNumber < 100 ? "0" + queryNumber : Integer.toString(queryNumber);
        String category = type.getDisplayName();
        String queryName = "Q" + number + "_Excel出力_年金予約_" + category
                + "_データ明細リスト";
        String scope = staffSpecified ? "担当者別" : "全担当者";
        String period = mode == PensionBatchRunMode.DAILY ? "日次" : "月次";
        String fileName = "年金予約【" + category + "】データ明細リスト（"
                + scope + period + "）.xlsx";
        return new ExportSpec(type, queryName, fileName, category + "分データ",
                "年金予約【" + category + "】データ明細リスト");
    }

    private static String emptyMessage(AuditType type, PensionBatchRunMode mode,
            boolean staffSpecified) {
        String period = mode == PensionBatchRunMode.DAILY ? "日次" : "月次";
        if (staffSpecified) {
            return "入力した担当者の【" + type.getDisplayName() + "分（" + period
                    + "）】の該当明細はありませんでした";
        }
        String dateText = mode == PensionBatchRunMode.DAILY ? "入力年月日の" : "入力年月の";
        return dateText + "【" + type.getDisplayName() + "分（" + period
                + "）】の該当明細はありませんでした";
    }

    private static void sortAudits(List<PensionAuditRecord> audits) {
        Collections.sort(audits, new Comparator<PensionAuditRecord>() {
            public int compare(PensionAuditRecord left, PensionAuditRecord right) {
                PensionReservation a = left.getReservation();
                PensionReservation b = right.getReservation();
                int branch = compareInteger(a.getBranchNo(), b.getBranchNo());
                if (branch != 0) {
                    return branch;
                }
                int customer = compareInteger(a.getCustomerNo(), b.getCustomerNo());
                return customer != 0 ? customer : Long.valueOf(left.getAuditId())
                        .compareTo(Long.valueOf(right.getAuditId()));
            }
        });
    }

    private static int compareInteger(Integer left, Integer right) {
        if (left == null) {
            return right == null ? 0 : -1;
        }
        return right == null ? 1 : left.compareTo(right);
    }

    private static List<Object[]> toRows(List<PensionAuditRecord> audits, AuditType type) {
        List<Object[]> rows = new ArrayList<Object[]>();
        for (int i = 0; i < audits.size(); i++) {
            PensionReservation row = audits.get(i).getReservation();
            if (type == AuditType.NEW) {
                rows.add(new Object[] {
                    Integer.valueOf(i + 1), wareki(row.getReservationRequestDate()),
                    row.getKanaName(), row.getCustomerName(), row.getGender(), row.getAddress(),
                    wareki(row.getBirthDate()), row.getPhoneNumber(), row.getPensionType(),
                    row.getPlannedAge(), wareki(row.getClaimScheduledDate()), row.getNotes(),
                    row.getSpouseName(), wareki(row.getSpouseBirthDate()), row.getBranchNo(),
                    row.getCustomerNo(), staffCode(row.getStaffCode())
                });
            } else {
                rows.add(new Object[] {
                    Integer.valueOf(i + 1), row.getBranchNo(), row.getCustomerNo(),
                    row.getCustomerName(), row.getKanaName(), row.getGender(), row.getAddress(),
                    row.getPhoneNumber(), wareki(row.getBirthDate()), row.getPensionType(),
                    row.getClaimStatus(), wareki(row.getClaimScheduledDate()), row.getPlannedAge(),
                    row.getSpouseName(), wareki(row.getSpouseBirthDate()), row.getHasBenefit(),
                    wareki(row.getReservationRequestDate()), staffCode(row.getStaffCode()),
                    row.getNotes(), row.isSixMonthCheck() ? "確" : ""
                });
            }
        }
        return rows;
    }

    private static WorkbookLayout buildLayout(ExportSpec spec,
            PensionBatchExportRequest request, DateRange range, int columnCount) {
        List<Object[]> leadingRows = new ArrayList<Object[]>();
        for (int i = 0; i < 7; i++) {
            leadingRows.add(new Object[columnCount]);
        }
        List<String> mergedRanges = new ArrayList<String>();
        String period = request.getRunMode() == PensionBatchRunMode.DAILY
                ? wareki(range.from) : wareki(range.from) + "～" + wareki(range.to);
        String staff = request.getStaffNo() == null || request.getStaffNo().trim().length() == 0
                ? "ALL" : request.getStaffNo().trim();

        Object[] titleRow = leadingRows.get(0);
        Object[] metaRow = leadingRows.get(4);
        if (spec.type == AuditType.NEW) {
            titleRow[3] = spec.title;
            metaRow[3] = "処理日";
            metaRow[5] = period;
            metaRow[9] = "職員番号";
            metaRow[11] = staff;
            mergedRanges.add("D1:M3");
            mergedRanges.add("D5:E6");
            mergedRanges.add(request.getRunMode() == PensionBatchRunMode.DAILY
                    ? "F5:H6" : "F5:I6");
            mergedRanges.add("J5:K6");
            mergedRanges.add("L5:M6");
        } else {
            titleRow[4] = spec.title;
            metaRow[4] = "処理日";
            metaRow[6] = period;
            metaRow[11] = "職員番号";
            metaRow[13] = staff;
            mergedRanges.add("E1:P3");
            mergedRanges.add("E5:F6");
            mergedRanges.add(request.getRunMode() == PensionBatchRunMode.DAILY
                    ? "G5:H6" : "G5:I6");
            mergedRanges.add("L5:M6");
            mergedRanges.add("N5:P6");
        }
        return new WorkbookLayout(leadingRows, mergedRanges,
                spec.type == AuditType.NEW ? 70 : 60);
    }

    private static String wareki(String value) {
        return value == null || value.trim().length() == 0 ? "" : DateUtil.toAccessWareki(value);
    }

    private static String staffCode(Integer value) {
        return value == null ? "" : String.format(Locale.ROOT, "%02d", value);
    }

    private static List<PensionBatchExportFileResult> toFileResults(
            List<GeneratedFile> generated) {
        List<PensionBatchExportFileResult> results =
                new ArrayList<PensionBatchExportFileResult>();
        for (int i = 0; i < generated.size(); i++) {
            GeneratedFile file = generated.get(i);
            results.add(new PensionBatchExportFileResult(file.spec.queryName,
                    file.spec.fileName, file.spec.type.getDisplayName(), file.rowCount));
        }
        return results;
    }

    private static byte[] buildZip(List<GeneratedFile> files, List<String> messages) {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        ZipOutputStream zip = new ZipOutputStream(output);
        try {
            for (int i = 0; i < files.size(); i++) {
                GeneratedFile file = files.get(i);
                writeZipEntry(zip, file.spec.fileName, file.content);
            }
            if (!messages.isEmpty()) {
                StringBuilder text = new StringBuilder();
                for (int i = 0; i < messages.size(); i++) {
                    text.append(messages.get(i)).append("\r\n");
                }
                writeZipEntry(zip, "出力結果.txt", text.toString().getBytes(UTF8));
            }
            zip.finish();
            return output.toByteArray();
        } catch (IOException e) {
            throw new IllegalStateException("ZIPファイルの生成に失敗しました。", e);
        } finally {
            try {
                zip.close();
            } catch (IOException e) {
                // ByteArrayOutputStream では close 失敗しない。
            }
        }
    }

    private static void writeZipEntry(ZipOutputStream zip, String name, byte[] content)
            throws IOException {
        ZipEntry entry = new ZipEntry(name);
        entry.setTime(0L);
        zip.putNextEntry(entry);
        zip.write(content);
        zip.closeEntry();
    }

    private static final class DateRange {
        private final String from;
        private final String to;

        private DateRange(String from, String to) {
            this.from = from;
            this.to = to;
        }
    }

    private static final class ExportSpec {
        private final AuditType type;
        private final String queryName;
        private final String fileName;
        private final String sheetName;
        private final String title;

        private ExportSpec(AuditType type, String queryName, String fileName,
                String sheetName, String title) {
            this.type = type;
            this.queryName = queryName;
            this.fileName = fileName;
            this.sheetName = sheetName;
            this.title = title;
        }
    }

    private static final class WorkbookLayout {
        private final List<Object[]> leadingRows;
        private final List<String> mergedRanges;
        private final int printScale;

        private WorkbookLayout(List<Object[]> leadingRows, List<String> mergedRanges,
                int printScale) {
            this.leadingRows = leadingRows;
            this.mergedRanges = mergedRanges;
            this.printScale = printScale;
        }
    }

    private static final class GeneratedFile {
        private final ExportSpec spec;
        private final int rowCount;
        private final byte[] content;

        private GeneratedFile(ExportSpec spec, int rowCount, byte[] content) {
            this.spec = spec;
            this.rowCount = rowCount;
            this.content = content;
        }
    }
}
