package nenkin.bean;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import nenkin.model.BranchLookupItem;
import nenkin.model.CustomerLookupItem;
import nenkin.model.StaffLookupItem;

public final class LookupViewBean implements Serializable {
	private static final long serialVersionUID = 1L;
	private String target = "customer";
	private String keyword = "";
	private String branchNo = "";
	private String nameKeyword = "";
	private String phoneKeyword = "";
	private int page = 1;
	private int pageSize = 20;
	private int totalCount;
	private List<BranchLookupItem> branches = new ArrayList<BranchLookupItem>();
	private List<CustomerLookupItem> customers = new ArrayList<CustomerLookupItem>();
	private List<StaffLookupItem> staff = new ArrayList<StaffLookupItem>();
	public String getTarget() { return target; }
	public void setTarget(String value) { target = value == null ? "customer" : value; }
	public String getKeyword() { return keyword; }
	public void setKeyword(String value) { keyword = value == null ? "" : value; }
	public String getBranchNo() { return branchNo; }
	public void setBranchNo(String value) { branchNo = value == null ? "" : value; }
	public String getNameKeyword() { return nameKeyword; }
	public void setNameKeyword(String value) { nameKeyword = value == null ? "" : value; }
	public String getPhoneKeyword() { return phoneKeyword; }
	public void setPhoneKeyword(String value) { phoneKeyword = value == null ? "" : value; }
	public int getPage() { return page; }
	public void setPage(int value) { page = value < 1 ? 1 : value; }
	public int getPageSize() { return pageSize; }
	public int getTotalCount() { return totalCount; }
	public void setTotalCount(int value) { totalCount = value; }
	public int getTotalPages() { return Math.max(1, (totalCount + pageSize - 1) / pageSize); }
	public int getFirstRow() { return totalCount == 0 ? 0 : (page - 1) * pageSize + 1; }
	public int getLastRow() { return Math.min(page * pageSize, totalCount); }
	public List<BranchLookupItem> getBranches() { return branches; }
	public void setBranches(List<BranchLookupItem> value) { branches = value == null ? new ArrayList<BranchLookupItem>() : value; }
	public List<CustomerLookupItem> getCustomers() { return customers; }
	public void setCustomers(List<CustomerLookupItem> value) { customers = value == null ? new ArrayList<CustomerLookupItem>() : value; }
	public List<StaffLookupItem> getStaff() { return staff; }
	public void setStaff(List<StaffLookupItem> value) { staff = value == null ? new ArrayList<StaffLookupItem>() : value; }
}

