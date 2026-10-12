package webon.operation;

import java.sql.Connection;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.w3c.dom.Node;

import webon.WebonBase;
import webon.WebonException;
import webon.util.ConvertUtil;

import common.bean.LoginInfoBean;

/**
 * Webon汎用照会クラス　積立定期預金口座汎用照会クラス
 * 積立定期預金口座照会(XML)の取得とデータ管理、アクセスメソッドの提供
 * 
 * @author 吉津
 * 
 * @date	2020.04.16	新規作成
 */
public class TumitateTeikiYokinKozaShokai extends CommonOperation{
	private static final String syokaiName = "積立定期預金口座照会";
	
	//オペレーションＩＤ
	private final String operationId="OP-TSUMITEI-0001";
	//ログイン情報
	LoginInfoBean loginInfo;
	//webon引数
	String woAccno;
	String woBrno;
	
	//Errorレベル
	private static final int ERRLEVEL_ERROR=0;	//Error
	private static final int ERRLEVEL_WARNING=1;	//Warning
	//Error箇所
	private static final String ERRSPOT_WOGET = "0";		//取得時
	//private static final String ERRSPOT_WOANALYZE = "1";	//解析時
	private static final String ERRSPOT_WOMOLD = "2";		//成型時
	//Erro追加情報格納用リスト
	List<Map<String, String>> etc = new ArrayList<Map<String,String>>();
	//Error有無フラグ
	boolean errFlg=false;
	
	//setter,getter
	public List<Map<String, String>> getEtc() {
		return etc;
	}
	public void setEtc(List<Map<String, String>> etc) {
		this.etc = etc;
	}
	public boolean isErrFlg() {
		return errFlg;
	}
	public void setErrFlg(boolean errFlg) {
		this.errFlg = errFlg;
	}
	public String getWoAccno() {
		return woAccno;
	}
	public void setWoAccno(String woAccno) {
		this.woAccno = woAccno;
	}
	public String getWoBrno() {
		return woBrno;
	}
	public void setWoBrno(String woBrno) {
		this.woBrno = woBrno;
	}
	
	//=== 積立定期預金口座照会 ===
	//取得結果
	String 店番="";
	String 顧客番号="";
	String 科目="";
	String 口座番号="";
	String 口座状態="";
	String 商品コード="";
	String 商品名="";
	String 積立残高="";
	String 毎月積立額="";
	String 契約日="";
	String 預入期限日="";
	String 満期日="";
	String 最終取扱日="";
	String マル優本人死亡日="";
	String 支払開始日="";
	String 移受管日="";
	String 移受管店番="";
	String 移受管顧客番号="";
	String 移受管口座番号="";
	
	//==================================================
	//Getter,Setter
	//==================================================
	public String get店番() {
		return 店番;
	}
	public void set店番(String 店番) {
		this.店番 = 店番;
	}
	public String get顧客番号() {
		return 顧客番号;
	}
	public void set顧客番号(String 顧客番号) {
		this.顧客番号 = 顧客番号;
	}
	public String get科目() {
		return 科目;
	}
	public void set科目(String 科目) {
		this.科目 = 科目;
	}
	public String get口座番号() {
		return 口座番号;
	}
	public void set口座番号(String 口座番号) {
		this.口座番号 = 口座番号;
	}
	public String get口座状態() {
		return 口座状態;
	}
	public void set口座状態(String 口座状態) {
		this.口座状態 = 口座状態;
	}
	public String get商品コード() {
		return 商品コード;
	}
	public void set商品コード(String 商品コード) {
		this.商品コード = 商品コード;
	}
	public String get商品名() {
		return 商品名;
	}
	public void set商品名(String 商品名) {
		this.商品名 = 商品名;
	}
	public String get積立残高() {
		return 積立残高;
	}
	public void set積立残高(String 積立残高) {
		this.積立残高 = 積立残高;
	}
	public String get毎月積立額() {
		return 毎月積立額;
	}
	public void set毎月積立額(String 毎月積立額) {
		this.毎月積立額 = 毎月積立額;
	}
	public String get契約日() {
		return 契約日;
	}
	public void set契約日(String 契約日) {
		this.契約日 = 契約日;
	}
	public String get預入期限日() {
		return 預入期限日;
	}
	public void set預入期限日(String 預入期限日) {
		this.預入期限日 = 預入期限日;
	}
	public String get満期日() {
		return 満期日;
	}
	public void set満期日(String 満期日) {
		this.満期日 = 満期日;
	}
	public String get最終取扱日() {
		return 最終取扱日;
	}
	public void set最終取扱日(String 最終取扱日) {
		this.最終取扱日 = 最終取扱日;
	}
	public String getマル優本人死亡日() {
		return マル優本人死亡日;
	}
	public void setマル優本人死亡日(String マル優本人死亡日) {
		this.マル優本人死亡日 = マル優本人死亡日;
	}
	public String get支払開始日() {
		return 支払開始日;
	}
	public void set支払開始日(String 支払開始日) {
		this.支払開始日 = 支払開始日;
	}
	public String get移受管日() {
		return 移受管日;
	}
	public void set移受管日(String 移受管日) {
		this.移受管日 = 移受管日;
	}
	public String get移受管店番() {
		return 移受管店番;
	}
	public void set移受管店番(String 移受管店番) {
		this.移受管店番 = 移受管店番;
	}
	public String get移受管顧客番号() {
		return 移受管顧客番号;
	}
	public void set移受管顧客番号(String 移受管顧客番号) {
		this.移受管顧客番号 = 移受管顧客番号;
	}
	public String get移受管口座番号() {
		return 移受管口座番号;
	}
	public void set移受管口座番号(String 移受管口座番号) {
		this.移受管口座番号 = 移受管口座番号;
	}

	/**
	 * 口座番号・店番を元に積立定期預金口座照会を取得する
	 * 
	 * @param accno 口座番号
	 * @param br 店番
	 * @param 
	 * @param loginInfo ログイン情報
	 * @param con
	 * @throws Exception
	 */
	public void getWebon(String accno, String br, LoginInfoBean loginInfo, Connection con) throws Exception {
		try{
			//引数チェック 引数がセットされているか
			if (accno == null) {throw new Exception("口座番号が設定されていません");}
			if (br == null) {throw new Exception("原店番号が設定されていません");}
			if (con == null) {throw new Exception("ＤＢコネクションが設定されていません");}
			
			//引数のセット
			this.woAccno=accno;
			this.woBrno=br;
			this.loginInfo = loginInfo;
			
			//Webon問合せ実行
			getWebon(con);
			
			//取得結果解析
			analyzeWeon();
			
			//取得項目のチェック
			checkWebon();
			
			//エラーチェック(Exceptionの有無を判定する)
			if(errFlg){
				WebonException e = createWoException("Webon取得結果解析エラー", ERRLEVEL_WARNING, ERRSPOT_WOMOLD);
				e.setEtc(etc);
				//エラー処理は上位に任せる
				throw e;
			}
			
		}catch(WebonException e){
			throw e;
		}catch(Exception e){
			throw e;
		}
	}
	
	/**
	 * Webon取得メソッド
	 * アクション内では、初期設定メソッド(setMember)と、データ保管メソッド(saveSession)を行うこと
	 * 
	 * @param req リクエスト
	 * @param res レスポンス
	 * @throws Exception 
	 */
	private void getWebon(Connection con) throws Exception {
		
		//WebonBaseの取得
		webonBase = new WebonBase(operationId, loginInfo, con);
		//設定値
		webonBase.put("口座番号",woAccno);
		webonBase.put("原店番号",woBrno);
		//問い合わせ
		webonBase.doQuery();
		
		//エラー処理
		if (!webonBase.checkResult()) {
			//エラーコード等をセット
			WebonException e = createWoException("Webon取得結果エラー", ERRLEVEL_ERROR, ERRSPOT_WOGET);
			//エラー処理は上位に任せる
			throw e;
		}
	}
	
	/**
	 * Webon取得内容解析メソッド
	 * アクション内では、初期設定メソッド(setMember)と、データ保管メソッド(saveSession)を行うこと
	 * 
	 * @param req リクエスト
	 * @param res レスポンス
	 * @throws Exception 
	 * @throws Exception 
	 */
	public void analyzeWeon() throws Exception {
		//WEBON結果走査用固定値
		final String WOKEY_TSUCYO="通帳部宛";
		final String WOKEY_TSUMITEIKOZA="積立定期預金口座照会";

		//結果取得
		Node editData = webonBase.getEditData();
		//結果解析
		//データの最上位ノードを取得
		Node root2=editData.getFirstChild();
		Node root=null;
		while (true) {
        	//取得できなかったら終わり
        	if (root2==null){break;}
	    	if (root2.getNodeType()==Node.ELEMENT_NODE) {
	    		//要素名の解析
	    		if (root2.getNodeName().equals(WOKEY_TSUCYO)) {

	    			root = root2.getFirstChild();
	    			while (true) {
	    	        	//取得できなかったら終わり
	    	        	if (root==null){break;}
	    		    	if (root.getNodeType()==Node.ELEMENT_NODE) {
	    		    		//要素名の解析
	    		    		if (root.getNodeName().equals(WOKEY_TSUMITEIKOZA)) {
	    		    			break;
	    		            } 
	    		    	}
	    	        	//次の子ノードを取得
	    		    	root = root.getNextSibling();
	    			}
	    			break;
	            } 
	    	}
        	//次の子ノードを取得
	    	root2 = root2.getNextSibling();
		}
		
		//全体の走査
        Node child = root.getFirstChild();
		while (true) {
        	//取得できなかったら終わり
        	if (child==null){break;}
	    	if (child.getNodeType()==Node.ELEMENT_NODE) {
	    		//要素名の解析
	            if (child.getNodeName().equals("店番")){
    				set店番(getChildText(child));
	            } else if (child.getNodeName().equals("顧客番号")){
    				set顧客番号(getChildText(child));
	    		} else if (child.getNodeName().equals("科目")){
	    			set科目(getChildText(child));
	    		} else if (child.getNodeName().equals("口座番号")){
	    			set口座番号(getChildText(child));
	    		} else if (child.getNodeName().equals("口座状態")){
    				set口座状態(getChildText(child));
	            } else if (child.getNodeName().equals("商品コード")){
    				set商品コード(getChildText(child));
	    		} else if (child.getNodeName().equals("商品名")){
	    			set商品名(getChildText(child));
	    		} else if (child.getNodeName().equals("積立残高")){
	    			set積立残高(getChildText(child));
	    		} else if (child.getNodeName().equals("毎月積立額")){
	    			set毎月積立額(getChildText(child));
	    		} else if (child.getNodeName().equals("契約日")){
    				set契約日(getChildText(child));
	            } else if (child.getNodeName().equals("預入期限日")){
    				set預入期限日(getChildText(child));
	    		} else if (child.getNodeName().equals("満期日")){
	    			set満期日(getChildText(child));
	    		} else if (child.getNodeName().equals("マル優本人死亡日")){
	    			setマル優本人死亡日(getChildText(child));
	    		} else if (child.getNodeName().equals("支払開始日")){
    				set支払開始日(getChildText(child));
	            } else if (child.getNodeName().equals("移受管日")){
    				set移受管日(getChildText(child));
	    		} else if (child.getNodeName().equals("移受管店番")){
	    			set移受管店番(getChildText(child));
	    		} else if (child.getNodeName().equals("移受管顧客番号")){
	    			set移受管顧客番号(getChildText(child));
	    		} else if (child.getNodeName().equals("移受管口座番号")){
	    			set移受管口座番号(getChildText(child));
	    		}
	            
	    	}
        	//次の子ノードを取得
        	child = child.getNextSibling();
		}
	}
	
	/**
	 * 取得内容チェックメソッド
	 */
	private void checkWebon() throws Exception{
		
		set店番(ConvertUtil.chkConvertNumAdd0(get店番(), 3));
		set顧客番号(ConvertUtil.chkConvertNumAdd0(get顧客番号(), 7));
		set科目(ConvertUtil.chkConvertNumAdd0(get科目(), 2));
		set口座番号(ConvertUtil.chkConvertNumAdd0(get口座番号(), 7));
		set口座状態(ConvertUtil.chkNull(get口座状態()));
		set商品コード(ConvertUtil.chkConvertNumAdd0(get商品コード(),6));
		set商品名(ConvertUtil.chkNull(get商品名()));
		set積立残高(ConvertUtil.chkDelCommaAdd0(get積立残高(), 1));
		set毎月積立額(ConvertUtil.chkDelCommaAdd0(get毎月積立額(), 1));
		//【和暦処理】
		set契約日(ConvertUtil.chkConvertDateAdd0(get契約日()));
		set預入期限日(ConvertUtil.chkConvertDateAdd0(get預入期限日()));
		set満期日(ConvertUtil.chkConvertDateAdd0(get満期日()));
		set最終取扱日(ConvertUtil.chkConvertDateAdd0(get最終取扱日()));
		setマル優本人死亡日(ConvertUtil.chkConvertDateAdd0(getマル優本人死亡日()));
		set支払開始日(ConvertUtil.chkConvertDateAdd0(get支払開始日()));
		set移受管日(ConvertUtil.chkConvertDateAdd0(get移受管日()));
		
		set移受管店番(ConvertUtil.chkConvertNumAdd0(get移受管店番(), 3));
		set移受管顧客番号(ConvertUtil.chkConvertNumAdd0(get移受管顧客番号(), 7));
		set移受管口座番号(ConvertUtil.chkConvertNumAdd0(get移受管口座番号(), 7));
		
	}
	
	//以下UTILITY
	//以下、ユーティリティ的メソッド
	/**
	 * エラー生成メソッド
	 * @param String	エラーメッセージ
	 * @param int		エラーレベル
	 * @param String	エラー箇所
	 */
	private WebonException createWoException(String msg ,int el, String es){
		//エラーコード等をセット
		WebonException e = new WebonException(msg,webonBase);
		//顧客を特定する情報をセット
		e.setOperationId(operationId);
		e.setBrno(woBrno);
		e.setAccno(woAccno);
		e.setErrStat(el);
		e.setErrSpot(es);
		//エラー処理は上位に任せる
		return e;
	}
	/**
	 * 照会名取得メソッド(Static)
	 * 照会名を取得する
	 * 
	 * @return String 照会名
	 */
	public static String getSyokaiName() {
		return syokaiName;
	}
}
