/*
 * 作成日: 2007/05/14
 *
 */
package common;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

/**
 * データウェアハウス　ログアウト処理アクションクラス
 * 
 * @author JSC kengo murayama
 * 
 * @date	H22.9.6		青木・浅見		センター集約対応なし
 */
public class LogoutAction extends CommonAction {
	/**
	 * アクション実行メソッド
	 * 
	 * @param req リクエスト
	 * @param res レスポンス
	 * @return ＪＳＰ名
	 */
	public String perform(HttpServletRequest req, HttpServletResponse res) {
		HttpSession session = req.getSession();
		session.removeAttribute(CommonConst.SS_JSP_BEAN);
		session.removeAttribute(CommonConst.SS_LOGIN_INFO_BEAN);

//		session.setAttribute("login","false");
//		session.setAttribute("userId","");
		return "./JSP/MENU/Login.jsp";
	}
}
