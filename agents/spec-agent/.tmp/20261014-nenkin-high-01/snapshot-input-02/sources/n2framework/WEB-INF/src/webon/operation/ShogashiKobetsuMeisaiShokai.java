package webon.operation;

import java.sql.Connection;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import webon.WebonBase;
import webon.WebonException;
import webon.util.ConvertUtil;

import common.bean.LoginInfoBean;
/**
 * Webon汎用照会クラス　証書貸付個別明細照会管理クラス
 * 証書貸付個別明細照会(XML)の取得とデータ管理、アクセスメソッドの提供
 * 
 * @author	吉津
 * 
 * @date	2020.05.12	新規作成
 */
public class ShogashiKobetsuMeisaiShokai extends CommonOperation {

	private static final String syokaiName = "証書貸付個別明細照会";
	
	//オペレーションＩＤ
	private final String operationId="OP-SHGASIKO-0001";
	//ログイン情報
	LoginInfoBean loginInfo;
	//webon引数
	String woCif;
	String woBrno;
	String woSyogashiNo;
	
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
	
	//証書貸付個別明細
	private String 初回内入日 = "";
	
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
	public String get初回内入日() {
		return 初回内入日;
	}
	public void set初回内入日(String 初回内入日) {
		this.初回内入日 = 初回内入日;
	}
	
	/**
	 * 店番・顧客番号・証貸番号を元に証書貸付個別明細照会を取得する
	 * 
	 * @param cif 顧客番号
	 * @param br 店番
	 * @param syogashiNo 証貸番号
	 * @param loginInfo ログイン情報
	 * @param con
	 * @throws Exception
	 */
	public void getWebonByCif(String cif,String br, String syogashiNo, LoginInfoBean loginInfo, Connection con) throws Exception {
		try{
			//起動チェック 引数がセットされているか
			if (cif == null) {throw new Exception("顧客番号が設定されていません");}
			if (br == null) {throw new Exception("原店番号が設定されていません");}
			if (syogashiNo == null) {throw new Exception("証貸番号が設定されていません");}
			if (con == null) {throw new Exception("ＤＢコネクションが設定されていません");}
			
			//引数のセット
			this.woBrno=br;
			this.woCif=cif;
			this.woSyogashiNo=syogashiNo;
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
		webonBase.put("証貸番号",woSyogashiNo);
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
		//ＬＩＮＥデータの解析
		ArrayList<String> lineList = getLineByXML();
		//初回内入日（20行目、20～28文字）
		if(lineList.size()>21){
			String line = lineList.get(20);
			if(line.length()>29){
				set初回内入日(line.substring(19,28));
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
		set初回内入日(ConvertUtil.replaceJPtoAD(get初回内入日()));
		
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
	 * 照会名取得メソッド(Static)
	 * 照会名を取得する
	 * 
	 * @return String 照会名
	 */
	public static String getSyokaiName() {
		return syokaiName;
	}
}
