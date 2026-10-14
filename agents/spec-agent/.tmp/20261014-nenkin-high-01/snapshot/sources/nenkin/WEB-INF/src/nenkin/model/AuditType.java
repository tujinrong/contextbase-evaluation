package nenkin.model;

/** Access の変更FLG/削除明細に対応する監査区分。 */
public enum AuditType {
    NEW("N", "新規"),
    CHANGED("C", "変更"),
    DELETED("D", "削除");

    private final String code;
    private final String displayName;

    AuditType(String code, String displayName) {
        this.code = code;
        this.displayName = displayName;
    }

    public String getCode() {
        return code;
    }

    public String getDisplayName() {
        return displayName;
    }

    public static AuditType fromCode(String code) {
        AuditType[] values = values();
        for (int i = 0; i < values.length; i++) {
            if (values[i].code.equalsIgnoreCase(code == null ? "" : code.trim())) {
                return values[i];
            }
        }
        throw new IllegalArgumentException("未対応の監査区分です: " + code);
    }
}
