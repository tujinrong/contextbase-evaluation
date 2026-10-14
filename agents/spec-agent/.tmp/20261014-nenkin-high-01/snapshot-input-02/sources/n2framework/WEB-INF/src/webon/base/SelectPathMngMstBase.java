package webon.base;

import java.sql.Connection;
import java.sql.SQLException;

import common.base.CommonBaseSelect;

/**
 * Webon汎用照会ベースクラス　パス管理マスタ Select Baseクラス
 * 
 * @author Minori 加瀬
 * 
 * @date	H25.12.30	加瀬		新規作成
 * @date	2020.02.06	京極　	webonのFW化対応
 */
public class SelectPathMngMstBase extends CommonBaseSelect {

	public SelectPathMngMstBase(Connection connection) {
		super(connection);
		// TODO Auto-generated constructor stub
	}
	//DB名
	public static final String DBNAME = "NAVI.ＵＭパス管理マスタ";
	//DBキー
	public static final String DBKEY_ACCESSPOINT="接続先";
	public static final String DBKEY_PATHMAX="パス最大数";
	public static final String DBKEY_LIMPATHMAX="制限パス最大数";
	/** 
	  * マスタＤＢから値を読込
	  * 
	  * @param String 接続先（IPアドレス）
	  * @return boolean 取得結果
	  * @throws SQLException 
	  */
	public boolean selectPathMax(String ip) throws SQLException {
		//SQL編集
		StringBuilder sb = new StringBuilder();
		sb.append("SELECT *");
		sb.append(" FROM ").append(DBNAME);
		sb.append(" WHERE ").append(DBKEY_ACCESSPOINT).append("='").append(ip).append("'");

		try {
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
