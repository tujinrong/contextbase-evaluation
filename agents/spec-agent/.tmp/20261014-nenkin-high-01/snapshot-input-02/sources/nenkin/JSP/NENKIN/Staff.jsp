<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" import="nenkin.bean.StaffViewBean,nenkin.util.HtmlUtil" %>
<!DOCTYPE html>
<jsp:useBean id="ViewBean" class="nenkin.bean.StaffViewBean" scope="session"/>
<html lang="ja">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>職員番号入力</title><link rel="stylesheet" href="<%=request.getContextPath()%>/assets/css/site.css"><script src="<%=request.getContextPath()%>/assets/js/app.js" defer></script></head>
<body>
	<header class="app-nav"><div class="app-nav__title">年金自動受取予約管理システム</div><form action="<%=request.getContextPath()%>/Action.do" method="post"><input type="hidden" name="FUNCTION_ID" value="common"><input type="hidden" name="VIEW_ID" value="Logout"><input type="hidden" name="COMMAND_ID" value=""><button class="nav-button" type="submit">ログアウト</button></form></header>
	<main class="app-shell"><section class="screen surface staff-screen">
		<div class="screen-header compact"><h1>職員番号入力</h1></div>
		<% if(ViewBean.getMessage().length()>0){ %><div class="message error"><%=HtmlUtil.escape(ViewBean.getMessage())%></div><% } %>
		<form id="staffForm" action="<%=request.getContextPath()%>/Action.do" method="post" accept-charset="Windows-31J" class="access-form staff-form">
			<input type="hidden" name="FUNCTION_ID" value="nenkin"><input type="hidden" name="VIEW_ID" value="Staff"><input id="staffCommand" type="hidden" name="COMMAND_ID" value="Verify">
			<div class="field-row"><label for="staffNo">職員番号</label><input id="staffNo" class="form-control code-input" name="STAFF_NO" value="<%=HtmlUtil.escape(ViewBean.getStaffNo())%>" maxlength="8" inputmode="numeric" data-digits-only autofocus></div>
			<div class="button-row"><button class="access-button primary" type="submit" onclick="document.getElementById('staffCommand').value='Verify'">メニュー画面へ</button><button class="access-button secondary" type="submit" formnovalidate onclick="document.getElementById('staffCommand').value='Clear'">クリア</button></div>
		</form>
		<p class="hint">ローカル確認用職員番号：3001（山田 太郎）／2001（佐藤 花子）</p>
	</section></main>
</body></html>

