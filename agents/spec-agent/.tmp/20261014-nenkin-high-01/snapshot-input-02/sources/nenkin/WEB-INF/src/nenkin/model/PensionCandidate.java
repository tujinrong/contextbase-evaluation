package nenkin.model;

import java.io.Serializable;

public class PensionCandidate implements Serializable {
    private static final long serialVersionUID = 1L;

    private int branchNo;
    private int customerNo;
    private String kanaName = "";
    private String customerName = "";
    private String phoneNumber = "";
    private String birthDate = "";

    public PensionCandidate() {
    }

    public PensionCandidate(int branchNo, int customerNo, String kanaName,
            String customerName, String phoneNumber, String birthDate) {
        this.branchNo = branchNo;
        this.customerNo = customerNo;
        this.kanaName = text(kanaName);
        this.customerName = text(customerName);
        this.phoneNumber = text(phoneNumber);
        this.birthDate = text(birthDate);
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

    private static String text(String value) { return value == null ? "" : value; }
}
