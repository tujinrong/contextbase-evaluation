package nenkin;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import nenkin.model.PensionReservation;
import nenkin.service.PensionRepository;

/** フリガナ+電話番号の正規化キーで、選択した予約を確実に読み込む。 */
public final class PensionLoadAction extends NenkinBaseAction {
	public String perform(HttpServletRequest request, HttpServletResponse response) {
		if (!requireStaff(request)) return STAFF_JSP;
		PensionReservation input = readReservation(request);
		String kana = trim(request.getParameter("LOOKUP_KANA"));
		String phone = trim(request.getParameter("LOOKUP_PHONE"));
		if (kana.length() == 0) kana = input.getKanaName();
		if (phone.length() == 0) phone = input.getPhoneNumber();
		PensionRepository repository = PensionRepository.getInstance();
		PensionReservation found = repository.findByKanaAndPhone(kana, phone);
		if (found == null) {
			Integer branch = integerOrNull(request.getParameter("BRANCH_NO"));
			Integer customer = integerOrNull(request.getParameter("CUSTOMER_NO"));
			PensionReservation master = branch == null || customer == null ? null
					: repository.findByCustomer(branch.intValue(), customer.intValue());
			setViewBean(request.getSession(), pensionBean(master == null ? input : master,
					master == null ? "" : "顧客基本表から読み込みました。", false,
					request.getSession()));
		} else {
			setViewBean(request.getSession(), pensionBean(found, "既存データを読み込みました。", true, request.getSession()));
		}
		return PENSION_JSP;
	}
}
