/*
 * 作成日: 2007/05/29
 *
 */
package common.base;

import java.sql.Connection;
import java.sql.SQLException;

/**
 * データウェアハウス　業種コードテーブル検索Baseクラス
 * 
 * @author JSC kengo murayama
 * 
 * @date	H22.9.6		青木・浅見		センター集約対応
 */
public class SelectCodeGyosyuBase extends CommonBaseSelectCode {

	/**
	 * コンストラクタ
	 * 
	 * @param connection
	 */
	public SelectCodeGyosyuBase(Connection connection) {
		super(connection);
	}

	/**
	 * 
	 * SELECT文（コードをMap形式で取得）を実行する
	 * 
	 * @return boolean
	 * @throws SQLException
	 */
	public boolean select() throws SQLException {

		try {

			//ＳＱＬ実行
			executeMap("SELECT コード,項目１ FROM DB2.ＵＪ業種 ORDER BY コード");

		} catch (SQLException e) {
			throw e;
		}

		if (getMap() != null) {
			return true;
		} else{
			return false;
		}
	}

}
