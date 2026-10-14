<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" import="java.util.List,nenkin.util.HtmlUtil" %>
<!DOCTYPE html>
<html lang="ja">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<meta http-equiv="Cache-Control" content="no-store">
	<title>年金自動受取予約管理システム - ログイン</title>
	<link rel="stylesheet" href="<%= request.getContextPath() %>/assets/css/site.css">
</head>
<% boolean localDb=Boolean.parseBoolean(System.getProperty("n2nenkin.localDb","false")); %>
<body class="login-page">
	<header class="app-nav"><div class="app-nav__title">年金自動受取予約管理システム</div><div class="app-nav__meta">N2 Framework</div></header>
	<main class="login-shell">
		<section class="screen surface login-card">
			<h1>ログイン</h1>
			<% List messages=(List)session.getAttribute("MESSAGE"); if(messages!=null&&!messages.isEmpty()){ %>
			<div class="message error"><% for(int i=0;i<messages.size();i++){ %><div><%=HtmlUtil.escape(messages.get(i))%></div><% } session.removeAttribute("MESSAGE"); %></div>
			<% } %>
			<form name="form0" action="<%= request.getContextPath() %>/Action.do" method="post" accept-charset="Windows-31J">
				<input type="hidden" name="APPL_NAME" value="unify">
				<input type="hidden" name="FUNCTION_ID" value="nenkin">
				<input type="hidden" name="VIEW_ID" value="Login">
				<input type="hidden" name="COMMAND_ID" value="">
				<input type="hidden" name="UNIFY_FLG" value="0">
				<div class="field-row"><label for="loginUser">職員番号</label><input id="loginUser" class="form-control code-input" name="DWH_USER_ID" maxlength="8" value="<%=localDb?"00001234":""%>" inputmode="numeric" autocomplete="username"></div>
				<div class="field-row"><label for="loginPassword">パスワード</label><input id="loginPassword" class="form-control" type="password" name="DWH_PASS_WORD" maxlength="20" value="<%=localDb?"samplepass":""%>" autocomplete="current-password"></div>
				<div class="button-row"><button class="access-button primary" type="submit">ログイン</button></div>
			</form>
			<% if(localDb){ %><p class="hint">ローカル確認用：職員番号 00001234 ／ パスワード samplepass</p><% } %>
		</section>
	</main>
</body>
</html>
