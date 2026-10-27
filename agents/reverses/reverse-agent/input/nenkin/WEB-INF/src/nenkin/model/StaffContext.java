package nenkin.model;

import java.io.Serializable;

public class StaffContext implements Serializable {
    private static final long serialVersionUID = 1L;

    private int staffNo;
    private String staffName = "";
    private int branchNo;
    private String roleCode = "";

    public StaffContext() {
    }

    public StaffContext(int staffNo, String staffName, int branchNo) {
        this(staffNo, staffName, branchNo, "");
    }

    public StaffContext(int staffNo, String staffName, int branchNo, String roleCode) {
        this.staffNo = staffNo;
        this.staffName = staffName == null ? "" : staffName;
        this.branchNo = branchNo;
        this.roleCode = roleCode == null ? "" : roleCode;
    }

    public int getStaffNo() {
        return staffNo;
    }

    public void setStaffNo(int staffNo) {
        this.staffNo = staffNo;
    }

    public String getStaffName() {
        return staffName;
    }

    public void setStaffName(String staffName) {
        this.staffName = staffName == null ? "" : staffName;
    }

    public int getBranchNo() {
        return branchNo;
    }

    public void setBranchNo(int branchNo) {
        this.branchNo = branchNo;
    }

    public String getRoleCode() {
        return roleCode;
    }

    public void setRoleCode(String roleCode) {
        this.roleCode = roleCode == null ? "" : roleCode;
    }
}
