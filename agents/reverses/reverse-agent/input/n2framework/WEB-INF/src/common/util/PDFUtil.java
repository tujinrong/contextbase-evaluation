/*
 * 作成日: 2007/05/24
 *
 */
package common.util;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.PrintWriter;
import java.net.SocketException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Vector;

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
import com.itextpdf.text.pdf.PdfCopyFields;
import com.itextpdf.text.pdf.PdfReader;

import common.FWLog;
import common.pdf.FWSessionAgent;
import common.pdf.FWTimerHandler;

/**
 * データウェアハウス　ＰＤＦ帳票出力クラス
 * データを結合して使用する場合は、
 * ＰＤＦの再取得は実施せず、常にＰＤＦを新規出力する
 *
 * @author JSC kengo murayama
 *
 * @date	H22.9.3		青木・浅見		センター集約対応
 * @date	H24.5.8		NEC Soft 児高	SSO経由の場合のPDF作成エラー対応
 * @date	H26.3.4		Minori米持		PDFの保持後、結合出力（iText）メソッドの追加
 */
public class PDFUtil implements FWTimerHandler{

	private Object _sessionLock = new Object();		// セッションカウント用
	private static long _timeout = 180000;			// セッションタイムアウトの長さ（ミリ秒）
	private static final String AGENTNAME = "FcwAgent";	// セッションへの値設定で使用するキー文字列
	private static final String FAKE_SERVLET = "/servlet/common.ControlServlet";	//GETリクエストを受け付けるサーブレット
	private static final String FAKEFILE_CALLBACK_PDF = "/callback.pdf?";
	private static final String FAKEFILE_PDF = ".pdf";
	private static final String RETRIEVE = "fcw-retrieve";
	private static final int FCW_GET = 0;
	private static final int FCW_POST = 1;
//	private static final int STATUS_OK = 0;
	private static final int STATUS_ERROR = 9999999;

	private List pdfDataList = new ArrayList();		//ＰＤＦデータ保持用

	//PDFデータ取得
	public List getPdfDataList() {
		return pdfDataList;
	}
	/**
	 * PDFデータを直接追加：List<PdfReader>
	 * @param pdfDataList
	 */
	public void addPdfDataList(List pdfDataList) {
		for(int i=0;i<pdfDataList.size();i++){
			this.pdfDataList.add((PdfReader)pdfDataList.get(i));
		}
	}
	/**
	 * PDFデータを直接追加：PdfReader
	 * @param pdfData
	 */
	public void addPdfDataList(PdfReader pdfData) {
		this.pdfDataList.add(pdfData);
	}

	/**
	 * 
	 * @param request
	 * @param response
	 * @param koteidata
	 * @param data
	 * @param vectorCount
	 * @param formatFileName
	 * @param method
	 * @throws Exception
	 */
	public void pdfControl(HttpServletRequest request,
							HttpServletResponse response,
							String koteidata[][],
							Vector data,
							int vectorCount,
							String formatFileName,
							int method) throws Exception{
		FWSessionAgent agent = null;	// エージェント
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
				// キー AGENTNAME で FWSessionAgent オブジェクトを保持しています。
				agent = (FWSessionAgent)session.getAttribute(AGENTNAME);
				if (agent == null) {		// 新規セッションの場合
					synchronized (_sessionLock) {
						// 新規に FWSessionAgent インスタンスを生成します。
						FWLog.debug(this.getClass(), "agent new: SID=" + session.getId());
						agent = new FWSessionAgent(session.getId(), null, null);
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
				if (agent != (FWSessionAgent)session.getAttribute(AGENTNAME)) {
					throw new IllegalStateException();
				}
				FMResponse result = null;	// オーバレイの結果
				//boolean canOverlay = false;	// オーバレイの準備ができたかどうか

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

	/**
	 * ＰＤＦデータ保持用メソッド（iText使用）
	 * 
	 * @param request
	 * @param response
	 * @param koteidata
	 * @param data
	 * @param vectorCount
	 * @param formatFileName
	 * @param method
	 * @throws Exception
	 */
	public void addPdfControl(HttpServletRequest request,
							HttpServletResponse response,
							String koteidata[][],
							Vector data,
							int vectorCount,
							String formatFileName,
							int method) throws Exception{
		FWSessionAgent agent = null;	// エージェント
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
				// キー AGENTNAME で FWSessionAgent オブジェクトを保持しています。
				agent = (FWSessionAgent)session.getAttribute(AGENTNAME);
				if (agent == null) {		// 新規セッションの場合
					synchronized (_sessionLock) {
						// 新規に FWSessionAgent インスタンスを生成します。
						agent = new FWSessionAgent(session.getId(), null, null);
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
				if (agent != (FWSessionAgent)session.getAttribute(AGENTNAME)) {
					throw new IllegalStateException();
				}
				FMResponse result = null;	// オーバレイの結果
				//boolean canOverlay = false;	// オーバレイの準備ができたかどうか

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
					this.iTextReturnHttpResponse(response, agent, result, method);
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
				FWSessionAgent agent = (FWSessionAgent)session.getAttribute(AGENTNAME);
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
			FWLog.error(e);
		}
	}

	//--------------------------------------------------------------
	// レスポンス関連
	//--------------------------------------------------------------

	/**
	 * FcwResponseオブジェクトの内容を用いて、サーブレットからのレスポンスを構成するためのメソッドです。.
	 */
	private void returnHttpResponse(HttpServletResponse response, FWSessionAgent agent,
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
	 * FcwResponseオブジェクトの内容を用いて、サーブレットからのレスポンスを構成するためのメソッドです。.
	 * iText用のメソッドとして（returnHttpResponse）を改造
	 * 改造箇所については、ソース内コメント参照
	 */
	private void iTextReturnHttpResponse(HttpServletResponse response, FWSessionAgent agent,
	                                FMResponse result, int method)
	                                throws FMSystemException, IOException {
		boolean returnGet = false;
		boolean useFrame = false;

		long dateVal = System.currentTimeMillis();
		response.setHeader("Pragma", "no-cache");
		response.setDateHeader("Expires", (long)0);
		response.setDateHeader("Date", dateVal);

//【コメントアウト：コールバックのロジックに入らないようにする】
//		if (!agent.isCallback()) {
//			returnGet = true;
//			useFrame = true;
//		}

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
					this.iTextReturnPDF(response, agent, result);
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
	private void returnCallback(HttpServletResponse response, FWSessionAgent agent, FMResponse result)
	             throws FMSystemException, SocketException, IOException {
		ServletOutputStream servletOut = null;
		try {
//			agent.resetOutputStream(null);
			ByteArrayOutputStream byteOut = new ByteArrayOutputStream();
			DataOutputStream out = new DataOutputStream(byteOut);
			String url;
			response.setContentType("text/html");
			String uid = agent.getUniqueId();
//			url = "http://" + agent.getRequestHost() + agent.getRequestUri() + FAKEFILE_CALLBACK_PDF + RETRIEVE + "=" + uid + FAKEFILE_PDF;
//			url = "http://webts.dntsv01.johokubank.co.jp/webap/dwh/servlet/common.ControlServlet" + FAKEFILE_CALLBACK_PDF + RETRIEVE + "=" + uid + FAKEFILE_PDF;

			String applPath = agent.getRequestUri().substring(0, agent.getRequestUri().lastIndexOf('/')); //「～/Action.do」の前を切り取る
			url = applPath + FAKE_SERVLET + FAKEFILE_CALLBACK_PDF + RETRIEVE + "=" + uid + FAKEFILE_PDF;

			out.write("<HTML><FRAMESET rows=\"0,*\" border=0 framespacing=0>".getBytes("Windows-31J"));
			out.write(("<FRAME marginheight=1 marginwidth=1 noresize scrolling=\"no\" src=\"/n2fcw/blank.html\">").getBytes("Windows-31J"));
			out.write(("<FRAME marginheight=0 marginwidth=0 noresize scrolling=\"no\" name=\"PDFView\" src=\"" + url + "\">").getBytes("Windows-31J"));
			out.write("</FRAMESET></HTML>".getBytes("Windows-31J"));
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
	private void returnPDF(HttpServletResponse response, FWSessionAgent agent, FMResponse result)
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
			FWLog.error(e);
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
	 * PDF データを出力します。.
	 * iText用のメソッドとして（returnPDF）を改造
	 * 改造箇所については、ソース内コメント「※」参照
	 */
	private void iTextReturnPDF(HttpServletResponse response, FWSessionAgent agent, FMResponse result)
	             throws SocketException, IOException {
//※		InputStream in = null;
//※		ServletOutputStream servletOut = null;
//※		int outSize = 0;
		try {
//			agent.resetOutputStream(null);
			response.setStatus(HttpServletResponse.SC_OK);
			response.setContentType("application/pdf");
			//NECIKO response.setContentLength((int)result.length());
			//  Content-Length ヘッダーの設定はメソッド化
//※			setContentLength(response, result);
			//NECIKO in = result.getInputStream();
			//  FMResponseクラスからgetInputStreamメソッドが無くなった。
			//  jobクラスからFMResponseOperatorクラスを生成してInputStreamを取得するよう変更
			FMJob job = agent.getJob();
			FMResponseOperator resOpe = job.getResponseOperator();
//			in = resOpe.getInputStream();

//※追加--ここから--			
			BufferedInputStream inputstream = new BufferedInputStream(resOpe.getInputStream());
			PdfReader reader = new PdfReader(inputstream);
			addPdfDataList(reader);
//※追加--ここまで--
			
//※			outSize = 0;
//※			servletOut = response.getOutputStream();
//※			byte [] buf = new byte[2048];
//※			int nread;
//※			while ((nread = pdfData.read(buf)) != -1) {
//※				servletOut.write(buf, 0, nread);
//※				outSize += nread;
//※			}
//※			servletOut.flush();
		} catch (SocketException e) {
//			agent.resetOutputStream(servletOut);
//※			servletOut = null;
			throw e;
		} catch (IOException e) {
			FWLog.error(e);
			throw e;
		} finally {
//※			if (in != null) {
//※				in.close();
//※			}
//※			if (servletOut != null) {
//※				servletOut.flush();
//				agent.resetOutputStream(servletOut);
//※			}
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
	private void returnHttpErrorResponse(HttpServletResponse response, FWSessionAgent agent, String message, int code) {
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
			FWLog.error(e);
		}
	}

	/**
	 * 保持してきたＰＤＦを出力する
	 */
	public void outputPDF(HttpServletResponse res) throws Exception{
	
		try{
			//出力
			BufferedOutputStream outstream=new BufferedOutputStream(res.getOutputStream());
			res.setContentType("application/pdf");
			//PDF結合用のインスタンス生成
			PdfCopyFields pdfout = new PdfCopyFields(outstream);
			//PDFを追加する処理
			Iterator it = this.pdfDataList.iterator();
			PdfReader reader;
			while (it.hasNext()) {
				reader=(PdfReader)it.next();
				pdfout.addDocument(reader);
			}
			pdfout.close();		
		}catch (Exception e) {
			FWLog.error(e);
		}
	}

}
