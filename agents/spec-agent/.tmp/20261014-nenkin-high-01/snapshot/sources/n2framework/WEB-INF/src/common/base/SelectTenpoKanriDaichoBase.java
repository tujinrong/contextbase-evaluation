/*
 * ì¬“ú: 2017/05/15
 */
package common.base;

import java.sql.Connection;
import java.sql.SQLException;

import common.base.CommonBaseSelect;

/**
 * DB2.‚t‚i“X•ÜŠÇ—‘ä’ @ŒŸõBaseƒNƒ‰ƒX
*
 * @author Minoei ŽRŒû
 * 
 * @date
 *   
 */
public class SelectTenpoKanriDaichoBase extends CommonBaseSelect {

	/**
	 * ƒRƒ“ƒXƒgƒ‰ƒNƒ^
	 * 
	 * @param connection
	 */
	public SelectTenpoKanriDaichoBase(Connection connection) {
		super(connection);
	}
	

	/**
	 * 
	 * “X•Ü–¼ˆê——‚ðŽæ“¾B
	 * i•›“X”Ô = 0 , ó‘Ô = 0j
	 *
	 * @return boolean
	 * @throws SQLException
	 */
	public boolean selectTenpoIchiran() throws SQLException {

		try {
			StringBuffer sb = new StringBuffer();

			sb.append("SELECT");
			sb.append(" “X”Ô,");
			sb.append(" TRIM('@' from Š¿Žš“X–¼) AS Š¿Žš“X–¼");
			sb.append(" FROM DB2.‚t‚i“X•ÜŠÇ—‘ä’ ");
			sb.append(" WHERE •›“X”Ô = 0");
			sb.append(" AND ó‘Ô = 0");
			sb.append(" AND “X”Ô > 10");
			sb.append(" ORDER BY “X”Ô");

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
