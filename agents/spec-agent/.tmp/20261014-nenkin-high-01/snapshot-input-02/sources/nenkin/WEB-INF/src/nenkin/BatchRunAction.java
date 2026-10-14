package nenkin;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import nenkin.bean.BatchViewBean;
import nenkin.service.PensionBatchExportRequest;
import nenkin.service.PensionBatchExportResult;
import nenkin.service.PensionBatchExportService;
import nenkin.service.PensionBatchRunMode;

abstract class BatchRunAction extends NenkinBaseAction {
	abstract PensionBatchRunMode runMode();
	public String perform(HttpServletRequest request,HttpServletResponse response) throws Exception {
		if(!requireStaff(request))return STAFF_JSP;
		BatchViewBean bean=new BatchViewBean();bean.setStaffNo(trim(request.getParameter("STAFF_NO")));bean.setIncludeNew(isChecked(request,"INCLUDE_NEW"));bean.setIncludeChanged(isChecked(request,"INCLUDE_CHANGED"));bean.setIncludeDeleted(isChecked(request,"INCLUDE_DELETED"));bean.setDailyDate(trim(request.getParameter("DAILY_DATE")));bean.setMonthStart(trim(request.getParameter("MONTH_START")));bean.setMonthEnd(trim(request.getParameter("MONTH_END")));bean.setDeleteCutoffDate(trim(request.getParameter("DELETE_CUTOFF_DATE")));
		if(!isAuthorizedMutation(request)){bean.setMessage(INVALID_REQUEST_MESSAGE);setViewBean(request.getSession(),bean);return BATCH_JSP;}
		if(!bean.isIncludeNew()&&!bean.isIncludeChanged()&&!bean.isIncludeDeleted()){bean.setMessage("新規分、変更分、削除分のどれかを選択してから再度、実行ボタンを選択してください");setViewBean(request.getSession(),bean);return BATCH_JSP;}
		if(bean.getStaffNo().length()>0&&(!bean.getStaffNo().matches("[0-9]+")||bean.getStaffNo().length()>8)){bean.setMessage("職員番号は8桁以内の数字で入力してください");setViewBean(request.getSession(),bean);return BATCH_JSP;}
		PensionBatchExportRequest input=new PensionBatchExportRequest();input.setRunMode(runMode());input.setDailyDate(bean.getDailyDate());input.setMonthStart(bean.getMonthStart());input.setMonthEnd(bean.getMonthEnd());input.setStaffNo(bean.getStaffNo());input.setIncludeNew(bean.isIncludeNew());input.setIncludeChanged(bean.isIncludeChanged());input.setIncludeDeleted(bean.isIncludeDeleted());input.setDeleteCutoffDate(bean.getDeleteCutoffDate());
		try { PensionBatchExportResult result=PensionBatchExportService.getInstance().build(input);if(!result.hasContent()){StringBuilder message=new StringBuilder();for(int i=0;i<result.getMessages().size();i++){if(i>0)message.append(' ');message.append(result.getMessages().get(i));}bean.setMessage(message.toString());setViewBean(request.getSession(),bean);return BATCH_JSP;}writeDownload(response,result.getFileName(),result.getContentType(),result.getContent());return "CSV"; }
		catch(IllegalArgumentException e){bean.setMessage(e.getMessage());setViewBean(request.getSession(),bean);return BATCH_JSP;}
	}
}
