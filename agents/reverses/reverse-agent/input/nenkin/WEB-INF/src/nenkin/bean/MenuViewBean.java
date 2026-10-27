package nenkin.bean;

import java.io.Serializable;

public final class MenuViewBean implements Serializable {
	private static final long serialVersionUID = 1L;
	private String staffNo = "-";
	private String staffName = "未確認";
	public String getStaffNo() { return staffNo; }
	public void setStaffNo(String value) { staffNo = value == null ? "-" : value; }
	public String getStaffName() { return staffName; }
	public void setStaffName(String value) { staffName = value == null ? "未確認" : value; }
}

