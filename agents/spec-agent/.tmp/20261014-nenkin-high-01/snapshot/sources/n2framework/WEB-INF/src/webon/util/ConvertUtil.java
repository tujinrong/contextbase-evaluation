package webon.util;

import java.io.BufferedInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.SQLException;
import java.text.DateFormat;
import java.text.NumberFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import webon.base.SelectDB2KamokuBase;
import webon.base.SelectOperationBranchMstBase;


import common.FWLog;
import common.util.CommonConverter;
import common.util.CommonUtil;

/**
 * webon汎用照会　各種コード変換ユーティリティ
 * 
 * @author Minori 京極
 * 
 * @date	2020.02.13		京極		新規作成
 * 
 */
public class ConvertUtil {

//=======項目判定メソッド
	/**
	 * 店番が、稼動可能な店舗か判定する。
	 * @param String brno
	 * 
	 * @return boolean true:試行店舗でない、false:試行店舗である
	 */
	public static boolean checkOpBranchNo(String brno,Connection con) throws SQLException{
		boolean flg=false;
		if (brno==null||brno.equals("")) {
			return true;
		}
		try{
			FWLog.debug("稼動店舗開始★★★");
			SelectOperationBranchMstBase base = new SelectOperationBranchMstBase(con);
			base.selectNotActiveByBrno(brno);
			List<Map<String, String>>list = CastUtil.genelicToStringList2(base.getList());
			if(0<list.size()){
				flg=true;
			}
			
//			base.selectOperationBranchNo();
//			ArrayList<HashMap<String, String>> list = CastUtil.genelicToStringList(base.getList());//稼動店舗リスト
//			Iterator<HashMap<String, String>> it = list.iterator();
//			while(it.hasNext()){
//				HashMap<String , String>map = it.next();
//				String opBrno = map.get("店番");
//				if(CommonConverter.getAdd0String(brno,3).equals(CommonConverter.getAdd0String(opBrno,3))){
//					flg=true;
//				}
//			}
		}catch(SQLException e){
			FWLog.debug("稼動店舗情報問い合わせに失敗しました");
			throw e;
		}
		return flg;
	}
	
//=======項目コピーメソッド=========
	/**
	 * StringのdeepCopyを行う
	 * (同値別インスタンスのStringを返す)
	 * @param String 文字列
	 * @return String 
	 */
	public static String deepCopy(String str) {
		String result = null;
		if (str==null) {return result;}
		result=String.copyValueOf(str.toCharArray());
		return result;
	}
	/**
	 * ArrayList<HashMap<String,String>のディープコピー
	 * @param ArrayList<HashMap<String,String>> コピー元
	 * @return ArrayList<HashMap<String,String>> コピーしたインスタンス
	 */
	public static ArrayList<HashMap<String,String>> deepCopy(ArrayList<HashMap<String,String>> list) {
		ArrayList<HashMap<String,String>> list2 = new ArrayList<HashMap<String,String>>(); //結果
		for (Iterator<HashMap<String, String>> listIt=list.iterator(); listIt.hasNext();) {
			HashMap<String,String> map = listIt.next();
			HashMap<String, String> map2 = new HashMap<String, String>();
			map2=deepCopy(map);
			list2.add(map2); //結果に追加
		}
		return list2;
	}
	/**
	 * HashMap<String,String>のディープコピー
	 * @param HashMap<String,String> コピー元
	 * @return HashMap<String,String> コピーしたインスタンス
	 */
	public static HashMap<String,String> deepCopy(HashMap<String,String> map) {
		String key; //Key保持用
		HashMap<String, String> map2 = new HashMap<String, String>();
		Set<String> ks = map.keySet();
		for (Iterator<String> ksIt = ks.iterator(); ksIt.hasNext();) {
			key=ksIt.next();
			map2.put(key,map.get(key));
		}
		return map2;
	}

//=======項目変換・修正メソッド=======
	/**
	 * 科目名称をキーに、科目コードを取得する
	 * （DB2.ＵＪ科目を参照）
	 * null又は空文字の場合、空文字を返す
	 * 
	 * @throws Exception 
	 * @param name 科目名称
	 * @param con	コネクション
	 * @return String 科目コード
	 */
	public static String convertKamokuNameToCode(String name, Connection con) throws Exception{
		String code="";
		if (name==null||name.equals("")) {
			return "";
		}
		try{
			//DB2.ＵＪ科目から科目名称をキーに、科目コードを取得
			SelectDB2KamokuBase base = new SelectDB2KamokuBase(con);
			base.selectCodeByKamokuName(name);
			List<Map<String, String>>list = CastUtil.genelicToStringList2(base.getList());
			if(0<list.size()){
				//取得結果の科目コード
				code = list.get(0).get(SelectDB2KamokuBase.DBKEY_CODE);
			}
		}catch (Exception e) {
			// TODO: handle exception
			FWLog.debug("DB2.ＵＪ科目問い合わせに失敗しました");
			throw e;
		}
		//検索結果を返す、該当なしの場合は空白を返す
		return code;
	}
	/**
	 * 科目コードをキーに、科目名称を取得する
	 * （DB2.ＵＪ科目を参照）
	 * null又は空文字の場合、空文字を返す
	 * 
	 * @throws Exception 
	 * @param code 科目コード
	 * @param con	コネクション
	 * @return String 科目名称
	 */
	public static String convertKamokuCodeToName(String code, Connection con) throws Exception{
		String name="";
		if (code==null||code.equals("")) {
			return "";
		}
		try{
			//DB2.ＵＪ科目から科目コードをキーに、科目名称を取得
			SelectDB2KamokuBase base = new SelectDB2KamokuBase(con);
			base.selectKamokuNameByCode(code);
			List<Map<String, String>>list = CastUtil.genelicToStringList2(base.getList());
			if(0<list.size()){
				//取得結果の科目名称
				name = list.get(0).get(SelectDB2KamokuBase.DBKEY_KOUMOKU1);
			}
		}catch (Exception e) {
			// TODO: handle exception
			FWLog.debug("DB2.ＵＪ科目問い合わせに失敗しました");
			throw e;
		}
		//検索結果を返す、該当なしの場合は空白を返す
		return name;
	}
	
	/**
	 * 文字列のリストを走査し、重複する文字列を削除する
	 * 
	 * @param ArrayList<String>      重複チェック前の文字列リスト
	 * 
	 * @return ArrayList<String>             重複チェック後の文字列リスト
	 */
	public static ArrayList<String> dchkStrList(ArrayList<String> strList){
		ArrayList<String> rList = new ArrayList<String>();	//一意な統一顧客番号を格納するリスト
		LinkedHashSet<String> set = new LinkedHashSet<String>();		//重複排除用のセット
		
		for(String s : strList){
			set.add(s);
		}
		for(Iterator<String> i = set.iterator();i.hasNext();){
			rList.add(i.next());
		}
		return rList;
	}
	/**
	 * 【和暦処理】西暦をWebon日付(数値７桁)に変換する
	 * （yyyymmdd型をgyymmdd型に変換する)
	 * 
	 */
	public static String convertWebonDateFromSeireki(String seireki){
		if (seireki==null||seireki.equals("")) {
			return "";
		}
		String wareki="";	//和暦
		StringBuffer sWareki=new StringBuffer();
		String gengo="";	//元号
		String wYear="";		//和暦年
		String wMonth="";	//和暦月
		String wDay="";		//和暦日
		
		wareki=CommonConverter.convertWareki2(seireki);
		gengo=wareki.substring(0,1);
		wYear=wareki.substring(2, 4);
		wMonth=wareki.substring(5,7);
		wDay=wareki.substring(8,10);
		if(gengo.equals("明")){
			gengo="2";
		}else if(gengo.equals("大")){
			gengo="3";
		}else if(gengo.equals("昭")){
			gengo="4";
		}else if(gengo.equals("平")){
			gengo="5";
		}else if(gengo.equals("令")){
			gengo="6";
		}
		wYear=CommonConverter.getAdd0String(wYear, 2);
		wMonth=CommonConverter.getAdd0String(wMonth, 2);
		wDay=CommonConverter.getAdd0String(wDay, 2);
		
		sWareki.append(gengo);
		sWareki.append(wYear);
		sWareki.append(wMonth);
		sWareki.append(wDay);
		
		return sWareki.toString();
	}
	/**
	 * 文字列の１文字目を判定し、0だった場合半角空白に変換する
	 * @param val
	 * @return
	 */
	public static String convertFirstCharSpacheToZero(String val){
		if (val==null||val.equals("")) {
			return "";
		}
		char fc = val.charAt(0);
		if(fc=='0'){
			StringBuffer replaceVal = new StringBuffer(val);
			replaceVal.replace(0, 1, " ");
			val=replaceVal.toString();
		}
		return val;
	}
	
	/**
	 * 【和暦処理】日付のデータ「元号コード（１桁）＋和暦年月日（６桁）」を西暦に変換する
	 * （gyymmdd型をyyyymmdd型に変換する)
	 * @param String gDate
	 * @return String seireki
	 * null又は空文字の場合、空文字を返す
	 */
	public static String convertSeirekiFromGdate(String gDate){
		if (gDate==null||gDate.equals("")||gDate.length()!=7) {
			return "";
		}
		
		String seireki="";	//西暦
		StringBuffer wareki=new StringBuffer();
		
		String gengo="";	//元号
		String wYear="";		//和暦年
		String wMonth="";	//和暦月
		String wDay="";		//和暦日
		
		gengo=gDate.substring(0,1);
		wYear=gDate.substring(1, 3);
		wMonth=gDate.substring(3,5);
		wDay=gDate.substring(5,7);
		
		if(gengo.equals("0")||gengo.equals("6")){
			gengo="R";
		}else if(gengo.equals("2")){
			gengo="M";
		}else if(gengo.equals("3")){
			gengo="T";
		}else if(gengo.equals("4")){
			gengo="S";
		}else if(gengo.equals("5")){
			gengo="H";
		}
		
		wYear=CommonConverter.getAdd0String(wYear, 2);
		wMonth=CommonConverter.getAdd0String(wMonth, 2);
		wDay=CommonConverter.getAdd0String(wDay, 2);
		
		wareki.append(gengo);
		wareki.append(wYear);
		wareki.append(wMonth);
		wareki.append(wDay);
		
		seireki=CommonConverter.convertSeireki2(wareki.toString());
		
		return seireki;
	}
	
	/**
	 * 指定された西暦年月日（yyyyMMdd）に、指定された月数を加算する。
	 * 
	 * @param year	西暦年月日（yyyyMMdd）
	 * @param add	加算月数（負数の場合は減算）
	 * @return
	 */
	public static String addMonth(String year, int add){
		try{
			//加算後の西暦年月日
			String addMonth = "";
			
			//ニューメリックチェック
			if(year!=null && !year.isEmpty()){
				
				//指定の西暦年月日に、指定された月数を加算した西暦を取得する。
				DateFormat df = new SimpleDateFormat("yyyyMMdd");
				Date dt = df.parse(year);
				
				Calendar cal = Calendar.getInstance();
				cal.setTime(dt);
				cal.add(Calendar.MONTH, add);
				addMonth = df.format(cal.getTime());
				//加算した西暦年月日を返す。
				return addMonth;
				
			} else {
				return "";
			}
		} catch (Exception e) {
			//日付換算ができない場合は空文字で返す。
			return "";
		}
	}
	
	/**
	 * 【和暦処理】Webonから取得した日付のデータを西暦に変換する
	 * （Gyy-mm-dd型をyyyymmdd型に変換する)
	 * @param String webonDate
	 * @return String seireki
	 * null又は空文字の場合、空文字を返す
	 */
	public static String convertSeirekiFromWebonDate(String webonDate){
		if (webonDate==null||webonDate.equals("")||webonDate.length()!=9) {
			return "";
		}
		
		String seireki="";	//西暦
		StringBuffer wareki=new StringBuffer();
		String gengo="";	//元号
		String wYear="";		//和暦年
		String wMonth="";	//和暦月
		String wDay="";		//和暦日
		
		gengo=webonDate.substring(0,1);
		wYear=webonDate.substring(1, 3);
		wMonth=webonDate.substring(4,6);
		wDay=webonDate.substring(7,9);
		
		if(gengo.equals("明")){
			gengo="M";
		}else if(gengo.equals("大")){
			gengo="T";
		}else if(gengo.equals("昭")){
			gengo="S";
		}else if(gengo.equals("平")){
			gengo="H";
		}else if(gengo.equals("令")){
			gengo="R";
		}
		
		wYear=CommonConverter.getAdd0String(wYear, 2);
		wMonth=CommonConverter.getAdd0String(wMonth, 2);
		wDay=CommonConverter.getAdd0String(wDay, 2);
		
		wareki.append(gengo);
		wareki.append(wYear);
		wareki.append(wMonth);
		wareki.append(wDay);
		
		seireki=CommonConverter.convertSeireki2(wareki.toString());
		return seireki;
	}
	/**
	 * 【和暦処理】Webonから取得した日付のデータを元号コード（１桁）＋和暦年月日（６桁）に変換する
	 * （Gyy-mm-dd型をgyymmdd型に変換する)
	 * @param String webonDate
	 * @return String seireki
	 * null又は空文字の場合、空文字を返す
	 */
	public static String convertGwarekiFromWebonDate(String webonDate){
		if (webonDate==null||webonDate.equals("")) {
			return "";
		}
		
		StringBuffer wareki=new StringBuffer();
		String gengo="";	//元号
		String wYear="";	//和暦年
		String wMonth="";	//和暦月
		String wDay="";		//和暦日
		
		gengo=webonDate.substring(0,1);
		wYear=webonDate.substring(1, 3);
		wMonth=webonDate.substring(4,6);
		wDay=webonDate.substring(7,9);
		
		if(gengo.equals("明")){
			gengo="2";
		}else if(gengo.equals("大")){
			gengo="3";
		}else if(gengo.equals("昭")){
			gengo="4";
		}else if(gengo.equals("平")){
			gengo="5";
		}else if(gengo.equals("令")){
			gengo="6";
		}
		
		wYear=CommonConverter.getAdd0String(wYear, 2);
		wMonth=CommonConverter.getAdd0String(wMonth, 2);
		wDay=CommonConverter.getAdd0String(wDay, 2);
		
		wareki.append(gengo);
		wareki.append(wYear);
		wareki.append(wMonth);
		wareki.append(wDay);
		
		return wareki.toString();
	}
	/**
	 * 【和暦処理】日付Convert GYY-MM-DD(和) → YYYYMMDD(西暦) or YY-MM-DD(和) → YYYYMMDD(西暦)
	 * 変換元に元号コードが無い（YY-MM-DD）場合は、
	 * 48年以降は昭和、25年以降は平成、それ以前は令和として西暦に変換　⇒　【稟議支援と同じ条件】
	 * @param String 対象文字
	 * @param String 項目名
	 */
	public static String replaceJPtoAD(String key) {
		return replaceCommonJPtoAD(key,48);
	}
	/**
	 * 【和暦処理】Webonから取得した日付のデータを西暦に変換する
	 * （ GYY-MM-DD(和) → YYYYMMDD(西暦) or YY-MM-DD(和) → YYYYMMDD(西暦))
	 * 変換元に元号コードが無い（YY-MM-DD）場合は、
	 * 48年以降は昭和、25年以降は平成、それ以前は令和として西暦に変換　⇒　【稟議支援と同じ条件】
	 * 
	 * @param String webonDate
	 * @param int sep （未使用項目）
	 * @return String seireki
	 * null又は空文字の場合、空文字を返す
	 */
	public static String replaceCommonJPtoAD(String webonDate, int sep){
		String val = webonDate;
		if (val==null||val.equals("")) {
			return "";
		}
		
		//フォーマットチェックし、元号がついていれば西暦に変換する
		if ((val.matches("[A-Z][0-9 ][0-9]-[0-9 ][0-9]-[0-9 ][0-9]"))) {
			
			//要素を取得
			String[] vals=val.split("-");
			String gengo=(vals[0]).substring(0,1);
			String year=(vals[0]).substring(1,3);
			String month=vals[1];
			String day=vals[2];
			
			//FW共通部品で西暦変換
			StringBuilder sb = new StringBuilder();
			sb.append(gengo);
			sb.append(CommonConverter.getAdd0String(year,2));
			sb.append(CommonConverter.getAdd0String(month,2));
			sb.append(CommonConverter.getAdd0String(day,2));
			String adyear = CommonConverter.convertSeireki2(sb.toString());
			
			//結果を格納し、リターン
			return adyear;
			
		}
		
		//フォーマットチェックし、元号がついていなければ、48年以降は昭和、25年以降は平成、それ以前は令和として西暦に変換する
		if ((val.matches("[0-9 ][0-9]-[0-9 ][0-9]-[0-9 ][0-9]")
				||val.matches("[0-9]-[0-9 ][0-9]-[0-9 ][0-9]"))) {
			
			if(val==null||val.equals("")){return "";}
			
			//要素を取得
			String[] vals=val.split("-");
			String year=vals[0];
			String month=vals[1];
			String day=vals[2];
			
			//48年以降は昭和、25年以降は平成、それ以前は令和
			int intyear=Integer.parseInt(year);
			String gengo;
			
			if (intyear<25) {
				gengo="R";
			} else if (intyear<48) {
				gengo="H";
			} else {
				gengo="S";
			}
	
			//FW共通部品で西暦変換
			StringBuilder sb = new StringBuilder();
			sb.append(gengo);
			sb.append(CommonConverter.getAdd0String(year,2));
			sb.append(CommonConverter.getAdd0String(month,2));
			sb.append(CommonConverter.getAdd0String(day,2));
			String adyear = CommonConverter.convertSeireki2(sb.toString());
	
			//結果を格納
			return adyear;
			
		}
		
		//フォーマットチェックに該当しなければ、空文字を返却する
		return "";
		
	}
	/**
	 * 【和暦処理】Webonから取得した日付のデータを西暦に変換する [y]y-mm-dd → yyyyMMdd （取得元の元号は令和とする）
	 * （[y]y-mm-dd型をyyyymmdd型に変換する)
	 * Webonから取得した日付は、令和として判断する
	 * @param String webonDate
	 * @return String seireki
	 * null又は空文字の場合、空文字を返す
	 */
	public static String replaceReiwaJPtoAD(String webonDate){
		String val = webonDate;
		if (val==null||val.equals("")) {
			return "";
		}
		//とりあえずフォーマットチェックして、だめなら変換無し
		if (!(val.matches("[0-9 ][0-9]-[0-9 ][0-9]-[0-9 ][0-9]")
				||val.matches("[0-9]-[0-9 ][0-9]-[0-9 ][0-9]"))) {return webonDate;}
		if(val==null||val.equals("")){return "";}
		//要素を取得
		String[] vals=val.split("-");
		String year=vals[0];
		String month=vals[1];
		String day=vals[2];
		
		//取得元の元号は令和とする
		String gengo="R";
		
		//FW共通部品で西暦変換
		StringBuilder sb = new StringBuilder();
		sb.append(gengo);
		sb.append(CommonConverter.getAdd0String(year,2));
		sb.append(CommonConverter.getAdd0String(month,2));
		sb.append(CommonConverter.getAdd0String(day,2));
		String adyear = CommonConverter.convertSeireki2(sb.toString());

		//結果を格納
		return adyear;
	}
	/**
	 * Webonから取得した時刻のデータを4桁に変換する
	 * （hh:mm型をhhmm型に変換する)
	 * 
	 * @param String webonTime
	 * @return String Time
	 * null又は空文字の場合、空文字を返す
	 */
	public static String convertTimeFromWebonTime(String webonTime){
		if (webonTime==null||webonTime.equals("")) {
			return "";
		}
		webonTime = CommonConverter.getAdd0String(webonTime, 5);
		StringBuilder time =new StringBuilder(webonTime);
		String hh ="";
		String mm ="";
		StringBuffer sb=new StringBuffer();
		time.deleteCharAt(2);
		hh=CommonConverter.getAdd0String(delSpace(time.substring(0,2).toString()),2);
		mm=CommonConverter.getAdd0String(delSpace(time.substring(2,4).toString()),2);
		sb.append(hh).append(mm);
		
		return sb.toString();
	}
	/**
	 * 4桁の数値を時刻に変換する
	 * (hhmm型をhh:mm型に変換する)
	 * 
	 * @param String val
	 * @return String Time
	 * null又は空文字の場合、空文字を返す
	 */
	public static String convertTime(String val){
		if (val==null||val.equals("")) {
			return "";
		}
		StringBuilder time =new StringBuilder(val);
		time.insert(2, ":");
		return time.toString();
	}
	/**
	 * Webonで取得した事故受付番号「XXX-XX-XXXXX [仮受付]」を10桁の数値に変換する
	 * 
	 */
	public static String convertNotifiNoByWbNo(String val){
		if (val==null||val.equals("")) {
			return "";
		}
		String nn="";
		//先頭から１２文字を切り出す
		nn=val.substring(0,12);
		//ハイフンを取り除く
		nn=delHyphen(nn);
		return nn;
	}
	/**
	 * 10桁の数値を諸届け受付番号に変換する
	 * (xxx-xx-xxxxx型に変換する)
	 * 
	 * 
	 */
	public static String convertNotificationNo(String val){
		if (val==null||val.equals("")) {
			return "";
		}
		StringBuilder nno =new StringBuilder(val);
		nno.insert(3, "-");
		nno.insert(6, "-");
		return nno.toString();
	}
	/**
	 * Webonから取得した電話番号のデータから電話区分とハイフン及び先頭の0を除去する
	 */
	public static String replaceTelNo(String telNo){
		if (telNo==null||telNo.equals("")) {
			return "";
		}
		String rTelNo = telNo.replaceFirst("呼", "");
		rTelNo=rTelNo.replaceFirst("^0+", "");
		rTelNo = rTelNo.replaceAll("-","");
		return rTelNo;
	}
	/**
	 * 文字列の先頭に0を追加し、後方５桁目に-を追加する。
	 */
/*	public static String restoreTelNo(String telNo){
		String rTelNo="";
		StringBuilder sb =new StringBuilder(telNo);
		sb.insert(0, "0");
		if(sb.length()>4){
			int pChar =sb.length()-4;
			sb.insert(pChar,"-");
			rTelNo = sb.toString();
		}
		return rTelNo;
	}
*/	/**
	 * 後方５桁目に-を追加する。
	 */
	public static String restoreTelNo(String telNo){
		String rTelNo="";
		StringBuilder sb =new StringBuilder(telNo);
		//sb.insert(0, "0");
		if(sb.length()>4){
			int pChar =sb.length()-4;
			sb.insert(pChar,"-");
			rTelNo = sb.toString();
		}
		return rTelNo;
	}
	/**
	 * 文字列の先頭に0を追加する
	 * 
	 */
	public static String add0StrTop(String val){
		//NULLもしくは空、0の場合、空白を返す
		if (val==null||val.equals("")||val.equals("0")) {
			return "";
		}
		StringBuffer sb = new StringBuffer();
		sb.append("0").append(val);
		return sb.toString();
	}
	
	/**
	 * 文字列が0だった場合、空白に置換する。
	 *  null又は空文字の場合、空文字を返す
	 */
	public static String delcomma(String val){
		if (val==null||val.equals("")) {
			return "";
		}
		if(val.equals("0")){
			return "";
		}else{
			return val;
		}
	}
	/**
	 * 文字列を１文字おきの全角カンマ区切りに編集する
	 * @param String 
	 * @return String
	 * null又は空文字の場合、空文字を返す
	 */
	public static String insertComma(String val){
		if (val==null||val.equals("")) {
			return "";
		}
		StringBuffer sb = new StringBuffer();
		String spplit="";
		for(int i=0;i<val.length();i++){
			sb.append(spplit);
			sb.append(String.valueOf(val.charAt(i)));
			spplit="，";
		}
		return sb.toString();
	}
	/**
	 * 数値文字列から、カンマを取り除く
	 * @param String カンマつき文字列(半角のみ)
	 * @return String カンマ無し文字列(数値のみ)
	 */
	public static String delComma(String money) {
		String result = money.replace(",","");
		return result;
	}
	/**
	 * 数値文字列から、アスタリスクを取り除く
	 * @param String アスタリスクつき文字列(半角のみ)
	 * @return String アスタリスク無し文字列(数値のみ)
	 */
	public static String delAsterisk(String money) {
		String result = money.replace("*","");
		return result;
	}
	//Number型右端切捨て
	private static int dbMoldIntLeft(String str,int dig) {
		int result;
		//先頭１文字目-の処理
		String fugou  ="";
		if (str.substring(0,1).equals("-")){
			fugou = str.substring(0,1);
			str = str.substring(1,str.length());
		}
		str=str.replaceAll("[^0-9]", "");
		//桁数左揃え(右端切捨て)
		if (str.length()>dig) {
			str=str.substring(0, dig);
		}
		str=fugou+str;
		
		result = Integer.parseInt(str);
		return result;
	}
	//Number型
	public static int dbMoldInt(boolean flag,int dig) throws Exception{
		if (flag) {
			return dbMoldInt("1", dig);
		} else {
			return dbMoldInt("0", dig);
		}
	}
	public static int dbMoldInt(int num,int dig) throws Exception{
		String str = Integer.toString(num);
		return dbMoldInt(str, dig);
	}
	public static int dbMoldInt(String str,int dig) throws Exception{
		if (str==null ||str.isEmpty()) {return 0;}
		int result;
		//先頭１文字目-の処理
		String fugou  ="";
		if (str.substring(0,1).equals("-")){
			fugou = str.substring(0,1);
			str = str.substring(1,str.length());
		}
		str=str.replaceAll("[^0-9]", "");
		//桁数右揃え(左端切捨て)
		if (str.length()>dig) {
			//str=str.substring(str.length()-dig, str.length());
			StringBuilder sb = new StringBuilder();
			sb.append("ConvertUtil.dbMoldInt：");
			sb.append(" 変換エラー：文字列の長さが指定より大きいです。");
			sb.append(" 指定桁数：").append(dig);
			sb.append(" 文字列桁数：").append(str.length());
			sb.append(" 指定文字列：").append(str);
			String msg = sb.toString();
			FWLog.error(msg);
			throw new Exception(msg);
		}
		str=fugou+str;
		
		result = Integer.parseInt(str);
		return result;
	}
	public static long dbMoldLong(String str,int dig) throws Exception{
		if (str==null ||str.isEmpty()) {return 0;}
		long result;
		//先頭１文字目-の処理
		String fugou  ="";
		if (str.substring(0,1).equals("-")){
			fugou = str.substring(0,1);
			str = str.substring(1,str.length());
		}
		str=str.replaceAll("[^0-9]", "");
		//桁数右揃え(左端切捨て)
		if (str.length()>dig) {
			//str=str.substring(str.length()-dig, str.length());
			StringBuilder sb = new StringBuilder();
			sb.append("ConvertUtil.dbMoldInt：");
			sb.append(" 変換エラー：文字列の長さが指定より大きいです。");
			sb.append(" 指定桁数：").append(dig);
			sb.append(" 文字列桁数：").append(str.length());
			sb.append(" 指定文字列：").append(str);
			String msg = sb.toString();
			FWLog.error(msg);
			throw new Exception(msg);
		}
		str=fugou+str;
		
		result = Long.parseLong(str);
		return result;
	}
	//VARCHARA型
	public static String dbMoldStr(boolean flag,int dig) throws Exception{
		if (flag) {
			return dbMoldStr("1",dig);
		} else {
			return dbMoldStr("0",dig);
		}
	}
	public static String dbMoldStr(String str,int dig) throws Exception{
		if (str==null ) {str="";}
		//桁数右揃え(左端切捨て)
		if (str.length()>dig) {
			//str=str.substring(str.length()-dig, str.length());
			StringBuilder sb = new StringBuilder();
			sb.append("ConvertUtil.dbMoldStr：");
			sb.append(" 変換エラー：文字列の長さが指定より大きいです。");
			sb.append(" 指定桁数：").append(dig);
			sb.append(" 文字列桁数：").append(str.length());
			sb.append(" 指定文字列：").append(str);
			String msg = sb.toString();
			FWLog.error(msg);
			throw new Exception(msg);
		}
		StringBuilder sb=new StringBuilder();
		sb.append("'").append(escapeSingleQuote(str)).append("'");
		return sb.toString();
	}
	//VARCHARA型右詰0パディング
	public static String dbMoldStrPadZeroRight(String str,int dig) throws Exception{
		if (str==null ) {str="";}
		//桁数右揃え
		if (str.length()>dig) {
			//str=str.substring(0, dig);
			StringBuilder sb = new StringBuilder();
			sb.append("ConvertUtil.dbMoldStrPadZeroRight：");
			sb.append(" 変換エラー：文字列の長さが指定より大きいです。");
			sb.append(" 指定桁数：").append(dig);
			sb.append(" 文字列桁数：").append(str.length());
			sb.append(" 指定文字列：").append(str);
			String msg = sb.toString();
			FWLog.error(msg);
			throw new Exception(msg);
		} else if(str.length()<dig){
			StringBuilder sb = new StringBuilder(str);
			while (sb.length()<dig) {
				sb.insert(0, "0");
			}
			str=sb.toString();
		}
		StringBuilder sb=new StringBuilder();
		sb.append("'").append(str).append("'");
		return sb.toString();
	}
	//VARCHARA型左詰0パディング
	public static String dbMoldStrPadZeroLeft(String str,int dig) throws Exception{
		if (str==null ) {str="";}
		//桁数右揃え(左端切捨て)
		if (str.length()>dig) {
			//str=str.substring(0, dig);
			StringBuilder sb = new StringBuilder();
			sb.append("ConvertUtil.dbMoldStrPadZeroLeft：");
			sb.append(" 変換エラー：文字列の長さが指定より大きいです。");
			sb.append(" 指定桁数：").append(dig);
			sb.append(" 文字列桁数：").append(str.length());
			sb.append(" 指定文字列：").append(str);
			String msg = sb.toString();
			FWLog.error(msg);
			throw new Exception(msg);
		} else if(str.length()<dig){
			StringBuilder sb = new StringBuilder(str);
			while (sb.length()<dig) {
				sb.append("0");
			}
			str=sb.toString();
		}
		StringBuilder sb=new StringBuilder();
		sb.append("'").append(str).append("'");
		return sb.toString();
	}
	//VARCHARA型右詰スペースパディング
	public static String dbMoldStrPadSpRight(String str,int dig) throws Exception{
		if (str==null ) {str="";}
		//桁数右揃え(左端切捨て)
		if (str.length()>dig) {
			//str=str.substring(0, dig);
			StringBuilder sb = new StringBuilder();
			sb.append("ConvertUtil.dbMoldStrPadSpRight：");
			sb.append(" 変換エラー：文字列の長さが指定より大きいです。");
			sb.append(" 指定桁数：").append(dig);
			sb.append(" 文字列桁数：").append(str.length());
			sb.append(" 指定文字列：").append(str);
			String msg = sb.toString();
			FWLog.error(msg);
			throw new Exception(msg);
		} else if(str.length()<dig){
			StringBuilder sb = new StringBuilder(str);
			while (sb.length()<dig) {
				sb.insert(0, " ");
			}
			str=sb.toString();
		}
		StringBuilder sb=new StringBuilder();
		sb.append("'").append(str).append("'");
		return sb.toString();
	}
	//VARCHARA型左詰スペースパディング
	public static String dbMoldStrPadSpLeft(String str,int dig) throws Exception{
		if (str==null ) {str="";}
		//桁数右揃え(左端切捨て)
		if (str.length()>dig) {
			//str=str.substring(0, dig);
			StringBuilder sb = new StringBuilder();
			sb.append("ConvertUtil.dbMoldStrPadSpLeft：");
			sb.append(" 変換エラー：文字列の長さが指定より大きいです。");
			sb.append(" 指定桁数：").append(dig);
			sb.append(" 文字列桁数：").append(str.length());
			sb.append(" 指定文字列：").append(str);
			String msg = sb.toString();
			FWLog.error(msg);
			throw new Exception(msg);
		} else if(str.length()<dig){
			StringBuilder sb = new StringBuilder(str);
			while (sb.length()<dig) {
				sb.append(" ");
			}
			str=sb.toString();
		}
		StringBuilder sb=new StringBuilder();
		sb.append("'").append(str).append("'");
		return sb.toString();
	}
	/**
	 * 文字列からシングルクォートを検出し、エスケープする
	 * nullの場合、空白を返す
	 * 
	 * @param val
	 * @return
	 */
	public static String escapeSingleQuote(String val){
		if (val==null ) {val="";}
		
		StringBuilder sb = new StringBuilder(val);
		
		//１文字ずつ抜き出して判定する。
		for(int i=0;i<sb.length();i++){
			char checkChar = sb.charAt(i);	//比較文字
			//文字がシングルクォートかを判定する
			if(checkChar=='\''){
				//シングルクォートなら、シングルクォートを挿入しエスケープする。
				sb.insert(i, '\'');
				//挿入後１カウントアップする
				i++;
			}
		}
		return sb.toString();
	}
	
	/**
	 * 全角トリム(半角も)
	 * 
	 * @param s
	 * @return
	 */
	public static String trimUni(String s){
		int len = s.length();
		int st = 0;
		char[] val = s.toCharArray();
		while (st < len && (val[st] <= ' ' || val[st] == '　')) {
			st++;
		}
		while (st < len && (val[len - 1] <= ' ' || val[len - 1] == '　')) {
			len--;
		}
		if(st > 0 || len < s.length()) {
			return s.substring(st, len);
		}
		return s;
	}	public static int dbGetDate() {
		String formatDate = "yyyyMMdd";
		String date=CommonUtil.getCurrentDate(formatDate);
		return dbMoldIntLeft(date,8);
	}
	public static int dbGetTime() {
		String formatTime = "HHmmssSS";
		String time=CommonUtil.getCurrentDate(formatTime);
		return dbMoldIntLeft(time,8);
	}
	public static int dbGetTimeminute() {
		String formatTime = "HHmm";
		String time=CommonUtil.getCurrentDate(formatTime);
		return dbMoldIntLeft(time,4);
	}
	//注意コードの変換(注意コード名をコードに変換)
	public static String convToWarningCode(String name) {
		String result="";
		if (name.equals("本人死亡")){result="301";}
		else if (name.equals("取引停止")){result="302";}
		else if (name.equals("差押え")){result="360";}
		else if (name.equals("支払差し止め")){result="361";}
		else if (name.equals("強制解約")){result="362";}
		else if (name.equals("全額非付保")){result="366";}
		else if (name.equals("一部非付保")){result="367";}
		return result;
	}
	//フラグ変換
	public static String replaceFlag(String flg) {
		String val = flg;
		if (val.equals("*")) {
			return "1";
		} else {
			return "0";
		}
	}
	//ハイフン除去
	public static String delHyphen(String hs){
		String rhs = hs.replaceAll("-","");
		return rhs;
	}
	//空白除去
	public static String delSpace(String ss){
		String rss = ss.replaceAll(" ","");
		return rss;
	}
	/**
	 * 引数の文字列から指定した桁数分の文字を抜き出す
	 * ※全角も１桁と換算
	 * ※trim実施後に変換
	 * 
	 * @param value 抜き出し前の文字列
	 * @param dig 抜き出したい桁数()
	 * @return 
	 */
	public static String getStringByDig(String value,int dig){
		String result;
		String val = value.trim();
		int keta = val.length();
		if(keta <= dig){
			result = val;
		}else{
			result = val.substring(0, dig);
		}
		return result;
	}	
	/**
	 * 国籍コード分解（数字分）
	 * XXXXＸＸＸ→XXXX
	 * 想定外は空を返す
	 */
	public static String getKokusekiCode(String kokuseki) {
		String value = "";
		if(kokuseki.length() == 7){
			if(kokuseki.substring(0,4).matches("[0-9][0-9][0-9][0-9]")){
				value = kokuseki.substring(0,4);
			}
		}
	    return value;
	}
	/**
	 * 国籍コード分解（国略称分）
	 * XXXXＸＸＸ→ＸＸＸ
	 * 想定外は空を返す
	 */
	public static String getKokusekiName(String kokuseki) {
		String value = "";
		if(kokuseki.length() == 7){
			value = kokuseki.substring(4,7);
		}
	    return value;
	}

	/**
	 * 半角英数→全角英数
	 */
	public static String EnToEm(String value) {
	    StringBuilder sb = new StringBuilder(value);
	    for (int i = 0; i < sb.length(); i++) {
	        int c = (int) sb.charAt(i);
	        if ((c >= 0x30 && c <= 0x39) || (c >= 0x41 && c <= 0x5A) || (c >= 0x61 && c <= 0x7A)) {
	            sb.setCharAt(i, (char) (c + 0xFEE0));
	        }
	    }
	    value = sb.toString();
	    return value;
	}
	/**
	 * 全角英数→半角英数
	 */
	public static String EmToEn(String value) {
	    StringBuilder sb = new StringBuilder(value);
	    for (int i = 0; i < sb.length(); i++) {
	        int c = (int) sb.charAt(i);
	        if ((c >= 0xFF10 && c <= 0xFF19) || (c >= 0xFF21 && c <= 0xFF3A) || (c >= 0xFF41 && c <= 0xFF5A)) {
	            sb.setCharAt(i, (char) (c - 0xFEE0));
	        }
	    }
	    value = sb.toString();
	    return value;
	}
	/**
	 * 年度取得
	 */
	public static String getFiscalYear () {
		int year = Integer.parseInt(CommonUtil.getCurrentDate("yyyy"));
		int month = Integer.parseInt(CommonUtil.getCurrentDate("MM"));
		if (month<4) {
			year--;
		}
		return Integer.toString(year);
	}
	/**
	 * boolean変換
	 */
	public static boolean toBoolean (String str) {
		if (str==null) { return false; }
		if (str.isEmpty()) { return false; }
		if (str.equals("0")) { return false; }
		if (str.equals("1")) { return true; }
		return false;
	}
	/**
	 * 【和暦処理】入力した日付から年齢を求める。
	 * 
	 * @param	String	誕生日
	 * 			String	年齢を求めたい時点
	 * @return	"" or 年齢
	 */
	public static String getAge(String birthday, String date){

		String strAge = "";
		if(!"".equals(CommonConverter.convertWareki2(date)) && !"".equals(CommonConverter.convertWareki2(birthday))){
		
			int year1 = Integer.parseInt(birthday.substring(0,4)); 
			int month1 = Integer.parseInt(birthday.substring(4, 6)); 
			int day1 = Integer.parseInt(birthday.substring(6, 8)); 
			int year2 = Integer.parseInt(date.substring(0, 4)); 
			int month2 = Integer.parseInt(date.substring(4, 6)); 
			int day2 = Integer.parseInt(date.substring(6, 8)); 

			int intAge = year2 - year1;
			if (intAge > 0) { 
				if (month1 > month2) { 
					intAge = intAge - 1; 
				} else if (month1 == month2) { 
					if (day1 > day2) { 
						intAge = intAge - 1; 
					}
				}

				strAge = String.valueOf(intAge);
			}
		}
		return strAge;
	}
	
	/**
	 * 金額返還（1234567 ⇒ \1,234,567）
	 * 
	 * @param val 金額変換対象の数値
	 * @return String 金額
	 */
	public static String convertKingaku(String val){
		//null 空白チェック
		if (val==null||val.equals("")) {
			return val;
		}
		//数値チェック
		if(!ValidateUtil.intCheck(val)){
			return val;
		}
		
		//金額
		String kingaku ="";
		
		//金額フォーマット
		int kin =Integer.parseInt(val);
		NumberFormat nf = NumberFormat.getCurrencyInstance();
		kingaku = nf.format(kin);
		
		//フォーマット後の金額を返却
		return kingaku;
	}
	
	/**
	 * 数値チェック　文字列が数値以外だった場合に0に変換
	 * 数値のチェックは自然数チェックを使用(-+,等は数値ではない)
	 * @param String チェック文字列
	 * @return String 変換後文字列
	 */
	public static String digitConvert(String str) {
		String result="";
		if (str==null || str.isEmpty()){
			result="0";
		}else if (!ValidateUtil.numCheck(str)){
			result = "0";
		}else {
			result = str;
		}
		return result;
	}

//=====照会で取得した項目のConverter=====

	/**
	 * nullチェック
	 * 想定外の値は空を返却
	 * 
	 * @param str チェック文字
	 * @return 変わらず or ""
	 */
	public static String chkNull(String str){
		String result = "";
		//nullまたは空チェック
		if(str != null && !"".equals(str)){
			result = str;
		}
		return result;
	}

	/**
	 * 数値変換
	 * 想定外の値は指定桁数で０パディング
	 * 
	 * @param str 変換前の値
	 * @param dig 指定桁数
	 * @return ０パディングされた値
	 */
	public static String chkConvertNumAdd0(String str,int dig){
		String result = CommonConverter.getAdd0String("0",dig);
		//nullまたは空チェック
		if(str != null && !"".equals(str)){
			//数値チェック
			if(ValidateUtil.doubleCheck(str)){
				result = CommonConverter.getAdd0String(str,dig);
			}
		}
		return result;
	}
	
	/**
	 * カンマ変換
	 * 想定外の値は指定桁数で０パディング
	 * 
	 * @param str 変換前の値
	 * @param dig 指定桁数
	 * @return ０パディングされた変換後の値
	 */
	public static String chkDelCommaAdd0(String str,int dig){
		String result = CommonConverter.getAdd0String("0",dig);
		//nullまたは空チェック
		if(str != null && !"".equals(str)){
			//「,」取り除き後に０パディング
			result = CommonConverter.getAdd0String(str.replace(",",""),dig);
			//結果が数値でなければ、０返却
			if(!ValidateUtil.doubleCheck(result)){
				result = CommonConverter.getAdd0String("0",dig);
			}
		}
		return result;
	}

	/**
	 * ハイフン変換
	 * 想定外の値は指定桁数で０パディング
	 * 
	 * @param str 変換前の値
	 * @param dig 指定桁数
	 * @return ０パディングされた変換後の値
	 */
	public static String chkDelHyphenAdd0(String str,int dig){
		String result = CommonConverter.getAdd0String("0",dig);
		//nullまたは空チェック
		if(str != null && !"".equals(str)){
			//「-」取り除き後に０パディング
			result = CommonConverter.getAdd0String(str.replaceAll("-",""),dig);
			//結果が数値でなければ、０返却
			if(!ValidateUtil.doubleCheck(result)){
				result = CommonConverter.getAdd0String("0",dig);
			}
		}
		return result;
	}

	/**
	 * ハイフン変換
	 * 想定外の値は空を返却
	 * 
	 * @param str 変換前の値
	 * @return 変換後
	 */
	public static String chkDelHyphen(String str){
		String result = "";
		//nullまたは空チェック
		if(str != null && !"".equals(str)){
			//「-」取り除く
			result = str.replaceAll("-","");
		}
		return result;
	}

	/**
	 * フラグ変換
	 * "*"は"1"を返却
	 * nullまたは空の場合は"0"を返却
	 * それ以外は値をそのまま返却
	 * 
	 * @param str 変換前の値
	 * @return 変換後
	 */
	public static String chkConvertFlag(String str){
		String result = str;
		//nullまたは空チェック
		if(str != null && !"".equals(str)){
			//「*」である場合は"1"を返却
			if("*".equals(str)){
				result = "1";
			}
		}else{
			result = "0";
		}
		return result;
	}

	/**
	 * 利率変換（1234.56 , 2 → 123456）
	 * 想定外の値は指定桁数で０パディング
	 * 
	 * @param str 変換前の値
	 * @param dig 桁移動分の桁数
	 * @param padDig ０パディング数
	 * @return 変換後
	 */
	public static String chkConvertRate(String str ,int dig, int padDig){
		String result = CommonConverter.getAdd0String("0",padDig);;
		//nullまたは空チェック
		if(str != null && !"".equals(str)){
			//数値チェック
			if(ValidateUtil.doubleCheck(str)){
				double 	dbl = Double.parseDouble(str);
				double multi = Math.pow(10,dig);
				//桁移動して少数点をなくす
				dbl = dbl * multi;
				BigDecimal bd = new BigDecimal(dbl);
				//精度の問題で、小数点以下が出てしまうことがある
				//小数点以下があったら、以下を削除
				result = bd.divide(new BigDecimal("1"),0,BigDecimal.ROUND_DOWN).toPlainString();
			}
		}
		return result;
	}

	/**
	 * 電話番号変換（呼XXXX-XX-XXXX → XXXXXXXXXX）
	 * 想定外の値は"0"を返却
	 * 
	 * @param str 変換前の値
	 * @return 変換後 or "0"
	 */
//	public static String chkConvertTel(String str){
//		String result = "0";
//		//nullまたは空チェック
//		if(str != null && !"".equals(str)){
//			//先頭「呼」取り除く
//			String rTelNo = str.replaceFirst("呼", "");
//			//先頭「0」取り除く（ＤＢが数値型の為）
//			rTelNo=rTelNo.replaceFirst("^0+", "");
//			//「-」取り除く
//			rTelNo = rTelNo.replaceAll("-","");
//			result = rTelNo;
//			//結果が数値でなければ、０返却
//			if(!ValidateUtil.doubleCheck(result)){
//				result = "0";
//			}
//		}
//		return result;
//	}
	/**
	 * 電話番号変換（呼XXXX-XX-XXXX → XXXXXXXXXX）
	 * 想定外の値は""を返却
	 * 
	 * @param str 変換前の値
	 * @return 変換後 or ""
	 */
	public static String chkConvertTel(String str){
		String result = "";
		//nullまたは空チェック
		if(str != null && !"".equals(str)){
			//先頭「呼」取り除く
			String rTelNo = str.replaceFirst("呼", "");
			//先頭「0」取り除く（ＤＢが数値型の為）
			//rTelNo=rTelNo.replaceFirst("^0+", "");
			//「-」取り除く
			rTelNo = rTelNo.replaceAll("-","");
			result = rTelNo;
			//結果が数値でなければ、ブランク返却
			if(!ValidateUtil.doubleCheck(result)){
				result = "";
			}
		}
		return result;
	}

	/**
	 * 【和暦処理】日付変換（Gyy-mm-dd → yyyyMMdd）
	 * 想定外の値は８桁で０パディング
	 * 
	 * @param str 変換前の値
	 * @return ０パディングされた値
	 */
	public static String chkConvertGengoDateAdd0(String str){
		String result ="0";
		//nullまたは空チェック
		if(str != null && !"".equals(str)){
			//桁数チェック
			if(str.length()==9){
				//それぞれ分割
				String gengo  = str.substring(0,1);
				String year  = CommonConverter.getAdd0String(str.substring(1,3),2);
				String month = CommonConverter.getAdd0String(str.substring(4,6),2);
				String day   = CommonConverter.getAdd0String(str.substring(7,9),2);
				//元号変換
				if(gengo.equals("明")){
					gengo="M";
				}else if(gengo.equals("大")){
					gengo="T";
				}else if(gengo.equals("昭")){
					gengo="S";
				}else if(gengo.equals("平")){
					gengo="H";
				}else if(gengo.equals("令")){
					gengo="R";
				}
				//GyyMMddの形に変換
				String wareki = gengo + year + month + day;
				//西暦変換
				String seireki = CommonConverter.convertSeireki2(wareki);
				//NGの場合でも０パディングして返却
				result = CommonConverter.getAdd0String(seireki,8);
			}
		}
		return result;
	}
	
	/**
	 * 【和暦処理】日付変換２（ GYY-MM-DD(和) → YYYYMMDD(西暦) or YY-MM-DD(和) → YYYYMMDD(西暦)）
	 * 変換元に元号コードが無い（YY-MM-DD）場合は、
	 * 48年以降は昭和、25年以降は平成、それ以前は令和として西暦に変換　⇒　【稟議支援と同じ条件】
	 * 
	 * @param str 変換前の値
	 * @return 西暦変換和暦
	 * 想定外の値は空文字を返す
	 */
	public static String chkConvertDateAdd0(String str){
		
		String val = str;
		if (val==null||val.equals("")) {
			return "";
		}
		
		//フォーマットチェックし、元号がついていれば西暦に変換する
		if ((val.matches("[A-Z][0-9 ][0-9]-[0-9 ][0-9]-[0-9 ][0-9]"))) {
			
			//要素を取得
			String[] vals=val.split("-");
			String gengo=(vals[0]).substring(0,1);
			String year=(vals[0]).substring(1,3);
			String month=vals[1];
			String day=vals[2];
			
			//FW共通部品で西暦変換
			StringBuilder sb = new StringBuilder();
			sb.append(gengo);
			sb.append(CommonConverter.getAdd0String(year,2));
			sb.append(CommonConverter.getAdd0String(month,2));
			sb.append(CommonConverter.getAdd0String(day,2));
			String adyear = CommonConverter.convertSeireki2(sb.toString());
			
			//結果を格納し、リターン
			return adyear;
			
		}
		
		//フォーマットチェックし、元号がついていなければ、48年以降は昭和、25年以降は平成、それ以前は令和として西暦に変換する
		if ((val.matches("[0-9 ][0-9]-[0-9 ][0-9]-[0-9 ][0-9]")
				||val.matches("[0-9]-[0-9 ][0-9]-[0-9 ][0-9]"))) {
			
			if(val==null||val.equals("")){return "";}
			
			//要素を取得
			String[] vals=val.split("-");
			String year=vals[0];
			String month=vals[1];
			String day=vals[2];
			
			//48年以降は昭和、25年以降は平成、それ以前は令和
			int intyear=Integer.parseInt(year);
			String gengo;
			
			if (intyear<25) {
				gengo="R";
			} else if (intyear<48) {
				gengo="H";
			} else {
				gengo="S";
			}
	
			//FW共通部品で西暦変換
			StringBuilder sb = new StringBuilder();
			sb.append(gengo);
			sb.append(CommonConverter.getAdd0String(year,2));
			sb.append(CommonConverter.getAdd0String(month,2));
			sb.append(CommonConverter.getAdd0String(day,2));
			String adyear = CommonConverter.convertSeireki2(sb.toString());
	
			//結果を格納
			return adyear;
			
		}
		
		//フォーマットチェックに該当しなければ、空文字を返却する
		return "";
		
	}
	/**
	 * 【和暦処理】日付変換３（ GYY-MM-DD(和) → YYYYMMDD(西暦) or YY-MM-DD(和) → YYYYMMDD(西暦)）
	 * 変換元に元号コードが無い（YY-MM-DD）場合は、
	 * 48年以降は昭和、25年以降は平成、それ以前は令和として西暦に変換　⇒　【稟議支援と同じ条件】
	 * 
	 * @param str 変換前の値
	 * @return 西暦変換和暦
	 * 想定外の値は空文字を返す
	 */
	public static String chkConvertSysDateAdd0(String str){
		
		String val = str;
		if (val==null||val.equals("")) {
			return "";
		}
		
		//フォーマットチェックし、元号がついていれば西暦に変換する
		if ((val.matches("[A-Z][0-9 ][0-9]-[0-9 ][0-9]-[0-9 ][0-9]"))) {
			
			//要素を取得
			String[] vals=val.split("-");
			String gengo=(vals[0]).substring(0,1);
			String year=(vals[0]).substring(1,3);
			String month=vals[1];
			String day=vals[2];
			
			//FW共通部品で西暦変換
			StringBuilder sb = new StringBuilder();
			sb.append(gengo);
			sb.append(CommonConverter.getAdd0String(year,2));
			sb.append(CommonConverter.getAdd0String(month,2));
			sb.append(CommonConverter.getAdd0String(day,2));
			String adyear = CommonConverter.convertSeireki2(sb.toString());
			
			//結果を格納し、リターン
			return adyear;
		}
		
		//フォーマットチェックし、元号がついていなければ、48年以降は昭和、25年以降は平成、それ以前は令和として西暦に変換する
		if ((val.matches("[0-9 ][0-9]-[0-9 ][0-9]-[0-9 ][0-9]")
				||val.matches("[0-9]-[0-9 ][0-9]-[0-9 ][0-9]"))) {
			
			if(val==null||val.equals("")){return "";}
			
			//要素を取得
			String[] vals=val.split("-");
			String year=vals[0];
			String month=vals[1];
			String day=vals[2];
			
			//48年以降は昭和、25年以降は平成、それ以前は令和
			int intyear=Integer.parseInt(year);
			String gengo;
			
			if (intyear<25) {
				gengo="R";
			} else if (intyear<48) {
				gengo="H";
			} else {
				gengo="S";
			}
	
			//FW共通部品で西暦変換
			StringBuilder sb = new StringBuilder();
			sb.append(gengo);
			sb.append(CommonConverter.getAdd0String(year,2));
			sb.append(CommonConverter.getAdd0String(month,2));
			sb.append(CommonConverter.getAdd0String(day,2));
			String adyear = CommonConverter.convertSeireki2(sb.toString());
	
			//結果を格納
			return adyear;
		}
		
		//フォーマットチェックに該当しなければ、空文字を返却する
		return "";
		
	}
	/**
	 * 代表者資格のコードを削除し、名称を返却する
	 * 
	 */
	public static String getRecepCapacityName(String code) throws Exception{
		try{
			FWLog.debug("代表者資格"+code+" 文字列の長さ："+code.length());
			//空白かNULLの場合空文字を返す
			if(code==null || code.isEmpty() || code.length()<3){
				return "";
			}
			return code.substring(2,code.length());
		}catch(Exception e){
			FWLog.error("代表者資格のコード削除時エラー⇒⇒"+e);
			throw e;
		}
	}
	/**
	 * 代表者資格からコードのみ抽出する
	 * 
	 * @param String 代表者資格(代表者資格コード＋名称)
	 * @return String 代表者資格コード(2桁)
	 */
	public static String getRecepCapacityCode(String code) throws Exception{
		try{
			FWLog.debug("代表者資格"+code+" 文字列の長さ："+code.length());
			//空白かNULLの場合空文字を返す
			if(code==null || code.isEmpty() || code.length()<3){
				return "";
			}
			return code.substring(0,2);
		}catch(Exception e){
			FWLog.error("代表者資格の抽出時エラー⇒⇒"+e);
			throw e;
		}
	}
	/**
	 * 付属名称から「代表者名」を切り取り、役職名に張り替える。
	 * 役職名:「40:漢字代表者登録（任意）」「41:カナ代表者登録（任意）」は役職名を空白に置き換える。
	 * 
	 * @param String Str1	役職名
	 * @param String Str2	付属名称
	 * 
	 * @return	String 役職名+付属名称
	 */
	public static String getAddManageNameToRecepName(String str1, String str2){
		//空白、NULLチェック
		boolean emptyFlg1 = false;
		boolean emptyFlg2 = false;
		if(str1==null || str1.isEmpty()){
			emptyFlg1=true;
		}else if(str1.equals("漢字代表者登録（任意）")||str1.equals("カナ代表者登録（任意）")){
			emptyFlg1=true;
		}
		if(str2==null || str2.isEmpty()){
			emptyFlg2=true;
		}
		
		if(emptyFlg1){
			if(emptyFlg2){
				//空白かNULLの場合空文字を返す
				return "";
			}else{
				//付属名称のみの場合、付属名称を返す
				if(4<str2.length() && str2.substring(0, 5).equals("代表者名 ")){
					//付属名称から代表者名を切り取り、役職名に張り替えた値を返す。
					StringBuilder sb = new StringBuilder(); 
					sb.append(str2.substring(5, str2.length()));
					return sb.toString();
				}else{
					//役職名+付属名称を返す
					StringBuilder sb = new StringBuilder();
					sb.append(str2);
					return sb.toString();
				}
			}
		}else{
			if(emptyFlg2){
				//役職名のみの場合、役職名を返す
				return str1;
			}else{
				if(4<str2.length() && str2.substring(0, 5).equals("代表者名 ")){
					//付属名称から代表者名を切り取り、役職名に張り替えた値を返す。
					StringBuilder sb = new StringBuilder(str1); 
					sb.append(" ");
					sb.append(str2.substring(5, str2.length()));
					return sb.toString();
				}else{
					//役職名+付属名称を返す
					StringBuilder sb = new StringBuilder(str1);
					sb.append(" ");
					sb.append(str2);
					return sb.toString();
				}
			}
		}
	}
	/**
	 * 付属名称から先頭5文字「屋　　号」を切り取る
	 * @param String Str	付属名称
	 * 
	 * @return	String 切取った付属名称
	 * 
	 * null又は空文字の場合、空文字を返す
	 */
	public static String getSplitTopYagou(String str){
		if (str==null||str.equals("")) {
			return "";
		}
		//5文字未満か屋号以外はチェックしない
		if(str.length()<5){
			return str;
		}
		if(!str.substring(0, 5).equals("屋　　号 ")){
			return str;
		}
		//先頭5文字を切取る。
		StringBuilder sb = new StringBuilder(); 
		sb.append(str.substring(5, str.length()));
		return sb.toString();
	}
	/**
	 * 付属名称の先頭5文字が「勤務先名 」か判定する
	 * @param String Str	付属名称
	 * 
	 * @return	boolean true:勤務先名　false:勤務先名で無い
	 * 
	 * null又は空文字の場合、空文字を返す
	 */
	public static boolean isStrTopKinmusaki(String str){
		if (str==null||str.equals("")) {
			return false;
		}
		//5文字未満か屋号以外はチェックしない
		if(str.length()<5){
			return false;
		}
		if(!str.substring(0, 5).equals("勤務先名 ")){
			return false;
		}
		//上記いずれの条件にも当てはまらなければtrueを返す
		return true;
	}
	/**
	 * 付属名称から先頭5文字「代表者名 」を削除した名称(代表者名)を取得する
	 * 
	 * @param String Str	付属名称
	 * @return	String 切取った付属名称
	 * null又は空文字の場合、空文字を返す
	 */
	public static String getSplitTopDaihyo(String str){
		if (str==null||str.equals("")) {
			return "";
		}
		//5文字未満か屋号以外はチェックしない
		if(str.length()<5){
			return str;
		}
		if(!str.substring(0, 5).equals("代表者名 ")){
			return str;
		}
		//先頭5文字を切取る。
		StringBuilder sb = new StringBuilder(); 
		sb.append(str.substring(5, str.length()));
		return sb.toString();
	}
	
//=======================================役席管理・仕掛一覧で使用=============================================================
	/**
	 * 事象IDから事象名を取得する。
	 * 
	 */
	public static String getEventNameByEventId(String eventId){
		String[][] list = {{"SOZOKU","HENKOU","SASIOS","SOSITU","JYUNIN","SEINEN"}
							,{"相続","変更届","差押","喪失","受任通知","成年後見制度"}};
		String eventName="";
		if (eventId==null||eventId.equals("")) {
			return "全て";
		}
		for(int i=0;i<list[0].length;i++){
			if(eventId.equals(list[0][i])){eventName=list[1][i];}
		}
		return eventName;
	}
	/**
	 * 受付区分コードから名称を取得する
	 * 
	 * @param code		受付区分コード（先頭２ケタ０埋め）
	 * @param String	受付区分名称
	 */
	public static String getUkeKubunNameByUkeKubunCode(String code){
		String[][] list = {{"01","02","03","04","05","06","07","09"}
							,{"窓口","営業","電話","ＰＣ","ＳＩＳ","ﾃﾚﾎﾝ","ｱﾌﾟﾘ","その他"}};
		String name="";
		if (code==null||code.equals("")) {
			return "";
		}else{
			code = CommonConverter.getAdd0String(code, 2);
		}
		for(int i=0;i<list[0].length;i++){
			if(code.equals(list[0][i])){name=list[1][i];}
		}
		return name;
	}
		
	
	/**
	 * value値から状態を取得する。
	 * 
	 */
	public static String getStatNameByValue(String val){
		String[][] list = {{"3","4","5","100"}
							,{"仕掛中","完了済","長期未完了","証跡印刷"}};
		String Name="";
		if (val==null||val.equals("")) {
			return "全て";
		}
		for(int i=0;i<list[0].length;i++){
			if(val.equals(list[0][i])){Name=list[1][i];}
		}
		return Name;
	}
	/**
	 * InputStreamをbyte[]に変換する
	 * 
	 * @param BufferdInputStream
	 * @return byte[] InputStreamをbyte[]変換した値
	 */
	static public byte[] inputToByteArray(BufferedInputStream inputStream) throws IOException {
		ByteArrayOutputStream bout = new ByteArrayOutputStream();
		byte [] buffer = new byte[1024];
		while(true) {
			int len = inputStream.read(buffer);
			if(len < 0) {
				break;
			}
			bout.write(buffer, 0, len);
		}
		return bout.toByteArray();
	}

}
