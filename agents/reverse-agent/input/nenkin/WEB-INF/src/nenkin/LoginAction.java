package nenkin;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public final class LoginAction extends common.LoginAction {
	public String perform(HttpServletRequest request, HttpServletResponse response) throws Exception {
		request.getSession().removeAttribute(NenkinBaseAction.STAFF_CONTEXT_KEY);
		request.getSession().removeAttribute(NenkinBaseAction.CSRF_TOKEN_KEY);
		String next = super.perform(request, response);
		if ("./JSP/MENU/Login.jsp".equals(next)) return next;
		return new MenuViewAction().perform(request, response);
	}
}

