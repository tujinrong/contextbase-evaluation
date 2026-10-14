package webon.operation;

import java.sql.Connection;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import org.w3c.dom.Node;

import webon.WebonBase;
import webon.WebonException;
import webon.util.ConvertUtil;
import webon.util.FixedValue;

import common.bean.LoginInfoBean;

/**
 * Webon汎用照会クラス　出資金照会管理クラス
 * 出資金照会(XML)の取得とデータ管理、アクセスメソッドの提供
 * 
 * @author	富永
 * 
 * @date	2020.03.27	新規作成
 */
public class SyushikinShokai extends CommonOperation {
	
	private static final String syokaiName = "出資金照会";

	//オペレーションＩＤ
	private final String operationId="OP-SYUSHIKN-0001";
	//ログイン情報
	LoginInfoBean loginInfo;
	//webon引数
	String woCif;
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
	public List<SyushikinBean> getSyushikinList() {
		return syushikinList;
	}
	public void setSyushikinList(List<SyushikinBean> syushikinList) {
		this.syushikinList = syushikinList;
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
	public String getWoCif() {
		return woCif;
	}
	public void setWoCif(String woCif) {
		this.woCif = woCif;
	}
	public String getWoBrno() {
		return woBrno;
	}
	public void setWoBrno(String woBrno) {
		this.woBrno = woBrno;
	}
	
	//==出資金照会==
	
	//取得結果
	private String 店番="";
	private String 顧客番号="";
	private String 会員番号="";
	private String 当初加入日="";
	private String 現在出資金額="";
	private String 振替店番="";
	private String 振替科目="";
	private String 振替口座番号="";
	private String 未払配当金合計件数="";
	private String 未払配当金合計金額="";

	//出資金照会明細情報リスト
	List<SyushikinBean> syushikinList = new ArrayList<SyushikinBean>();
	
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
	public String get会員番号() {
		return 会員番号;
	}
	public void set会員番号(String 会員番号) {
		this.会員番号 = 会員番号;
	}
	public String get当初加入日() {
		return 当初加入日;
	}
	public void set当初加入日(String 当初加入日) {
		this.当初加入日 = 当初加入日;
	}
	public String get現在出資金額() {
		return 現在出資金額;
	}
	public void set現在出資金額(String 現在出資金額) {
		this.現在出資金額 = 現在出資金額;
	}
	public String get振替店番() {
		return 振替店番;
	}
	public void set振替店番(String 振替店番) {
		this.振替店番 = 振替店番;
	}
	public String get振替科目() {
		return 振替科目;
	}
	public void set振替科目(String 振替科目) {
		this.振替科目 = 振替科目;
	}
	public String get振替口座番号() {
		return 振替口座番号;
	}
	public void set振替口座番号(String 振替口座番号) {
		this.振替口座番号 = 振替口座番号;
	}
	public String get未払配当金合計金額() {
		return 未払配当金合計金額;
	}
	public void set未払配当金合計金額(String 未払配当金合計金額) {
		this.未払配当金合計金額 = 未払配当金合計金額;
	}
	public String get未払配当金合計件数() {
		return 未払配当金合計件数;
	}
	public void set未払配当金合計件数(String 未払配当金合計件数) {
		this.未払配当金合計件数 = 未払配当金合計件数;
	}
	/**
	 * 増資0を除いた証券番号リストを返却するメソッド
	 */
	public  List<SyushikinBean> getEnableSyushikinList() {
		List<SyushikinBean> slist = new ArrayList<SyushikinBean>();
		Iterator<SyushikinBean> sIt = syushikinList.iterator();
		while(sIt.hasNext()){
			SyushikinBean sBean = sIt.next();
			if(0<Integer.parseInt(sBean.get増資())){
				slist.add(sBean);
			}
		}
		return slist;
	}

	//出資金照会明細情報
	public class SyushikinBean{

		//顧客情報
		String 証券番号="";
		String 増資="";
		String 減資="";
		String 当初購入日="";
		
		//setter,getter
		public String get証券番号() {
			return 証券番号;
		}
		public void set証券番号(String 証券番号) {
			this.証券番号 = 証券番号;
		}
		public String get増資() {
			return 増資;
		}
		public void set増資(String 増資) {
			this.増資 = 増資;
		}
		public String get減資() {
			return 減資;
		}
		public void set減資(String 減資) {
			this.減資 = 減資;
		}
		public String get当初購入日() {
			return 当初購入日;
		}
		public void set当初購入日(String 当初購入日) {
			this.当初購入日 = 当初購入日;
		}	
	}

	/**
	 * 店番・顧客番号を元に出資金照会を取得する
	 * 
	 * @param cif 顧客番号
	 * @param br 店番
	 * @param loginInfo ログイン情報
	 * @param con
	 * @throws Exception
	 */
	public void getWebonByCif(String cif,String br, LoginInfoBean loginInfo, Connection con) throws Exception {
		try{
			//引数チェック 引数がセットされているか
			if (cif == null) {throw new Exception("顧客番号が設定されていません");}
			if (br == null) {throw new Exception("原店番号が設定されていません");}
			if (con == null) {throw new Exception("ＤＢコネクションが設定されていません");}
			
			//引数のセット
			this.woBrno=br;
			this.woCif=cif;
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
		webonBase.put("顧客番号",woCif);
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
		final String WOKEY_SYUSHI="出資金照会票";	//これがroot2
		final String WOKEY_ROOP="明細行";	//２回使用
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
	    		    		if (root2.getNodeName().equals(WOKEY_SYUSHI)) {
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
        List<Node> loopNodes = new ArrayList<Node>();

//		while (true) {
		for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
        	//取得できなかったら終わり
        	if (child==null){break;}
	    	if (child.getNodeType()==Node.ELEMENT_NODE) {
	    		//要素名の解析
	    		//ループ対象行(明細行階層は２段階)
	    		if (child.getNodeName().equals(WOKEY_ROOP)) {
    		        Node child2 = child.getFirstChild();
	    			for (int roopCount2=0;roopCount2<FixedValue.SYS_WBNUMLIMIT;roopCount2++){
	    	        	if (child2==null){break;}
	    				if(child2.getNodeName().equals(WOKEY_ROOP)){
	    					loopNodes.add(child2);
	    				}
	    	        	//次の子ノードを取得
	    	        	child2 = getNextElement(child2);
	    			}
	            //ループ対象行以外
	            } else if (child.getNodeName().equals(DBKEY_BRANCHNO)){
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
	            } else if (child.getNodeName().equals("会員番号")){
	            	set会員番号(getChildText(child));
	            } else if (child.getNodeName().equals("当初加入日")){
	            	set当初加入日(getChildText(child));
	            } else if (child.getNodeName().equals("現在出資金額")){
	            	set現在出資金額(getChildText(child));
	            } else if (child.getNodeName().equals("振替店番")){
	            	set振替店番(getChildText(child));
	            } else if (child.getNodeName().equals("振替科目")){
	            	set振替科目(getChildText(child));
	            } else if (child.getNodeName().equals("振替口座番号")){
	            	set振替口座番号(getChildText(child));
	            } else if (child.getNodeName().equals("未払配当金合計件数")){
	            	set未払配当金合計件数(getChildText(child));
	            } else if (child.getNodeName().equals("未払配当金合計金額")){
	            	set未払配当金合計金額(getChildText(child));
	            }
	    	}
        	//次の子ノードを取得
        	child = getNextElement(child);
		}
		//ループ行の走査＆値のセット
		for (int i=0; i<loopNodes.size(); i++ ) {
			//ループの要素を取り出し
			Node elem=loopNodes.get(i).getFirstChild();
//			while (true) {
			//データ格納用ビーンの生成
			SyushikinBean bean = new SyushikinBean();
			for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
	        	if (elem==null){break;}
	//			while (true) {
				if (elem.getNodeType()==Node.ELEMENT_NODE) {

					if(elem.getNodeName().equals("証券番号")){
						bean.set証券番号(getChildText(elem));				
					}else if(elem.getNodeName().equals("増資")){
						bean.set増資(getChildText(elem));						
					}else if(elem.getNodeName().equals("減資")){
						bean.set減資(getChildText(elem));					
					}
				}
	        	//次の子ノードを取得
		    	elem = getNextElement(elem);	
			}
			//リストに格納
			syushikinList.add(bean);
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
		
		set店番(ConvertUtil.chkConvertNumAdd0(get店番(), 3));
		set顧客番号(ConvertUtil.chkConvertNumAdd0(get顧客番号(), 7));
		set会員番号(ConvertUtil.chkConvertNumAdd0(get会員番号(), 7));
		set当初加入日(ConvertUtil.chkConvertDateAdd0(get当初加入日()));
		set現在出資金額(ConvertUtil.chkDelCommaAdd0(get現在出資金額(), 13));
		set振替店番(ConvertUtil.chkConvertNumAdd0(get振替店番(), 3));
		set振替科目(ConvertUtil.chkConvertNumAdd0(get振替科目(), 2));
		set振替口座番号(ConvertUtil.chkConvertNumAdd0(get振替口座番号(), 7));
		set未払配当金合計件数(ConvertUtil.chkConvertNumAdd0(get未払配当金合計件数(), 2));
		set未払配当金合計金額(ConvertUtil.chkDelCommaAdd0(get未払配当金合計金額(), 13));
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
		e.setCif(woCif);
		e.setErrStat(el);
		e.setErrSpot(es);
		//エラー処理は上位に任せる
		return e;
	}

}
