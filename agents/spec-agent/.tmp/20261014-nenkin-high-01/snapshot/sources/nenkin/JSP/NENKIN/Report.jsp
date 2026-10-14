<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" import="java.util.Date,java.util.List,java.util.Locale,java.text.SimpleDateFormat,nenkin.bean.ReportViewBean,nenkin.model.PensionReservation,nenkin.model.StaffContext,nenkin.util.DateUtil,nenkin.util.HtmlUtil" %>
<!DOCTYPE html>
<jsp:useBean id="ViewBean" class="nenkin.bean.ReportViewBean" scope="session"/>
<%
StaffContext LoginStaff=(StaffContext)session.getAttribute("NENKIN_STAFF_CONTEXT");
String LoginStaffNo=LoginStaff==null?"":String.format(Locale.ROOT,"%08d",Integer.valueOf(LoginStaff.getStaffNo()));
String LoginStaffName=LoginStaff==null?"":LoginStaff.getStaffName();
String GeneratedAt=HtmlUtil.formatReportDate(DateUtil.todayIso())+" "+new SimpleDateFormat("HH:mm",Locale.ROOT).format(new Date());
String SortLabel=ViewBean.getSortType()==2?"顧客氏名":ViewBean.getSortType()==3?"生年月日":ViewBean.getSortType()==4?"請求予定日":"担当者コード";
%>
<html lang="ja">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>登録内容印刷</title>
	<link rel="stylesheet" href="<%=request.getContextPath()%>/assets/css/site.css">
	<script src="<%=request.getContextPath()%>/assets/js/app.js" defer></script>
</head>
<body>
	<header class="app-nav no-print"><div class="app-nav__title">年金自動受取予約管理システム</div></header>
	<main class="app-shell">
		<section class="screen surface report-screen">
			<div class="screen-header report-page-header no-print">
				<div class="report-page-title"><h1>登録内容印刷</h1><p>並び順と対象店舗を指定し、印刷用の明細表を作成します。</p></div>
				<div class="screen-header-actions"><div class="staff-badge"><span>ログイン職員</span><strong><%=HtmlUtil.escape(LoginStaffNo)%></strong><span><%=HtmlUtil.escape(LoginStaffName)%></span></div><button class="access-button secondary narrow" type="button" onclick="backMenu()">戻る</button></div>
			</div>

			<% if(ViewBean.getMessage().length()>0){ %><div class="validation-summary no-print" role="alert"><%=HtmlUtil.escape(ViewBean.getMessage())%></div><% } %>

			<form id="reportForm" action="<%=request.getContextPath()%>/Action.do" method="post" accept-charset="Windows-31J" class="report-filter-form no-print">
				<input type="hidden" name="FUNCTION_ID" value="nenkin">
				<input id="reportView" type="hidden" name="VIEW_ID" value="Report">
				<input id="reportCommand" type="hidden" name="COMMAND_ID" value="Preview">

				<div class="report-filter-heading"><div><h2>印刷条件</h2><p>店舗を指定しない場合は全店舗が対象です。</p></div><span>店番ごとに改ページします</span></div>
				<div class="report-filter-grid">
					<fieldset class="report-filter-panel report-sort-panel">
						<legend>並び替え基準</legend>
						<div class="report-sort-options">
							<label class="report-radio-card"><input type="radio" name="SORT_TYPE" value="1"<%=ViewBean.getSortType()==1?" checked":""%>><span><strong>担当者コード</strong><small>担当者、顧客番号の順</small></span></label>
							<label class="report-radio-card"><input type="radio" name="SORT_TYPE" value="2"<%=ViewBean.getSortType()==2?" checked":""%>><span><strong>顧客氏名</strong><small>カナ氏名の順</small></span></label>
							<label class="report-radio-card"><input type="radio" name="SORT_TYPE" value="3"<%=ViewBean.getSortType()==3?" checked":""%>><span><strong>生年月日</strong><small>生年月日、顧客番号の順</small></span></label>
							<label class="report-radio-card"><input type="radio" name="SORT_TYPE" value="4"<%=ViewBean.getSortType()==4?" checked":""%>><span><strong>請求予定日</strong><small>請求予定日、顧客番号の順</small></span></label>
						</div>
					</fieldset>

					<fieldset class="report-filter-panel report-branch-panel">
						<legend>対象店舗</legend>
						<label class="report-branch-toggle"><input id="useBranch" type="checkbox" name="USE_BRANCH_RANGE" value="1"<%=HtmlUtil.checked(ViewBean.isUseBranchRange())%> onchange="toggleBranch(true)"><span><strong>店番を指定する</strong><small>チェックなしで全店舗</small></span></label>
						<div class="report-branch-range">
							<div class="report-branch-field"><label for="branchFrom">店番自</label><input id="branchFrom" name="BRANCH_FROM" value="<%=HtmlUtil.escape(ViewBean.getBranchFrom())%>" class="form-control code-input" maxlength="3" inputmode="numeric" autocomplete="off" data-digits-only></div>
							<span class="branch-range-separator" aria-hidden="true">～</span>
							<div class="report-branch-field"><label for="branchTo">店番至</label><input id="branchTo" name="BRANCH_TO" value="<%=HtmlUtil.escape(ViewBean.getBranchTo())%>" class="form-control code-input" maxlength="3" inputmode="numeric" autocomplete="off" data-digits-only></div>
						</div>
						<p class="report-filter-note">店番至を空欄にすると、店番自の1店舗だけを出力します。</p>
					</fieldset>
				</div>

				<div class="report-filter-actions">
					<div class="report-preview-status" aria-live="polite"><% if(ViewBean.isPreview()){ %><span>現在のプレビュー</span><strong><%=ViewBean.getRows().size()%>件</strong><% } else { %><span>条件を指定して</span><strong>プレビューを作成</strong><% } %></div>
					<div class="report-action-buttons"><button class="access-button primary" type="submit">プレビューを作成</button><button class="access-button report-print-button" type="button" onclick="window.print()"<%=ViewBean.isPreview()?"":" disabled"%>>印刷</button></div>
				</div>
			</form>

			<% if(ViewBean.isPreview()){ List<PensionReservation> Rows=ViewBean.getRows(); %>
			<section class="report-preview-shell" aria-label="印刷プレビュー">
				<div class="report-preview-toolbar no-print"><div><h2>印刷プレビュー</h2><p>A4横・店舗ごとに改ページ</p></div><div><span>並び順</span><strong><%=HtmlUtil.escape(SortLabel)%></strong><span>合計</span><strong><%=Rows.size()%>件</strong></div></div>
				<% if(Rows.isEmpty()){ %><div class="report-empty-state"><strong>対象データがありません</strong><span>印刷条件を変更してプレビューを作成してください。</span></div><% } else {
				int GroupStart=0;
				while(GroupStart<Rows.size()){
					PensionReservation First=Rows.get(GroupStart);
					Integer BranchNo=First.getBranchNo();
					int GroupEnd=GroupStart+1;
					while(GroupEnd<Rows.size()){
						Integer NextBranch=Rows.get(GroupEnd).getBranchNo();
						if(BranchNo==null?NextBranch!=null:!BranchNo.equals(NextBranch))break;
						GroupEnd++;
					}
				%>
				<article class="report-page">
					<table class="report-ledger" aria-label="店番 <%=HtmlUtil.value(BranchNo)%> の年金自動受取予約明細表">
						<thead><tr><th scope="col">
							<div class="report-print-title"><h2>年金自動受取予約明細表</h2><div><span>出力日時</span><strong><%=HtmlUtil.escape(GeneratedAt)%></strong></div></div>
							<div class="report-branch-band"><div><span>店番</span><strong><%=HtmlUtil.value(BranchNo)%></strong><span><%=HtmlUtil.escape(First.getBranchName())%></span></div><div><span>並び順</span><strong><%=HtmlUtil.escape(SortLabel)%></strong><span>出力件数</span><strong><%=GroupEnd-GroupStart%>件</strong></div></div>
							<div class="report-ledger-grid report-ledger-grid--head">
								<span class="report-cell report-cell--customer">顧客番号</span><span class="report-cell report-cell--staff">担当</span><span class="report-cell report-cell--name">顧客氏名</span><span class="report-cell report-cell--kana">カナ氏名</span><span class="report-cell report-cell--gender">性別</span><span class="report-cell report-cell--phone">電話番号</span><span class="report-cell report-cell--birth">生年月日</span><span class="report-cell report-cell--claim">裁請</span><span class="report-cell report-cell--claim-date">請求予定日</span><span class="report-cell report-cell--age">予齢</span><span class="report-cell report-cell--request">予約徴求日</span>
								<span class="report-cell report-cell--address">住所</span><span class="report-cell report-cell--spouse">配偶者氏名</span><span class="report-cell report-cell--benefit">受給</span><span class="report-cell report-cell--spouse-birth">配偶者生年月日</span><span class="report-cell report-cell--pension">年金種類</span><span class="report-cell report-cell--notes">備考</span>
							</div>
						</th></tr></thead>
						<tbody>
						<% for(int RowIndex=GroupStart;RowIndex<GroupEnd;RowIndex++){ PensionReservation Row=Rows.get(RowIndex); %>
						<tr><td><div class="report-ledger-grid report-ledger-grid--row">
							<span class="report-cell report-cell--customer"><%=HtmlUtil.value(Row.getCustomerNo())%></span><span class="report-cell report-cell--staff"><%=HtmlUtil.value(Row.getStaffCode())%></span><span class="report-cell report-cell--name" title="<%=HtmlUtil.escape(Row.getCustomerName())%>"><%=HtmlUtil.escape(Row.getCustomerName())%></span><span class="report-cell report-cell--kana" title="<%=HtmlUtil.escape(Row.getKanaName())%>"><%=HtmlUtil.escape(Row.getKanaName())%></span><span class="report-cell report-cell--gender"><%=HtmlUtil.escape(Row.getGender())%></span><span class="report-cell report-cell--phone"><%=HtmlUtil.escape(Row.getPhoneNumber())%></span><span class="report-cell report-cell--birth"><%=HtmlUtil.escape(HtmlUtil.formatReportDate(Row.getBirthDate()))%></span><span class="report-cell report-cell--claim"><%=HtmlUtil.escape(Row.getClaimStatus())%></span><span class="report-cell report-cell--claim-date"><%=HtmlUtil.escape(HtmlUtil.formatReportDate(Row.getClaimScheduledDate()))%></span><span class="report-cell report-cell--age"><%=HtmlUtil.value(Row.getPlannedAge())%></span><span class="report-cell report-cell--request"><%=HtmlUtil.escape(HtmlUtil.formatReportDate(Row.getReservationRequestDate()))%></span>
							<span class="report-cell report-cell--address" title="<%=HtmlUtil.escape(Row.getAddress())%>"><%=HtmlUtil.escape(Row.getAddress())%></span><span class="report-cell report-cell--spouse" title="<%=HtmlUtil.escape(Row.getSpouseName())%>"><%=HtmlUtil.escape(Row.getSpouseName())%></span><span class="report-cell report-cell--benefit"><%=HtmlUtil.escape(Row.getHasBenefit())%></span><span class="report-cell report-cell--spouse-birth"><%=HtmlUtil.escape(HtmlUtil.formatReportDate(Row.getSpouseBirthDate()))%></span><span class="report-cell report-cell--pension" title="<%=HtmlUtil.escape(Row.getPensionType())%>"><%=HtmlUtil.escape(Row.getPensionType())%></span><span class="report-cell report-cell--notes" title="<%=HtmlUtil.escape(Row.getNotes())%>"><%=HtmlUtil.escape(Row.getNotes())%></span>
						</div></td></tr>
						<% } %>
						</tbody>
					</table>
				</article>
				<% GroupStart=GroupEnd; } } %>
			</section>
			<% } %>
		</section>
	</main>
	<script>
	function toggleBranch(focusFirst){const enabled=document.getElementById('useBranch').checked;const inputs=[document.getElementById('branchFrom'),document.getElementById('branchTo')];inputs.forEach(input=>input.disabled=!enabled);if(enabled&&focusFirst)inputs[0].focus();}
	function backMenu(){document.getElementById('reportView').value='Menu';document.getElementById('reportCommand').value='View';document.getElementById('reportForm').submit();}
	toggleBranch(false);
	</script>
</body>
</html>
