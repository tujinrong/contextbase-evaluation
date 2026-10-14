package webon.util;

import java.io.UnsupportedEncodingException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

/**
 * webon汎用照会　値のべリファイ用ユーティリティ
 * 
 * @author Minori 京極
 * 
 * @date	2020.02.13		京極		新規作成
 */
public class ValidateUtil {
	//以下、メンバ=============================================================================================================================
	private static final String kanaHanZenTbl[][] = {			//全角カナ⇒半角ｶﾅ変換用テーブル
		// 2文字構成の濁点付き半角カナ
	    // 必ずテーブルに先頭に置いてサーチ順を優先すること
	      { "ｶﾞ", "ガ" }, { "ｷﾞ", "ギ" }, { "ｸﾞ", "グ" }, { "ｹﾞ", "ゲ" }, { "ｺﾞ", "ゴ" }, 
	      { "ｻﾞ", "ザ" }, { "ｼﾞ", "ジ" }, { "ｽﾞ", "ズ" }, { "ｾﾞ", "ゼ" }, { "ｿﾞ", "ゾ" },
	      { "ﾀﾞ", "ダ" }, { "ﾁﾞ", "ヂ" }, { "ﾂﾞ", "ヅ" }, { "ﾃﾞ", "デ" }, { "ﾄﾞ", "ド" },
	      { "ﾊﾞ", "バ" }, { "ﾋﾞ", "ビ" }, { "ﾌﾞ", "ブ" }, { "ﾍﾞ", "ベ" }, { "ﾎﾞ", "ボ" }, 
	      { "ﾊﾟ", "パ" }, { "ﾋﾟ", "ピ" }, { "ﾌﾟ", "プ" }, { "ﾍﾟ", "ペ" }, { "ﾎﾟ", "ポ" }, 
	      { "ｳﾞ", "ヴ" },
	      // 1文字構成の半角カナ
	      { "ｱ", "ア" }, { "ｲ", "イ" }, { "ｳ", "ウ" }, { "ｴ", "エ" }, { "ｵ", "オ" }, 
	      { "ｶ", "カ" }, { "ｷ", "キ" }, { "ｸ", "ク" }, { "ｹ", "ケ" }, { "ｺ", "コ" }, 
	      { "ｻ", "サ" }, { "ｼ", "シ" }, { "ｽ", "ス" }, { "ｾ", "セ" }, { "ｿ", "ソ" }, 
	      { "ﾀ", "タ" }, { "ﾁ", "チ" }, { "ﾂ", "ツ" }, { "ﾃ", "テ" }, { "ﾄ", "ト" }, 
	      { "ﾅ", "ナ" }, { "ﾆ", "ニ" }, { "ﾇ", "ヌ" }, { "ﾈ", "ネ" }, { "ﾉ", "ノ" }, 
	      { "ﾊ", "ハ" }, { "ﾋ", "ヒ" }, { "ﾌ", "フ" }, { "ﾍ", "ヘ" }, { "ﾎ", "ホ" }, 
	      { "ﾏ", "マ" }, { "ﾐ", "ミ" }, { "ﾑ", "ム" }, { "ﾒ", "メ" }, { "ﾓ", "モ" }, 
	      { "ﾔ", "ヤ" }, { "ﾕ", "ユ" }, { "ﾖ", "ヨ" }, 
	      { "ﾗ", "ラ" }, { "ﾘ", "リ" }, { "ﾙ", "ル" }, { "ﾚ", "レ" }, { "ﾛ", "ロ" }, 
	      { "ﾜ", "ワ" }, { "ｦ", "ヲ" }, { "ﾝ", "ン" }, 
	      { "ｧ", "ァ" }, { "ｨ", "ィ" }, { "ｩ", "ゥ" }, { "ｪ", "ェ" }, { "ｫ", "ォ" }, 
	      { "ｬ", "ャ" }, { "ｭ", "ュ" }, { "ｮ", "ョ" }, { "ｯ", "ッ" }, 
	  };
	
	private static final String kanaCheckTbl[][] = {		//全角カナ⇒半角ｶﾅ変換、リーガルチェック用テーブル
	      //規定外文字（規定外文字を使用可能文字に変換する）
	      { "ｱ", "ァ" }, { "ｲ", "ィ" }, { "ｳ", "ゥ" }, { "ｴ", "ェ" }, { "ｵ", "ォ" }, 
	      { "ﾔ", "ャ" }, { "ﾕ", "ュ" }, { "ﾖ", "ョ" }, { "ﾂ", "ッ" }, 
	      { "ｱ", "ｧ"}, { "ｲ", "ｨ"}, { "ｳ", "ｩ"}, { "ｴ", "ｪ"}, { "ｵ", "ｫ"}, 
	      { "ﾔ", "ｬ"}, { "ﾕ", "ｭ"}, { "ﾖ", "ｮ"}, { "ﾂ", "ｯ"}, 
	      //半角記号(全角・半角の長音は、ハイフンに変換する)
	      { "｢", "「" }, { "｣", "」" },{ "-", "‐" },{ "-", "－" },{ "-", "ー" },{ "-", "ｰ" }, 
	      { " ", "　" }, {"(", "（"},{")", "）"}
	};
	
	//以上、メンバ=============================================================================================================================

	//数値チェック
	public static boolean doubleCheck (String str) {
		try {
            Double.parseDouble(str);
            return true;
        } catch(NumberFormatException e) {
            return false;
        }
	}
	//整数チェック
	public static boolean intCheck (String str) {
		try {
            Integer.parseInt(str);
            return true;
        } catch(NumberFormatException e) {
            return false;
        }
	}
	//自然数チェック
    public static boolean numCheck(String str) {
    	final String P_ALPHA_DIGIT_ONLY     = "^[0-9]+$";
    	return str.matches(P_ALPHA_DIGIT_ONLY);
	}
	//自然数チェック(全角OK)
    public static boolean numCheck2(String str) {
    	str=EmToEn(str);
    	return numCheck(str);
	}
	//金額チェック(数値、カンマのみ)
    public static boolean amountCheck(String str) {
    	final String P_ALPHA_DIGIT_ONLY     = "^[0-9,]+$";
    	return str.matches(P_ALPHA_DIGIT_ONLY);
	}
	//金額チェック(数値、カンマ、-のみ)
    public static boolean amountCheck2(String str) {
    	final String P_ALPHA_DIGIT_ONLY     = "^[0-9,-]+$";
    	return str.matches(P_ALPHA_DIGIT_ONLY);
	}
	//英数チェック
    public static boolean alphaCheck(String str) {
    	final String P_ALPHA_DIGIT_ONLY     = "^[0-9A-Za-z]+$";
    	return str.matches(P_ALPHA_DIGIT_ONLY);
	}
	//英数チェック(全角OK)
    public static boolean alphaCheck2(String str) {
    	str=EmToEn(str);
    	return alphaCheck(str);
	}
    //最大桁数チェック
	public static boolean digitMaxCheck (String str, int len) {
		return str.length()<=len;
	}
	//最小桁数チェック
	public static boolean digitMinCheck (String str, int len) {
		return str.length()>=len;
	}
	//数値整形用(右詰０パディング)
	public static String numberForm (String str, int dig) {
		String result="";
		str = EmToEn(str);
		if (numCheck(str)) {
			if (str.length()>dig){
				result=str.substring(str.length()-dig);
			} else {
				result=String.format("%1$0"+dig+"d", Integer.parseInt(str));
			}
			return result;
		}
		return result;
	}
	//半角英数→全角英数
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
	//全角英数→半角英数
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
	 * 全角カナ・半角カナ変換用メソッド
	 * 全角カナ⇒半角カナ
	 * @param String 変換対象文字列
	 * @return String 変換後文字列
	 * 
	 * null又は空文字の場合、空文字を返す
	 */
	  public static String ZenToHanForKKana(String p) {
		  StringBuffer sb = new StringBuffer();
		  for (int i = 0, j = 0; i < p.length(); i++) {
			Character c = new Character(p.charAt(i));
			// 半角全角変換テーブルを検索する
			for (j = 0; j < kanaHanZenTbl.length; j++) {
				if (p.substring(i).startsWith(kanaHanZenTbl[j][1])) {
					sb.append(kanaHanZenTbl[j][0]);
					break;
				}
			}
			// 検索できなければ、変換しない
			if (j >= kanaHanZenTbl.length) {
				sb.append(c);
			}   
		  }
		return sb.toString();
	  }
	/**
	 * 全角カナ・半角カナリーガルチェック用メソッド
	 * 規定外文字⇒使用可能文字
	 * @param String 変換対象文字列
	 * @return String 変換後文字列
	 * 
	 * null又は空文字の場合、空文字を返す
	 */
	public static String checkZenToHanKana(String p) {
		StringBuffer sb = new StringBuffer();
		for (int i = 0, j = 0; i < p.length(); i++) {
			Character c = new Character(p.charAt(i));
			// カナリーガルチェックテーブルを検索する
			for (j = 0; j < kanaCheckTbl.length; j++) {
				if (p.substring(i).startsWith(kanaCheckTbl[j][1])) {
					sb.append(kanaCheckTbl[j][0]);
					break;
				}
			}
			// 検索できなければ、変換しない
			if (j >= kanaCheckTbl.length) {
				sb.append(c);
			}   
		}
		return sb.toString();
	}
	
	/**
	 * 全角Shift-JISコード　レンジチェックメソッド
	 * 対象の文字列が指定された文字コードの範囲内かチェックする
	 * null又は空文字の場合、falseを返す
	 * @throws UnsupportedEncodingException 
	 * 
	 * @return boolean 判定結果　false:範囲内　true:範囲外
	 */
	public static boolean checkZenCodeBool(String val) throws UnsupportedEncodingException{
		if (val==null||val.equals("")) {
			return false;
		}
		boolean flg=false;
		byte[]br=val.getBytes();
		//2バイトづつ抜き出し、２バイト文字列として比較
		for(int i=0;i+1<br.length;i+=2){
			byte b1=br[i];
			byte b2=br[i+1];
			//バイトを１６進数変換後、負数の符号化ビットを取り除き、正の１６進数文字コードを生成する。
			String sj = Integer.toHexString(b1 & 0xff)+Integer.toHexString(b2 & 0xff);
			//１文字ずつ比較し、範囲外文字があったらtrueを返す
			if(!(checkRange(sj, "8140", "817A")||
					checkRange(sj, "824F", "8396")||
					checkRange(sj, "889F", "9872")||
					checkRange(sj, "989F", "EAA4"))){
				flg=true;
			}
		}
		return flg;
	}
	/**
	 * 全角Shift-JISコード　レンジチェックメソッド(全角文字列のみ判定可能)
	 * 対象の文字列が指定された文字コードの範囲内かチェックする
	 * null又は空文字の場合、空文字を返す
	 * @throws UnsupportedEncodingException 
	 * 
	 * @return String 使用不可能文字列　0文字：使用不可能文字なし、1文字以上：使用不可能文字あり　
	 */
	public static String checkZenCodeStr(String val) throws UnsupportedEncodingException{
		if (val==null||val.equals("")) {
			return "";
		}
		//使用不可能文字列
		String ngStr="";
		//使用不可能文字格納用リスト
		ArrayList<Byte> ngChrList = new ArrayList<Byte>();
		//文字列からバイトコード配列を取得
		byte[]br=val.getBytes();
		//2バイトづつ抜き出し、２バイト文字列として比較
		for(int i=0;i+1<br.length;i+=2){
			byte b1=br[i];
			byte b2=br[i+1];
			//バイトを１６進数変換後、負数の符号化ビットを取り除き、正の１６進数文字コードを生成する。
			String sj = Integer.toHexString(b1 & 0xff)+Integer.toHexString(b2 & 0xff);
			//１文字ずつ比較し、範囲外文字があったらリストに格納する
			if(!(checkRange(sj, "8140", "817A")||
					checkRange(sj, "824F", "8396")||
					checkRange(sj, "889F", "9872")||
					checkRange(sj, "989F", "EAA4"))){
				ngChrList.add(b1);
				ngChrList.add(b2);
			}
		}
		//使用不可能文字格納用配列
		byte ngBr[] = new byte[ngChrList.size()];
		for(int i=0;i<ngChrList.size();i++){
			ngBr[i]=ngChrList.get(i);
		}
		//バイト配列から文字列を取得
		ngStr=new String(ngBr);
		//使用不可能文字列を返す
		return ngStr;
	}
	/**
	 * 全角Shift-JISコード　レンジチェックメソッド(全角文字列のみ判定可能)
	 * 第一、第二水準漢字及び信金外字使用範囲
	 * Unicodeタグ対応のため、1バイト文字も処理できるように修正
	 * ※1バイト文字は全て使用不可として処理
	 * null又は空文字の場合、空文字を返す
	 * @throws UnsupportedEncodingException 
	 * 
	 * @return String 使用不可能文字列　0文字：使用不可能文字なし、1文字以上：使用不可能文字あり　
	 */
	public static String checkShinkinCodeStr(String val) throws UnsupportedEncodingException{
		if (val==null||val.equals("")) {
			return "";
		}
		char[] charr= val.toCharArray();
		//コピーとしてListを作成
		List<Character> chList = new ArrayList<Character>(); 
		for (Character ch:charr) {
			chList.add(ch);
		}
		
		List<Character> ngChList = new ArrayList<Character>();
		
		//文字列の走査
		Iterator<Character> it = chList.iterator();
		Character chkChr;
		byte[] bytArr;
		byte byt1,byt2;
		String chkCode;
		while (it.hasNext()){
			chkChr=it.next();
			byt1=0;
			byt2=0;
			bytArr=chkChr.toString().getBytes();
			if (bytArr.length>2) {
				//もし、3バイト以上のUnicodeがあったらエラーとする(Unicodeタグ化されるのでないはず)
				throw new UnsupportedEncodingException("3バイト以上の長さの文字はサポート外です。："+chkChr.toString());
			} else if (bytArr.length==2) {
				byt1=bytArr[0];
				byt2=bytArr[1];
				chkCode = Integer.toHexString(byt1 & 0xff)+Integer.toHexString(byt2 & 0xff);

				if(!(checkRange(chkCode, "8140", "EAA4")||
						checkRange(chkCode, "F040", "F2C8"))){
					
					ngChList.add(chkChr);
				}
				
			} else if (bytArr.length==1) {
				//1バイト文字は全て処理不可
				ngChList.add(chkChr);
			} else {
				throw new UnsupportedEncodingException("チェックする対象文字がありません。");
			}
			
		}

		char[] charAr =new char[ngChList.size()];
		for(int i=0;i<ngChList.size();i++){
			charAr[i]=ngChList.get(i).charValue();
		}
		String ngStr=new String(charAr);
		//使用不可能文字列を返す
		return ngStr;
	}
	/**
	 * 文字列中にUnicodeタグ(&#xxxx;)形式の文字列があった場合、
	 * JavaScriptのUnicodeEscapeSeaquence形式に変換する
	 * 入力するUnicodeタグは10進
	 * 出力するEscapeSeaquenceは16進
	 * @param String 変換対象文字列
	 * @return String 変換後文字列　
	 */
	public static String convertUniTag2Esc(String ngString){
		StringBuilder sb1 = new StringBuilder(ngString);	//処理文字列
		StringBuilder sb2 = new StringBuilder();			//処理結果文字列
		StringBuilder sbTmp = new StringBuilder();			//ワーク用
		final String shead="&#";							//ユニコードタグヘッダ
		final String sfoot=";";								//ユニコードタグフッタ
		final String thead="\\u";							//エスケープ用ヘッダ
		//int pointer=0;	//検索ポインタ
		int unicode=0;	//変換用
		String uniStr="";
		int count=0;
		
		//接頭辞(&#)の取得
		while (sb1.indexOf(shead)>=0){	
			int st = sb1.indexOf(shead);
			//if (st>=0) {
				sb2.append(sb1.subSequence(0, st));		//ユニコード出現前までの文字列を結果に退避
				sb1.delete(0, st);						//退避分を削除
				
				sbTmp.setLength(0);								//ワークのクリア
				int en = sb1.indexOf(sfoot);						
				sbTmp.append(sb1.subSequence(shead.length(), en));	//Unicodeの取得
				sb1.delete(0, en+sfoot.length());						//ユニコード分のクリア
				
				//ユニコードの数値チェック
				uniStr=sbTmp.toString();
				if (intCheck(uniStr)){
					//unicodeの変換
					unicode = Integer.parseInt(uniStr);
					//FWLog.debug("★★★unicode取得："+unicode);
					//JIS2004対応(サロゲートペアの処理)
					//範囲はとりあえず、JIS2004追加分の\u2000B-\u2A6B2の範囲とする
					//→修正0x10000-0x10FFFFまでの範囲にする(サロゲート追加範囲)
					//if (unicode>=131083 && unicode <=173746) {
					if (unicode>=0x10000 && unicode <=0x10FFFF) {
						int uppeer=(unicode-0x10000)/0x400+0xD800;
						int lower=(unicode-0x10000)%0x400+0xDC00;
						sb2.append(thead).append(Integer.toHexString(uppeer)).append(thead).append(Integer.toHexString(lower));
						//FWLog.debug("★★★unicode変換："+Integer.toHexString(upper)+" "+Integer.toHexString(lower));
						
					} else {
						//通常の変換
						sb2.append(thead).append(Integer.toHexString(unicode));
						//FWLog.debug("★★★unicode変換："+Integer.toHexString(unicode));
					}
				} else {
					//数値変換エラーの場合は変換せずにそのまま追加
					sb2.append(shead).append(uniStr).append(sfoot);
				}
				
			//}
				count++;
				if (count>100) {break;}
		}
		
		sb2.append(sb1);
		//FWLog.debug("★★★ESC変換後文字列："+sb2.toString());
		return sb2.toString();
	}
	/**
	 * 全角Shift-JISコード　レンジチェックメソッド(全角文字列のみ判定可能)
	 * 信金外字が使用されているかチェック
	 * null又は空文字の場合、空文字を返す
	 * @throws UnsupportedEncodingException 
	 * 
	 * @return String 使用不可能文字列　0文字：使用不可能文字なし、1文字以上：使用不可能文字あり　
	 */
	public static boolean checkGaijiCodeStr(String val) throws UnsupportedEncodingException{
		if (val==null||val.equals("")) {
			return false;
		}
		//文字列からバイトコード配列を取得
		byte[]br=val.getBytes();
		//2バイトづつ抜き出し、２バイト文字列として比較
		for(int i=0;i+1<br.length;i+=2){
			byte b1=br[i];
			byte b2=br[i+1];
			//バイトを１６進数変換後、負数の符号化ビットを取り除き、正の１６進数文字コードを生成する。
			String sj = Integer.toHexString(b1 & 0xff)+Integer.toHexString(b2 & 0xff);
			//１文字ずつ比較し、範囲内文字があったらTrue復帰
			if(checkRange(sj, "F040", "F2C8")){
				return true;
			}
		}
		return false;
	}
	/**
	 * Shift-JISコード　レンジチェック用メソッド
	 * 文字列が引数２と引数３の範囲内にある文字コードか判定する。
	 * @param String 文字コード１
	 * @param String 文字コード２
	 *  @return boolean 判定結果　false:範囲内　true:範囲外
	 * @throws UnsupportedEncodingException 
	 */
	public static boolean checkRange(String sj,String r1,String r2) throws UnsupportedEncodingException{
		boolean flg=false;
//			System.out.println("比較値："+Integer.parseInt(sj, 16)+"値１："+Integer.parseInt(r1, 16)+"値２："+Integer.parseInt(r2, 16));
//			System.out.println("結論："+((Integer.parseInt(r1,16))<=Integer.parseInt(sj, 16)&&Integer.parseInt(sj,16)<=(Integer.parseInt(r2, 16))));
			if((Integer.parseInt(r1,16))<=Integer.parseInt(sj, 16)&&Integer.parseInt(sj,16)<=(Integer.parseInt(r2, 16))){
				flg=true;
			}
		return flg;
	}
}
