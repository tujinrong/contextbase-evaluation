package nenkin.service;

import java.io.Serializable;

public class PensionBatchExportFileResult implements Serializable {
    private static final long serialVersionUID = 1L;

    private final String queryName;
    private final String fileName;
    private final String categoryName;
    private final int rowCount;

    public PensionBatchExportFileResult(String queryName, String fileName,
            String categoryName, int rowCount) {
        this.queryName = queryName == null ? "" : queryName;
        this.fileName = fileName == null ? "" : fileName;
        this.categoryName = categoryName == null ? "" : categoryName;
        this.rowCount = rowCount;
    }

    public String getQueryName() { return queryName; }
    public String getFileName() { return fileName; }
    public String getCategoryName() { return categoryName; }
    public int getRowCount() { return rowCount; }
}
