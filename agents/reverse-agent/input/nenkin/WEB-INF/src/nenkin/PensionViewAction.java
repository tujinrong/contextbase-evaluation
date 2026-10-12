package nenkin;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import nenkin.service.PensionRepository;

public class PensionViewAction extends NenkinBaseAction {
	public String perform(HttpServletRequest request, HttpServletResponse response) {
		if (!requireStaff(request)) return STAFF_JSP;
		setViewBean(request.getSession(), pensionBean(PensionRepository.getInstance().createEmpty(currentStaff(request.getSession())), "", false, request.getSession()));
		return PENSION_JSP;
	}
}
