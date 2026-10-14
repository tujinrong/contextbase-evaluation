/*
 * 作成日: 2014/02/20
 *
 */
package common.util;

import java.sql.Connection;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.List;
import java.util.Map;

import javax.naming.InitialContext;

import common.CommonConst;
import common.FWLog;
import common.base.SelectSaijitsuBase;

/**
 * 日付計算クラス
 *
 * @author Minori米持
 *
 */
public class DateArithmetic {

	/** このクラスのシングルトンオブジェクト */
	private static final DateArithmetic da = new DateArithmetic();

	/**
	 *  休日リスト（※土日は含まない
	 *  例：「2014/05/03」は祝日だが土曜のため、リストにはない
	 */
	private List lsSaijitsu;

	/**
	 * コンストラクタ
	 * 祭日を取得して保持する。
	 */
	private DateArithmetic(){
		Connection con = null;
		List ls = new ArrayList();

		try {
			//Connectionの取得
			con = CommonUtil.getConnection(new InitialContext(), CommonConst.JDBC_ORACLE_SP2NM);

			//祭日の取得
			SelectSaijitsuBase base = new SelectSaijitsuBase(con);
			base.select();
			for(int i=0;i<base.getList().size();i++){
				Map map = (Map)base.getList().get(i);
				ls.add((String)map.get("日付"));
			}
			setLsSaijitsu(ls);
			
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
	}

	private List getLsSaijitsu() {
		return lsSaijitsu;
	}
	public void setLsSaijitsu(List lsSaijitsu) {
		this.lsSaijitsu = lsSaijitsu;
	}

	/**
	 * 営業日の計算をして、日付を返却する。
	 * ※正しく判定する為には、「DB2.Ｕ祭日」の日付の登録が必須
	 * 
	 * @param code 基準日付(YYYYMMDD)
	 * @param niti	計算値
	 * 				 1 → 基準日付の翌営業日
	 * 			 	-3 → 基準日付の３営業日前
	 * 
	 * @return 計算結果日付
	 */
	public static String calcEigyoDate(String date , int niti){

		//計算値が０の場合は""を返却
		if(niti == 0) {return "";}

		//日付に妥当性がない場合は""を返却
		if(!CommonConverter.checkDate(date)) {return "";}

		boolean bSaijitu = false;
		String yyyy = "";
		String mm = "";
		String dd = "";
		String yyyyMMdd = "";
		int count = niti;
		
		Calendar cal = Calendar.getInstance();
		int sysYear = CommonConverter.convertInt(date.substring(0,4));
		int sysMonth = CommonConverter.convertInt(date.substring(4,6));
		int sysDate = CommonConverter.convertInt(date.substring(6,8));
		cal.set(sysYear,sysMonth-1,sysDate);

		//正の数の場合
		if(count > 0){
			while(count > 0){
				cal.add(Calendar.DAY_OF_MONTH, 1);

				yyyy = String.valueOf(cal.get(Calendar.YEAR));
				mm = CommonConverter.getAdd0String(String.valueOf(cal.get(Calendar.MONTH)+1),2);
				dd = CommonConverter.getAdd0String(String.valueOf(cal.get(Calendar.DATE)),2);
				yyyyMMdd = yyyy + mm + dd;
				
				//土日の判定
				if(Calendar.SUNDAY != cal.get(Calendar.DAY_OF_WEEK) && Calendar.SATURDAY != cal.get(Calendar.DAY_OF_WEEK)){

					//休日の判定（休日はtrue）
					bSaijitu = false;
					for(int i=0;i < da.getLsSaijitsu().size();i++){
						if(yyyyMMdd.equals((String)da.getLsSaijitsu().get(i))){bSaijitu = true;}
					}
					if(!bSaijitu){
						count--;
					}
				}			
			}

		//負の数の場合
		}else{
			while(count < 0){
				cal.add(Calendar.DAY_OF_MONTH, -1);

				yyyy = String.valueOf(cal.get(Calendar.YEAR));
				mm = CommonConverter.getAdd0String(String.valueOf(cal.get(Calendar.MONTH)+1),2);
				dd = CommonConverter.getAdd0String(String.valueOf(cal.get(Calendar.DATE)),2);
				yyyyMMdd = yyyy + mm + dd;

				//土日の判定
				if(Calendar.SUNDAY != cal.get(Calendar.DAY_OF_WEEK) && Calendar.SATURDAY != cal.get(Calendar.DAY_OF_WEEK)){

					//休日の判定（休日はtrue）
					bSaijitu = false;
					for(int i=0;i < da.getLsSaijitsu().size();i++){
						if(yyyyMMdd.equals((String)da.getLsSaijitsu().get(i))){bSaijitu = true;}
					}
					if(!bSaijitu){
						count++;
					}
				}			
			}
		}
		
		return yyyyMMdd;
	}

}
