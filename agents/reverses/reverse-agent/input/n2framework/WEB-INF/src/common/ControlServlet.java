/*
 * 作成日: 2007/05/14
 *
 */
package common;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.Vector;

import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import common.bean.LoginInfoBean;
import common.bean.OtherUserBean;
import common.util.PDFUtil;

/**
 * 共通コントロールサーブレット
 *
 * @author JSC kengo murayama
 *
 * @date	H22.9.3		青木・浅見		センター集約対応なし
 *			H27.8.28	岩渕			ＴＭ連携対応（ＴＭからはgetを認める）
 *			H28.04.02	Minori山口		アプリ超え対応（cif ⇔ unify）
 * 			H30.04.05	Minori山口		【稟議支援】融資情報システムとの連携
 *  		R06.11.11	Minori山口		窓口支援／渉外支援システム連携対応 
 */
public class ControlServlet extends HttpServlet { 

	/**
	 * サーブレット初期化メソッド<BR>
	 * ログ出力クラスを初期化する。
	 */
	public void init() {
		ServletContext scntxt = this.getServletContext();
		String loggerName = scntxt.getInitParameter("LOGGER_NAME");
		FWLog.initLogger(loggerName);
	}

	/**
	 * (注意)ＰＤＦ帳票出力時の２回目のリクエスト処理用
	 * （注意）ＴＭ連携対応により、ＴＭからもgetを認めるよう変更
	 *  ＰＤＦとの判定は、ＴＭ固定パラメータＯＰＫのパラメータ有無で判定
	 * @param req
	 * @param res
	 */

	protected void doGet(HttpServletRequest req, HttpServletResponse res)
		throws ServletException, IOException {

		String tm_opk = req.getParameter("OPK");

		//渉外支援からの識別をget
		String charCommonuid = req.getParameter("charCommonUID");

		if (tm_opk == null && charCommonuid == null) {
			FWLog.info(this.getClass(), "2nd Request for PDF START!!");
			String koteidata[][]={};
			Vector data=new Vector();

			try {
				new PDFUtil().pdfControl(req,res,koteidata,data,0,"",0);//GET
			} catch (Exception e) {
				FWLog.error(e);
			}			
				
		}else{
			try {
				process(req, res);
			} catch (Exception e) {
				FWLog.error(e);
			}
		}
	}
	



	/**
	 * (注意)アクションクラス実行時はdoGetは認めない
	 * 
	 * @param req
	 * @param res
	 */
	protected void doPost(HttpServletRequest req, HttpServletResponse res)
		throws ServletException, IOException {

		FWLog.debug(this.getClass(), "ＦＷログ出力テスト");

		process(req, res);
	}

	/**
	 * (役割)認証チェック
	 * (役割)ページの基本設定を行う
	 * (役割)URLへのディスパッチ
	 * (前提)別ページに行くときは必ずここを通る
	 * @param req
	 * @param res
	 */
	private void process(HttpServletRequest req, HttpServletResponse res)
		throws ServletException, IOException {
		
		//リクエストパラメータのエンコーディング
		req.setCharacterEncoding("Windows-31J");
		//req.setCharacterEncoding("Shift_JIS");
		//req.setCharacterEncoding("EUCJIS");

		//他アプリからの識別をget
		String o_apl  = req.getParameter("Otheflg");
		
		//ＴＭからの識別をget
		String tm_opk = req.getParameter("OPK");
		String dsp = req.getParameter("DSP");
		

		//渉外支援からの識別をget
		String charCommonuid = req.getParameter("charCommonUID");

		//ＴＭ、他アプリ（一元）、現行アプリの識別を行うための変数を初期化
		String OTHER_PASS_WORD ="";
		String applname="";
		String OTHER_USER_ID ="";
		String functionID ="";
		String viewID ="";
		String commandID ="";
		String vFunctionID="";
		String vViewID ="";	
		
		//ＴＭ、他アプリ（一元）、現行アプリの識別を行い、パラメータをSet
		if(tm_opk!=null && !tm_opk.isEmpty()){
			
			
			//窓口タブレット	
			if(dsp == null || dsp.isEmpty()){
	
				ServletContext scntxt = this.getServletContext();
				OTHER_PASS_WORD = scntxt.getInitParameter("TM_LOGIN_PASS");
				applname="unify";
				OTHER_USER_ID = req.getParameter("UID");
				functionID = "common";
				viewID = "Login";
				commandID = "Interface";
				vFunctionID = "custportal";
				vViewID = "CstPtlSm";
	
			//TMから	
			}else{
	
				ServletContext scntxt = this.getServletContext();
				OTHER_PASS_WORD = scntxt.getInitParameter("TM_LOGIN_PASS");
				applname="unify";
				OTHER_USER_ID = req.getParameter("UID");
				functionID = "common";
				viewID = "Login";
				commandID = "Interface";
				vFunctionID = "custportal";
				vViewID = "CstPtlSm";
				
			}
		

		} else if(o_apl != null &&  !o_apl.isEmpty()){
			ServletContext scntxt = this.getServletContext();
			applname=req.getParameter("APPL_NAME");
			OTHER_USER_ID = req.getParameter("OtherUserId");
			functionID = "common";
			viewID = "Login";
			commandID = "Interface";
			vFunctionID = req.getParameter("Package");
			vViewID = req.getParameter("Screen");
			
			if("unify".equals(o_apl)){		
				OTHER_PASS_WORD = scntxt.getInitParameter("TM_LOGIN_PASS");

			}else if("cif".equals(o_apl)){
				OTHER_PASS_WORD = scntxt.getInitParameter("Cif_LOGIN_PASS");
				
			}else if("ringi".equals(o_apl)){
				OTHER_PASS_WORD = scntxt.getInitParameter("TM_LOGIN_PASS");	
				
			}

		//渉外支援から	
		}else if(charCommonuid!=null && !charCommonuid.isEmpty()){
			
			//セッションの取得
			HttpSession session = req.getSession();	
			LoginInfoBean loginInfo = (LoginInfoBean)session.getAttribute(CommonConst.SS_LOGIN_INFO_BEAN);
			

				ServletContext scntxt = this.getServletContext();
				OTHER_PASS_WORD = scntxt.getInitParameter("TM_LOGIN_PASS");
				applname="unify";
				OTHER_USER_ID = charCommonuid;
				functionID = "common";
				viewID = "Login";
				commandID = "Interface";

				String wk_CustNr =req.getParameter("intCustNr");
				String wk_Br = req.getParameter("intBr");

				//顧客番号、店番がない場合はメニューを表示
				if((wk_CustNr == null && wk_Br == null) || (wk_CustNr.isEmpty() && wk_Br.isEmpty())){
					
					if(loginInfo!=null && loginInfo.isログイン可否()){
				
						functionID = req.getParameter("FUNCTION_ID");
						viewID = req.getParameter("VIEW_ID");
						commandID = req.getParameter("COMMAND_ID");
						
					}else{

						vFunctionID = "list";
						vViewID = "MenuSyougai";
					}


				//顧客番号、店番がある場合は大ポータルを表示	
				}else{

					if(loginInfo!=null && loginInfo.isログイン可否()){
											
						functionID = req.getParameter("FUNCTION_ID");
						viewID = req.getParameter("VIEW_ID");
						commandID = req.getParameter("COMMAND_ID");
					
					}else{
						
						vFunctionID = "custportal";
						vViewID = "CstPtlLg";	
					}
						
				}


		} else {
			functionID = req.getParameter("FUNCTION_ID");
			viewID = req.getParameter("VIEW_ID");
			commandID = req.getParameter("COMMAND_ID");
			//String actionPackage = functionID.toLowerCase();
		}


//リクエスト等のログへの表示――――→本番時はコメントアウト	
//		String DS_opk = req.getParameter("OPK");
//		FWLog.debug(getClass(), "●res_OPK="+DS_opk);		
//		String DS_uid = req.getParameter("UID");
//		FWLog.debug(getClass(), "●res_UID="+DS_uid);	
//		String DS_cst = req.getParameter("CST");
//		FWLog.debug(getClass(), "●res_CST="+DS_cst);	
//		String DS_kam = req.getParameter("KAM");
//		FWLog.debug(getClass(), "●res_KAM="+DS_kam);	
//		String DS_koz = req.getParameter("KOZ");
//		FWLog.debug(getClass(), "●res_KOZ="+DS_koz);	
//		String DS_tnp = req.getParameter("TNP");
//		FWLog.debug(getClass(), "●res_TNP="+DS_tnp);
//		String DS_pa1 = req.getParameter("PA1");
//		FWLog.debug(getClass(), "●res_PA1="+DS_pa1);
//		String DS_pa2 = req.getParameter("PA2");
//		FWLog.debug(getClass(), "●res_PA2="+DS_pa2);
//		String DS_pa3 = req.getParameter("PA3");
//		FWLog.debug(getClass(), "●res_PA3="+DS_pa3);
//		String DS_pa4 = req.getParameter("PA4");
//		FWLog.debug(getClass(), "●res_PA4="+DS_pa4);
//		String DS_pa5 = req.getParameter("PA5");
//		FWLog.debug(getClass(), "●res_PA5="+DS_pa5);					
//		FWLog.debug(getClass(), "★OTHER_PASS_WORD="+OTHER_PASS_WORD);
//		FWLog.debug(getClass(), "★OTHER_USER_ID="+OTHER_USER_ID);
//		FWLog.debug(getClass(), "★applname="+applname);
//		FWLog.debug(getClass(), "★functionID="+functionID);
//		FWLog.debug(getClass(), "★viewID="+viewID);
//		FWLog.debug(getClass(), "★commandID="+commandID);
//		FWLog.debug(getClass(), "★vFunctionID="+vFunctionID);
//		FWLog.debug(getClass(), "★vViewID="+vViewID);
//		
		
		
		//セッションの開始
		HttpSession session = req.getSession();

		//セッションに格納
		if(tm_opk != null || o_apl != null || charCommonuid !=null) {
			
			OtherUserBean OtherUserInfo = new OtherUserBean();
			OtherUserInfo.setユーザ(OTHER_USER_ID);
			OtherUserInfo.setパスワード(OTHER_PASS_WORD);
			OtherUserInfo.setアプリケーション名(applname);
			OtherUserInfo.setパッケージ名(vFunctionID);
			OtherUserInfo.set画面ＩＤ(vViewID);
			session.setAttribute(CommonConst.SS_OTHER_INFO_BEAN,OtherUserInfo);
		}

		//	処理内で使う変数の宣言
		String strUrl;
		String userId = null;

		//アクションクラス実行ＩＤの取得(ＴＭ連携時に場所移動)
		//String functionID = req.getParameter("FUNCTION_ID");
		//String viewID = req.getParameter("VIEW_ID");
		//String commandID = req.getParameter("COMMAND_ID");
		
		String actionPackage = functionID.toLowerCase();

		//ログイン情報をチェックし、ＯＫならアクションクラス実行。
		//ログイン処理の場合、無条件にログインアクションクラスを実行。
		if (!viewID.equals("Login") && !checkLogin(session)) {
			session.setAttribute(CommonConst.ERROR_MSG,"ログイン時間切れです。再度ログインしてください。");
			strUrl = CommonConst.ERROR_JSP;
		} else {
			//req.setCharacterEncoding("MS932");

			//ログアウト処理の場合、処理前の職員番号を取得
			if(viewID.equals("Logout")) {
				LoginInfoBean loginInfo = (LoginInfoBean)session.getAttribute(CommonConst.SS_LOGIN_INFO_BEAN);
				userId = loginInfo.get職員番号();
			}

			//運用時間帯チェック
			if(!OperatePermission.check(actionPackage)){
				session.setAttribute(CommonConst.ERROR_MSG,"現在メンテナンス中のため画面を表示できません。");
				strUrl = CommonConst.ERROR_JSP;
			} else {
				CommonAction action;

				try{
					
					//アクションクラスの実行
					//System.out.println("アクションクラス名：" + actionPackage + "." + viewID + commandID + "Action");
					Class cls = Class.forName(actionPackage + "." + viewID + commandID + "Action");
					action = (CommonAction)cls.newInstance();
					strUrl = action.perform(req, res);
				}catch (Exception e){
					e.printStackTrace();
					//アクションクラスでエラーが発生した場合、エラーログ出力およびエラー画面に遷移。
					FWLog.error(e);
					session.setAttribute(CommonConst.ERROR_MSG, "アプリケーションエラーが発生しました。<BR>システム管理者に連絡してください。");
					strUrl = CommonConst.ERROR_JSP;
				}
			}
		}

		//ログアウト処理以外の場合、処理後の職員番号を取得
		if(!viewID.equals("Logout")) {
			LoginInfoBean loginInfo = (LoginInfoBean)session.getAttribute(CommonConst.SS_LOGIN_INFO_BEAN);
			if (loginInfo != null){
				userId = loginInfo.get職員番号();
			}
		}

		//カウンターシフト処理
		Map mapCS = new HashMap();
		mapCS.put("機能ＩＤ", functionID);
		mapCS.put("画面ＩＤ", viewID);
		mapCS.put("コマンドＩＤ", commandID);
		mapCS.put("アクションＩＤ", viewID + commandID);

		//画面入力エラーの場合は、サブメッセージ画面を登録
		if(session.getAttribute(CommonConst.ERROR_MSG_LIST) != null) {
			mapCS.put("ＪＳＰ名", "./JSP/COMMON/SubMessage.jsp");
		} else {
			mapCS.put("ＪＳＰ名", strUrl);
		}

		mapCS.put("ユーザーＩＤ", userId);

		CounterShift.countUp(mapCS);

		//ＪＳＰ画面への遷移
		if(strUrl != null && !"PDF".equals(strUrl) && !"CSV".equals(strUrl)){
			//ページ基本設定
			res.setContentType("text/html; charset=Windows-31J");
			res.setHeader("Expires", "Sat, 01 Jan 2000 00:00:00 GMT");
			res.setHeader("cache-control", "no-store");
			res.setHeader("Pragma", "no-cache");

			req.getRequestDispatcher(strUrl).forward(req, res);
		}
	}

	/**
	 * 
	 * ログインの状態をgetAttributeして調べ、
	 * ログインが行われていればtrueを戻り値として返す。
	 * 行われていない場合falseを返す。
	 * 
	 * @param session HttpSession 
	 * @return true：ログインＯＫ、false：ログインＮＧ
	 */
	private boolean checkLogin(HttpSession session){
		LoginInfoBean loginInfo = (LoginInfoBean)session.getAttribute(CommonConst.SS_LOGIN_INFO_BEAN);

		if (loginInfo != null && loginInfo.isログイン可否()) {
			return true;
		}

		return false;
	}
}
