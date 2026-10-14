<!-- H22.9.3	青木・浅見		センター集約対応なし -->
<%@ page contentType="text/html; charset=Windows-31J" language="java" import="java.util.List" errorPage="" %>

<HTML>
<HEAD>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html;charset=Windows-31J">
<META HTTP-EQUIV="Expires" CONTENT="Sat, 01 Jan 2000 00:00:00 GMT">
<META HTTP-EQUIV="cache-control" CONTENT="no-store">
<META HTTP-EQUIV="Pragma" CONTENT="no-cache">
<TITLE>エラーメッセージ画面</TITLE>
<style type="text/css">
<!--
-->
.T00 {
	BACKGROUND-COLOR: #CCCCCC;
	BORDER-BOTTOM: #999999 2px double;
	BORDER-LEFT: #c8c0ff 3px double;
	BORDER-RIGHT: #999999 2px double;
	BORDER-TOP: #c8c0ff 3px double;
	COLOR: #000000;
	FONT-SIZE: 12px;
	width: 100px;
	text-align: center;
	clip: rect(   );
	cursor: hand;
	line-height: 120%;
	border: 3px #FFFFFF outset;
}
</style>
</HEAD>
<BODY bgcolor="#ececec" onLoad="window.focus()">
	<p align="center">
	<table width="400" border="0" height="46">
		<tr>
			<td align="center">
			<p><b><font size="5"><strong>操作内容にエラーがあります</strong></font></b></p>
			</td>
		</tr>
	</table>
	<hr>
	<p align="center">
	<form name="form0">
		<table width="450" border="0" cellspacing="0">

<%		if(session.getAttribute("MESSAGE") != null){
			List lsMessage = (List)session.getAttribute("MESSAGE");
			for(int i=0; i < lsMessage.size(); i++){
%>
				<tr valign="top" height="20">
					<td width="30" align="right"><font color="#FF0000"><strong><%= i + 1 %>:</strong></font></td>
					<td align="left"><font color="#FF0000"><strong><%= lsMessage.get(i) %></strong></font></td>
				</tr>
<%			}%>
<%		}%>
<%		session.removeAttribute("MESSAGE");%>

			<tr align="center" height="40">
				<td align="center" colspan=2>
					<input type="button" class=T00 name="btn1" value="閉じる" onClick="window.close()">
				</td>
			</tr>	
		</table>
	</form>
</BODY>
</HTML>