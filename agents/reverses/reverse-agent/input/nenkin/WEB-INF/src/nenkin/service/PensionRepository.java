package nenkin.service;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Types;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import nenkin.model.AuditType;
import nenkin.model.PensionAuditRecord;
import nenkin.model.PensionCandidate;
import nenkin.model.PensionReservation;
import nenkin.model.StaffContext;
import nenkin.util.AnsiTextUtil;
import nenkin.util.DateUtil;

/** Access と同じ年金業務表を N2 JNDI 経由で操作する Repository。 */
public final class PensionRepository {
    private static final String TABLE = "年金1_LK";
    private static final String DELETE_TABLE = "年金＿削除明細";
    private static final String BRANCH_TABLE = "店名テーブル";
    private static final String GENDER_TABLE = "性別テーブル";
    private static final String CLAIM_TABLE = "裁定請求テーブル";
    private static final String BENEFIT_TABLE = "受給有無テーブル";
    private static final String PENSION_TYPE_TABLE = "年金種類テーブル";
    private static final String CUSTOMER_TABLE = "N2_SIGHT.Ｂ顧客基本表";
    private static final String LIKE_ESCAPE = " ESCAPE '\\'";

    private static final String[] RECORD_COLUMNS = {
        "店番", "顧客番号", "担当者コード", "顧客氏名", "ふりがな", "性別", "住所", "電話番号",
        "生年月日", "\"種類：国民年金\"", "\"種類：厚生年金\"", "\"種類：共済年金\"",
        "\"種類：厚生年金基金\"", "\"種類：国民年金基金\"", "年金種類", "裁定請求",
        "請求予定日", "予定年齢", "配偶者名",
        "配偶者生年月日", "受給有無", "予約徴求日", "備考", "データ更新日", "更新時間", "更新者",
        "\"６ヶ月先確認\"", "変更FLG"
    };

    private static final String SELECT_COLUMNS =
            "R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, "
            + "R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, "
            + "R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, "
            + "G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, "
            + "R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, "
            + "R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, "
            + "R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, "
            + "R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, "
            + "R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, "
            + "R.\"種類：国民年金\" AS NATIONAL_PENSION, "
            + "R.\"種類：厚生年金\" AS EMPLOYEE_PENSION, "
            + "R.\"種類：共済年金\" AS MUTUAL_AID_PENSION, "
            + "R.\"種類：厚生年金基金\" AS EMPLOYEE_PENSION_FUND, "
            + "R.\"種類：国民年金基金\" AS NATIONAL_PENSION_FUND, "
            + "R.\"６ヶ月先確認\" AS SIX_MONTH_CHECK";

    private static final String INSERT_SQL = "INSERT INTO " + TABLE + " ("
            + join(RECORD_COLUMNS, ", ") + ") VALUES (" + placeholders(RECORD_COLUMNS.length)
            + ")";
    private static final String INSERT_DELETED_SQL = "INSERT INTO " + DELETE_TABLE + " ("
            + join(RECORD_COLUMNS, ", ") + ") VALUES (" + placeholders(RECORD_COLUMNS.length)
            + ")";
    private static final String UPDATE_SQL = "UPDATE " + TABLE + " SET "
            + assignments(RECORD_COLUMNS) + " WHERE ふりがな = ? AND 電話番号 = ?";

    private static final PensionRepository INSTANCE = new PensionRepository();

    private PensionRepository() {
    }

    public static PensionRepository getInstance() {
        return INSTANCE;
    }

    public PensionReservation createEmpty() {
        return new PensionReservation();
    }

    public PensionReservation createEmpty(StaffContext staff) {
        return new PensionReservation();
    }

    /** Access の顧客基本読み込みクエリー4900と同じ顧客主データを返す。 */
    public PensionReservation findByCustomer(int branchNo, int customerNo) {
        String sql = "SELECT C.店舗コード AS BRANCH_NO, C.顧客番号 AS CUSTOMER_NO, "
                + "C.担当者コード AS STAFF_CODE, C.漢字氏名 AS CUSTOMER_NAME, "
                + "C.カナ氏名 AS KANA_NAME, C.性別コード AS GENDER_CODE, "
                + "C.漢字住所 AS ADDRESS, C.電話番号 AS PHONE_NUMBER, "
                + "C.生年月日 AS BIRTH_DATE FROM " + CUSTOMER_TABLE
                + " C WHERE C.店舗コード = ? AND C.顧客番号 = ?";
        Connection customerConnection = null;
        PreparedStatement statement = null;
        ResultSet results = null;
        PensionReservation value = null;
        String genderCode = "";
        try {
            customerConnection = NenkinDataSource.openCustomerConnection();
            statement = customerConnection.prepareStatement(sql);
            statement.setInt(1, branchNo);
            statement.setInt(2, customerNo);
            results = statement.executeQuery();
            if (results.next()) {
                value = new PensionReservation();
                value.setBranchNo(nullableInteger(results, "BRANCH_NO"));
                value.setCustomerNo(nullableInteger(results, "CUSTOMER_NO"));
                value.setStaffCode(nullableInteger(results, "STAFF_CODE"));
                value.setCustomerName(results.getString("CUSTOMER_NAME"));
                value.setKanaName(results.getString("KANA_NAME"));
                genderCode = text(results.getString("GENDER_CODE")).trim();
                value.setAddress(results.getString("ADDRESS"));
                value.setPhoneNumber(ReferenceDataService.displayPhone(
                        results.getString("PHONE_NUMBER")));
                value.setBirthDate(ReferenceDataService.compactDate(
                        results.getString("BIRTH_DATE")));
            }
        } catch (SQLException e) {
            throw failure("顧客基本表の取得", e);
        } finally {
            close(results);
            close(statement);
            close(customerConnection);
        }
        if (value == null) {
            return null;
        }

        Connection businessConnection = null;
        try {
            businessConnection = NenkinDataSource.openConnection();
            value.setBranchName(resolveBranchName(businessConnection, value.getBranchNo(), ""));
            value.setGender(resolveCodeLabel(businessConnection, GENDER_TABLE,
                    "性別ｺｰﾄﾞ", "性別", integerOrNull(genderCode)));
            return value;
        } catch (SQLException e) {
            throw failure("顧客基本表の表示値変換", e);
        } finally {
            close(businessConnection);
        }
    }

    public PensionReservation findByKanaAndPhone(String kanaName, String phoneNumber) {
        String kana = normalize(kanaName);
        BigDecimal phone = phoneValue(phoneNumber);
        if (kana.length() == 0 || phone == null) {
            return null;
        }
        String sql = "SELECT " + SELECT_COLUMNS + fromClause(TABLE)
                + " WHERE R.ふりがな = ? AND R.電話番号 = ?";
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            connection = NenkinDataSource.openConnection();
            statement = connection.prepareStatement(sql);
            statement.setString(1, kana);
            statement.setBigDecimal(2, phone);
            results = statement.executeQuery();
            return results.next() ? readReservation(results) : null;
        } catch (SQLException e) {
            throw failure("フリガナ・電話番号による年金予約の取得", e);
        } finally {
            close(results);
            close(statement);
            close(connection);
        }
    }

    public List<PensionCandidate> searchCandidates(String kanaName, String phoneNumber) {
        String kana = normalize(kanaName);
        String phone = canonicalPhone(phoneNumber);
        StringBuilder sql = new StringBuilder("SELECT R.店番 AS BRANCH_NO, ")
                .append("R.顧客番号 AS CUSTOMER_NO, R.ふりがな AS KANA_NAME, ")
                .append("R.顧客氏名 AS CUSTOMER_NAME, R.電話番号 AS PHONE_NUMBER, ")
                .append("R.生年月日 AS BIRTH_DATE FROM ").append(TABLE)
                .append(" R WHERE 1 = 1");
        if (kana.length() > 0) {
            sql.append(" AND UPPER(R.ふりがな) LIKE UPPER(?)").append(LIKE_ESCAPE);
        }
        if (phone.length() > 0) {
            sql.append(" AND CAST(R.電話番号 AS VARCHAR(40)) LIKE ?").append(LIKE_ESCAPE);
        }
        sql.append(" ORDER BY R.ふりがな, R.店番, R.顧客番号");
        List<PensionCandidate> rows = new ArrayList<PensionCandidate>();
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            connection = NenkinDataSource.openConnection();
            statement = connection.prepareStatement(sql.toString());
            int index = 1;
            if (kana.length() > 0) {
                statement.setString(index++, containsPattern(kana));
            }
            if (phone.length() > 0) {
                statement.setString(index++, containsPattern(phone));
            }
            results = statement.executeQuery();
            while (results.next()) {
                rows.add(new PensionCandidate(results.getInt("BRANCH_NO"),
                        results.getInt("CUSTOMER_NO"), results.getString("KANA_NAME"),
                        results.getString("CUSTOMER_NAME"),
                        ReferenceDataService.displayPhone(results.getString("PHONE_NUMBER")),
                        results.getString("BIRTH_DATE")));
            }
            return rows;
        } catch (SQLException e) {
            throw failure("年金予約候補の検索", e);
        } finally {
            close(results);
            close(statement);
            close(connection);
        }
    }

    public List<PensionReservation> list() {
        return queryReservations("SELECT " + SELECT_COLUMNS + fromClause(TABLE)
                + " ORDER BY R.店番, R.顧客番号, R.ふりがな", null, null);
    }

    public List<PensionReservation> listByBranch(int branchNo) {
        String sql = "SELECT " + SELECT_COLUMNS + fromClause(TABLE)
                + " WHERE R.店番 = ? ORDER BY R.請求予定日 DESC, R.担当者コード, R.顧客番号";
        List<PensionReservation> rows = new ArrayList<PensionReservation>();
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            connection = NenkinDataSource.openConnection();
            statement = connection.prepareStatement(sql);
            statement.setInt(1, branchNo);
            results = statement.executeQuery();
            while (results.next()) {
                rows.add(readReservation(results));
            }
            return rows;
        } catch (SQLException e) {
            throw failure("店舗別年金予約の検索", e);
        } finally {
            close(results);
            close(statement);
            close(connection);
        }
    }

    /** sortType: 1=担当者, 2=フリガナ, 3=生年月日, 4=請求予定日。 */
    public List<PensionReservation> search(Integer branchFrom, Integer branchTo, int sortType) {
        StringBuilder sql = new StringBuilder("SELECT ").append(SELECT_COLUMNS)
                .append(fromClause(TABLE)).append(" WHERE 1 = 1");
        if (branchFrom != null) {
            sql.append(branchTo == null ? " AND R.店番 = ?" : " AND R.店番 >= ?");
        }
        if (branchTo != null) {
            sql.append(" AND R.店番 <= ?");
        }
        switch (sortType) {
        case 2:
            sql.append(" ORDER BY R.店番, R.ふりがな, R.顧客番号");
            break;
        case 3:
            sql.append(" ORDER BY R.店番, R.生年月日, R.顧客番号");
            break;
        case 4:
            sql.append(" ORDER BY R.店番, R.請求予定日, R.顧客番号");
            break;
        default:
            sql.append(" ORDER BY R.店番, R.担当者コード, R.顧客番号");
            break;
        }
        return queryReservations(sql.toString(), branchFrom, branchTo);
    }

    public AuditType save(PensionReservation reservation) {
        Integer updatedBy = reservation == null ? null : reservation.getStaffCode();
        return save(reservation, updatedBy);
    }

    public synchronized AuditType save(PensionReservation reservation, Integer updatedBy) {
        PensionReservation value = prepareForSave(reservation);
        String keyKana = value.getKanaName();
        BigDecimal keyPhone = phoneValue(value.getPhoneNumber());
        Connection connection = null;
        try {
            connection = NenkinDataSource.openConnection();
            connection.setAutoCommit(false);
            value.setBranchName(resolveBranchName(connection, value.getBranchNo(),
                    value.getBranchName()));
            boolean exists = exists(connection, keyKana, keyPhone);
            AuditType type = exists ? AuditType.CHANGED : AuditType.NEW;
            String updateTime = DateUtil.currentTime();
            if (exists) {
                update(connection, value, keyKana, keyPhone, updatedBy, updateTime);
            } else {
                insert(connection, value, updatedBy, updateTime);
            }
            connection.commit();
            return type;
        } catch (Exception e) {
            rollback(connection);
            if (e instanceof NenkinDataAccessException) {
                throw (NenkinDataAccessException) e;
            }
            throw failure("年金予約の登録・更新", e);
        } finally {
            close(connection);
        }
    }

    public boolean delete(String kanaName, String phoneNumber) {
        return delete(kanaName, phoneNumber, null);
    }

    public synchronized boolean delete(String kanaName, String phoneNumber, Integer updatedBy) {
        String kana = normalize(kanaName);
        BigDecimal phone = phoneValue(phoneNumber);
        if (kana.length() == 0 || phone == null) {
            return false;
        }
        Connection connection = null;
        PreparedStatement delete = null;
        try {
            connection = NenkinDataSource.openConnection();
            connection.setAutoCommit(false);
            PensionReservation existing = findByKey(connection, kana, phone);
            if (existing == null) {
                connection.rollback();
                return false;
            }
            existing.setDataUpdateDate(DateUtil.todayIso());
            insertDeleted(connection, existing, updatedBy, DateUtil.currentTime());

            delete = connection.prepareStatement("DELETE FROM " + TABLE
                    + " WHERE ふりがな = ? AND 電話番号 = ?");
            delete.setString(1, kana);
            delete.setBigDecimal(2, phone);
            int deleted = delete.executeUpdate();
            if (deleted != 1) {
                throw new SQLException("削除件数が1件ではありません: " + deleted);
            }
            connection.commit();
            return true;
        } catch (Exception e) {
            rollback(connection);
            throw failure("年金予約の削除", e);
        } finally {
            close(delete);
            close(connection);
        }
    }

    public List<PensionAuditRecord> findAuditRecords(AuditType type, String dateFrom,
            String dateTo, Integer updatedBy) {
        if (type == null) {
            throw new IllegalArgumentException("監査区分を指定してください。");
        }
        String from = optionalDate(dateFrom);
        String to = optionalDate(dateTo);
        String sourceTable = type == AuditType.DELETED ? DELETE_TABLE : TABLE;
        StringBuilder sql = new StringBuilder("SELECT ").append(SELECT_COLUMNS)
                .append(", R.データ更新日 AS AUDIT_DATE, R.更新時間 AS AUDIT_TIME, ")
                .append("R.更新者 AS UPDATED_BY").append(fromClause(sourceTable))
                .append(" WHERE 1 = 1");
        if (type != AuditType.DELETED) {
            sql.append(" AND R.変更FLG = ?");
        }
        if (from.length() > 0) {
            sql.append(" AND R.データ更新日 >= ?");
        }
        if (to.length() > 0) {
            sql.append(" AND R.データ更新日 <= ?");
        }
        if (updatedBy != null) {
            sql.append(" AND R.更新者 = ?");
        }
        sql.append(" ORDER BY R.データ更新日, R.更新時間, R.店番, R.顧客番号");

        List<PensionAuditRecord> rows = new ArrayList<PensionAuditRecord>();
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            connection = NenkinDataSource.openConnection();
            statement = connection.prepareStatement(sql.toString());
            int index = 1;
            if (type != AuditType.DELETED) {
                statement.setInt(index++, type == AuditType.NEW ? 0 : 1);
            }
            if (from.length() > 0) {
                setDate(statement, index++, from);
            }
            if (to.length() > 0) {
                setDate(statement, index++, to);
            }
            if (updatedBy != null) {
                statement.setInt(index++, updatedBy.intValue());
            }
            results = statement.executeQuery();
            long rowId = 1L;
            while (results.next()) {
                rows.add(new PensionAuditRecord(rowId++, type,
                        results.getString("AUDIT_DATE"), results.getString("AUDIT_TIME"),
                        nullableInteger(results, "UPDATED_BY"), readReservation(results)));
            }
            return rows;
        } catch (SQLException e) {
            throw failure("年金予約の更新区分検索", e);
        } finally {
            close(results);
            close(statement);
            close(connection);
        }
    }

    public AuditType findLatestAuditType(String kanaName, String phoneNumber) {
        String kana = normalize(kanaName);
        BigDecimal phone = phoneValue(phoneNumber);
        if (kana.length() == 0 || phone == null) {
            return null;
        }
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            connection = NenkinDataSource.openConnection();
            statement = connection.prepareStatement("SELECT 変更FLG FROM " + TABLE
                    + " WHERE ふりがな = ? AND 電話番号 = ?");
            statement.setString(1, kana);
            statement.setBigDecimal(2, phone);
            statement.setMaxRows(1);
            results = statement.executeQuery();
            if (results.next()) {
                int flag = results.getInt(1);
                return flag == 0 ? AuditType.NEW : AuditType.CHANGED;
            }
            close(results);
            results = null;
            close(statement);
            statement = connection.prepareStatement("SELECT 1 FROM " + DELETE_TABLE
                    + " WHERE ふりがな = ? AND 電話番号 = ?"
                    + " ORDER BY データ更新日 DESC, 更新時間 DESC");
            statement.setString(1, kana);
            statement.setBigDecimal(2, phone);
            statement.setMaxRows(1);
            results = statement.executeQuery();
            return results.next() ? AuditType.DELETED : null;
        } catch (SQLException e) {
            throw failure("最終更新区分の取得", e);
        } finally {
            close(results);
            close(statement);
            close(connection);
        }
    }

    /** Access Q130 と同様に基準日以前の年金＿削除明細を削除する。 */
    public synchronized int purgeDeletedAuditsThrough(String cutoffDate) {
        String cutoff = optionalDate(cutoffDate);
        if (cutoff.length() == 0) {
            return 0;
        }
        Connection connection = null;
        PreparedStatement statement = null;
        try {
            connection = NenkinDataSource.openConnection();
            connection.setAutoCommit(false);
            statement = connection.prepareStatement("DELETE FROM " + DELETE_TABLE
                    + " WHERE データ更新日 <= ?");
            setDate(statement, 1, cutoff);
            int count = statement.executeUpdate();
            connection.commit();
            return count;
        } catch (SQLException e) {
            rollback(connection);
            throw failure("削除明細履歴の整理", e);
        } finally {
            close(statement);
            close(connection);
        }
    }

    private List<PensionReservation> queryReservations(String sql, Integer branchFrom,
            Integer branchTo) {
        List<PensionReservation> rows = new ArrayList<PensionReservation>();
        Connection connection = null;
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            connection = NenkinDataSource.openConnection();
            statement = connection.prepareStatement(sql);
            int index = 1;
            if (branchFrom != null) {
                statement.setInt(index++, branchFrom.intValue());
            }
            if (branchTo != null) {
                statement.setInt(index++, branchTo.intValue());
            }
            results = statement.executeQuery();
            while (results.next()) {
                rows.add(readReservation(results));
            }
            return rows;
        } catch (SQLException e) {
            throw failure("年金予約一覧の検索", e);
        } finally {
            close(results);
            close(statement);
            close(connection);
        }
    }

    private static PensionReservation prepareForSave(PensionReservation source) {
        if (source == null) {
            throw new IllegalArgumentException("登録対象の年金予約がありません。");
        }
        PensionReservation value = source.copy();
        value.setKanaName(normalize(value.getKanaName()));
        value.setPhoneNumber(value.getPhoneNumber().trim());
        if (value.getKanaName().length() == 0) {
            throw new IllegalArgumentException("フリガナを入力してください。");
        }
        if (phoneValue(value.getPhoneNumber()) == null) {
            throw new IllegalArgumentException("電話番号を入力してください。");
        }
        AnsiTextUtil.validateNotes(value.getNotes());
        value.setBirthDate(optionalDate(value.getBirthDate()));
        value.setClaimScheduledDate(optionalDate(value.getClaimScheduledDate()));
        value.setReservationRequestDate(optionalDate(value.getReservationRequestDate()));
        value.setSpouseBirthDate(optionalDate(value.getSpouseBirthDate()));
        value.setDataUpdateDate(DateUtil.todayIso());
        return value;
    }

    private static String resolveBranchName(Connection connection, Integer branchNo,
            String fallback) throws SQLException {
        if (branchNo == null) {
            return text(fallback);
        }
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            statement = connection.prepareStatement("SELECT 店名 FROM " + BRANCH_TABLE
                    + " WHERE 店舗ｺｰﾄﾞ = ?");
            statement.setInt(1, branchNo.intValue());
            results = statement.executeQuery();
            return results.next() ? text(results.getString(1)) : text(fallback);
        } finally {
            close(results);
            close(statement);
        }
    }

    private static String resolveCodeLabel(Connection connection, String table,
            String codeColumn, String labelColumn, Integer code) throws SQLException {
        if (code == null) {
            return "";
        }
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            statement = connection.prepareStatement("SELECT " + labelColumn + " FROM " + table
                    + " WHERE " + codeColumn + " = ?");
            statement.setInt(1, code.intValue());
            results = statement.executeQuery();
            return results.next() ? text(results.getString(1)) : "";
        } finally {
            close(results);
            close(statement);
        }
    }

    private static Integer resolveCode(Connection connection, String table, String codeColumn,
            String labelColumn, String label) throws SQLException {
        String value = text(label).trim();
        if (value.length() == 0) {
            return null;
        }
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            statement = connection.prepareStatement("SELECT " + codeColumn + " FROM " + table
                    + " WHERE " + labelColumn + " = ?");
            statement.setString(1, value);
            results = statement.executeQuery();
            if (!results.next()) {
                throw new SQLException(table + "に表示値がありません: " + value);
            }
            return Integer.valueOf(results.getInt(1));
        } finally {
            close(results);
            close(statement);
        }
    }

    private static Integer resolvePensionTypeCode(Connection connection,
            PensionReservation value) throws SQLException {
        int code = (value.isNationalPension() ? 1 : 0)
                + (value.isEmployeePension() ? 2 : 0)
                + (value.isMutualAidPension() ? 4 : 0)
                + (value.isEmployeePensionFund() ? 8 : 0)
                + (value.isNationalPensionFund() ? 16 : 0);
        if (code == 0) {
            return null;
        }
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            statement = connection.prepareStatement("SELECT 年金種類 FROM "
                    + PENSION_TYPE_TABLE + " WHERE 種類ｺｰﾄﾞ = ?");
            statement.setInt(1, code);
            results = statement.executeQuery();
            if (!results.next()) {
                throw new SQLException(PENSION_TYPE_TABLE + "に種類コードがありません: " + code);
            }
            return Integer.valueOf(code);
        } finally {
            close(results);
            close(statement);
        }
    }

    private static boolean exists(Connection connection, String kana, BigDecimal phone)
            throws SQLException {
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            statement = connection.prepareStatement("SELECT 1 FROM " + TABLE
                    + " WHERE ふりがな = ? AND 電話番号 = ?");
            statement.setString(1, kana);
            statement.setBigDecimal(2, phone);
            results = statement.executeQuery();
            return results.next();
        } finally {
            close(results);
            close(statement);
        }
    }

    private static PensionReservation findByKey(Connection connection, String kana,
            BigDecimal phone) throws SQLException {
        PreparedStatement statement = null;
        ResultSet results = null;
        try {
            statement = connection.prepareStatement("SELECT " + SELECT_COLUMNS
                    + fromClause(TABLE) + " WHERE R.ふりがな = ? AND R.電話番号 = ?");
            statement.setString(1, kana);
            statement.setBigDecimal(2, phone);
            results = statement.executeQuery();
            return results.next() ? readReservation(results) : null;
        } finally {
            close(results);
            close(statement);
        }
    }

    private static void insert(Connection connection, PensionReservation value,
            Integer updatedBy, String updateTime) throws SQLException {
        PreparedStatement statement = null;
        try {
            statement = connection.prepareStatement(INSERT_SQL);
            bindRecord(connection, statement, 1, value, updatedBy, updateTime,
                    Integer.valueOf(0));
            if (statement.executeUpdate() != 1) {
                throw new SQLException("新規登録件数が1件ではありません。");
            }
        } finally {
            close(statement);
        }
    }

    private static void update(Connection connection, PensionReservation value, String keyKana,
            BigDecimal keyPhone, Integer updatedBy, String updateTime) throws SQLException {
        PreparedStatement statement = null;
        try {
            statement = connection.prepareStatement(UPDATE_SQL);
            int index = bindRecord(connection, statement, 1, value, updatedBy, updateTime,
                    Integer.valueOf(1));
            statement.setString(index++, keyKana);
            statement.setBigDecimal(index, keyPhone);
            int changed = statement.executeUpdate();
            if (changed != 1) {
                throw new SQLException("更新件数が1件ではありません: " + changed);
            }
        } finally {
            close(statement);
        }
    }

    private static void insertDeleted(Connection connection, PensionReservation value,
            Integer updatedBy, String updateTime) throws SQLException {
        PreparedStatement statement = null;
        try {
            statement = connection.prepareStatement(INSERT_DELETED_SQL);
            bindRecord(connection, statement, 1, value, updatedBy, updateTime, null);
            if (statement.executeUpdate() != 1) {
                throw new SQLException("削除明細登録件数が1件ではありません。");
            }
        } finally {
            close(statement);
        }
    }

    private static int bindRecord(Connection connection, PreparedStatement statement, int index,
            PensionReservation value, Integer updatedBy, String updateTime, Integer changeFlag)
            throws SQLException {
        setInteger(statement, index++, value.getBranchNo());
        setInteger(statement, index++, value.getCustomerNo());
        setInteger(statement, index++, value.getStaffCode());
        statement.setString(index++, value.getCustomerName());
        statement.setString(index++, value.getKanaName());
        setInteger(statement, index++, resolveCode(connection, GENDER_TABLE,
                "性別ｺｰﾄﾞ", "性別", value.getGender()));
        statement.setString(index++, value.getAddress());
        setPhone(statement, index++, value.getPhoneNumber());
        setDate(statement, index++, value.getBirthDate());
        statement.setInt(index++, value.isNationalPension() ? 1 : 0);
        statement.setInt(index++, value.isEmployeePension() ? 1 : 0);
        statement.setInt(index++, value.isMutualAidPension() ? 1 : 0);
        statement.setInt(index++, value.isEmployeePensionFund() ? 1 : 0);
        statement.setInt(index++, value.isNationalPensionFund() ? 1 : 0);
        setInteger(statement, index++, resolvePensionTypeCode(connection, value));
        setInteger(statement, index++, resolveCode(connection, CLAIM_TABLE,
                "裁請ｺｰﾄﾞ", "裁定請求", value.getClaimStatus()));
        setDate(statement, index++, value.getClaimScheduledDate());
        setInteger(statement, index++, value.getPlannedAge());
        statement.setString(index++, value.getSpouseName());
        setDate(statement, index++, value.getSpouseBirthDate());
        setInteger(statement, index++, resolveCode(connection, BENEFIT_TABLE,
                "受給ｺｰﾄﾞ", "受給有無", value.getHasBenefit()));
        setDate(statement, index++, value.getReservationRequestDate());
        statement.setString(index++, value.getNotes());
        setDate(statement, index++, value.getDataUpdateDate());
        setTime(statement, index++, updateTime);
        setInteger(statement, index++, updatedBy);
        statement.setInt(index++, value.isSixMonthCheck() ? 1 : 0);
        setInteger(statement, index++, changeFlag);
        return index;
    }

    private static PensionReservation readReservation(ResultSet results) throws SQLException {
        PensionReservation value = new PensionReservation();
        value.setBranchNo(nullableInteger(results, "BRANCH_NO"));
        value.setBranchName(results.getString("BRANCH_NAME"));
        value.setCustomerNo(nullableInteger(results, "CUSTOMER_NO"));
        value.setStaffCode(nullableInteger(results, "STAFF_CODE"));
        value.setCustomerName(results.getString("CUSTOMER_NAME"));
        value.setKanaName(results.getString("KANA_NAME"));
        value.setGender(results.getString("GENDER"));
        value.setAddress(results.getString("ADDRESS"));
        value.setPhoneNumber(ReferenceDataService.displayPhone(results.getString("PHONE_NUMBER")));
        value.setBirthDate(results.getString("BIRTH_DATE"));
        value.setClaimStatus(results.getString("CLAIM_STATUS"));
        value.setClaimScheduledDate(results.getString("CLAIM_SCHEDULED_DATE"));
        value.setPlannedAge(nullableInteger(results, "PLANNED_AGE"));
        value.setReservationRequestDate(results.getString("RESERVATION_REQUEST_DATE"));
        value.setDataUpdateDate(results.getString("DATA_UPDATE_DATE"));
        value.setNotes(results.getString("NOTES"));
        value.setSpouseName(results.getString("SPOUSE_NAME"));
        value.setHasBenefit(results.getString("HAS_BENEFIT"));
        value.setSpouseBirthDate(results.getString("SPOUSE_BIRTH_DATE"));
        value.setPensionType(results.getString("PENSION_TYPE"));
        value.setNationalPension(results.getInt("NATIONAL_PENSION") != 0);
        value.setEmployeePension(results.getInt("EMPLOYEE_PENSION") != 0);
        value.setMutualAidPension(results.getInt("MUTUAL_AID_PENSION") != 0);
        value.setEmployeePensionFund(results.getInt("EMPLOYEE_PENSION_FUND") != 0);
        value.setNationalPensionFund(results.getInt("NATIONAL_PENSION_FUND") != 0);
        value.setSixMonthCheck(results.getInt("SIX_MONTH_CHECK") != 0);
        return value;
    }

    private static String fromClause(String table) {
        return " FROM " + table + " R"
                + " LEFT JOIN " + BRANCH_TABLE + " B ON R.店番 = B.店舗ｺｰﾄﾞ"
                + " LEFT JOIN " + GENDER_TABLE + " G ON R.性別 = G.性別ｺｰﾄﾞ"
                + " LEFT JOIN " + CLAIM_TABLE + " C ON R.裁定請求 = C.裁請ｺｰﾄﾞ"
                + " LEFT JOIN " + BENEFIT_TABLE + " H ON R.受給有無 = H.受給ｺｰﾄﾞ"
                + " LEFT JOIN " + PENSION_TYPE_TABLE + " P ON R.年金種類 = P.種類ｺｰﾄﾞ";
    }

    private static Integer nullableInteger(ResultSet results, String column) throws SQLException {
        int value = results.getInt(column);
        return results.wasNull() ? null : Integer.valueOf(value);
    }

    private static Integer integerOrNull(String value) {
        String text = value == null ? "" : value.trim();
        if (text.length() == 0) {
            return null;
        }
        try {
            return Integer.valueOf(text);
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static void setInteger(PreparedStatement statement, int index, Integer value)
            throws SQLException {
        if (value == null) {
            statement.setNull(index, Types.INTEGER);
        } else {
            statement.setInt(index, value.intValue());
        }
    }

    private static void setPhone(PreparedStatement statement, int index, String value)
            throws SQLException {
        BigDecimal phone = phoneValue(value);
        if (phone == null) {
            statement.setNull(index, Types.DECIMAL);
        } else {
            statement.setBigDecimal(index, phone);
        }
    }

    private static void setDate(PreparedStatement statement, int index, String value)
            throws SQLException {
        String date = text(value).trim();
        if (date.length() == 0) {
            statement.setNull(index, Types.DATE);
        } else {
            statement.setDate(index, java.sql.Date.valueOf(date));
        }
    }

    private static void setTime(PreparedStatement statement, int index, String value)
            throws SQLException {
        String time = text(value);
        if (time.length() < 8) {
            statement.setNull(index, Types.TIME);
        } else {
            statement.setTime(index, java.sql.Time.valueOf(time.substring(0, 8)));
        }
    }

    private static String normalize(String value) {
        return Normalizer.normalize(text(value), Normalizer.Form.NFKC)
                .trim().replace('　', ' ').replaceAll(" +", " ")
                .toUpperCase(Locale.JAPAN);
    }

    static String digits(String value) {
        String source = text(value);
        StringBuilder result = new StringBuilder(source.length());
        for (int i = 0; i < source.length(); i++) {
            char character = source.charAt(i);
            if (Character.isDigit(character)) {
                int digit = Character.digit(character, 10);
                if (digit >= 0) {
                    result.append((char) ('0' + digit));
                }
            }
        }
        return result.toString();
    }

    private static BigDecimal phoneValue(String value) {
        String phone = digits(value);
        return phone.length() == 0 ? null : new BigDecimal(phone);
    }

    private static String canonicalPhone(String value) {
        BigDecimal phone = phoneValue(value);
        return phone == null ? "" : phone.toPlainString();
    }

    private static String optionalDate(String value) {
        return text(value).trim().length() == 0 ? "" : DateUtil.toIsoDate(value);
    }

    private static String text(String value) {
        return value == null ? "" : value;
    }

    private static String join(String[] values, String separator) {
        StringBuilder result = new StringBuilder();
        for (int i = 0; i < values.length; i++) {
            if (i > 0) {
                result.append(separator);
            }
            result.append(values[i]);
        }
        return result.toString();
    }

    private static String placeholders(int count) {
        StringBuilder result = new StringBuilder();
        for (int i = 0; i < count; i++) {
            if (i > 0) {
                result.append(", ");
            }
            result.append('?');
        }
        return result.toString();
    }

    private static String assignments(String[] values) {
        StringBuilder result = new StringBuilder();
        for (int i = 0; i < values.length; i++) {
            if (i > 0) {
                result.append(", ");
            }
            result.append(values[i]).append(" = ?");
        }
        return result.toString();
    }

    private static String containsPattern(String value) {
        String escaped = text(value).replace("\\", "\\\\")
                .replace("%", "\\%").replace("_", "\\_")
                .replace("[", "\\[").replace("]", "\\]");
        return "%" + escaped + "%";
    }

    private static NenkinDataAccessException failure(String operation, Throwable cause) {
        return new NenkinDataAccessException(operation + "に失敗しました。", cause);
    }

    private static void rollback(Connection connection) {
        if (connection == null) {
            return;
        }
        try {
            connection.rollback();
        } catch (SQLException e) {
            // 元の更新例外を優先する。
        }
    }

    private static void close(AutoCloseable value) {
        if (value == null) {
            return;
        }
        try {
            value.close();
        } catch (Exception e) {
            // close 失敗で業務結果を上書きしない。
        }
    }
}
