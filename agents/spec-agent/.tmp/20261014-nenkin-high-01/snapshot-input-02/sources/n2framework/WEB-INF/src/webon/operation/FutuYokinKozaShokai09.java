package webon.operation;

import java.sql.Connection;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.w3c.dom.Node;

import webon.WebonBase;
import webon.WebonException;
import webon.util.ConvertUtil;
import webon.util.FixedValue;

import common.bean.LoginInfoBean;

/**
 * Webon汎用照会クラス　　普通預金口座照会０９管理クラス
 * 普通預金口座照会０９(XML)の取得とデータ管理、アクセスメソッドの提供
 * 
 * @author 吉津
 * 
 * @date	2020.04.16		webonのFW化対応
 */
public class FutuYokinKozaShokai09 extends CommonOperation{

	//照会名
	private static final String syokaiName = "普通預金口座照会０９";
	
	//オペレーションＩＤ
	private final String operationId="OP-FUTUKO09-0001";
	//ログイン情報
	LoginInfoBean loginInfo;
	//webon引数
	String woAcc;
	String woBrno;
	
	//Errorレベル
	private static final int ERRLEVEL_ERROR=0;	//Error
	private static final int ERRLEVEL_WARNING=1;	//Warning
	//Error箇所
	private static final String ERRSPOT_WOGET = "0";		//取得時
//	private static final String ERRSPOT_WOANALYZE = "1";	//解析時
	private static final String ERRSPOT_WOMOLD = "2";		//成型時
	//Error追加情報格納用リスト
	List<Map<String, String>> etc = new ArrayList<Map<String,String>>();
	//Error有無フラグ
	boolean errFlg=false;

	//普通預金口座詳細
	 private String 店番 ="";
	 private String 顧客番号 ="";
	 private String 科目 ="";
	 private String 口座番号 ="";
	 private String 口座状態 ="";
	 private String 商品コード ="";
	 private String ＮＢ件数 ="";
	 private String カード発行本人 ="";
	 private String カード発行代理人 ="";
	 private String 年金受取 ="";
	 private String 随時ＣＬ商品コード ="";
	 private String 総合口座 ="";
	 private String スウィング ="";
	 private String 随時ローン ="";
	 private String 定額ローン ="";
	 private String ＡＮＳＥＲ ="";
	 private String ＨＢ ="";
	 private String ＦＢ ="";
	 private String 元帳残高 ="";
	 private String 通帳残高 ="";
	 private String 貸越限度額 ="";
	 private String 経過利息預金利息 ="";
	 private String 経過利息総合口座貸越利息 ="";
	 private String 経過利息カードローン貸越利息 ="";
	 private String 総合未収利息 ="";
	 private String ＣＬ未収利息 ="";
	 private String 最新取引日 ="";
	 private String 年金 ="";
	 private String 移受管日 ="";
	 private String 移受管店 ="";
	 private String 移受管口番 ="";
	 private String コール暗証有 ="";
	 private String 投信契約有 ="";

	//==================================================
	//Getter,Setter
	//==================================================
	public String getWoBrno() {
		return woBrno;
	}
	public void setWoBrno(String woBrno) {
		this.woBrno = woBrno;
	}
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
	public String getWoAcc() {
		return woAcc;
	}
	public void setWoAcc(String woAcc) {
		this.woAcc = woAcc;
	}
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
	public String get年金受取() {
		return 年金受取;
	}
	public void set年金受取(String 年金受取) {
		this.年金受取 = 年金受取;
	}
	public String get総合口座() {
		return 総合口座;
	}
	public void set総合口座(String 総合口座) {
		this.総合口座 = 総合口座;
	}
	public String getスウィング() {
		return スウィング;
	}
	public void setスウィング(String スウィング) {
		this.スウィング = スウィング;
	}
	public String get随時ローン() {
		return 随時ローン;
	}
	public void set随時ローン(String 随時ローン) {
		this.随時ローン = 随時ローン;
	}
	public String get定額ローン() {
		return 定額ローン;
	}
	public void set定額ローン(String 定額ローン) {
		this.定額ローン = 定額ローン;
	}
	public String get元帳残高() {
		return 元帳残高;
	}
	public void set元帳残高(String 元帳残高) {
		this.元帳残高 = 元帳残高;
	}
	public String get通帳残高() {
		return 通帳残高;
	}
	public void set通帳残高(String 通帳残高) {
		this.通帳残高 = 通帳残高;
	}
	public String get貸越限度額() {
		return 貸越限度額;
	}
	public void set貸越限度額(String 貸越限度額) {
		this.貸越限度額 = 貸越限度額;
	}
	public String get経過利息預金利息() {
		return 経過利息預金利息;
	}
	public void set経過利息預金利息(String 経過利息預金利息) {
		this.経過利息預金利息 = 経過利息預金利息;
	}
	public String get経過利息総合口座貸越利息() {
		return 経過利息総合口座貸越利息;
	}
	public void set経過利息総合口座貸越利息(String 経過利息総合口座貸越利息) {
		this.経過利息総合口座貸越利息 = 経過利息総合口座貸越利息;
	}
	public String get経過利息カードローン貸越利息() {
		return 経過利息カードローン貸越利息;
	}
	public void set経過利息カードローン貸越利息(String 経過利息カードローン貸越利息) {
		this.経過利息カードローン貸越利息 = 経過利息カードローン貸越利息;
	}
	public String get総合未収利息() {
		return 総合未収利息;
	}
	public void set総合未収利息(String 総合未収利息) {
		this.総合未収利息 = 総合未収利息;
	}
	public String get最新取引日() {
		return 最新取引日;
	}
	public void set最新取引日(String 最新取引日) {
		this.最新取引日 = 最新取引日;
	}
	public String get年金() {
		return 年金;
	}
	public void set年金(String 年金) {
		this.年金 = 年金;
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
	public String getコール暗証有() {
		return コール暗証有;
	}
	public void setコール暗証有(String コール暗証有) {
		this.コール暗証有 = コール暗証有;
	}
	public String get投信契約有() {
		return 投信契約有;
	}
	public void set投信契約有(String 投信契約有) {
		this.投信契約有 = 投信契約有;
	}
	public String getOperationId() {
		return operationId;
	}
	public String getＮＢ件数() {
		return ＮＢ件数;
	}
	public void setＮＢ件数(String ｎＢ件数) {
		ＮＢ件数 = ｎＢ件数;
	}
	public String get随時ＣＬ商品コード() {
		return 随時ＣＬ商品コード;
	}
	public void set随時ＣＬ商品コード(String 随時ｃｌ商品コード) {
		随時ＣＬ商品コード = 随時ｃｌ商品コード;
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
	public String getＣＬ未収利息() {
		return ＣＬ未収利息;
	}
	public void setＣＬ未収利息(String ｃＬ未収利息) {
		ＣＬ未収利息 = ｃＬ未収利息;
	}
	/**
	 * 店番・口座番号を元に普通預金口座照会を取得する
	 * 
	 * @param acc 口座番号
	 * @param br 店番
	 * @param loginInfo ログイン情報
	 * @param con
	 * @throws Exception
	 */
	public void getWebon(String acc,String br, LoginInfoBean loginInfo, Connection con) throws Exception {
		try{

			//起動チェック 引数がセットされているか
			if (acc == null) {throw new Exception("口座番号が設定されていません");}
			if (br == null) {throw new Exception("原店番号が設定されていません");}
			if (loginInfo == null) {throw new Exception("ログイン情報が設定されていません");}
			if (con == null) {throw new Exception("ＤＢコネクションが設定されていません");}
			
			//引数のセット
			this.woBrno = br;
			this.woAcc = acc;
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
		webonBase.put("口座番号",woAcc);
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
	 * @throws Exception 
	 */
	public void analyzeWeon() throws Exception {
		//WEBON結果走査用固定値
		final String WOKEY_TSUCYO="通帳部宛";				//root
		final String WOKEY_FUTUKOZA="普通預金口座照会";		//root2
		
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
	    		    		if (root2.getNodeName().equals(WOKEY_FUTUKOZA)) {
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
	    		} else if (child.getNodeName().equals("NB件数")){
	    			setＮＢ件数(getChildText(child));
	    		} else if (child.getNodeName().equals("カード発行本人")){
	    			setカード発行本人(getChildText(child));
	    		} else if (child.getNodeName().equals("カード発行代理人")){
	    			setカード発行代理人(getChildText(child));
	    		} else if (child.getNodeName().equals("年金受取")){
	    			set年金受取(getChildText(child));
	    		} else if (child.getNodeName().equals("随時CL商品コード")){
	    			set随時ＣＬ商品コード(getChildText(child));
	    		} else if (child.getNodeName().equals("総合口座")){
	    			set総合口座(getChildText(child));
	    		} else if (child.getNodeName().equals("スウィング")){
	    			setスウィング(getChildText(child));
	    		} else if (child.getNodeName().equals("随時ローン")){
	    			set随時ローン(getChildText(child));
	    		} else if (child.getNodeName().equals("定額ローン")){
	    			set定額ローン(getChildText(child));
	    		} else if (child.getNodeName().equals("ANSER")){
	    			setＡＮＳＥＲ(getChildText(child));
	    		} else if (child.getNodeName().equals("HB")){
	    			setＨＢ(getChildText(child));
	    		} else if (child.getNodeName().equals("FB")){
	    			setＦＢ(getChildText(child));
	    		} else if (child.getNodeName().equals("元帳残高")){
	    			set元帳残高(getChildText(child));
	    		} else if (child.getNodeName().equals("通帳残高")){
	    			set通帳残高(getChildText(child));
	    		} else if (child.getNodeName().equals("貸越限度額")){
	    			set貸越限度額(getChildText(child));
	    		} else if (child.getNodeName().equals("経過利息預金利息")){
	    			set経過利息預金利息(getChildText(child));
	    		} else if (child.getNodeName().equals("経過利息総合口座貸越利息")){
	    			set経過利息総合口座貸越利息(getChildText(child));
	    		} else if (child.getNodeName().equals("経過利息カードローン貸越利息")){
	    			set経過利息カードローン貸越利息(getChildText(child));
	    		} else if (child.getNodeName().equals("総合未収利息")){
	    			set総合未収利息(getChildText(child));
	    		} else if (child.getNodeName().equals("CL未収利息")){
	    			setＣＬ未収利息(getChildText(child));
	    		} else if (child.getNodeName().equals("最新取引日")){
	    			set最新取引日(getChildText(child));
	    		} else if (child.getNodeName().equals("年金")){
	    			set年金(getChildText(child));
	    		} else if (child.getNodeName().equals("移受管日")){
	    			set移受管日(getChildText(child));
	    		} else if (child.getNodeName().equals("移受管店")){
	    			set移受管店(getChildText(child));
	    		} else if (child.getNodeName().equals("移受管口番")){
	    			set移受管口番(getChildText(child));
	    		} else if (child.getNodeName().equals("コール暗証有")){
	    			setコール暗証有(getChildText(child));
	    		} else if (child.getNodeName().equals("投信契約有")){
	    			set投信契約有(getChildText(child));
	    		}
	    	}
        	//次の子ノードを取得
        	child = getNextElement(child);
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
		set商品コード(ConvertUtil.chkConvertNumAdd0(get商品コード(), 6));
		setＮＢ件数(ConvertUtil.chkConvertNumAdd0(getＮＢ件数(), 1));
		setカード発行本人(ConvertUtil.chkNull(getカード発行本人()));
		setカード発行代理人(ConvertUtil.chkNull(getカード発行代理人()));
		set年金受取(ConvertUtil.chkConvertFlag(get年金受取()));
		set随時ＣＬ商品コード(ConvertUtil.chkConvertNumAdd0(get随時ＣＬ商品コード(), 6));
		set総合口座(ConvertUtil.chkConvertFlag(get総合口座()));
		setスウィング(ConvertUtil.chkConvertFlag(getスウィング()));
		set随時ローン(ConvertUtil.chkConvertFlag(get随時ローン()));
		set定額ローン(ConvertUtil.chkConvertFlag(get定額ローン()));
		setＡＮＳＥＲ(ConvertUtil.chkConvertFlag(getＡＮＳＥＲ()));
		setＨＢ(ConvertUtil.chkConvertFlag(getＨＢ()));
		setＦＢ(ConvertUtil.chkConvertFlag(getＦＢ()));
		set元帳残高(ConvertUtil.chkDelCommaAdd0(get元帳残高(), 1));
		set通帳残高(ConvertUtil.chkDelCommaAdd0(get通帳残高(), 1));
		set貸越限度額(ConvertUtil.chkDelCommaAdd0(get貸越限度額(), 1));
		set経過利息預金利息(ConvertUtil.chkConvertRate(get経過利息預金利息(),3,1));
		set経過利息総合口座貸越利息(ConvertUtil.chkConvertRate(get経過利息総合口座貸越利息(),3,1));
		set経過利息カードローン貸越利息(ConvertUtil.chkConvertRate(get経過利息カードローン貸越利息(),3,1));
		set総合未収利息(ConvertUtil.chkConvertNumAdd0(get総合未収利息(), 1));
		setＣＬ未収利息(ConvertUtil.chkConvertNumAdd0(getＣＬ未収利息(), 1));
		//【和暦処理】
		set最新取引日(ConvertUtil.chkConvertDateAdd0(get最新取引日()));
		set年金(ConvertUtil.chkConvertFlag(get年金()));
		//【和暦処理】
		set移受管日(ConvertUtil.chkConvertDateAdd0(get移受管日()));
		set移受管店(ConvertUtil.chkConvertNumAdd0(get移受管店(), 3));
		set移受管口番(ConvertUtil.chkConvertNumAdd0(get移受管口番(), 7));
		setコール暗証有(ConvertUtil.chkConvertFlag(getコール暗証有()));
		set投信契約有(ConvertUtil.chkConvertFlag(get投信契約有()));
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
		e.setAccno(woAcc);
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
