/*
 * 作成日: 2014/02/20
 *
 */
package common.base;

import java.sql.Connection;
import java.sql.SQLException;

/**
 * DB2.Ｕ祭日　検索Baseクラス
 * 
 * @author Minori米持
 * 
 */
public class SelectSaijitsuBase extends CommonBaseSelect {

	/**
	 * コンストラクタ
	 * 
	 * @param connection
	 */
	public SelectSaijitsuBase(Connection connection) {
		super(connection);
	}

	/**
	 * SELECT文を実行する
	 * 
	 * @return boolean
	 * @throws SQLException
	 */
	public boolean select() throws SQLException {

		try {

			//Ｕ祭日の検索
			StringBuffer sb = new StringBuffer();

			sb.append("select 日付");
			sb.append(" from DB2.Ｕ祭日");
			sb.append(" order by 日付 ");

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
