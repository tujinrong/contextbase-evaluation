package nenkin.service;

import java.io.Serializable;

public class PensionExcelExportResult implements Serializable {
    private static final long serialVersionUID = 1L;

    private final String fileName;
    private final byte[] content;
    private final int rowCount;

    public PensionExcelExportResult(String fileName, byte[] content, int rowCount) {
        this.fileName = fileName == null ? "" : fileName;
        this.content = content == null ? new byte[0] : content.clone();
        this.rowCount = rowCount;
    }

    public String getFileName() {
        return fileName;
    }

    public byte[] getContent() {
        return content.clone();
    }

    public int getRowCount() {
        return rowCount;
    }

    public boolean hasContent() {
        return content.length > 0;
    }
}
