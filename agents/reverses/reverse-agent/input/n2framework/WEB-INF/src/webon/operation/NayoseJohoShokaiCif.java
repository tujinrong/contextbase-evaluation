package webon.operation;

import java.sql.Connection;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.w3c.dom.Node;

import webon.WebonBase;
import webon.WebonException;
import webon.util.ConvertUtil;
import webon.util.FixedValue;

import common.FWLog;
import common.bean.LoginInfoBean;

/**
 * Webon汎用照会クラス　名寄せ情報照会（統一顧客番号による照会）クラス
 * 
 * @author	Minori 岡野
 * 
 * @date	2020.04.10	岡野		webonのFW化対応
 *
 */
public class NayoseJohoShokaiCif extends CommonOperation{

	private static final String syokaiName = "名寄せ情報照会（統一顧客番号による照会）";
	
	//webon情報
	WebonBase webonBase;
	//オペレーションＩＤ
	private final String operationId="OP-UNAYOSEJ-0001";
	//ログイン情報
	LoginInfoBean loginInfo;
	//webon引数
	String woToitsuCif;
	
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
	
	//名寄せ情報照会リスト
	List<NayoseJohoBean> nayoseJohoList = new ArrayList<NayoseJohoBean>();

	//==================================================
	//顧客結合照会
	public class NayoseJohoBean{
		
		//顧客情報
		private String 統一顧客番号="";
		private String 統一カナ氏名 ="";
		private String 統一生年月日="";
		private String 統一電話番号="";
		private String 統一人格Ｃ ="";
		private String 店番="";
		private String 顧客番号="";
		private String 活口座 = "";
		private String 抹消予定 = "";
		
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
		public String get活口座() {
			return 活口座;
		}
		public void set活口座(String 活口座) {
			this.活口座 = 活口座;
		}
		public String get抹消予定() {
			return 抹消予定;
		}
		public void set抹消予定(String 抹消予定) {
			this.抹消予定 = 抹消予定;
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
	public String getWoToitsuCif() {
		return woToitsuCif;
	}
	public void setWoToitsuCif(String woToitsuCif) {
		this.woToitsuCif = woToitsuCif;
	}
	public List<NayoseJohoBean> getNayoseJohoList() {
		return nayoseJohoList;
	}
	public void setNayoseJohoList(List<NayoseJohoBean> nayoseJohoList) {
		this.nayoseJohoList = nayoseJohoList;
	}

	/**
	 * 指定店番・重複を除いた店番のリストを取得
	 * （ソートは実施済み）
	 * 
	 * @return
	 */
	public List<String> getNayoseBrList(String br){
		List<String> uniequeBrList = new ArrayList<String>();
		Set<String> set = new LinkedHashSet<String>();
		//店番の重複排除
		for(NayoseJohoBean njb : getNayoseJohoList()){
			if(!br.equals(njb.get店番())){
				set.add(njb.get店番());	
			}
		}
		//重複排除後の店番をセット
		for(Iterator<String> i = set.iterator();i.hasNext();){
			uniequeBrList.add(i.next());
		}
		return uniequeBrList;
	}
	/**
	 * 指定店番・重複を除いた店番のリストを取得
	 * （抹消予定のレコードは除く）
	 * （ソートは実施済み）
	 * 
	 * @return	
	 */
	public List<String> getNayoseActiveBrList(String br){
		List<String> uniequeBrList = new ArrayList<String>();
		Set<String> set = new LinkedHashSet<String>();
		//店番の重複排除
		for(NayoseJohoBean njb : getNayoseJohoList()){
			if(!br.equals(njb.get店番())){
				FWLog.debug("抹消予定："+njb.get抹消予定()+"活口座:"+njb.get活口座());
				if(njb.get抹消予定().equals("0")&&njb.get活口座().equals("1")){
					set.add(njb.get店番());
				}
			}
		}
		//重複排除後の店番をセット
		for(Iterator<String> i = set.iterator();i.hasNext();){
			uniequeBrList.add(i.next());
		}
		return uniequeBrList;
	}
	
	/**
	 * オーバライドクラス
	 * (NayoseJohoBeanの店番（昇順）・顧客番号（昇順）でソート)
	 * @author Minori 米持
	 * 
	 * @date	H25.08.28	新規作成
	 */
	public class NayoseComparator implements Comparator<NayoseJohoBean> {
	  public int compare(NayoseJohoBean b1, NayoseJohoBean b2) {
		  NayoseJohoBean bean1 = (NayoseJohoBean) b1;
		  NayoseJohoBean bean2 = (NayoseJohoBean) b2;

		  if(bean1.get店番().equals(bean2.get店番())){
			  return bean1.get顧客番号().compareTo(bean2.get顧客番号());
		  }else{
			  return bean1.get店番().compareTo((bean2.get顧客番号()));
		  }
	  }
	}
	
	/**
	 * 統一顧客番号を元に名寄せ情報照会を取得する
	 * 
	 * @param cif 統一顧客番号
	 * @param loginInfo ログイン情報
	 * @param con
	 * @throws Exception
	 */
	public void getWebon(String cif, LoginInfoBean loginInfo, Connection con) throws Exception {
		try{
			//引数チェック 引数がセットされているか
			if (cif == null) {throw new Exception("顧客番号が設定されていません");}
			if (con == null) {throw new Exception("ＤＢコネクションが設定されていません");}
			
			//引数のセット
			this.woToitsuCif = cif;
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
		webonBase.put("統一顧客番号",woToitsuCif);
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
		final String WOKEY_NAYOSE="統一顧客名寄せ情報照会";	//これがroot2
		final String WOKEY_ROOP="店番顧客番号行";
		
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
	    		    		if (root2.getNodeName().equals(WOKEY_NAYOSE)) {
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
        String woCif	=null;
        String woJinkaku=null;
        String woKana	=null;
        String woBirthday	=null;
        String woTel	=null;
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
	            } else if (child.getNodeName().equals("統一顧客番号")){
	    			//必須チェック
	    			if(!getChildText(child).equals("")){
	    				woCif = getChildText(child);
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
	            } else if (child.getNodeName().equals("統一人格C")){
	            	woJinkaku=getChildText(child);
	            } else if (child.getNodeName().equals("統一カナ氏名")){
	            	woKana=getChildText(child);
	            } else if (child.getNodeName().equals("統一生年月日")){
	            	woBirthday=getChildText(child);
	            } else if (child.getNodeName().equals("統一電話番号")){
	            	woTel=getChildText(child);
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
			for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
				if (elem==null){break;}
		    	if (elem.getNodeType()==Node.ELEMENT_NODE && elem.getNodeName().equals("名寄せ店番")) {
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
			    				//データ格納用ビーンの生成
			    				NayoseJohoBean bean = new NayoseJohoBean();
			    				bean.set統一顧客番号(woCif);
			    				bean.set統一人格Ｃ(woJinkaku);
			    				bean.set統一カナ氏名(woKana);
			    				bean.set統一生年月日(woBirthday);
			    				bean.set統一電話番号(woTel);

				    			if (child1.getNodeType()==Node.ELEMENT_NODE && child1.getNodeName().equals("店番")) {
				    				bean.set店番(getChildText(child1));
				    	    	}

				    	    	if (child2.getNodeType()==Node.ELEMENT_NODE && child2.getNodeName().equals("顧客番号")) {
				    	    		bean.set顧客番号(getChildText(child2));
				    	    	}
				    	    	nayoseJohoList.add(bean);
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
				elem = getNextElement(elem);
			}
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
		//項目チェック
		Iterator<NayoseJohoBean> it = nayoseJohoList.iterator();

		//項目チェック
		while(it.hasNext()){
			NayoseJohoBean njb = it.next();

			njb.set統一顧客番号(ConvertUtil.chkConvertNumAdd0(njb.get統一顧客番号(),9));
			njb.set統一人格Ｃ(ConvertUtil.chkConvertNumAdd0(njb.get統一人格Ｃ(),2));
			njb.set統一カナ氏名(ConvertUtil.chkNull(njb.get統一カナ氏名()));
			//【和暦処理】
			njb.set統一生年月日(ConvertUtil.chkConvertGengoDateAdd0(njb.get統一生年月日()));
			njb.set統一電話番号(ConvertUtil.chkConvertTel(njb.get統一電話番号()));
			njb.set店番(ConvertUtil.chkConvertNumAdd0(njb.get店番(),3));
			njb.set顧客番号(ConvertUtil.chkConvertNumAdd0(njb.get顧客番号(),7));
		}

		//ソートして使用することが多いので店番（昇順）顧客番号（昇順）
		Collections.sort(nayoseJohoList, this.new NayoseComparator());
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
