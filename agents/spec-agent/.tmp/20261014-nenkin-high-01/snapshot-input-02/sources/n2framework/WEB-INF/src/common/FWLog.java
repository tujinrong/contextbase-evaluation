package common;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;

/**
 * フレームワークログ出力クラス
 *
 * @author JSC kengo murayama
 *
 * @date	H22.9.3		青木・浅見		センター集約対応なし
 */
public class FWLog {

	/** アプリケーション単位の Log オブジェクト */
	private static Log logger;

	/** エラー専用の共通 Log オブジェクト */
	private static Log errorLogger;

	/** クラス名とメッセージの区切り */
	private static final String DEVIDE_MSG = " : ";

	/**
	 * Logger初期化メソッド<BR>
	 * ControlServlet起動時に呼び出されて、アプリケーションごとのLoggerを初期化する。
	 * 
	 * @param loggerName
	 */
	static void initLogger(String loggerName) {
		logger = LogFactory.getLog(loggerName);
		errorLogger = LogFactory.getLog("error");
	}

	/**
	 * Loggerの設定が、DEBUGモードか確認する。
	 * 
	 * @return
	 */
	public static boolean isDebug(){
		return logger.isDebugEnabled();
	}

	/**
	 * Debugログ出力メソッド（メッセージのみ）
	 * 
	 * @param msg
	 */
	public static void debug(String msg){
		logger.debug(msg);
	}

	/**
	 * Debugログ出力メソッド（クラス名、メッセージ）
	 * 
	 * @param cls
	 * @param msg
	 */
	public static void debug(Class cls, String msg){
		logger.debug(cls.getName() + DEVIDE_MSG + msg);
	}

	/**
	 * Infoログ出力メソッド（クラス名、メッセージ）
	 * 
	 * @param cls
	 * @param msg
	 */
	public static void info(Class cls, String msg){
		logger.info(cls.getName() + DEVIDE_MSG + msg);
	}

	/**
	 * Warnログ出力メソッド（クラス名、メッセージ）
	 * 
	 * @param cls
	 * @param msg
	 */
	public static void warn(Class cls, String msg){
		logger.warn(cls.getName() + DEVIDE_MSG + msg);
	}

	/**
	 * Errorログ出力メソッド（メッセージのみ）
	 * 
	 * @param msg
	 */
	public static void error(String msg){
		errorLogger.error(msg);
		logger.error(msg);
	}

	/**
	 * Errorログ出力メソッド（クラス名、メッセージ）
	 * 
	 * @param cls
	 * @param msg
	 */
	public static void error(Class cls, String msg){
		errorLogger.error(cls.getName() + DEVIDE_MSG + msg);
		logger.error(cls.getName() + DEVIDE_MSG + msg);
	}

	/**
	 * Errorログ出力メソッド（StackTrace）
	 * 
	 * @param e
	 */
	public static void error(Throwable e){
		errorLogger.error(e.toString(), e);
		logger.error(e.toString(), e);
	}
}
