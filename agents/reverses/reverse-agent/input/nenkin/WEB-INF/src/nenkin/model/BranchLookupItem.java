package nenkin.model;

import java.io.Serializable;

public class BranchLookupItem implements Serializable {
    private static final long serialVersionUID = 1L;

    private int branchNo;
    private String branchName = "";

    public BranchLookupItem() {
    }

    public BranchLookupItem(int branchNo, String branchName) {
        this.branchNo = branchNo;
        this.branchName = branchName == null ? "" : branchName;
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
}
