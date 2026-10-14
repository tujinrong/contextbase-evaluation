package nenkin;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import nenkin.model.PensionReservation;
import nenkin.model.StaffContext;
import nenkin.service.PensionRepository;

public final class PensionDeleteAction extends NenkinBaseAction {
	public String perform(HttpServletRequest request, HttpServletResponse response) {
		if (!requireStaff(request)) return STAFF_JSP;
		PensionReservation value = readReservation(request);
		if (!isAuthorizedMutation(request)) { setViewBean(request.getSession(), pensionBean(value, INVALID_REQUEST_MESSAGE, false, request.getSession())); return PENSION_JSP; }
		if (value.getBranchNo() == null) { setViewBean(request.getSession(), pensionBean(value, "店番は必ず入力してください", true, request.getSession())); return PENSION_JSP; }
		if (value.getKanaName().length() == 0 || value.getPhoneNumber().length() == 0) { setViewBean(request.getSession(), pensionBean(value, "削除対象がありません。既存レコードを読み込んでから削除してください。", false, request.getSession())); return PENSION_JSP; }
		PensionRepository repository = PensionRepository.getInstance();
		PensionReservation existing = repository.findByKanaAndPhone(value.getKanaName(), value.getPhoneNumber());
		PensionReservation original = repository.findByKanaAndPhone(request.getParameter("ORIGINAL_KANA"), request.getParameter("ORIGINAL_PHONE"));
		if (existing == null || !sameReservationKey(existing, original)) {
			setViewBean(request.getSession(), pensionBean(existing == null ? value : existing,
				"削除対象を参照画面またはキー入力から読み込んでください。", existing != null, request.getSession()));
			return PENSION_JSP;
		}
		StaffContext staff = currentStaff(request.getSession());
		if (isRestrictedStaff(staff)) {
			setViewBean(request.getSession(), pensionBean(existing,
				"権限が不足しています。削除を行う場合には\r\n推進役以上の方が削除してください。",
				true, request.getSession()));
			return PENSION_JSP;
		}
		boolean deleted = repository.delete(value.getKanaName(), value.getPhoneNumber(), Integer.valueOf(staff.getStaffNo()));
		String message = deleted ? "削除終了！" : "削除対象が見つかりません。";
		setViewBean(request.getSession(), pensionBean(deleted ? repository.createEmpty(staff) : value, message, !deleted, request.getSession()));
		return PENSION_JSP;
	}
}
