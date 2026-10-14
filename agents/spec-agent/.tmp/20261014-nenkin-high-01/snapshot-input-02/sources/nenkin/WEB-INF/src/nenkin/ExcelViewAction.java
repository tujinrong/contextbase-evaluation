package nenkin;
import javax.servlet.http.HttpServletRequest;import javax.servlet.http.HttpServletResponse;import nenkin.bean.ExcelViewBean;
public final class ExcelViewAction extends NenkinBaseAction { public String perform(HttpServletRequest request,HttpServletResponse response){if(!requireStaff(request))return STAFF_JSP;setViewBean(request.getSession(),new ExcelViewBean());return EXCEL_JSP;} }
