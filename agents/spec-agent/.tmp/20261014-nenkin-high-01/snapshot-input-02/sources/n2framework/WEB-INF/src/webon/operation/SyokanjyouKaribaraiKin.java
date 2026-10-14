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
 * 諸勘定内訳照会 (IN-00750N-99105.xml)の取得とデータ管理、アクセスメソッドの提供
 * 
 * @author	Minori山口
 * 
 * @date	R03.02.08	新規作成
 */
public class SyokanjyouKaribaraiKin extends CommonOperation {
	
	private static final String syokaiName = "諸勘定内訳全照会";
	
	//オペレーションＩＤ
	private final String operationId="OP-SYOKANJYOU-01";
	//ログイン情報
	LoginInfoBean loginInfo;
	//webon引数
	String woKamoku;
	String wokubun;
	String woNenetu;
	String woGetenBr;
	
	String hukuten1;
	String hukuten2;
	String hukuten3;
	
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
	//諸勘定内訳全照会仮払金明細一覧
	List<SyokanjyouKaribaraikinBean> SyokanjyoKaribaraikinBeanList = new ArrayList<SyokanjyouKaribaraikinBean>();
	
	
    //諸勘定内訳全照会仮払金明細
	public class SyokanjyouKaribaraikinBean{
		String 残高 = "";
				
		
		//setter,getter
		public String get残高() {
			return 残高;
		}
		public void set残高(String 残高) {
			this.残高 = 残高;
		}
	}
	
	//setter,getter

	public List<SyokanjyouKaribaraikinBean> getSyokanjyoKaribaraikinBeanList() {
		return SyokanjyoKaribaraikinBeanList;
	}
	public void setSyokanjyoKaribaraikinBeanList(
			List<SyokanjyouKaribaraikinBean> syokanjyoKaribaraikinBeanList) {
		SyokanjyoKaribaraikinBeanList = syokanjyoKaribaraikinBeanList;
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
	 * 諸勘定科目番号・内訳照会区分・原店番号を元に諸勘定内訳（仮払金　14900）照会を取得する
	 * 
	 * @param kamoku		諸勘定科目番号
	 * @param kubun			内訳照会区分
	 * @param gentenBr		原店番号
	 * @param loginInfo		ログイン情報
	 * @param con
	 * @throws Exception
	 */
	public void getWebonSyokanjyou(String kamoku, String kubun, String gentenBr,String hukuten1, String hukuten2, String hukuten3, LoginInfoBean loginInfo, Connection con) throws Exception {
		try{
			//起動チェック 引数がセットされているか
			if (kamoku == null) {throw new Exception("諸勘定科目番号が設定されていません");}
			if (kubun == null) {throw new Exception("内訳照会区分が設定されていません");}
			if (gentenBr == null) {throw new Exception("原店番号が設定されていません");}
			if (con == null) {throw new Exception("ＤＢコネクションが設定されていません");}
			
			//引数のセット
			this.woKamoku=kamoku;
			this.wokubun=kubun;
			this.woGetenBr=gentenBr;
			this.loginInfo = loginInfo;
			
			this.hukuten1 = hukuten1;
			this.hukuten2 = hukuten2;
			this.hukuten3 = hukuten3;
	
			//Webon問合せ実行
			getWebon(con);

			//取得結果解析
			analyzeWeon(woKamoku);

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
		webonBase.put("諸勘定科目番号",woKamoku);
		webonBase.put("内訳照会区分",wokubun);
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

		FWLog.debug(getClass(), "☆★=====ＬＩＮＥデータの解析　スタート　00750N-99203.xml=====★☆");				
		for(int i = 0; i < lineList.size(); i++) {
			
			//明細情報Bean作成
			SyokanjyouKaribaraikinBean Bean = new SyokanjyouKaribaraikinBean();
			String line = lineList.get(i);

			//01出納不足金口　　
			if(i == 2){
				Bean.set残高((line.substring(32,49)));					
				FWLog.debug(getClass(), "★★★★01 出納不足金口　　★"+(line.substring(32,49))+"★");
				//明細リストにビーンを追加
				getSyokanjyoKaribaraikinBeanList().add(Bean);
			}
				
			//******** 母店 ********
			//20 雑口　
			if(i == 21){
				Bean.set残高((line.substring(32,49)));
				FWLog.debug(getClass(), "★★★★20 雑口　　　　　　★"+(line.substring(32,49))+"★");
				//明細リストにビーンを追加
				getSyokanjyoKaribaraikinBeanList().add(Bean);
			}
			
			//21 違算金口
			if(i == 22){
				Bean.set残高((line.substring(32,49)));
				FWLog.debug(getClass(), "★★★★21 違算金口　　　　★"+(line.substring(32,49))+"★");
				//明細リストにビーンを追加
				getSyokanjyoKaribaraikinBeanList().add(Bean);
			}
			
			
			
			//27 出張所雑口　　
			if(i == 28){				
				//******** 出張所１ ********
				if("1".equals(hukuten1)){
					Bean.set残高((line.substring(32,49)));
					FWLog.debug(getClass(), "★★★★27 出張所雑口　　　★"+(line.substring(32,49))+"★");
					//明細リストにビーンを追加
					getSyokanjyoKaribaraikinBeanList().add(Bean);
				}
				
			}
				
			//28 出張所違算金口
			if(i == 29){
				//******** 出張所１ ********
				if("1".equals(hukuten1)){
					Bean.set残高((line.substring(32,49)));
					FWLog.debug(getClass(), "★★★★28 出張所違算金口　★"+(line.substring(32,49))+"★");
					//明細リストにビーンを追加
					getSyokanjyoKaribaraikinBeanList().add(Bean);
				}
			}	
						
		
				
			//58 出張所雑口２　　
			if(i == 61){
				//******** 主張所２ ********
				if("2".equals(hukuten2)){
					Bean.set残高((line.substring(32,49)));
					FWLog.debug(getClass(), "★★★★58 出張所雑口２　　★"+(line.substring(32,49))+"★");
					//明細リストにビーンを追加
					getSyokanjyoKaribaraikinBeanList().add(Bean);
				}					
			}
		
			//59 出張所違算金口２
			if(i == 62){
				//******** 主張所２ ********
				if("2".equals(hukuten2)){			
					Bean.set残高((line.substring(32,49)));
					FWLog.debug(getClass(), "★★★★59 出張所違算金口２★"+(line.substring(32,49))+"★");
					//明細リストにビーンを追加
					getSyokanjyoKaribaraikinBeanList().add(Bean);
				}
			}							
	
			//66 出張所雑口３
			if(i == 69){
				if("3".equals(hukuten3)){
					Bean.set残高((line.substring(32,49)));
					FWLog.debug(getClass(), "★★★★66 出張所雑口３　　★"+(line.substring(32,49))+"★");
					//明細リストにビーンを追加
					getSyokanjyoKaribaraikinBeanList().add(Bean);
				}
			}
			
			//67 出張所違算金口３
			if(i == 70){
				if("3".equals(hukuten3)){
					Bean.set残高((line.substring(32,49)));
					FWLog.debug(getClass(), "★★★★67 出張所違算金口３★"+(line.substring(32,49))+"★");
					//明細リストにビーンを追加
					getSyokanjyoKaribaraikinBeanList().add(Bean);
			
				}
			}
		}
		
		FWLog.debug(getClass(), "★======ＬＩＮＥデータの解析　エンド============★");


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
