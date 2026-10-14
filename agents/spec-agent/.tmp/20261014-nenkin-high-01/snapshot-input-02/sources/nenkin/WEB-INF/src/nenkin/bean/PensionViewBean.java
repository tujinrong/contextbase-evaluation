package nenkin.bean;

import java.io.Serializable;
import nenkin.model.PensionReservation;

public final class PensionViewBean implements Serializable {
	private static final long serialVersionUID = 1L;
	private PensionReservation reservation = new PensionReservation();
	private String message = "";
	private String staffNo = "-";
	private String staffName = "未確認";
	private boolean existing;
	public PensionReservation getReservation() { return reservation; }
	public void setReservation(PensionReservation value) { reservation = value == null ? new PensionReservation() : value; }
	public String getMessage() { return message; }
	public void setMessage(String value) { message = value == null ? "" : value; }
	public String getStaffNo() { return staffNo; }
	public void setStaffNo(String value) { staffNo = value == null ? "-" : value; }
	public String getStaffName() { return staffName; }
	public void setStaffName(String value) { staffName = value == null ? "未確認" : value; }
	public boolean isExisting() { return existing; }
	public void setExisting(boolean value) { existing = value; }
}

