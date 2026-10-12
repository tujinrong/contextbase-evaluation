/*
 * 作成日: 2017/05/15
 *
 */
package common;

import java.sql.Connection;
import java.sql.SQLException;
import java.util.List;
import java.util.Map;

import javax.naming.InitialContext;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import common.base.SearchLoginInfoBase;
import common.bean.LoginInfoBean;
import common.util.CommonConverter;

/**
 * 代行店舗選択画面　表示共通アクションクラス
 * （マーケティングプランナー　ログイン情報の書換え）
 *
 * @author Minoei 山口
 * 
 * @date
 *   
 */
public class ViewMenuAction extends CommonAction {

	/**
	 * アクション実行メソッド
	 * 
	 * @param req リクエスト
	 * @param res レスポンス
	 * @return ＪＳＰ名
	 */
	public String perform(HttpServletRequest req, HttpServletResponse res) throws Exception {
		HttpSession session = req.getSession();

		//リクエスト項目の取得（取得したら上書き禁止にするため「final」宣言）
		final String hdn_br = CommonConverter.getAdd0String(req.getParameter("HDN_BR"),3);
		final String hdn_tenpo_name = req.getParameter("HDN_TENPO_NAME");


		//ログイン情報取得
		LoginInfoBean loginInfo = (LoginInfoBean)session.getAttribute(CommonConst.SS_LOGIN_INFO_BEAN);
		String applName =  loginInfo.getアプリケーション名();
		String sUser = loginInfo.get融資系ユーザーＩＤ();
		String login_br = CommonConverter.getAdd0String(loginInfo.get所属店番(),3);
		
		
		//支店の変更がなかった場合はメニュー画面に遷移するだけ
		if((login_br).equals(hdn_br)){
						
			session.removeAttribute(CommonConst.SS_JSP_BEAN);
			return "./JSP/MENU/Menu.jsp";			
			
		//支店の変更があった場合はLoginInfoBeanを再作成する
		}else{

			//ＤＢ検索
			Connection con = null;
	
			try {
				//DB接続
				InitialContext ic = new InitialContext();
				con = getConnection(ic, CommonConst.JDBC_ORACLE_SP2NM);			
				
				String creditUserId = "J" + hdn_br + sUser.substring(4,7);
				
				//ＷＥＢログイン状況表検索データ取得
				SearchLoginInfoBase base = new SearchLoginInfoBase(con);
				base.selectＷＥＢログイン情報表(applName,creditUserId);
				List lsWebLogin = base.getList();
				
				loginInfo.set融資系ユーザーＩＤ(creditUserId);
				loginInfo.set所属店名(hdn_tenpo_name);
				
	
				//検索結果が０件の場合、ログインＮＧ
				if(lsWebLogin == null || lsWebLogin.isEmpty()){
	
					FWLog.error(this.getClass(), "ＷＥＢログイン状況表の取得に失敗");
					throw new Exception();
	
				} else {
	
					Map mapWebLogin = (Map)lsWebLogin.get(0);
	
					loginInfo.set融資系ユーザー名((String)mapWebLogin.get("融資系ユーザー名"));
					loginInfo.set所属店番(CommonConverter.getAdd0String((String)mapWebLogin.get("融資系所属店番"),3));
					loginInfo.set債権書類権限(CommonConverter.convertInt((String)mapWebLogin.get("債権書類権限")));
					loginInfo.set決算書権限(CommonConverter.convertInt((String)mapWebLogin.get("決算書権限")));
					loginInfo.setＣＲＤ権限(CommonConverter.convertInt((String)mapWebLogin.get("ＣＲＤ権限")));
					loginInfo.set格付権限(CommonConverter.convertInt((String)mapWebLogin.get("格付権限")));
					loginInfo.set自己査定権限(CommonConverter.convertInt((String)mapWebLogin.get("自己査定権限")));
	
				}
				
	
				session.removeAttribute(CommonConst.SS_JSP_BEAN);
				session.setAttribute(CommonConst.SS_LOGIN_INFO_BEAN, loginInfo);
				return "./JSP/MENU/Menu.jsp";
	
			} catch (Exception e) {
				try {
					if (con != null) con.rollback();
				} catch (SQLException e1) {
					FWLog.error(e1);
				}
				throw e;
			} finally {
				try {
					if (con != null) con.close();
					con = null;
				} catch (SQLException e1) {
					FWLog.error(e1);
				}
			}
		}			
	}	
}
