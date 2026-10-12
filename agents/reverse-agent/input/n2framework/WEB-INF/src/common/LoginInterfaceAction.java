/*
 * 作成日: 2007/05/14
 *
 */
package common;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import common.bean.LoginInfoBean;
import common.bean.OtherUserBean;
import common.util.CommonConverter;

/**
 * フレームワーク　ログインインターフェイス分岐処理アクションクラス
 *
 * @author H27.8.28	岩渕 * 
 * 
 * @date	H30.04.05	Minori山口		【稟議支援】融資情報システムとの連携
 * 
 */
public class LoginInterfaceAction extends LoginAction {

	/**
	 * アクション実行メソッド
	 * 
	 * @param req リクエスト
	 * @param res レスポンス
	 * @return ＪＳＰ名
	 */
	public String perform(HttpServletRequest req, HttpServletResponse res) throws Exception {
		
		//セッションから情報取得
		HttpSession session = req.getSession();	
		LoginInfoBean loginInfo = (LoginInfoBean)session.getAttribute(CommonConst.SS_LOGIN_INFO_BEAN);
		OtherUserBean OtherUserInfo = (OtherUserBean)session.getAttribute(CommonConst.SS_OTHER_INFO_BEAN);
						
		String dwhUserId =req.getParameter("DWH_USER_ID");		
		String applName =req.getParameter("APPL_NAME");
					
		//戻り先画面名
		String strUrl = "";
		
		//稟議支援（調査カード印刷の場合はLoginAction.javaは動かず、ログイン可否をtrueにする！）
		if("ringi".equals(applName) && (("".equals(dwhUserId) || dwhUserId == null))){
			
			//アクションクラスの実行
			String functionID = "ringi";
			String viewID = "RingiPrintInsatu";
			String actionPackage = functionID.toLowerCase();
			Class cls = Class.forName(actionPackage + "." + viewID  + "Action");
			CommonAction action = (CommonAction)cls.newInstance();
			
			
			//ログイン情報Beanをセッションにセット
			loginInfo = new LoginInfoBean();
			loginInfo.setログイン可否(true);
			session.setAttribute(CommonConst.SS_LOGIN_INFO_BEAN, loginInfo);
			
			strUrl = action.perform(req, res);
			return strUrl;
		}

		
		//Login判定
		if(loginInfo!=null && loginInfo.isログイン可否()){
			//ログイン中
			String syokuinid = OtherUserInfo.getユーザ();		
			String userid = loginInfo.get職員番号();
				if(CommonConverter.getAdd0String(syokuinid,8) != userid){
					super.perform(req, res);	
				}
		}else{
			//未ログイン
			super.perform(req, res);
		}
	
//		アクションクラスの実行
//		System.out.println("アクションクラス名：" + actionPackage + "." + viewID + commandID + "Action");
		String functionID = OtherUserInfo.getパッケージ名();
		String viewID = OtherUserInfo.get画面ＩＤ();
		String actionPackage = functionID.toLowerCase();
		Class cls = Class.forName(actionPackage + "." + viewID  + "Action");
		CommonAction action = (CommonAction)cls.newInstance();
		
		strUrl = action.perform(req, res);
        //本番時コメントはずす↑
		//テスト時にコメントアウトする↓
		//strUrl = "./JSP/MENU/Menu.jsp";
				
		return strUrl;
		
	}
}


