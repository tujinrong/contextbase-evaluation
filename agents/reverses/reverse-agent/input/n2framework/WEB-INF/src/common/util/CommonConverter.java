/*
 * 作成日: 2007/05/29
 *
 */
package common.util;

import java.util.Calendar;
import java.util.GregorianCalendar;


/**
 * 項目変換共通ユーティリティクラス。
 * メソッドは必ずstaticメソッドにする。
 * 定数以外のメンバ変数は持たせない。
 *
 * @author JSC kengo murayama
 *
 * @date	H22.9.6		青木・浅見		センター集約対応なし
 * @date	H31.3.29	Minori山口		新元号対応
 * @date	R02.9.30	富永         			元号対応 20190430⇒20190432
 */
public class CommonConverter {

	/** 元号 | 自年月日 | 至年月日 */
	private static final String [][]gengoTable= {
		{"平成","19890108","99999999"},
		{"昭和","19261225","19890107"},
		{"大正","19120730","19261224"},
		{"明治","18680908","19120729"},
		{"不明","00000000","18680907"}
	};

	/**
	 * 西暦（YYYYMMDD）⇒ 和暦（年号X年XX月XX日）の変換
	 * 
	 * @param seireki 編集前の数字
	 * @return 編集後の結果<br>
	 * null又は８桁以外の場合、空文字を返す
	 */
	public static String convertWareki(String seireki){
		//８桁ＣＨＥＣＫ	
		if(seireki == null || (seireki.length() != 8)){
			return "";
		}

		//ニューメリックＣＨＥＣＫ
		try{
			Integer.parseInt(seireki);
		}
		catch(NumberFormatException nfe){
			return "";
		}

//		if(!checkDate(seireki)){
//			throw new CifApplicationException("1008-02" +"暦上日を入力して下さい" + seireki);
//		}
		
		int i = 0;
		for(  ; i < gengoTable.length;i++){
			if(Integer.parseInt(seireki) >= Integer.parseInt(gengoTable[i][1]) && Integer.parseInt(seireki) <= Integer.parseInt(gengoTable[i][2])){
				break;
			}
		}
		if (gengoTable[i][0].equals("不明")){
			return "";
		}
		
		String wareki = "";
		wareki = gengoTable[i][0];
		int year =Integer.parseInt(seireki.substring(0,4)) - Integer.parseInt(gengoTable[i][1].substring(0,4)) + 1 ;
		if(year < 10 ){
			wareki = wareki + "0";
		}
		wareki = wareki + Integer.toString(year) + "年" + seireki.substring(4,6) + "月" + seireki.substring(6,8) + "日"; 
		
		return wareki;
		 
	}

	/**
     * 西暦8桁yyyymmddのString引数から和暦に返還しString型の和暦を返す。
     * @param  seireki   西暦8桁のString
     *
     * @return 和暦 元号"H"or"S"or"T"+yymmdd"フォーマット
     */
	public static String convertSimpleWareki(String seireki){
		try {
			StringBuffer sbDate;

			if(seireki==null){
				sbDate=new StringBuffer("");
			}else{
				sbDate=new StringBuffer(convertWareki(seireki));
				sbDate.delete(10,11);
				sbDate.delete(7,8);
				sbDate.delete(4,5);
				if(sbDate.substring(0,2).equals("平成")){
					sbDate.replace(0,2,"H");
				}else if(sbDate.substring(0,2).equals("昭和")){
					sbDate.replace(0,2,"S");
				}else if(sbDate.substring(0,2).equals("大正")){
					sbDate.replace(0,2,"T");
				}else if(sbDate.substring(0,2).equals("明治")){
					sbDate.replace(0,2,"M");
				}else{
					return "";
				}
			}

			return sbDate.toString();

		} catch (Exception e) {
			//和暦変換ができない場合は空文字で返す。
			return "";
		}
	}

	/**
	 * 和暦（GyyMMdd）を、ドット区切り（Gyy.MM.dd）に変換する。
	 * 
	 * @param wareki
	 * @return
	 */
	public static String editSimpleWarekiDot(String wareki){
		if(wareki != null && wareki.length() == 7){
			StringBuffer sb = new StringBuffer();

			sb.append(wareki.substring(0,3));
			sb.append(".");
			sb.append(wareki.substring(3,5));
			sb.append(".");
			sb.append(wareki.substring(5,7));

			return sb.toString();

		} else {
			return "";
		}
	}

	/**
	 * 和暦（GyyMMdd）⇒西暦（yyyyMMdd）変換
	 * 
	 * @param wareki
	 * @return
	 * @throws Exception
	 */
	public static String convertSeireki(String wareki){
		try {
			if(wareki != null && wareki.length() == 7){
				String gengo = wareki.substring(0,1);
				int date = Integer.parseInt(wareki.substring(1));

				//00年の入力は不可
				if(date < 10000){
					return "";
				}

				String seireki;
				if(gengo.equals("M")){
					//明治
					seireki = String.valueOf(18670000 + date);
				}else if(gengo.equals("T")){
					//大正
					seireki = String.valueOf(19110000 + date);
				}else if(gengo.equals("S")){
					//昭和
					seireki = String.valueOf(19250000 + date);
				}else if(gengo.equals("H")){
					//平成
					seireki = String.valueOf(19880000 + date);
				}else{
					//その他の元号は変換不可
					seireki = "";
				}

				//和暦の整合性が取れない（平成元年１月１日など）場合、変換不可
				if(wareki.equals(convertSimpleWareki(seireki))){
					return seireki;
				} else {
					return "";
				}
			} else {
				return "";
			}
		} catch (NumberFormatException e) {
			//数値以外が日付部分に入っていたら空文字で返す。
			return "";
		}
	}

	/**
	 * 日付妥当性チェック
	 * 
	 * @param date　西暦（yyyyMMdd）
	 * @return
	 */
	public static boolean checkDate(String seireki){

		if(seireki != null && seireki.length() == 8){
			try {
				//年・月・日に分割
				int year = Integer.parseInt(seireki.substring(0,4));
				int month = Integer.parseInt(seireki.substring(4,6));
				int day = Integer.parseInt(seireki.substring(6,8));

				return checkDate(year, month, day);

			} catch (NumberFormatException e) {
				return false;
			}
		} else {
			return false;
		}
	}

	/**
	 * 日付妥当性チェック
	 * 
	 * @param year
	 * @param month
	 * @param day
	 * @return
	 */
	public static boolean checkDate(int year,int month,int day ){
		try {
			Calendar cal = new GregorianCalendar();

			//日付/時刻の解釈を厳密に行う設定にする
			cal.setLenient( false );

			//年、月、日付のフィールドに値を設定（Month 値は 0 から始まる。つまり、0 は 1 月）
			cal.set(year, month -1, day);

			//Calendar の現在時刻を取得し、不正な引数だった場合はException発生し、チェックＮＧ
			cal.getTime();

			//ここまで到達したら日付チェックＯＫ
			return true;

		} catch (IllegalArgumentException e) {
			return false;
		}
	}

	/**
	 * HHmmss -> HH:mm:ssの時刻変換
	 * 
	 * @param jikoku 編集前の数字
	 * @return 編集後の結果<br>
	 * null又は６桁以外の場合、空文字を返す
	 */
	public static String convertTime(String jikoku){
		//６桁ＣＨＥＣＫ	
		if(jikoku == null || (jikoku.length() != 6)){
			return "";
		}

		//ニューメリックＣＨＥＣＫ
		try{
			Integer.parseInt(jikoku);
		}
		catch(NumberFormatException nfe){
			return "";
		}

		return jikoku.substring(0,2) + ":" + jikoku.substring(2,4) + ":" + jikoku.substring(4,6);
	}

	/**
	 * (注意)LASUtilから借用
	 * 引数valueがnull又は「null」文字列だった場合、空文字を返す。
	 * その他の場合は引数をそのまま返す。
	 */
	public static String null2blank(String value) {
		if (value == null || value.equalsIgnoreCase("null")) {
			return "";
		} else {
			return value.trim();
		}
	}

	/**
	 * 桁数をそろえるため、文字列頭に0を付加する
	 * @param sValue 編集前の数字
	 * @param iKeta 桁数
	 * @return result 編集後の結果<br>
	 * null又は空文字の場合、空文字を返す
	 */
	public static String getAdd0String(String sValue, int iKeta) {
		String sVal = null2blank(sValue);

		if (sVal.equals("")) {
			return "";
		}

		sVal = sVal.trim();
		int iLen = sVal.length();

		//値が桁数以上だった場合、文字列を編集せずに返す
		if (iLen >= iKeta) {
			return sVal;
		}

		StringBuffer sbVal = new StringBuffer(sVal);
		for (int i = iLen; i < iKeta; i++) {
			sbVal.insert(0, "0");
		}

		return sbVal.toString();
	}

	/**
	 * 文字列型をint型に変換する
	 * 空文字だった場合、0を返す
	 * 
	 * @param str 変換前の文字列
	 * @return
	 * @throws NumberFormatException
	 */
	public static int convertInt(String str) throws NumberFormatException{
		if(str != null && !"".equals(str) && !"0".equals(str)){
			try {
				return Integer.parseInt(str);
			} catch (NumberFormatException e) {
				throw e;
			}
		} else {
			return 0;
		}
	}

	/**
	 * 文字列型をlong型に変換する
	 * 空文字だった場合、0を返す
	 * 
	 * @param str 変換前の文字列
	 * @return
	 * @throws NumberFormatException
	 */
	public static long convertLong(String str) throws NumberFormatException{
		if(str != null && !"".equals(str) && !"0".equals(str)){
			try {
				return Long.parseLong(str);
			} catch (NumberFormatException e) {
				throw e;
			}
		} else {
			return 0;
		}
	}

	/** 
	 * String引数に、下記の通りにハイフンを付与した形式に編集し、
	 * String型の文字列として返す。
	 *	引数が１０桁　→　携帯電話：０９０ＸＸＸＸ－ＸＸＸＸ	
	 *	引数が９桁　　→　固定電話：　ＸＸＸＸＸＸーＸＸＸＸ
	 *	引数の先頭がゼロ　→　空白
	 * @param  tel   ハイフンを付与したいString
	 *
	 * @return ハイフンを付与した形式のString
	 */
	public static String editTelephone(String tel){

		String editTel = "";
		if(tel != null && !"0".equals(tel.substring(0,1))){
			String phone = "0" + tel;

			switch (tel.length() ){
				case 10:
					editTel = phone.substring(0,7) + "-" + phone.substring(7,11);
					break;
				case 9:
					editTel = phone.substring(0,6) + "-" + phone.substring(6,10);
					break;
			}
		}
		return  editTel;
	}

	/** 
	 * String引数を３桁ごとのカンマを付与した形式に編集し、
	 * String型の文字列として返す。（先頭のゼロは除去する）
	 * なお、先頭の１文字が数字でなければ、記号とみなし反映する。
	 * 　　　２文字目以降に数字以外があれば、"PARAMERR"を返す。
	 *
	 * @param  kingaku   カンマを付与したいString
	 *
	 * @return ３桁ごとのカンマを付与した形式のString（先頭のゼロは除去する）
	 */
	public static String editComma(String kingaku) {

		String editKingaku = kingaku;

		//先頭１文字目が数字以外の場合、最後に付加する処理
		String fugou  ="";
		try{
			//チェックするだけ
			Integer.parseInt(editKingaku.substring(0,1));
		}
		catch(NumberFormatException nfe){
			fugou = editKingaku.substring(0,1);
			editKingaku = editKingaku.substring(1,editKingaku.length());
		}

		//２文字目以降のニューメリックＣＨＥＣＫ
		int startPoint;
		int endPoint;
		for( int cnt =editKingaku.length(); cnt > 0 ; cnt = cnt - 9 ){
			endPoint = cnt;
			if(cnt > 9){
				startPoint = cnt - 9;
			}
			else{
				startPoint = 0;
			}

			try{
				//チェックするだけ
				Integer.parseInt(editKingaku.substring(startPoint,endPoint));
			}
			catch(NumberFormatException nfe){
				return "";
			}
		}

		//先頭ゼロの除去
		for(int cnt  =editKingaku.length(); cnt > 1 ; cnt = cnt - 1 ){
			
			if(editKingaku.substring(0,1).compareTo("0") == 0){
				editKingaku = editKingaku.substring(1,cnt);
			}
			else{
				cnt = 0;
			}
	
		}

		//カンマを付加
		int leng = editKingaku.length();
		int setCount = (leng -1 ) / 3;
		int setPoint = leng % 3 ;
		if( setPoint == 0 ){
			setPoint = setPoint + 3;
		}

		for( ; setCount > 0 ; setCount-- ){
			editKingaku = editKingaku.substring(0,setPoint) + "," + editKingaku.substring(setPoint,leng);
			setPoint = setPoint + 4;
			leng++;
		}  

		//NECIKO if(fugou != ""){
		if(!fugou.equals("")){
			editKingaku = fugou + editKingaku;
		} 

		return editKingaku;
	 }
	/**
	 * 性別コードをアルファベットに変換する
	 * 1→M 2→W（想定外は空を返却）
	 * 
	 * @param str 変換前の文字列
	 * @return 
	 */
	public static String convertSex(String code){
		String str = "";
		if("1".equals(code)){
			str = "M";
		} else if("2".equals(code)){
			str = "W";
		}
		return str;
	}





/************************* 元号対応後　*************************/



	/** 元号 | 自年月日 | 至年月日 */
	private static final String [][]gengoTable2= {
		{"令和","20190501","99999999"},
		{"平成","19890108","20190432"},
		{"昭和","19261225","19890107"},
		{"大正","19120730","19261224"},
		{"明治","18680908","19120729"},
		{"不明","00000000","18680907"}
	};

	/**
	 * 西暦（YYYYMMDD）⇒ 和暦（年号X年XX月XX日）の変換
	 * 
	 * @param seireki 編集前の数字
	 * @return 編集後の結果<br>
	 * null又は８桁以外の場合、空文字を返す
	 */
	public static String convertWareki2(String seireki){
		//８桁ＣＨＥＣＫ	
		if(seireki == null || (seireki.length() != 8)){
			return "";
		}

		//ニューメリックＣＨＥＣＫ
		try{
			Integer.parseInt(seireki);
		}
		catch(NumberFormatException nfe){
			return "";
		}

//		if(!checkDate(seireki)){
//			throw new CifApplicationException("1008-02" +"暦上日を入力して下さい" + seireki);
//		}
		
		int i = 0;
		for(  ; i < gengoTable2.length;i++){
			if(Integer.parseInt(seireki) >= Integer.parseInt(gengoTable2[i][1]) && Integer.parseInt(seireki) <= Integer.parseInt(gengoTable2[i][2])){
				break;
			}
		}
		if (gengoTable2[i][0].equals("不明")){
			return "";
		}
		
		String wareki = "";
		wareki = gengoTable2[i][0];
		int year =Integer.parseInt(seireki.substring(0,4)) - Integer.parseInt(gengoTable2[i][1].substring(0,4)) + 1 ;
		if(year < 10 ){
			wareki = wareki + "0";
		}
		wareki = wareki + Integer.toString(year) + "年" + seireki.substring(4,6) + "月" + seireki.substring(6,8) + "日"; 
		
		return wareki;
		 
	}

	/**
     * 西暦8桁yyyymmddのString引数から和暦に返還しString型の和暦を返す。
     * @param  seireki   西暦8桁のString
     *
     * @return 和暦 元号"H"or"S"or"T"+yymmdd"フォーマット
     */
	public static String convertSimpleWareki2(String seireki){
		try {
			StringBuffer sbDate;

			if(seireki==null){
				sbDate=new StringBuffer("");
			}else{
				sbDate=new StringBuffer(convertWareki2(seireki));
				sbDate.delete(10,11);
				sbDate.delete(7,8);
				sbDate.delete(4,5);
				if(sbDate.substring(0,2).equals("令和")){
					sbDate.replace(0,2,"R");
				}else if(sbDate.substring(0,2).equals("平成")){
					sbDate.replace(0,2,"H");	
				}else if(sbDate.substring(0,2).equals("昭和")){
					sbDate.replace(0,2,"S");
				}else if(sbDate.substring(0,2).equals("大正")){
					sbDate.replace(0,2,"T");
				}else if(sbDate.substring(0,2).equals("明治")){
					sbDate.replace(0,2,"M");
				}else{
					return "";
				}
			}

			return sbDate.toString();

		} catch (Exception e) {
			//和暦変換ができない場合は空文字で返す。
			return "";
		}
	}


	/**
	 * 和暦（GyyMMdd）⇒西暦（yyyyMMdd）変換
	 * 
	 * @param wareki
	 * @return
	 * @throws Exception
	 */
	public static String convertSeireki2(String wareki){
		try {
			if(wareki != null && wareki.length() == 7){
				String gengo = wareki.substring(0,1);
				int date = Integer.parseInt(wareki.substring(1));

				//00年の入力は不可
				if(date < 10000){
					return "";
				}

				String seireki;
				if(gengo.equals("M")){
					//明治
					seireki = String.valueOf(18670000 + date);
				}else if(gengo.equals("T")){
					//大正
					seireki = String.valueOf(19110000 + date);
				}else if(gengo.equals("S")){
					//昭和
					seireki = String.valueOf(19250000 + date);
				}else if(gengo.equals("H")){
					//平成
					seireki = String.valueOf(19880000 + date);
				}else if(gengo.equals("R")){
					//**
					seireki = String.valueOf(20180000 + date);	
				}else{
					//その他の元号は変換不可
					seireki = "";
				}

				//和暦の整合性が取れない（平成元年１月１日など）場合、変換不可
				if(wareki.equals(convertSimpleWareki2(seireki))){
					return seireki;
				} else {
					return "";
				}
			} else {
				return "";
			}
		} catch (NumberFormatException e) {
			//数値以外が日付部分に入っていたら空文字で返す。
			return "";
		}
	}


}
