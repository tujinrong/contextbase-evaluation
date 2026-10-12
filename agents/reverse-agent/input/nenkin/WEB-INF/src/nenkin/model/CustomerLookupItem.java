package nenkin.model;

import java.io.Serializable;

public class CustomerLookupItem implements Serializable {
    private static final long serialVersionUID = 1L;

    private int branchNo;
    private int customerNo;
    private String kanaName = "";
    private String customerName = "";
    private String phoneNumber = "";
    private String birthDate = "";
    private String branchName = "";
    private int staffCode;

    public CustomerLookupItem() {
    }

    public CustomerLookupItem(int branchNo, int customerNo, String kanaName,
            String customerName, String phoneNumber, String birthDate,
            String branchName, int staffCode) {
        this.branchNo = branchNo;
        this.customerNo = customerNo;
        this.kanaName = text(kanaName);
        this.customerName = text(customerName);
        this.phoneNumber = text(phoneNumber);
        this.birthDate = text(birthDate);
        this.branchName = text(branchName);
        this.staffCode = staffCode;
    }

    public int getBranchNo() { return branchNo; }
    public void setBranchNo(int branchNo) { this.branchNo = branchNo; }
    public int getCustomerNo() { return customerNo; }
    public void setCustomerNo(int customerNo) { this.customerNo = customerNo; }
    public String getKanaName() { return kanaName; }
    public void setKanaName(String kanaName) { this.kanaName = text(kanaName); }
    public String getCustomerName() { return customerName; }
    public void setCustomerName(String customerName) { this.customerName = text(customerName); }
    public String getPhoneNumber() { return phoneNumber; }
    public void setPhoneNumber(String phoneNumber) { this.phoneNumber = text(phoneNumber); }
    public String getBirthDate() { return birthDate; }
    public void setBirthDate(String birthDate) { this.birthDate = text(birthDate); }
    public String getBranchName() { return branchName; }
    public void setBranchName(String branchName) { this.branchName = text(branchName); }
    public int getStaffCode() { return staffCode; }
    public void setStaffCode(int staffCode) { this.staffCode = staffCode; }

    private static String text(String value) { return value == null ? "" : value; }
}
