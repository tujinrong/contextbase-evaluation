package nenkin;

import java.util.Locale;
import java.util.Collections;
import java.util.UUID;
import java.text.Normalizer;
import java.net.URLEncoder;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpSession;
import javax.servlet.http.HttpServletResponse;

import common.CommonAction;
import common.CommonConst;
import common.bean.LoginInfoBean;
import nenkin.bean.PensionViewBean;
import nenkin.model.PensionReservation;
import nenkin.model.StaffContext;
import nenkin.service.ReferenceDataService;
import nenkin.util.AnsiTextUtil;
import nenkin.util.DateUtil;

abstract class NenkinBaseAction extends CommonAction {
	static final String LOGIN_JSP = "./JSP/MENU/Login.jsp";
	// 既存Actionの未認証時戻り値。手入力画面は廃止し、ログイン画面へ戻す。
	static final String STAFF_JSP = LOGIN_JSP;
	static final String MENU_JSP = "./JSP/NENKIN/Menu.jsp";
	static final String PENSION_JSP = "./JSP/NENKIN/Pension.jsp";
	static final String LOOKUP_JSP = "./JSP/NENKIN/Lookup.jsp";
	static final String REPORT_JSP = "./JSP/NENKIN/Report.jsp";
	static final String EXCEL_JSP = "./JSP/NENKIN/Excel.jsp";
	static final String BATCH_JSP = "./JSP/NENKIN/Batch.jsp";
	static final String STAFF_CONTEXT_KEY = "NENKIN_STAFF_CONTEXT";
	static final String CSRF_TOKEN_KEY = "NENKIN_CSRF_TOKEN";
	static final String INVALID_REQUEST_MESSAGE = "画面の有効期限が切れました。メニューから操作しなおしてください。";

	void setViewBean(HttpSession session, Object bean) {
		session.setAttribute(CommonConst.SS_JSP_BEAN, bean);
	}

	void setSubWindowBean(HttpSession session, Object bean) {
		session.setAttribute(CommonConst.SS_SUB_JSP_BEAN, bean);
	}

	StaffContext currentStaff(HttpSession session) {
		Object value = session.getAttribute(STAFF_CONTEXT_KEY);
		return value instanceof StaffContext ? (StaffContext) value : null;
	}

	boolean requireStaff(HttpServletRequest request) {
		HttpSession session = request.getSession();
		if (currentStaff(session) != null) {
			ensureCsrfToken(session);
			return true;
		}

		Object value = session.getAttribute(CommonConst.SS_LOGIN_INFO_BEAN);
		if (value instanceof LoginInfoBean && ((LoginInfoBean) value).isログイン可否()) {
			String staffNo = trim(((LoginInfoBean) value).get職員番号());
			if (staffNo.matches("[0-9]{1,8}")) {
				StaffContext staff = ReferenceDataService.getInstance()
						.verifyStaff(Integer.parseInt(staffNo));
				if (staff != null) {
					session.setAttribute(STAFF_CONTEXT_KEY, staff);
					ensureCsrfToken(session);
					return true;
				}
			}
			session.removeAttribute(CommonConst.SS_LOGIN_INFO_BEAN);
			session.setAttribute(CommonConst.ERROR_MSG_LIST, Collections.singletonList(
					"ログイン職員番号が職員名簿に存在しません。管理者に確認してください。"));
		} else {
			session.setAttribute(CommonConst.ERROR_MSG_LIST,
					Collections.singletonList("ログインしてください。"));
		}
		session.removeAttribute(STAFF_CONTEXT_KEY);
		session.removeAttribute(CSRF_TOKEN_KEY);
		return false;
	}

	String ensureCsrfToken(HttpSession session) {
		Object current = session.getAttribute(CSRF_TOKEN_KEY);
		if (current instanceof String && ((String) current).length() > 0) return (String) current;
		String token = UUID.randomUUID().toString();
		session.setAttribute(CSRF_TOKEN_KEY, token);
		return token;
	}

	boolean isAuthorizedMutation(HttpServletRequest request) {
		if (!"POST".equalsIgnoreCase(request.getMethod())) return false;
		Object expected = request.getSession().getAttribute(CSRF_TOKEN_KEY);
		String actual = request.getParameter("CSRF_TOKEN");
		return expected instanceof String && expected.equals(actual);
	}

	boolean isRestrictedStaff(StaffContext staff) {
		if (staff == null || staff.getBranchNo() != 75) return false;
		try { return Integer.parseInt(trim(staff.getRoleCode())) < 3000; }
		catch (NumberFormatException e) { return true; }
	}

	boolean sameReservationKey(PensionReservation first, PensionReservation second) {
		if (first == null || second == null) return false;
		String firstKana = Normalizer.normalize(trim(first.getKanaName()), Normalizer.Form.NFKC).toUpperCase(Locale.ROOT);
		String secondKana = Normalizer.normalize(trim(second.getKanaName()), Normalizer.Form.NFKC).toUpperCase(Locale.ROOT);
		return firstKana.equals(secondKana) && phoneDigits(first.getPhoneNumber()).equals(phoneDigits(second.getPhoneNumber()));
	}

	private String phoneDigits(String value) {
		String normalized = Normalizer.normalize(trim(value), Normalizer.Form.NFKC);
		StringBuilder digits = new StringBuilder();
		for (int i = 0; i < normalized.length(); i++) {
			char c = normalized.charAt(i);
			if (c >= '0' && c <= '9') digits.append(c);
		}
		return digits.toString();
	}

	String trim(String value) { return value == null ? "" : value.trim(); }

	Integer integerOrNull(String value) {
		String text = trim(value);
		if (text.length() == 0) return null;
		try { int result = Integer.parseInt(text); return result > 0 ? Integer.valueOf(result) : null; }
		catch (NumberFormatException e) { return null; }
	}

	int integerOrDefault(String value, int defaultValue) {
		Integer result = integerOrNull(value);
		return result == null ? defaultValue : result.intValue();
	}

	boolean isChecked(HttpServletRequest request, String name) {
		String value = request.getParameter(name);
		return value != null && ("1".equals(value) || "true".equalsIgnoreCase(value) || "on".equalsIgnoreCase(value));
	}

	PensionReservation readReservation(HttpServletRequest request) {
		PensionReservation value = new PensionReservation();
		value.setBranchNo(integerOrNull(request.getParameter("BRANCH_NO")));
		value.setCustomerNo(integerOrNull(request.getParameter("CUSTOMER_NO")));
		value.setStaffCode(integerOrNull(request.getParameter("STAFF_CODE")));
		value.setCustomerName(trim(request.getParameter("CUSTOMER_NAME")));
		value.setKanaName(trim(request.getParameter("KANA_NAME")));
		value.setGender(trim(request.getParameter("GENDER")));
		value.setAddress(trim(request.getParameter("ADDRESS")));
		value.setPhoneNumber(trim(request.getParameter("PHONE_NUMBER")));
		value.setBirthDate(trim(request.getParameter("BIRTH_DATE")));
		value.setClaimStatus(trim(request.getParameter("CLAIM_STATUS")));
		value.setClaimScheduledDate(trim(request.getParameter("CLAIM_SCHEDULED_DATE")));
		value.setPlannedAge(integerOrNull(request.getParameter("PLANNED_AGE")));
		value.setReservationRequestDate(trim(request.getParameter("RESERVATION_REQUEST_DATE")));
		value.setDataUpdateDate(trim(request.getParameter("DATA_UPDATE_DATE")));
		value.setNotes(trim(request.getParameter("NOTES")));
		value.setSpouseName(trim(request.getParameter("SPOUSE_NAME")));
		value.setHasBenefit(trim(request.getParameter("HAS_BENEFIT")));
		value.setSpouseBirthDate(trim(request.getParameter("SPOUSE_BIRTH_DATE")));
		value.setNationalPension(isChecked(request, "NATIONAL_PENSION"));
		value.setEmployeePension(isChecked(request, "EMPLOYEE_PENSION"));
		value.setMutualAidPension(isChecked(request, "MUTUAL_AID_PENSION"));
		value.setEmployeePensionFund(isChecked(request, "EMPLOYEE_PENSION_FUND"));
		value.setNationalPensionFund(isChecked(request, "NATIONAL_PENSION_FUND"));
		value.setSixMonthCheck(isChecked(request, "SIX_MONTH_CHECK"));
		return value;
	}

	String validateAndNormalize(PensionReservation value) {
		if (value.getBranchNo() == null) return "店番は必ず入力してください";
		if (value.getKanaName().length() == 0) return "フリガナを入力してください。";
		if (value.getPhoneNumber().length() == 0) return "電話番号を入力してください。";
		String error;
		error = normalizeDate(value.getBirthDate(), "生年月日は和暦または西暦の日付で入力してください。");
		if (error != null) return error; else value.setBirthDate(normalizedDate);
		error = normalizeDate(value.getSpouseBirthDate(), "配偶者生年月日は和暦または西暦の日付で入力してください。");
		if (error != null) return error; else value.setSpouseBirthDate(normalizedDate);
		error = normalizeDate(value.getClaimScheduledDate(), "請求予定日は和暦または西暦の日付で入力してください。");
		if (error != null) return error; else value.setClaimScheduledDate(normalizedDate);
		error = normalizeDate(value.getReservationRequestDate(), "予約徴求日は和暦または西暦の日付で入力してください。");
		if (error != null) return error; else value.setReservationRequestDate(normalizedDate);
		if (!AnsiTextUtil.isValidNotes(value.getNotes())) return "Excel出力した際、文字が途中で切れてしまいます。編集しなおしてください";
		return null;
	}

	private String normalizedDate = "";
	private String normalizeDate(String value, String message) {
		if (trim(value).length() == 0) { normalizedDate = ""; return null; }
		try { normalizedDate = DateUtil.toIsoDate(value); return null; }
		catch (IllegalArgumentException e) { return message; }
	}

	PensionViewBean pensionBean(PensionReservation reservation, String message, boolean existing, HttpSession session) {
		PensionViewBean bean = new PensionViewBean();
		bean.setReservation(reservation);
		bean.setMessage(message);
		bean.setExisting(existing);
		StaffContext staff = currentStaff(session);
		if (staff != null) {
			bean.setStaffNo(String.format(Locale.ROOT, "%08d", Integer.valueOf(staff.getStaffNo())));
			bean.setStaffName(staff.getStaffName());
		}
		return bean;
	}

	void writeDownload(HttpServletResponse response, String fileName, String contentType, byte[] content) throws Exception {
		String encoded = URLEncoder.encode(fileName, "UTF-8").replace("+", "%20");
		response.reset();
		response.setContentType(contentType);
		response.setHeader("Content-Disposition", "attachment; filename=download; filename*=UTF-8''" + encoded);
		response.setContentLength(content.length);
		response.getOutputStream().write(content);
		response.getOutputStream().flush();
	}
}
