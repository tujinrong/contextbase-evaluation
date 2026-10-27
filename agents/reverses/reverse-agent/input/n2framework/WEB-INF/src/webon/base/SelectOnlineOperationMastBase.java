package webon.base;

import java.sql.Connection;
import java.sql.SQLException;

import common.base.CommonBaseSelect;

/**
 * Webon汎用照会ベースクラス　NAVI.ＵＪオンラインＯＰマスタSelect Baseクラス
 * 
 * @author Minori 吉津
 * 
 * @date	H24.10.23	吉津		新規作成
 * @date	2020.02.06	京極　	webonのFW化対応
 */
public class SelectOnlineOperationMastBase extends CommonBaseSelect {

	/**
	 * コンストラクタ
	 * 
	 * @param Connection
	 */
	public SelectOnlineOperationMastBase(Connection connection) {
		super(connection);
	}
	public static final String DBNAME = "NAVI.ＵＭオンラインＯＰマスタ";
	public static final String DBKEY_OPEID = "オペレーションＩＤ";
	public static final String DBKEY_INFILENAME = "画面定義体ファイル名";
	public static final String DBKEY_OUTFILENAME = "出力定義体ファイル名";
	public static final String DBKEY_STYLESHEET = "出力スタイルシート";
	public static final String DBKEY_COMMENT = "コメント";
	
	/** 
	  * オペレーションＩＤをキーにレコードを取得する
	  * (全項目)
	  * @param	String 	キー
	  *	
	  * @return boolean
	  * @throws SQLException
	  */
	public boolean selectByOperationId(String operationId) throws SQLException {

		// ＳＱＬ編集
		StringBuilder sb = new StringBuilder();
		sb.append("SELECT *");
		sb.append(" FROM ").append(DBNAME);
		sb.append(" WHERE ").append(DBKEY_OPEID).append("='").append(operationId).append("'");

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
