/*
 * 作成日: 2007/05/14
 *
 */
package common;

import java.sql.Connection;
import java.sql.SQLException;

import javax.naming.InitialContext;
import javax.naming.NamingException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import common.util.CommonUtil;

/**
 * アクションクラスのスーパークラス。
 * 各業務ロジックのアクションクラスは、必ずこのクラスを継承する。
 *
 * @author JSC kengo murayama
 *
 * @date	H22.9.3		青木・浅見		センター集約対応なし
 */
public abstract class CommonAction {

	/**
	 * (前提)認証チェック済み
	 * (役割)入力データチェック(DB等を使わない)
	 * (役割)データ引き渡して結果をSessionに登録
	 * (役割)次ページのＪＳＰ名を返す
	 * @param req
	 * @param res
	 * @return	ＪＳＰ名
	 */
	public abstract String perform(HttpServletRequest req, HttpServletResponse res) throws Exception;

	/**
	 * 
	 * @param ic		InitialContext
	 * @param strDS	ＪＤＢＣ名
	 * @return
	 * @throws NamingException
	 * @throws SQLException
	 */
	protected Connection getConnection(InitialContext ic, String strDS)
		throws NamingException, SQLException {

		return CommonUtil.getConnection(ic, strDS);
	}
}
