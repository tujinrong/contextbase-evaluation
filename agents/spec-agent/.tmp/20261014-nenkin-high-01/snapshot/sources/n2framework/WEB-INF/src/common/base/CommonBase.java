/*
 * 作成日: 2005/06/01
 *
 */
package common.base;

import java.sql.Connection;
import java.sql.SQLException;
import java.sql.Statement;

import common.FWLog;

/**
 * データウェアハウス　Baseクラスのスーパークラス。
 * 各Baseクラスは、必ずこのクラスを継承する。
 * 
 * @author JSC kengo murayama
 *
 * @date	H22.9.3		青木・浅見		センター集約対応なし
 */
public abstract class CommonBase {

	/** ＤＢコネクション */
	private Connection connection;

	/** 処理件数 */
	private int count;

	/**
	 * コンストラクタ
	 * 
	 * @param connection
	 */
	public CommonBase(Connection connection) {
		this.connection = connection;
		this.count = 0;
	}

	/**
	 * 
	 * SQLのINSERT文、UPDATE文、DELETE文を実行する。
	 * 
	 */
	public void execute(String sql) throws SQLException{
		Statement stmt = null;
		stmt = getConnection().createStatement();

		try {
			count = stmt.executeUpdate(sql);

			//ＳＱＬ実行が正常終了したら、debug ログ出力
			if(FWLog.isDebug()){
				FWLog.debug(this.getClass(), sql);
			}

		} catch (SQLException e) {
			FWLog.error(sql);
			throw e;

		} finally {
			if (stmt != null) stmt.close();
			stmt = null;
		}
	}

	/**
	 * @return
	 */
	protected Connection getConnection() {
		return connection;
	}

	/**
	 * @param connection
	 */
	protected void setConnection(Connection connection) {
		this.connection = connection;
	}

	/**
	 * @return
	 */
	public int getCount() {
		return count;
	}

	/**
	 * @param i
	 */
	public void setCount(int i) {
		count = i;
	}

}
