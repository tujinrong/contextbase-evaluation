package webon.base;

import java.sql.Connection;
import java.sql.SQLException;

import webon.util.ConvertUtil;

import common.base.CommonBase;

/**
 * Webon汎用照会ベースクラス　パス管理ステータスUpdate Baseクラス
 * 
 * @author Minori 加瀬
 * 
 * @date	H25.12.30	加瀬		新規作成
 * @date	2020.02.06	京極　	webonのFW化対応
 */
public class UpdatePathMngStatBase  extends CommonBase{

	public UpdatePathMngStatBase(Connection connection) {
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
	  * 参照・更新用のレコードを更新する
	  * 
	  * @param String 接続先
	  * @param int パス使用数
	  * @throws SQLException
	  */
	public void updatePathNo(String ip,int pathNum) throws SQLException {

		//SQL編集
		StringBuffer sb = new StringBuffer();

		sb.append("UPDATE ").append(DBNAME);

		sb.append(" SET");
		sb.append(" ").append(DBKEY_PATHNUM).append("=").append(pathNum);
		sb.append(",").append(DBKEY_UPDATE).append("=").append(ConvertUtil.dbGetDate());
		sb.append(",").append(DBKEY_UPTIME).append("=").append(ConvertUtil.dbGetTime());

		sb.append(" WHERE ").append(DBKEY_ACCESSPOINT).append("='").append(ip).append("'");

		try {
			execute(sb.toString());
		} catch (SQLException e) {
			throw e;
		}
		
	}
	/** 
	  * 参照・更新用のレコードを更新する
	  * 
	  * @param String 接続先
	  * @param int パス使用数
	  * @param int 制限パス使用数
	  * @throws SQLException
	  */
	public void updatePathNo(String ip,int pathNum,int pathNumLim) throws SQLException {

		//SQL編集
		StringBuffer sb = new StringBuffer();

		sb.append("UPDATE ").append(DBNAME);

		sb.append(" SET");
		sb.append(" ").append(DBKEY_PATHNUM).append("=").append(pathNum);
		sb.append(",").append(DBKEY_LIMPATHNUM).append("=").append(pathNumLim);
		sb.append(",").append(DBKEY_UPDATE).append("=").append(ConvertUtil.dbGetDate());
		sb.append(",").append(DBKEY_UPTIME).append("=").append(ConvertUtil.dbGetTime());

		sb.append(" WHERE ").append(DBKEY_ACCESSPOINT).append("='").append(ip).append("'");

		try {
			execute(sb.toString());
		} catch (SQLException e) {
			throw e;
		}
		
	}
}
