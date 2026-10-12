package nenkin.bean;

import java.io.Serializable;

public final class BatchViewBean implements Serializable {
	private static final long serialVersionUID = 1L;
	private String staffNo = "";
	private boolean includeNew;
	private boolean includeChanged;
	private boolean includeDeleted;
	private String dailyDate = "";
	private String monthStart = "";
	private String monthEnd = "";
	private String deleteCutoffDate = "";
	private String message = "";
	public String getStaffNo() { return staffNo; }
	public void setStaffNo(String value) { staffNo = value == null ? "" : value; }
	public boolean isIncludeNew() { return includeNew; }
	public void setIncludeNew(boolean value) { includeNew = value; }
	public boolean isIncludeChanged() { return includeChanged; }
	public void setIncludeChanged(boolean value) { includeChanged = value; }
	public boolean isIncludeDeleted() { return includeDeleted; }
	public void setIncludeDeleted(boolean value) { includeDeleted = value; }
	public String getDailyDate() { return dailyDate; }
	public void setDailyDate(String value) { dailyDate = value == null ? "" : value; }
	public String getMonthStart() { return monthStart; }
	public void setMonthStart(String value) { monthStart = value == null ? "" : value; }
	public String getMonthEnd() { return monthEnd; }
	public void setMonthEnd(String value) { monthEnd = value == null ? "" : value; }
	public String getDeleteCutoffDate() { return deleteCutoffDate; }
	public void setDeleteCutoffDate(String value) { deleteCutoffDate = value == null ? "" : value; }
	public String getMessage() { return message; }
	public void setMessage(String value) { message = value == null ? "" : value; }
}
