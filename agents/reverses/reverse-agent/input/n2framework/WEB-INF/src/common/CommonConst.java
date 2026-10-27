/*
 * 作成日: 2007/05/14
 *
 */
package common;

/**
 * フレームワーク　定数クラス
 *
 * @author JSC kengo murayama
 *
 * @date	H22.9.3		青木・浅見		センター集約対応
 * @date	H27.10		岩渕			ＴＭ一元化対応
 * @date	R8.4.3		Seraku 有村		役職コード変更対応
 */
public class CommonConst {

	/** JDBC JDBC_ORACLE_SP2NM */
	public static final String JDBC_ORACLE_SP2NM = "jdbc/Oracle_SP2NM";

	/** JDBC JDBC_ORACLE_DWH */
	public static final String JDBC_ORACLE_DWH = "jdbc/Oracle_DWH";

	/** JDBC JDBC_SQL_RAROA */
	public static final String JDBC_SQL_RAROA = "jdbc/RAROA_DB";

	/** JDBC JDBC_SQL_SHARE */
	public static final String JDBC_SQL_SHARE = "jdbc/RAROA_SHARE";

	/** セッションに格納するJSPBeanのKey */
	public static final String SS_JSP_BEAN = "ViewBean";

	/** セッションに格納するログイン情報BeanのKey */
	public static final String SS_LOGIN_INFO_BEAN = "LoginBean";

	/** セッションに格納するサブウィンドウJSPBeanのKey */
	public static final String SS_SUB_JSP_BEAN = "SubWindowBean";

	/** セッションに格納するメッセージのKey */
	public static final String ERROR_MSG = "ErrorMsg";

	/** セッションに格納するエラーメッセージリストのKey */
	public static final String ERROR_MSG_LIST = "MESSAGE";

	/** エラーＪＳＰファイル名 */
	public static final String ERROR_JSP = "./JSP/COMMON/Error.jsp";

	/** セッションに格納するログイン情報BeanのKey */
	public static final String SS_OTHER_INFO_BEAN = "OtherUserBean";

	/** ログイン権限　参照用 */
	public static final int AUTH_SANSYO = 1;

	/** ログイン権限　営業店一般 */
	public static final int AUTH_EIGYO_IPPAN = 10;

	/** ログイン権限　営業店役席 */
	public static final int AUTH_EIGYO_YAKUSEKI = 20;

	/** ログイン権限　営業店長 */
	public static final int AUTH_EIGYO_TENCHO = 30;

	/** ログイン権限　本部一般 */
	public static final int AUTH_HONBU_IPPAN = 40;

	/** ログイン権限　本部役席 */
	public static final int AUTH_HONBU_YAKUSEKI = 50;

	/** ログイン権限　本部長 */
	public static final int AUTH_HONBU_BUCHO = 60;

	/** ログイン権限　システムメンテナンス用 */
	public static final int AUTH_SYSTEM = 999;

	/** 役職コード（係長） */
	public static final int YAKUSYOKU_C_KAKARITYO = 411;

	/** 役職コード（課長代理） */
	public static final int YAKUSYOKU_C_KATYODAIRI = 511;

	/** 役職コード（担当課長） */
	public static final int YAKUSYOKU_C_KATYO = 520;

	/** 役職コード（課長（担当次長待遇）） */
	public static final int YAKUSYOKU_C_KATYO_T = 609;

	/** 役職コード（次長代理） */
	public static final int YAKUSYOKU_C_JITYODAIRI = 611;

	/** 役職コード（担当次長） */
	public static final int YAKUSYOKU_C_TANTOJITYO = 621;

	/** 役職コード（所長） */
	public static final int YAKUSYOKU_C_SYOTYO = 631;

	/** 役職コード（次長） */
	public static final int YAKUSYOKU_C_JITYO = 640;

	/** 役職コード（所長（支店長代理待遇）） */
	public static final int YAKUSYOKU_C_SYOTYO_S = 710;

	/** 役職コード（所長（副部長代理待遇）） */
	public static final int YAKUSYOKU_C_SYOTYO_H = 720;

	/** 役職コード（次長（支店長代理待遇）） */
	public static final int YAKUSYOKU_C_JITYO_S = 721;

	/** 役職コード（次長（副部長代理待遇）） */
	public static final int YAKUSYOKU_C_JITYO_H = 722;

	/** 役職コード（支店長代理） */
	public static final int YAKUSYOKU_C_SHITENTYODAIRI = 730;

	/** 役職コード（副部長代理） */
	public static final int YAKUSYOKU_C_HUKUBUTYODAIRI = 750;

	/** 役職コード（担当副部長） */
	public static final int YAKUSYOKU_C_TANTOHUKUBUTYO = 760;

	/** 役職コード（支店長） */
	public static final int YAKUSYOKU_C_SHITENTYO = 770;

	/** 役職コード（副室長） */
	public static final int YAKUSYOKU_C_HUKUSHITUTYO = 780;

	/** 役職コード（副部長） */
	public static final int YAKUSYOKU_C_HUKUBUTYO = 790;

	/** 役職コード（支店長（部長代理待遇）） */
	public static final int YAKUSYOKU_C_SHITENTYO_BD = 800;

	/** 役職コード（支店長（部長待遇）） */
	public static final int YAKUSYOKU_C_SHITENTYO_B = 840;

	/** 役職コード（室長） */
	public static final int YAKUSYOKU_C_SHITSUTYO = 850;

	/** 役職コード（部長） */
	public static final int YAKUSYOKU_C_BUTYO = 860;

	/** 役職コード（執行役員部長） */
	public static final int YAKUSYOKU_C_SHIKOYAKUINBUTYO = 920;

	/** 役職コード（常勤理事部長委嘱） */
	public static final int YAKUSYOKU_C_RIJIBUTYO = 9045;

}