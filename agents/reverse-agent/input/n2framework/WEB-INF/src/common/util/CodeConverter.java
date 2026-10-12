/*
 * 作成日: 2007/05/29
 *
 */
package common.util;

//import java.sql.Connection;
//import java.sql.SQLException;
//import java.util.Map;

//import javax.naming.InitialContext;

//import common.CommonConst;
//import common.FWLog;
//import common.base.SelectCodeGyosyuBase;

/**
 * コードテーブル項目コンバートクラス。
 * RqsDbSearchのようなもの。
 * 現状使用しないため、コメントアウト。
 * 使用する場合は、コメント解除。
 *
 * @author JSC kengo murayama
 *
 * @date	H22.9.6		青木・浅見		センター集約対応なし
 */
public class CodeConverter {

//	/** このクラスのシングルトンオブジェクト */
//	private static final CodeConverter cc = new CodeConverter();

//	/** 業種コード */
//	private Map mapGyosyu;

	/**
	 * コンストラクタ<BR>
	 * <BR>
	 * コード項目を取得して保持する。
	 */
	private CodeConverter(){
//		Connection con = null;
//
//		try {
//			//Connectionの取得
//			con = CommonUtil.getConnection(new InitialContext(), CommonConst.JDBC_ORACLE_SP2NM);
//
//			//業種コードの取得
//			SelectCodeGyosyuBase base = new SelectCodeGyosyuBase(con);
//			base.select();
//			setMapGyosyu(base.getMap());
//
//		} catch (Exception e) {
//			FWLog.error(e);
//		} finally {
//			try {
//				if (con != null) con.close();
//				con = null;
//			} catch (SQLException e1) {
//				FWLog.error(e1);
//			}
//		}
	}

//	/**
//	 * 引数の業種名を返す。
//	 * 
//	 * @param code 業種コード
//	 * @return 業種名
//	 */
//	public static String getGyosyuCode(String code){
//		return (String)cc.getMapGyosyu().get(code);
//	}
//
//	/**
//	 * @return mapGyosyu を戻します。
//	 */
//	private Map getMapGyosyu() {
//		return mapGyosyu;
//	}
//
//	/**
//	 * @param mapGyosyu 設定する mapGyosyu。
//	 */
//	private void setMapGyosyu(Map mapGyosyu) {
//		this.mapGyosyu = mapGyosyu;
//	}
}
