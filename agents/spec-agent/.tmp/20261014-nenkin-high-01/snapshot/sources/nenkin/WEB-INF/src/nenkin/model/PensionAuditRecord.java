package nenkin.model;

import java.io.Serializable;

/** バッチ出力で使用する予約の監査スナップショット。 */
public class PensionAuditRecord implements Serializable {
    private static final long serialVersionUID = 1L;

    private long auditId;
    private AuditType auditType;
    private String auditDate = "";
    private String auditTime = "";
    private Integer updatedBy;
    private PensionReservation reservation = new PensionReservation();

    public PensionAuditRecord() {
    }

    public PensionAuditRecord(long auditId, AuditType auditType, String auditDate,
            String auditTime, Integer updatedBy, PensionReservation reservation) {
        this.auditId = auditId;
        this.auditType = auditType;
        this.auditDate = auditDate == null ? "" : auditDate;
        this.auditTime = auditTime == null ? "" : auditTime;
        this.updatedBy = updatedBy;
        this.reservation = reservation == null ? new PensionReservation() : reservation.copy();
    }

    public long getAuditId() { return auditId; }
    public void setAuditId(long auditId) { this.auditId = auditId; }
    public AuditType getAuditType() { return auditType; }
    public void setAuditType(AuditType auditType) { this.auditType = auditType; }
    public String getAuditDate() { return auditDate; }
    public void setAuditDate(String auditDate) { this.auditDate = auditDate == null ? "" : auditDate; }
    public String getAuditTime() { return auditTime; }
    public void setAuditTime(String auditTime) { this.auditTime = auditTime == null ? "" : auditTime; }
    public Integer getUpdatedBy() { return updatedBy; }
    public void setUpdatedBy(Integer updatedBy) { this.updatedBy = updatedBy; }
    public PensionReservation getReservation() { return reservation.copy(); }
    public void setReservation(PensionReservation reservation) {
        this.reservation = reservation == null ? new PensionReservation() : reservation.copy();
    }
}
