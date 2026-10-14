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
 * 日計表照会（利益勘定）(IN-00750N-99204.xml)の取得とデータ管理、アクセスメソッドの提供
 * 
 * @author	Minori山口
 * 
 * @date	R03.01.07	新規作成
 */
public class NikkiehyouRiekiKanjyou extends CommonOperation {
	
	private static final String syokaiName = "日計表ＤＢ作成";
	
	//オペレーションＩＤ
	private final String operationId="OP-NIKKEI-04";
	//ログイン情報
	LoginInfoBean loginInfo;
	//webon引数
	String woSyubetu;
	String wokubun;
	String woNenetu;
	String woGetenBr;
	
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

	//日計作成
	private String 照会日 = "";
	private String 処理日 = "";
	private String 処理時間 = "";


	public String get照会日() {
		return 照会日;
	}
	public void set照会日(String 照会日) {
		this.照会日 = 照会日;
	}
	public String get処理日() {
		return 処理日;
	}
	public void set処理日(String 処理日) {
		this.処理日 = 処理日;
	}
	public String get処理時間() {
		return 処理時間;
	}
	public void set処理時間(String 処理時間) {
		this.処理時間 = 処理時間;
	}
	//日計表資産勘定明細リスト
	List<NikkeihyouRiekiBean> NikkeihyouRiekiBeanList = new ArrayList<NikkeihyouRiekiBean>();
	
	
    //日計表勘定照会明細
	public class NikkeihyouRiekiBean{
		String 出金額 = "";
		String 入金額 = "";
		String 残高 = "";
		String 月中平残 = "";
		String 期中平残 = "";
				
		
		//setter,getter
		public String get出金額() {
			return 出金額;
		}
		public void set出金額(String 出金額) {
			this.出金額 = 出金額;
		}
		public String get入金額() {
			return 入金額;
		}
		public void set入金額(String 入金額) {
			this.入金額 = 入金額;
		}
		public String get残高() {
			return 残高;
		}
		public void set残高(String 残高) {
			this.残高 = 残高;
		}
		public String get月中平残() {
			return 月中平残;
		}
		public void set月中平残(String 月中平残) {
			this.月中平残 = 月中平残;
		}
		public String get期中平残() {
			return 期中平残;
		}
		public void set期中平残(String 期中平残) {
			this.期中平残 = 期中平残;
		}
	}
	
	//setter,getter	
	public List<NikkeihyouRiekiBean> getNikkeihyouRiekiBeanList() {
		return NikkeihyouRiekiBeanList;
	}
	public void setNikkeihyouRiekiBeanList(
			List<NikkeihyouRiekiBean> nikkeihyouRiekiBeanList) {
		NikkeihyouRiekiBeanList = nikkeihyouRiekiBeanList;
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
	
	
  	
	/**
	 * 種別コード・周期区分コード・指定年月日・原店番号を元に日計表（資産勘定、負債・純資産勘定、利益勘定、損失勘定）照会を取得する
	 * 
	 * @param syubetu		種別コード
	 * @param kubun			周期区分コード
	 * @param nengetu		指定年月日
	 * @param gentenBr		原店番号
	 * @param loginInfo		ログイン情報
	 * @param con
	 * @throws Exception
	 */
	public void getWebonRieki(String syubetu, String kubun, String nengetu, String gentenBr, LoginInfoBean loginInfo, Connection con) throws Exception {
		try{
			//起動チェック 引数がセットされているか
			if (syubetu == null) {throw new Exception("照会種別コードが設定されていません");}
			if (kubun == null) {throw new Exception("周期区分コードが設定されていません");}
			if (nengetu == null) {throw new Exception("指定年月日が設定されていません");}
			if (gentenBr == null) {throw new Exception("原店番号が設定されていません");}
			if (con == null) {throw new Exception("ＤＢコネクションが設定されていません");}
			
			//引数のセット
			this.woSyubetu=syubetu;
			this.wokubun=kubun;
			this.woNenetu=nengetu;
			this.woGetenBr=gentenBr;
			this.loginInfo = loginInfo;
	
			//Webon問合せ実行
			getWebon(con);

			//取得結果解析
			analyzeWeon(woSyubetu);

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
		webonBase.put("照会種別コード",woSyubetu);
		webonBase.put("周期区分コード",wokubun);
		webonBase.put("指定年月日",woNenetu);
		webonBase.put("原店番号",woGetenBr);
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
	public void analyzeWeon(String woSyubetu) throws Exception {
		//ＬＩＮＥデータの解析
		ArrayList<String> lineList = getLineByXML();
				
		
		
		/**
		*明細を作成する
		*※０行から始まる
		*０行目⇒店番、照会日、処理日、処理時間
		*１行目⇒項目名
		*２行目のデータから明細を作成する
		* 
		*/

		FWLog.debug(getClass(), "☆★=====ＬＩＮＥデータの解析　スタート　00750N-99204.xml=====★☆");
					
	
		for(int i = 2; i < lineList.size(); i++) {
			
			if(i == 55){
				
				break;
				
			}else{
						
				//明細情報Bean作成
				NikkeihyouRiekiBean Bean = new NikkeihyouRiekiBean();
				String line = lineList.get(i);
				
				//種別⇒１：残高
				if("1".equals(woSyubetu)){							

					if(line.length()>0){

						//出金額（13～33文字目）
						if("                    ".equals(line.substring(13,33))){
							Bean.set出金額("0");								
							
						}else{						
							Bean.set出金額((line.substring(13,33)));
						}


						//入金額（34～64文字目）
						if("                    ".equals(line.substring(44,64))){
							Bean.set入金額("0");								

						}else{
					
							Bean.set入金額((line.substring(44,64)));
						}


						//残高（64～84文字目）
						if("                    ".equals(line.substring(64,84))){
							Bean.set残高("0");								

						}else{					
							Bean.set残高((line.substring(64,84)));
						}
												
					}else{

						//使用していない項目のため０をセット
						Bean.set出金額("0");
						Bean.set入金額("0");
						Bean.set残高("0");
						
					}		
			
				//種別⇒２：平残
				}else if("2".equals(woSyubetu)){
					
					
					if(line.length()>0){
						
						//月中平残（34～64文字目）
						if("                    ".equals(line.substring(44,64))){
							Bean.set月中平残("0");									

						}else{
					
							Bean.set月中平残((line.substring(44,64)));
						}


						//期中平残（64～84文字目）
						if("                    ".equals(line.substring(64,84))){
							Bean.set期中平残("0");								

						}else{
					
							Bean.set期中平残((line.substring(64,84)));
						}																				
					}else{
						
						//使用していない項目のため０をセット
						Bean.set月中平残("0");
						Bean.set期中平残("0");
					}
				}

				//明細リストにビーンを追加
				getNikkeihyouRiekiBeanList().add(Bean);
									
				//１ページ目が終ったら２ページ目の見出しの２行を足す
				if(i== 31){
					
					i =i + 2;
				}				
			}
		}
		
		
		FWLog.debug(getClass(), "☆★=====ＬＩＮＥデータの解析　エンド　00750N-99204.xml=====★☆");


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
