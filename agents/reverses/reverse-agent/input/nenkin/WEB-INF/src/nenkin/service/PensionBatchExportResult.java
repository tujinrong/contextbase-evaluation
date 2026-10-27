package nenkin.service;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class PensionBatchExportResult implements Serializable {
    private static final long serialVersionUID = 1L;

    private final String fileName;
    private final String contentType;
    private final byte[] content;
    private final List<PensionBatchExportFileResult> files;
    private final List<String> messages;

    public PensionBatchExportResult(String fileName, String contentType, byte[] content,
            List<PensionBatchExportFileResult> files, List<String> messages) {
        this.fileName = fileName == null ? "" : fileName;
        this.contentType = contentType == null ? "" : contentType;
        this.content = content == null ? new byte[0] : content.clone();
        this.files = Collections.unmodifiableList(
                new ArrayList<PensionBatchExportFileResult>(files));
        this.messages = Collections.unmodifiableList(new ArrayList<String>(messages));
    }

    public String getFileName() { return fileName; }
    public String getContentType() { return contentType; }
    public byte[] getContent() { return content.clone(); }
    public List<PensionBatchExportFileResult> getFiles() { return files; }
    public List<String> getMessages() { return messages; }
    public boolean hasContent() { return content.length > 0; }
}
