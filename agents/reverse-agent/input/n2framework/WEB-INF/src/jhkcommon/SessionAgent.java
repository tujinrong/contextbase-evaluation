package jhkcommon;

/*
 * SessionAgent.java
 * 
 * 
 * @date	H22.8.19	青木・浅見		センター集約対応
 *  
 */

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.SocketException;
import java.util.List;

import javax.servlet.ServletOutputStream;
import javax.servlet.http.HttpServletRequest;

import com.canon.iw.fm.common.exception.FMIllegalStatusException;
import com.canon.iw.fm.common.exception.FMPrintException;
import com.canon.iw.fm.common.exception.FMPropertyException;
import com.canon.iw.fm.common.exception.FMSystemException;
import com.canon.iw.fm.common.message.FMResponse;
import com.canon.iw.fm.server.FMComposerAgent;
import com.canon.iw.fm.server.FMJob;

/**
 * SessionAgent
 *
 * セッション単位生成されるエージェント
 *
 * 修正履歴：2005/10/21 NEC Soft, Ltd.
 *   「FormCraft Pro. for Web」から「Form Manager V6.1」へのバージョンアップ
 *    にともない大幅変更。(NECIKO)
 *     
 *     FcwJobControlクラスは廃止。FMComposerAgentクラスへ統合された。
 *     FMComposerAgentクラスはfinalクラス（継承不可）のため、本クラスで
 *     継承する方式をやめ、本クラス内でFMComposerAgentクラスのインスタンス
 *     を作成して使用する方式へ変更。
 *     その他、各種クラス名の変更、各種メソッドの仕様変更、Fcp3Dataクラスの
 *     廃止など、Form ManagerのJavaAPIの仕様に合わせ、変更点多数。
 *     
 *
 */
public class SessionAgent {
	
	private FMComposerAgent	_agent = null;	// エージェント
	private FMJob _job = null;				// ジョブ
	private SessionTimer _timer = null;		// タイムアウト用セッションタイマー
	private ServletOutputStream _outputStream = null;

	private boolean _callback = false;		// コールバックかどうか
	private String _requestHost = null;		// サーバを呼び出したときのURLホスト名（webap01:8181）
	private String _requestHostIP = null;	// サーバを呼び出したときのURLホスト名（webap01）
	private String _requestUri = null;		// URI （/webap/cif/servlet/xxxxx）

	private static final int AGENT_ERROR_TIMEOUT = 4001010;
	private static final int AGENT_ERROR = 4999999;
	private static final String RETRIEVE = "fcw-retrieve";


	/**
	 * コンストラクタ.
	 */
	public SessionAgent() throws IOException, FMPropertyException, FMSystemException {
		this(null, null, null);
	}

	/**
	 * コンストラクタ.
	 */
	public SessionAgent(String uniqueId, String managerUrlKey, File logFile)
	       throws IOException, FMPropertyException, FMSystemException {
		// FormManagerインストールディレクトリの指定
		FMComposerAgent.setRootDirectory("C:\\iWFM");	
		// エージェントの作成
	  	_agent = new FMComposerAgent(uniqueId, managerUrlKey, logFile);
		// ジョブの作成
		_job= _agent.newJob();
	}


	/**
	 * セッション終了時の処理を行います。
	 */
	public void invalidate() {
		clear();
		try {
			_agent.removeJob(getJob());
		} catch (FMSystemException e) {
		}
	}

	/**
	 * リクエストオブジェクトに設定されている属性に従ってオーバレイを実行します。
	 */
	public FMResponse overlay() throws FMPropertyException, FMPrintException,
	                                   FMIllegalStatusException {
		FMResponse response = null;

		try {
			int jobstatus = 0;
			int resstatus = 0;
			FMJob job = getJob();
			job.overlay();					//オーバレイの同期実行
			jobstatus = job.getStatus();	//ジョブステータスの取得(処理が終わっていれば0)
			response = job.getResponse();	//リクエストタイムアウト時はnullが返る
			if (response != null) {
				//レスポンスオブジェクトから結果情報を取得
				resstatus = ((Integer)response.get("fm-status")).intValue();
			}

			if (jobstatus != 0 || response == null || resstatus != 0) {
				// 何らかの理由で同期オーバレイが失敗した。
				// おそらくタイムアウト。
				if (job.isTimeout() == true) {
					// ジョブを置き換えないと次のリクエストと衝突してしまう。
					// セッションを終了するか、ジョブを切り替える。
					clear();
					_agent.removeJob(job);
					_job = _agent.newJob();
					throw new FMPrintException("synchronous overlay timeout",
				                               AGENT_ERROR_TIMEOUT);
				} else {
					// タイムアウト以外の理由でジョブが異常終了
					String msg = null;
					if (response != null) {
						msg = (String)response.get("fm-message");
					}
					if (msg == null) {
						msg = "エラーコード:" + jobstatus;
					}
					throw new FMPrintException("message: " + msg, AGENT_ERROR);
				}
			} else {
				// オーバレイは成功した
			}
		} catch (FMPropertyException e) {
			throw e;
		} catch (FMPrintException e) {
			throw e;
		} catch (FMIllegalStatusException e) {
			throw e;
		}

		return response;
	}

	/**
	 * overlay メソッドで最後に生成された結果オブジェクトを返します。.
	 * なければ null を返します。
	 * 本メソッドは、Internet Explorerのような特異な動作をするクライアントへの対処や、
	 * そもそも切断しやすいHTTPプロトコルで再送リクエストが発行されるようなケースに
	 * 対処するためのものです。
	 */
	public FMResponse getLastResponse() {
		return getJob().getResponse();
	}

	/**
	 * 読み込まれたパラメータをもとに、オーバレイ実行可能かどうかを返します。.
	 */
	public boolean canOverlay() {
		return getJob().canOverlay();
	}

	/**
	 * canOverlay() メソッド呼出しで false が返されたときに、エラーメッセージを獲得します。.
	 */
	public String getMessage() {
		return getJob().getMessage();
	}

	/**
	 * 保持していた全パラメータをクリアするためのメソッドです。.
	 */
	public synchronized void clear() {
		try {
			getJob().clear();
		} catch (FMIllegalStatusException e) {
		}
	}


	//--------------------------------------------------------------
	// オーバーレイ属性の設定
	//--------------------------------------------------------------
		
	/**
	 * フォームファイル名(fm-formfilename)の設定
	 *
	 */
	public void setFormFileName(String formFileName) {
		getJob().getRequest().put("fm-formfilename",formFileName);
	}

	/**
	 * フィールドデータ(fm-fielddata)の設定
	 *
	 */
	public void setFieldData(byte[] fieldData) {
		getJob().getRequest().put("fm-fielddata",fieldData);
		
		//-----------デバック用（フィールドデータをサーバ上へファイル出力）
		/*******
		OutputStream out = null;
		try {
		String fname = new String().valueOf(System.currentTimeMillis());
		out = new BufferedOutputStream(new FileOutputStream("C:\\iWFM\\data\\"
			                                                + fname + ".txt"));
		out.write(fieldData);
		out.close();
		} catch (Exception e) {
			e.printStackTrace();
		} finally {
			try {
				if (out!=null) out.close();
			} catch (Exception e) {}
		}
		*******/
		//-------------デバックＥＮＤ
	}

	/**
	 * 出力先(fm-target)の設定
	 *   dest={"client","sever","folder"}
	 */
	public void setDestination(String dest) {
		getJob().getRequest().put("fm-target",dest);
	}

	/**
	 * 出力方式(fm-action)の設定
	 *   act={"view","save","print","printsave"}
	 */
	public void setAction(String act) {
		getJob().getRequest().put("fm-action",act);
	}

	/**
	 * 出力データ形式(fm-outputtype)の設定
	 *   type={"pdf","csm","fcm"}
	 */
	public void setType(String type) {
		getJob().getRequest().put("fm-outputtype",type);
	}

	/**
	 * ドライバ(fm-driver)の設定
	 *  ※fm-target="client",fm-action="view"の場合、この指定は無視されます。
	 *  ※fm-outputtype="pdf"の場合、この指定は無視されます。
	 */
	public void setDriver(String driver) {
		getJob().getRequest().put("fm-driver",driver);
	}

	/**
	 * サーバセーブ用ファイル名(fm-outfile)の設定
	 *  ※fm-target="server",fm-action="save"の場合のみ有効
	 */
	public void setServerSaveFile(File fileName) {
		getJob().getRequest().put("fm-outfile",fileName);
	}

	//--------------------------------------------------------------
	// パラメータ関連
	//--------------------------------------------------------------

	/**
	 * HttpServletRequest からパラメータを読み込みこみます。.
	 */
	public void parseParameters(HttpServletRequest request) {
		String key, value;

		String requestHost = request.getHeader("Host");
		if (requestHost != null) {
			_requestHost = requestHost;
			int pos = requestHost.indexOf(":");
			if (pos >= 0) {
				String requestHostIP = requestHost.substring(0, pos);
				_requestHostIP = requestHostIP;
			}else{
				_requestHostIP = requestHost;
			}
		}

		_requestUri = request.getRequestURI();

		// リクエストパラメータ中に"fcw-retrieve"の文字列が含まれる場合は、
		// IE 問題対策としてプログラムが発行したコールバックと判断します。
		value = request.getParameter(RETRIEVE);
		if (value != null) {
			_callback = true;
		}
		else {
			_callback = false;
		}
	}

	/**
	 * リクエストオブジェクトにオーバレイ属性を設定します。
	 */
	public void setFMParameters(String[][] fixedData, List variableData, int formCount,
	                            String formatFileName) throws IOException {

		InputStream stream = null;
		ServletOutputStream out = null;

		// フォームファイル名の設定
		setFormFileName(formatFileName);
	  	// フィールドデータの設定
	  	byte[] fieldData = makeFieldData(fixedData, variableData, formCount);
		setFieldData(fieldData);
		// 出力先の設定
		setDestination("client");
		// 出力方式の設定
		setAction("view");
		// データ形式の設定
		setType("pdf");

		//ドライバは設定不要
		//setDriver("FCPC");	


	  	/**テスト用（c:\\iWFM\\storeへＰＤＦファイルを出力する）
		setDestination("server");
		setAction("view");
		setType("pdf");
		String fname = new String().valueOf(System.currentTimeMillis());
		File testFile = new File("C:\\iWFM\\store", fname + ".pdf");
		setServerSaveFile(testFile);
		************************************************************/

	}


	/**
	 * フィールドデータの作成
	 */
	public byte[] makeFieldData(String[][] fixedData, List variableData, int formCount) {

		final String SP = ",";		//データ項目区切り子
		final String QT = "\"";		//リテラル記法引用符
		byte[] fielddata = null;

		/*******************************************
		 * 制御セクション
		 *******************************************/
		StringBuffer sb = new StringBuffer();
		sb.append("[Control Section]\r\n");
		sb.append("VERSION=5.0\r\n");

		/*******************************************
		 * 固定セクション
		 *******************************************/
		if (fixedData==null || fixedData[0][0].equals("")) {
			//固定フィールド無し
		} else {
			//固定フィールドデータセット
			sb.append("[Fixed Data Section]\r\n");
			for(int i=0 ; i < fixedData.length ; i++){
				sb.append(fixedData[i][0] + "=" + QT + fixedData[i][1] + QT + "\r\n");
			}
		}

		/*******************************************
		 * 可変セクション
		 *******************************************/
		sb.append("[Body Data Section]\r\n");
		boolean isFirstRow = true;		//可変セクション内の先頭行かどうか
		boolean isFirstCol = true;		//明細行の先頭列かどうか

		if (formCount > 1 ){
			////////////////////////////////////////////////
			// 複数フォームの場合の処理
			////////////////////////////////////////////////
			int pageCount = 0;		//処理済みページ(フォーム)数
			// ページ(フォーム)の数だけ繰り返す
			for (int page = 0; page < variableData.size(); page++) {
				// １ページ分データ取り出し
				List pagedata = (List)variableData.get(page);
				// 行(明細)の数だけ繰り返す
				for (int row = 0; row < pagedata.size(); row++) {
					isFirstCol = true;
					// 先頭行以外はまず改行出力
					if (!isFirstRow) sb.append("\r\n");
					isFirstRow = false;
					// １明細分データ取り出し
					List rowdata = (List)pagedata.get(row);
					// 要素(列データ)の数だけ繰り返す
					for (int col = 0; col < rowdata.size(); col++) {
						// 列データ取り出し
						//  String dt = (String)rowdata.get(col);
						//  要素がBigDecimalだとClassCastExceptionが発生した為、toString()に変更
						//  かつ、データに￥を含む場合の対処追加
						String dt = rowdata.get(col).toString().replaceAll("\\\\","\\\\\\\\");
						// 先頭データ以外はセパレータ付与
						if (!isFirstCol) sb.append(SP);
						// データ出力
						sb.append(QT + dt + QT);
						isFirstCol = false;
					}
				}
				// １ページ分の処理終わったのでページ数カウントアップ
				pageCount++;
				// まだ未処理ページがあれば、フォーム切替えして処理継続
				if (pageCount < formCount) {
					/*******************************************
					 * フォームセクション
					 *******************************************/
					sb.append("\r\n[Form Section]\r\n");
					// フォームの切り替え指定
					sb.append("NEXTPAGE\r\n");
					/*******************************************
					 * 次の固定セクション
					 *******************************************/
					//固定フィールド有無チェック
					if (fixedData==null || fixedData[0][0].equals("")) {
						//固定フィールド無し
					} else {
						//固定フィールドデータセット
						sb.append("[Fixed Data Section]\r\n");
						for(int i=0; i < fixedData.length; i++) {
							sb.append(fixedData[i][0] + "="
							        + QT + fixedData[i][1] + QT + "\r\n");
						}
					}
					/*******************************************
					 * 次の可変セクション開始
					 *******************************************/
					sb.append("[Body Data Section]\r\n");
					isFirstRow = true;
				}
			}
		} else {
			////////////////////////////////////////////////
			// 単数フォームの場合の処理
			////////////////////////////////////////////////
			// 行(明細)の数だけ繰り返す
			for (int row = 0; row < variableData.size(); row++) {
				isFirstCol = true;
				// 先頭行以外はまず改行出力
				if (!isFirstRow) sb.append("\r\n");
				isFirstRow = false;
				// １明細分データ取り出し
				List rowdata = (List)variableData.get(row);
				// 要素(列データ)の数だけ繰り返す
				for (int col = 0; col < rowdata.size(); col++) {
					// 列データ取り出し
					//  String dt = (String)rowdata.get(col);
					//  要素がBigDecimalだとClassCastExceptionが発生した為、toString()に変更
					//  かつ、データに￥を含む場合の対処追加
					String dt = rowdata.get(col).toString().replaceAll("\\\\","\\\\\\\\");
					// 先頭データ以外はセパレータ付与
					if (!isFirstCol) sb.append(SP);
					// データ出力
					sb.append(QT + dt + QT);
					isFirstCol = false;
				}
			}
		}

		// デフォルト文字セットにてバイト配列に変換
		fielddata = sb.toString().getBytes();
		return fielddata;
	}

	//--------------------------------------------------------------
	// レスポンス関連
	//--------------------------------------------------------------

	/**
	 * ServletOutputStream の遅延クローズ
	 * データデータ送出後、即座に close()メソッドを呼び出すとエラーになることがある。.
	 */
	public void resetOutputStream(ServletOutputStream stream) {
		try {
			// 前回ストリームをクローズしていなかった場合はここでクローズする
			if (_outputStream != null) {
				_outputStream.close();
			}
			// 新しいストリームを後でクローズするために覚えておく
			_outputStream = stream;
		} catch (SocketException e) {
			// IE では、ストリームをクローズすると SocketException が発生することがある。
			// 結果を表示するために処理しない。
		} catch (IOException e) {
		}
	}

	//--------------------------------------------------------------
	// タイマー関連
	//--------------------------------------------------------------

	/**
	 * タイマーを始動し、指定時間後にハンドラが呼び出されるようにします。.
	 */
	public void setSessionTimer(long msec, TimerHandler handler, Object userInfo) {
		if (_timer == null) {
			_timer = new SessionTimer(msec, handler);
		} else {
			_timer.cancel();
		}
		_timer.setTime(msec);
		_timer.setHandler(handler);
		_timer.setUserInfo(userInfo);
	}

	/**
	 * タイマーを始動し、指定時間後にハンドラが呼び出されるようにします。.
	 */
	public void startTimer() throws IllegalThreadStateException, SecurityException {
		if (_timer != null) {
			_timer.restart();
		}
	}

	/**
	 * タイマーをストップし、これ以降ハンドラが呼び出されないようにします。.
	 */
	public void stopTimer() {
		if (_timer != null) {
			_timer.cancel();
		}
	}

	//--------------------------------------------------------------
	// getter / setter
	//--------------------------------------------------------------

	public FMJob getJob() {
		return _job;
	}

	public boolean isCallback() {
		return _callback;
	}

	public String getRequestHost() {
		return _requestHost;
	}

	public String getRequestHostIP() {
		return _requestHostIP;
	}

	public String getRequestUri() {
		return _requestUri;
	}

	//--------------------------------------------------------------
	// FMComposerAgentクラスのメソッド実装
	//--------------------------------------------------------------
	public String getUniqueId() throws FMSystemException {
		return _agent.getUniqueId();
	}
}
