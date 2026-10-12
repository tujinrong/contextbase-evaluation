package webon.operation;

import java.sql.Connection;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.w3c.dom.Node;

import webon.WebonBase;
import webon.WebonException;
import webon.util.ConvertUtil;
import webon.util.FixedValue;

import common.bean.LoginInfoBean;

/**
 * Webon汎用照会クラス　当座勘定照会管理クラス
 * 当座勘定照会(XML)の取得とデータ管理、アクセスメソッドの提供
 * 
 * @author	富永
 * 
 * @date	2020.03.27	新規作成
 */
public class TozaKanjoKozaShokai extends CommonOperation {
	
	private static final String syokaiName = "当座勘定口座照会";

	//オペレーションＩＤ
	private final String operationId="OP-TOZAKOZA-0001";
	//ログイン情報
	LoginInfoBean loginInfo;
	//webon引数
	String woKoza;
	String woBrno;
	
	//Errorレベル
	private static final int ERRLEVEL_ERROR=0;	//Error
	private static final int ERRLEVEL_WARNING=1;	//Warning
	//Error箇所
	private static final String ERRSPOT_WOGET = "0";		//取得時
	private static final String ERRSPOT_WOANALYZE = "1";	//解析時
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
	public WebonBase getWebonBase() {
		return webonBase;
	}
	public void setWebonBase(WebonBase webonBase) {
		this.webonBase = webonBase;
	}
	
	public LoginInfoBean getLoginInfo() {
		return loginInfo;
	}
	public void setLoginInfo(LoginInfoBean loginInfo) {
		this.loginInfo = loginInfo;
	}
	public String getWoBrno() {
		return woBrno;
	}
	public void setWoBrno(String woBrno) {
		this.woBrno = woBrno;
	}
	public String getWoKoza() {
		return woKoza;
	}
	public void setWoKoza(String woKoza) {
		this.woKoza = woKoza;
	}
	
	//=== 当座勘定口座照会 ===
	//取得結果
	String 店番="";
	String 顧客番号="";
	String 科目="";
	String 口座番号="";
	String 種類="";
	String 口座区分="";
	String 口座状態="";
	String 通帳冊数="";
	String ＡＮＳＥＲ="";
	String ＨＢ="";
	String ＦＢ="";
	String ＩＢ="";
	String コール暗証有="";
	String 当貸契約="";
	String 当貸契約期限="";
	String 元帳残高="";
	String 貸越極度額合計="";
	String 経過貸越利息="";
	String 未収貸越利息="";
	String 経過損害金="";
	String 元帳損害金="";
	String 未収損害金="";
	String 最新取引日="";
	String 移受管日="";
	String 移受管店="";
	String 移受管口番="";
	String カード発行本人="";
	String カード発行代理人="";
	
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
	public String get種類() {
		return 種類;
	}
	public void set種類(String 種類) {
		this.種類 = 種類;
	}
	public String get口座区分() {
		return 口座区分;
	}
	public void set口座区分(String 口座区分) {
		this.口座区分 = 口座区分;
	}
	public String get口座状態() {
		return 口座状態;
	}
	public void set口座状態(String 口座状態) {
		this.口座状態 = 口座状態;
	}
	public String get通帳冊数() {
		return 通帳冊数;
	}
	public void set通帳冊数(String 通帳冊数) {
		this.通帳冊数 = 通帳冊数;
	}
	public String getＡＮＳＥＲ() {
		return ＡＮＳＥＲ;
	}
	public void setＡＮＳＥＲ(String ａＮＳＥＲ) {
		ＡＮＳＥＲ = ａＮＳＥＲ;
	}
	public String getＨＢ() {
		return ＨＢ;
	}
	public void setＨＢ(String ｈＢ) {
		ＨＢ = ｈＢ;
	}
	public String getＦＢ() {
		return ＦＢ;
	}
	public void setＦＢ(String ｆＢ) {
		ＦＢ = ｆＢ;
	}
	public String getＩＢ() {
		return ＩＢ;
	}
	public void setＩＢ(String ｉＢ) {
		ＩＢ = ｉＢ;
	}
	public String getコール暗証有() {
		return コール暗証有;
	}
	public void setコール暗証有(String コール暗証有) {
		this.コール暗証有 = コール暗証有;
	}
	public String get当貸契約() {
		return 当貸契約;
	}
	public void set当貸契約(String 当貸契約) {
		this.当貸契約 = 当貸契約;
	}
	public String get当貸契約期限() {
		return 当貸契約期限;
	}
	public void set当貸契約期限(String 当貸契約期限) {
		this.当貸契約期限 = 当貸契約期限;
	}
	public String get元帳残高() {
		return 元帳残高;
	}
	public void set元帳残高(String 元帳残高) {
		this.元帳残高 = 元帳残高;
	}
	public String get貸越極度額合計() {
		return 貸越極度額合計;
	}
	public void set貸越極度額合計(String 貸越極度額合計) {
		this.貸越極度額合計 = 貸越極度額合計;
	}
	public String get経過貸越利息() {
		return 経過貸越利息;
	}
	public void set経過貸越利息(String 経過貸越利息) {
		this.経過貸越利息 = 経過貸越利息;
	}
	public String get未収貸越利息() {
		return 未収貸越利息;
	}
	public void set未収貸越利息(String 未収貸越利息) {
		this.未収貸越利息 = 未収貸越利息;
	}
	public String get経過損害金() {
		return 経過損害金;
	}
	public void set経過損害金(String 経過損害金) {
		this.経過損害金 = 経過損害金;
	}
	public String get元帳損害金() {
		return 元帳損害金;
	}
	public void set元帳損害金(String 元帳損害金) {
		this.元帳損害金 = 元帳損害金;
	}
	public String get未収損害金() {
		return 未収損害金;
	}
	public void set未収損害金(String 未収損害金) {
		this.未収損害金 = 未収損害金;
	}
	public String get最新取引日() {
		return 最新取引日;
	}
	public void set最新取引日(String 最新取引日) {
		this.最新取引日 = 最新取引日;
	}
	public String get移受管日() {
		return 移受管日;
	}
	public void set移受管日(String 移受管日) {
		this.移受管日 = 移受管日;
	}
	public String get移受管店() {
		return 移受管店;
	}
	public void set移受管店(String 移受管店) {
		this.移受管店 = 移受管店;
	}
	public String get移受管口番() {
		return 移受管口番;
	}
	public void set移受管口番(String 移受管口番) {
		this.移受管口番 = 移受管口番;
	}
	public String getカード発行本人() {
		return カード発行本人;
	}
	public void setカード発行本人(String カード発行本人) {
		this.カード発行本人 = カード発行本人;
	}
	public String getカード発行代理人() {
		return カード発行代理人;
	}
	public void setカード発行代理人(String カード発行代理人) {
		this.カード発行代理人 = カード発行代理人;
	}
	/**
	 * 店番・口座番号を元に当座勘定口座照会を取得する
	 * 	 
	 * @param koza 口座番号
	 * @param br 店番
	 * @param loginInfo ログイン情報
	 * @param con
	 * @throws Exception
	 */
	public void getWebon(String koza, String br, LoginInfoBean loginInfo, Connection con) throws Exception {
		try{
			//起動チェック 引数がセットされているか
			if (koza == null) {throw new Exception("口座番号が設定されていません");}
			if (br == null) {throw new Exception("原店番号が設定されていません");}
			if (con == null) {throw new Exception("ＤＢコネクションが設定されていません");}
			
			//引数のセット
			this.woBrno=br;
			this.woKoza=koza;
			this.loginInfo = loginInfo;
			
			//Webon問合せ実行
			getWebon(con);
			
			//取得結果解析
			analyzeWeon();
			
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
		
		//設定値（必須項目は事前チェックしてあることが前提）
		webonBase.put("口座番号",woKoza);
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
		final String WOKEY_TSUCYO="通帳部宛";		//これがroot
		final String WOKEY_TOZA="当座勘定口座照会";	//これがroot2
		final String DBKEY_CUSTNO="顧客番号";
		final String DBKEY_BRANCHNO="店番";
		
		//結果取得
		Node editData = webonBase.getEditData();
		//結果解析
		//データの最上位ノードを取得(もうちょっと精査要)
		Node root=editData.getFirstChild();
		Node root2=null;
//		while (true) {
		for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
        	//取得できなかったら終わり
        	if (root==null){break;}
	    	if (root.getNodeType()==Node.ELEMENT_NODE) {
	    		//要素名の解析
	    		if (root.getNodeName().equals(WOKEY_TSUCYO)) {
	    			root2 = root.getFirstChild();
//	    			while (true) {
	    			for (int roopCount2=0;roopCount2<FixedValue.SYS_WBNUMLIMIT;roopCount2++){
	    	        	//取得できなかったら終わり
	    	        	if (root2==null){break;}
	    		    	if (root2.getNodeType()==Node.ELEMENT_NODE) {
	    		    		//要素名の解析
	    		    		if (root2.getNodeName().equals(WOKEY_TOZA)) {
	    		    			break;
	    		            }
	    		    	}
	    	        	//次の子ノードを取得
	    		    	root2 = root.getNextSibling();
	    			}
	    			break;
	            } 
	    	}
        	//次の子ノードを取得
	    	root = root.getNextSibling();
		}
		//全体の走査
        Node child = root2.getFirstChild();
//		while (true) {
		for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
        	//取得できなかったら終わり
        	if (child==null){break;}
	    	if (child.getNodeType()==Node.ELEMENT_NODE) {
	    		//要素名の解析
	            if (child.getNodeName().equals(DBKEY_BRANCHNO)){
	    			//必須チェック
	    			if(!getChildText(child).equals("")){
	    				set店番(getChildText(child));
	    			}else{
	    				WebonException e = createWoException("Webon取得結果解析エラー", ERRLEVEL_ERROR, ERRSPOT_WOANALYZE);
	    				//エラー項目のセット
	    				Map<String, String>map = new HashMap<String, String>();
	    				map.put("店番", null);
	    				etc.add(map);
	    				e.setEtc(etc);
	    				//エラー処理は上位に任せる
	    				throw e;
	    			}
	            } else if (child.getNodeName().equals(DBKEY_CUSTNO)){
	    			//必須チェック
	    			if(!getChildText(child).equals("")){
	    				set顧客番号(getChildText(child));
	    			}else{
	    				WebonException e = createWoException("Webon取得結果解析エラー", ERRLEVEL_ERROR, ERRSPOT_WOANALYZE);
	    				//エラー項目のセット
	    				Map<String, String>map = new HashMap<String, String>();
	    				map.put("顧客番号", null);
	    				etc.add(map);
	    				e.setEtc(etc);
	    				//エラー処理は上位に任せる
	    				throw e;
	    			}
	            } else if (child.getNodeName().equals("科目")){
	            	set科目(getChildText(child));
	            } else if (child.getNodeName().equals("口座番号")){
	            	set口座番号(getChildText(child));
	            } else if (child.getNodeName().equals("種類")){
	            	set種類(getChildText(child));
	            } else if (child.getNodeName().equals("口座区分")){
	            	set口座区分(getChildText(child));
	            } else if (child.getNodeName().equals("口座状態")){
	            	set口座状態(getChildText(child));
	            } else if (child.getNodeName().equals("通帳冊数")){
	            	set通帳冊数(getChildText(child));
	            } else if (child.getNodeName().equals("ANSER")){
	            	setＡＮＳＥＲ(getChildText(child));
	            } else if (child.getNodeName().equals("HB")){
	            	setＨＢ(getChildText(child));
	            } else if (child.getNodeName().equals("FB")){
	            	setＦＢ(getChildText(child));
	            } else if (child.getNodeName().equals("IB")){
	            	setＩＢ(getChildText(child));
	            } else if (child.getNodeName().equals("コール暗証有")){
	            	setコール暗証有(getChildText(child));
	            } else if (child.getNodeName().equals("当貸契約")){
	            	set当貸契約(getChildText(child));
	            } else if (child.getNodeName().equals("当貸契約期限")){
	            	set当貸契約期限(getChildText(child));
	            } else if (child.getNodeName().equals("元帳残高")){
	            	set元帳残高(getChildText(child));
	            } else if (child.getNodeName().equals("貸越極度額合計")){
	            	set貸越極度額合計(getChildText(child));
	            } else if (child.getNodeName().equals("経過貸越利息")){
	            	set経過貸越利息(getChildText(child));
	            } else if (child.getNodeName().equals("未収貸越利息")){
	            	set未収貸越利息(getChildText(child));
	            } else if (child.getNodeName().equals("経過損害金")){
	            	set経過損害金(getChildText(child));
	            } else if (child.getNodeName().equals("元帳損害金")){
	            	set元帳損害金(getChildText(child));
	            } else if (child.getNodeName().equals("未収損害金")){
	            	set未収損害金(getChildText(child));
	            } else if (child.getNodeName().equals("最新取引日")){
	            	set最新取引日(getChildText(child));
	            } else if (child.getNodeName().equals("移受管日")){
	            	set移受管日(getChildText(child));
	            } else if (child.getNodeName().equals("移受管店")){
	            	set移受管店(getChildText(child));
	            } else if (child.getNodeName().equals("移受管口番")){
	            	set移受管口番(getChildText(child));
	            } else if (child.getNodeName().equals("カード発行本人")){
	            	setカード発行本人(getChildText(child));
	            } else if (child.getNodeName().equals("カード発行代理人")){
	            	setカード発行代理人(getChildText(child));
	            }
	    	}
        	//次の子ノードを取得
        	child = getNextElement(child);
		}
		
		//取得項目のチェック
		checkWebon();
		
		//エラーチェック(Exceptionの有無を判定する)
		if(errFlg){
			WebonException e = createWoException("Webon取得結果解析エラー", ERRLEVEL_WARNING, ERRSPOT_WOMOLD);
			e.setEtc(etc);
			//エラー処理は上位に任せる
			throw e;
		}
	}
	/**
	 * 取得内容チェックメソッド
	 */
	private void checkWebon(){
		
		set店番(ConvertUtil.chkConvertNumAdd0(get店番(),3));
		set顧客番号(ConvertUtil.chkConvertNumAdd0(get顧客番号(),7));
		set科目(ConvertUtil.chkConvertNumAdd0(get科目(),2));
		set口座番号(ConvertUtil.chkConvertNumAdd0(get口座番号(),7));
		set種類(ConvertUtil.chkConvertNumAdd0(get種類(),1));
		set口座区分(ConvertUtil.chkConvertNumAdd0(get口座区分(),2));
		set口座状態(ConvertUtil.chkNull(get口座状態()));
		set通帳冊数(ConvertUtil.chkConvertNumAdd0(get通帳冊数(),3));
		setＡＮＳＥＲ(ConvertUtil.chkNull(getＡＮＳＥＲ()));
		setＨＢ(ConvertUtil.chkConvertFlag(getＨＢ()));
		setＦＢ(ConvertUtil.chkNull(getＦＢ()));
		setＩＢ(ConvertUtil.chkConvertFlag(getＩＢ()));
		setコール暗証有(ConvertUtil.chkConvertFlag(getコール暗証有()));
		set当貸契約(ConvertUtil.chkConvertFlag(get当貸契約()));
		set当貸契約期限(ConvertUtil.chkConvertDateAdd0(get当貸契約期限()));
		set元帳残高(ConvertUtil.chkDelCommaAdd0(get元帳残高(),13));
		set貸越極度額合計(ConvertUtil.chkDelCommaAdd0(get貸越極度額合計(),13));
		set経過貸越利息(ConvertUtil.chkConvertRate(ConvertUtil.chkDelCommaAdd0(get経過貸越利息(),11),3,11));
		set未収貸越利息(ConvertUtil.chkDelCommaAdd0(get未収貸越利息(),11));
		set経過損害金(ConvertUtil.chkConvertRate(ConvertUtil.chkDelCommaAdd0(get経過損害金(),13),3,13));
		set元帳損害金(ConvertUtil.chkDelCommaAdd0(get元帳損害金(),13));
		set未収損害金(ConvertUtil.chkConvertRate(ConvertUtil.chkDelCommaAdd0(get未収損害金(),13),3,13));
		set最新取引日(ConvertUtil.chkConvertDateAdd0(get最新取引日()));
		set移受管日(ConvertUtil.chkConvertDateAdd0(get移受管日()));
		set移受管店(ConvertUtil.chkConvertNumAdd0(get移受管店(),3));
		set移受管口番(ConvertUtil.chkConvertNumAdd0(get移受管口番(),7));
		setカード発行本人(ConvertUtil.chkNull(getカード発行本人()));
		setカード発行代理人(ConvertUtil.chkNull(getカード発行代理人()));
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
//		e.setCif(woCif);
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
