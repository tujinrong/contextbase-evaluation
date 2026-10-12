package nenkin.service;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import nenkin.model.PensionReservation;
import nenkin.util.DateUtil;
import nenkin.util.OpenXmlWorkbookWriter;

/** Access 年金データ Excel 出力の Open XML 置換。 */
public final class PensionExcelExportService {
    public static final String CONTENT_TYPE =
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

    private static final PensionExcelExportService INSTANCE =
            new PensionExcelExportService(PensionRepository.getInstance());

    private final PensionRepository repository;

    public PensionExcelExportService() {
        this(PensionRepository.getInstance());
    }

    public PensionExcelExportService(PensionRepository repository) {
        if (repository == null) {
            throw new IllegalArgumentException("repositoryはnullにできません。");
        }
        this.repository = repository;
    }

    public static PensionExcelExportService getInstance() {
        return INSTANCE;
    }

    public PensionExcelExportResult buildByBranch(int branchNo) {
        List<PensionReservation> reservations = repository.listByBranch(branchNo);
        if (reservations.isEmpty()) {
            return new PensionExcelExportResult("", new byte[0], 0);
        }

        List<String> headers = Arrays.asList(
                "顧客番号", "担\n当", "顧客氏名", "ふりがな", "性\n別", "住所",
                "電話番号", "生年月日", "年金種類", "裁定\n請求", "受給\n有無",
                "請求予定日", "予定\n年齢", "配偶者名", "配偶者\n生年月日",
                "予約徴求日", "備考", "６ヶ月先\n確認");
        List<Object[]> rows = new ArrayList<Object[]>();
        for (int i = 0; i < reservations.size(); i++) {
            PensionReservation row = reservations.get(i);
            rows.add(new Object[] {
                row.getCustomerNo(), row.getStaffCode(), row.getCustomerName(), row.getKanaName(),
                row.getGender(), row.getAddress(), row.getPhoneNumber(), row.getBirthDate(),
                row.getPensionType(), row.getClaimStatus(), row.getHasBenefit(),
                row.getClaimScheduledDate(), row.getPlannedAge(), row.getSpouseName(),
                row.getSpouseBirthDate(), row.getReservationRequestDate(), row.getNotes(),
                row.isSixMonthCheck() ? "確" : ""
            });
        }

        String compactDate = DateUtil.todayIso().replace("-", "");
        String fileName = "年金データ_" + threeDigits(branchNo) + "_" + compactDate + ".xlsx";
        byte[] content = OpenXmlWorkbookWriter.buildWorkbook("年金ﾃﾞｰﾀ", headers, rows);
        return new PensionExcelExportResult(fileName, content, rows.size());
    }

    private static String threeDigits(int value) {
        String text = Integer.toString(value);
        while (text.length() < 3) {
            text = "0" + text;
        }
        return text;
    }
}
