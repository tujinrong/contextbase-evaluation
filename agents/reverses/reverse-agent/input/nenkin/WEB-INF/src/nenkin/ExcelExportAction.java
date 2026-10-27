package nenkin;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import nenkin.bean.ExcelViewBean;
import nenkin.model.BranchLookupItem;
import nenkin.service.PensionExcelExportResult;
import nenkin.service.PensionExcelExportService;
import nenkin.service.ReferenceDataService;

public final class ExcelExportAction extends NenkinBaseAction {
	private static final String CONTENT_TYPE="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
	public String perform(HttpServletRequest request,HttpServletResponse response) throws Exception {
		if(!requireStaff(request))return STAFF_JSP;
		ExcelViewBean bean=new ExcelViewBean();String text=trim(request.getParameter("BRANCH_NO"));bean.setBranchNo(text);Integer branch=integerOrNull(text);
		if(text.length()==0||branch==null){bean.setMessage("店番を入力してください。");setViewBean(request.getSession(),bean);return EXCEL_JSP;}
		if(text.length()>3||!text.matches("[0-9]+")){bean.setMessage("店番は3桁以内の数字で入力してください。");setViewBean(request.getSession(),bean);return EXCEL_JSP;}
		BranchLookupItem item=ReferenceDataService.getInstance().getBranch(branch.intValue());if(item!=null)bean.setBranchName(item.getBranchName());
		PensionExcelExportResult result=PensionExcelExportService.getInstance().buildByBranch(branch.intValue());
		if(result.getRowCount()==0){bean.setMessage("入力された店番には対象データがありません。");setViewBean(request.getSession(),bean);return EXCEL_JSP;}
		writeDownload(response,result.getFileName(),CONTENT_TYPE,result.getContent());return "CSV";
	}
}
