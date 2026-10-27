package nenkin;

import java.util.ArrayList;
import java.util.List;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import nenkin.bean.LookupViewBean;
import nenkin.model.BranchLookupItem;
import nenkin.model.CustomerLookupItem;
import nenkin.model.StaffLookupItem;
import nenkin.service.ReferenceDataService;

public class LookupViewAction extends NenkinBaseAction {
	public String perform(HttpServletRequest request, HttpServletResponse response) {
		if (!requireStaff(request)) return STAFF_JSP;
		LookupViewBean bean=new LookupViewBean();String target=trim(request.getParameter("TARGET"));if(!"branch".equals(target)&&!"staff".equals(target))target="customer";bean.setTarget(target);bean.setKeyword(trim(request.getParameter("KEYWORD")));bean.setBranchNo(trim(request.getParameter("BRANCH_NO")));bean.setNameKeyword(trim(request.getParameter("NAME_KEYWORD")));bean.setPhoneKeyword(trim(request.getParameter("PHONE_KEYWORD")));bean.setPage(integerOrDefault(request.getParameter("PAGE"),1));ReferenceDataService service=ReferenceDataService.getInstance();Integer branch=integerOrNull(bean.getBranchNo());
		if("branch".equals(target)){List<BranchLookupItem> all=service.searchBranches(bean.getKeyword());bean.setTotalCount(all.size());bean.setBranches(page(all,bean.getPage(),bean.getPageSize()));}
		else if("staff".equals(target)){List<StaffLookupItem> all=service.searchStaff(branch,bean.getKeyword());bean.setTotalCount(all.size());bean.setStaff(page(all,bean.getPage(),bean.getPageSize()));}
		else {List<CustomerLookupItem> all=service.searchCustomers(branch,bean.getNameKeyword(),bean.getPhoneKeyword());bean.setTotalCount(all.size());bean.setCustomers(page(all,bean.getPage(),bean.getPageSize()));}
		if(bean.getPage()>bean.getTotalPages())bean.setPage(bean.getTotalPages());setSubWindowBean(request.getSession(),bean);return LOOKUP_JSP;
	}
	private <T> List<T> page(List<T> source,int page,int size){int start=Math.max(0,(page-1)*size);int end=Math.min(source.size(),start+size);return start>=source.size()?new ArrayList<T>():new ArrayList<T>(source.subList(start,end));}
}
