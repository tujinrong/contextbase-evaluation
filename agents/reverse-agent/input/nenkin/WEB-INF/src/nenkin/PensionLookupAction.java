package nenkin;

import java.io.PrintWriter;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import nenkin.model.PensionReservation;
import nenkin.service.PensionRepository;
import nenkin.util.DateUtil;
import nenkin.util.HtmlUtil;

public final class PensionLookupAction extends NenkinBaseAction {
	public String perform(HttpServletRequest request, HttpServletResponse response) throws Exception {
		if (!requireStaff(request)) return STAFF_JSP;
		if (!"POST".equalsIgnoreCase(request.getMethod())) {
			response.sendError(HttpServletResponse.SC_METHOD_NOT_ALLOWED);
			return "CSV";
		}
		PensionReservation value;
		if ("key".equals(request.getParameter("LOOKUP_MODE"))) value=PensionRepository.getInstance().findByKanaAndPhone(request.getParameter("KANA_NAME"),request.getParameter("PHONE_NUMBER"));
		else { Integer branch=integerOrNull(request.getParameter("BRANCH_NO")),customer=integerOrNull(request.getParameter("CUSTOMER_NO")); value=branch==null||customer==null?null:PensionRepository.getInstance().findByCustomer(branch.intValue(),customer.intValue()); }
		response.setCharacterEncoding("UTF-8"); response.setContentType("application/json; charset=UTF-8");
		PrintWriter out=response.getWriter(); out.write(value==null?"{\"found\":false}":"{\"found\":true,\"reservation\":"+toJson(value)+"}"); out.flush();
		return "CSV";
	}
	private String toJson(PensionReservation x) {
		StringBuilder b=new StringBuilder("{"); append(b,"branchNo",x.getBranchNo());append(b,"branchName",x.getBranchName());append(b,"customerNo",x.getCustomerNo());append(b,"staffCode",x.getStaffCode());append(b,"customerName",x.getCustomerName());append(b,"kanaName",x.getKanaName());append(b,"gender",x.getGender());append(b,"address",x.getAddress());append(b,"phoneNumber",x.getPhoneNumber());append(b,"birthDate",x.getBirthDate());append(b,"birthDateDisplay",DateUtil.toWarekiDisplay(x.getBirthDate()));append(b,"claimStatus",x.getClaimStatus());append(b,"claimScheduledDate",x.getClaimScheduledDate());append(b,"claimScheduledDateDisplay",DateUtil.toGregorianDisplay(x.getClaimScheduledDate()));append(b,"plannedAge",x.getPlannedAge());append(b,"reservationRequestDate",x.getReservationRequestDate());append(b,"reservationRequestDateDisplay",DateUtil.toGregorianDisplay(x.getReservationRequestDate()));append(b,"dataUpdateDate",x.getDataUpdateDate());append(b,"dataUpdateDateDisplay",DateUtil.toGregorianDisplay(x.getDataUpdateDate()));append(b,"notes",x.getNotes());append(b,"spouseName",x.getSpouseName());append(b,"hasBenefit",x.getHasBenefit());append(b,"spouseBirthDate",x.getSpouseBirthDate());append(b,"spouseBirthDateDisplay",DateUtil.toWarekiDisplay(x.getSpouseBirthDate()));append(b,"pensionType",x.getPensionType());append(b,"nationalPension",Boolean.valueOf(x.isNationalPension()));append(b,"employeePension",Boolean.valueOf(x.isEmployeePension()));append(b,"mutualAidPension",Boolean.valueOf(x.isMutualAidPension()));append(b,"employeePensionFund",Boolean.valueOf(x.isEmployeePensionFund()));append(b,"nationalPensionFund",Boolean.valueOf(x.isNationalPensionFund()));append(b,"sixMonthCheck",Boolean.valueOf(x.isSixMonthCheck()));b.append('}');return b.toString();
	}
	private void append(StringBuilder b,String name,Object value){if(b.length()>1)b.append(',');b.append('"').append(name).append("\":");if(value==null)b.append("null");else if(value instanceof Number||value instanceof Boolean)b.append(value);else b.append('"').append(HtmlUtil.json(String.valueOf(value))).append('"');}
}
