/**
 * 作成日: 2007/06/01
 *
 */
package common.base;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.Vector;

import common.FWLog;

/**
 * データウェアハウス　ＰＤＦ検索Baseのスーパークラス
 * ＰＤＦ検索を行うBaseクラスは、必ずこのクラスを継承する。
 * 
 * @author JSC kengo murayama
 * 
 * @date	H22.9.6		青木・浅見		センター集約対応なし
 */
public class CommonBaseSelectPDF extends CommonBaseSelect {

	/**
	 * コンストラクタ
	 * 
	 * @param connection
	 */
	public CommonBaseSelectPDF(Connection connection) {
		super(connection);
	}

	/**
	 * SQLのSELECT文を実行する。
	 * 
	 * @param sql ＳＱＬ文
	 */
	protected void executeVector(String sql) throws SQLException{

		Statement stmt = null;
		ResultSet rs = null;

		try {
			stmt = getConnection().createStatement();
			rs = stmt.executeQuery(sql);

			//ＳＱＬ実行が正常終了したら、debug ログ出力
			if(FWLog.isDebug()){
				FWLog.debug(this.getClass(), sql);
			}

			setList(makeVector(rs));

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
	 * ResultSetからVector(［行数］[列数])を作成し返す
	 *
	 * @param  rs   データベースの検索結果（ResultSet型の変数名）
	 * @return Vector(［行数］[列数])
	 */
	private Vector makeVector(ResultSet rs) 
      	throws SQLException{

       	Vector vecData = new Vector();

		ResultSetMetaData meta = rs.getMetaData();

		// ResultSetの全データをVectorへ格納する
		while (rs.next()) {
	        Vector row = new Vector();
			for (int i=0; i < meta.getColumnCount(); i++) {
				if(rs.getString(i+1) == null){
					row.addElement("");
				}
				else {
					row.addElement(rs.getString(i+1));
				}
			}
			vecData.addElement(row);
		}

		return vecData;
	}
}
