package webon.operation;

import java.sql.Connection;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import org.w3c.dom.Node;

import common.bean.LoginInfoBean;

import webon.WebonBase;
import webon.WebonException;
import webon.util.ConvertUtil;
import webon.util.FixedValue;

/**
 * Webon汎用照会クラス　名寄せ情報照会（統一カナ氏名・生年月日による照会）クラス
 * 
 * @author	Minori 岡野
 * 
 * @date	2020.03.31	岡野		webonのFW化対応
 *
 */
public class NayoseJohoShokai extends CommonOperation{
	
	private static final String syokaiName = "名寄せ情報照会（統一カナ氏名・生年月日による照会）";
	
	//webon情報
	WebonBase webonBase;
	//オペレーションＩＤ
	private final String operationId="OP-UNAYOSEJ-0003";
	//ログイン情報
	LoginInfoBean loginInfo;
	//webon引数
	String woKanaName;
	String woBirthDate;

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
	
	//名寄せ情報
	private ArrayList<customerNayoseInfoBean> custNayoseInfoList = new ArrayList<customerNayoseInfoBean>();

	public class customerNayoseInfoBean{
		private String 統一顧客番号="";
		private String 統一カナ氏名 ="";
		private String 統一生年月日="";
		private String 統一電話番号="";
		private String 統一人格Ｃ ="";
		private String 店番="";
		private String 顧客番号="";
		//setter,getter
		public String get統一顧客番号() {
			return 統一顧客番号;
		}
		public void set統一顧客番号(String 統一顧客番号) {
			this.統一顧客番号 = 統一顧客番号;
		}
		public String get統一カナ氏名() {
			return 統一カナ氏名;
		}
		public void set統一カナ氏名(String 統一カナ氏名) {
			this.統一カナ氏名 = 統一カナ氏名;
		}
		public String get統一生年月日() {
			return 統一生年月日;
		}
		public void set統一生年月日(String 統一生年月日) {
			this.統一生年月日 = 統一生年月日;
		}
		public String get統一電話番号() {
			return 統一電話番号;
		}
		public void set統一電話番号(String 統一電話番号) {
			this.統一電話番号 = 統一電話番号;
		}
		public String get統一人格Ｃ() {
			return 統一人格Ｃ;
		}
		public void set統一人格Ｃ(String 統一人格ｃ) {
			統一人格Ｃ = 統一人格ｃ;
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
	}
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
	public ArrayList<customerNayoseInfoBean> getCustNayoseInfoList() {
		return custNayoseInfoList;
	}
	public void setCustNayoseInfoList(	ArrayList<customerNayoseInfoBean> custNayoseInfoList) {
		this.custNayoseInfoList = custNayoseInfoList;
	}

	/**
	 * カナ氏名・生年月日を元に名寄せ照会を行う（完全一致）
	 * 
	 * @param unionKanaName カナ氏名
	 * @param unionBirthDate 生年月日
	 * @param loginInfo
	 * @param con
	 * @throws WebonException
	 * @throws Exception
	 */
	public void getWebon(String unionKanaName, String unionBirthDate, LoginInfoBean loginInfo, Connection con) throws WebonException, Exception{
		try{
			//引数のセット
			this.woKanaName=unionKanaName;
			this.woBirthDate=unionBirthDate;
			this.loginInfo = loginInfo;

			//起動チェック 引数がセットされているか
			if (woKanaName == null) {throw new Exception("統一カナ氏名が設定されていません");}
			if (woBirthDate == null) {throw new Exception("統一生年月日が設定されていません");}
			if (operationId == null) {throw new Exception("オペレーションＩＤが設定されていません");}
			if (con == null) {throw new Exception("ＤＢコネクションが設定されていません");}

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
	private void getWebon(Connection con) throws WebonException,Exception {
		
		//WebonBaseの取得
		webonBase = new WebonBase(operationId, loginInfo, con);
		//設定値
		webonBase.put("照会区分", "1");
		webonBase.put("統一カナ氏名",woKanaName);
		webonBase.put("統一生年月日",woBirthDate);
		//問い合わせ
		webonBase.doQuery();
		
		//エラー処理
		if (!webonBase.checkResult()) {
			//エラーコード等をセット
			WebonException e = new WebonException("Webon取得結果エラー",webonBase);
			//顧客を特定する情報をセット
			e.setOperationId(operationId);
			e.setErrStat(ERRLEVEL_ERROR);
			e.setErrSpot(ERRSPOT_WOGET);
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
		final String WOKEY_TSUCYO="通帳部宛";					//root
		final String WOKEY_NAYOSE="統一顧客名寄せ情報照会";		//root2

		//起動チェック、webonが取得されているか
		if (webonBase==null) {
			StringBuilder errmsg=new StringBuilder();
			errmsg.append("Webonの結果が未取得です");
			throw new Exception(errmsg.toString());
		}
		
		//結果取得
		Node editData = webonBase.getEditData();
		//データの最上位ノードを取得(もうちょっと精査要)
		ArrayList<Node> loopNode = new ArrayList<Node>();
		Node root  = editData.getFirstChild(); //通帳部ノード
		Node root2 = null;
//		while (true) {
		for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
        	//取得できなかったら終わり
        	if (root==null){break;}
	    	if (root.getNodeType()==Node.ELEMENT_NODE) {
	    		//要素名の解析
	    		if (root.getNodeName().equals(WOKEY_TSUCYO)) {
	    			root2=root.getFirstChild();	//統一顧客名寄せ情報照会ノード
//	    			while (true) {
    				for (int roopCount2=0;roopCount2<FixedValue.SYS_WBNUMLIMIT;roopCount2++){
	    	        	//取得できなかったら終わり
	    	        	if (root2==null){break;}
	    	        	if (root2.getNodeType()==Node.ELEMENT_NODE) {
	    		    		if (root2.getNodeName().equals(WOKEY_NAYOSE)) {
	    		    			loopNode.add(root2);
	    		    		}
	    	        	}
	    	        	//次の子ノードを取得
	    	        	root2=root2.getNextSibling();
	    			}
	    			break;
	            }
	    	}
        	//次の子ノードを取得
	    	root = root.getNextSibling();
		}

		//ループ行の走査＆値のセット
		for (int i=0; i<loopNode.size(); i++ ) {
			//データ格納用
			String cif = "";
			String kana = "";
			String birthDate = "";
			String tel = "";
			String jinkaku = "";

			//ループの要素を取り出し
			Node elem=loopNode.get(i).getFirstChild();
			//while (true) {
			for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
				if (elem==null){break;}
				if (elem.getNodeType()==Node.ELEMENT_NODE && elem.getNodeName().equals("統一顧客番号")) {
		    		
	    			//必須チェック
	    			if(!getChildText(elem).equals("")){
	    				cif = getChildText(elem);
	    			}else{
	    				WebonException e = createWoException("Webon取得結果解析エラー", ERRLEVEL_ERROR, ERRSPOT_WOANALYZE);
	    				//エラー項目のセット
	    				Map<String, String>map = new HashMap<String, String>();
	    				map.put("統一顧客番号", null);
	    				etc.add(map);
	    				e.setEtc(etc);
	    				//エラー処理は上位に任せる
	    				throw e;
	    			}
				} else if (elem.getNodeType()==Node.ELEMENT_NODE && elem.getNodeName().equals("統一カナ氏名")) {

	    			//必須チェック
	    			if(!getChildText(elem).equals("")){
	    				kana = getChildText(elem);
	    			}else{
	    				WebonException e = createWoException("Webon取得結果解析エラー", ERRLEVEL_ERROR, ERRSPOT_WOANALYZE);
	    				//エラー項目のセット
	    				Map<String, String>map = new HashMap<String, String>();
	    				map.put("統一カナ氏名", null);
	    				etc.add(map);
	    				e.setEtc(etc);
	    				//エラー処理は上位に任せる
	    				throw e;
	    			}

				} else if (elem.getNodeType()==Node.ELEMENT_NODE && elem.getNodeName().equals("統一生年月日")) {
		    		birthDate = getChildText(elem);
		    	} else if (elem.getNodeType()==Node.ELEMENT_NODE && elem.getNodeName().equals("統一電話番号")) {
		    		tel = getChildText(elem);
		    	} else if (elem.getNodeType()==Node.ELEMENT_NODE && elem.getNodeName().equals("統一人格C")) {
		    		jinkaku = getChildText(elem);
		    	} else if (elem.getNodeType()==Node.ELEMENT_NODE && elem.getNodeName().equals("名寄せ店番")) {
		    		Node elemBr  =elem;	//名寄せ店番
		    		Node elemCif =getNextElement(elem);	//名寄せ顧客

		    		//問合せ結果の取得
			    	//店番と顧客番号を並行して走査していく
			    	//順番が入れ替わっていないこと、ノード数が同じである事が前提
//		    		FWLog.debug("店番タグ："+elemBr+"ＣＩＦタグ："+elemCif);
					if(elemBr.hasChildNodes()&&elemCif.hasChildNodes()){
						Node child1 = elemBr.getFirstChild();	//店番
						Node child2 = elemCif.getFirstChild();	//顧客番号
			    		//while (true) {
			    		for (int roopCount2=0;roopCount2<FixedValue.SYS_WBNUMLIMIT;roopCount2++){
//			    			FWLog.debug("店番："+child1+"ＣＩＦ："+child2);
			    			if(child1.hasChildNodes()&&child2.hasChildNodes()){
				    			//最深階層にてBeanをセットしていく
				    			customerNayoseInfoBean bean = new customerNayoseInfoBean();
				    			bean.set統一顧客番号(cif);
				    			bean.set統一カナ氏名(kana);
				    			bean.set統一生年月日(birthDate);
				    			bean.set統一電話番号(tel);
				    			bean.set統一人格Ｃ(jinkaku);

				    			if (child1.getNodeType()==Node.ELEMENT_NODE && child1.getNodeName().equals("店番")) {
				            		bean.set店番(getChildText(child1));
				    	    	}

				    	    	if (child2.getNodeType()==Node.ELEMENT_NODE && child2.getNodeName().equals("顧客番号")) {
				    	    		bean.set顧客番号(getChildText(child2));
				    	    	}
				            	custNayoseInfoList.add(bean);
			    			}

			    	    	//次の子ノードを取得
			    			child1  = child1.getNextSibling();	
			    	    	child2  = child2.getNextSibling();	
			            	//取得できなかったら終わり
			            	if (child1 ==null){break;}
			            	if (child2==null){break;}
			    		}
			    	}
		    	}
				elem=getNextElement(elem);
			}
		}
		//取得項目のチェック
		checkValue();

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
	private void checkValue(){
		
		Iterator<customerNayoseInfoBean> it = custNayoseInfoList.iterator();
		while(it.hasNext()){
			customerNayoseInfoBean nb = it.next();

			nb.set店番(ConvertUtil.chkConvertNumAdd0(nb.get店番(), 3));
			nb.set顧客番号(ConvertUtil.chkConvertNumAdd0(nb.get顧客番号(), 7));
			nb.set統一顧客番号(ConvertUtil.chkConvertNumAdd0(nb.get統一顧客番号(), 9));
			//【和暦処理】
			nb.set統一生年月日(ConvertUtil.chkConvertGengoDateAdd0(nb.get統一生年月日()));

		}
	}

	//以下UTILITY
	//以下、ユーティリティ的メソッド
	/**
	 * エラー生成メソッド
	 * @param String	エラーメッセージ
	 * @param int		エラーレベル
	 * @param String	エラー箇所
	 */
	public WebonException createWoException(String msg ,int el, String es){
		//エラーコード等をセット
		WebonException e = new WebonException(msg,webonBase);
		//顧客を特定する情報をセット
		e.setOperationId(operationId);
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
