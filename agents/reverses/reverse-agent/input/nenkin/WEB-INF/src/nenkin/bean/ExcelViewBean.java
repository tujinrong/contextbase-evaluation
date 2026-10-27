package nenkin.bean;

import java.io.Serializable;

public final class ExcelViewBean implements Serializable {
	private static final long serialVersionUID = 1L;
	private String branchNo = "";
	private String branchName = "";
	private String message = "";
	public String getBranchNo() { return branchNo; }
	public void setBranchNo(String value) { branchNo = value == null ? "" : value; }
	public String getBranchName() { return branchName; }
	public void setBranchName(String value) { branchName = value == null ? "" : value; }
	public String getMessage() { return message; }
	public void setMessage(String value) { message = value == null ? "" : value; }
}

