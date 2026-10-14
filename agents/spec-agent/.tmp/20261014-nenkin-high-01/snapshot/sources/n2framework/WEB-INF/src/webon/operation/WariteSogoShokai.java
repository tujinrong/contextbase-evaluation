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
import webon.util.ValidateUtil;

import common.bean.LoginInfoBean;

/**
 * Webon汎用照会クラス　割引手形総合明細照会（稟議明細取得）クラス
 * 
 * @author	岡野
 * 
 * @date	2020.04.14	新規作成
 */
public class WariteSogoShokai extends CommonOperation{

	//照会名
	private static final String syokaiName = "割引手形総合明細照会";
	//webon情報
	WebonBase webonBase;
	//オペレーションＩＤ
	private final String operationId="OP-WARITESG-0001";
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

	//割引手形総合明細
	private String 店番="";
	private String 顧客番号="";
	private String 割引枚数	="";
	private String 割引現在残高="";

	//割引手形総合明細照会リスト(保持するのみ)
    List<WariteSogoBean> wariteSogoList = new ArrayList<WariteSogoBean>();

	//割引手形総合明細
	public class WariteSogoBean{
		
		//顧客情報
		String 稟議種別="";
		String 稟議番号="";
		String 実行済="";
		String 実行日="";

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
		public String get実行済() {
			return 実行済;
		}
		public void set実行済(String 実行済) {
			this.実行済 = 実行済;
		}
		public String get実行日() {
			return 実行日;
		}
		public void set実行日(String 実行日) {
			this.実行日 = 実行日;
		}
	}
	
	//setter,getter
	public LoginInfoBean getLoginInfo() {
		return loginInfo;
	}
	public void setLoginInfo(LoginInfoBean loginInfo) {
		this.loginInfo = loginInfo;
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
	public List<WariteSogoBean> getWariteSogoList() {
		return wariteSogoList;
	}
	public void setWariteSogoList(List<WariteSogoBean> wariteSogoList) {
		this.wariteSogoList = wariteSogoList;
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
	public String get割引枚数() {
		return 割引枚数;
	}
	public void set割引枚数(String 割引枚数) {
		this.割引枚数 = 割引枚数;
	}
	public String get割引現在残高() {
		return 割引現在残高;
	}
	public void set割引現在残高(String 割引現在残高) {
		this.割引現在残高 = 割引現在残高;
	}
	public WebonBase getWebonBase() {
		return webonBase;
	}
	public void setWebonBase(WebonBase webonBase) {
		this.webonBase = webonBase;
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
	/**
	 * 店番・顧客番号を元に割引手形総合照会を取得する
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
			if (loginInfo == null) {throw new Exception("ログイン情報が設定されていません");}
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
	 * @throws Exception 
	 * @throws Exception 
	 */
	public void analyzeWeon() throws Exception {
		//WEBON結果走査用固定値
		final String WOKEY_TSUCYO="通帳部宛";				//root
		final String WOKEY_WARITESOGO="割手総合明細照会";	//root2
		final String WOKEY_ROOP="明細";
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
	    		    		if (root2.getNodeName().equals(WOKEY_WARITESOGO)) {
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
	    		//ループ対象行
	    		if (child.getNodeName().equals(WOKEY_ROOP)) {
	    			loopNodes.add(child);
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
	    		} else if (child.getNodeName().equals("割引枚数")){
	    			set割引枚数(getChildText(child));
	    		} else if (child.getNodeName().equals("割引現在残高")){
	    			set割引現在残高(getChildText(child));
	    		}
	    	}
        	//次の子ノードを取得
        	child = getNextElement(child);
		}
		
		//ループ行の走査＆値のセット
		for (int i=0; i<loopNodes.size(); i++ ) {
			//ループの要素を取り出し
			Node elem=loopNodes.get(i).getFirstChild();
			//データ格納用ビーンの生成
			WariteSogoBean bean = new WariteSogoBean();
//			while (true) {
			for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
//				while (true) {
				if (elem==null){break;}
				if (elem.getNodeType()==Node.ELEMENT_NODE) {

					if(elem.getNodeName().equals("稟議種別")){
						bean.set稟議種別(getChildText(elem));
					}else if(elem.getNodeName().equals("稟議番号")){
						bean.set稟議番号(getChildText(elem));						
					}else if(elem.getNodeName().equals("実行済")){
						bean.set実行済(getChildText(elem));						
					}else if(elem.getNodeName().equals("実行日")){
						bean.set実行日(getChildText(elem));					
					}
				}
	        	//次の子ノードを取得
		    	elem = getNextElement(elem);
			}
			//1口座分取得したので、リストに格納
			wariteSogoList.add(bean);
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
		set割引枚数(ConvertUtil.chkConvertNumAdd0(get割引枚数(), 3));
		set割引現在残高(ConvertUtil.chkDelCommaAdd0(get割引現在残高(), 13));

		//取得した情報分チェックする
		Iterator<WariteSogoBean> it = wariteSogoList.iterator();
		while(it.hasNext()){
			WariteSogoBean wsb = it.next();

			//稟議種別・稟議番号チェック
			boolean deleteFlag = false;
			
			//項目が取得できていなかったらNG
			if(wsb.get稟議種別()==null){deleteFlag = true;}
			if(wsb.get稟議番号()==null){deleteFlag = true;}
			//ブランクだったらNG
			if(wsb.get稟議種別().isEmpty()){deleteFlag = true;}
			if(wsb.get稟議番号().isEmpty()){deleteFlag = true;}		
			//稟議種別・稟議番号は数値
			if(!ValidateUtil.doubleCheck(wsb.get稟議種別())){deleteFlag = true;}
			if(!ValidateUtil.doubleCheck(wsb.get稟議番号())){deleteFlag = true;}
			//重複チェック　同一レコードがあったら、NG
			Iterator<WariteSogoBean> it2 = wariteSogoList.iterator();
			WariteSogoBean wsb2;
			int dupCount=0;
			while (it2.hasNext()){
				wsb2 = it2.next();
				//キー項目がどれかひとつでも違っていれば重複ではない
				if (wsb.get稟議種別().equals(wsb2.get稟議種別()) && wsb.get稟議番号().equals(wsb2.get稟議番号())){
					dupCount++;
				}
				//FWLog.debug("稟議種別："+wsb.get稟議種別()+"稟議種別2："+wsb2.get稟議種別()+"稟議番号："+wsb.get稟議番号()+"稟議番号2："+wsb2.get稟議番号());
			}
			//重複レコードだったらNG
			if(dupCount>1){deleteFlag = true;}

			//チェックに引っかかったら削除
			if(deleteFlag){
				it.remove();
			} else {
				//チェックに引っかからなければ、残りの項目の変換
				wsb.set実行済(ConvertUtil.chkConvertFlag(wsb.get実行済()));
				//【和暦処理】
				wsb.set実行日(ConvertUtil.chkConvertDateAdd0(wsb.get実行日()));
			}

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
	 * 照会名取得メソッド(Static)
	 * 照会名を取得する
	 * 
	 * @return String 照会名
	 */
	public static String getSyokaiName() {
		return syokaiName;
	}
}
