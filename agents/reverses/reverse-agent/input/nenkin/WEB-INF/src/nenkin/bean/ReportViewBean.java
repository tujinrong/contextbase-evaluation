package nenkin.bean;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import nenkin.model.PensionReservation;

public final class ReportViewBean implements Serializable {
	private static final long serialVersionUID = 1L;
	private boolean useBranchRange;
	private String branchFrom = "";
	private String branchTo = "";
	private int sortType = 1;
	private boolean preview;
	private String message = "";
	private List<PensionReservation> rows = new ArrayList<PensionReservation>();
	public boolean isUseBranchRange() { return useBranchRange; }
	public void setUseBranchRange(boolean value) { useBranchRange = value; }
	public String getBranchFrom() { return branchFrom; }
	public void setBranchFrom(String value) { branchFrom = value == null ? "" : value; }
	public String getBranchTo() { return branchTo; }
	public void setBranchTo(String value) { branchTo = value == null ? "" : value; }
	public int getSortType() { return sortType; }
	public void setSortType(int value) { sortType = value; }
	public boolean isPreview() { return preview; }
	public void setPreview(boolean value) { preview = value; }
	public String getMessage() { return message; }
	public void setMessage(String value) { message = value == null ? "" : value; }
	public List<PensionReservation> getRows() { return rows; }
	public void setRows(List<PensionReservation> value) { rows = value == null ? new ArrayList<PensionReservation>() : value; }
}

