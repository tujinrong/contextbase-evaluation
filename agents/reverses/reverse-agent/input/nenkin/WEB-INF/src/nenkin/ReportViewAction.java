package nenkin;
import javax.servlet.http.HttpServletRequest;import javax.servlet.http.HttpServletResponse;import nenkin.bean.ReportViewBean;
public final class ReportViewAction extends NenkinBaseAction { public String perform(HttpServletRequest request,HttpServletResponse response){if(!requireStaff(request))return STAFF_JSP;setViewBean(request.getSession(),new ReportViewBean());return REPORT_JSP;} }
