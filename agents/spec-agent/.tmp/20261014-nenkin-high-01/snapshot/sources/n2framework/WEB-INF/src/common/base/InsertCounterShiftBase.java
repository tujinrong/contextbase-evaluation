/*
 * 作成日: 2007/05/22
 *
 */
package common.base;

import java.sql.Connection;
import java.sql.SQLException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Map;

/**
 * データウェアハウス　カウンターシフト登録Baseクラス
 * 
 * @author JSC kengo murayama
 * 
 * @date	H22.9.3		青木・浅見		センター集約対応
 */
public class InsertCounterShiftBase extends CommonBase {

	private static final String comma = " , ";
	private StringBuffer sb = new StringBuffer();

	/**
	 * コンストラクタ
	 * 
	 * @param connection
	 */
	public InsertCounterShiftBase(Connection connection) {
		super(connection);
	}

	public void insert(Map map) throws SQLException/*,NamingException*/{
		try {

			sb.append("insert into DB2.Ｕカウンターシフト ");
			sb.append("(アクセス日付,アクセス時刻,機能ＩＤ,画面ＩＤ,コマンドＩＤ,アクションＩＤ,");
			sb.append("ＪＳＰ名,ユーザーＩＤ) ");
			sb.append(" values ");

			sb.append("(");

			//アクセス日付
			Date date = new Date();
			SimpleDateFormat gSDFDate = new SimpleDateFormat("yyyyMMdd");
			sb.append(gSDFDate.format(date) + ",");

			//アクセス時刻
			SimpleDateFormat gSDFTime = new SimpleDateFormat("HHmmssSSS");
			sb.append(gSDFTime.format(date));


			setColumun(map,"機能ＩＤ",true);
			setColumun(map,"画面ＩＤ",true);
			setColumun(map,"コマンドＩＤ",true);
			setColumun(map,"アクションＩＤ",true);
			setColumun(map,"ＪＳＰ名",true);

			//ＰＫ項目のnull対応
			sb.append(",'").append(map.get("ユーザーＩＤ")).append("'");

			sb.append(")");

			execute(sb.toString());

		} catch (SQLException e) {
			throw e;
		}
	}

	/**
	 * 
	 * @param columun
	 * @param map
	 * @param varchar
	 */
	private void setColumun(Map map, String columun, boolean isChar){
		sb.append(comma);
		if(map.get(columun) != null && !"".equals(map.get(columun))){
			if(isChar) sb.append("'");
			sb.append(map.get(columun));
			if(isChar) sb.append("'");
		} else {
			sb.append("null");
		}
		//comma = " , ";
	}
}
