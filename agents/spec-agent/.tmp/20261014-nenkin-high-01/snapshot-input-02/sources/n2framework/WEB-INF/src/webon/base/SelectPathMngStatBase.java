package webon.base;

import java.sql.Connection;
import java.sql.SQLException;

import common.base.CommonBaseSelect;

/**
 * Webon汎用照会ベースクラス　パス管理ステータス Select Baseクラス
 * 
 * @author Minori 加瀬
 * 
 * @date	H25.12.30	加瀬		新規作成
 * @date	2020.02.06	京極　	webonのFW化対応
 */
public class SelectPathMngStatBase extends CommonBaseSelect{

	public SelectPathMngStatBase(Connection connection) {
		super(connection);
		// TODO Auto-generated constructor stub
	}
	//DB名
	public static final String DBNAME = "NAVI.ＵＳパス管理ステータス";
	//DBキー
	public static final String DBKEY_ACCESSPOINT="接続先";
	public static final String DBKEY_PATHNUM="パス使用数";
	public static final String DBKEY_LIMPATHNUM="制限パス使用数";
	public static final String DBKEY_MKDATE = "作成日";
	public static final String DBKEY_MKTIME = "作成時刻";
	public static final String DBKEY_UPDATE = "更新日";
	public static final String DBKEY_UPTIME = "更新時刻";
	/** 
	  * パス使用数を更新前提で取得する(更新ロックをかける)
	  * 
	  * @param String 接続先(IPアドレス)
	  * @return boolean
	  * @throws SQLException
	  */
	public boolean selectPathNoForUp(String ip) throws SQLException {

		//SQL編集
		StringBuilder sb = new StringBuilder();
		sb.append("SELECT ").append(DBKEY_PATHNUM);
		sb.append(",").append(DBKEY_LIMPATHNUM);
		sb.append(" FROM ").append(DBNAME);
		sb.append(" WHERE ").append(DBKEY_ACCESSPOINT).append("='").append(ip).append("'");
		sb.append(" FOR UPDATE" );
		sb.append(" WAIT ").append("10");

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
	  * 該当する接続先のレコードが存在するか確認する
	  * 
	  * @param String 接続先(IPアドレス)
	  * @return boolean(1件以上でTRUE)
	  * @throws SQLException
	  */
	public boolean checkPathNo(String ip) throws SQLException {

		//SQL編集
		StringBuilder sb = new StringBuilder();
		sb.append("SELECT ").append(DBKEY_PATHNUM);
		sb.append(",").append(DBKEY_LIMPATHNUM);
		sb.append(" FROM ").append(DBNAME);
		sb.append(" WHERE ").append(DBKEY_ACCESSPOINT).append("='").append(ip).append("'");

		//SQL実行
		try {
			execute(sb.toString());
		} catch (SQLException e) {
			throw e;
		}
		
		//結果返却
		if (getList() != null) {
			if (getList().size()>0){
				return true;
			} else {
				return false;
			}
		} else{
			return false;
		}
	}

}
