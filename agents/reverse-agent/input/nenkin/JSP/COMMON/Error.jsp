<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" import="nenkin.util.HtmlUtil" %>
<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><title>エラー</title>
<link rel="stylesheet" href="<%= request.getContextPath() %>/assets/css/site.css"></head>
<body><main class="app-shell"><section class="screen surface compact-screen">
<h1>処理エラー</h1><div class="message error"><%=HtmlUtil.escape(session.getAttribute("ErrorMsg") == null ? "処理を完了できませんでした。" : session.getAttribute("ErrorMsg"))%></div>
<a class="access-button" href="<%= request.getContextPath() %>/">ログイン画面へ</a>
</section></main></body></html>
