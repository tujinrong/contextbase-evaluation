package nenkin;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import nenkin.model.PensionReservation;
import nenkin.model.StaffContext;
import nenkin.service.PensionRepository;

public final class PensionSaveAction extends NenkinBaseAction {
	public String perform(HttpServletRequest request, HttpServletResponse response) {
		if (!requireStaff(request)) return STAFF_JSP;
		PensionReservation value = readReservation(request);
		if (!isAuthorizedMutation(request)) {
			setViewBean(request.getSession(), pensionBean(value, INVALID_REQUEST_MESSAGE, false, request.getSession()));
			return PENSION_JSP;
		}
		String error = validateAndNormalize(value);
		if (error != null) {
			boolean existing = PensionRepository.getInstance().findByKanaAndPhone(value.getKanaName(), value.getPhoneNumber()) != null;
			setViewBean(request.getSession(), pensionBean(value, error, existing, request.getSession()));
			return PENSION_JSP;
		}
		PensionRepository repository = PensionRepository.getInstance();
		PensionReservation existing = repository.findByKanaAndPhone(value.getKanaName(), value.getPhoneNumber());
		PensionReservation original = repository.findByKanaAndPhone(
			request.getParameter("ORIGINAL_KANA"), request.getParameter("ORIGINAL_PHONE"));
		if (existing != null && !sameReservationKey(existing, original)) {
			setViewBean(request.getSession(), pensionBean(existing,
				"同じフリガナと電話番号の既存データを読み込みました。内容を確認してから登録してください。",
				true, request.getSession()));
			return PENSION_JSP;
		}
		if (existing == null && original != null) {
			setViewBean(request.getSession(), pensionBean(original,
				"キー項目は変更できません。クリア後に新規データとして入力してください。",
				true, request.getSession()));
			return PENSION_JSP;
		}
		StaffContext staff = currentStaff(request.getSession());
		if (existing != null && isRestrictedStaff(staff)) {
			setViewBean(request.getSession(), pensionBean(existing,
				"権限が不足しています。変更を行う場合には\r\n推進役以上の方が変更してください。",
				true, request.getSession()));
			return PENSION_JSP;
		}
		repository.save(value, Integer.valueOf(staff.getStaffNo()));
		setViewBean(request.getSession(), pensionBean(repository.createEmpty(staff), "登録終了！", false, request.getSession()));
		return PENSION_JSP;
	}
}
