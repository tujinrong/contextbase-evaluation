package jhkcommon;

/**
 *
 * OjiServletPdf
 *
 * @date	H22.9.7		青木			センター集約対応
 *
 */
  
import java.io.ByteArrayOutputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.PrintWriter;
import java.net.SocketException;
import java.util.Vector;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletOutputStream;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import com.canon.iw.fm.common.exception.FMPrintException;
import com.canon.iw.fm.common.exception.FMPropertyException;
import com.canon.iw.fm.common.exception.FMSystemException;
import com.canon.iw.fm.common.message.FMResponse;
import com.canon.iw.fm.common.message.FMResponseOperator;
import com.canon.iw.fm.server.FMJob;

/** CifアプリケーションのテンプレートになるServlet */
public abstract class OjiServletPdf extends OjiServlet implements TimerHandler{
//public class OjiServletPdf extends OjiServlet implements TimerHandler{

	
	
	//Pdf
	private Object _sessionLock = new Object();		// セッションカウント用
	private static long _timeout = 180000;			// セッションタイムアウトの長さ（ミリ秒）
	private static final String AGENTNAME = "FcwAgent";	// セッションへの値設定で使用するキー文字列
	private static final String FAKEFILE_CALLBACK_PDF = "/callback.pdf?";
	private static final String FAKEFILE_PDF = ".pdf";
	private static final String RETRIEVE = "fcw-retrieve";
	private static final int FCW_GET = 0;
	private static final int FCW_POST = 1;
//	private static final int STATUS_OK = 0;
	private static final int STATUS_ERROR = 9999999;
	//Pdf


	/** イニシャライズ */
	public void init(ServletConfig config) throws ServletException {
		// HttpServletのinitメソッドを起動
		super.init(config);
	}



	/**
	 * GET の処理。
	 */
	public void doGet(HttpServletRequest req, HttpServletResponse res)
	{
		try {
			String fcw = req.getParameter(RETRIEVE);
			if (fcw == null){
				cifServletMain(req, res, FCW_POST);
			}else{
				cifServletMain(req, res, FCW_GET);
			}
		} catch (Exception e) {
			errorControl(e,req,res);
		}
	}

	/**
	 * POST の処理。
	 */
	public void doPost(HttpServletRequest req, HttpServletResponse res)
	{
		try {
			cifServletMain(req, res, FCW_POST);
		} catch (Exception e) {
			errorControl(e,req,res);
		}
	}

	
	/** CifServletのメインコントロール*/
	private void cifServletMain(HttpServletRequest req, HttpServletResponse res, int method)
	{
		try{


			if(method==FCW_POST){
				startMain();
				mainControl(req,res,method);
			}else{
				String koteidata[][]={};
				Vector data=new Vector();
				pdfControl(req,res,koteidata,data,0,"",method);
			}
			exitMain();
			
		}
		catch (Exception e){
			errorControl(e,req,res);
		}
	}
	
	
	public void mainControl(HttpServletRequest req, HttpServletResponse res)
		throws Exception
	{

	}
	
	

	/** cifServletMainから呼ばれるオーバーライド専用メソッド
	    アプリケーションはこのメソッドをオーバーライドする。*/
	public abstract void mainControl(HttpServletRequest req, HttpServletResponse res,int method)throws Exception;
	
//	public void mainControl(HttpServletRequest req, HttpServletResponse res,int method)
//		throws Exception
//	{
	
	
	
//	}
	
	
	
	
	/** initから呼ばれるオーバーライド専用メソッド
	    アプリケーションはこのメソッドをオーバーライドする。*/
	public abstract void setProperties();
	
	

















	public void pdfControl(HttpServletRequest request,HttpServletResponse response,String koteidata[][],Vector data,int vectorCount,String formatFileName,int method) throws Exception{
		SessionAgent agent = null;	// エージェント
		HttpSession session = null;	// セッション

		// 処理を開始します
		while (agent == null) {
			// セッション（HttpSession）を獲得します。
			session = request.getSession(true);
			if (session == null) {
				// セッションオブジェクトは得られない場合、致命的なエラー。
				this.returnHttpErrorResponse(response, null, "INTERNAL ERROR (session tracking error).", STATUS_ERROR);
				return;
			}

			//--------------------------------------------------------------
			// エージェントを獲得します。
			// セッション単位でエージェントオブジェクトを１個ずつ持ちます。
			//--------------------------------------------------------------
			try {
				// キー AGENTNAME で SessionAgent オブジェクトを保持しています。
				agent = (SessionAgent)session.getAttribute(AGENTNAME);
				if (agent == null) {		// 新規セッションの場合
					synchronized (_sessionLock) {
						// 新規に SessionAgent インスタンスを生成します。
						agent = new SessionAgent(session.getId(), null, null);
					}

					if (_timeout > 0) {
						// セッションタイマーをセットします。
						agent.setSessionTimer(_timeout, this, session);
					}

					// このセッションで作成したエージェントを保持します。
					
					session.setAttribute(AGENTNAME, agent);
				} else {			// 継続セッションの場合
					agent.stopTimer();	// タイマーを止めます。
				}
			} catch (FMSystemException e) {
				throw e;
			} catch (FMPropertyException e) {
				int code = e.getStatusCode();
				this.returnHttpErrorResponse(response, null, e.getMessage(), code);
				if (session != null) {
					session.invalidate();
				}
				return;
			} catch (IllegalStateException e) {
				if (session != null) {
					session.invalidate();
				}
				agent = null;
				continue;
			}

			synchronized (agent) {
				// エージェントを獲得・ロックしたので、セッションの正当性を再確認します。
				if (agent != (SessionAgent)session.getAttribute(AGENTNAME)) {
					throw new IllegalStateException();
				}
				FMResponse result = null;	// オーバレイの結果
//				boolean canOverlay = false;	// オーバレイの準備ができたかどうか

				try {
					// request 中のパラメータを読みこみます。
					agent.parseParameters(request);

					if(!agent.isCallback()) {
						agent.clear();		// 既存Jobのクリア(temp削除)
						agent.setFMParameters(koteidata,data,vectorCount,formatFileName);
					}
				} catch (Exception e) {
					throw e;
				}

				//---------------------------------------------------------
				// オーバレイの実行
				//---------------------------------------------------------
				try {
					//---------------------------------------------------------
					// Internet Explorer の変な動作に対応するための処理
					//---------------------------------------------------------
					if (method == FCW_GET && agent.isCallback()) {
						//---------------------------------------------------------
						// GET リクエストで、かつ、プログラムが発行したコールバックである場合。
						// セッションで蓄えておいたレスポンスを再度返します。
						//---------------------------------------------------------
						result = agent.getLastResponse();
						if (result == null) {
							throw new FMPrintException("Session may have timed out.", STATUS_ERROR);
						}
					} else {
						// 明示的なオーバレイ実行命令があった
						if (agent.canOverlay()) {
							result = agent.overlay();
							if (result == null) {		// 使用できるコンポーザがありません。
								throw new FMPrintException("Request failed because no composer is available at this time. Call system manager.", STATUS_ERROR);
							}
						} else {
							// オーバレイを実施できるだけのパラメータがそろっていない。
							String msg = agent.getMessage();
							throw new FMPropertyException(msg, STATUS_ERROR);
						}
					}
				} catch (FMPrintException e) {
					int code = e.getStatusCode();
					this.returnHttpErrorResponse(response, null, e.getMessage(), code);
					agent.startTimer();	// startTimer() します。
					return;
				} catch (FMSystemException e) {
					throw e;
				} catch (FMPropertyException e) {
					int code = e.getStatusCode();
					this.returnHttpErrorResponse(response, null, e.getMessage(), code);
					agent.startTimer();	// startTimer() します。
					return;
				}
				
				//---------------------------------------------------------
				// 結果の処理
				//---------------------------------------------------------
				try {
					this.returnHttpResponse(response, agent, result, method);
				} catch (FMSystemException e) {
					throw e;
				} catch (Exception e) {
					throw e;
				}
				agent.startTimer();
				return;	// while を抜ける
			} // synchronized (agent)
		} /* while */
	}
























	//--------------------------------------------------------------
	// タイマー関連
	//--------------------------------------------------------------

	/**
	 * エージェントのタイマー機能で呼び出されるハンドラです。
	 * IE の場合、PDF取得が、何度か失敗する可能性があるため、
	 * 生成結果をすぐにクリアするわけにはいきません。
	 * セッションタイムアウト時に、クリアします。
	 */
	public synchronized void handleTimer(Object userInfo) {
		try {
			HttpSession session = (HttpSession)userInfo;	// セッション
			if (session != null) {
				SessionAgent agent = (SessionAgent)session.getAttribute(AGENTNAME);
				if (agent != null) {
					// agent オブジェクトに対して何か呼び出している最中はロックがかかるようにする。
					synchronized (agent) {
						agent.invalidate();
					}
				}
				session.removeAttribute(AGENTNAME);
				//session.invalidate();
			}
		} catch (IllegalStateException  e) {
			e.printStackTrace();
		}
	}

	//--------------------------------------------------------------
	// レスポンス関連
	//--------------------------------------------------------------

	/**
	 * FcwResponseオブジェクトの内容を用いて、サーブレットからのレスポンスを構成するためのメソッドです。.
	 */
	private void returnHttpResponse(HttpServletResponse response, SessionAgent agent,
	                                FMResponse result, int method)
	                                throws FMSystemException, IOException {
		boolean returnGet = false;
		boolean useFrame = false;

		long dateVal = System.currentTimeMillis();
		response.setHeader("Pragma", "no-cache");
		response.setDateHeader("Expires", (long)0);
		response.setDateHeader("Date", dateVal);

		if (!agent.isCallback()) {
			returnGet = true;
			useFrame = true;
		}

		//NECIKO if (result.getStatus() == STATUS_OK) {
		if ( ((Integer)result.get("fm-status")).intValue() == 0){
			if ((method == FCW_POST && returnGet) || useFrame) {	// 新規のオーバレイリクエストの場合
				try {
					// データ取得用の GET ページを作成して返します
					this.returnCallback(response, agent, result);
				} catch (FMSystemException e) {
					throw e;
				} catch (IOException e) {
					throw e;
				}
			} else {						// コールバックによるPDF要求の場合
				try {
					// PDF データを出力します
					this.returnPDF(response, agent, result);
				} catch (SocketException e) {
				} catch (IOException e) {
					throw e;
				}
			}
		} else {
			//NECIKO this.returnHttpErrorResponse(response, agent, result.getMessage(), result.getStatus());
			this.returnHttpErrorResponse(response, agent, (String)result.get("fm-message"),
			                             ((Integer)result.get("fm-status")).intValue());
		}
	}


	/**
	 * データ取得用の GET ページを作成して返します。.
	 */
	private void returnCallback(HttpServletResponse response, SessionAgent agent, FMResponse result)
	             throws FMSystemException, SocketException, IOException {
		ServletOutputStream servletOut = null;
		try {
//			agent.resetOutputStream(null);
			ByteArrayOutputStream byteOut = new ByteArrayOutputStream();
			DataOutputStream out = new DataOutputStream(byteOut);
			String url;
			response.setContentType("text/html");
			String uid = agent.getUniqueId();
			url = "http://" + agent.getRequestHost() + agent.getRequestUri() + FAKEFILE_CALLBACK_PDF + RETRIEVE + "=" + uid + FAKEFILE_PDF;

			out.write("<HTML><FRAMESET rows=\"0,*\" border=0 framespacing=0>".getBytes("Shift_JIS"));
			out.write(("<FRAME marginheight=1 marginwidth=1 noresize scrolling=\"no\" src=\"http://" + agent.getRequestHostIP() + "/n2fcw/blank.html\">").getBytes("Shift_JIS"));
			out.write(("<FRAME marginheight=0 marginwidth=0 noresize scrolling=\"no\" name=\"PDFView\" src=\"" + url + "\">").getBytes("Shift_JIS"));
			out.write("</FRAMESET></HTML>".getBytes("Shift_JIS"));
			out.flush();
			byte[] buf = byteOut.toByteArray();
			response.setContentLength(buf.length);
			servletOut = response.getOutputStream();
			servletOut.write(buf);
			try {
				servletOut.flush();
				out.flush();
				byteOut.flush();
				out.close();
				byteOut.close();
			} catch (Exception e2) {
			}
		} catch (FMSystemException e) {
			throw e;
		} catch (SocketException e) {
			throw e;
		} catch (IOException  e) {
			throw e;
		} finally {
			if (servletOut != null) {
				servletOut.flush();
//				agent.resetOutputStream(servletOut);
			}
		}
	}

	/**
	 * PDF データを出力します。.
	 */
	private void returnPDF(HttpServletResponse response, SessionAgent agent, FMResponse result)
	             throws SocketException, IOException {
		InputStream in = null;
		ServletOutputStream servletOut = null;
		int outSize = 0;
		try {
//			agent.resetOutputStream(null);
			response.setStatus(HttpServletResponse.SC_OK);
			response.setContentType("application/pdf");
			//NECIKO response.setContentLength((int)result.length());
			//  Content-Length ヘッダーの設定はメソッド化
			setContentLength(response, result);
			//NECIKO in = result.getInputStream();
			//  FMResponseクラスからgetInputStreamメソッドが無くなった。
			//  jobクラスからFMResponseOperatorクラスを生成してInputStreamを取得するよう変更
			FMJob job = agent.getJob();
			FMResponseOperator resOpe = job.getResponseOperator();
			in = resOpe.getInputStream();

			outSize = 0;
			servletOut = response.getOutputStream();
			byte [] buf = new byte[2048];
			int nread;
			while ((nread = in.read(buf)) != -1) {
				servletOut.write(buf, 0, nread);
				outSize += nread;
			}
			servletOut.flush();
		} catch (SocketException e) {
//			agent.resetOutputStream(servletOut);
			servletOut = null;
			throw e;
		} catch (IOException e) {
			e.printStackTrace();
			throw e;
		} finally {
			if (in != null) {
				in.close();
			}
			if (servletOut != null) {
				servletOut.flush();
//				agent.resetOutputStream(servletOut);
			}
		}
	}

	/**
	 * NECIKO
	 *
	 * Content-Length ヘッダーを設定する。
	 */
	private void setContentLength(HttpServletResponse response, FMResponse overlayRes) {
		// レスポンスには、"fm-databytes" or "fm-datafile" のどちらかが必ず設定されている。
		long length = 0;
		byte[] data = (byte[]) overlayRes.get("fm-databytes");
		if (data != null) {
			length = data.length;
		} else {
			File file = (File) overlayRes.get("fm-datafile");
			length = file.length();
		}

		// long値対応
		// response.setContentLength((int) length);
		response.setHeader("Content-Length", Long.toString(length));
	}

	/**
	 * エラー画面を出力します。.
	 */
	private void returnHttpErrorResponse(HttpServletResponse response, SessionAgent agent, String message, int code) {
		try {
			response.setContentType("text/html");
			PrintWriter errout = response.getWriter();
			errout.println("<HTML>");
			errout.println("<HEAD><TITLE>ERROR</TITLE>");
			errout.println("</HEAD>");
			errout.println("<BODY>");
			errout.println("<H2>Error Message : " + message +"</H2>");
			errout.println("<H2>Error Code    : " + code +"</H2>");
			errout.println("</BODY>");
			errout.println("</HTML>");
			errout.flush();
			errout.close();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
}



