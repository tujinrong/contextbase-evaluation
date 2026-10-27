package webon.operation;

import java.sql.Connection;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import webon.WebonBase;
import webon.WebonException;

import common.bean.LoginInfoBean;
/**
 * 01702N-発行手形・小切手登録
 * 
 * @author Minori 山口
 * 
 * @date	R03.03.02	新規作成
 */
public class TegataKogitteTouroku {
	
	//webon情報
	WebonBase webonBase;
	//オペレーションＩＤ
	private final String operationId="OP-HAKKOUTEGATA";
	//ログイン情報
	LoginInfoBean loginInfo;
	
	//webon引数
	String woKozaNo;			//口座番号
	String woTegataNo;      	//手形小切手番号
	String woTegataSyurui;  	//手形小切手種類
	String woMaisu;         	//手形小切手枚数
	String woKubun;         	//手数料徴求区分
	String woTesuryou;      	//手数料
	String woTesuryoJidou;  	//手数料自動徴求
	String woUchiake;       	//手数料内訳
	String woJuyoSyurui;    	//重要印刷物種類
	String woTorikesiNo;    	//取消手形番号
	String woTorikeshiSyurui;	//取消手形種類C
	String woKisanbi;        	//起算日
	String woGentenBr;       	//原店番号

	
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
 * 以下の情報を元に手形小切手登録を行う 
 * 
 * @param  kozaNo		     口座番号
 * @param  tegataNo         手形小切手番号
 * @param  tegataSyurui     手形小切手種類
 * @param  maisu            手形小切手枚数
 * @param  kubbun           手数料徴求区分
 * @param  tesuryou         手数料
 * @param  tesuryoJidou     手数料自動徴求
 * @param  uchiake          手数料内訳
 * @param  juyoSyurui       重要印刷物種類
 * @param  torikesiNo       取消手形番号
 * @param  torikeshiSyurui  取消手形種類C
 * @param  kisanbi          起算日
 * @param  gentenBr         原店番号
 * @param  con
 * @throws Exception
 */
	public void setWebon(	String kozaNo,
							String tegataNo,
							String tegataSyurui,
							String maisu,
							String kubun,
							String tesuryou,
							String tesuryoJidou,
							String uchiake,
							String juyoSyurui,
							String torikesiNo,
							String torikeshiSyurui,
							String kisanbi,
							String gentenBr,
							
							LoginInfoBean loginInfo,
							
							Connection con) throws Exception {
		//引数のセット	
		this.woKozaNo          = kozaNo;
		this.woTegataNo        = tegataNo;
		this.woTegataSyurui    = tegataSyurui;
		this.woMaisu           = maisu;
		this.woKubun           = kubun;
		this.woTesuryou        = tesuryou;
		this.woTesuryoJidou    = tesuryoJidou;
		this.woUchiake         = uchiake;
		this.woJuyoSyurui      = juyoSyurui;
		this.woTorikesiNo      = torikesiNo;
		this.woTorikeshiSyurui = torikeshiSyurui;
		this.woKisanbi         = kisanbi;
		this.woGentenBr        = gentenBr;
			
		this.loginInfo			=loginInfo;
			
			setWebon(con);
			
	}
	/**
	 * 以下の情報を元に手形小切手登録を行う
	 * 各パラメータは事前に設定要
	 * 
	 * @param con
	 * @throws Exception
	 */
	public void setWebon(Connection con) throws Exception {
		
		//起動チェック 必須項目がセットされているか
		if (woKozaNo == null) {throw new Exception("口座番号が設定されていません");}
		if (woTegataNo == null) {throw new Exception("手形小切手種類が設定されていません");}
		if (operationId == null) {throw new Exception("オペレーションＩＤが設定されていません");}
		if (con == null) {throw new Exception("ＤＢコネクションが設定されいません");}
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
		if(woKozaNo != null){webonBase.put("口座番号",woKozaNo);}
		if(woTegataNo != null){webonBase.put("手形小切手番号",woTegataNo);}
		if(woTegataSyurui != null){webonBase.put("手形小切手種類",woTegataSyurui);}
		if(woMaisu != null){webonBase.put("手形小切手枚数",woMaisu);}
		if(woKubun != null){webonBase.put("手数料徴求区分",woMaisu);}
		if(woKubun != null){webonBase.put("手数料",woKubun);}
		if(woTesuryou != null){webonBase.put("手数料自動徴求",woTesuryou);}
		if(woTesuryoJidou != null){webonBase.put("手数料内訳",woTesuryoJidou);}
		if(woUchiake != null){webonBase.put("重要印刷物種類",woUchiake);}
		if(woTorikeshiSyurui != null){webonBase.put("取消手形番号",woTorikeshiSyurui);}
		if(woTorikesiNo != null){webonBase.put("取消手形種類C",woTorikesiNo);}
		if(woKisanbi != null){webonBase.put("起算日",woKisanbi);}
		if(woGentenBr != null){webonBase.put("原店番号",woGentenBr);}
		//問い合わせ
		webonBase.doQuery();
		
		//エラー処理
		if (!webonBase.checkResult()) {
			//エラーコード等をセット
			WebonException e = createWoException("発行手形・小切手登録エラー", ERRLEVEL_ERROR, ERRSPOT_WOGET);
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
	//	e.setBrno(woBrno);
	//	e.setCif(woCif);
		e.setErrStat(el);
		e.setErrSpot(es);
		//エラー処理は上位に任せる
		return e;
	}

}
