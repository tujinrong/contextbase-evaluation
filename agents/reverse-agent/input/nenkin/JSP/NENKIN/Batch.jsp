<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" import="java.util.Locale,nenkin.bean.BatchViewBean,nenkin.model.StaffContext,nenkin.util.HtmlUtil" %>
<!DOCTYPE html>
<jsp:useBean id="ViewBean" class="nenkin.bean.BatchViewBean" scope="session"/>
<%
StaffContext LoginStaff=(StaffContext)session.getAttribute("NENKIN_STAFF_CONTEXT");
String LoginStaffNo=LoginStaff==null?"":String.format(Locale.ROOT,"%08d",Integer.valueOf(LoginStaff.getStaffNo()));
String LoginStaffName=LoginStaff==null?"":LoginStaff.getStaffName();
%>
<html lang="ja">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>日次 / 月次処理</title>
	<link rel="stylesheet" href="<%=request.getContextPath()%>/assets/css/site.css">
	<script src="<%=request.getContextPath()%>/assets/js/app.js" defer></script>
	<script src="<%=request.getContextPath()%>/assets/js/japanese-era-calendar.js?v=20260710-2" defer></script>
</head>
<body>
	<header class="app-nav"><div class="app-nav__title">年金自動受取予約管理システム</div></header>
	<main class="app-shell">
		<section class="screen surface batch-export-screen">
			<div class="screen-header batch-page-header">
				<div class="batch-page-title">
					<h1>日次 / 月次処理</h1>
					<p>出力条件と対象期間を指定して、年金予約データをExcelへ出力します。</p>
				</div>
				<div class="screen-header-actions">
					<div class="staff-badge"><span>ログイン職員</span><strong><%=HtmlUtil.escape(LoginStaffNo)%></strong><span><%=HtmlUtil.escape(LoginStaffName)%></span></div>
					<button class="access-button secondary narrow" type="button" onclick="backMenu()">戻る</button>
				</div>
			</div>

			<% if(ViewBean.getMessage().length()>0){ %><div class="validation-summary" role="alert"><%=HtmlUtil.escape(ViewBean.getMessage())%></div><% } %>

			<form id="batchForm" action="<%=request.getContextPath()%>/Action.do" method="post" accept-charset="Windows-31J" class="batch-export-form">
				<input type="hidden" name="FUNCTION_ID" value="nenkin">
				<input id="batchView" type="hidden" name="VIEW_ID" value="Batch">
				<input id="batchCommand" type="hidden" name="COMMAND_ID" value="Daily">
				<input type="hidden" name="CSRF_TOKEN" value="<%=HtmlUtil.escape(String.valueOf(session.getAttribute("NENKIN_CSRF_TOKEN")))%>">
				<input type="hidden" name="DELETE_CUTOFF_DATE" value="<%=HtmlUtil.escape(ViewBean.getDeleteCutoffDate())%>">

				<section class="batch-condition-card" aria-labelledby="batchConditionTitle">
					<div class="batch-section-heading">
						<div><h2 id="batchConditionTitle">共通の出力条件</h2><p>日次・月次のどちらにも適用されます。</p></div>
						<span class="batch-required-note">出力対象は複数選択できます</span>
					</div>
					<div class="batch-condition-grid">
						<div class="batch-staff-filter">
							<label for="batchStaff">抽出対象の職員番号</label>
							<div class="batch-staff-input-line"><input id="batchStaff" name="STAFF_NO" value="<%=HtmlUtil.escape(ViewBean.getStaffNo())%>" class="form-control code-input staff-code-input" maxlength="8" inputmode="numeric" autocomplete="off" data-digits-only><span class="batch-all-staff-badge">空欄：全職員</span></div>
							<p class="field-note">職員を限定する場合だけ8桁以内の職員番号を入力します。</p>
						</div>
						<fieldset class="batch-target-fieldset">
							<legend>出力対象</legend>
							<div class="batch-options">
								<label class="checkbox-item"><input type="checkbox" name="INCLUDE_NEW" value="1"<%=HtmlUtil.checked(ViewBean.isIncludeNew())%>><span><strong>新規分</strong><small>新しく登録した明細</small></span></label>
								<label class="checkbox-item"><input type="checkbox" name="INCLUDE_CHANGED" value="1"<%=HtmlUtil.checked(ViewBean.isIncludeChanged())%>><span><strong>変更分</strong><small>内容を変更した明細</small></span></label>
								<label class="checkbox-item"><input type="checkbox" name="INCLUDE_DELETED" value="1"<%=HtmlUtil.checked(ViewBean.isIncludeDeleted())%>><span><strong>削除分</strong><small>削除履歴の明細</small></span></label>
							</div>
						</fieldset>
					</div>
				</section>

				<div class="batch-period-grid">
					<section class="batch-period-card batch-period-card--daily" aria-labelledby="dailyTitle">
						<div class="batch-period-heading"><span class="batch-period-mark">日</span><div><h2 id="dailyTitle">日次処理</h2><p>指定した1日分のデータを出力</p></div></div>
						<div class="batch-period-body">
							<label for="dailyDate">対象日</label>
							<div class="calendar-input batch-date-control"><input id="dailyDate" name="DAILY_DATE" value="<%=HtmlUtil.escape(HtmlUtil.formatWesternDate(ViewBean.getDailyDate()))%>" class="form-control" maxlength="14" autocomplete="off" data-era-calendar data-era-calendar-mode="western"><button class="era-calendar-button" type="button" data-era-calendar-toggle="dailyDate" aria-label="日付のカレンダーを開く" title="カレンダー"></button></div>
							<p class="batch-period-note">データ更新日が対象日と一致する明細を抽出します。</p>
						</div>
						<div class="batch-period-actions"><button class="access-button primary batch-run-button" type="button" onclick="runBatch('Daily')">日次データを出力</button></div>
					</section>

					<section class="batch-period-card batch-period-card--monthly" aria-labelledby="monthlyTitle">
						<div class="batch-period-heading"><span class="batch-period-mark">月</span><div><h2 id="monthlyTitle">月次処理</h2><p>開始日から終了日までのデータを出力</p></div></div>
						<div class="batch-period-body">
							<div class="batch-date-range">
								<div class="batch-date-field"><label for="monthStart">開始日</label><div class="calendar-input batch-date-control"><input id="monthStart" name="MONTH_START" value="<%=HtmlUtil.escape(HtmlUtil.formatWesternDate(ViewBean.getMonthStart()))%>" class="form-control" maxlength="14" autocomplete="off" data-era-calendar data-era-calendar-mode="western"><button class="era-calendar-button" type="button" data-era-calendar-toggle="monthStart" aria-label="開始日のカレンダーを開く" title="カレンダー"></button></div></div>
								<span class="range-separator" aria-hidden="true">～</span>
								<div class="batch-date-field"><label for="monthEnd">終了日</label><div class="calendar-input batch-date-control"><input id="monthEnd" name="MONTH_END" value="<%=HtmlUtil.escape(HtmlUtil.formatWesternDate(ViewBean.getMonthEnd()))%>" class="form-control" maxlength="14" autocomplete="off" data-era-calendar data-era-calendar-mode="western"><button class="era-calendar-button" type="button" data-era-calendar-toggle="monthEnd" aria-label="終了日のカレンダーを開く" title="カレンダー"></button></div></div>
							</div>
							<p class="batch-period-note">初期値は当月の月初日から月末日です。</p>
						</div>
						<div class="batch-period-actions"><button class="access-button primary batch-run-button" type="button" onclick="runBatch('Monthly')">月次データを出力</button></div>
					</section>
				</div>
			</form>
		</section>
	</main>
	<script>
	function runBatch(command){document.getElementById('batchCommand').value=command;document.getElementById('batchForm').submit();}
	function backMenu(){document.getElementById('batchView').value='Menu';document.getElementById('batchCommand').value='View';document.getElementById('batchForm').submit();}
	</script>
</body>
</html>
