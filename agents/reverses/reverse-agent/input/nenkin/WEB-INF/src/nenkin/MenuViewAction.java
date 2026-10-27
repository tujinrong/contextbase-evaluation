package nenkin;

import java.util.Locale;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import nenkin.bean.MenuViewBean;
import nenkin.model.StaffContext;

public final class MenuViewAction extends NenkinBaseAction {
	public String perform(HttpServletRequest request, HttpServletResponse response) {
		if (!requireStaff(request)) return STAFF_JSP;
		MenuViewBean bean = new MenuViewBean();
		StaffContext staff = currentStaff(request.getSession());
		if (staff != null) { bean.setStaffNo(String.format(Locale.ROOT, "%08d", Integer.valueOf(staff.getStaffNo()))); bean.setStaffName(staff.getStaffName()); }
		setViewBean(request.getSession(), bean);
		return MENU_JSP;
	}
}
