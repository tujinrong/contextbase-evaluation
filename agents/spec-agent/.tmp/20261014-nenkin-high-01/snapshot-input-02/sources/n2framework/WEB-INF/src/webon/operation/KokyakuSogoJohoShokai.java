package webon.operation;

import java.sql.Connection;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import webon.WebonBase;
import webon.WebonException;
import webon.util.ConvertUtil;
import webon.util.FixedValue;
import org.w3c.dom.Node;
import common.FWLog;
import common.bean.LoginInfoBean;

/**
 * Webon汎用照会クラス　顧客総合情報照会管理クラス
 * 顧客総合情報照会(XML)の取得とデータ管理、アクセスメソッドの提供
 * 
 * @author 京極
 * 
 * @date	2020.02.12	京極			webonのFW化対応
 */
public class KokyakuSogoJohoShokai extends CommonOperation {

	//オペレーションＩＤ
	private final String operationId="OP-SOGOJOHO-0001";
	//ログイン情報
	LoginInfoBean loginInfo;
	//webon引数
	String woCif;
	String woBrno;
	String woKamoku;
	String woKoza;
	
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
	
	//顧客総合情報照会
	private String 店舗番号 = "";
	private String 顧客番号 = "";
	private String カナ氏名 = "";
	private String 漢字氏名 = "";
	private String 活口座 = "";
	private String 抹消予定 = "";
	private String 人格 = "";
	private String 元号生設立年月日 = "";
	private String 預金保険カナ氏名 = "";
	private String 統一カナ氏名 = "";
	private String 業種コード = "";
	private String 統一顧客番号 = "";
	private String 統一顧客人格 = "";
	private String 統一顧客元号生設立年月日 = "";
	private String 統一顧客電話番号 = "";
	private String 統一顧客関連情報名寄件数 = "";
	private String 統一顧客データ整備済コード = "";
	private String 国籍情報 = "";
	private String 担当者 = "";
	private String 店舗担当地区 = "";
	private String 移管事由 = "";
	private String 移受管店番顧客番号 = "";
	private String 移受管日 = "";
	private String 代表者資格 = "";
	private String 勤務先電話番号 = "";
	private String 付属名称 = "";
	private String 電話番号 = "";
	private String 携帯電話番号 = "";
	private String 第二電話番号 = "";
	private String 住所印字 = "";
	private String 訪問先 = "";
	private String 住所コード = "";
	private String 第二住所コード = "";
	private String 郵便番号 = "";
	private String 住所一行目 = "";
	private String 住所二行目 = "";
	private String 第二住所郵便番号 = "";
	private String 第二住所一行目 = "";
	private String 第二住所二行目 = "";
	private String カナ補助住所 = "";
	private String 家族取引数 = "";
	private String 関連顧客数 = "";
	private String 出資基本 = "";
	private String 会員 = "";
	private String 活口座数当座 = "";
	private String 活口座数普通 = "";
	private String 活口座数貯蓄 = "";
	private String 活口座数定期 = "";
	private String 活口座数通知 = "";
	private String 活口座数定積 = "";
	private String 活口座数積定 = "";
	private String 活口座数別段 = "";
	private String 活口座数債券 = "";
	private String 活口座数納税 = "";
	private String 活口座数職員 = "";
	private String 時効解約口座数 = "";
	private String SW件数 = "";
	private String 総合口座 = "";
	private String 投信契約有 = "";
	private String 特定口座契約有 = "";
	private String 預金マル優申告額千円 = "";
	private String 債券マル優申告額千円 = "";
	private String マル財申告額千円 = "";
	private String マル特申告額千円 = "";
	private String 投信マル優申告額千円 = "";
	private String 融資基本 = "";
	private String 融資抹消 = "";
	private String 割手 = "";
	private String 手貸 = "";
	private String 証貸 = "";
	private String 代理貸 = "";
	private String 債務保証 = "";
	private String 住公契約 = "";
	private String 当貸契約 = "";
	private String 個人CL = "";		
	private String 事業者CL = "";		
	private String IP電話番号 = "";
	private String 第二IP電話番号 = "";
	private String 電債決済口座数 = "";
	private String 定例発行契約自動発行 = "";
	private String 振込登録件数 = "";
	private String 為替自動振込件数 = "";
	private String 貸金庫 = "";
	private String 夜間金庫 = "";
	private String 諸届け = "";
	private String 外為 = "";
	private String 共有名義 = "";
	private String 金庫任意一 = "";
	private String 金庫任意二 = "";
	private String 金庫任意三 = "";
	private String 給振件数 = "";
	private String 給与振込 = "";
	private String 給与最新振込日 = "";
	private String 年金件数 = "";
	private String 年金振込 = "";
	private String 年金最新振込日 = "";
	private String FB契約 = "";
	private String WEBFB契約 = "";
	private String HB契約数 = "";
	private String ANS代表 = "";
	private String ANS照会数 = "";
	private String ANS通知数 = "";
	private String コール契約 = "";
	private String IB代表店番 = "";
	private String IB代表科目口座番号 = "";
	private String AA契約口座数 = "";
	private String サークル一 = "";
	private String サークル二 = "";
	private String サークル三 = "";
	private String サークル四 = "";
	private String サークル五 = "";
	private String サークル六 = "";
	private String サークル七 = "";
	private String サークル八 = "";
	private String サークル九 = "";
	private String サークル十 = "";
	private String サークル十一 = "";
	private String サークル十二 = "";
	private String サークル十三 = "";
	private String サークル十四 = "";
	private String サークル十五 = "";
	
	//setter,getter
	public String get店舗番号() {
		return 店舗番号;
	}
	public void set店舗番号(String 店舗番号) {
		this.店舗番号 = 店舗番号;
	}
	public String get顧客番号() {
		return 顧客番号;
	}
	public void set顧客番号(String 顧客番号) {
		this.顧客番号 = 顧客番号;
	}
	public String getカナ氏名() {
		return カナ氏名;
	}
	public void setカナ氏名(String カナ氏名) {
		this.カナ氏名 = カナ氏名;
	}
	public String get漢字氏名() {
		return 漢字氏名;
	}
	public void set漢字氏名(String 漢字氏名) {
		this.漢字氏名 = 漢字氏名;
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
	public String get人格() {
		return 人格;
	}
	public void set人格(String 人格) {
		this.人格 = 人格;
	}
	public String get元号生設立年月日() {
		return 元号生設立年月日;
	}
	public void set元号生設立年月日(String 元号生設立年月日) {
		this.元号生設立年月日 = 元号生設立年月日;
	}
	public String get預金保険カナ氏名() {
		return 預金保険カナ氏名;
	}
	public void set預金保険カナ氏名(String 預金保険カナ氏名) {
		this.預金保険カナ氏名 = 預金保険カナ氏名;
	}
	public String get統一顧客関連情報名寄件数() {
		return 統一顧客関連情報名寄件数;
	}
	public void set統一顧客関連情報名寄件数(String 統一顧客関連情報名寄件数) {
		this.統一顧客関連情報名寄件数 = 統一顧客関連情報名寄件数;
	}
	public String get国籍情報() {
		return 国籍情報;
	}
	public void set国籍情報(String 国籍情報) {
		this.国籍情報 = 国籍情報;
	}
	public String get住所印字() {
		return 住所印字;
	}
	public void set住所印字(String 住所印字) {
		this.住所印字 = 住所印字;
	}
	public String get郵便番号() {
		return 郵便番号;
	}
	public void set郵便番号(String 郵便番号) {
		this.郵便番号 = 郵便番号;
	}
	public String get第二住所郵便番号() {
		return 第二住所郵便番号;
	}
	public void set第二住所郵便番号(String 第二住所郵便番号) {
		this.第二住所郵便番号 = 第二住所郵便番号;
	}
	public String get家族取引数() {
		return 家族取引数;
	}
	public void set家族取引数(String 家族取引数) {
		this.家族取引数 = 家族取引数;
	}
	public String get関連顧客数() {
		return 関連顧客数;
	}
	public void set関連顧客数(String 関連顧客数) {
		this.関連顧客数 = 関連顧客数;
	}
	public String get統一カナ氏名() {
		return 統一カナ氏名;
	}
	public void set統一カナ氏名(String 統一カナ氏名) {
		this.統一カナ氏名 = 統一カナ氏名;
	}
	public String get業種コード() {
		return 業種コード;
	}
	public void set業種コード(String 業種コード) {
		this.業種コード = 業種コード;
	}
	public String get統一顧客番号() {
		return 統一顧客番号;
	}
	public void set統一顧客番号(String 統一顧客番号) {
		this.統一顧客番号 = 統一顧客番号;
	}
	public String get統一顧客人格() {
		return 統一顧客人格;
	}
	public void set統一顧客人格(String 統一顧客人格) {
		this.統一顧客人格 = 統一顧客人格;
	}
	public String get統一顧客元号生設立年月日() {
		return 統一顧客元号生設立年月日;
	}
	public void set統一顧客元号生設立年月日(String 統一顧客元号生設立年月日) {
		this.統一顧客元号生設立年月日 = 統一顧客元号生設立年月日;
	}
	public String get統一顧客電話番号() {
		return 統一顧客電話番号;
	}
	public void set統一顧客電話番号(String 統一顧客電話番号) {
		this.統一顧客電話番号 = 統一顧客電話番号;
	}
	public String get統一顧客データ整備済コード() {
		return 統一顧客データ整備済コード;
	}
	public void set統一顧客データ整備済コード(String 統一顧客データ整備済コード) {
		this.統一顧客データ整備済コード = 統一顧客データ整備済コード;
	}
	public String get担当者() {
		return 担当者;
	}
	public void set担当者(String 担当者) {
		this.担当者 = 担当者;
	}
	public String get店舗担当地区() {
		return 店舗担当地区;
	}
	public void set店舗担当地区(String 店舗担当地区) {
		this.店舗担当地区 = 店舗担当地区;
	}
	public String get移管事由() {
		return 移管事由;
	}
	public void set移管事由(String 移管事由) {
		this.移管事由 = 移管事由;
	}
	public String get移受管店番顧客番号() {
		return 移受管店番顧客番号;
	}
	public void set移受管店番顧客番号(String 移受管店番顧客番号) {
		this.移受管店番顧客番号 = 移受管店番顧客番号;
	}
	public String get移受管日() {
		return 移受管日;
	}
	public void set移受管日(String 移受管日) {
		this.移受管日 = 移受管日;
	}
	public String get代表者資格() {
		return 代表者資格;
	}
	public void set代表者資格(String 代表者資格) {
		this.代表者資格 = 代表者資格;
	}
	public String get勤務先電話番号() {
		return 勤務先電話番号;
	}
	public void set勤務先電話番号(String 勤務先電話番号) {
		this.勤務先電話番号 = 勤務先電話番号;
	}
	public String get付属名称() {
		return 付属名称;
	}
	public void set付属名称(String 付属名称) {
		this.付属名称 = 付属名称;
	}
	public String get電話番号() {
		return 電話番号;
	}
	public void set電話番号(String 電話番号) {
		this.電話番号 = 電話番号;
	}
	public String get携帯電話番号() {
		return 携帯電話番号;
	}
	public void set携帯電話番号(String 携帯電話番号) {
		this.携帯電話番号 = 携帯電話番号;
	}
	public String get第二電話番号() {
		return 第二電話番号;
	}
	public void set第二電話番号(String 第二電話番号) {
		this.第二電話番号 = 第二電話番号;
	}
	public String get訪問先() {
		return 訪問先;
	}
	public void set訪問先(String 訪問先) {
		this.訪問先 = 訪問先;
	}
	public String get住所コード() {
		return 住所コード;
	}
	public void set住所コード(String 住所コード) {
		this.住所コード = 住所コード;
	}
	public String get第二住所コード() {
		return 第二住所コード;
	}
	public void set第二住所コード(String 第二住所コード) {
		this.第二住所コード = 第二住所コード;
	}
	public String get住所一行目() {
		return 住所一行目;
	}
	public void set住所一行目(String 住所一行目) {
		this.住所一行目 = 住所一行目;
	}
	public String get住所二行目() {
		return 住所二行目;
	}
	public void set住所二行目(String 住所二行目) {
		this.住所二行目 = 住所二行目;
	}
	public String get第二住所一行目() {
		return 第二住所一行目;
	}
	public void set第二住所一行目(String 第二住所一行目) {
		this.第二住所一行目 = 第二住所一行目;
	}
	public String get第二住所二行目() {
		return 第二住所二行目;
	}
	public void set第二住所二行目(String 第二住所二行目) {
		this.第二住所二行目 = 第二住所二行目;
	}
	public String getカナ補助住所() {
		return カナ補助住所;
	}
	public void setカナ補助住所(String カナ補助住所) {
		this.カナ補助住所 = カナ補助住所;
	}
	public String get出資基本() {
		return 出資基本;
	}
	public void set出資基本(String 出資基本) {
		this.出資基本 = 出資基本;
	}
	public String get会員() {
		return 会員;
	}
	public void set会員(String 会員) {
		this.会員 = 会員;
	}
	public String get活口座数当座() {
		return 活口座数当座;
	}
	public void set活口座数当座(String 活口座数当座) {
		this.活口座数当座 = 活口座数当座;
	}
	public String get活口座数普通() {
		return 活口座数普通;
	}
	public void set活口座数普通(String 活口座数普通) {
		this.活口座数普通 = 活口座数普通;
	}
	public String get活口座数貯蓄() {
		return 活口座数貯蓄;
	}
	public void set活口座数貯蓄(String 活口座数貯蓄) {
		this.活口座数貯蓄 = 活口座数貯蓄;
	}
	public String get活口座数定期() {
		return 活口座数定期;
	}
	public void set活口座数定期(String 活口座数定期) {
		this.活口座数定期 = 活口座数定期;
	}
	public String get活口座数通知() {
		return 活口座数通知;
	}
	public void set活口座数通知(String 活口座数通知) {
		this.活口座数通知 = 活口座数通知;
	}
	public String get活口座数定積() {
		return 活口座数定積;
	}
	public void set活口座数定積(String 活口座数定積) {
		this.活口座数定積 = 活口座数定積;
	}
	public String get活口座数積定() {
		return 活口座数積定;
	}
	public void set活口座数積定(String 活口座数積定) {
		this.活口座数積定 = 活口座数積定;
	}
	public String get活口座数別段() {
		return 活口座数別段;
	}
	public void set活口座数別段(String 活口座数別段) {
		this.活口座数別段 = 活口座数別段;
	}
	public String get活口座数債券() {
		return 活口座数債券;
	}
	public void set活口座数債券(String 活口座数債券) {
		this.活口座数債券 = 活口座数債券;
	}
	public String get活口座数納税() {
		return 活口座数納税;
	}
	public void set活口座数納税(String 活口座数納税) {
		this.活口座数納税 = 活口座数納税;
	}
	public String get活口座数職員() {
		return 活口座数職員;
	}
	public void set活口座数職員(String 活口座数職員) {
		this.活口座数職員 = 活口座数職員;
	}
	public String get時効解約口座数() {
		return 時効解約口座数;
	}
	public void set時効解約口座数(String 時効解約口座数) {
		this.時効解約口座数 = 時効解約口座数;
	}
	public String getSW件数() {
		return SW件数;
	}
	public void setSW件数(String sW件数) {
		SW件数 = sW件数;
	}
	public String get総合口座() {
		return 総合口座;
	}
	public void set総合口座(String 総合口座) {
		this.総合口座 = 総合口座;
	}
	public String get投信契約有() {
		return 投信契約有;
	}
	public void set投信契約有(String 投信契約有) {
		this.投信契約有 = 投信契約有;
	}
	public String get特定口座契約有() {
		return 特定口座契約有;
	}
	public void set特定口座契約有(String 特定口座契約有) {
		this.特定口座契約有 = 特定口座契約有;
	}
	public String get預金マル優申告額千円() {
		return 預金マル優申告額千円;
	}
	public void set預金マル優申告額千円(String 預金マル優申告額千円) {
		this.預金マル優申告額千円 = 預金マル優申告額千円;
	}
	public String get債券マル優申告額千円() {
		return 債券マル優申告額千円;
	}
	public void set債券マル優申告額千円(String 債券マル優申告額千円) {
		this.債券マル優申告額千円 = 債券マル優申告額千円;
	}
	public String getマル財申告額千円() {
		return マル財申告額千円;
	}
	public void setマル財申告額千円(String マル財申告額千円) {
		this.マル財申告額千円 = マル財申告額千円;
	}
	public String getマル特申告額千円() {
		return マル特申告額千円;
	}
	public void setマル特申告額千円(String マル特申告額千円) {
		this.マル特申告額千円 = マル特申告額千円;
	}
	public String get投信マル優申告額千円() {
		return 投信マル優申告額千円;
	}
	public void set投信マル優申告額千円(String 投信マル優申告額千円) {
		this.投信マル優申告額千円 = 投信マル優申告額千円;
	}
	public String get融資基本() {
		return 融資基本;
	}
	public void set融資基本(String 融資基本) {
		this.融資基本 = 融資基本;
	}
	public String get融資抹消() {
		return 融資抹消;
	}
	public void set融資抹消(String 融資抹消) {
		this.融資抹消 = 融資抹消;
	}
	public String get割手() {
		return 割手;
	}
	public void set割手(String 割手) {
		this.割手 = 割手;
	}
	public String get手貸() {
		return 手貸;
	}
	public void set手貸(String 手貸) {
		this.手貸 = 手貸;
	}
	public String get証貸() {
		return 証貸;
	}
	public void set証貸(String 証貸) {
		this.証貸 = 証貸;
	}
	public String get代理貸() {
		return 代理貸;
	}
	public void set代理貸(String 代理貸) {
		this.代理貸 = 代理貸;
	}
	public String get債務保証() {
		return 債務保証;
	}
	public void set債務保証(String 債務保証) {
		this.債務保証 = 債務保証;
	}
	public String get住公契約() {
		return 住公契約;
	}
	public void set住公契約(String 住公契約) {
		this.住公契約 = 住公契約;
	}
	public String get当貸契約() {
		return 当貸契約;
	}
	public void set当貸契約(String 当貸契約) {
		this.当貸契約 = 当貸契約;
	}
	public String get個人CL() {
		return 個人CL;
	}
	public void set個人CL(String 個人cl) {
		個人CL = 個人cl;
	}
	public String get事業者CL() {
		return 事業者CL;
	}
	public void set事業者CL(String 事業者cl) {
		事業者CL = 事業者cl;
	}
	public String getIP電話番号() {
		return IP電話番号;
	}
	public void setIP電話番号(String iP電話番号) {
		IP電話番号 = iP電話番号;
	}
	public String get第二IP電話番号() {
		return 第二IP電話番号;
	}
	public void set第二IP電話番号(String 第二ip電話番号) {
		第二IP電話番号 = 第二ip電話番号;
	}
	public String get電債決済口座数() {
		return 電債決済口座数;
	}
	public void set電債決済口座数(String 電債決済口座数) {
		this.電債決済口座数 = 電債決済口座数;
	}
	public String get定例発行契約自動発行() {
		return 定例発行契約自動発行;
	}
	public void set定例発行契約自動発行(String 定例発行契約自動発行) {
		this.定例発行契約自動発行 = 定例発行契約自動発行;
	}
	public String get振込登録件数() {
		return 振込登録件数;
	}
	public void set振込登録件数(String 振込登録件数) {
		this.振込登録件数 = 振込登録件数;
	}
	public String get為替自動振込件数() {
		return 為替自動振込件数;
	}
	public void set為替自動振込件数(String 為替自動振込件数) {
		this.為替自動振込件数 = 為替自動振込件数;
	}
	public String get貸金庫() {
		return 貸金庫;
	}
	public void set貸金庫(String 貸金庫) {
		this.貸金庫 = 貸金庫;
	}
	public String get夜間金庫() {
		return 夜間金庫;
	}
	public void set夜間金庫(String 夜間金庫) {
		this.夜間金庫 = 夜間金庫;
	}
	public String get諸届け() {
		return 諸届け;
	}
	public void set諸届け(String 諸届け) {
		this.諸届け = 諸届け;
	}
	public String get外為() {
		return 外為;
	}
	public void set外為(String 外為) {
		this.外為 = 外為;
	}
	public String get共有名義() {
		return 共有名義;
	}
	public void set共有名義(String 共有名義) {
		this.共有名義 = 共有名義;
	}
	public String get金庫任意一() {
		return 金庫任意一;
	}
	public void set金庫任意一(String 金庫任意一) {
		this.金庫任意一 = 金庫任意一;
	}
	public String get金庫任意二() {
		return 金庫任意二;
	}
	public void set金庫任意二(String 金庫任意二) {
		this.金庫任意二 = 金庫任意二;
	}
	public String get金庫任意三() {
		return 金庫任意三;
	}
	public void set金庫任意三(String 金庫任意三) {
		this.金庫任意三 = 金庫任意三;
	}
	public String get給振件数() {
		return 給振件数;
	}
	public void set給振件数(String 給振件数) {
		this.給振件数 = 給振件数;
	}
	public String get給与振込() {
		return 給与振込;
	}
	public void set給与振込(String 給与振込) {
		this.給与振込 = 給与振込;
	}
	public String get給与最新振込日() {
		return 給与最新振込日;
	}
	public void set給与最新振込日(String 給与最新振込日) {
		this.給与最新振込日 = 給与最新振込日;
	}
	public String get年金件数() {
		return 年金件数;
	}
	public void set年金件数(String 年金件数) {
		this.年金件数 = 年金件数;
	}
	public String get年金振込() {
		return 年金振込;
	}
	public void set年金振込(String 年金振込) {
		this.年金振込 = 年金振込;
	}
	public String get年金最新振込日() {
		return 年金最新振込日;
	}
	public void set年金最新振込日(String 年金最新振込日) {
		this.年金最新振込日 = 年金最新振込日;
	}
	public String getFB契約() {
		return FB契約;
	}
	public void setFB契約(String fB契約) {
		FB契約 = fB契約;
	}
	public String getWEBFB契約() {
		return WEBFB契約;
	}
	public void setWEBFB契約(String wEBFB契約) {
		WEBFB契約 = wEBFB契約;
	}
	public String getHB契約数() {
		return HB契約数;
	}
	public void setHB契約数(String hB契約数) {
		HB契約数 = hB契約数;
	}
	public String getANS代表() {
		return ANS代表;
	}
	public void setANS代表(String aNS代表) {
		ANS代表 = aNS代表;
	}
	public String getANS照会数() {
		return ANS照会数;
	}
	public void setANS照会数(String aNS照会数) {
		ANS照会数 = aNS照会数;
	}
	public String getANS通知数() {
		return ANS通知数;
	}
	public void setANS通知数(String aNS通知数) {
		ANS通知数 = aNS通知数;
	}
	public String getコール契約() {
		return コール契約;
	}
	public void setコール契約(String コール契約) {
		this.コール契約 = コール契約;
	}
	public String getIB代表店番() {
		return IB代表店番;
	}
	public void setIB代表店番(String iB代表店番) {
		IB代表店番 = iB代表店番;
	}
	public String getIB代表科目口座番号() {
		return IB代表科目口座番号;
	}
	public void setIB代表科目口座番号(String iB代表科目口座番号) {
		IB代表科目口座番号 = iB代表科目口座番号;
	}
	public String getAA契約口座数() {
		return AA契約口座数;
	}
	public void setAA契約口座数(String aA契約口座数) {
		AA契約口座数 = aA契約口座数;
	}
	public String getサークル一() {
		return サークル一;
	}
	public void setサークル一(String サークル一) {
		this.サークル一 = サークル一;
	}
	public String getサークル二() {
		return サークル二;
	}
	public void setサークル二(String サークル二) {
		this.サークル二 = サークル二;
	}
	public String getサークル三() {
		return サークル三;
	}
	public void setサークル三(String サークル三) {
		this.サークル三 = サークル三;
	}
	public String getサークル四() {
		return サークル四;
	}
	public void setサークル四(String サークル四) {
		this.サークル四 = サークル四;
	}
	public String getサークル五() {
		return サークル五;
	}
	public void setサークル五(String サークル五) {
		this.サークル五 = サークル五;
	}
	public String getサークル六() {
		return サークル六;
	}
	public void setサークル六(String サークル六) {
		this.サークル六 = サークル六;
	}
	public String getサークル七() {
		return サークル七;
	}
	public void setサークル七(String サークル七) {
		this.サークル七 = サークル七;
	}
	public String getサークル八() {
		return サークル八;
	}
	public void setサークル八(String サークル八) {
		this.サークル八 = サークル八;
	}
	public String getサークル九() {
		return サークル九;
	}
	public void setサークル九(String サークル九) {
		this.サークル九 = サークル九;
	}
	public String getサークル十() {
		return サークル十;
	}
	public void setサークル十(String サークル十) {
		this.サークル十 = サークル十;
	}
	public String getサークル十一() {
		return サークル十一;
	}
	public void setサークル十一(String サークル十一) {
		this.サークル十一 = サークル十一;
	}
	public String getサークル十二() {
		return サークル十二;
	}
	public void setサークル十二(String サークル十二) {
		this.サークル十二 = サークル十二;
	}
	public String getサークル十三() {
		return サークル十三;
	}
	public void setサークル十三(String サークル十三) {
		this.サークル十三 = サークル十三;
	}
	public String getサークル十四() {
		return サークル十四;
	}
	public void setサークル十四(String サークル十四) {
		this.サークル十四 = サークル十四;
	}
	public String getサークル十五() {
		return サークル十五;
	}
	public void setサークル十五(String サークル十五) {
		this.サークル十五 = サークル十五;
	}
	//getter(編集値)
	public String get住所() {
		return 住所一行目+住所二行目;
	}
	public String get第2住所() {
		return 第二住所一行目+第二住所二行目;
	}
	public String get金庫任意() {
		return 金庫任意一+金庫任意二+金庫任意三;
	}
	public String getIB代表科目() {
		//代表科目口座番号の桁数チェック、9桁無ければエンプティを返す。
		if(9<=getIB代表科目口座番号().length()){
			return getIB代表科目口座番号().substring(0,2);		//IB代表科目口座番号の上2桁;
		}else{
			return "";
		}
	}
	public String getIB代表口座番号() {
		//代表科目口座番号の桁数チェック、9桁無ければエンプティを返す。
		if(9<=getIB代表科目口座番号().length()){
			return getIB代表科目口座番号().substring(2,9);//IB代表科目口座番号の下7桁
		}else{
			return "";
		}
	}
	public String getサークル() {
		return サークル一+サークル二+サークル三+サークル四+サークル五+サークル六+サークル七+サークル八
		+サークル九+サークル十+サークル十一+サークル十二+サークル十三+サークル十四+サークル十五;
	}
	
	/**
	 * 顧客番号・店番を元に総合情報照会を取得する
	 * 
	 * @param cif 顧客番号
	 * @param brno 店番
	 * @param loginInfo ログイン情報
	 * @param con
	 * @throws WebonException
	 * @throws Exception
	 */
	public void getWebonByCif(String cif, String brno, LoginInfoBean loginInfo, Connection con) throws WebonException, Exception{
		try{
			//引数チェック 引数がセットされているか
			if (cif == null) {throw new Exception("顧客番号が設定されていません");}
			if (brno == null) {throw new Exception("原店番号が設定されていません");}
			if (con == null) {throw new Exception("ＤＢコネクションが設定されていません");}
			
			//引数のセット
			this.woCif=cif;
			this.woBrno=brno;
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
	 * 店番・科目・口座番号を元に総合情報照会を取得する
	 * 
	 * @param brno	 店番
	 * @param kamoku 科目コード
	 * @param koza	 口座番号
	 * @param loginInfo ログイン情報
	 * @param con
	 * @throws WebonException
	 * @throws Exception
	 */
	public void getWebonByAcc(String brno, String kamoku, String koza, LoginInfoBean loginInfo, Connection con) throws WebonException, Exception{
		try{
			
			//引数チェック 引数がセットされているか
			if (brno == null) {throw new Exception("原店番号が設定されていません");}
			if (kamoku == null) {throw new Exception("科目コードが設定されていません");}
			if (koza == null) {throw new Exception("口座番号が設定されていません");}
			if (con == null) {throw new Exception("ＤＢコネクションが設定されていません");}
			
			//引数のセット
			this.woBrno=brno;
			this.woKamoku=kamoku;
			this.woKoza=koza;
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

		//設定値（必須項目は事前チェックしてあることが前提）
		if (woCif != null) {webonBase.put("顧客番号",woCif);}
		if (woBrno != null) {webonBase.put("原店番号",woBrno);}
		if (woKamoku != null) {webonBase.put("科目コード",woKamoku);}
		if (woKoza != null) {webonBase.put("口座番号",woKoza);}

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
	private void analyzeWeon() throws Exception {
		//WEBON結果走査用固定値
		final String WOKEY_TSUCYO="通帳部宛";
		final String WOKEY_SOGOJOHO="顧客総合情報照会";
		
		//起動チェック、webonが取得されているか
		if (webonBase==null) {
			StringBuilder errmsg=new StringBuilder();
			errmsg.append("Webonの結果が未取得です");
			throw new Exception(errmsg.toString());
		}
		
		//結果取得
		Node editData = webonBase.getEditData();
		//データの最上位ノードを取得(もうちょっと精査要)
		Node root=null;
		Node root2=editData.getFirstChild(); //通帳部ノード
//		while (true) {
		for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
        	//取得できなかったら終わり
        	if (root2==null){break;}
	    	if (root2.getNodeType()==Node.ELEMENT_NODE) {
	    		//要素名の解析
	    		if (root2.getNodeName().equals(WOKEY_TSUCYO)) {
	    			root=root2.getFirstChild();	//総合情報照会ノード
//	    			while (true) {
    				for (int roopCount2=0;roopCount2<FixedValue.SYS_WBNUMLIMIT;roopCount2++){
	    	        	//取得できなかったら終わり
	    	        	if (root==null){break;}
	    	        	if (root.getNodeType()==Node.ELEMENT_NODE) {
	    		    		if (root.getNodeName().equals(WOKEY_SOGOJOHO)) {
	    		    			break; 
	    		    		}
	    	        	}
	    	        	//次の子ノードを取得
	    	        	root=root.getNextSibling();
	    			}
	    			break;
	            }
	    	}
        	//次の子ノードを取得
	    	root2 = root2.getNextSibling();
		}
		
		//全体の走査
        Node child = root.getFirstChild();	//顧客情報ノード（先頭は店舗番号のはず）

//		while (true) {
		for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
        	//取得できなかったら終わり
        	if (child==null){break;}
	    	if (child.getNodeType()==Node.ELEMENT_NODE) {
	    		//要素名の解析
	    		if(child.getNodeName().equals("店舗番号")){
	    			//必須チェック
	    			if(!getChildText(child).equals("")){
	    				set店舗番号(getChildText(child));
	    			}else{
	    				WebonException e = createWoException("Webon取得結果解析エラー　店舗番号："+child.getNodeValue(), ERRLEVEL_ERROR, ERRSPOT_WOANALYZE);
	    				//エラー項目のセット
	    				Map<String, String>map = new HashMap<String, String>();
	    				map.put("店舗番号", "");
	    				etc.add(map);
	    				e.setEtc(etc);
	    				//エラー処理は上位に任せる
	    				throw e;
	    			}
		    	}else if(child.getNodeName().equals("顧客番号")){
	    			//必須チェック
	    			if(!getChildText(child).equals("")){
	    				set顧客番号(getChildText(child));
	    			}else{
	    				WebonException e = createWoException("Webon取得結果解析エラー　顧客番号："+child.getNodeValue(), ERRLEVEL_ERROR, ERRSPOT_WOANALYZE);
	    				//エラー項目のセット
	    				Map<String, String>map = new HashMap<String, String>();
	    				map.put("顧客番号", "");
	    				etc.add(map);
	    				e.setEtc(etc);
	    				//エラー処理は上位に任せる
	    				throw e;
	    			}
	    		}else if(child.getNodeName().equals("カナ氏名")){
	    			setカナ氏名(getChildText(child));
	    		}else if(child.getNodeName().equals("漢字氏名")){
	    			set漢字氏名(getChildText(child));
	    		}else if(child.getNodeName().equals("活口座")){
	    			set活口座(getChildText(child));
	    		}else if(child.getNodeName().equals("抹消予定")){
	    			set抹消予定(getChildText(child));
	    		}else if(child.getNodeName().equals("人格")){
	    			set人格(getChildText(child));
	    		}else if(child.getNodeName().equals("元号生設立年月日")){
	    			set元号生設立年月日(getChildText(child));
	    		}else if(child.getNodeName().equals("預金保険カナ氏名")){
	    			set預金保険カナ氏名(getChildText(child));
	    		}else if(child.getNodeName().equals("統一カナ氏名")){
	    			set統一カナ氏名(getChildText(child));
	    		}else if(child.getNodeName().equals("業種コード")){
	    			set業種コード(getChildText(child));
	    		}else if(child.getNodeName().equals("統一顧客番号")){
	    			set統一顧客番号(getChildText(child));
	    		}else if(child.getNodeName().equals("統一顧客人格")){
	    			set統一顧客人格(getChildText(child));
	    		}else if(child.getNodeName().equals("統一顧客元号生設立年月日")){
	    			set統一顧客元号生設立年月日(getChildText(child));
	    		}else if(child.getNodeName().equals("統一顧客電話番号")){
	    			set統一顧客電話番号(getChildText(child));
	    		}else if(child.getNodeName().equals("統一顧客名寄件数")){
	    			set統一顧客関連情報名寄件数(getChildText(child));
	    		}else if(child.getNodeName().equals("統一顧客データ整備済コード")){
	    			set統一顧客データ整備済コード(getChildText(child));
	    		}else if(child.getNodeName().equals("国籍情報")){
	    			set国籍情報(getChildText(child));
	    		}else if(child.getNodeName().equals("担当者")){
	    			set担当者(getChildText(child));
	    		}else if(child.getNodeName().equals("店舗担当地区")){
	    			set店舗担当地区(getChildText(child));
	    		}else if(child.getNodeName().equals("移管事由")){
	    			set移管事由(getChildText(child));
	    		}else if(child.getNodeName().equals("移受管店番顧客番号")){
	    			set移受管店番顧客番号(getChildText(child));
	    		}else if(child.getNodeName().equals("移受管日")){
	    			set移受管日(getChildText(child));
	    		}else if(child.getNodeName().equals("代表者資格")){
	    			set代表者資格(getChildText(child));
	    		}else if(child.getNodeName().equals("勤務先電話番号")){
	    			set勤務先電話番号(getChildText(child));
	    		}else if(child.getNodeName().equals("付属名称")){
	    			set付属名称(getChildText(child));
	    		}else if(child.getNodeName().equals("電話番号")){
	    			set電話番号(getChildText(child));
	    		}else if(child.getNodeName().equals("携帯電話番号")){
	    			set携帯電話番号(getChildText(child));
	    		}else if(child.getNodeName().equals("第二電話番号")){
	    			set第二電話番号(getChildText(child));
	    		}else if(child.getNodeName().equals("住所印字")){
	    			set住所印字(getChildText(child));
	    		}else if(child.getNodeName().equals("訪問先")){
	    			set訪問先(getChildText(child));
	    		}else if(child.getNodeName().equals("住所コード")){
	    			set住所コード(getChildText(child));
	    		}else if(child.getNodeName().equals("第二住所コード")){
	    			set第二住所コード(getChildText(child));
	    		}else if(child.getNodeName().equals("郵便番号")){
	    			set郵便番号(getChildText(child));
	    		}else if(child.getNodeName().equals("住所一行目")){
	    			set住所一行目(getChildText(child));
	    		}else if(child.getNodeName().equals("住所二行目")){
	    			set住所二行目(getChildText(child));
	    		}else if(child.getNodeName().equals("第二住所郵便番号")){
	    			set第二住所郵便番号(getChildText(child));
	    		}else if(child.getNodeName().equals("第二住所一行目")){
	    			set第二住所一行目(getChildText(child));
	    		}else if(child.getNodeName().equals("第二住所二行目")){
	    			set第二住所二行目(getChildText(child));
	    		}else if(child.getNodeName().equals("カナ補助住所")){
	    			setカナ補助住所(getChildText(child));
	    		}else if(child.getNodeName().equals("家族取引数")){
	    			set家族取引数(getChildText(child));
	    		}else if(child.getNodeName().equals("関連顧客数")){
	    			set関連顧客数(getChildText(child));
	    		}else if(child.getNodeName().equals("出資基本")){
	    			set出資基本(getChildText(child));
	    		}else if(child.getNodeName().equals("会員")){
	    			set会員(getChildText(child));
	    		}else if(child.getNodeName().equals("活口座数当座")){
	    			set活口座数当座(getChildText(child));
	    		}else if(child.getNodeName().equals("活口座数普通")){
	    			set活口座数普通(getChildText(child));
	    		}else if(child.getNodeName().equals("活口座数貯蓄")){
	    			set活口座数貯蓄(getChildText(child));
	    		}else if(child.getNodeName().equals("活口座数定期")){
	    			set活口座数定期(getChildText(child));
	    		}else if(child.getNodeName().equals("活口座数通知")){
	    			set活口座数通知(getChildText(child));
	    		}else if(child.getNodeName().equals("活口座数定積")){
	    			set活口座数定積(getChildText(child));
	    		}else if(child.getNodeName().equals("活口座数積定")){
	    			set活口座数積定(getChildText(child));
	    		}else if(child.getNodeName().equals("活口座数別段")){
	    			set活口座数別段(getChildText(child));
	    		}else if(child.getNodeName().equals("活口座数債券")){
	    			set活口座数債券(getChildText(child));
	    		}else if(child.getNodeName().equals("活口座数納税")){
	    			set活口座数納税(getChildText(child));
	    		}else if(child.getNodeName().equals("活口座数職員")){
	    			set活口座数職員(getChildText(child));
	    		}else if(child.getNodeName().equals("時効解約口座数")){
	    			set時効解約口座数(getChildText(child));
	    		}else if(child.getNodeName().equals("SW件数")){
	    			setSW件数(getChildText(child));
	    		}else if(child.getNodeName().equals("総合口座")){
	    			set総合口座(getChildText(child));
	    		}else if(child.getNodeName().equals("投信契約有")){
	    			set投信契約有(getChildText(child));
	    		}else if(child.getNodeName().equals("特定口座契約有")){
	    			set特定口座契約有(getChildText(child));
	    		}else if(child.getNodeName().equals("預金マル優申告額千円")){
	    			set預金マル優申告額千円(getChildText(child));
	    		}else if(child.getNodeName().equals("債券マル優申告額千円")){
	    			set債券マル優申告額千円(getChildText(child));
	    		}else if(child.getNodeName().equals("マル財申告額千円")){
	    			setマル財申告額千円(getChildText(child));
	    		}else if(child.getNodeName().equals("マル特申告額千円")){
	    			setマル特申告額千円(getChildText(child));
	    		}else if(child.getNodeName().equals("投信マル優申告額千円")){
	    			set投信マル優申告額千円(getChildText(child));
	    		}else if(child.getNodeName().equals("融資基本")){
	    			set融資基本(getChildText(child));
	    		}else if(child.getNodeName().equals("融資抹消")){
	    			set融資抹消(getChildText(child));
	    		}else if(child.getNodeName().equals("割手")){
	    			set割手(getChildText(child));
	    		}else if(child.getNodeName().equals("手貸")){
	    			set手貸(getChildText(child));
	    		}else if(child.getNodeName().equals("証貸")){
	    			set証貸(getChildText(child));
	    		}else if(child.getNodeName().equals("代理貸")){
	    			set代理貸(getChildText(child));
	    		}else if(child.getNodeName().equals("債務保証")){
	    			set債務保証(getChildText(child));
	    		}else if(child.getNodeName().equals("住公契約")){
	    			set住公契約(getChildText(child));
	    		}else if(child.getNodeName().equals("当貸契約")){
	    			set当貸契約(getChildText(child));
	    		}else if(child.getNodeName().equals("個人CL")){
	    			set個人CL(getChildText(child));
	    		}else if(child.getNodeName().equals("事業者CL")){
	    			set事業者CL(getChildText(child));
	    		}else if(child.getNodeName().equals("IP電話番号")){
	    			setIP電話番号(getChildText(child));
	    		}else if(child.getNodeName().equals("第二IP電話番号")){
	    			set第二IP電話番号(getChildText(child));
	    		}else if(child.getNodeName().equals("電債決済口座数")){
	    			set電債決済口座数(getChildText(child));
	    		}else if(child.getNodeName().equals("定例発行契約自動発行")){
	    			set定例発行契約自動発行(getChildText(child));
	    		}else if(child.getNodeName().equals("振込登録件数")){
	    			set振込登録件数(getChildText(child));
	    		}else if(child.getNodeName().equals("為替自動振込件数")){
	    			set為替自動振込件数(getChildText(child));
	    		}else if(child.getNodeName().equals("貸金庫")){
	    			set貸金庫(getChildText(child));
	    		}else if(child.getNodeName().equals("夜間金庫")){
	    			set夜間金庫(getChildText(child));
	    		}else if(child.getNodeName().equals("諸届け")){
	    			set諸届け(getChildText(child));
	    		}else if(child.getNodeName().equals("外為")){
	    			set外為(getChildText(child));
	    		}else if(child.getNodeName().equals("共有名義")){
	    			set共有名義(getChildText(child));
	    		}else if(child.getNodeName().equals("金庫任意一")){
	    			set金庫任意一(getChildText(child));
	    		}else if(child.getNodeName().equals("金庫任意二")){
	    			set金庫任意二(getChildText(child));
	    		}else if(child.getNodeName().equals("金庫任意三")){
	    			set金庫任意三(getChildText(child));
	    		}else if(child.getNodeName().equals("給振件数")){
	    			set給振件数(getChildText(child));
	    		}else if(child.getNodeName().equals("給与振込")){
	    			set給与振込(getChildText(child));
	    		}else if(child.getNodeName().equals("給与最新振込日")){
	    			set給与最新振込日(getChildText(child));
	    		}else if(child.getNodeName().equals("年金件数")){
	    			set年金件数(getChildText(child));
	    		}else if(child.getNodeName().equals("年金振込")){
	    			set年金振込(getChildText(child));
	    		}else if(child.getNodeName().equals("年金最新振込日")){
	    			set年金最新振込日(getChildText(child));
	    		}else if(child.getNodeName().equals("FB契約")){
	    			setFB契約(getChildText(child));
	    		}else if(child.getNodeName().equals("WEBFB契約")){
	    			setWEBFB契約(getChildText(child));
	    		}else if(child.getNodeName().equals("HB契約数")){
	    			setHB契約数(getChildText(child));
	    		}else if(child.getNodeName().equals("ANS代表")){
	    			setANS代表(getChildText(child));
	    		}else if(child.getNodeName().equals("ANS照会数")){
	    			setANS照会数(getChildText(child));
	    		}else if(child.getNodeName().equals("ANS通知数")){
	    			setANS通知数(getChildText(child));
	    		}else if(child.getNodeName().equals("コール契約")){
	    			setコール契約(getChildText(child));
	    		}else if(child.getNodeName().equals("IB代表店番")){
	    			setIB代表店番(getChildText(child));
	    		}else if(child.getNodeName().equals("IB代表科目口座番号")){
	    			setIB代表科目口座番号(getChildText(child));
	    		}else if(child.getNodeName().equals("AA契約口座数")){
	    			setAA契約口座数(getChildText(child));
	    		}else if(child.getNodeName().equals("サークル一")){
	    			setサークル一(getChildText(child));
	    		}else if(child.getNodeName().equals("サークル二")){
	    			setサークル二(getChildText(child));
	    		}else if(child.getNodeName().equals("サークル三")){
	    			setサークル三(getChildText(child));
	    		}else if(child.getNodeName().equals("サークル四")){
	    			setサークル四(getChildText(child));
	    		}else if(child.getNodeName().equals("サークル五")){
	    			setサークル五(getChildText(child));
	    		}else if(child.getNodeName().equals("サークル六")){
	    			setサークル六(getChildText(child));
	    		}else if(child.getNodeName().equals("サークル七")){
	    			setサークル七(getChildText(child));
	    		}else if(child.getNodeName().equals("サークル八")){
	    			setサークル八(getChildText(child));
	    		}else if(child.getNodeName().equals("サークル九")){
	    			setサークル九(getChildText(child));
	    		}else if(child.getNodeName().equals("サークル十")){
	    			setサークル十(getChildText(child));
	    		}else if(child.getNodeName().equals("サークル十一")){
	    			setサークル十一(getChildText(child));
	    		}else if(child.getNodeName().equals("サークル十二")){
	    			setサークル十二(getChildText(child));
	    		}else if(child.getNodeName().equals("サークル十三")){
	    			setサークル十三(getChildText(child));
	    		}else if(child.getNodeName().equals("サークル十四")){
	    			setサークル十四(getChildText(child));
	    		}else if(child.getNodeName().equals("サークル十五")){
	    			setサークル十五(getChildText(child));
	    		}
	    	}
        	//次の子ノードを取得
        	child = child.getNextSibling();
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
	 * @throws Exception 
	 */
	private void checkWebon() throws Exception{
		
		set店舗番号(ConvertUtil.chkConvertNumAdd0(get店舗番号(), 3));
		set顧客番号(ConvertUtil.chkConvertNumAdd0(get顧客番号(), 7));
		setカナ氏名(ConvertUtil.chkNull(getカナ氏名()));
		set漢字氏名(ConvertUtil.chkNull(get漢字氏名()));
		set活口座(ConvertUtil.chkConvertFlag(get活口座()));
		set抹消予定(ConvertUtil.chkConvertFlag(get抹消予定()));
		set人格(ConvertUtil.chkConvertNumAdd0(get人格(), 2));
		//【和暦処理】
		set元号生設立年月日(ConvertUtil.chkConvertGengoDateAdd0(get元号生設立年月日()));
		set預金保険カナ氏名(ConvertUtil.chkNull(get預金保険カナ氏名()));
		set統一カナ氏名(ConvertUtil.chkNull(get統一カナ氏名()));
		set業種コード(ConvertUtil.chkConvertNumAdd0(get業種コード(), 6));
		set統一顧客番号(ConvertUtil.chkConvertNumAdd0(get統一顧客番号(), 9));
		set統一顧客人格(ConvertUtil.chkConvertNumAdd0(get統一顧客人格(), 2));
		//【和暦処理】
		set統一顧客元号生設立年月日(ConvertUtil.chkConvertGengoDateAdd0(get統一顧客元号生設立年月日()));
		set統一顧客電話番号(ConvertUtil.chkConvertTel(get統一顧客電話番号()));
		set統一顧客関連情報名寄件数(ConvertUtil.chkConvertNumAdd0(get統一顧客関連情報名寄件数(),1));
		set統一顧客データ整備済コード(ConvertUtil.chkNull(get統一顧客データ整備済コード()));
		set国籍情報(ConvertUtil.chkNull(get国籍情報()));
		set担当者(ConvertUtil.chkConvertNumAdd0(get担当者(), 2));
		set店舗担当地区(ConvertUtil.chkConvertNumAdd0(get店舗担当地区(), 4));
		set移管事由(ConvertUtil.chkNull(get移管事由()));
		set移受管店番顧客番号(ConvertUtil.chkDelHyphenAdd0(get移受管店番顧客番号(), 10));
		//【和暦処理】
		set移受管日(ConvertUtil.chkConvertDateAdd0(get移受管日()));
		//set代表者資格(changeRecepCode(get代表者資格()));	//暫定的にコードのみ取得中、名称を合わせて取得に変更要
		set代表者資格(ConvertUtil.chkNull(get代表者資格()));
		set勤務先電話番号(ConvertUtil.chkConvertTel(get勤務先電話番号()));
		set付属名称(ConvertUtil.chkNull(get付属名称()));
		set電話番号(ConvertUtil.chkConvertTel(get電話番号()));
		set携帯電話番号(ConvertUtil.chkConvertTel(get携帯電話番号()));
		set第二電話番号(ConvertUtil.chkConvertTel(get第二電話番号()));
		set住所印字(ConvertUtil.chkConvertNumAdd0(get住所印字(),1));
		set訪問先(ConvertUtil.chkNull(get訪問先()));
		set住所コード(ConvertUtil.chkDelHyphen(get住所コード()));
		set第二住所コード(ConvertUtil.chkDelHyphen(get第二住所コード()));
		set郵便番号(ConvertUtil.chkDelHyphen(get郵便番号()));
		set住所一行目(ConvertUtil.chkNull(get住所一行目()));
		set住所二行目(ConvertUtil.chkNull(get住所二行目()));
		set第二住所郵便番号(ConvertUtil.chkDelHyphen(get第二住所郵便番号()));
		set第二住所一行目(ConvertUtil.chkNull(get第二住所一行目()));
		set第二住所二行目(ConvertUtil.chkNull(get第二住所二行目()));
		setカナ補助住所(ConvertUtil.chkNull(getカナ補助住所()));
		set家族取引数(ConvertUtil.chkConvertNumAdd0(get家族取引数(),1));
		set関連顧客数(ConvertUtil.chkConvertNumAdd0(get関連顧客数(),1));
		set出資基本(ConvertUtil.chkConvertFlag(get出資基本()));
		set会員(ConvertUtil.chkConvertFlag(get会員()));
		set活口座数当座(ConvertUtil.chkConvertNumAdd0(get活口座数当座(), 1));
		set活口座数普通(ConvertUtil.chkConvertNumAdd0(get活口座数普通(), 1));
		set活口座数貯蓄(ConvertUtil.chkConvertNumAdd0(get活口座数貯蓄(), 1));
		set活口座数定期(ConvertUtil.chkConvertNumAdd0(get活口座数定期(), 1));
		set活口座数通知(ConvertUtil.chkConvertNumAdd0(get活口座数通知(), 1));
		set活口座数定積(ConvertUtil.chkConvertNumAdd0(get活口座数定積(), 1));
		set活口座数積定(ConvertUtil.chkConvertNumAdd0(get活口座数積定(), 1));
		set活口座数別段(ConvertUtil.chkConvertNumAdd0(get活口座数別段(), 1));
		set活口座数債券(ConvertUtil.chkConvertNumAdd0(get活口座数債券(), 1));
		set活口座数納税(ConvertUtil.chkConvertNumAdd0(get活口座数納税(), 1));
		set活口座数職員(ConvertUtil.chkConvertNumAdd0(get活口座数職員(), 1));
		set時効解約口座数(ConvertUtil.chkConvertNumAdd0(get時効解約口座数(), 1));
		setSW件数(ConvertUtil.chkConvertNumAdd0(getSW件数(), 1));
		set総合口座(ConvertUtil.chkConvertFlag(get総合口座()));
		set投信契約有(ConvertUtil.chkConvertFlag(get投信契約有()));
		set特定口座契約有(ConvertUtil.chkConvertFlag(get特定口座契約有()));
		set預金マル優申告額千円(ConvertUtil.chkDelCommaAdd0(get預金マル優申告額千円(), 1));
		set債券マル優申告額千円(ConvertUtil.chkDelCommaAdd0(get債券マル優申告額千円(), 1));
		setマル財申告額千円(ConvertUtil.chkDelCommaAdd0(getマル財申告額千円(), 1));
		setマル特申告額千円(ConvertUtil.chkDelCommaAdd0(getマル特申告額千円(), 1));
		set投信マル優申告額千円(ConvertUtil.chkDelCommaAdd0(get投信マル優申告額千円(), 1));
		set融資基本(ConvertUtil.chkConvertFlag(get融資基本()));
		set融資抹消(ConvertUtil.chkConvertFlag(get融資抹消()));
		set割手(ConvertUtil.chkConvertFlag(get割手()));
		set手貸(ConvertUtil.chkConvertFlag(get手貸()));
		set証貸(ConvertUtil.chkConvertFlag(get証貸()));
		set代理貸(ConvertUtil.chkConvertFlag(get代理貸()));
		set債務保証(ConvertUtil.chkConvertFlag(get債務保証()));
		set住公契約(ConvertUtil.chkConvertFlag(get住公契約()));
		set当貸契約(ConvertUtil.chkConvertFlag(get当貸契約()));
		set個人CL(ConvertUtil.chkConvertFlag(get個人CL()));
		set事業者CL(ConvertUtil.chkConvertFlag(get事業者CL()));
		setIP電話番号(ConvertUtil.chkConvertTel(getIP電話番号()));
		set第二IP電話番号(ConvertUtil.chkConvertTel(get第二IP電話番号()));
		set電債決済口座数(ConvertUtil.chkConvertNumAdd0(get電債決済口座数(), 1));
		set定例発行契約自動発行(ConvertUtil.chkNull(get定例発行契約自動発行()));
		set振込登録件数(ConvertUtil.chkConvertNumAdd0(get振込登録件数(), 1));
		set為替自動振込件数(ConvertUtil.chkConvertNumAdd0(get為替自動振込件数(), 1));
		set貸金庫(ConvertUtil.chkConvertFlag(get貸金庫()));
		set夜間金庫(ConvertUtil.chkConvertFlag(get夜間金庫()));
		set諸届け(ConvertUtil.chkConvertFlag(get諸届け()));
		set外為(ConvertUtil.chkConvertFlag(get外為()));
		set共有名義(ConvertUtil.chkConvertFlag(get共有名義()));
		set金庫任意一(ConvertUtil.chkConvertNumAdd0(get金庫任意一(), 5));
		set金庫任意二(ConvertUtil.chkConvertNumAdd0(get金庫任意二(), 5));
		set金庫任意三(ConvertUtil.chkConvertNumAdd0(get金庫任意三(), 5));
		set給振件数(ConvertUtil.chkConvertNumAdd0(get給振件数(), 1));
		set給与振込(ConvertUtil.chkConvertFlag(get給与振込()));
		//【和暦処理】
		set給与最新振込日(ConvertUtil.chkConvertDateAdd0(get給与最新振込日()));
		set年金件数(ConvertUtil.chkConvertNumAdd0(get年金件数(), 1));
		set年金振込(ConvertUtil.chkConvertFlag(get年金振込()));
		//【和暦処理】
		set年金最新振込日(ConvertUtil.chkConvertDateAdd0(get年金最新振込日()));
		setFB契約(ConvertUtil.chkConvertFlag(getFB契約()));
		setWEBFB契約(ConvertUtil.chkConvertFlag(getWEBFB契約()));
		setHB契約数(ConvertUtil.chkConvertNumAdd0(getHB契約数(), 2));
		setANS代表(ConvertUtil.chkConvertFlag(getANS代表()));
		setANS照会数(ConvertUtil.chkConvertNumAdd0(getANS照会数(), 1));
		setANS通知数(ConvertUtil.chkConvertNumAdd0(getANS通知数(), 1));
		setコール契約(ConvertUtil.chkConvertFlag(getコール契約()));
		setIB代表店番(ConvertUtil.chkConvertNumAdd0(getIB代表店番(), 3));
		setIB代表科目口座番号(ConvertUtil.chkDelHyphenAdd0(getIB代表科目口座番号(), 9));
		setAA契約口座数(ConvertUtil.chkConvertNumAdd0(getAA契約口座数(), 1));
		setサークル一(ConvertUtil.chkConvertNumAdd0(getサークル一(), 2));
		setサークル二(ConvertUtil.chkConvertNumAdd0(getサークル二(), 2));
		setサークル三(ConvertUtil.chkConvertNumAdd0(getサークル三(), 2));
		setサークル四(ConvertUtil.chkConvertNumAdd0(getサークル四(), 2));
		setサークル五(ConvertUtil.chkConvertNumAdd0(getサークル五(), 2));
		setサークル六(ConvertUtil.chkConvertNumAdd0(getサークル六(), 2));
		setサークル七(ConvertUtil.chkConvertNumAdd0(getサークル七(), 2));
		setサークル八(ConvertUtil.chkConvertNumAdd0(getサークル八(), 2));
		setサークル九(ConvertUtil.chkConvertNumAdd0(getサークル九(), 2));
		setサークル十(ConvertUtil.chkConvertNumAdd0(getサークル十(), 2));
		setサークル十一(ConvertUtil.chkConvertNumAdd0(getサークル十一(), 2));
		setサークル十二(ConvertUtil.chkConvertNumAdd0(getサークル十二(), 2));
		setサークル十三(ConvertUtil.chkConvertNumAdd0(getサークル十三(), 2));
		setサークル十四(ConvertUtil.chkConvertNumAdd0(getサークル十四(), 2));
		setサークル十五(ConvertUtil.chkConvertNumAdd0(getサークル十五(), 2));
		
	}
	
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
	//以下UTILITY
	//以下、ユーティリティ的メソッド
	/**
	 * 代表者資格変換要メソッド（暫定版）修正後削除
	 * @throws Exception 
	 */
	public String changeRecepCode(String code) throws Exception{
		try{
			FWLog.debug("代表者資格"+code+" 文字列の長さ："+code.length());
			//空白かNULLの場合[00]を返す
			if(code==null || code.isEmpty() || code.length()<3){
				return "00";
			}else{
				//それ以外は、先頭2桁を返す
				return code.substring(0,2);
			}
		}catch(Exception e){
			FWLog.error("代表者資格のコード削除時エラー⇒⇒"+e);
			throw e;
		}
	}
}
