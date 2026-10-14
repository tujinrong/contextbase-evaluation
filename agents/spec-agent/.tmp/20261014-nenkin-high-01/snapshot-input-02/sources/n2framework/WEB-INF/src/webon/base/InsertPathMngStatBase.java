package webon.base;

import java.sql.Connection;
import java.sql.SQLException;

import webon.util.ConvertUtil;


import common.base.CommonBase;

/**
 * Webon汎用照会ベースクラス　パス管理ステータスInsert Baseクラス
 * 
 * @author Minori 京極
 * 
 * @date	2020.02.13		京極		新規作成
 */
public class InsertPathMngStatBase extends CommonBase{

	public InsertPathMngStatBase(Connection connection) {
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
	public static final int DBVAL_INITPATHNUM = 0;
	public static final int DBVAL_INITPATHNUMLIM = 0;
	/** 
	  * レコードを新規に作成する
	  * 
	  * @param String 接続先(IPアドレス)
	  * @throws Exception 
	  */
	public void insertPathNo(String ip) throws Exception {

		//SQL編集
		StringBuffer sb = new StringBuffer();

		sb.append("INSERT INTO ").append(DBNAME);

		sb.append(" (").append(DBKEY_ACCESSPOINT);
		sb.append(" ,").append(DBKEY_PATHNUM);
		sb.append(" ,").append(DBKEY_LIMPATHNUM);
		sb.append(" ,").append(DBKEY_MKDATE);
		sb.append(" ,").append(DBKEY_MKTIME);
		sb.append(" ,").append(DBKEY_UPDATE);
		sb.append(" ,").append(DBKEY_UPTIME);
		sb.append(" )");

		sb.append(" VALUES");
		sb.append("(").append(ConvertUtil.dbMoldStr(ip, 15));
		sb.append(",").append(ConvertUtil.dbMoldInt(DBVAL_INITPATHNUM, 3));
		sb.append(",").append(ConvertUtil.dbMoldInt(DBVAL_INITPATHNUMLIM, 3));
		sb.append(",").append(ConvertUtil.dbGetDate());
		sb.append(",").append(ConvertUtil.dbGetTime());
		sb.append(",").append(ConvertUtil.dbGetDate());
		sb.append(",").append(ConvertUtil.dbGetTime());
		sb.append(")");
		
		try {
			execute(sb.toString());
		} catch (SQLException e) {
			throw e;
		}
		
	}
	

}
