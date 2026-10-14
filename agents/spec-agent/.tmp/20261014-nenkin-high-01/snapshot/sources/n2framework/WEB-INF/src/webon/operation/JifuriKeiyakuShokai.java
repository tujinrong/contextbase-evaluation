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
 * Webon汎用照会クラス　自振契約明細照会汎用管理クラス
 * 自振契約明細照会(XML)の取得とデータ管理、アクセスメソッドの提供
 * 
 * @author 吉津
 * 
 * @date	2020.04.16	新規作成
 */
public class JifuriKeiyakuShokai extends CommonOperation{
	
	private static final String syokaiName = "自振契約明細照会";
	
	//オペレーションＩＤ
	private final String operationId="OP-JIFURIKY-0001";
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
	
	//顧客結合照会リスト
	List<JifuriKeiyakuBean> jifuriKeiyakuList = new ArrayList<JifuriKeiyakuBean>();
	
	//自振契約明細照会
	public class JifuriKeiyakuBean{
		//顧客情報
		String 店番="";
		String 顧客番号="";
		String 科目="";
		String 口座番号="";
		String 振替コード="";
		String 振替摘要="";
		String 企業="";
		String 自振契約日="";
		String 最新振替日="";
		
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
		public String get振替コード() {
			return 振替コード;
		}
		public void set振替コード(String 振替コード) {
			this.振替コード = 振替コード;
		}
		public String get振替摘要() {
			return 振替摘要;
		}
		public void set振替摘要(String 振替摘要) {
			this.振替摘要 = 振替摘要;
		}
		public String get企業() {
			return 企業;
		}
		public void set企業(String 企業) {
			this.企業 = 企業;
		}
		public String get自振契約日() {
			return 自振契約日;
		}
		public void set自振契約日(String 自振契約日) {
			this.自振契約日 = 自振契約日;
		}
		public String get最新振替日() {
			return 最新振替日;
		}
		public void set最新振替日(String 最新振替日) {
			this.最新振替日 = 最新振替日;
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
	public List<JifuriKeiyakuBean> getJifuriKeiyakuList() {
		return jifuriKeiyakuList;
	}
	public void setJifuriKeiyakuList(List<JifuriKeiyakuBean> jifuriKeiyakuList) {
		this.jifuriKeiyakuList = jifuriKeiyakuList;
	}

	/**
	 * 店番・顧客番号を元に自振契約明細照会を取得する
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
		final String WOKEY_JIFURI="自振契約明細照会";	//これがroot2
		final String WOKEY_ROOP="明細票";
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
	    		    		if (root2.getNodeName().equals(WOKEY_JIFURI)) {
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
        String wobrno=null;
        String wocustno=null;
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
	    				wobrno=getChildText(child);
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
	    				wocustno=getChildText(child);
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
			JifuriKeiyakuBean bean = new JifuriKeiyakuBean();
			bean.set店番(wobrno);
			bean.set顧客番号(wocustno);
			//項目の取得
//			while (true) {
			for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
				if (elem==null){break;}
				if (elem.getNodeType()==Node.ELEMENT_NODE ){
					if(elem.getNodeName().equals("科目")) {
						bean.set科目(getChildText(elem));
					}else if(elem.getNodeName().equals("口座番号")){
						bean.set口座番号(getChildText(elem));
					}else if(elem.getNodeName().equals("振替コード")){
						bean.set振替コード(getChildText(elem));
					}else if(elem.getNodeName().equals("振替摘要")){
						bean.set振替摘要(getChildText(elem));
					}else if(elem.getNodeName().equals("企業")){
						bean.set企業(getChildText(elem));
					}else if(elem.getNodeName().equals("自振契約日")){
						bean.set自振契約日(getChildText(elem));
					}else if(elem.getNodeName().equals("最新振替日")){
						bean.set最新振替日(getChildText(elem));
					}
				}
	        	//次の子ノードを取得
		    	elem = getNextElement(elem);
				
			}

			//1口座分取得したので、リストに格納
	    	jifuriKeiyakuList.add(bean);
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
		//取得した口座情報分チェックする
		Iterator<JifuriKeiyakuBean> it = jifuriKeiyakuList.iterator();

		//不要レコードの削除
		while (it.hasNext()) {
			JifuriKeiyakuBean jkb = it.next();
			//店顧客のレコードの正規チェックして異常なら取り除く
			if (!autoTransAccCheck(jkb)) {
				it.remove();}
		}
		
		//項目チェック
		it = jifuriKeiyakuList.iterator();
		while(it.hasNext()){
			JifuriKeiyakuBean jkb = it.next();
			
			jkb.set店番(ConvertUtil.chkConvertNumAdd0(jkb.get店番(), 3));
			jkb.set顧客番号(ConvertUtil.chkConvertNumAdd0(jkb.get顧客番号(), 7));
			jkb.set科目(ConvertUtil.chkConvertNumAdd0(jkb.get科目(), 2));
			jkb.set口座番号(ConvertUtil.chkConvertNumAdd0(jkb.get口座番号(), 7));
			jkb.set振替コード(ConvertUtil.chkConvertNumAdd0(jkb.get振替コード(), 3));
			jkb.set振替摘要(ConvertUtil.chkNull(jkb.get振替摘要()));
			jkb.set企業(ConvertUtil.chkConvertNumAdd0(jkb.get企業(),5));
			//【和暦処理】
			jkb.set自振契約日(ConvertUtil.chkConvertDateAdd0(jkb.get自振契約日()));
			jkb.set最新振替日(ConvertUtil.chkConvertDateAdd0(jkb.get最新振替日()));			
		}
	}
	/** 
	 * 自振契約明細照会のループ区間が口座情報かどうかをチェック
	 * @param Connection DB接続
	 * @return boolean 判定結果
	 */
	private boolean autoTransAccCheck(JifuriKeiyakuBean jkb) {
		
		//項目が取得できていなかったらNG
		if (jkb.get科目()==null) {return false;}
		if (jkb.get口座番号()==null) {return false;}
		//ブランクだったらNG
		if (jkb.get科目().isEmpty()) {return false;}
		if (jkb.get口座番号().isEmpty()) {return false;}
		//数値でなかったらNG
		if (!ValidateUtil.numCheck(jkb.get科目())) {return false;}
		if (!ValidateUtil.numCheck(jkb.get口座番号())) {return false;}
		//長さがあっていなかったらNG
		if (jkb.get科目().length()!=2) {return false;}
		//自振契約日のフォーマットチェック
		if (!jkb.get自振契約日().matches("[0-9 ][0-9]-[0-9 ][0-9]-[0-9 ][0-9]")) {return false;}
		return true;
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
