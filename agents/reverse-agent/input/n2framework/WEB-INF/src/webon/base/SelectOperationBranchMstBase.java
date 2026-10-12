package webon.base;

import java.sql.Connection;
import java.sql.SQLException;

import common.base.CommonBaseSelect;

/**
 * Webon汎用照会ベースクラス　稼動店舗管理マスタSelect Baseクラス
 * 
 * @author Minori 吉津
 * 
 * @date	H24.04.15	吉津			新規作成
 * @date	2020.02.06	京極　		webonのFW化対応
 */
public class SelectOperationBranchMstBase extends CommonBaseSelect {
	//DB名
	final String dbname = "NAVI.ＵＪ稼動店舗管理マスタ";
	//DBキー
	public static final String DBKEY_BRANGHNO = "店番";
	public static final String DBKEY_TRADEBRCODE = "取引店舗コード";
	public static final String DBKEY_ACCESSPOINT  = "接続先";
	public static final String DBKEY_ACTIVEFLAG = "取引可能フラグ";
	
	/**
	 * コンストラクタ
	 * 
	 * @param Connection
	 */
	public SelectOperationBranchMstBase(Connection con) {
		super(con);
		// TODO Auto-generated constructor stub
	}
	/** 
	  * 参照ＤＢ（NAVI.ＵＪ稼動店舗管理マスタ）
	  * 全レコードを取得する(全項目)
	  *	
	  * @return boolean
	  * @throws SQLException
	  */
	public boolean selectOperationBranchNo() throws SQLException {
		//SQL編集
		StringBuffer sb = new StringBuffer();
		sb.append("SELECT *");
		sb.append(" FROM " + dbname);
		sb.append(" ORDER BY " + DBKEY_BRANGHNO);
		

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
	/** 
	  * 参照ＤＢ（NAVI.ＵＪ稼動店舗管理マスタ）
	  * 店番をキーに該当するレコードを取得する
	  * @param  String 店番	
	  *
	  * @return boolean
	  * @throws SQLException
	  */
	public boolean selectByBrno(String brno) throws SQLException {
		//SQL編集
		StringBuffer sb = new StringBuffer();
		sb.append("SELECT ");
		sb.append(" ").append(DBKEY_BRANGHNO);
		sb.append(",").append(DBKEY_TRADEBRCODE);
		sb.append(",").append(DBKEY_ACCESSPOINT);
		sb.append(",").append(DBKEY_ACTIVEFLAG);
		sb.append(" FROM ").append(dbname);
		sb.append(" WHERE ").append(DBKEY_BRANGHNO).append("=").append(brno);

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
	/** 
	  * 参照ＤＢ（NAVI.ＵＪ稼動店舗管理マスタ）
	  * 店番をキーに、取引可能店舗のレコードを取得する
	  * @param  String 店番	
	  *
	  * @return boolean
	  * @throws SQLException
	  */
	public boolean selectNotActiveByBrno(String brno) throws SQLException {
		//SQL編集
		StringBuffer sb = new StringBuffer();
		sb.append("SELECT ");
		sb.append(" ").append(DBKEY_BRANGHNO);
		sb.append(",").append(DBKEY_TRADEBRCODE);
		sb.append(",").append(DBKEY_ACCESSPOINT);
		sb.append(",").append(DBKEY_ACTIVEFLAG);
		sb.append(" FROM ").append(dbname);
		sb.append(" WHERE ").append(DBKEY_BRANGHNO).append("=").append(brno);
		sb.append(" AND ").append(DBKEY_ACTIVEFLAG).append("=").append("'1'");

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
