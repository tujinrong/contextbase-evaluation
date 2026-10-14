package webon.base;

import java.sql.Connection;
import java.sql.SQLException;

import common.base.CommonBaseSelect;

/**
 * Webon汎用照会ベースクラス　機能マスタSelect Baseクラス
 * 
 * @author Minori 加瀬
 * 
 * @date	H24.10.30	加瀬		新規作成
 * @date	2020.02.06	京極　	webonのFW化対応
 */
public class SelectFunctionMasterBase extends CommonBaseSelect{

	/**
	 * コンストラクタ
	 * 
	 * @param Connection
	 */
	
	public SelectFunctionMasterBase(Connection connection) {
		super(connection);
	}
	/** 
	  * 参照ＤＢ（NAVI.ＵＪ機能マスタ）
	  * 機能名をキーにレコードを取得する(全項目)
	  *
	  * @param	String		機能名
	  * @param	String		キー名
	  *	
	  * @return boolean
	  * @throws SQLException
	  */
	
	
	public boolean selectValueByFunctionIdAndKey (String functionId,String key) throws SQLException {
		try {
			// ＳＱＬ編集
			StringBuffer sb = new StringBuffer();
			sb.append("select 値 from NAVI.ＵＭ機能マスタ ");
			sb.append("where 機能名='"+ functionId +"'");
			sb.append("and キー名='"+ key +"'");
			
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
	
	public boolean selectByFunctionId (String functionId) throws SQLException {
		try {
			// ＳＱＬ編集
			StringBuffer sb = new StringBuffer();
			sb.append("select * from NAVI.ＵＪ機能マスタ ");
			sb.append("where 機能名='"+ functionId +"'");

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
