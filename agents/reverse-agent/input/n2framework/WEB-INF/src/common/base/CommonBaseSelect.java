/*
 * 作成日: 2005/06/01
 *
 */
package common.base;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import common.FWLog;

/**
 * データウェアハウス　検索Baseのスーパークラス
 * 各検索Baseクラスは、必ずこのクラスを継承する。
 * 
 * @author JSC kengo murayama
 * 
 * @date	H22.9.3		青木・浅見		センター集約対応なし
 */
public abstract class CommonBaseSelect extends CommonBase {

	/** 検索結果List */
	private List list = null;

	/**
	 * コンストラクタ
	 * 
	 * @param connection
	 */
	public CommonBaseSelect(Connection connection) {
		super(connection);
	}

	/**
	 * SQLのSELECT文を実行する。
	 * 
	 * @param sql ＳＱＬ文
	 */
	public void execute(String sql) throws SQLException{

		Statement stmt = null;
		ResultSet rs = null;

		try {
			stmt = getConnection().createStatement();
			rs = stmt.executeQuery(sql);

			//ＳＱＬ実行が正常終了したら、debug ログ出力
			if(FWLog.isDebug()){
				FWLog.debug(this.getClass(), sql);
			}

			setList(convertResultSetToList(rs));

			if(getList() != null){
				setCount(getList().size());
			}

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
	private List convertResultSetToList(ResultSet rs) throws SQLException{

		List ls = new ArrayList();
			
		while (rs.next()) {

			Map map = new HashMap();
			ResultSetMetaData rsmd = rs.getMetaData();

			for(int i=1; i <= rsmd.getColumnCount(); i++){
				String name = rsmd.getColumnName(i);
				String str = rs.getString(name);

				if(str == null){
					map.put(name,"");
				} else {
					map.put(name,str.trim());
				}
			}

			ls.add(map);
		}

		return ls;
	}

	/**
	 * @return
	 */
	public List getList() {
		return list;
	}

	/**
	 * @param list
	 */
	public void setList(List list) {
		this.list = list;
	}
}
