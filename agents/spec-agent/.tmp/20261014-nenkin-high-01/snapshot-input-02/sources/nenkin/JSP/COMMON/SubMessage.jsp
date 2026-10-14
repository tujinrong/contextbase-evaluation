<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" import="java.util.List,nenkin.util.HtmlUtil" %>
<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8"><title>入力確認</title>
<link rel="stylesheet" href="<%= request.getContextPath() %>/assets/css/site.css"></head>
<body><main class="app-shell"><section class="screen surface compact-screen"><h1>入力内容を確認してください</h1>
<div class="message error"><% List messages=(List)session.getAttribute("MESSAGE"); if(messages!=null){for(int i=0;i<messages.size();i++){%><div><%=HtmlUtil.escape(messages.get(i))%></div><%}}%></div>
<button class="access-button" type="button" onclick="history.back()">戻る</button>
</section></main></body></html>
