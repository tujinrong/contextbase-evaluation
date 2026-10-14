/*
 * 作成日: 2007/05/29
 *
 */
package common.base;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.HashMap;
import java.util.Map;

import common.FWLog;

/**
 * データウェアハウス　コード検索Baseのスーパークラス
 * 各コード検索Baseクラスは、必ずこのクラスを継承する。
 * 
 * @author JSC kengo murayama
 * 
 * @date	H22.9.6		青木・浅見		センター集約対応なし
 */
public abstract class CommonBaseSelectCode extends CommonBaseSelect {

	/** 検索結果Map */
	private Map map = null;

	/**
	 * コンストラクタ
	 * 
	 * @param connection
	 */
	public CommonBaseSelectCode(Connection connection) {
		super(connection);
	}

	/**
	 * SQLのSELECT文を実行する。
	 * 
	 * @param sql ＳＱＬ文
	 */
	public void executeMap(String sql) throws SQLException{

		Statement stmt = null;
		ResultSet rs = null;

		try {
			stmt = getConnection().createStatement();
			rs = stmt.executeQuery(sql);

			//ＳＱＬ実行が正常終了したら、debug ログ出力
			if(FWLog.isDebug()){
				FWLog.debug(this.getClass(), sql);
			}

			setMap(convertResultSetToMap(rs));

		} catch (SQLException e) {
			FWLog.error(sql);
			throw e;

		} finally {
			if (rs != null) rs.close();
			if (stmt != null) stmt.close();
			rs = null;
			stmt = null;
		}
	}

	/**
	 * 
	 * ResultSetをList(Map)の配列に変換する。
	 * 
	 * @param	rs	ResultSet
	 * @return ls	変換されたList(Map)形式のデータ
	 */
	private Map convertResultSetToMap(ResultSet rs) throws SQLException{

		Map mapRS = new HashMap();

		while (rs.next()) {

			String code = rs.getString(1);
			String value = rs.getString(2);
			
			if(value == null){
				mapRS.put(code,"");
			} else {
				mapRS.put(code,value.trim());
			}
		}

		return mapRS;
	}

	/**
	 * @return map を戻します。
	 */
	public Map getMap() {
		return map;
	}

	/**
	 * @param map 設定する map。
	 */
	private void setMap(Map map) {
		this.map = map;
	}

}
