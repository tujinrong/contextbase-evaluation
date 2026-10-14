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
 * Webon汎用照会クラス　定期預金口座照会管理クラス
 * 定期預金口座照会(XML)の取得とデータ管理、アクセスメソッドの提供
 * 
 * @author	富永
 * 
 * @date	2020.04.02	新規作成
 */
public class TeikiYokinKozaSyokai extends CommonOperation {
	
	private static final String syokaiName = "定期預金口座照会";
	
	//オペレーションＩＤ
	private final String operationId="OP-TEKIKOZA-0001";
	//ログイン情報
	LoginInfoBean loginInfo;
	//webon引数
	String woAccno;
	String woYonyu;
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
	
	//getter,setter
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
	public LoginInfoBean getLoginInfo() {
		return loginInfo;
	}
	public void setLoginInfo(LoginInfoBean loginInfo) {
		this.loginInfo = loginInfo;
	}
	public String getWoAccno() {
		return woAccno;
	}
	public void setWoAccno(String woAccno) {
		this.woAccno = woAccno;
	}
	public String getWoYonyu() {
		return woYonyu;
	}
	public void setWoYonyu(String woYonyu) {
		this.woYonyu = woYonyu;
	}
	public String getWoBrno() {
		return woBrno;
	}
	public void setWoBrno(String woBrno) {
		this.woBrno = woBrno;
	}
	
	//=== 定期預金口座照会 ===
	
	//取得結果
	String 店番="";
	String 顧客番号="";
	String 科目="";
	String 口座番号="";
	String 入金番号="";
	String 口座状態="";
	String 元帳残高="";
	String 解約残高="";
	String 移受管店番="";
	String 移受管口座番号="";
	String 移受管日="";
	String 総合口座科目="";
	String 総合口座口座番号="";
	String 現在残高="";
	String 預入日="";
	String 満期日="";
	String 預入期間="";
	String 当初預入日="";
	String 商品コード="";
	String 商品名="";
	String 預金利率="";
	String マル優分かち情報相続前課税適用="";
	String マル優分かち情報本人死亡日="";
	String マル優分かち情報相続前課税="";
	String マル優分かち情報相続前子課税="";
	String 次回利払日="";
	
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
	public String get入金番号() {
		return 入金番号;
	}
	public void set入金番号(String 入金番号) {
		this.入金番号 = 入金番号;
	}
	public String get口座状態() {
		return 口座状態;
	}
	public void set口座状態(String 口座状態) {
		this.口座状態 = 口座状態;
	}
	public String get元帳残高() {
		return 元帳残高;
	}
	public void set元帳残高(String 元帳残高) {
		this.元帳残高 = 元帳残高;
	}
	public String get解約残高() {
		return 解約残高;
	}
	public void set解約残高(String 解約残高) {
		this.解約残高 = 解約残高;
	}
	public String get移受管店番() {
		return 移受管店番;
	}
	public void set移受管店番(String 移受管店番) {
		this.移受管店番 = 移受管店番;
	}
	public String get移受管口座番号() {
		return 移受管口座番号;
	}
	public void set移受管口座番号(String 移受管口座番号) {
		this.移受管口座番号 = 移受管口座番号;
	}
	public String get移受管日() {
		return 移受管日;
	}
	public void set移受管日(String 移受管日) {
		this.移受管日 = 移受管日;
	}
	public String get総合口座科目() {
		return 総合口座科目;
	}
	public void set総合口座科目(String 総合口座科目) {
		this.総合口座科目 = 総合口座科目;
	}
	public String get総合口座口座番号() {
		return 総合口座口座番号;
	}
	public void set総合口座口座番号(String 総合口座口座番号) {
		this.総合口座口座番号 = 総合口座口座番号;
	}
	public String get現在残高() {
		return 現在残高;
	}
	public void set現在残高(String 現在残高) {
		this.現在残高 = 現在残高;
	}
	public String get預入日() {
		return 預入日;
	}
	public void set預入日(String 預入日) {
		this.預入日 = 預入日;
	}
	public String get満期日() {
		return 満期日;
	}
	public void set満期日(String 満期日) {
		this.満期日 = 満期日;
	}
	public String get預入期間() {
		return 預入期間;
	}
	public void set預入期間(String 預入期間) {
		this.預入期間 = 預入期間;
	}
	public String get当初預入日() {
		return 当初預入日;
	}
	public void set当初預入日(String 当初預入日) {
		this.当初預入日 = 当初預入日;
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
	public String get預金利率() {
		return 預金利率;
	}
	public void set預金利率(String 預金利率) {
		this.預金利率 = 預金利率;
	}
	public String getマル優分かち情報相続前課税適用() {
		return マル優分かち情報相続前課税適用;
	}
	public void setマル優分かち情報相続前課税適用(String マル優分かち情報相続前課税適用) {
		this.マル優分かち情報相続前課税適用 = マル優分かち情報相続前課税適用;
	}
	public String getマル優分かち情報本人死亡日() {
		return マル優分かち情報本人死亡日;
	}
	public void setマル優分かち情報本人死亡日(String マル優分かち情報本人死亡日) {
		this.マル優分かち情報本人死亡日 = マル優分かち情報本人死亡日;
	}
	public String getマル優分かち情報相続前課税() {
		return マル優分かち情報相続前課税;
	}
	public void setマル優分かち情報相続前課税(String マル優分かち情報相続前課税) {
		this.マル優分かち情報相続前課税 = マル優分かち情報相続前課税;
	}
	public String getマル優分かち情報相続前子課税() {
		return マル優分かち情報相続前子課税;
	}
	public void setマル優分かち情報相続前子課税(String マル優分かち情報相続前子課税) {
		this.マル優分かち情報相続前子課税 = マル優分かち情報相続前子課税;
	}
	public String get次回利払日() {
		return 次回利払日;
	}
	public void set次回利払日(String 次回利払日) {
		this.次回利払日 = 次回利払日;
	}
	
	/**
	 * 預入番号・口座番号・店番を元に定期預金口座照会を取得する
	 * 
	 * @param accno 口座番号
	 * @param br 店番
	 * @param yonyuno 預入番号
	 * @param 解約残高 kaiyakuZandaka 
	 * 
	 * @param loginInfo ログイン情報
	 * @param con
	 * @throws Exception
	 */
	public void getWebon( String accno, String br, String yonyuno, String kaiyakuZandaka, LoginInfoBean loginInfo, Connection con) throws Exception {
		try{
			//引数チェック 引数がセットされているか
			if (accno == null) {throw new Exception("口座番号が設定されていません");}
			if (br == null) {throw new Exception("原店番号が設定されていません");}
			if (con == null) {throw new Exception("ＤＢコネクションが設定されていません");}
			
			//引数のセット
			this.woAccno=accno;
			this.woBrno=br;
			this.loginInfo = loginInfo;
			
			//起動チェック 入金番号がセットされているか
			if (yonyuno == null) {throw new Exception("預入番号が設定されていません");}
			//入金番号チェック(0は空白に置き換える)
			if(yonyuno.equals("0")||yonyuno.equals("00")){
				woYonyu="";
			}else{
				this.woYonyu=yonyuno;
			}
			//Webon問合せ実行
			getWebon(con);
			
			//取得結果解析
			analyzeWeon();
			
			//解約残高（定期預金入金明細照会の値）をセット
			set解約残高(ConvertUtil.chkConvertFlag(kaiyakuZandaka));
			
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
		webonBase.put("預入番号",woYonyu);
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
		final String WOKEY_TEIKIKOZA="定期預金口座照会";
		//final String WOKEY_ROOP="明細行";
		
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
	    		    		if (root.getNodeName().equals(WOKEY_TEIKIKOZA)) {
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
		//HashMap<String,String> map = new HashMap<String,String>();
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
	    		}else if (child.getNodeName().equals("入金番号")){
	    			set入金番号(getChildText(child));
	    		}else if (child.getNodeName().equals("口座状態")){
	    			set口座状態(getChildText(child));
	    		} else if (child.getNodeName().equals("元帳残高")){
    				set元帳残高(getChildText(child));
	            } else if (child.getNodeName().equals("移受管店番")){
    				set移受管店番(getChildText(child));
	    		} else if (child.getNodeName().equals("移受管口座番号")){
	    			set移受管口座番号(getChildText(child));
	    		} else if (child.getNodeName().equals("移受管日")){
	    			set移受管日(getChildText(child));
	    		} else if (child.getNodeName().equals("総合口座科目")){
	    			set総合口座科目(getChildText(child));
	    		} else if (child.getNodeName().equals("総合口座口座番号")){
	    			set総合口座口座番号(getChildText(child));
	    		} else if (child.getNodeName().equals("現在残高")){
	    			set現在残高(getChildText(child));
	    		} else if (child.getNodeName().equals("預入日")){
    				set預入日(getChildText(child));
	            } else if (child.getNodeName().equals("満期日")){
    				set満期日(getChildText(child));
	    		} else if (child.getNodeName().equals("預入期間")){
	    			set預入期間(getChildText(child));
	    		} else if (child.getNodeName().equals("当初預入日")){
	    			set当初預入日(getChildText(child));
	    		} else if (child.getNodeName().equals("商品コード")){
	    			set商品コード(getChildText(child));
	    		} else if (child.getNodeName().equals("商品名")){
	    			set商品名(getChildText(child));
	    		} else if (child.getNodeName().equals("預金利率")){
	    			set預金利率(getChildText(child));
	    		} else if (child.getNodeName().equals("マル優分かち情報相続前課税適用")){
	    			setマル優分かち情報相続前課税適用(getChildText(child));
	    		} else if (child.getNodeName().equals("マル優分かち情報本人死亡日")){
	    			setマル優分かち情報本人死亡日(getChildText(child));
	    		} else if (child.getNodeName().equals("マル優分かち情報相続前課税")){
    				setマル優分かち情報相続前課税(getChildText(child));
	            } else if (child.getNodeName().equals("マル優分かち情報相続前子課税")){
    				setマル優分かち情報相続前子課税(getChildText(child));
	    		} else if (child.getNodeName().equals("次回利払日")){
	    			set次回利払日(getChildText(child));
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
		set入金番号(ConvertUtil.chkConvertNumAdd0(get入金番号(), 2));
		set口座状態(ConvertUtil.chkNull(get口座状態()));
		set元帳残高(ConvertUtil.chkDelCommaAdd0(get元帳残高(),1));
		set移受管店番(ConvertUtil.chkConvertNumAdd0(get移受管店番(), 3));
		set移受管口座番号(ConvertUtil.chkConvertNumAdd0(get移受管口座番号(), 7));
		set移受管店番(ConvertUtil.chkConvertNumAdd0(get移受管店番(), 3));
		set総合口座科目(ConvertUtil.chkConvertNumAdd0(get総合口座科目(), 2));
		set総合口座口座番号(ConvertUtil.chkConvertNumAdd0(get総合口座口座番号(), 7));
		set現在残高(ConvertUtil.chkDelCommaAdd0(get現在残高(), 1));
		set預入日(ConvertUtil.chkConvertDateAdd0(get預入日()));
		set満期日(ConvertUtil.chkConvertDateAdd0(get満期日()));
		set預入期間(ConvertUtil.chkNull(get預入期間()));
		set当初預入日(ConvertUtil.chkConvertDateAdd0(get当初預入日()));
		set商品コード(ConvertUtil.chkConvertNumAdd0(get商品コード(), 6));
		set商品名(ConvertUtil.chkNull(get商品名()));
		set預金利率(ConvertUtil.chkConvertRate(get預金利率(),3,8));
		setマル優分かち情報相続前課税適用(ConvertUtil.chkConvertFlag(getマル優分かち情報相続前課税適用()));
		setマル優分かち情報本人死亡日(ConvertUtil.chkConvertDateAdd0(getマル優分かち情報本人死亡日()));
		setマル優分かち情報相続前課税(ConvertUtil.chkNull(getマル優分かち情報相続前課税()));
		setマル優分かち情報相続前子課税(ConvertUtil.chkNull(getマル優分かち情報相続前子課税()));
		set次回利払日(ConvertUtil.chkConvertDateAdd0(get次回利払日()));
		
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