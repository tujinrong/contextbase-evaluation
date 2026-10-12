package nenkin.model;

import java.io.Serializable;

/**
 * 年金予約の入力・帳票共通モデル。
 *
 * <p>日付はサービス境界で yyyy-MM-dd に正規化する。</p>
 */
public class PensionReservation implements Serializable {
    private static final long serialVersionUID = 1L;

    private Integer branchNo;
    private String branchName = "";
    private Integer customerNo;
    private Integer staffCode;
    private String customerName = "";
    private String kanaName = "";
    private String gender = "";
    private String address = "";
    private String phoneNumber = "";
    private String birthDate = "";
    private String claimStatus = "";
    private String claimScheduledDate = "";
    private Integer plannedAge;
    private String reservationRequestDate = "";
    private String dataUpdateDate = "";
    private String notes = "";
    private String spouseName = "";
    private String hasBenefit = "";
    private String spouseBirthDate = "";
    private String pensionType = "";
    private boolean nationalPension;
    private boolean employeePension;
    private boolean mutualAidPension;
    private boolean employeePensionFund;
    private boolean nationalPensionFund;
    private boolean sixMonthCheck;

    public PensionReservation() {
    }

    public PensionReservation(PensionReservation source) {
        if (source == null) {
            return;
        }
        branchNo = source.branchNo;
        branchName = source.branchName;
        customerNo = source.customerNo;
        staffCode = source.staffCode;
        customerName = source.customerName;
        kanaName = source.kanaName;
        gender = source.gender;
        address = source.address;
        phoneNumber = source.phoneNumber;
        birthDate = source.birthDate;
        claimStatus = source.claimStatus;
        claimScheduledDate = source.claimScheduledDate;
        plannedAge = source.plannedAge;
        reservationRequestDate = source.reservationRequestDate;
        dataUpdateDate = source.dataUpdateDate;
        notes = source.notes;
        spouseName = source.spouseName;
        hasBenefit = source.hasBenefit;
        spouseBirthDate = source.spouseBirthDate;
        pensionType = source.pensionType;
        nationalPension = source.nationalPension;
        employeePension = source.employeePension;
        mutualAidPension = source.mutualAidPension;
        employeePensionFund = source.employeePensionFund;
        nationalPensionFund = source.nationalPensionFund;
        sixMonthCheck = source.sixMonthCheck;
    }

    public PensionReservation copy() {
        return new PensionReservation(this);
    }

    public Integer getBranchNo() {
        return branchNo;
    }

    public void setBranchNo(Integer branchNo) {
        this.branchNo = branchNo;
    }

    public String getBranchName() {
        return branchName;
    }

    public void setBranchName(String branchName) {
        this.branchName = valueOrEmpty(branchName);
    }

    public Integer getCustomerNo() {
        return customerNo;
    }

    public void setCustomerNo(Integer customerNo) {
        this.customerNo = customerNo;
    }

    public Integer getStaffCode() {
        return staffCode;
    }

    public void setStaffCode(Integer staffCode) {
        this.staffCode = staffCode;
    }

    public String getCustomerName() {
        return customerName;
    }

    public void setCustomerName(String customerName) {
        this.customerName = valueOrEmpty(customerName);
    }

    public String getKanaName() {
        return kanaName;
    }

    public void setKanaName(String kanaName) {
        this.kanaName = valueOrEmpty(kanaName);
    }

    public String getGender() {
        return gender;
    }

    public void setGender(String gender) {
        this.gender = valueOrEmpty(gender);
    }

    public String getAddress() {
        return address;
    }

    public void setAddress(String address) {
        this.address = valueOrEmpty(address);
    }

    public String getPhoneNumber() {
        return phoneNumber;
    }

    public void setPhoneNumber(String phoneNumber) {
        this.phoneNumber = valueOrEmpty(phoneNumber);
    }

    public String getBirthDate() {
        return birthDate;
    }

    public void setBirthDate(String birthDate) {
        this.birthDate = valueOrEmpty(birthDate);
    }

    public String getClaimStatus() {
        return claimStatus;
    }

    public void setClaimStatus(String claimStatus) {
        this.claimStatus = valueOrEmpty(claimStatus);
    }

    public String getClaimScheduledDate() {
        return claimScheduledDate;
    }

    public void setClaimScheduledDate(String claimScheduledDate) {
        this.claimScheduledDate = valueOrEmpty(claimScheduledDate);
    }

    public Integer getPlannedAge() {
        return plannedAge;
    }

    public void setPlannedAge(Integer plannedAge) {
        this.plannedAge = plannedAge;
    }

    public String getReservationRequestDate() {
        return reservationRequestDate;
    }

    public void setReservationRequestDate(String reservationRequestDate) {
        this.reservationRequestDate = valueOrEmpty(reservationRequestDate);
    }

    public String getDataUpdateDate() {
        return dataUpdateDate;
    }

    public void setDataUpdateDate(String dataUpdateDate) {
        this.dataUpdateDate = valueOrEmpty(dataUpdateDate);
    }

    public String getNotes() {
        return notes;
    }

    public void setNotes(String notes) {
        this.notes = valueOrEmpty(notes);
    }

    public String getSpouseName() {
        return spouseName;
    }

    public void setSpouseName(String spouseName) {
        this.spouseName = valueOrEmpty(spouseName);
    }

    public String getHasBenefit() {
        return hasBenefit;
    }

    public void setHasBenefit(String hasBenefit) {
        this.hasBenefit = valueOrEmpty(hasBenefit);
    }

    public String getSpouseBirthDate() {
        return spouseBirthDate;
    }

    public void setSpouseBirthDate(String spouseBirthDate) {
        this.spouseBirthDate = valueOrEmpty(spouseBirthDate);
    }

    public String getPensionType() {
        return pensionType;
    }

    public void setPensionType(String pensionType) {
        this.pensionType = valueOrEmpty(pensionType);
    }

    public boolean isNationalPension() {
        return nationalPension;
    }

    public void setNationalPension(boolean nationalPension) {
        this.nationalPension = nationalPension;
    }

    public boolean isEmployeePension() {
        return employeePension;
    }

    public void setEmployeePension(boolean employeePension) {
        this.employeePension = employeePension;
    }

    public boolean isMutualAidPension() {
        return mutualAidPension;
    }

    public void setMutualAidPension(boolean mutualAidPension) {
        this.mutualAidPension = mutualAidPension;
    }

    public boolean isEmployeePensionFund() {
        return employeePensionFund;
    }

    public void setEmployeePensionFund(boolean employeePensionFund) {
        this.employeePensionFund = employeePensionFund;
    }

    public boolean isNationalPensionFund() {
        return nationalPensionFund;
    }

    public void setNationalPensionFund(boolean nationalPensionFund) {
        this.nationalPensionFund = nationalPensionFund;
    }

    public boolean isSixMonthCheck() {
        return sixMonthCheck;
    }

    public void setSixMonthCheck(boolean sixMonthCheck) {
        this.sixMonthCheck = sixMonthCheck;
    }

    private static String valueOrEmpty(String value) {
        return value == null ? "" : value;
    }
}
