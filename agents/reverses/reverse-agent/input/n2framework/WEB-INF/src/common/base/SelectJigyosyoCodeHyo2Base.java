/*
 * 作成日: 2009/02/17
 *
 */
package common.base;


import java.sql.Connection;
import java.sql.SQLException;

import common.base.CommonBaseSelect;

/**
 * フレームワーク　SYSDWH.Ｊ事業所コード表２検索Baseクラス
 * 
 * @author JSC kengo murayama
 * 
 * @date	H22.9.6		青木・浅見		センター集約対応
 */
public class SelectJigyosyoCodeHyo2Base extends CommonBaseSelect {

	/**
	 * コンストラクタ
	 * 
	 * @param connection
	 */
	public SelectJigyosyoCodeHyo2Base(Connection connection) {
		super(connection);
	}

	/**
	 * SELECT文を実行する
	 * 
	 * @param code
	 * @param edaban
	 * @return
	 * @throws SQLException
	 */
	public boolean select(String code, String edaban) throws SQLException {

		try {

			//ＵＤＢ管理ＤＢの検索
			StringBuffer sb = new StringBuffer();

			sb.append("select 事業所名");
			sb.append(" from N2_DWH.Ｊ事業所コード表２");
			sb.append(" where 店舗コード = ").append(code);
			sb.append(" and 枝番 = ").append(edaban);

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
