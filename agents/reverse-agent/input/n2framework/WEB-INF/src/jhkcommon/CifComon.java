package jhkcommon;

/**
 *
 * 顧客基本情報　共通メソッド
 *
 * Copyright 王子信用金庫 2001
 *
 * @date	H22.8.19	青木・浅見		センター集約対応
 * @date	H28.9.13	宮田		　　　 全角カナ→半角カナの変換にハイフンと長音を追加
 * @date	H28.12.19	吉津		　　　 数値カンマ編集（LONG型）を追加
 */

//CifComon.java
//
//
//	顧客基本情報　共通メソッド
//
//
//	Copyright 王子信用金庫 2001
//
//

import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.text.NumberFormat;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.GregorianCalendar;
import java.util.TimeZone;


/** 
  * 顧客情報システム共通クラス
  */


public class CifComon {

	private String gsSFilePath;

								// 元号 | 自年月日 | 至年月日
	private String [][]gengoTable= 
							{
								{"平成","19890108","99999999"},
								{"昭和","19261225","19890107"},
								{"大正","19120730","19261224"},
								{"明治","18680908","19120729"},
								{"不明","00000000","18680907"}
							};
	int giCnt;
	public String s;


	SimpleDateFormat gSDFDate = new SimpleDateFormat("yyyyMMdd");
	SimpleDateFormat gSDFTime = new SimpleDateFormat("HHmmss");
	Calendar cal = new GregorianCalendar();

	public CifComon(String sSFilePath,String sDBServ,String sDBUser,String sDBPass)
	{

		gsSFilePath = sSFilePath;

	}

	//YYYYMMDD->和暦（年号X年XX月XX日）
	public String getWareki(String seireki)throws Exception
	{
		//８桁ＣＨＥＣＫ	
		if(seireki.length() != 8){
			if(seireki.length() != 10){
				throw new CifApplicationException("1008-02" +"西暦８or10桁を入力して下さい" + seireki);
			}else{
				if(seireki.substring(4,5).equals("-")&&seireki.substring(7,8).equals("-")){
					StringBuffer sbDate=new StringBuffer(seireki);
					sbDate.delete(7,8);
					sbDate.delete(4,5);
					seireki=sbDate.toString();
				}else{
					throw new CifApplicationException("1008-02" +"西暦10桁を入力して下さい" + seireki);
				}
			}
		}
		//ニューメリックＣＨＥＣＫ
		try{
			int wk =  Integer.parseInt(seireki);
		}
		catch(NumberFormatException nfe){
			throw new CifApplicationException("1007-02" + seireki);
		}
		if(!checkDate(seireki)){
			throw new CifApplicationException("1008-02" +"暦上日を入力して下さい" + seireki);
		}
		
		int i = 0;
		for(  ; i < gengoTable.length;i++){
			if(Integer.parseInt(seireki) >= Integer.parseInt(gengoTable[i][1]) && Integer.parseInt(seireki) <= Integer.parseInt(gengoTable[i][2])){
				break;
			}
		}
		if (gengoTable[i][0].equals("不明")){
			throw new CifApplicationException("1008-02"+":明治元年より過去の日付が入力された"+ seireki);
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
	 * 西暦（YYYYMMDD）⇒ 和暦（年号X年XX月XX日）の変換
	 * 
	 * @param seireki 編集前の数字
	 * @return 編集後の結果<br>
	 * null又は８桁以外の場合、空文字を返す
	 */
	//YYYYMMDD->和暦（年号X年XX月XX日）
	public String getWarekiHenkan(String seireki)throws Exception
	{
		//８桁ＣＨＥＣＫ	
		if(seireki == null || (seireki.length() != 8)){
			return "";
		}

		//ニューメリックＣＨＥＣＫ
		try{
			int wk =  Integer.parseInt(seireki);
		}
		catch(NumberFormatException nfe){
			throw new CifApplicationException("1007-02" + seireki);
		}
		
		int i = 0;
		for(  ; i < gengoTable.length;i++){
			if(Integer.parseInt(seireki) >= Integer.parseInt(gengoTable[i][1]) && Integer.parseInt(seireki) <= Integer.parseInt(gengoTable[i][2])){
				break;
			}
		}
		if (gengoTable[i][0].equals("不明")){
			throw new CifApplicationException("1008-02"+":明治元年より過去の日付が入力された"+ seireki);
		}
		
		String wareki = "";
		wareki = gengoTable[i][0];
		int year =Integer.parseInt(seireki.substring(0,4)) - Integer.parseInt(gengoTable[i][1].substring(0,4)) + 1 ;
		if(year < 10 ){
			wareki = wareki + "0";
		}
		wareki = wareki + Integer.toString(year) + "年" + seireki.substring(4,6) + "月"; 		
		return wareki;		 
	}
	
	
	/**
     * 西暦8桁yyyymmddもしくは西暦10桁yyyy-mm-ddのString引数から
     * “－“を削除した形式に編集してから和暦に返還しString型の和暦を返す。
     * @param  eDate   西暦8桁のStringもしくは“－“を削除したい西暦10桁のString
     *
     * @return 和暦 平成yy年mm月dd日フォーマット
     */
	public String get49Wareki(String eDate)throws Exception{
		StringBuffer sbDate;
		
		if(eDate.length()==10){
			if(eDate.substring(4,5).equals("-")&eDate.substring(7,8).equals("-")){
				sbDate=new StringBuffer(getWareki(edit49Date(eDate)));
			}else{
				sbDate=new StringBuffer("dateError in CifComn");
			}
		}else{
			sbDate=new StringBuffer(getWareki(eDate));
		}
		return sbDate.toString();
	}
	
		
	/**
     * 西暦8桁yyyymmddもしくは西暦10桁yyyy-mm-ddのString引数から
     * “－“を削除した形式に編集してから和暦に返還しString型の和暦を返す。
     * @param  eDate   西暦8桁のStringもしくは“－“を削除したい西暦10桁のString
     *
     * @return 和暦 "yymmdd"フォーマット
     */
	public String getSimpleWareki(String eDate)throws Exception{
		StringBuffer sbDate=new StringBuffer(get49Wareki(eDate));
		sbDate.delete(10,11);
		sbDate.delete(7,8);
		sbDate.delete(4,5);
		sbDate.delete(0,2);
		return sbDate.toString();
	}
	
	
	
	/**
     * 西暦8桁yyyymmddもしくは西暦10桁yyyy-mm-ddのString引数から
     * “－“を削除した形式に編集してから和暦に返還しString型の和暦を返す。
     * @param  eDate   西暦8桁のStringもしくは“－“を削除したい西暦10桁のString
     *
     * @return 和暦 元号"H"or"S"or"T"+yymmdd"フォーマット
     */
	public String getSimpleGengoWareki(String eDate)throws Exception{
		StringBuffer sbDate;
		if(eDate==null){
			sbDate=new StringBuffer("");
		}else{
			sbDate=new StringBuffer(get49Wareki(eDate));
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
				sbDate.delete(0,2);
			}
		}
		return sbDate.toString();
	}
	



	/**
	  * 本日日付取得（YYYYMMDD）
	  */
	public String getToday()
	{
		gSDFDate.setTimeZone(TimeZone.getTimeZone("JST"));
		return gSDFDate.format(new java.util.Date());
	}



	/**
	  * 現在時間取得（HHMMSS）
	  */
	public String getTime()
	{
		gSDFTime.setTimeZone(TimeZone.getTimeZone("JST"));
		return gSDFTime.format(new java.util.Date());
	}




	/**
	  * 月末日の取得
	  * String(yyyymmdd)をセットすると、その日付の属する月の
	  * 月末日をString(yyyymmdd)で返す。
	  */
	public String getLastMonthDate(String inDate)
	{
		TimeZone tz=TimeZone.getTimeZone("JST");
		Calendar cal=new GregorianCalendar(tz);
		int yyyy=Integer.parseInt(inDate.substring(0,4));
		int mm=Integer.parseInt(inDate.substring(4,6));
		int dd=Integer.parseInt(inDate.substring(6));
		
		cal.set(yyyy,mm-1,dd);
		Integer lastDay=new Integer(cal.getActualMaximum(Calendar.DAY_OF_MONTH));
		String lastDate=inDate.substring(0,6);
		lastDate+=lastDay.toString();
		return lastDate;
	}


	/**
	 * ローカルデータの読込み
	 */
	public String CifComonRead(String sFilePath) throws Exception
	{
		String sBuffer = "";
		FileInputStream cFIS;
		InputStreamReader cISR = null;

		cFIS = new FileInputStream(sFilePath);
		//NECIKO	cISR = new InputStreamReader(cFIS,"x-sjis");
		cISR = new InputStreamReader(cFIS, "Windows-31J");

		char[] cBuf = new char[4096];
		int iLen = 0;

		while((iLen = cISR.read(cBuf)) != -1){
			String sWk = new String(cBuf, 0, iLen);
			sBuffer = sBuffer + sWk;
		}

		if(cISR != null){
			cISR.close();
		}

		return sBuffer;
	}



	/** 
	  * 指定されたテンプレートのHtmlファイルを読込み、
	  * <SERVLETLINE>に指定された文字列を差込み結果を戻す。
	  * 引数は（テンプレートのHtmlファイル,差し込みたい文字列）
	  */
	public String CifComonHTMLRead(String htmlFileName,String addHtmlData) 
		throws Exception
	{
		String sFilePath = gsSFilePath + "\\" + htmlFileName;
		String sBuffer = "";
		String sReturn = "";



		sBuffer = "<!--INPUT FILE:" + sFilePath + "-->\n";
		try {
			sBuffer = CifComonRead(sFilePath);
			int iHit = sBuffer.indexOf("SERVLETLINE");
			StringBuffer sbScr = new StringBuffer(sBuffer);
			if(iHit > -1){
				sbScr.insert(iHit + 14,"\n" + addHtmlData);
			}
			sReturn = sbScr.toString();
		}
		catch (Exception e) {
			throw new CifApplicationException("9002-02"+sFilePath);
		/**
			sReturn += "<BODY BGCOLOR='#d0d0d0'>";
			sReturn += "<H1>画面表示ができません<BR>\n";
			sReturn += "<!-- Error : SubMenu File Cannot Read\n";
			sReturn += e.getMessage() + " -->\n";
			sReturn += "<BR>\n";
			sReturn += "<BR>\n";
			sReturn += "<a href="+sFilePath+"/Ciflogin.html>ログインへ</a>\n";
		*/
		}
		return sReturn;
	}
	
	/** 
	  * String引数１のString引数２を検索し、直後にString引数３を
	　* insertしてString型の文字列として返す。
	　*	
	　* @param  baseString insertする元のString
    	　*
		* @param tag 挿入する位置を決定する検索文字列String
		* @param addString 挿入する文字列String
		* @return 挿入後のString
	  */
	public String insertTag(String baseString,String tag,String addString){
		
		int i=baseString.indexOf(tag);
		StringBuffer sb = new StringBuffer(baseString);
		if(i>-1){
			sb.insert(i+tag.length(),"\n"+addString);
		}
		return sb.toString();
	}



	/** 
	  * 半角カナの拗音を半角カナの対応する文字に変換する。
	  * またカナの長音をハイフンに変換する。
	  * String型の変換したい文字列を引数にセットすると
	  * 変換後のString型の文字列をもどす。
	  * 「"ｧ","ｨ","ｩ","ｪ","ｫ","ｬ","ｭ","ｮ","ｯ","ｰ"」
	  */
	public String decodeSmallKana(String argCheckData){
	
		String[][] smallKana = {
			{"ｧ","ｨ","ｩ","ｪ","ｫ","ｬ","ｭ","ｮ","ｯ","ｰ"},
			{"ｱ","ｲ","ｳ","ｴ","ｵ","ﾔ","ﾕ","ﾖ","ﾂ","-"}
		};
		String checkString="";
		checkString=argCheckData;
		int count=0;
		for (;count<smallKana[0].length;count++){
			int index=0;
			while (index!=-1){
				index=checkString.indexOf(smallKana[0][count]);
				
				if (index>-1){
					StringBuffer checkStringBuffer = new StringBuffer(checkString);
					checkStringBuffer.replace(index,index+1,smallKana[1][count]);
					checkString=checkStringBuffer.toString();
				}
				s=s+" in="+index+" co="+count;
			}
		}
		return checkString;
	}
	
	
	/** 
	  * 全角かな文字を半角カナ文字に変換する。
	  * 全角長音、ハイフンを半角に変換する。
	  * String型の変換したい文字列を引数にセット
	  * 変換後のString型の文字列をもどす。
	  */
	public String zenKanamojiHenkan(String argCheckData){
	
		String[][] Kananmoji = {
			{"あ","い","う","え","お","か","き","く","け","こ","さ","し","す","せ","そ","た","ち","つ","て","と","な","に","ぬ","ね","の"
			,"は","ひ","ふ","へ","ほ","ま","み","む","め","も","や","ゆ","よ","ら","り","る","れ","ろ","わ","を","ん"
			,"が","ぎ","ぐ","げ","ご","ざ","じ","ず","ぜ","ぞ","だ","ぢ","づ","で","ど","ば","び","ぶ","べ","ぼ","ぱ","ぴ","ぷ","ぺ","ぽ","ー","－"},
			{"ｱ","ｲ","ｳ","ｴ","ｵ","ｶ","ｷ","ｸ","ｹ","ｺ","ｻ","ｼ","ｽ","ｾ","ｿ","ﾀ","ﾁ","ﾂ","ﾃ","ﾄ","ﾅ","ﾆ","ﾇ","ﾈ","ﾉ"
			,"ﾊ","ﾋ","ﾌ","ﾍ","ﾎ","ﾏ","ﾐ","ﾑ","ﾒ","ﾓ","ﾔ","ﾕ","ﾖ","ﾗ","ﾘ","ﾙ","ﾚ","ﾛ","ﾜ","ｦ","ﾝ"
			,"ｶﾞ","ｷﾞ","ｸﾞ","ｹﾞ","ｺﾞ","ｻﾞ","ｼﾞ","ｽﾞ","ｾﾞ","ｿﾞ","ﾀﾞ","ﾁﾞ","ﾂﾞ","ﾃﾞ","ﾄﾞ","ﾊﾞ","ﾋﾞ","ﾌﾞ","ﾍﾞ","ﾎﾞ","ﾊﾟ","ﾋﾟ","ﾌﾟ","ﾍﾟ","ﾎﾟ","ｰ","-"},
		};
		String checkString="";
		checkString=argCheckData;
		int count=0;
		for (;count<Kananmoji[0].length;count++){
			int index=0;
			while (index!=-1){
				index=checkString.indexOf(Kananmoji[0][count]);
				
				if (index>-1){
					StringBuffer checkStringBuffer = new StringBuffer(checkString);
					checkStringBuffer.replace(index,index+1,Kananmoji[1][count]);
					checkString=checkStringBuffer.toString();
				}
				s=s+" in="+index+" co="+count;
			}
		}
		return checkString;
	}
	
	/** 
	  * 全角カナ文字を半角カナ文字に変換する。
	  * String型の変換したい文字列を引数にセット
	  * 変換後のString型の文字列をもどす。
	  */
	public String zenKataKanamojiHenkan(String argCheckData){
	
		String[][] Kananmoji = {
			{"ア","イ","ウ","エ","オ","カ","キ","ク","ケ","コ","サ","シ","ス","セ","ソ","タ","チ","ツ","テ","ト","ナ","ニ","ヌ","ネ","ノ"
			,"ハ","ヒ","フ","ヘ","ホ","マ","ミ","ム","メ","モ","ヤ","ユ","ヨ","ラ","リ","ル","レ","ロ","ワ","ヲ","ン"
			,"ガ","ギ","グ","ゲ","ゴ","ザ","ジ","ズ","ゼ","ゾ","ダ","ヂ","ヅ","デ","ド","バ","ビ","ブ","ベ","ボ","パ","ピ","プ","ペ","ポ","ー","－"},
			{"ｱ","ｲ","ｳ","ｴ","ｵ","ｶ","ｷ","ｸ","ｹ","ｺ","ｻ","ｼ","ｽ","ｾ","ｿ","ﾀ","ﾁ","ﾂ","ﾃ","ﾄ","ﾅ","ﾆ","ﾇ","ﾈ","ﾉ"
			,"ﾊ","ﾋ","ﾌ","ﾍ","ﾎ","ﾏ","ﾐ","ﾑ","ﾒ","ﾓ","ﾔ","ﾕ","ﾖ","ﾗ","ﾘ","ﾙ","ﾚ","ﾛ","ﾜ","ｦ","ﾝ"
			,"ｶﾞ","ｷﾞ","ｸﾞ","ｹﾞ","ｺﾞ","ｻﾞ","ｼﾞ","ｽﾞ","ｾﾞ","ｿﾞ","ﾀﾞ","ﾁﾞ","ﾂﾞ","ﾃﾞ","ﾄﾞ","ﾊﾞ","ﾋﾞ","ﾌﾞ","ﾍﾞ","ﾎﾞ","ﾊﾟ","ﾋﾟ","ﾌﾟ","ﾍﾟ","ﾎﾟ","ｰ","-"},
		};
		String checkString="";
		checkString=argCheckData;
		int count=0;
		for (;count<Kananmoji[0].length;count++){
			int index=0;
			while (index!=-1){
				index=checkString.indexOf(Kananmoji[0][count]);
				
				if (index>-1){
					StringBuffer checkStringBuffer = new StringBuffer(checkString);
					checkStringBuffer.replace(index,index+1,Kananmoji[1][count]);
					checkString=checkStringBuffer.toString();
				}
				s=s+" in="+index+" co="+count;
			}
		}
		return checkString;
	}
	
	
	/** 
	  * 半角カナ文字を全角カナ文字に変換する。
	  * String型の変換したい文字列を引数にセット
	  * 変換後のString型の文字列をもどす。
	  */
	public String zenkakumokiHenkan(String argCheckData){
	
		String[][] Kananmoji = {
			{"ｱ","ｲ","ｳ","ｴ","ｵ","ｶ","ｷ","ｸ","ｹ","ｺ","ｻ","ｼ","ｽ","ｾ","ｿ","ﾀ","ﾁ","ﾂ","ﾃ","ﾄ","ﾅ","ﾆ","ﾇ","ﾈ","ﾉ"
			,"ﾊ","ﾋ","ﾌ","ﾍ","ﾎ","ﾏ","ﾐ","ﾑ","ﾒ","ﾓ","ﾔ","ﾕ","ﾖ","ﾗ","ﾘ","ﾙ","ﾚ","ﾛ","ﾜ","ｦ","ﾝ"},
			{"ア","イ","ウ","エ","オ","カ","キ","ク","ケ","コ","サ","シ","ス","セ","ソ","タ","チ","ツ","テ","ト","ナ","ニ","ヌ","ネ","ノ"
			,"ハ","ヒ","フ","ヘ","ホ","マ","ミ","ム","メ","モ","ヤ","ユ","ヨ","ラ","リ","ル","レ","ロ","ワ","ヲ","ン"},
		};
		String checkString="";
		checkString=argCheckData;
		int count=0;
		for (;count<Kananmoji[0].length;count++){
			int index=0;
			while (index!=-1){
				index=checkString.indexOf(Kananmoji[0][count]);
				
				if (index>-1){
					StringBuffer checkStringBuffer = new StringBuffer(checkString);
					checkStringBuffer.replace(index,index+1,Kananmoji[1][count]);
					checkString=checkStringBuffer.toString();
				}
				s=s+" in="+index+" co="+count;
			}
		}
		return checkString;
	}
	
	
	/** 
	  * 全角平仮名の小文字を半角カナ大文字文字に変換する。
	  * String型の変換したい文字列を引数にセットすると
	  * 変換後のString型の文字列をもどす。
	  */
	public String decodeSmallzenKana(String argCheckData){
	
		String[][] smallzenKana = {
			{"ぁ","ぃ","ぅ","ぇ","ぉ","ゃ","ゅ","ょ","っ"},
			{"ｱ","ｲ","ｳ","ｴ","ｵ","ﾔ","ﾕ","ﾖ","ﾂ"}
		};
		String checkString="";
		checkString=argCheckData;
		int count=0;
		for (;count<smallzenKana[0].length;count++){
			int index=0;
			while (index!=-1){
				index=checkString.indexOf(smallzenKana[0][count]);
				
				if (index>-1){
					StringBuffer checkStringBuffer = new StringBuffer(checkString);
					checkStringBuffer.replace(index,index+1,smallzenKana[1][count]);
					checkString=checkStringBuffer.toString();
				}
				s=s+" in="+index+" co="+count;
			}
		}
		return checkString;
	}
	

	/** 
	  * 全角カナの小文字を半角カナ大文字文字に変換する。
	  * String型の変換したい文字列を引数にセットすると
	  * 変換後のString型の文字列をもどす。
	  */
	public String decodeSmallkatakana(String argCheckData){
	
		String[][] smallzenKana = {
			{"ァ","ィ","ゥ","ェ","ォ","ャ","ュ","ョ","ッ"},
			{"ｱ","ｲ","ｳ","ｴ","ｵ","ﾔ","ﾕ","ﾖ","ﾂ"}
		};
		String checkString="";
		checkString=argCheckData;
		int count=0;
		for (;count<smallzenKana[0].length;count++){
			int index=0;
			while (index!=-1){
				index=checkString.indexOf(smallzenKana[0][count]);
				
				if (index>-1){
					StringBuffer checkStringBuffer = new StringBuffer(checkString);
					checkStringBuffer.replace(index,index+1,smallzenKana[1][count]);
					checkString=checkStringBuffer.toString();
				}
				s=s+" in="+index+" co="+count;
			}
		}
		return checkString;
	}	
	
	
	
	/** 
	  * 全角小文字のアルファベット文字を全角大文字のアルファベット文字に変換する。
	  * String型の変換したい文字列を引数にセットすると
	  * 変換後のString型の文字列をもどす。
	  */
	public String alphabetZenHenkan(String argCheckData){
	
		String[][] alphabet = {
			{"ａ","ｂ","ｃ","ｄ","ｅ","ｆ","ｇ","ｈ","ｉ","ｊ","ｋ","ｌ","ｍ","ｎ","ｏ","ｐ","ｑ","ｒ","ｓ","ｔ","ｕ","ｖ","ｗ","ｘ","ｙ","ｚ"},
			{"Ａ","Ｂ","Ｃ","Ｄ","Ｅ","Ｆ","Ｇ","Ｈ","Ｉ","Ｊ","Ｋ","Ｌ","Ｍ","Ｎ","Ｏ","Ｐ","Ｑ","Ｒ","Ｓ","Ｔ","Ｕ","Ｖ","Ｗ","Ｘ","Ｙ","Ｚ"},
		};
		String checkString="";
		checkString=argCheckData;
		int count=0;
		for (;count<alphabet[0].length;count++){
			int index=0;
			while (index!=-1){
				index=checkString.indexOf(alphabet[0][count]);
				
				if (index>-1){
					StringBuffer checkStringBuffer = new StringBuffer(checkString);
					checkStringBuffer.replace(index,index+1,alphabet[1][count]);
					checkString=checkStringBuffer.toString();
				}
				s=s+" in="+index+" co="+count;
			}
		}
		return checkString;
	}	
	
	
	
	
	
	
	
	


	/** 
	  * 全角文字中の半角"?"を全角"－"に変換する。
	  */
	public String decodeLongMinus(String argCheckData){
		String checkString;
		try{
			checkString=new String(argCheckData.getBytes());
		}
		catch(Exception e){
			checkString=argCheckData;
		}
		String q="－";
		while (checkString.indexOf("?")!=-1){
			int index=checkString.indexOf("?");
			StringBuffer checkStringBuffer = new StringBuffer(checkString);
			checkStringBuffer.replace(index,index+1,q);
			giCnt=index;
			checkString=checkStringBuffer.toString();
		}
		return checkString;
	}


	/** 
	  * Stringの引数の改行文字を２バイトの空白文字１文字に返還し、
	　* String型の文字列として返す。
	　*	
	　* @param  input   改行文字を削除したいString
      *
      * @return String型の文字列
	  */
	public String editNewLine(String input){
		String s=input;
		while(s.indexOf("\r\n")!=-1){
			int index=s.indexOf("\r\n");
			StringBuffer sb=new StringBuffer(s);
			sb.replace(index,index+2,"　");
			s=sb.toString();
		}
		return s;
	 }

	/** 
	  * long引数を３桁ごとのカンマを付与した形式に編集し、
	　* String型の文字列として返す。
	　*	
	　* @param  kingaku   カンマを付与したいlong
   	　*
   	　* @return ３桁ごとのカンマを付与した形式のString
	  */
	public String editKanma(long kingaku){

		return NumberFormat.getInstance().format(kingaku);
	 }

	/** 
	  * int引数を３桁ごとのカンマを付与した形式に編集し、
	　* String型の文字列として返す。
	　*	
	　* @param  kingaku   カンマを付与したいint
     	　*
     	　* @return ３桁ごとのカンマを付与した形式のString
	  */
	public String editKanma(int kingaku){

		return NumberFormat.getInstance().format(kingaku);
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
	public String editKanma(String kingaku)throws Exception{

		String editKingaku = kingaku;

		//先頭１文字目が数字以外の場合、最後に付加する処理
		String fugou  ="";
		try{
			int top =  Integer.parseInt(editKingaku.substring(0,1));
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
				int top =  Integer.parseInt(editKingaku.substring(startPoint,endPoint));
			}
			catch(NumberFormatException nfe){
				throw new CifApplicationException("9000-02"+nfe.toString());
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
	* String引数に、下記の通りにハイフンを付与した形式に編集し、
	* String型の文字列として返す。
	*	引数が１０桁　→　携帯電話：０９０ＸＸＸＸ－ＸＸＸＸ	
	*	引数が９桁　　→　固定電話：　ＸＸＸＸＸＸーＸＸＸＸ
	*	引数の先頭がゼロ　→　空白
	* @param  telphone   ハイフンを付与したいString
     	*
     	* @return ３桁ごとのカンマを付与した形式のString
	*/
	public String editTelphone(String telphone){

		String editTel = "";
		//M,Aoki 2008-11-25 エラー対応
		if(telphone == null) {
			return editTel;
		}
		if(telphone.substring(0,1) != "0"){
			switch (telphone.length() ){
				case 10:
					telphone = "0" + telphone;
					editTel = telphone.substring(0,7) + "-" + telphone.substring(7,11);
					break;
				case 9:
					telphone = "0" + telphone;
					editTel = telphone.substring(0,6) + "-" + telphone.substring(6,10);
					break;
			}
		}
		return  editTel;
	}

	/** 
	* int引数に、下記の通りにハイフンを付与した形式に編集し、
	* int型の文字列として返す。
	*	引数が１０桁　→　携帯電話使用不可（int型の桁が足りない為）	
	*	引数が９桁　　→　固定電話：　ＸＸＸＸＸＸーＸＸＸＸ
	*	引数の先頭がゼロ　→　空白
	* @param  telphone   ハイフンを付与したいint
     	*
     	* @return ３桁ごとのカンマを付与した形式のString
	*/
	public String editTelphone(int telphone){
		
		return editTelphone(Integer.toString(telphone));
	}

    /**
     * 西暦８桁又は和暦６桁のString引数を“－“を付与した形式に編集し
     * String型の文字列として返す。
     * @param  eDate   “－“を付与したいString
     *
     * @return “－“を付与した形式のString
     */
	public String editDate(String eDate){
		if(eDate.length() == 8){
			String dateString="";
			StringBuffer dateStringBuffer = new StringBuffer(eDate);
			dateStringBuffer.insert(4,"-");
			dateStringBuffer.insert(7,"-");
			dateString = dateStringBuffer.toString();
			return dateString;
		}
		else if(eDate.length() == 6){
			String dateString="";
			StringBuffer dateStringBuffer = new StringBuffer(eDate);
			dateStringBuffer.insert(2,"-");
			dateStringBuffer.insert(5,"-");
			dateString = dateStringBuffer.toString();
			return dateString;
		}
		else{
			return eDate;
		}
	}
	
	
	
	/**
     * 西暦10桁yyyy-mm-ddのString引数から“－“を削除した形式に編集し
     * String型の文字列として返す。
     * @param  eDate   “－“を削除したいString
     *
     * @return “－“を削除した形式のString
     */
	public String edit49Date(String eDate){
		StringBuffer sbDate=new StringBuffer(eDate);
		sbDate.delete(7,8);
		sbDate.delete(4,5);
		return sbDate.toString();
	}
	
	
	
    /**
     * ６桁のString引数を２桁ごとに“：“を付与した形式に編集し
     * String型の文字列として返す。
     * @param  eTime   “：“を付与したいString
     *
     * @return “：“を付与した形式のString
     */
	public String editTime(String eTime){
		if(eTime.length() == 6){
			String timeString ="";
			StringBuffer timeStringBuffer = new StringBuffer(eTime);
			timeStringBuffer.insert(2,":");
			timeStringBuffer.insert(5,":");
			timeString = timeStringBuffer.toString();
			return timeString;
		}
		else{
			return eTime;
		}
	}

    /**
     * データベースの検索結果をHTTPクライアント(Webブラウザ)
     * に出力する。
     *
     * @param  rs   データベースの検索結果（ResultSet型の変数名）
     * @param  out  検索結果の出力先（PrintWriter型の変数名）
     *
     * @return なし
     */

    public void display(ResultSet rs, PrintWriter out) {

        try {
            // ResultSetオブジェクトがnullでなければ、検索結果を表示する
            if (rs != null) {
                out.println(
                    "<h2>サーブレットによるサンプルデータベースの検索結果</h2>"
                );
                out.println("<table border>");
                out.print("<tr>");
                // 検索結果1行のカラム(列)数を取得する
                ResultSetMetaData rsmd = rs.getMetaData();
                int    columns = rsmd.getColumnCount();
                // 検索結果の各カラム(列)名称を表示する
                for(int i = 1; i <= columns; i++)   {
                    out.print("<th>" + rsmd.getColumnName(i) + "</th>");
                }
                out.println("</tr>");
                // 検索結果の各カラム(列)タイプを表示する
                for(int i = 1; i <= columns; i++)   {
                    out.print("<th>" + rsmd.getColumnTypeName(i) + "</th>");
                }
                out.println("</tr>");
                // 検索結果が1行以上存在する場合は、それを表示する。
                if (rs.next()) {
                    // 検索結果の行数を初期化する
                    int row = 0;
                    // 検索結果の行数分だけ以下を繰り返す
                    do  {
                        out.print("<tr>");
                        // 検索結果1行分のデータを表示する
                        for(int i = 1; i <= columns; i++)   {
                            // 検索結果のi番目のカラムの内容を取得する
                            String data = rs.getString(i);
                            // 検索結果がNULLだった場合は"--NULL--"に変換する
                            if ( data == null ) data = "<b>--NULL--</b>";
                            // 検索結果を表示する
                            out.print("<td>" + data + "</td>");
                        }
                        out.println("</tr>");
                        // 検索結果の行数を1ずつカウントアップする
                        row++;
                    } while(rs.next());
                    out.println("</table>");
                    // 検索結果の行数を表示する
                    out.println(row + "件のデータが見つかりました。");
                } else {
                    out.println("</table>");
                    // 検索結果が1行も無い場合はメッセージを表示して終了する
                    out.println(
                        "検索条件に適合するデータは見つかりませんでした。"
                    );
                }
            }
        } catch(SQLException ex) {

            // データベースへのアクセス時にエラーが発生した場合は
            // エラーメッセージを表示する
            out.println(ex.getMessage());
            out.println("</tr></table>");
        }
    }	

	/** 
	　* 引数７桁　元号表示"H"or"S"or"T" + 和暦ＹＹＭＭＤＤとみなし、西暦ＹＹＹＹＭＭＤＤで返す。
	  * 引数６桁　和暦ＹＹＭＭＤＤとみなし、西暦ＹＹＹＹＭＭＤＤで返す。
	　* 　　　　　　ただし、指定の年月日が存在していれば、"PARAMERR"を返す。
	　* 引数４桁　和暦ＹＹＭＭとみなし、西暦ＹＹＹＹＭＭで返す。
	　* 引数２桁　和暦ＹＹとみなし、西暦ＹＹＹＹで返す。
     	　* 以外　　、"PARAMERR"を返す。
	  *
	  * @param  wareki  和暦日付（String型）
	  *
	  */

	public String getSeireki(String wareki)throws Exception{


		String seirekiDate = "";

		String gengo="";
		String warekiYear = "";
		String warekiMonth = "";
		String warekiDay = "";

		int seirekiYear;
		int seirekiMonth;
		int seirekiDay;

		
		if(wareki.length() == 7){
			gengo       =wareki.substring(0,1);
			warekiYear  =wareki.substring(1,3);
			warekiMonth =wareki.substring(3,5);
			warekiDay   =wareki.substring(5,7);
			if(gengo.equals("H")){
				seirekiYear = 1988 + Integer.parseInt(warekiYear);
			}else if(gengo.equals("S")){
				seirekiYear = 1925 + Integer.parseInt(warekiYear);
			}else if(gengo.equals("T")){
				seirekiYear = 1911 + Integer.parseInt(warekiYear);
			}else if(gengo.equals("M")){
				seirekiYear = 1867 + Integer.parseInt(warekiYear);
			}else{
				seirekiYear = 1988 + Integer.parseInt(warekiYear);
			}
			seirekiDate = Integer.toString(seirekiYear) + warekiMonth + warekiDay;
			seirekiMonth = Integer.parseInt(warekiMonth) ;
			seirekiDay = Integer.parseInt(warekiDay);
		}else{
			//ニューメリックＣＨＥＣＫ
			try{
				int wk =  Integer.parseInt(wareki);
			}
			catch(NumberFormatException nfe){
				throw new CifApplicationException("9000-02"+nfe.toString());
			}
			if(wareki.length() == 6){
				warekiYear = wareki.substring(0,2);
				warekiMonth = wareki.substring(2,4);
				warekiDay = wareki.substring(4,6);

				seirekiYear = 1988 + Integer.parseInt(warekiYear);
				seirekiDate = Integer.toString(seirekiYear) + warekiMonth + warekiDay;
				seirekiMonth = Integer.parseInt(warekiMonth) ;
				seirekiDay = Integer.parseInt(warekiDay);
			}
			else if(wareki.length() == 4){
				warekiYear = wareki.substring(0,2);
				warekiMonth = wareki.substring(2,4);

				seirekiYear = 1988 + Integer.parseInt(warekiYear);
				seirekiDate = Integer.toString(seirekiYear) + warekiMonth;
				seirekiMonth = Integer.parseInt(warekiMonth) ;
				seirekiDay = 10;//平成１年１月１日は存在しない為「１０」セット
			}
			else if(wareki.length() == 2){
				warekiYear = wareki.substring(0,2);

				seirekiYear = 1988 + Integer.parseInt(warekiYear);
				seirekiDate = Integer.toString(seirekiYear);
				seirekiMonth = 1;
				seirekiDay = 10;//平成１年１月１日は存在しない為「１０」セット
			}
			else{
				return "PARAMERR";
			}
			
		}

		//存在する暦上日なら、trueを返す。存在しない暦上日なら、falseを返す。
		boolean check = checkDate(seirekiYear,seirekiMonth,seirekiDay);
		if(check == false){
			return "PARAMERR";
		}
		return seirekiDate ;
	}


	/** 
	　* 指定の西暦年月日が存在するなら、trueを返す。
	　* 指定の西暦年月日が存在しなければ、falseを返す。
	　* 引数が４桁以下なら、falseを返す。
	　* 
	  * @param  seireki  西暦日付（int型）
	  */
	public boolean checkDate(int seireki ){

		return checkDate(Integer.toString(seireki));

	}
	/** 
	　* 指定の西暦年月日が存在するなら、trueを返す。
	　* 指定の西暦年月日が存在しなければ、falseを返す。
	　* 引数が４桁以下なら、falseを返す。
	　* 
	  * @param  seireki  西暦日付（String型）
	  */
	public boolean checkDate(String seireki ){

		if(seireki.length() < 5){
			return false;
		} 

		String year = seireki.substring(0,seireki.length() - 4 );
		String month = seireki.substring(seireki.length() - 4,seireki.length() - 2 );
		String day = seireki.substring(seireki.length() - 2,seireki.length() );
		return checkDate(Integer.parseInt(year),Integer.parseInt(month),Integer.parseInt(day));
	}


	/** 
	　* 指定の西暦年月日が存在するなら、trueを返す。
	　* 指定の西暦年月日が存在しなければ、falseを返す。
	　* 
	  * @param  year   西暦年（String型）
	  * @param  month  西暦月（String型）
	  * @param  day    西暦日（String型）
	  */
	public boolean checkDate(String year,String month,String day ){

		return checkDate(Integer.parseInt(year),Integer.parseInt(month),Integer.parseInt(day));
	}

	/** 
	　* 指定の西暦年月日が存在するなら、trueを返す。
	　* 指定の西暦年月日が存在しなければ、falseを返す。
	　* 
	  * @param  year   西暦年（int型）
	  * @param  month  西暦月（int型）
	  * @param  day    西暦日（int型）
	  */

	public boolean checkDate(int year,int month,int day ){

		boolean check = true;
		//日付/時刻の解釈を厳密に行う設定にする
		cal.setLenient( false );
		//年、月、日付のフィールドに値を設定（Month 値は 0 から始まる。つまり、0 は 1 月）
		cal.set(year, month -1, day);
	  
		try {
			//Calendar の現在時刻を取得
			java.util.Date ud = cal.getTime();

			//不正な引数、または不適切な引数をメソッドに渡したことを示すためにスローされます
		} catch (IllegalArgumentException iae) {
			check = false;
		}
		return check;
	}
	
	
	
	/** 
	　* 指定の和暦年月日が存在するなら、trueを返す。
	　* 指定の和暦年月日が存在しなければ、falseを返す。
	　* 引数が６桁ならyymmdd、７桁なら"H"or"S"or"T" + 和暦yymmdd。
	　* 
	  * @param  wareki  和暦日付（String型）
	  */
	public boolean checkWarekiDate(String wareki)throws Exception{

		boolean status=false;
		String date;
		if(wareki.length()==6){
			date=new String(wareki);
		}else if(wareki.length()==7){
			String gengo=new String(wareki.substring(0,1));
			if(gengo.equals("H")|gengo.equals("S")|gengo.equals("T")|gengo.equals("M")){
				date=new String(wareki.substring(1,7));
			}else{
				return status;
			}
		}else{
			return status;
		}
		try{
			int wk=Integer.parseInt(date);
		}
		catch(NumberFormatException nfe){
			return status;
		}
		if(!getSeireki(wareki).equals("PARAMERR")){
			status=true;
		}
		return status;
	}

	
	

	
	/** 
	　* ２つの指定された西暦年月日の差日数を求め、int型で返す。
	　* 指定の西暦年月日が存在しなければ、CifApplicationExceptionにthrow する。
	　* 
	  * @param  startYear   開始西暦年（int型）
	  * @param  startMonth  開始西暦月（int型）
	  * @param  startDay    開始西暦日（int型）
	  * @param  endYear     終了西暦年（int型）
	  * @param  endMonth    終了西暦月（int型）
	  * @param  endDay      終了西暦日（int型）
	  */

	public int getSanissu(int startYear,int startMonth,int startDay,int endYear,int endMonth,int endDay)throws Exception {
		
		boolean check = true;
		check = checkDate( startYear, startMonth, startDay);
		if(check ==false){
			throw new CifApplicationException("1008-02:"+Integer.toString(startYear)+Integer.toString(startMonth)+Integer.toString(startDay));
		}
		check = checkDate( endYear, endMonth, endDay);
		if(check ==false){
			throw new CifApplicationException("1008-02:"+Integer.toString(endYear)+Integer.toString(endMonth)+Integer.toString(endDay));
		}
		
		cal.clear();
		cal.set(startYear, startMonth - 1, startDay);    /* 年月日をセット */
		long startTime= (cal.getTime()).getTime();  /* ミリ秒数取り出し */
	
		cal.clear();
		cal.set( endYear, endMonth - 1, endDay);    /* 年月日をセット */
		long endTime  = (cal.getTime()).getTime();  /* ミリ秒数取り出し */

		long nissu = (endTime - startTime)/(1000*60*60*24);

		return (int)nissu;
		
	}	
	/** 
	　* ２つの指定された西暦年月日の差日数を求め、int型で返す。
	　* 指定の西暦年月日が存在しなければ、CifApplicationExceptionにthrow する。
	　* 
	  * @param  startYear   開始西暦年（String型）
	  * @param  startMonth  開始西暦月（String型）
	  * @param  startDay    開始西暦日（String型）
	  * @param  endYear     終了西暦年（String型）
	  * @param  endMonth    終了西暦月（String型）
	  * @param  endDay      終了西暦日（String型）
	  */

	public int getSanissu(String startYear,String startMonth,String startDay,String endYear,String endMonth,String endDay)throws Exception {

		//ニューメリックＣＨＥＣＫ
		try{
			int wk =  Integer.parseInt(startYear);
			wk =  Integer.parseInt(startMonth);
			wk =  Integer.parseInt(startDay);
		}
		catch(NumberFormatException nfe){
			throw new CifApplicationException("1008-02:" + startYear + startMonth + startDay);
		}

		//ニューメリックＣＨＥＣＫ
		try{
			int wk =  Integer.parseInt(endYear);
			wk =  Integer.parseInt(endMonth);
			wk =  Integer.parseInt(endDay);
		}
		catch(NumberFormatException nfe){
			throw new CifApplicationException("1008-02:" + endYear + endMonth + endDay);
		}

		return getSanissu(Integer.parseInt(startYear),Integer.parseInt(startMonth),Integer.parseInt(startDay),Integer.parseInt(endYear),Integer.parseInt(endMonth),Integer.parseInt(endDay));
	}

	/** 
	　* ２つの指定された西暦年月日の差日数を求め、int型で返す。
	　* 指定の西暦年月日が存在しなければ、CifApplicationExceptionにthrow する。
	　* 
	  * @param  startDate   開始西暦年月日（String型）
	  * @param  endDate     終了西暦年月日（String型）
	  */

	public int getSanissu(String startDate,String endDate)throws Exception {
		
		if(startDate.length() != 8){
			throw new CifApplicationException("1008-02:"+startDate);
		} 

		if(endDate.length() != 8){
			throw new CifApplicationException("1008-02:"+endDate);
		} 

		String startYear = startDate.substring(0,startDate.length() - 4 );
		String startMonth = startDate.substring(startDate.length() - 4,startDate.length() - 2 );
		String startDay = startDate.substring(startDate.length() - 2,startDate.length() );
		String endYear = endDate.substring(0,endDate.length() - 4 );
		String endMonth = endDate.substring(endDate.length() - 4,endDate.length() - 2 );
		String endDay = endDate.substring(endDate.length() - 2,endDate.length() );
		
		return getSanissu(startYear,startMonth,startDay,endYear,endMonth,endDay);
		
	}

	/** 
	　* ２つの指定された西暦年月日の差日数を求め、int型で返す。
	　* 指定の西暦年月日が存在しなければ、CifApplicationExceptionにthrow する。
	　* 
	  * @param  startDate   開始西暦年月日（int型）
	  * @param  endDate     終了西暦年月日（int型）
	  */

	public int getSanissu(int startDate,int endDate)throws Exception {
		
		String startDate8keta = Integer.toString(startDate);
		while (startDate8keta.length() < 8){
			startDate8keta = "0"+ startDate8keta;
		}
		String endDate8keta = Integer.toString(endDate);
		while (endDate8keta.length() < 8){
			endDate8keta = "0"+ endDate8keta;
		}
		
		return getSanissu(startDate8keta,endDate8keta);
		
	}
	
	
	/** 
	　* ２つの指定された西暦年月日の差年数を求め、int型で返す。
	　* 指定の西暦年月日が存在しなければ、CifApplicationExceptionにthrow する。
	　* 以下の場合、CifApplicationExceptionにthrow する。
	　*		①引数が暦上日でなければ、エラー画面出力
	　*		②引数の開始日付　＞　引数の終了日付　ならエラー画面出力
	　* 	　* 
	  * @param  startDate   開始西暦年月日（int型）
	  * @param  endDate     終了西暦年月日（int型）
	  */

	public int getAge(int startDate,int endDate)throws Exception {
		
		String startDate8keta = Integer.toString(startDate);
		while (startDate8keta.length() < 8){
			startDate8keta = "0"+ startDate8keta;
		}
		String endDate8keta = Integer.toString(endDate);
		while (endDate8keta.length() < 8){
			endDate8keta = "0"+ endDate8keta;
		}
		
		return getAge(startDate8keta,endDate8keta);
		
	}
		/** 
	　* ２つの指定された西暦年月日の差年数を求め、int型で返す。
	　* 以下の場合、CifApplicationExceptionにthrow する。
	　*		①引数が８桁でなければ、エラー画面出力
	　*		②引数がニューメリックでなければ、エラー画面出力
	　*		③引数が暦上日でなければ、エラー画面出力
	　*		④引数の開始日付　＞　引数の終了日付　ならエラー画面出力
	　*  
	  * @param  startDate   開始西暦年月日（String型）
	  * @param  endDate     終了西暦年月日（String型）
	  */

	public int getAge(String startDate,String endDate)throws Exception {
		
		if(startDate.length() != 8){
			throw new CifApplicationException("1008-02:"+startDate);
		} 

		if(endDate.length() != 8){
			throw new CifApplicationException("1008-02:"+endDate);
		} 

		String startYear = startDate.substring(0,startDate.length() - 4 );
		String startMonth = startDate.substring(startDate.length() - 4,startDate.length() - 2 );
		String startDay = startDate.substring(startDate.length() - 2,startDate.length() );
		String endYear = endDate.substring(0,endDate.length() - 4 );
		String endMonth = endDate.substring(endDate.length() - 4,endDate.length() - 2 );
		String endDay = endDate.substring(endDate.length() - 2,endDate.length() );
		
		return getAge(startYear,startMonth,startDay,endYear,endMonth,endDay);
		
	}
	
	/** 
	　* ２つの指定された西暦年月日の差年数を求め、int型で返す。
	　* 以下の場合、CifApplicationExceptionにthrow する。
	　*		①引数がニューメリックでなければ、エラー画面出力
	　*		②引数が暦上日でなければ、エラー画面出力
	　*		③引数の開始日付　＞　引数の終了日付　ならエラー画面出力
	　* 
	  * @param  startYear   開始西暦年（String型）
	  * @param  startMonth  開始西暦月（String型）
	  * @param  startDay    開始西暦日（String型）
	  * @param  endYear     終了西暦年（String型）
	  * @param  endMonth    終了西暦月（String型）
	  * @param  endDay      終了西暦日（String型）
	  */

	public int getAge(String startYear,String startMonth,String startDay,String endYear,String endMonth,String endDay)throws Exception {

		//ニューメリックＣＨＥＣＫ
		try{
			int wk =  Integer.parseInt(startYear);
			wk =  Integer.parseInt(startMonth);
			wk =  Integer.parseInt(startDay);
		}
		catch(NumberFormatException nfe){
			throw new CifApplicationException("1008-02:" + startYear + startMonth + startDay);
		}

		//ニューメリックＣＨＥＣＫ
		try{
			int wk =  Integer.parseInt(endYear);
			wk =  Integer.parseInt(endMonth);
			wk =  Integer.parseInt(endDay);
		}
		catch(NumberFormatException nfe){
			throw new CifApplicationException("1008-02:" + endYear + endMonth + endDay);
		}

		return getAge(Integer.parseInt(startYear),Integer.parseInt(startMonth),Integer.parseInt(startDay),Integer.parseInt(endYear),Integer.parseInt(endMonth),Integer.parseInt(endDay));
	}
	
	/** 
	　* ２つの指定された西暦年月日の差年数を求め、int型で返す。
	　* 以下の場合、CifApplicationExceptionにthrow する。
	　*		①引数が８桁でなければ、エラー画面出力
	　*		②引数がニューメリックでなければ、エラー画面出力
	　*		③引数が暦上日でなければ、エラー画面出力
	　*		④引数の開始日付　＞　引数の終了日付　ならエラー画面出力
	　* 
	  * @param  startYear   開始西暦年（int型）
	  * @param  startMonth  開始西暦月（int型）
	  * @param  startDay    開始西暦日（int型）
	  * @param  endYear     終了西暦年（int型）
	  * @param  endMonth    終了西暦月（int型）
	  * @param  endDay      終了西暦日（int型）
	  */

	public int getAge(int startYear,int startMonth,int startDay,int endYear,int endMonth,int endDay)throws Exception {
		
		
		String startYear8keta = Integer.toString(startYear);
		while (startYear8keta.length() < 4){
			startYear8keta = "0"+ startYear8keta;
		}
		String startMonth8keta = Integer.toString(startMonth);
		while (startMonth8keta.length() < 2){
			startMonth8keta = "0"+ startMonth8keta;
		}
		String startDay8keta = Integer.toString(startDay);
		while (startDay8keta.length() < 2){
			startDay8keta = "0"+ startDay8keta;
		}
		String endYear8keta = Integer.toString(endYear);
		while (endYear8keta.length() < 4){
			endYear8keta = "0"+ endYear8keta;
		}
		String endMonth8keta = Integer.toString(endMonth);
		while (endMonth8keta.length() < 2){
			endMonth8keta = "0"+ endMonth8keta;
		}
		String endDay8keta = Integer.toString(endDay);
		while (endDay8keta.length() < 2){
			endDay8keta = "0"+ endDay8keta;
		}
		
		boolean check = true;
		check = checkDate( startYear, startMonth, startDay);
		if(check ==false){
			throw new CifApplicationException("1008-02:"+startYear8keta + startMonth8keta + startDay8keta);
		}
		check = checkDate( endYear, endMonth, endDay);
		if(check ==false){
			throw new CifApplicationException("1008-02:"+ endYear8keta + endMonth8keta + endDay8keta);
		}
		
				
		if(endYear < startYear){
			throw new CifApplicationException("1000-02"+":日付（自）より大きな日付を日付（至）に入力して下さい。（自）" + startYear8keta + startMonth8keta + startDay8keta + "（至）" + endYear8keta + endMonth8keta + endDay8keta);
		} else if(startYear == endYear){
			if(endMonth < startMonth){
			throw new CifApplicationException("1000-02"+":日付（自）より大きな日付を日付（至）に入力して下さい。（自）" + startYear8keta + startMonth8keta + startDay8keta + "（至）" + endYear8keta + endMonth8keta + endDay8keta);
			} else if(endMonth == startMonth){
				if(endDay < startDay){
					throw new CifApplicationException("1000-02"+":日付（自）より大きな日付を日付（至）に入力して下さい。（自）" + startYear8keta + startMonth8keta + startDay8keta + "（至）" + endYear8keta + endMonth8keta + endDay8keta);
				}
			}
		}
			
		int age = endYear - startYear ;
		
		if(endMonth < startMonth){
			age-- ;
		} else if(endMonth == startMonth){
			if(endDay < startDay){
					age-- ;
			}
		}
		
		return age;
		
	}
	
	
	/** 
	　* 指定の西暦年月日が営業日なら、trueを返す。
	　* 指定の西暦年月日が非営業日または存在しなければ、falseを返す。
	　* 以下の場合、CifApplicationExceptionにthrow する。
	　*		①引数が８桁でなければ、エラー画面出力
	　*		②引数がニューメリックでなければ、エラー画面出力
	　* 
	  * @param  seireki   西暦年月日（int 型）
	  */

	public boolean checkEigyobi(int seireki )throws Exception {
		
		return checkEigyobi(Integer.toString(seireki));
	}
	
	/** 
	　* 指定の西暦年月日が営業日なら、trueを返す。
	　* 指定の西暦年月日が非営業日または存在しなければ、falseを返す。
	　* 以下の場合、CifApplicationExceptionにthrow する。
	　*		①引数が８桁でなければ、エラー画面出力
	　*		②引数がニューメリックでなければ、エラー画面出力
	　* 
	  * @param  seireki   西暦年月日（String 型）
	  */

	public boolean checkEigyobi(String seireki )throws Exception {

		if(seireki.length() != 8){
			throw new CifApplicationException("1008-02:"+ seireki);
		}
		//ニューメリックＣＨＥＣＫ
		try {
			int wk =  Integer.parseInt(seireki);
		}
		catch(NumberFormatException nfe){
			throw new CifApplicationException("1008-02:" + seireki);
		}
		
		//暦上日チェック		
		if(!checkDate( seireki )){
			throw new CifApplicationException("1008-02:" + seireki);
		}
		
		//土・日以外の祝日チェック
		if(RqsDbSearch.checkHoliday( seireki)){
			return false;
		}
		
		int year = Integer.parseInt(seireki.substring(0,seireki.length() - 4 ));
		int month = Integer.parseInt(seireki.substring(seireki.length() - 4,seireki.length() - 2 ));
		int day = Integer.parseInt(seireki.substring(seireki.length() - 2,seireki.length() ));

		//日付/時刻の解釈を厳密に行う設定にする
		cal.setLenient( false );
		//年、月、日付のフィールドに値を設定（Month 値は 0 から始まる。つまり、0 は 1 月）
		cal.set(year, month -1, day);
	  
		int youbi= cal.get(Calendar.DAY_OF_WEEK);  /* 曜日ＧＥＴ */
		
		if(youbi == 1 || youbi == 7){
			return false;	
		}
		
		return true;
	}
	
	
	/** 
	　* 指定された西暦年月日のＸ日前またはＸ日後をString 型で返す。
	　* Ｘ日前を求めるには、第２引数に負の数
	　* Ｘ日後を求めるには、第２引数に正の数をセットする
	　* ( 第２引数に "0" をセットすると、第１引数をそのまま返す）
	　* 以下の場合、CifApplicationExceptionにthrow する。
	　*		①引数が８桁でなければ、エラー画面出力
	　*		②引数がニューメリックでなければ、エラー画面出力
	　*		③引数が暦上日でなければ、エラー画面出力
	　* 
	  * @param  seireki    基準西暦年（int型）
	  * @param  sanissu    差日数（int型）
	  */

	public String getSanissuDate(int seireki,int sanissu)throws Exception {
	
		return getSanissuDate(Integer.toString(seireki),sanissu);
	}
	
	
	/** 
	　* 指定された西暦年月日のＸ日前またはＸ日後をString 型で返す。
	　* Ｘ日前を求めるには、第２引数に負の数
	　* Ｘ日後を求めるには、第２引数に正の数をセットする
	　* ( 第２引数に "0" をセットすると、第１引数をそのまま返す）
	　* 以下の場合、CifApplicationExceptionにthrow する。
	　*		①引数が８桁でなければ、エラー画面出力
	　*		②引数がニューメリックでなければ、エラー画面出力
	　*		③引数が暦上日でなければ、エラー画面出力
	　* 
	  * @param  seireki    基準西暦年（String型）
	  * @param  sanissu    差日数（int型）
	  */

	public String getSanissuDate(String seireki,int sanissu)throws Exception {
		
		if(seireki.length() != 8){
			throw new CifApplicationException("1008-02:"+ seireki);
		}
		//ニューメリックＣＨＥＣＫ
		try {
			int wk =  Integer.parseInt(seireki);
		}
		catch(NumberFormatException nfe){
			throw new CifApplicationException("1008-02:" + seireki);
		}
		
		//暦上日チェック		
		if(!checkDate( seireki )){
			throw new CifApplicationException("1008-02:" + seireki);
		}
		
		if(sanissu == 0 ){
			return seireki;
		}
		
		int year = Integer.parseInt(seireki.substring(0,seireki.length() - 4 ));
		int month = Integer.parseInt(seireki.substring(seireki.length() - 4,seireki.length() - 2 ));
		int day = Integer.parseInt(seireki.substring(seireki.length() - 2,seireki.length() ));
		
		
		//日付/時刻の解釈を厳密に行う設定にする
		cal.setLenient( false );
		//年、月、日付のフィールドに値を設定（Month 値は 0 から始まる。つまり、0 は 1 月）
		cal.set(year, month -1, day);

		cal.add(Calendar.DATE,sanissu);
		year  = cal.get(Calendar.YEAR);
		month  = cal.get(Calendar.MONTH);
		day  = cal.get(Calendar.DATE);
		//（Month 値は 1少ない値が返される為の調整）
		month++;
		
		String SanissuDateYear = Integer.toString(year);
		String SanissuDateMonth = Integer.toString(month);
		String SanissuDateDay = Integer.toString(day);
		while (SanissuDateMonth.length() < 2){
			SanissuDateMonth = "0" + SanissuDateMonth;
		}
		while (SanissuDateDay.length() < 2){
			SanissuDateDay = "0" + SanissuDateDay;
		}
		
		return SanissuDateYear +SanissuDateMonth +SanissuDateDay ; 
	}
	
	/** 
	　* 指定された西暦年月日のＸ営業日前またはＸ営業日後をString 型で返す。
	　* Ｘ営業日前を求めるには、第２引数に負の数
	　* Ｘ営業日後を求めるには、第２引数に正の数をセットする
	　* ( 第２引数に "0" をセットすると、第１引数をそのまま返す）
	　* 以下の場合、CifApplicationExceptionにthrow する。
	　*		①引数が８桁でなければ、エラー画面出力
	　*		②引数がニューメリックでなければ、エラー画面出力
	　*		③引数が暦上日でなければ、エラー画面出力
	　* 
	  * @param  seireki    基準西暦年（int型）
	  * @param  saeigyoubisu    差営業日数（int型）
	  */

	public String getSaeigyoubi(int seireki,int saeigyoubisu)throws Exception {
	
		return getSaeigyoubi(Integer.toString(seireki),saeigyoubisu);
	}

	
	
	/** 
	　* 指定された西暦年月日のＸ営業日前またはＸ営業日後をString 型で返す。
	　* Ｘ営業日前を求めるには、第２引数に負の数
	　* Ｘ営業日後を求めるには、第２引数に正の数をセットする
	　* ( 第２引数に "0" をセットすると、第１引数をそのまま返す）
	　* 以下の場合、CifApplicationExceptionにthrow する。
	　*		①引数が８桁でなければ、エラー画面出力
	　*		②引数がニューメリックでなければ、エラー画面出力
	　*		③引数が暦上日でなければ、エラー画面出力
	　* 
	  * @param  seireki    基準西暦年（String型）
	  * @param  saeigyoubisu    差営業日数（int型）
	  */

	public String getSaeigyoubi(String seireki,int saeigyoubisu)throws Exception {
		
		if(seireki.length() != 8){
			throw new CifApplicationException("1008-02:"+ seireki);
		}
		//ニューメリックＣＨＥＣＫ
		try {
			int wk =  Integer.parseInt(seireki);
		}
		catch(NumberFormatException nfe){
			throw new CifApplicationException("1008-02:" + seireki);
		}
		
		//暦上日チェック		
		if(!checkDate( seireki )){
			throw new CifApplicationException("1008-02:" + seireki);
		}
		
		if(saeigyoubisu == 0 ){
			return seireki;
		}
		
		int eigyoubiCheckCounter = saeigyoubisu;		/* for loop 用カウンター */
		int sanissuParameter = 1 ;						/* 1:翌日を求めるパラメーター、-1:前日を求めるパラメーター */
		String saeigyoubi = seireki ;                     	/* 算出した差営業日 */
		
		if(saeigyoubisu < 0) {
			eigyoubiCheckCounter = eigyoubiCheckCounter * -1 ;
			sanissuParameter = -1 ;
		}

		//Ｘ営行日前（後）を算出するforループ
		for(int i = 0; i < eigyoubiCheckCounter ; i++)   {
			
			//前（翌）営業日を算出するdoループ
			do {
				//前（翌）日を算出する
				saeigyoubi = getSanissuDate( saeigyoubi , sanissuParameter );
			} while ( !checkEigyobi(saeigyoubi) ); /* 非営業日なら繰り返す */
		
		}
		
		return saeigyoubi ;

		}
	
	
	/**
	 * 和暦（GGyy年MM月dd日）⇒西暦（yyyyMMdd）変換
	 * 
	 * @param wareki
	 * @return
	 * @throws Exception
	 */
	public String getSeirekiForWareki(String wareki){
		try {
			if(wareki != null && wareki.length() == 11){
				String gengo = wareki.substring(0,2);
				String nen = wareki.substring(2,4);
				String tuki = wareki.substring(5,7);
				String niti = wareki.substring(8,10);
				
				int date = Integer.parseInt(nen + tuki + niti);
				
//				int date = Integer.parseInt(wareki.substring(1));				

				//00年の入力は不可
				if(date < 10000){
					return "";
				}

				String seireki;
				if(gengo.equals("明治")){
					//明治
					seireki = String.valueOf(18670000 + date);
				}else if(gengo.equals("大正")){
					//大正
					seireki = String.valueOf(19110000 + date);
				}else if(gengo.equals("昭和")){
					//昭和
					seireki = String.valueOf(19250000 + date);
				}else if(gengo.equals("平成")){
					//平成
					seireki = String.valueOf(19880000 + date);
				}else{
					//その他の元号は変換不可
					seireki = "";
				}

				//和暦の整合性が取れない（平成元年１月１日など）場合、変換不可
//				if(wareki.equals(convertSimpleWareki(seireki))){
					return seireki;
//				} else {
//					return "";
//				}
			} else {
				return "";
			}
		} catch (NumberFormatException e) {
			//数値以外が日付部分に入っていたら空文字で返す。
			return "";
		}
	}
	
	
	
	/************************* 元号対応後　*************************/

	/** 元号 | 自年月日 | 至年月日 */
	private static final String [][]gengoTable2= {
		{"令和","20190501","99999999"},
		{"平成","19890108","20190430"},
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

	/**
	 * 和暦（GGyy年MM月dd日）⇒西暦（yyyyMMdd）変換
	 * 
	 * @param wareki
	 * @return
	 * @throws Exception
	 */
	public static String getSeirekiForWareki2(String wareki){
		try {
						
			if(wareki != null && wareki.length() == 11){
				String gengo = wareki.substring(0,2);
				String nen = wareki.substring(2,4);
				String tuki = wareki.substring(5,7);
				String niti = wareki.substring(8,10);
				
				int date = Integer.parseInt(nen + tuki + niti);
				
//				int date = Integer.parseInt(wareki.substring(1));				

				//00年の入力は不可
				if(date < 10000){
					return "";
				}

				String seireki;

				if(gengo.equals("明治")){
					//明治
					seireki = String.valueOf(18670000 + date);
				}else if(gengo.equals("大正")){
					//大正
					seireki = String.valueOf(19110000 + date);
				}else if(gengo.equals("昭和")){
					//昭和
					seireki = String.valueOf(19250000 + date);
				}else if(gengo.equals("平成")){
					//平成
					seireki = String.valueOf(19880000 + date);
				}else if(gengo.equals("令和")){
					//令和
					seireki = String.valueOf(20180000 + date);	
					
				}else{
					//その他の元号は変換不可
					seireki = "";
				}

				//和暦の整合性が取れない（平成元年１月１日など）場合、変換不可
//				if(wareki.equals(convertSimpleWareki(seireki))){
				
					return seireki;
//				} else {
//					return "";
//				}
			} else {
				return "";
			}
		} catch (NumberFormatException e) {
			//数値以外が日付部分に入っていたら空文字で返す。
			return "";
		}
	}
	
	
	/**
     * 西暦8桁yyyymmddもしくは西暦10桁yyyy-mm-ddのString引数から
     * “－“を削除した形式に編集してから和暦に返還しString型の和暦を返す。
     * @param  eDate   西暦8桁のStringもしくは“－“を削除したい西暦10桁のString
     *
     * @return 和暦 元号"H"or"S"or"T"+yymmdd"フォーマット
     */
	public String getSimpleGengoWareki2(String eDate)throws Exception{
		StringBuffer sbDate;
		if(eDate==null){
			sbDate=new StringBuffer("");
		}else{
			sbDate=new StringBuffer(get49Wareki2(eDate));
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
				sbDate.delete(0,2);
			}
		}
		return sbDate.toString();
	}
	
	
	
	/**
     * 西暦8桁yyyymmddもしくは西暦10桁yyyy-mm-ddのString引数から
     * “－“を削除した形式に編集してから和暦に返還しString型の和暦を返す。
     * @param  eDate   西暦8桁のStringもしくは“－“を削除したい西暦10桁のString
     *
     * @return 和暦 平成yy年mm月dd日フォーマット
     */
	public String get49Wareki2(String eDate)throws Exception{
		StringBuffer sbDate;
		
		if(eDate.length()==10){
			if(eDate.substring(4,5).equals("-")&eDate.substring(7,8).equals("-")){
				sbDate=new StringBuffer(getWareki2(edit49Date(eDate)));
			}else{
				sbDate=new StringBuffer("dateError in CifComn");
			}
		}else{
			sbDate=new StringBuffer(getWareki2(eDate));
		}
		return sbDate.toString();
	}

	//YYYYMMDD->和暦（年号X年XX月XX日）
	public String getWareki2(String seireki)throws Exception
	{
		//８桁ＣＨＥＣＫ	
		if(seireki.length() != 8){
			if(seireki.length() != 10){
				throw new CifApplicationException("1008-02" +"西暦８or10桁を入力して下さい" + seireki);
			}else{
				if(seireki.substring(4,5).equals("-")&&seireki.substring(7,8).equals("-")){
					StringBuffer sbDate=new StringBuffer(seireki);
					sbDate.delete(7,8);
					sbDate.delete(4,5);
					seireki=sbDate.toString();
				}else{
					throw new CifApplicationException("1008-02" +"西暦10桁を入力して下さい" + seireki);
				}
			}
		}
		//ニューメリックＣＨＥＣＫ
		try{
			int wk =  Integer.parseInt(seireki);
		}
		catch(NumberFormatException nfe){
			throw new CifApplicationException("1007-02" + seireki);
		}
		if(!checkDate(seireki)){
			throw new CifApplicationException("1008-02" +"暦上日を入力して下さい" + seireki);
		}
		
		int i = 0;
		for(  ; i < gengoTable2.length;i++){
			if(Integer.parseInt(seireki) >= Integer.parseInt(gengoTable2[i][1]) && Integer.parseInt(seireki) <= Integer.parseInt(gengoTable2[i][2])){
				break;
			}
		}
		if (gengoTable2[i][0].equals("不明")){
			throw new CifApplicationException("1008-02"+":明治元年より過去の日付が入力された"+ seireki);
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
	　* 引数７桁　元号表示"R"or"H"or"S"or"T" + 和暦ＹＹＭＭＤＤとみなし、西暦ＹＹＹＹＭＭＤＤで返す。
	  * 引数６桁　和暦ＹＹＭＭＤＤとみなし、西暦ＹＹＹＹＭＭＤＤで返す。
	　* 　　　　　　ただし、指定の年月日が存在していれば、"PARAMERR"を返す。
	　* 引数４桁　和暦ＹＹＭＭとみなし、西暦ＹＹＹＹＭＭで返す。
	　* 引数２桁　和暦ＹＹとみなし、西暦ＹＹＹＹで返す。
    	　* 以外　　、"PARAMERR"を返す。
	  *
	  * @param  wareki  和暦日付（String型）
	  *
	  */

	public String getSeireki2(String wareki)throws Exception{

		String seirekiDate = "";

		String gengo="";
		String warekiYear = "";
		String warekiMonth = "";
		String warekiDay = "";

		int seirekiYear;
		int seirekiMonth;
		int seirekiDay;

		
		if(wareki.length() == 7){
			gengo       =wareki.substring(0,1);
			warekiYear  =wareki.substring(1,3);
			warekiMonth =wareki.substring(3,5);
			warekiDay   =wareki.substring(5,7);
			if(gengo.equals("R")){
				seirekiYear = 2018 + Integer.parseInt(warekiYear);
			}else if(gengo.equals("H")){
				seirekiYear = 1988 + Integer.parseInt(warekiYear);
			}else if(gengo.equals("S")){
				seirekiYear = 1925 + Integer.parseInt(warekiYear);
			}else if(gengo.equals("T")){
				seirekiYear = 1911 + Integer.parseInt(warekiYear);
			}else if(gengo.equals("M")){
				seirekiYear = 1867 + Integer.parseInt(warekiYear);
			}else{
				seirekiYear = 2018 + Integer.parseInt(warekiYear);
			}
			
			seirekiDate = Integer.toString(seirekiYear) + warekiMonth + warekiDay;
			seirekiMonth = Integer.parseInt(warekiMonth) ;
			seirekiDay = Integer.parseInt(warekiDay);
		}else{
			//ニューメリックＣＨＥＣＫ
			try{
				int wk =  Integer.parseInt(wareki);
			}
			catch(NumberFormatException nfe){
				throw new CifApplicationException("9000-02"+nfe.toString());
			}
			if(wareki.length() == 6){
				warekiYear = wareki.substring(0,2);
				warekiMonth = wareki.substring(2,4);
				warekiDay = wareki.substring(4,6);

				seirekiYear = 1988 + Integer.parseInt(warekiYear);
				seirekiDate = Integer.toString(seirekiYear) + warekiMonth + warekiDay;
				seirekiMonth = Integer.parseInt(warekiMonth) ;
				seirekiDay = Integer.parseInt(warekiDay);
			}
			else if(wareki.length() == 4){
				warekiYear = wareki.substring(0,2);
				warekiMonth = wareki.substring(2,4);

				seirekiYear = 1988 + Integer.parseInt(warekiYear);
				seirekiDate = Integer.toString(seirekiYear) + warekiMonth;
				seirekiMonth = Integer.parseInt(warekiMonth) ;
				seirekiDay = 10;//平成１年１月１日は存在しない為「１０」セット
			}
			else if(wareki.length() == 2){
				warekiYear = wareki.substring(0,2);

				seirekiYear = 1988 + Integer.parseInt(warekiYear);
				seirekiDate = Integer.toString(seirekiYear);
				seirekiMonth = 1;
				seirekiDay = 10;//平成１年１月１日は存在しない為「１０」セット
			}
			else{
				return "PARAMERR";
			}
			
		}

		//存在する暦上日なら、trueを返す。存在しない暦上日なら、falseを返す。
		boolean check = checkDate(seirekiYear,seirekiMonth,seirekiDay);
		if(check == false){
			return "PARAMERR";
		}
		return seirekiDate ;
	}

	
	
	/** 
	　* 指定の和暦年月日が存在するなら、trueを返す。
	　* 指定の和暦年月日が存在しなければ、falseを返す。
	　* 引数が６桁ならyymmdd、７桁なら"H"or"S"or"T" + 和暦yymmdd。
	　* 
	  * @param  wareki  和暦日付（String型）
	  */
	public boolean checkWarekiDate2(String wareki)throws Exception{

		boolean status=false;
		String date;
		if(wareki.length()==6){
			date=new String(wareki);
		}else if(wareki.length()==7){
			String gengo=new String(wareki.substring(0,1));
			if(gengo.equals("R")|gengo.equals("H")|gengo.equals("S")|gengo.equals("T")|gengo.equals("M")){
				date=new String(wareki.substring(1,7));
			}else{
				return status;
			}
		}else{
			return status;
		}
		try{
			int wk=Integer.parseInt(date);
		}
		catch(NumberFormatException nfe){
			return status;
		}
		if(!getSeireki2(wareki).equals("PARAMERR")){
			status=true;
		}
		return status;
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
	

}
