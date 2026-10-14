package webon.operation;

import java.sql.Connection;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import webon.WebonBase;
import webon.WebonException;
import webon.operation.WariteSogoShokai.WariteSogoBean;
import webon.util.ConvertUtil;

import common.bean.LoginInfoBean;
import common.util.CommonConverter;
/**
 * Webon汎用照会クラス　証書貸付返済予定表作成照会管理クラス
 * 証書貸付返済予定表作成照会(XML)の取得とデータ管理、アクセスメソッドの提供
 * 
 * @author	吉津
 * 
 * @date	2020.05.13	新規作成
 */
public class ShogashiHensaiYoteiHyoSakusei extends CommonOperation {
	
	private static final String syokaiName = "証書貸付返済予定表作成";
	
	//オペレーションＩＤ
	private final String operationId="OP-SHGASIHE-0001";
	//ログイン情報
	LoginInfoBean loginInfo;
	//webon引数
	String woCif;
	String woBrno;
	String woSyosyoNo;
	
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
	
	//証書貸付返済予定表照会
	private String 当初貸出日 = "";
	private String 貸出期限 = "";
	private String 貸出金額割賦払 = "";
	private String 貸出金額ボーナス払 = "";
	private String 最終償還予定日 = "";
	
	//setter,getter
	public String get当初貸出日() {
		return 当初貸出日;
	}
	public void set当初貸出日(String 当初貸出日) {
		this.当初貸出日 = 当初貸出日;
	}
	public String get貸出期限() {
		return 貸出期限;
	}
	public void set貸出期限(String 貸出期限) {
		this.貸出期限 = 貸出期限;
	}
	public String get貸出金額割賦払() {
		return 貸出金額割賦払;
	}
	public void set貸出金額割賦払(String 貸出金額割賦払) {
		this.貸出金額割賦払 = 貸出金額割賦払;
	}
	public String get貸出金額ボーナス払() {
		return 貸出金額ボーナス払;
	}
	public void set貸出金額ボーナス払(String 貸出金額ボーナス払) {
		this.貸出金額ボーナス払 = 貸出金額ボーナス払;
	}
	public String get最終償還予定日() {
		return 最終償還予定日;
	}
	public void set最終償還予定日(String 最終償還予定日) {
		this.最終償還予定日 = 最終償還予定日;
	}
	
	//証書貸付返済予定表照会明細リスト
	List<ShogashiHensaiBean> ShogashiHensaiList = new ArrayList<ShogashiHensaiBean>();
	
    //証書貸付返済予定表照会明細
	public class ShogashiHensaiBean{
		
		//顧客情報
		String 回次="";
		String 約定返済日="";
		String ボーナス="";
		String 毎回返済額="";
		String 割賦元金="";
		String 利息額="";
		String 計算期間月数="";
		String 計算期間日数="";
		String 残高="";
		String 変動金利未払利息額="";
		
		//setter,getter
		public String get回次() {
			return 回次;
		}
		public void set回次(String 回次) {
			this.回次 = 回次;
		}
		public String get約定返済日() {
			return 約定返済日;
		}
		public void set約定返済日(String 約定返済日) {
			this.約定返済日 = 約定返済日;
		}
		public String getボーナス() {
			return ボーナス;
		}
		public void setボーナス(String ボーナス) {
			this.ボーナス = ボーナス;
		}
		public String get毎回返済額() {
			return 毎回返済額;
		}
		public void set毎回返済額(String 毎回返済額) {
			this.毎回返済額 = 毎回返済額;
		}
		public String get割賦元金() {
			return 割賦元金;
		}
		public void set割賦元金(String 割賦元金) {
			this.割賦元金 = 割賦元金;
		}
		public String get利息額() {
			return 利息額;
		}
		public void set利息額(String 利息額) {
			this.利息額 = 利息額;
		}
		public String get計算期間月数() {
			return 計算期間月数;
		}
		public void set計算期間月数(String 計算期間月数) {
			this.計算期間月数 = 計算期間月数;
		}
		public String get計算期間日数() {
			return 計算期間日数;
		}
		public void set計算期間日数(String 計算期間日数) {
			this.計算期間日数 = 計算期間日数;
		}
		public String get残高() {
			return 残高;
		}
		public void set残高(String 残高) {
			this.残高 = 残高;
		}
		public String get変動金利未払利息額() {
			return 変動金利未払利息額;
		}
		public void set変動金利未払利息額(String 変動金利未払利息額) {
			this.変動金利未払利息額 = 変動金利未払利息額;
		}
	}
	
	//setter,getter
	public List<ShogashiHensaiBean> getShogashiHensaiList() {
		return ShogashiHensaiList;
	}
	public void setShogashiHensaiList(List<ShogashiHensaiBean> shogashiHensaiList) {
		ShogashiHensaiList = shogashiHensaiList;
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
	 * 店番・顧客番号・証書番号を元に証書貸付返済予定表作成照会を取得する
	 * 
	 * @param cif 顧客番号
	 * @param br 店番
	 * @param syosyoNo 証書番号
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
			this.woSyosyoNo=syogashiNo;
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
		webonBase.put("証書番号",woSyosyoNo);
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
		//当初貸出日（4行目、39～47文字）
		if(lineList.size()>5){
			String line = lineList.get(3);
			if(line.length()>46){
				set当初貸出日(line.substring(38,47));
			}
		}
		//貸出金額割賦払(8行目、7～19文字目)
		if(lineList.size()>9){
			String line = lineList.get(7);
			if(line.length()>18){
				set貸出金額割賦払(line.substring(6,19));
			}
		}
		//貸出金額ボーナス払(9行目、7～19文字目)
		if(lineList.size()>10){
			String line = lineList.get(8);
			if(line.length()>18){
				set貸出金額ボーナス払(line.substring(6,19));
			}
		}
		//貸出期限（4行目、49～57文字）
		if(lineList.size()>5){
			String line = lineList.get(3);
			if(line.length()>56){
				set貸出期限(line.substring(48,57));
			}
		}
		//最終償還予定日（8行目、85～93文字）
		if(lineList.size()>9){
			String line = lineList.get(7);
			if(line.length()>92){
				set最終償還予定日(line.substring(84,93));
			}
		}
		//明細リストの作成(16行目～)
		if(lineList.size()>16){
			
			for(int i=15;i<lineList.size();i++){
				//明細情報Bean作成
				ShogashiHensaiBean shBean = new ShogashiHensaiBean();
				String line = lineList.get(i);
				
				//回次（3～4文字目）
				if(line.length()>3){
					shBean.set回次((line.substring(2,4)));
				}
				//約定返済日（7～15文字目）
				if(line.length()>14){
					shBean.set約定返済日((line.substring(6,15)));
				}
				//ボーナス（16文字目）
				if(line.length()>15){
					shBean.set利息額((line.substring(15,16)));
				}
				//毎回返済額（19～31文字目）
				if(line.length()>30){
					shBean.set毎回返済額((line.substring(18,31)));
				}
				//割賦元金（34～44文字目）
				if(line.length()>43){
					shBean.set割賦元金((line.substring(33,44)));
				}
				//利息額（46～56文字目）
				if(line.length()>55){
					shBean.set利息額((line.substring(45,56)));
				}
				/*
				//計算期間月数（～文字目）
				if(line.length()>16){
					shBean.set計算期間月数((line.substring(6,15)));
				}
				//計算期間日数（～文字目）
				if(line.length()>16){
					shBean.set計算期間日数((line.substring(6,15)));
				}
				*/
				//残高（69～81文字目）
				if(line.length()>80){
					shBean.set残高((line.substring(68,81)));
				}
				/*
				//変動金利未払利息額（～文字目）
				if(line.length()>16){
					shBean.set変動金利未払利息額((line.substring(6,15)));
				}
				*/
				//明細リストにビーンを追加
				getShogashiHensaiList().add(shBean);
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
		//和暦⇒西暦変換
		set当初貸出日(ConvertUtil.replaceJPtoAD(get当初貸出日()));
		set貸出期限(ConvertUtil.replaceJPtoAD(get貸出期限()));
		set最終償還予定日(ConvertUtil.replaceJPtoAD(get最終償還予定日()));
		//トリム
		set貸出金額割賦払(get貸出金額割賦払().trim());
		set貸出金額ボーナス払(get貸出金額ボーナス払().trim());
		
		//カンマ除去
		set貸出金額割賦払(ConvertUtil.delComma(get貸出金額割賦払()));
		set貸出金額ボーナス払(ConvertUtil.delComma(get貸出金額ボーナス払()));
		
		for(ShogashiHensaiBean sbean : getShogashiHensaiList()){
			//和暦⇒西暦変換
			sbean.set約定返済日(ConvertUtil.replaceJPtoAD(sbean.get約定返済日()));
			//トリム
			sbean.set毎回返済額(sbean.get毎回返済額().trim());
			sbean.set割賦元金(sbean.get割賦元金().trim());
			sbean.set利息額(sbean.get利息額().trim());
			sbean.set残高(sbean.get残高().trim());
			//カンマ除去
			sbean.set毎回返済額(ConvertUtil.delComma(sbean.get毎回返済額()));
			sbean.set割賦元金(ConvertUtil.delComma(sbean.get割賦元金()));
			sbean.set利息額(ConvertUtil.delComma(sbean.get利息額()));
			sbean.set残高(ConvertUtil.delComma(sbean.get残高()));
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
