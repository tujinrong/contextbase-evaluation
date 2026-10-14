package webon.base;

import java.sql.Connection;
import java.sql.SQLException;

import webon.util.ConvertUtil;

import common.base.CommonBaseSelect;

/**
 * Webon汎用照会ベースクラス　DB2.ＵＪ科目　SelectBaseクラス
 * 
 * @author Minori 吉津
 * 
 * @date	H26.02.24			新規作成
 * @date	2020.02.06	京極　	webonのFW化対応
 */
public class SelectDB2KamokuBase extends CommonBaseSelect {

	public SelectDB2KamokuBase(Connection con) {
		super(con);
		// TODO Auto-generated constructor stub
	}
	//DB名
	public static final String DBNAME = "DB2.ＵＪ科目";
	//DBキー
	public static final String DBKEY_CODE="コード";
	public static final String DBKEY_KOUMOKU1="項目１";
	
	/** 
	  * コードをキーに、項目１（科目名称）を取得
	  * 
	  * @param  code	科目コード 
	  * @return boolean 取得結果
	  * @throws Exception 
	  */
	public boolean selectKamokuNameByCode(String code) throws Exception{

		//SQL編集
		StringBuilder sb = new StringBuilder();
		sb.append("SELECT * FROM ").append(DBNAME);
		sb.append(" WHERE ").append(DBKEY_CODE).append("=").append(ConvertUtil.dbMoldStr(code,2)).append("");
		
		//SQL実行
		try {
			execute(sb.toString());
		} catch (SQLException e) {
			throw e;
		}

		//結果返却
		if (getList() != null) {
			return true;
		} else{
			return false;
		}
	}
	/** 
	  * 項目１（科目名称）をキーに、コードを取得
	  * 
	  * @param  name	科目名称
	  * @return boolean 取得結果
	  * @throws Exception 
	  */
	public boolean selectCodeByKamokuName(String name) throws Exception{

		//SQL編集
		StringBuilder sb = new StringBuilder();
		sb.append("SELECT * FROM ").append(DBNAME);
		sb.append(" WHERE ").append(DBKEY_KOUMOKU1).append("='").append(name).append("'");
		
		//SQL実行
		try {
			execute(sb.toString());
		} catch (SQLException e) {
			throw e;
		}

		//結果返却
		if (getList() != null) {
			return true;
		} else{
			return false;
		}
	}
}
