package nenkin;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public final class StaffViewAction extends NenkinBaseAction {
	public String perform(HttpServletRequest request, HttpServletResponse response) {
		return new MenuViewAction().perform(request, response);
	}
}

