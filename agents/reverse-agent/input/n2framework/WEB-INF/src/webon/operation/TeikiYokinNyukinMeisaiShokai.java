package webon.operation;

import java.sql.Connection;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import org.w3c.dom.Node;
import common.bean.LoginInfoBean;

import webon.WebonBase;
import webon.WebonException;
import webon.util.FixedValue;
import webon.util.ConvertUtil;

/**
 * Webon汎用照会クラス　定期預金入金明細照会管理クラス
 * 定期預金入金明細照会(XML)の取得とデータ管理、アクセスメソッドの提供
 * 
 * @author	富永
 * 
 * @date	2020.04.02	新規作成
 */
public class TeikiYokinNyukinMeisaiShokai extends CommonOperation {

	private static final String syokaiName = "定期預金入金明細照会";
	
	//オペレーションＩＤ(未設定)
	private final String operationId="OP-TEKMESAI-0001";
	//ログイン情報
	LoginInfoBean loginInfo;
	//webon引数
	String woAccno;
	String woShokaiDay;
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
	public String getWoShokaiDay() {
		return woShokaiDay;
	}
	public void setWoShokaiDay(String woShokaiDay) {
		this.woShokaiDay = woShokaiDay;
	}
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
	
	//=== 定期預金入金明細照会 ===

	//定期預金入金明細（共通項目）
	String 店舗番号="";
	String 顧客番号="";
	String 科目="";
	String 口座番号="";
	String 口座状態="";
	String 元帳残高="";
	
	//定期預金入金明細リスト(保持するのみ)
	List<TeikiYokinBean> teikiYokinList = new ArrayList<TeikiYokinBean>();
	
	//setter,getter
	public List<TeikiYokinBean> getTeikiYokinList() {
		return teikiYokinList;
	}
	public void setTeikiYokinList(List<TeikiYokinBean> teikiYokinList) {
		this.teikiYokinList = teikiYokinList;
	}
	public String get店舗番号() {
		return 店舗番号;
	}
	public void set店舗番号(String 店舗番号) {
		this.店舗番号 = 店舗番号;
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
	public String get元帳残高() {
		return 元帳残高;
	}
	public void set元帳残高(String 元帳残高) {
		this.元帳残高 = 元帳残高;
	}
	
	//定期預金入金明細（個別項目）
	public class TeikiYokinBean{
		//預入情報
		String 入金番号="";
		String 解約残高="";
		String 現在残高="";
		String 預入日="";
		String 満期日="";
		//値は取得するが、ＤＢには格納・保持しない項目
		String 解約日ハイフン="";
		String 預入日ハイフン="";
		String 子定期金額="";
		
		//getter,setter
		public String get入金番号() {
			return 入金番号;
		}
		public void set入金番号(String 入金番号) {
			this.入金番号 = 入金番号;
		}
		public String get解約残高() {
			return 解約残高;
		}
		public void set解約残高(String 解約残高) {
			this.解約残高 = 解約残高;
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
		public String get解約日ハイフン() {
			return 解約日ハイフン;
		}
		public void set解約日ハイフン(String 解約日ハイフン) {
			this.解約日ハイフン = 解約日ハイフン;
		}
		public String get預入日ハイフン() {
			return 預入日ハイフン;
		}
		public void set預入日ハイフン(String 預入日ハイフン) {
			this.預入日ハイフン = 預入日ハイフン;
		}
		public String get子定期金額() {
			return 子定期金額;
		}
		public void set子定期金額(String 子定期金額) {
			this.子定期金額 = 子定期金額;
		}
	}
	
	/**
	 * 預入番号・口座番号・店番を元に定期預金口座照会を取得する
	 * 
	 * @param accno 口座番号
	 * @param startDay 照会開始日		
	 * @param br 店番
	 * @param loginInfo ログイン情報
	 * @param con
	 * @throws Exception
	 */
	public void getWebon(String accno, String shokaiDay, String br, LoginInfoBean loginInfo, Connection con) throws Exception {
		try{
			//引数チェック 引数がセットされているか
			if (accno == null) {throw new Exception("口座番号が設定されていません");}
			if (shokaiDay == null) {throw new Exception("照会日が設定されていません");}
			if (br == null) {throw new Exception("原店番号が設定されていません");}
			if (con == null) {throw new Exception("ＤＢコネクションが設定されていません");}
			this.woAccno=accno;
			this.woShokaiDay=shokaiDay;
			this.woBrno=br;
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
		//設定値
		webonBase.put("口座番号",woAccno);
		webonBase.put("照会開始日",woShokaiDay);
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
		final String WOKEY_TEIKIMEISAI="定期預金入金明細照会";
		final String WOKEY_ROOP="預入明細";

		//結果取得
		Node editData = webonBase.getEditData();
		//結果解析
		//データの最上位ノードを取得
		Node root2=editData.getFirstChild();
		Node root=null;
		//while (true) {
		for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
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
	    		    		if (root.getNodeName().equals(WOKEY_TEIKIMEISAI)) {
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
        ArrayList<Node> loopNodes = new ArrayList<Node>();
        Node child = root.getFirstChild();
//			while (true) {
		for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
        	//取得できなかったら終わり
        	if (child==null){break;}
	    	if (child.getNodeType()==Node.ELEMENT_NODE) {
	    		//要素名の解析
	    		//ループ対象行
	    		if (child.getNodeName().equals(WOKEY_ROOP)) {
	    			loopNodes.add(child);
	            //ループ対象行以外
	            } else if (child.getNodeName().equals("店舗番号")){
	            	set店舗番号(getChildText(child));
	            } else if (child.getNodeName().equals("顧客番号")){
	            	set顧客番号(getChildText(child));
	            } else if (child.getNodeName().equals("科目")){
	            	set科目(getChildText(child));
	            } else if (child.getNodeName().equals("口座番号")){
	            	set口座番号(getChildText(child));
	            } else if (child.getNodeName().equals("口座状態")){
	            	set口座状態(getChildText(child));
	            } else if (child.getNodeName().equals("元帳残高")){
	            	set元帳残高(getChildText(child));
	            }
	        }
        	//次の子ノードを取得
        	child = child.getNextSibling();
		}
		
		//ループ行の走査＆値のセット
		for (int j=0; j<loopNodes.size(); j++ ) {
			//ループの要素を取り出し
			Node elem=loopNodes.get(j).getFirstChild();
			//データ格納用ビーンの生成
			TeikiYokinBean bean = new TeikiYokinBean();
			//while (true) {
			for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
		       	if (elem==null){break;}
		    	if (elem.getNodeType()==Node.ELEMENT_NODE) {
		    		//ノードの情報を取得
					if(elem.getNodeName().equals("入金番号")){
						bean.set入金番号(getChildText(elem));
					}else if(elem.getNodeName().equals("解約残高")){
						bean.set解約残高(getChildText(elem));						
					}else if(elem.getNodeName().equals("現在残高")){
						bean.set現在残高(getChildText(elem));						
					}else if(elem.getNodeName().equals("預入日")){
						bean.set預入日(getChildText(elem));					
					}else if(elem.getNodeName().equals("満期日")){
						bean.set満期日(getChildText(elem));
					}else if(elem.getNodeName().equals("解約日ハイフン")){
						bean.set解約日ハイフン(getChildText(elem));						
					}else if(elem.getNodeName().equals("預入日ハイフン")){
						bean.set預入日ハイフン(getChildText(elem));						
					}else if(elem.getNodeName().equals("子定期金額")){
						bean.set子定期金額(getChildText(elem));					
					}
		    	}
	        	//次の子ノードを取得
		    	elem = elem.getNextSibling();
			}
			//メンバにセット
			teikiYokinList.add(bean);
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
		
		//共通項目をチェック
		set店舗番号(ConvertUtil.chkConvertNumAdd0(get店舗番号(), 3));
		set顧客番号(ConvertUtil.chkConvertNumAdd0(get顧客番号(), 7));
		set科目(ConvertUtil.chkConvertNumAdd0(get科目(), 2));
		set口座番号(ConvertUtil.chkConvertNumAdd0(get口座番号(), 7));
		
		//取得した情報分チェックする
		Iterator<TeikiYokinBean> it = teikiYokinList.iterator();
		while(it.hasNext()){
			TeikiYokinBean tyb = it.next();

			//入金番号チェック
			boolean deleteFlag = false;
			
			//項目が取得できていなかったらNG
			tyb.set入金番号(ConvertUtil.chkNull(tyb.get入金番号()));
			
			//重複チェック　同一レコードがあったら、NG
			Iterator<TeikiYokinBean> it2 = teikiYokinList.iterator();
			TeikiYokinBean tyb2;
			int dupCount=0;
			while (it2.hasNext()){
				tyb2 = it2.next();
				//キー項目がどれかひとつでも違っていれば重複ではない
				if (tyb.get入金番号().equals(tyb2.get入金番号())){
					dupCount++;
				}
			}
			//重複レコードだったらNG
			if(dupCount>1){deleteFlag = true;}
			
			//チェックに引っかかったら削除
			if(deleteFlag){
				it.remove();
			} else {
				//チェックに引っかからなければ、残りの項目の変換
				tyb.set入金番号(tyb.get入金番号());
				tyb.set解約残高(ConvertUtil.chkConvertFlag(tyb.get解約残高()));
				tyb.set現在残高(ConvertUtil.delComma(ConvertUtil.delAsterisk(tyb.get現在残高())));
				tyb.set預入日(ConvertUtil.chkConvertDateAdd0(tyb.get預入日()));
				tyb.set満期日(ConvertUtil.chkConvertDateAdd0(tyb.get満期日()));
			}
		}
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
}
