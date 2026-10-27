/*
 * 作成日: 2007/05/22
 *
 */
package common;

import java.sql.Connection;
import java.sql.SQLException;
import java.util.Map;

import javax.naming.InitialContext;

import common.base.InsertCounterShiftBase;
import common.util.CommonUtil;

/**
 * カウンターシフトクラス。
 * 
 * @author JSC kengo murayama
 * 
 * @date	H22.9.3		青木・浅見		センター集約対応
 */
public class CounterShift {

	static void countUp(Map map) {

		Connection con = null;

		try {
			//Connectionの取得
			con = CommonUtil.getConnection(new InitialContext(), CommonConst.JDBC_ORACLE_SP2NM);

			InsertCounterShiftBase base = new InsertCounterShiftBase(con);

			base.insert(map);

			con.commit();
		} catch (Exception e) {
			try {
				if (con != null) con.rollback();
			} catch (SQLException e1) {
				FWLog.error(e1);
			}

			FWLog.error(e);
		} finally {
			try {
				if (con != null) con.close();
				con = null;
			} catch (SQLException e1) {
				FWLog.error(e1);
			}
		}
	}
}
