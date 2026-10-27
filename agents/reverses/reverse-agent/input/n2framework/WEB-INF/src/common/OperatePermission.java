/*
 * 作成日: 2007/05/14
 *
 */
package common;

import java.sql.Connection;
import java.sql.SQLException;
import java.util.List;
import java.util.Map;

import javax.naming.InitialContext;

import common.base.SelectDBKanriDBBase;
import common.util.CommonUtil;

/**
 * 運用時間帯チェッククラス。
 * 
 * @author JSC kengo murayama
 * 
 * @date	H22.9.3		青木・浅見		センター集約対応
 */
public class OperatePermission {

	static boolean check(String actionPackage) {

		Connection con = null;

		try {
			//Connectionの取得
			con = CommonUtil.getConnection(new InitialContext(), CommonConst.JDBC_ORACLE_SP2NM);

			//業務種別の判定
			String dbName;

			//※業務種別が増えた場合、このif文にelse if文を追加する。
			if(actionPackage != null && actionPackage.equals("ing")){
				//員外管理システムの場合
				dbName = "Ｕ員外管理顧客情報";
			}else if(actionPackage != null && actionPackage.equals("credit")){
				//融資情報システム（融資）の場合
				dbName = "Ｕ融資情報";
			}else if(actionPackage != null && actionPackage.equals("crd")){
				//融資情報システム（CRD）の場合
				dbName = "Ｕ融資情報";
			}else if(actionPackage != null && actionPackage.equals("rate")){
				//融資情報システム（格付）の場合
				dbName = "Ｕ融資情報";
			}else if(actionPackage != null && actionPackage.equals("saiken")){
				//融資情報システム（債権）の場合
				dbName = "Ｕ債権情報";
			} else {
				//チェック対象でない場合、チェックＯＫと見なす
				return true;
			}

			SelectDBKanriDBBase base = new SelectDBKanriDBBase(con);

			base.select(dbName);
			List ls = base.getList();

			if(ls != null && !ls.isEmpty()){
				Map map = (Map)ls.get(0);
				String flag = (String)map.get("処理中ＦＬＧ");

				//処理中ＦＬＧが稼動可だった場合、チェックＯＫ
				if(flag != null && flag.equals("0")){
					return true;
				}
			}

		} catch (Exception e) {
			FWLog.error(e);
		} finally {
			try {
				if (con != null) con.close();
				con = null;
			} catch (SQLException e1) {
				FWLog.error(e1);
			}
		}

		return false;
	}
}
