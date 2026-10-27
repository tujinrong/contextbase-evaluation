/*
 * 作成日: 2007/05/29
 *
 */
package common.util;

import java.sql.Connection;
import java.sql.SQLException;
import java.text.SimpleDateFormat;
import java.util.TimeZone;

import javax.naming.InitialContext;
import javax.naming.NamingException;
import javax.sql.DataSource;

/**
 * 共通ユーティリティクラス。
 * メソッドは必ずstaticメソッドにする。
 * 定数以外のメンバ変数は持たせない。
 *
 * @author JSC kengo murayama
 *
 * @date	H22.9.3		青木・浅見		センター集約対応なし
 */
public class CommonUtil {

	/**
	 * ＤＢコネクションを取得する
	 * 
	 * @param ic		InitialContext
	 * @param strDS	ＪＤＢＣ名
	 * @return
	 * @throws NamingException
	 * @throws SQLException
	 */
	public static Connection getConnection(InitialContext ic, String strDS)
		throws NamingException, SQLException {

		DataSource ds = (DataSource) ic.lookup(strDS);
		Connection cn = ds.getConnection();
		cn.setAutoCommit(false);

		return cn;
	}

	/**
	 * 本日日付・時刻取得
	 * @param format	日付・時刻フォーマット(「yyyyMMdd」、「HHmmss」など)
	 * 
	 * @return 本日日付
	 */
	public static String getCurrentDate(String format)
	{
		SimpleDateFormat gSDFDate = new SimpleDateFormat(format);
		gSDFDate.setTimeZone(TimeZone.getTimeZone("JST"));
		return gSDFDate.format(new java.util.Date());
	}
}
