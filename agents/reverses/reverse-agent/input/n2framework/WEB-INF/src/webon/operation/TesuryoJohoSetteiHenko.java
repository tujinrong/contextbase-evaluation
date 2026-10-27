package webon.operation;

import java.sql.Connection;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import webon.WebonBase;
import webon.WebonException;

import common.bean.LoginInfoBean;
/**
 * 10006N-手数料契約情報設定変更
 * 
 * @author Minori 山口
 * 
 * @date	R03.03.02	新規作成
 */
public class TesuryoJohoSetteiHenko {
	
	//webon情報
	WebonBase webonBase;
	//オペレーションＩＤ
	private final String operationId="OP-TESURYOUHENKO";
	//ログイン情報
	LoginInfoBean loginInfo;
	
	
	//webon引数
	String	woSyoriKubun;		//処理区分
	String	woCif;				//顧客番号
	String	woKeiyakuNo;		//契約番号
	String	woTyoukyuBr;		//徴求店番
	String	woTesuryoKamoku;	//徴求科目口番
	String	woTesuryoSyurui;	//手数料種類C
	String	woTesuryoUchiwake;	//手数料内訳C
	String	woTesuryoKubun;		//手数料徴求区分
	String	woTesuryogaku;		//手数料額
	String	woShiteibi;			//徴求指定日
	String	woSyuuki;			//周期
	String	woKaishibi;			//開始年月日
	String	woSyuryobi;			//終了年月日
	String	woKeiyakuKamoku;	//契約科目口番
	String	woDMHakkou;			//DM発行要否
	String	woKeiyakuKubun;		//契約区分
	String	woGentenBr;			//原店番号
	

	//Errorレベル
	private static final int ERRLEVEL_ERROR=0;	//Error
	private static final int ERRLEVEL_WARNING=1;	//Warning
	//Error箇所
	private static final String ERRSPOT_WOGET = "0";		//取得時
//	private static final String ERRSPOT_WOANALYZE = "1";	//解析時
	private static final String ERRSPOT_WOMOLD = "2";		//成型時
	//Error追加情報格納用リスト
	List<Map<String, String>> etc = new ArrayList<Map<String,String>>();
	//Error有無フラグ
	boolean errFlg=false;
	
	private ArrayList<String> lineList = new ArrayList<String>();
	private ArrayList<String> alertList = new ArrayList<String>();
	private String alertMessage;
	
	//setter,getter
	public WebonBase getWebonBase() {
		return webonBase;
	}
	public void setWebonBase(WebonBase webonBase) {
		this.webonBase = webonBase;
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
	public ArrayList<String> getLineList() {
		return lineList;
	}
	public void setLineList(ArrayList<String> lineList) {
		this.lineList = lineList;
	}
	public ArrayList<String> getAlertList() {
		return alertList;
	}
	public void setAlertList(ArrayList<String> alertList) {
		this.alertList = alertList;
	}
	public String getAlertMessage() {
		return alertMessage;
	}
	public void setAlertMessage(String alertMessage) {
		this.alertMessage = alertMessage;
	}

 /**
 * 以下の情報を元に手数料契約情報設定変更を行う 
 * 
 * @param	syoriKubun		処理区分
 * @param	cif				顧客番号
 * @param	keiyakuNo		契約番号
 * @param	tyoukyuBr		徴求店番
 * @param	tesuryoKamoku	徴求科目口番
 * @param	tesuryoSyurui	手数料種類C
 * @param	tesuryoUchiwake	手数料内訳C
 * @param	tesuryoKubun	手数料徴求区分
 * @param	tesuryogaku		手数料額
 * @param	shiteibi		徴求指定日
 * @param	syuuki			周期
 * @param	kaishibi		開始年月日
 * @param	syuryobi		終了年月日
 * @param	keiyakuKaooku	契約科目口番
 * @param	DMHakkou		DM発行要否
 * @param	keiyakuKubun	契約区分
 * @param	gentenBr		原店番号
 * @param  con
 * @throws Exception
 */
	public void setWebon(	String	syoriKubun,							
							String	cif,
							String	keiyakuNo,
							String	tyoukyuBr,
							String	tesuryoKamoku,
							String	tesuryoSyurui,
							String	tesuryoUchiwake,
							String	tesuryoKubun,
							String	tesuryogaku,
							String	shiteibi,
							String	syuuki,
							String	kaishibi,
							String	syuryobi,
							String	keiyakuKaooku,
							String	DMHakkou,
							String	keiyakuKubun,
							String	gentenBr,
							
							LoginInfoBean loginInfo,
							
							Connection con) throws Exception {
		
		//引数のセット	
		this.woSyoriKubun		= syoriKubun;
		this.woCif				= cif;
		this.woKeiyakuNo		= keiyakuNo;
		this.woTyoukyuBr		= tyoukyuBr;
		this.woTesuryoKamoku	= tesuryoKamoku;
		this.woTesuryoSyurui	= tesuryoSyurui;
		this.woTesuryoUchiwake	= tesuryoUchiwake;
		this.woTesuryoKubun		= tesuryoKubun;
		this.woTesuryogaku		= tesuryogaku;
		this.woShiteibi			= shiteibi;
		this.woSyuuki			= syuuki;
		this.woKaishibi			= kaishibi;
		this.woSyuryobi			= syuryobi;
		this.woKeiyakuKamoku	= keiyakuKaooku;
		this.woDMHakkou			= DMHakkou;
		this.woKeiyakuKubun		= keiyakuKubun;
		this.woGentenBr			= gentenBr;		
		this.loginInfo			= loginInfo;
			
		setWebon(con);
			
	}
	/**
	 * 以下の情報を元に手数料契約情報設定変更を行う
	 * 各パラメータは事前に設定要
	 * 
	 * @param con
	 * @throws Exception
	 */
	public void setWebon(Connection con) throws Exception {
		
		//起動チェック 必須項目がセットされているか
		if (woSyoriKubun == null) {throw new Exception("処理区分が設定されていません");}
		if (woCif == null) {throw new Exception("顧客番号が設定されていません");}
		if (woTesuryoKamoku == null) {throw new Exception("手数料種類Cが設定されていません");}
		if (woTesuryogaku == null) {throw new Exception("手数料額が設定されていません");}
		if (woShiteibi == null) {throw new Exception("徴求指定日が設定されていません");}
		if (woKaishibi == null) {throw new Exception("開始年月日が設定されていません");}
		if (woSyuryobi == null) {throw new Exception("終了年月日が設定されていません");}
		if (operationId == null) {throw new Exception("オペレーションＩＤが設定されていません");}
		if (con == null) {throw new Exception("ＤＢコネクションが設定されていません");}
		if (loginInfo == null) {throw new Exception("ログイン情報が設定されていません");}
		
		//Webon問合せ実行
		getWebon(con);
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
		if(	woSyoriKubun != null){webonBase.put("処理区分",	woSyoriKubun);}
		if(	woCif != null){webonBase.put("顧客番号",	woCif);}
		if(	woKeiyakuNo != null){webonBase.put("契約番号",	woKeiyakuNo);}
		if(	woTyoukyuBr	!= null){webonBase.put("徴求店番",	woTyoukyuBr);}
		if(	woTesuryoKamoku	 != null){webonBase.put("徴求科目口番",	woTesuryoKamoku);}
		if(	woTesuryoSyurui	 != null){webonBase.put("手数料種類C",	woTesuryoSyurui);}
		if(	woTesuryoUchiwake	 != null){webonBase.put("手数料内訳C",	woTesuryoUchiwake);}
		if(	woTesuryoKubun	 != null){webonBase.put("手数料徴求区分",	woTesuryoKubun);}
		if(	woTesuryogaku	 != null){webonBase.put("手数料額",	woTesuryogaku);}
		if(	woShiteibi	 != null){webonBase.put("徴求指定日",	woShiteibi);}
		if(	woSyuuki	 != null){webonBase.put("周期",	woSyuuki);}
		if(	woKaishibi	 != null){webonBase.put("開始年月日",	woKaishibi);}
		if(	woSyuryobi	 != null){webonBase.put("終了年月日",	woSyuryobi);}
		if(	woKeiyakuKamoku	 != null){webonBase.put("契約科目口番",	woKeiyakuKamoku);}
		if(	woDMHakkou	 != null){webonBase.put("DM発行要否	",	woDMHakkou);}
		if(	woKeiyakuKubun	 != null){webonBase.put("契約区分	",	woKeiyakuKubun);}
		if(	woGentenBr	 != null){webonBase.put("原店番号",	woGentenBr);}


		//問い合わせ
		webonBase.doQuery();
		
		//エラー処理
		if (!webonBase.checkResult()) {
			//エラーコード等をセット
			WebonException e = createWoException("手数料契約情報設定変更エラー", ERRLEVEL_ERROR, ERRSPOT_WOGET);
			//エラー処理は上位に任せる
			throw e;
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
		e.setBrno(woGentenBr);
	//	e.setCif(wocif);
	//	e.setErrStat(el);
		e.setErrSpot(es);
		//エラー処理は上位に任せる
		return e;
	}

}
