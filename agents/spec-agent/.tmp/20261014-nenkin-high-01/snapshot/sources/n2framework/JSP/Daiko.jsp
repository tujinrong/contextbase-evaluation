<!-- H29.05.10	Minori山口  新規作成 -->
<%@ page language="java" 
	contentType="text/html; charset=Windows-31J"
	import="java.util.List,common.CommonConst,common.util.CommonConverter,common.bean.TenpoListBean" %>

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">

<jsp:useBean id="LoginBean" class="common.bean.LoginInfoBean" scope="session"/>
<jsp:useBean id="ViewBean" class="common.bean.DaikoBean" scope="session"/>

<HTML>
<HEAD>
	<META http-equiv="Content-Type" content="text/html; charset=Windows-31J">
	<TITLE>代行店舗選択</TITLE>
	<SCRIPT LANGUAGE ="JavaScript">
	<!---
		//二重実行制御フラグ
		var DoubleSubmitFlag = true;

		<!-- ＴＯＰメニューへ戻る -->
		function p1(w1){ window.open(w1,"_main")}

		//ボタン実行
		function doAction(commandId){
			//二重実行制御フラグがfalseの場合はSubmitさせない
			if(DoubleSubmitFlag == true){
				//二重実行フラグを立てる
				DoubleSubmitFlag = false;
		
				document.form0.COMMAND_ID.value = commandId;
				document.form0.submit();
			}
		}
		

		var _wkbr = "";
		var _wktenpo = "";
		
		
		//選択した店舗を保持
		function tenpoSelect(_br,_tenpo){			
			_wkbr = _br;			
			_wktenpo = _tenpo;
		}
		
		
		//【選択中の店舗に変更】ボタン押下
		function doActionSelect(){
			
			if(_wkbr == "" && _wktenpo == ""){
				alert("代行店舗を選択してください！");
				return false;
				
			}else{
				var _loginBr = "<%= LoginBean.get所属店番() %>";
				
				//店番を変更しない場合
				if(_wkbr == _loginBr){
					
					if(window.confirm("支店の変更はありません。　よろしいですか？")){	
						document.form0.HDN_BR.value = _wkbr;
						document.form0.HDN_TENPO_NAME.value = _wktenpo;
						
						//サブミット処理
						doAction('Select');
						
					}else{
						return false;
					}	
						
				//変更する店番を選択した場合	
				}else{
			
					if(window.confirm("【 "+_wkbr + "  " +  _wktenpo + " 】に変更します。　よろしいですか？")){	
						
						document.form0.HDN_BR.value = _wkbr;
						document.form0.HDN_TENPO_NAME.value = _wktenpo;
						
						//サブミット処理
						doAction('Select');	
						
					}else{
						return false;
					}
				}
			}
		}


		<!-- ロード時の初期化処理 -->
		function init(){
			
			//login店番と、店舗名を取得
			_wkbr = "<%= LoginBean.get所属店番() %>"			
			_wktenpo = "<%= LoginBean.get所属店名() %>"	
		}
		
	//--->
	</SCRIPT>

	<STYLE type="text/css">
	<!--
	-->
	.T00 {
		BACKGROUND-COLOR: #cccccc;
		BORDER-BOTTOM: #999999 2px double;
		BORDER-LEFT: #c8c0ff 3px double;
		BORDER-RIGHT: #999999 2px double;
		BORDER-TOP: #c8c0ff 3px double;
		COLOR: #000000;
		FONT-SIZE: 12px;
		width: 80px;
		text-align: center;
		clip: rect(   );
		cursor: hand;
		line-height: 120%;
		border: 3px #ffffff outset;
	}


		/*--- 全体のエリア---*/
		#id_Main_Area {
			width: 1000px;
			height: 575px;
			text-align: center;
		}

		/*--- ヘッダーエリア---*/
		#id_Header_Area {
			top: 20px;
			width: 980px;
			height: 50px;
			text-align: left;
		}

		/*---タイトルエリア---*/
		#id_Taitolu_Area {
			width: 975px;
			height: 46px;
			text-align: left;
		}

		/*--- 店舗選択エリア---*/
		#id_SelectArea {
			background-color: #ffffff;
			border: 1px solid #888888;
			width: 975px;
			height: 417px;
			overflow: auto;
		}
		
		/*--- 終了エリア---*/
		#id_END_Area {
			width: 980px;
			height: 30px;
		}
		
	</STYLE>
</HEAD>

<BODY bgcolor="#ececec" onLoad="init()" style="text-align: center;">
	<FORM name="form0" action="./Action.do" method="post">
	<!-- アクションクラス起動パラメータ -->
	<INPUT type="hidden" name="FUNCTION_ID" value="common">
	<INPUT type="hidden" name="VIEW_ID" value="Daiko">
	<INPUT type="hidden" name="COMMAND_ID" value="">
	<INPUT type="hidden" name="HDN_BR" value="">
	<INPUT type="hidden" name="HDN_TENPO_NAME" value="">

	<DIV id="id_Main_Area">
		<DIV id="id_Header_Area">
			<TABLE width="980" border="0" cellspacing="0">
				<TR style="background-color: #666666;">
					<TD width="620">
						<DIV style="font-size: 10pt;color: #ffffff;"><STRONG>　＜＜ 代行店舗選択 ＞＞</STRONG></DIV>
					</TD>
					<TD width="360">
						<TABLE width="360" border="1" bordercolor="#666666" cellspacing="0" style="font-size: 10pt;">
							<TR style="background-color: #ffffff;" align="center">
								<TD width="120" ><%= LoginBean.get所属店名() %><BR></TD>
								<TD width="140" ><%= LoginBean.get融資系ユーザー名() %><BR></TD>
								<TD width="100" ><%= LoginBean.get職員氏名() %><BR></TD>
							</TR>
						</TABLE>
					</TD>
				</TR>
				<TR height="40">
					<TD colspan="2" style="text-align: center;vertical-align: bottom;">
						<DIV style="font-size: 20pt;"><STRONG>代行店舗選択画面</STRONG></DIV>
					</TD>
				</TR>
			</TABLE>
			<HR width="980">
		</DIV>


		<DIV id="id_Taitolu_Area">
			<TABLE width="975px" height="44px" border= "0" cellspacing="0" style="font-size:10pt;text-align: left;">
				<TR><TH style="text-indent:3px;">現在の店舗：<%= LoginBean.get所属店名()%></TH></TR>
				<TR>
					<TD style=" text-indent:3px; background-color: #A4C6FF; color:#000000; ">店舗を選択してください　　
						<INPUT type="button" name="BTN_END" value="選択中の店舗に変更" onClick="doActionSelect('')" style="width: 150px;">
					</TD>
				</TR>
			</TABLE>
		</DIV>

		<DIV id="id_SelectArea">
		
<%		List lsMeisai1 = ViewBean.get店舗一覧１();%>
<%		if(lsMeisai1 != null && !lsMeisai1.isEmpty()){%>		
		
			<TABLE width="180px"  border= "0" cellspacing="0" style="position:absolute; top:2px;left:10px;font-size:10pt">
<%          for(int i=0; i<lsMeisai1.size(); i++){
			TenpoListBean beanList = (TenpoListBean)lsMeisai1.get(i);%>				
				<TR>
					<TD height="24"><input type="radio" id="id_Main_rdo_idou" name="RDO_IDOU" value="<%=beanList.get店舗番号() %>"
					onClick="tenpoSelect('<%=beanList.get店舗番号() %>','<%=beanList.get店舗名() %>')" <%if(beanList.get店舗番号().equals(LoginBean.get所属店番())){ %> checked<% } %>><%=beanList.get店舗() %></TD>
				</TR>
<%          } %>			
			</TABLE>
<%     } %>



<%		List lsMeisai2 = ViewBean.get店舗一覧２();%>
<%		if(lsMeisai2 != null && !lsMeisai2.isEmpty()){%>
			<TABLE width="180px" border= "0" cellspacing="0" style="position:absolute; top:2px;left:200px;font-size:10pt">

<%          for(int i=0; i<lsMeisai2.size(); i++){
			TenpoListBean beanList = (TenpoListBean)lsMeisai2.get(i);%>				
				<TR>
					<TD height="24"><input type="radio" id="id_Main_rdo_idou" name="RDO_IDOU" value="<%=beanList.get店舗番号() %>"
					 onClick="tenpoSelect('<%=beanList.get店舗番号() %>','<%=beanList.get店舗名() %>')" <%if(beanList.get店舗番号().equals(LoginBean.get所属店番())){ %> checked<% } %>><%=beanList.get店舗() %></TD>
				</TR>
<%          } %>			
			</TABLE>
<%     } %>



<%		List lsMeisai3 = ViewBean.get店舗一覧３();%>
<%		if(lsMeisai3 != null && !lsMeisai3.isEmpty()){%>
			<TABLE width="180px" border= "0" cellspacing="0" style="position:absolute; top:2px;left:390px;font-size:10pt">

<%          for(int i=0; i<lsMeisai3.size(); i++){
			TenpoListBean beanList = (TenpoListBean)lsMeisai3.get(i);%>
				<TR>
					<TD height="24px"><input type="radio" id="id_Main_rdo_idou" name="RDO_IDOU" value="<%=beanList.get店舗番号() %>"
					 onClick="tenpoSelect('<%=beanList.get店舗番号() %>','<%=beanList.get店舗名() %>')" <%if(beanList.get店舗番号().equals(LoginBean.get所属店番())){ %> checked<% } %>><%=beanList.get店舗() %></TD>
				</TR>
<%          } %>			
			</TABLE>
<%     } %>



<%		List lsMeisai4 = ViewBean.get店舗一覧４();%>
<%		if(lsMeisai4 != null && !lsMeisai4.isEmpty()){%>
			<TABLE width="180px" border= "0" cellspacing="0" style="position:absolute; top:2px;left:580px;font-size:10pt">

<%          for(int i=0; i<lsMeisai4.size(); i++){
			TenpoListBean beanList = (TenpoListBean)lsMeisai4.get(i);%>
				<TR>
					<TD height="24px"><input type="radio" id="id_Main_rdo_idou" name="RDO_IDOU" value="<%=beanList.get店舗番号() %>"
					 onClick="tenpoSelect('<%=beanList.get店舗番号() %>','<%=beanList.get店舗名() %>')" <%if(beanList.get店舗番号().equals(LoginBean.get所属店番())){ %> checked<% } %>><%=beanList.get店舗() %></TD>
				</TR>
<%          } %>			
			</TABLE>
<%     } %>



<%		List lsMeisai5 = ViewBean.get店舗一覧５();%>
<%		if(lsMeisai5 != null && !lsMeisai5.isEmpty()){%>
			<TABLE width="180px" border= "0" cellspacing="0" style="position:absolute; top:2px;left:770px;font-size:10pt">

<%          for(int i=0; i<lsMeisai5.size(); i++){
			TenpoListBean beanList = (TenpoListBean)lsMeisai5.get(i);%>
				<TR>
					<TD height="24px"><input type="radio" id="id_Main_rdo_idou" name="RDO_IDOU" value="<%=beanList.get店舗番号() %>"
					 onClick="tenpoSelect('<%=beanList.get店舗番号() %>','<%=beanList.get店舗名() %>')" <%if(beanList.get店舗番号().equals(LoginBean.get所属店番())){ %> checked<% } %>><%=beanList.get店舗() %></TD>
				</TR>
<%          } %>			
			</TABLE>
<%     } %>
		</DIV>


		<DIV id="id_END_Area">
			<TABLE width="975px" border="0" cellspacing="0">
				<TR align="right">
					<TD width="970px">
						<INPUT type="button" name="BTN_END" value="終　了" onClick="p1('http://intra.dntsv01.johokubank.co.jp/')" class="T00">
					</TD>
				</TR>
			</TABLE>
		</DIV>
	</DIV>
	</FORM>
</BODY>
</HTML>