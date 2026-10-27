package nenkin.service;

import java.io.Serializable;

/** 日次・月次 Excel 出力条件。日付入力は和暦/西暦の両方を許容する。 */
public class PensionBatchExportRequest implements Serializable {
    private static final long serialVersionUID = 1L;

    private PensionBatchRunMode runMode = PensionBatchRunMode.DAILY;
    private String dailyDate = "";
    private String monthStart = "";
    private String monthEnd = "";
    private String staffNo = "";
    private boolean includeNew;
    private boolean includeChanged;
    private boolean includeDeleted;
    private String deleteCutoffDate = "";

    public PensionBatchExportRequest() {
    }

    public PensionBatchRunMode getRunMode() { return runMode; }
    public void setRunMode(PensionBatchRunMode runMode) { this.runMode = runMode; }
    public String getDailyDate() { return dailyDate; }
    public void setDailyDate(String dailyDate) { this.dailyDate = text(dailyDate); }
    public String getMonthStart() { return monthStart; }
    public void setMonthStart(String monthStart) { this.monthStart = text(monthStart); }
    public String getMonthEnd() { return monthEnd; }
    public void setMonthEnd(String monthEnd) { this.monthEnd = text(monthEnd); }
    public String getStaffNo() { return staffNo; }
    public void setStaffNo(String staffNo) { this.staffNo = text(staffNo); }
    public boolean isIncludeNew() { return includeNew; }
    public void setIncludeNew(boolean includeNew) { this.includeNew = includeNew; }
    public boolean isIncludeChanged() { return includeChanged; }
    public void setIncludeChanged(boolean includeChanged) { this.includeChanged = includeChanged; }
    public boolean isIncludeDeleted() { return includeDeleted; }
    public void setIncludeDeleted(boolean includeDeleted) { this.includeDeleted = includeDeleted; }
    public String getDeleteCutoffDate() { return deleteCutoffDate; }
    public void setDeleteCutoffDate(String deleteCutoffDate) {
        this.deleteCutoffDate = text(deleteCutoffDate);
    }

    private static String text(String value) { return value == null ? "" : value; }
}
