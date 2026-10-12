package nenkin.model;

import java.io.Serializable;

/** Access のコード表に格納されたコードと表示名。 */
public final class CodeLookupItem implements Serializable {
    private static final long serialVersionUID = 1L;

    private int code;
    private String label = "";

    public CodeLookupItem() {
    }

    public CodeLookupItem(int code, String label) {
        this.code = code;
        this.label = label == null ? "" : label;
    }

    public int getCode() {
        return code;
    }

    public void setCode(int code) {
        this.code = code;
    }

    public String getLabel() {
        return label;
    }

    public void setLabel(String label) {
        this.label = label == null ? "" : label;
    }
}
