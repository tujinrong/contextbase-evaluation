package nenkin.bean;

import java.io.Serializable;

/** 旧セッションのデシリアライズ互換用。職員番号入力画面では使用しない。 */
public final class StaffViewBean implements Serializable {
	private static final long serialVersionUID = 1L;
	private String staffNo = "";
	private String message = "";
	public String getStaffNo() { return staffNo; }
	public void setStaffNo(String value) { staffNo = value == null ? "" : value; }
	public String getMessage() { return message; }
	public void setMessage(String value) { message = value == null ? "" : value; }
}
