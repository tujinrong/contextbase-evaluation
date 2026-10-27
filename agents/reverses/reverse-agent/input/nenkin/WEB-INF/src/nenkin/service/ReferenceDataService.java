package nenkin.service;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import nenkin.model.BranchLookupItem;
import nenkin.model.CodeLookupItem;
import nenkin.model.CustomerLookupItem;
import nenkin.model.StaffContext;
import nenkin.model.StaffLookupItem;
import nenkin.util.DateUtil;

/** Access と同じ店舗・職員・顧客・コード表を参照する JDBC サービス。 */
public final class ReferenceDataService {
    private static final String BRANCH_TABLE = "店名テーブル";
    private static final String STAFF_TABLE = "DB2.Ｕ職員名簿表";
    private static final String CUSTOMER_TABLE = "N2_SIGHT.Ｂ顧客基本表";
    private static final String GENDER_TABLE = "性別テーブル";
    private static final String CLAIM_TABLE = "裁定請求テーブル";
    private static final String BENEFIT_TABLE = "受給有無テーブル";
    private static final String PENSION_TYPE_TABLE = "年金種類テーブル";
    private static final String LIKE_ESCAPE = " ESCAPE '\\'";

    private static final ReferenceDataService INSTANCE = new ReferenceDataService();

    private ReferenceDataService() {
    }

    public static ReferenceDataService getInstance() {
        return INSTANCE;
    }

    public List<BranchLookupItem> searchBranches(String keyword) {
        String value = normalize(keyword);
        String sql = "SELECT 店舗ｺｰﾄﾞ AS BRANCH_NO, 店名 AS BRANCH_NAME FROM "
                + BRANCH_TABLE
                + (value.length() == 0 ? "" : " WHERE CAST(店舗ｺｰﾄﾞ AS VARCHAR(20)) LIKE ?"
                        + LIKE_ESCAPE + " OR UPPER(店名) LIKE UPPER(?)" + LIKE_ESCAPE)
                + " ORDER BY 店舗ｺｰﾄﾞ";
        List<BranchLookupItem> rows = new ArrayList<BranchLookupItem>();
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            connection = NenkinDataSource.openConnection();
            statement = connection.prepareStatement(sql);
            if (value.length() > 0) {
                String pattern = containsPattern(value);
                statement.setString(1, pattern);
                statement.setString(2, pattern);
            }
            results = statement.executeQuery();
            while (results.next()) {
                rows.add(new BranchLookupItem(results.getInt("BRANCH_NO"),
                        results.getString("BRANCH_NAME")));
            }
            return rows;
        } catch (SQLException e) {
            throw failure("店舗の検索", e);
        } finally {
            close(results);
            close(statement);
            close(connection);
        }
    }

    public List<CustomerLookupItem> searchCustomers(Integer branchNo, String nameKeyword,
            String phoneKeyword) {
        String name = normalize(nameKeyword);
        String phone = canonicalPhone(phoneKeyword);
        StringBuilder sql = new StringBuilder("SELECT C.店舗コード AS BRANCH_NO, ")
                .append("C.顧客番号 AS CUSTOMER_NO, C.カナ氏名 AS KANA_NAME, ")
                .append("C.漢字氏名 AS CUSTOMER_NAME, C.電話番号 AS PHONE_NUMBER, ")
                .append("C.生年月日 AS BIRTH_DATE, C.担当者コード AS STAFF_CODE FROM ")
                .append(CUSTOMER_TABLE).append(" C WHERE 1 = 1");
        if (branchNo != null) {
            sql.append(" AND C.店舗コード = ?");
        }
        if (name.length() > 0) {
            sql.append(" AND (UPPER(C.漢字氏名) LIKE UPPER(?)").append(LIKE_ESCAPE)
                    .append(" OR UPPER(C.カナ氏名) LIKE UPPER(?)").append(LIKE_ESCAPE)
                    .append(')');
        }
        if (phone.length() > 0) {
            sql.append(" AND TO_CHAR(C.電話番号) LIKE ?").append(LIKE_ESCAPE);
        }
        sql.append(" ORDER BY C.店舗コード, C.顧客番号, C.カナ氏名");

        List<CustomerLookupItem> rows = new ArrayList<CustomerLookupItem>();
        Map<Integer, String> branchNames = loadBranchNames();
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            connection = NenkinDataSource.openCustomerConnection();
            statement = connection.prepareStatement(sql.toString());
            int index = 1;
            if (branchNo != null) {
                statement.setInt(index++, branchNo.intValue());
            }
            if (name.length() > 0) {
                String pattern = containsPattern(name);
                statement.setString(index++, pattern);
                statement.setString(index++, pattern);
            }
            if (phone.length() > 0) {
                statement.setString(index++, containsPattern(phone));
            }
            results = statement.executeQuery();
            while (results.next()) {
                int rowBranch = results.getInt("BRANCH_NO");
                rows.add(new CustomerLookupItem(rowBranch, results.getInt("CUSTOMER_NO"),
                        results.getString("KANA_NAME"), results.getString("CUSTOMER_NAME"),
                        displayPhone(results.getString("PHONE_NUMBER")),
                        compactDate(results.getString("BIRTH_DATE")),
                        text(branchNames.get(Integer.valueOf(rowBranch))),
                        nullableInt(results, "STAFF_CODE")));
            }
            return rows;
        } catch (SQLException e) {
            throw failure("顧客の検索", e);
        } finally {
            close(results);
            close(statement);
            close(connection);
        }
    }

    public List<StaffLookupItem> searchStaff(Integer branchNo, String kanaKeyword) {
        String keyword = normalize(kanaKeyword);
        StringBuilder sql = new StringBuilder("SELECT S.職員番号 AS STAFF_NO, ")
                .append("S.漢字氏名 AS STAFF_NAME, S.カナ氏名 AS STAFF_KANA_NAME, ")
                .append("S.所属店番 AS BRANCH_NO, S.役職コード AS ROLE_CODE FROM ")
                .append(STAFF_TABLE).append(" S WHERE 1 = 1");
        if (branchNo != null) {
            sql.append(" AND S.所属店番 = ?");
        }
        if (keyword.length() > 0) {
            sql.append(" AND (UPPER(S.カナ氏名) LIKE UPPER(?)")
                    .append(LIKE_ESCAPE).append(" OR UPPER(S.漢字氏名) LIKE UPPER(?)")
                    .append(LIKE_ESCAPE).append(')');
        }
        sql.append(" ORDER BY S.職員番号");

        List<StaffLookupItem> rows = new ArrayList<StaffLookupItem>();
        Map<Integer, String> branchNames = loadBranchNames();
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            connection = NenkinDataSource.openStaffConnection();
            statement = connection.prepareStatement(sql.toString());
            int index = 1;
            if (branchNo != null) {
                statement.setInt(index++, branchNo.intValue());
            }
            if (keyword.length() > 0) {
                String pattern = containsPattern(keyword);
                statement.setString(index++, pattern);
                statement.setString(index++, pattern);
            }
            results = statement.executeQuery();
            while (results.next()) {
                rows.add(readStaff(results, branchNames));
            }
            return rows;
        } catch (SQLException e) {
            throw failure("職員の検索", e);
        } finally {
            close(results);
            close(statement);
            close(connection);
        }
    }

    public BranchLookupItem getBranch(int branchNo) {
        String sql = "SELECT 店舗ｺｰﾄﾞ AS BRANCH_NO, 店名 AS BRANCH_NAME FROM "
                + BRANCH_TABLE + " WHERE 店舗ｺｰﾄﾞ = ?";
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            connection = NenkinDataSource.openConnection();
            statement = connection.prepareStatement(sql);
            statement.setInt(1, branchNo);
            results = statement.executeQuery();
            return results.next() ? new BranchLookupItem(results.getInt("BRANCH_NO"),
                    results.getString("BRANCH_NAME")) : null;
        } catch (SQLException e) {
            throw failure("店舗の取得", e);
        } finally {
            close(results);
            close(statement);
            close(connection);
        }
    }

    public StaffLookupItem getStaff(int staffCode) {
        String sql = "SELECT S.職員番号 AS STAFF_NO, S.漢字氏名 AS STAFF_NAME, "
                + "S.カナ氏名 AS STAFF_KANA_NAME, S.所属店番 AS BRANCH_NO, "
                + "S.役職コード AS ROLE_CODE FROM " + STAFF_TABLE
                + " S WHERE S.職員番号 = ?";
        Map<Integer, String> branchNames = loadBranchNames();
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            connection = NenkinDataSource.openStaffConnection();
            statement = connection.prepareStatement(sql);
            statement.setInt(1, staffCode);
            results = statement.executeQuery();
            return results.next() ? readStaff(results, branchNames) : null;
        } catch (SQLException e) {
            throw failure("職員の取得", e);
        } finally {
            close(results);
            close(statement);
            close(connection);
        }
    }

    public StaffContext verifyStaff(int staffNo) {
        StaffLookupItem staff = getStaff(staffNo);
        return staff == null ? null
                : new StaffContext(staff.getStaffCode(), staff.getStaffName(),
                        staff.getBranchNo(), staff.getRoleCode());
    }

    public List<CodeLookupItem> listGenders() {
        return listCodes(GENDER_TABLE, "性別ｺｰﾄﾞ", "性別");
    }

    public List<CodeLookupItem> listClaimStatuses() {
        return listCodes(CLAIM_TABLE, "裁請ｺｰﾄﾞ", "裁定請求");
    }

    public List<CodeLookupItem> listBenefitStatuses() {
        return listCodes(BENEFIT_TABLE, "受給ｺｰﾄﾞ", "受給有無");
    }

    public String getPensionTypeLabel(int code) {
        String label = getPensionTypeLabels().get(Integer.valueOf(code));
        return label == null ? "" : label;
    }

    public Map<Integer, String> getPensionTypeLabels() {
        Map<Integer, String> labels = new HashMap<Integer, String>();
        List<CodeLookupItem> rows = listCodes(PENSION_TYPE_TABLE, "種類ｺｰﾄﾞ", "年金種類");
        for (int i = 0; i < rows.size(); i++) {
            labels.put(Integer.valueOf(rows.get(i).getCode()), rows.get(i).getLabel());
        }
        return labels;
    }

    private List<CodeLookupItem> listCodes(String table, String codeColumn,
            String labelColumn) {
        String sql = "SELECT " + codeColumn + " AS CODE_VALUE, " + labelColumn
                + " AS LABEL_VALUE FROM " + table + " ORDER BY " + codeColumn;
        List<CodeLookupItem> rows = new ArrayList<CodeLookupItem>();
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            connection = NenkinDataSource.openConnection();
            statement = connection.prepareStatement(sql);
            results = statement.executeQuery();
            while (results.next()) {
                rows.add(new CodeLookupItem(results.getInt("CODE_VALUE"),
                        results.getString("LABEL_VALUE")));
            }
            return rows;
        } catch (SQLException e) {
            throw failure(table + "の取得", e);
        } finally {
            close(results);
            close(statement);
            close(connection);
        }
    }

    private Map<Integer, String> loadBranchNames() {
        Map<Integer, String> branchNames = new HashMap<Integer, String>();
        String sql = "SELECT 店舗ｺｰﾄﾞ AS BRANCH_NO, 店名 AS BRANCH_NAME FROM "
                + BRANCH_TABLE;
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            connection = NenkinDataSource.openConnection();
            statement = connection.prepareStatement(sql);
            results = statement.executeQuery();
            while (results.next()) {
                branchNames.put(Integer.valueOf(results.getInt("BRANCH_NO")),
                        results.getString("BRANCH_NAME"));
            }
            return branchNames;
        } catch (SQLException e) {
            throw failure("店舗名の取得", e);
        } finally {
            close(results);
            close(statement);
            close(connection);
        }
    }

    private static StaffLookupItem readStaff(ResultSet results,
            Map<Integer, String> branchNames) throws SQLException {
        int branchNo = results.getInt("BRANCH_NO");
        String branchName = branchNames.get(Integer.valueOf(branchNo));
        return new StaffLookupItem(results.getInt("STAFF_NO"),
                results.getString("STAFF_NAME"), results.getString("STAFF_KANA_NAME"),
                branchNo, branchName == null ? "" : branchName,
                results.getString("ROLE_CODE"));
    }

    private static int nullableInt(ResultSet results, String column) throws SQLException {
        int value = results.getInt(column);
        return results.wasNull() ? 0 : value;
    }

    static String displayPhone(String rawValue) {
        String value = canonicalPhone(rawValue);
        if ((value.length() == 9 || value.length() == 10) && !value.startsWith("0")) {
            return "0" + value;
        }
        return value;
    }

    static String compactDate(String rawValue) {
        String value = text(rawValue).trim();
        if (value.length() == 0 || "0".equals(value)) {
            return "";
        }
        int decimal = value.indexOf('.');
        if (decimal >= 0) {
            value = value.substring(0, decimal);
        }
        return DateUtil.toIsoDate(value);
    }

    private static String canonicalPhone(String value) {
        String digits = PensionRepository.digits(value);
        int first = 0;
        while (first < digits.length() - 1 && digits.charAt(first) == '0') {
            first++;
        }
        return digits.substring(first);
    }

    private static String normalize(String value) {
        return Normalizer.normalize(text(value), Normalizer.Form.NFKC)
                .trim().replace('　', ' ').replaceAll(" +", " ")
                .toUpperCase(Locale.JAPAN);
    }

    private static String text(String value) {
        return value == null ? "" : value;
    }

    private static String containsPattern(String value) {
        String escaped = text(value).replace("\\", "\\\\")
                .replace("%", "\\%").replace("_", "\\_")
                .replace("[", "\\[").replace("]", "\\]");
        return "%" + escaped + "%";
    }

    private static NenkinDataAccessException failure(String operation, SQLException cause) {
        return new NenkinDataAccessException(operation + "に失敗しました。", cause);
    }

    private static void close(AutoCloseable value) {
        if (value == null) {
            return;
        }
        try {
            value.close();
        } catch (Exception e) {
            // 元の検索結果を優先する。
        }
    }
}
