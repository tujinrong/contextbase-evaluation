/*
 * 作成日: 2017/05/16
 *
 */
package common.base;


import java.sql.Connection;
import java.sql.SQLException;

import common.base.CommonBaseSelect;

/**
 * フレームワーク　ログイン情報検索Baseクラス
 * 
 * @author Minori 山口
 * 
 * @date
 */
public class SelectDaikoSyokuinBase extends CommonBaseSelect {

	/**
	 * コンストラクタ
	 * 
	 * @param connection
	 */
	public SelectDaikoSyokuinBase(Connection connection) {
		super(connection);
	}

	/**

	/**
	 * Ｕ代行可能職員名簿表の検索を実行する
	 * 
	 * @param shokuinNo
	 * @return
	 * @throws SQLException
	 */
	public boolean selectCredit代行(String shokuinNo) throws SQLException {

		try {

			StringBuffer sb = new StringBuffer();

			sb.append("select *");
			sb.append(" from DB2.Ｕ代行可能職員名簿表");
			sb.append(" where 職員番号 = ").append(shokuinNo);
			sb.append(" and credit権限 = 1");

			execute(sb.toString());

		} catch (SQLException e) {
			throw e;
		}

		if (getList() != null) {
			return true;
		} else{
			return false;
		}
	}
}
