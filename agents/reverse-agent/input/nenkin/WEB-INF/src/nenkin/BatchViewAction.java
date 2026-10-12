package nenkin;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Locale;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import nenkin.bean.BatchViewBean;
import nenkin.util.DateUtil;

public final class BatchViewAction extends NenkinBaseAction {
	public String perform(HttpServletRequest request, HttpServletResponse response) {
		if (!requireStaff(request)) return STAFF_JSP;
		BatchViewBean bean = new BatchViewBean();
		String today = DateUtil.todayIso();
		bean.setDailyDate(today);
		bean.setMonthStart(DateUtil.firstDayOfMonth(today));
		bean.setMonthEnd(DateUtil.lastDayOfMonth(today));
		Calendar cutoff = Calendar.getInstance(Locale.JAPAN);
		cutoff.add(Calendar.MONTH, -2);
		bean.setDeleteCutoffDate(new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT).format(cutoff.getTime()));
		setViewBean(request.getSession(), bean);
		return BATCH_JSP;
	}
}
