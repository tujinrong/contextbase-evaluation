/*
 * ì¬“ú: 2007/05/14
 *
 */
package common.base;


import java.sql.Connection;
import java.sql.SQLException;

import common.base.CommonBaseSelect;

/**
 * ƒf[ƒ^ƒEƒFƒAƒnƒEƒX@‚c‚aŠÇ—‚c‚aŒŸõBaseƒNƒ‰ƒX
 * 
 * @author JSC kengo murayama
 * 
 * @date	H22.9.3		Â–ØEóŒ©		ƒZƒ“ƒ^[W–ñ‘Î‰
 */
public class SelectDBKanriDBBase extends CommonBaseSelect {

	/**
	 * ƒRƒ“ƒXƒgƒ‰ƒNƒ^
	 * 
	 * @param connection
	 */
	public SelectDBKanriDBBase(Connection connection) {
		super(connection);
	}

	/**
	 * 
	 * SELECT•¶‚ğÀs‚·‚é
	 * 
	 * @param dbName
	 * @return boolean
	 * @throws SQLException
	 */
	public boolean select(String dbName) throws SQLException {

		try {

			//‚t‚c‚aŠÇ—‚c‚a‚ÌŒŸõ
			StringBuffer sb = new StringBuffer();

			sb.append("select ˆ—’†‚e‚k‚f");
			sb.append(" from DB2.‚t‚c‚aŠÇ—‚c‚a");
			sb.append(" where ‚c‚a–¼ = '").append(dbName).append("'");

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
