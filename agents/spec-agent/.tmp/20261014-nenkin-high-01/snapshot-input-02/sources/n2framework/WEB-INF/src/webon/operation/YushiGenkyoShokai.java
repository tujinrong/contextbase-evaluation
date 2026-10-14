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
 * Webon汎用照会クラス　融資取引現況照会管理クラス
 * 融資取引現況照会(XML)の取得とデータ管理、アクセスメソッドの提供
 * 
 * @author	岡野
 * 
 * @date	2020.03.27	新規作成
 */
public class YushiGenkyoShokai extends CommonOperation {

	private static final String syokaiName = "融資取引現況照会";
	
	//オペレーションＩＤ
	private final String operationId="OP-YUSHIGEN-0001";
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
	
	//融資取引現況情報
	private String 店番 = "";
	private String 顧客番号 = "";
	private String 割引手形振替科目 = "";
	private String 割引手形振替口座番号 = "";
	private String 手形貸付振替科目 = "";
	private String 手形貸付振替口座番号 = "";
	private String 証書貸付振替科目 = "";
	private String 証書貸付振替口座番号 = "";
	private String 代理業務貸付振替科目 = "";
	private String 代理業務貸付振替口座番号 = "";
	private String 債務保証振替科目 = "";
	private String 債務保証振替口座番号 = "";
	
	//融資取引現況表照会詳細リスト
	List<LoanCurrentDetailBean> loanCurrentList = new ArrayList<LoanCurrentDetailBean>();
	
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
	public String get割引手形振替科目() {
		return 割引手形振替科目;
	}
	public void set割引手形振替科目(String 割引手形振替科目) {
		this.割引手形振替科目 = 割引手形振替科目;
	}
	public String get割引手形振替口座番号() {
		return 割引手形振替口座番号;
	}
	public void set割引手形振替口座番号(String 割引手形振替口座番号) {
		this.割引手形振替口座番号 = 割引手形振替口座番号;
	}
	public String get手形貸付振替科目() {
		return 手形貸付振替科目;
	}
	public void set手形貸付振替科目(String 手形貸付振替科目) {
		this.手形貸付振替科目 = 手形貸付振替科目;
	}
	public String get手形貸付振替口座番号() {
		return 手形貸付振替口座番号;
	}
	public void set手形貸付振替口座番号(String 手形貸付振替口座番号) {
		this.手形貸付振替口座番号 = 手形貸付振替口座番号;
	}
	public String get証書貸付振替科目() {
		return 証書貸付振替科目;
	}
	public void set証書貸付振替科目(String 証書貸付振替科目) {
		this.証書貸付振替科目 = 証書貸付振替科目;
	}
	public String get証書貸付振替口座番号() {
		return 証書貸付振替口座番号;
	}
	public void set証書貸付振替口座番号(String 証書貸付振替口座番号) {
		this.証書貸付振替口座番号 = 証書貸付振替口座番号;
	}
	public String get代理業務貸付振替科目() {
		return 代理業務貸付振替科目;
	}
	public void set代理業務貸付振替科目(String 代理業務貸付振替科目) {
		this.代理業務貸付振替科目 = 代理業務貸付振替科目;
	}
	public String get代理業務貸付振替口座番号() {
		return 代理業務貸付振替口座番号;
	}
	public void set代理業務貸付振替口座番号(String 代理業務貸付振替口座番号) {
		this.代理業務貸付振替口座番号 = 代理業務貸付振替口座番号;
	}
	public String get債務保証振替科目() {
		return 債務保証振替科目;
	}
	public void set債務保証振替科目(String 債務保証振替科目) {
		this.債務保証振替科目 = 債務保証振替科目;
	}
	public String get債務保証振替口座番号() {
		return 債務保証振替口座番号;
	}
	public void set債務保証振替口座番号(String 債務保証振替口座番号) {
		this.債務保証振替口座番号 = 債務保証振替口座番号;
	}
	public List<LoanCurrentDetailBean> getLoanCurrentList() {
		return loanCurrentList;
	}
	public void setLoanCurrentList(List<LoanCurrentDetailBean> loanCurrentList) {
		this.loanCurrentList = loanCurrentList;
	}

	//融資取引現況表照会（融資取引明細）
	public class LoanCurrentDetailBean{

		//顧客情報
		String 科目名 = "";
		String 稟議種別 = "";
		String 稟議番号 = "";
		String 取扱番号 = "";
		String 当初貸出日 = "";
		String 貸出期限保証期限 = "";
		String 当初貸出金額 = "";
		String 担保管理番号 = "";
		String 担保明細 = "";
		String 保証会社 = "";
		String 保証掛目 = "";
		String 返済方法 = "";
		String 利率 = "";
		String 現在残高 = "";
		String 手形期日次回約定日 = "";
		String 代理先 = "";
		String 融資代理貸種別 = "";
		String 資金使途 = "";
		String 延滞 = "";
		
		//setter,getter
		public String get科目名() {
			return 科目名;
		}
		public void set科目名(String 科目名) {
			this.科目名 = 科目名;
		}
		public String get稟議種別() {
			return 稟議種別;
		}
		public void set稟議種別(String 稟議種別) {
			this.稟議種別 = 稟議種別;
		}
		public String get稟議番号() {
			return 稟議番号;
		}
		public void set稟議番号(String 稟議番号) {
			this.稟議番号 = 稟議番号;
		}
		public String get取扱番号() {
			return 取扱番号;
		}
		public void set取扱番号(String 取扱番号) {
			this.取扱番号 = 取扱番号;
		}
		public String get当初貸出日() {
			return 当初貸出日;
		}
		public void set当初貸出日(String 当初貸出日) {
			this.当初貸出日 = 当初貸出日;
		}
		public String get貸出期限保証期限() {
			return 貸出期限保証期限;
		}
		public void set貸出期限保証期限(String 貸出期限保証期限) {
			this.貸出期限保証期限 = 貸出期限保証期限;
		}
		public String get当初貸出金額() {
			return 当初貸出金額;
		}
		public void set当初貸出金額(String 当初貸出金額) {
			this.当初貸出金額 = 当初貸出金額;
		}
		public String get担保管理番号() {
			return 担保管理番号;
		}
		public void set担保管理番号(String 担保管理番号) {
			this.担保管理番号 = 担保管理番号;
		}
		public String get担保明細() {
			return 担保明細;
		}
		public void set担保明細(String 担保明細) {
			this.担保明細 = 担保明細;
		}
		public String get保証会社() {
			return 保証会社;
		}
		public void set保証会社(String 保証会社) {
			this.保証会社 = 保証会社;
		}
		public String get保証掛目() {
			return 保証掛目;
		}
		public void set保証掛目(String 保証掛目) {
			this.保証掛目 = 保証掛目;
		}
		public String get返済方法() {
			return 返済方法;
		}
		public void set返済方法(String 返済方法) {
			this.返済方法 = 返済方法;
		}
		public String get利率() {
			return 利率;
		}
		public void set利率(String 利率) {
			this.利率 = 利率;
		}
		public String get現在残高() {
			return 現在残高;
		}
		public void set現在残高(String 現在残高) {
			this.現在残高 = 現在残高;
		}
		public String get手形期日次回約定日() {
			return 手形期日次回約定日;
		}
		public void set手形期日次回約定日(String 手形期日次回約定日) {
			this.手形期日次回約定日 = 手形期日次回約定日;
		}
		public String get代理先() {
			return 代理先;
		}
		public void set代理先(String 代理先) {
			this.代理先 = 代理先;
		}
		public String get融資代理貸種別() {
			return 融資代理貸種別;
		}
		public void set融資代理貸種別(String 融資代理貸種別) {
			this.融資代理貸種別 = 融資代理貸種別;
		}
		public String get資金使途() {
			return 資金使途;
		}
		public void set資金使途(String 資金使途) {
			this.資金使途 = 資金使途;
		}
		public String get延滞() {
			return 延滞;
		}
		public void set延滞(String 延滞) {
			this.延滞 = 延滞;
		}
	}

	/**
	 * 店番・顧客番号を元に融資取引現況照会を取得する
	 * 
	 * @param cif 顧客番号
	 * @param br 店番
	 * @param loginInfo ログイン情報
	 * @param con
	 * @throws Exception
	 */
	public void getWebonByCif(String cif,String br, LoginInfoBean loginInfo, Connection con) throws Exception {
		try{
			//起動チェック 引数がセットされているか
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
		final String WOKEY_KETSUGO="融資取引現況照会";	//これがroot2
		final String WOKEY_ROOP="融資取引明細";	//ループ（２箇所で使用）
		final String DBKEY_CUSTNO="顧客番号";	//必須項目
		final String DBKEY_BRANCHNO="店番";		//必須項目
		
		//結果取得
		Node editData = webonBase.getEditData();
		//結果解析
		//データの最上位ノードを取得
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
	    		    		if (root2.getNodeName().equals(WOKEY_KETSUGO)) {
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
        Node DetailNode = null;
//		while (true) {
		for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
        	//取得できなかったら終わり
        	if (child==null){break;}
	    	if (child.getNodeType()==Node.ELEMENT_NODE) {
	    		//要素名の解析
	    		//ループ対象行
	    		if (child.getNodeName().equals(WOKEY_ROOP)) {
	    			DetailNode = child;
	            //ループ対象行以外
	            } else if (child.getNodeName().equals(DBKEY_BRANCHNO)){
	    			//必須チェック
	    			if(!getChildText(child).isEmpty()){
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
	    			if(!getChildText(child).isEmpty()){
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
	            } else if(child.getNodeName().equals("割引手形振替科目")){
	            	set割引手形振替科目(getChildText(child));
	            } else if(child.getNodeName().equals("割引手形振替口座番号")){
	            	set割引手形振替口座番号(getChildText(child));
	            } else if(child.getNodeName().equals("手形貸付振替科目")){
	            	set手形貸付振替科目(getChildText(child));
	            } else if(child.getNodeName().equals("手形貸付振替口座番号")){
	            	set手形貸付振替口座番号(getChildText(child));
	            } else if(child.getNodeName().equals("証書貸付振替科目")){
	            	set証書貸付振替科目(getChildText(child));
	            } else if(child.getNodeName().equals("証書貸付振替口座番号")){
	            	set証書貸付振替口座番号(getChildText(child));
	            } else if(child.getNodeName().equals("代理業務貸付振替科目")){
	            	set代理業務貸付振替科目(getChildText(child));
	            } else if(child.getNodeName().equals("代理業務貸付振替口座番号")){
	            	set代理業務貸付振替口座番号(getChildText(child));
	            } else if(child.getNodeName().equals("債務保証振替科目")){
	            	set債務保証振替科目(getChildText(child));
	            } else if(child.getNodeName().equals("債務保証振替口座番号")){
	            	set債務保証振替口座番号(getChildText(child));
	            }
	    	}

        	//次の子ノードを取得
        	child = getNextElement(child);
		}

		//明細行の下の明細ノードリストを取得
        ArrayList<Node> loopNodes = new ArrayList<Node>();
        Node child2 = DetailNode.getFirstChild();
//		while (true) {
		for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
        	//取得できなかったら終わり
        	if (child2==null){break;}
	    	if (child2.getNodeType()==Node.ELEMENT_NODE) {
	    		//要素名の解析
	    		//ループ対象行(キーワードは共有)
	    		if (child2.getNodeName().equals(WOKEY_ROOP)) {
	    			loopNodes.add(child2);
	    		}
	    	}
        	//次の子ノードを取得
        	child2 = child2.getNextSibling();
		}

		//ループ行の走査＆値のセット
		for (int i=0; i<loopNodes.size(); i++ ) {
			//データ格納用ビーンの生成
			LoanCurrentDetailBean bean = new LoanCurrentDetailBean();
			//ループの要素を取り出し
			Node elem=loopNodes.get(i).getFirstChild();	//これが明細行
//			while (true) {
			for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
				if (elem==null){break;}
				if (elem.getNodeType()==Node.ELEMENT_NODE){
					
					if(elem.getNodeName().equals("科目名")){
						bean.set科目名(getChildText(elem));
					}else if(elem.getNodeName().equals("稟議種別")){
						bean.set稟議種別(getChildText(elem));
					}else if(elem.getNodeName().equals("稟議番号")){
						bean.set稟議番号(getChildText(elem));
					}else if(elem.getNodeName().equals("取扱番号")){
						bean.set取扱番号(getChildText(elem));
					}else if(elem.getNodeName().equals("当初貸出日")){
						bean.set当初貸出日(getChildText(elem));
					}else if(elem.getNodeName().equals("貸出期限保証期限")){
						bean.set貸出期限保証期限(getChildText(elem));
					}else if(elem.getNodeName().equals("当初貸出金額")){
						bean.set当初貸出金額(getChildText(elem));
					}else if(elem.getNodeName().equals("担保管理番号")){
						bean.set担保管理番号(getChildText(elem));
					}else if(elem.getNodeName().equals("担保明細")){
						bean.set担保明細(getChildText(elem));
					}else if(elem.getNodeName().equals("保証会社")){
						bean.set保証会社(getChildText(elem));
					}else if(elem.getNodeName().equals("保証掛目")){
						bean.set保証掛目(getChildText(elem));
					}else if(elem.getNodeName().equals("返済方法")){
						bean.set返済方法(getChildText(elem));
					}else if(elem.getNodeName().equals("利率")){
						bean.set利率(getChildText(elem));
					}else if(elem.getNodeName().equals("現在残高")){
						bean.set現在残高(getChildText(elem));
					}else if(elem.getNodeName().equals("手形期日次回約定日")){
						bean.set手形期日次回約定日(getChildText(elem));
					}else if(elem.getNodeName().equals("代理先")){
						bean.set代理先(getChildText(elem));
					}else if(elem.getNodeName().equals("融資代理貸種別")){
						bean.set融資代理貸種別(getChildText(elem));
					}else if(elem.getNodeName().equals("資金使途")){
						bean.set資金使途(getChildText(elem));
					}else if(elem.getNodeName().equals("延滞")){
						bean.set延滞(getChildText(elem));
					}
				}
				//次の子ノードを取得
				elem=getNextElement(elem);
			}
			//1口座分取得したので、リストに格納
			loanCurrentList.add(bean);
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
		set割引手形振替科目(ConvertUtil.chkConvertNumAdd0(get割引手形振替科目(), 2));
		set割引手形振替口座番号(ConvertUtil.chkConvertNumAdd0(get割引手形振替口座番号(), 7));
		set手形貸付振替科目(ConvertUtil.chkConvertNumAdd0(get手形貸付振替科目(), 2));
		set手形貸付振替口座番号(ConvertUtil.chkConvertNumAdd0(get手形貸付振替口座番号(), 7));
		set証書貸付振替科目(ConvertUtil.chkConvertNumAdd0(get証書貸付振替科目(), 2));
		set証書貸付振替口座番号(ConvertUtil.chkConvertNumAdd0(get証書貸付振替口座番号(), 7));
		set代理業務貸付振替科目(ConvertUtil.chkConvertNumAdd0(get代理業務貸付振替科目(), 2));
		set代理業務貸付振替口座番号(ConvertUtil.chkConvertNumAdd0(get代理業務貸付振替口座番号(), 7));
		set債務保証振替科目(ConvertUtil.chkConvertNumAdd0(get債務保証振替科目(), 2));
		set債務保証振替口座番号(ConvertUtil.chkConvertNumAdd0(get債務保証振替口座番号(), 7));
		
		//リスト全てチェックする
		Iterator<LoanCurrentDetailBean> it = loanCurrentList.iterator();
		while(it.hasNext()){
			LoanCurrentDetailBean lcdb = it.next();

			lcdb.set科目名(ConvertUtil.chkNull(lcdb.get科目名()));
			lcdb.set稟議種別(ConvertUtil.chkConvertNumAdd0(lcdb.get稟議種別(), 1));
			lcdb.set稟議番号(ConvertUtil.chkConvertNumAdd0(lcdb.get稟議番号(), 7));
			lcdb.set取扱番号(ConvertUtil.chkConvertNumAdd0(lcdb.get取扱番号(), 7));
			//【和暦処理】
			lcdb.set当初貸出日(ConvertUtil.chkConvertDateAdd0(lcdb.get当初貸出日()));
			lcdb.set貸出期限保証期限(ConvertUtil.chkConvertDateAdd0(lcdb.get貸出期限保証期限()));
			lcdb.set当初貸出金額(ConvertUtil.chkDelCommaAdd0(lcdb.get当初貸出金額(), 13));
			lcdb.set担保管理番号(ConvertUtil.chkConvertNumAdd0(lcdb.get担保管理番号(), 3));
			lcdb.set担保明細(ConvertUtil.chkConvertNumAdd0(lcdb.get担保明細(), 4));
			lcdb.set保証会社(ConvertUtil.chkConvertNumAdd0(lcdb.get保証会社(), 2));
			lcdb.set保証掛目(ConvertUtil.chkConvertNumAdd0(lcdb.get保証掛目(), 3));
			lcdb.set返済方法(ConvertUtil.chkNull(lcdb.get返済方法()));
			lcdb.set利率(ConvertUtil.chkConvertRate(lcdb.get利率(), 5, 8));
			lcdb.set現在残高(ConvertUtil.chkDelCommaAdd0(lcdb.get現在残高(), 13));
			//【和暦処理】
			lcdb.set手形期日次回約定日(ConvertUtil.chkConvertDateAdd0(lcdb.get手形期日次回約定日()));
			lcdb.set代理先(ConvertUtil.chkConvertNumAdd0(lcdb.get代理先(), 3));
			lcdb.set融資代理貸種別(ConvertUtil.chkConvertNumAdd0(lcdb.get融資代理貸種別(), 6));
			lcdb.set資金使途(ConvertUtil.chkConvertNumAdd0(lcdb.get資金使途(), 2));
			lcdb.set延滞(ConvertUtil.chkConvertFlag(lcdb.get延滞()));
	
		}
	}
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
	/**
	 * 融資科目名変換メソッド
	 * 融資現況照会の科目名を科目コードに変換
	 * ※外部に出したい
	 * 
	 * @param String 科目名
	 * @return String 科目コード
	 */
	public static String convertToSubcode (String subname) {
		if (subname.equals("手形貸付")) return "32";
		if (subname.equals("証書貸付")) return "33";
		if (subname.equals("代理貸付")) return "43";
		if (subname.equals("債務保証")) return "45";
		return null;
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
