<!-- H22.9.3	青木・浅見		センター集約対応なし -->
<%@ page contentType="text/html; charset=Windows-31J" language="java" errorPage="" %>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<jsp:useBean id="ErrorMsg" class="java.lang.String" scope="session"/>

<HTML>
<HEAD>
	<META http-equiv="Content-Type" content="text/html; charset=Windows-31J">
	<TITLE>エラーページ</TITLE>

	<SCRIPT LANGUAGE ="JavaScript">
	<!---
		<%-- 親ウィンドウ（opener）が有るかどうかで、ボタン処理を制御する --%>
		function p1(){
			if(window.opener != null && window.opener.closed == false){
				<%-- 親ウィンドウが有るときはＣＬＯＳＥする --%>
				window.close();
			} else {
				<%-- 親ウィンドウが無いときはＴＯＰページにもどる --%>
				window.open('http://intra.dntsv01.johokubank.co.jp/' , "_main");
			}
		}

		<%-- ロード時の初期化処理 --%>
		function init(){
			if(window.opener != null && window.opener.closed == false){
				document.form0.sitemap.value = "閉 じ る";
			} else {
				document.form0.sitemap.value = "ＴＯＰメニューへ戻る";
			}
		}

	//--->
	</SCRIPT>

	<STYLE type="text/css">
		body {background-color:#ececec;text-align:center}
		h1 {color:#004080;font-size:large;}
		th {background-color:#FFFFCC;}
		.tb1 {border-width:thin;width:400px; text-align:center;}
		.tb2 {text-align:center;}
	</STYLE>
</HEAD>

<BODY onLoad="init()">
	<B><STRONG>
		<SCRIPT LANGUAGE ="JavaScript">
			<!---
				if(window.opener != null && window.opener.closed == false){
					document.write("処理続行不可のため、ウィンドウを閉じます。");
				} else {
					document.write("処理続行不可のため、ＴＯＰメニュー画面に戻ります。");
				}
			//--->
		</SCRIPT>
	</STRONG></B><BR>
	<BR>
	<BR>
<%		if(ErrorMsg!=null){ %>
			下記のエラーが発生しました。<BR>
			<BR>
			<FONT color="#FF0000"><%= ErrorMsg %></FONT>
<%		} %>
	<BR>
	<BR>
	<TABLE class="tb2" width="90%" border="0">
		<TR>
			<TD width="10%">
				<FORM name="form0" method="post" action="./JSP/MENU/Login.jsp">
					<INPUT type="button" class=TA00 name="sitemap" value="" onClick="p1()">
<%--
					<input type="submit" name="menu" value="ログイン画面に戻る">
--%>
				</FORM>
			</TD>
		</TR>
	</TABLE>
</BODY>
</HTML>