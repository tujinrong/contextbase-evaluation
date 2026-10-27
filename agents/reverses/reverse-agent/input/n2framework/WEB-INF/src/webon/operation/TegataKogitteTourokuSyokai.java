package webon.operation;

import java.sql.Connection;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import webon.WebonBase;
import webon.WebonException;

import common.FWLog;
import common.bean.LoginInfoBean;
/**
 * Webon汎用照会クラス　
 * 手形・小切手登録照会 (IN-00750N-01104-RNZKTM.xml)の取得とデータ管理、アクセスメソッドの提供
 * 
 * @author	Minori山口
 * 
 * @date	R03.02.16	新規作成
 */
public class TegataKogitteTourokuSyokai extends CommonOperation {
	
	private static final String syokaiName = "手形小切手登録照会";
	
	//オペレーションＩＤ
	private final String operationId="OP-TEGATASYOKAI";
	//ログイン情報
	LoginInfoBean loginInfo;
	//webon引数
	String woKouzaNo;
	
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


	private String 顧客番号 = "";	
	
	public String get顧客番号() {
		return 顧客番号;
	}

	public void set顧客番号(String 顧客番号) {
		this.顧客番号 = 顧客番号;
	}
	//日計表資産勘定明細リスト
	List<TegataTourokuBean> TegataTourokuBeanList = new ArrayList<TegataTourokuBean>();
	
	
    //日計表勘定照会明細
	public class TegataTourokuBean{
		String 種類 = "";
		String 登録番号 = "";

		
		//setter,getter
		public String get種類() {
			return 種類;
		}
		public void set種類(String 種類) {
			this.種類 = 種類;
		}
		public String get登録番号() {
			return 登録番号;
		}
		public void set登録番号(String 登録番号) {
			this.登録番号 = 登録番号;
		}
	}
	
	//setter,getter
	
	
	
	public List<Map<String, String>> getEtc() {
		return etc;
	}

	public List<TegataTourokuBean> getTegataTourokuBeanList() {
		return TegataTourokuBeanList;
	}
	public void setTegataTourokuBeanList(
			List<TegataTourokuBean> tegataTourokuBeanList) {
		TegataTourokuBeanList = tegataTourokuBeanList;
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
	
	 	
	/**
	 * 種別コード・周期区分コード・指定年月日・原店番号を元に日計表（資産勘定、負債・純資産勘定、利益勘定、損失勘定）照会を取得する
	 * 
	 * @param syubetu		種別コード（１：残高　２：平残）
	 * @param kubun			周期区分コード
	 * @param nengetu		指定年月日
	 * @param gentenBr		原店番号
	 * @param loginInfo		ログイン情報
	 * @param con
	 * @throws Exception
	 */
	public void getWebonTegata(String KouzaNo, LoginInfoBean loginInfo, Connection con) throws Exception {
		try{
			//起動チェック 引数がセットされているか
			if (KouzaNo == null) {throw new Exception("口座番号が設定されていません");}
			if (con == null) {throw new Exception("ＤＢコネクションが設定されていません");}
			
			//引数のセット
			this.woKouzaNo=KouzaNo;
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
		webonBase.put("口座番号",woKouzaNo);

		//問い合わせ
		webonBase.doQuery();
	

		//結果識別を判定（正常：LINEデータをＤＢに格納、正常以外：エラーをＤＢに格納）
		if (webonBase.checkResult()) {

			//問合せ結果からLINE行を抽出
			ArrayList<String> lineList = getLineByXML();
			for(String line:lineList){
				FWLog.debug(line);
			}
		}else{

			//問合せ結果からエラー情報抽出
			StringBuffer sb=new StringBuffer();
			sb.append(webonBase.getErrMessage());
			String msg=sb.toString();
			FWLog.error(getClass(), msg);
		}
				
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
		//ＬＩＮＥデータの解析
		ArrayList<String> lineList = getLineByXML();

		/**
		*明細を作成する
		*※０行から始まる
		*０行目⇒店番、照会名、照会日、照会時間
		*１行目⇒項目名（顧客番号、口座番号、氏名、ページ）
		*２行目⇒顧客番号、口座番号、氏名、ページ
		*３行目空白号
		*４行目明細の項目名
		*５行目のデータから明細を作成する
		* 
		*/

		String syurui = "";
		String wk_syurui = "";		
		
		if(lineList.size()>0){
			
			FWLog.debug(getClass(), "☆★=====ＬＩＮＥデータの解析 スタート IN-00750N-01104-RNZKTM.xml=====★☆");
			
			for(int i = 0; i < lineList.size(); i++) {
				
					
				//明細情報Bean作成
				TegataTourokuBean Bean = new TegataTourokuBean();
				String line = lineList.get(i);
				
				
				if(i==2){
									
					set顧客番号(line.substring(0,7));		
				}
				
				if(i>=5){
					
					if(line.length() > 0){
					
						wk_syurui = line.substring(0,4);
						if("小切手　".equals(wk_syurui) || "約束手形".equals(wk_syurui) || "＊続く＊".equals(wk_syurui) || "＊終了＊".equals(wk_syurui)){
							
							if("＊続く＊".equals(wk_syurui)){									
								
								//次ページ
								i= i+5;
								
							}else if("＊終了＊".equals(wk_syurui)){
								
								//終わり
																	
							}else{
								
								syurui = line.substring(0,4);
								Bean.set種類(line.substring(0,4));
								Bean.set登録番号(line.substring(8,21));
								//明細リストにビーンを追加
								getTegataTourokuBeanList().add(Bean);
								
								if(line.length() > 42){					
									Bean.set種類(syurui);
									Bean.set登録番号(line.substring(47,60));
									//明細リストにビーンを追加
									getTegataTourokuBeanList().add(Bean);
								}
																	
							}
							
						}else{
	
							Bean.set種類(syurui);
							Bean.set登録番号(line.substring(12,25));
							//明細リストにビーンを追加
							getTegataTourokuBeanList().add(Bean);
							
							
							if(line.length() > 44){
								Bean.set種類(syurui);
								Bean.set登録番号(line.substring(51,64));
								//明細リストにビーンを追加
								getTegataTourokuBeanList().add(Bean);
							}						
						
						}
					}
				}							
			}
			
			FWLog.debug(getClass(), "☆★=====ＬＩＮＥデータの解析　エンド=====★☆");
		}
		

		//エラーチェック(Exceptionの有無を判定する)
		if(errFlg){
			WebonException e = createWoException("Webon取得結果解析エラー", ERRLEVEL_WARNING, ERRSPOT_WOMOLD);
			e.setEtc(etc);
			//エラー処理は上位に任せる
			throw e;
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
		e.setBrno("");
		e.setCif("");
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
