package nenkin.model;

import java.io.Serializable;

public class StaffLookupItem implements Serializable {
    private static final long serialVersionUID = 1L;

    private int staffCode;
    private String staffName = "";
    private String staffKanaName = "";
    private int branchNo;
    private String branchName = "";
    private String roleCode = "";

    public StaffLookupItem() {
    }

    public StaffLookupItem(int staffCode, String staffName, int branchNo, String branchName) {
        this(staffCode, staffName, "", branchNo, branchName, "");
    }

    public StaffLookupItem(int staffCode, String staffName, String staffKanaName,
            int branchNo, String branchName) {
        this(staffCode, staffName, staffKanaName, branchNo, branchName, "");
    }

    public StaffLookupItem(int staffCode, String staffName, String staffKanaName,
            int branchNo, String branchName, String roleCode) {
        this.staffCode = staffCode;
        this.staffName = staffName == null ? "" : staffName;
        this.staffKanaName = staffKanaName == null ? "" : staffKanaName;
        this.branchNo = branchNo;
        this.branchName = branchName == null ? "" : branchName;
        this.roleCode = roleCode == null ? "" : roleCode;
    }

    public int getStaffCode() {
        return staffCode;
    }

    public void setStaffCode(int staffCode) {
        this.staffCode = staffCode;
    }

    public int getStaffNo() {
        return staffCode;
    }

    public void setStaffNo(int staffNo) {
        this.staffCode = staffNo;
    }

    public String getStaffName() {
        return staffName;
    }

    public void setStaffName(String staffName) {
        this.staffName = staffName == null ? "" : staffName;
    }

    public String getStaffKanaName() {
        return staffKanaName;
    }

    public void setStaffKanaName(String staffKanaName) {
        this.staffKanaName = staffKanaName == null ? "" : staffKanaName;
    }

    public int getBranchNo() {
        return branchNo;
    }

    public void setBranchNo(int branchNo) {
        this.branchNo = branchNo;
    }

    public String getBranchName() {
        return branchName;
    }

    public void setBranchName(String branchName) {
        this.branchName = branchName == null ? "" : branchName;
    }

    public String getRoleCode() {
        return roleCode;
    }

    public void setRoleCode(String roleCode) {
        this.roleCode = roleCode == null ? "" : roleCode;
    }
}
