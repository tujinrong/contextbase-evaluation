package jhkcommon;

/**
 *
 * OjiServlet
 *
 * @date	H22.8.27	青木・浅見		センター集約対応
 * 			H23.12.12	Minori米持		リーディング連携対応
 *
 */
  
import java.io.IOException;
import java.io.PrintWriter;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

import javax.naming.InitialContext;
import javax.servlet.ServletConfig;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.sql.DataSource;

/** CifアプリケーションのテンプレートになるServlet */
public abstract class OjiServlet extends HttpServlet{

	private String servletName="";
	private String databaseType="";
	private String outputType="";
	private String inPutHtmlName="";
	private String outPutHtmlName="";
	private String outPutHtmlName2="";
	private String pdfFileName="";
	private String outPutListName="";
	private String errorReturnClassName="";
	private String errorReturnHtmlName="";
	private String notUsed="";
	//
	private String sDBServer = "";
	private String sClass = "";
	private String s47Status="";
	// HTMLのスケルトン格納ディレクトリを定義
	private String sFilePath = "";
	private String sPath = "";

	public CifComon cCom;
	public SubroutineCallFactory scf;
	private String htmlSkeleton="";
	public String htmlSkeleton2="";
	private Exception initException;

	/** イニシャライズ */
	public void init(ServletConfig config) throws ServletException {
		// HttpServletのinitメソッドを起動
		super.init(config);
		setProperties();
		ServletContext scntxt = this.getServletContext();
		sFilePath= scntxt.getInitParameter("SFILEPATH");
		sPath= scntxt.getInitParameter("SSERVLETPATH");

		// CifComonのインスタンスを作成
		cCom = new CifComon(sFilePath, sDBServer, "", "");
		// SubroutineCallFactoryのインスタンスを作成
		scf = new SubroutineCallFactory();
		// 出力用ＨＴＭＬのスケルトンを読込み
		try{
			//NECIKO if(outPutHtmlName!=""&&outPutHtmlName!=null){
			if(!outPutHtmlName.equals("") && outPutHtmlName!=null){
				htmlSkeleton=cCom.CifComonHTMLRead(outPutHtmlName,"");
			}
			//NECIKO if(outPutHtmlName2!=""&&outPutHtmlName2!=null){
			if(!outPutHtmlName2.equals("") && outPutHtmlName2!=null){
				htmlSkeleton2=cCom.CifComonHTMLRead(outPutHtmlName2,"");
			}
		}
		catch(Exception e){
			initException=e;
		}
	}

	
	/** Postメソッドリクエスト時の起動スレッド */
	public void doPost(HttpServletRequest req, HttpServletResponse res)
	{
		ojiServletMain(req,res);
	}


	/** Getメソッドリクエスト時の起動スレッド */
	public void doGet(HttpServletRequest req, HttpServletResponse res)
	{
		ojiServletMain(req,res);
	}

	
	/** initから呼ばれるオーバーライド専用メソッド
	    アプリケーションはこのメソッドをオーバーライドする。*/
	abstract public void setProperties();
	
	
	/** CifServletのメインコントロール*/
	private void ojiServletMain(HttpServletRequest req, HttpServletResponse res)
	{
		try{
			startMain();

			//メニュー画面のみＤＢ管理ＤＢチェックを行わない。
			String inputParams;
			inputParams=req.getParameter("HTML_NAME");
			if (inputParams == null) inputParams = "";
			if(!new String(inputParams.getBytes("iso-8859-1"),"Windows-31J").equals("LoanMain.html")){
				check();
			}

			mainControl(req,res);
			exitMain();
			
		}
		catch (Exception e){
			errorControl(e,req,res);
			if(e.toString().startsWith("java.sql.SQLException")){
				e.printStackTrace();
				this.getServletContext().log("log",e);
			}
		}
	}
	
	
	
	protected void startMain()
		throws Exception
	{
		if (initException!=null){
			throw initException;
		}
	}
	
	
	/** ojiServletMainから呼ばれるオーバーライド専用メソッド
	    アプリケーションはこのメソッドをオーバーライドする。*/
	abstract public void mainControl(HttpServletRequest req, HttpServletResponse res)
		throws Exception;

	
	protected void exitMain()
		throws Exception
	{
	}


	protected void errorControl(Exception e,HttpServletRequest req, HttpServletResponse res)
	{
		// エラー時のメッセージとSQLを画面に表示するHTMLを作成 
		res.setContentType("text/html; charset=Windows-31J");
		res.setHeader("Expires", "Sat, 01 Jan 2000 00:00:00 GMT");
		res.setHeader("cache-control", "no-store");
		res.setHeader("Pragma", "no-cache");
		String errorHtml="";
		errorHtml ="<FONT SIZE=3 COLOR=#0000A0><B>処理がエラーとなりました。</B></FONT><br><br>\n";
		
		errorHtml+="<table width=630 border=0>\n";
		if(e.toString().startsWith("jhkcommon.CifApplicationException")){
			errorHtml +="<tr><td width=100 valign=top>エラー理由＝</td>";
			errorHtml +="<td>"+CifErrorCode.getErrorMessage(e.getMessage())+"</td></tr></table><br><br>\n";
		}else{
			errorHtml +="システムエラーが発生しています。システム部へ問い合わせてください。<br><br>\n\n";
		}
		
		if(errorReturnClassName.equals("")){
			errorHtml+="<FORM name=eroor method=post action=HtmlHandler>\n";
			errorHtml+="<input type=hidden name=HTML_NAME value="+inPutHtmlName+">\n";
			errorHtml+="<input type=hidden name=SERVLET_LINE value=LineMakeBrno>\n";
			errorHtml+="<input type=submit value=もう一度入力画面に戻る>\n";
			errorHtml+="</FORM>\n";
		}else{
			errorHtml+="<FORM name=eroor method=post action="+errorReturnClassName+">\n";
			errorHtml+="<input type=hidden name=HTML_NAME value="+errorReturnHtmlName+">\n";
			errorHtml+="<input type=hidden name=SERVLET_LINE value=LineMakeBrno>\n";
			errorHtml+="<input type=submit value=もう一度入力画面に戻る>\n";
			errorHtml+="</FORM>\n";
		}
		
		errorHtml+="<table width=630 border=1>\n";
		
		errorHtml+="<tr><td width=110>className</td><td>"+servletName+"</td></tr>\n";
		errorHtml+="<tr><td>e.getMessage</td><td>"+e.getMessage()+"</td></tr>\n";
		errorHtml+="<tr><td>e.toString</td><td>"+e.toString()+"</td></tr>\n";
		errorHtml+="<tr><td>StackTrace</td><td>"+"\n";
		try{
			PrintWriter pw = res.getWriter();
			pw.println(errorHtml);
			e.printStackTrace(pw);
			
			pw.close();
		}
		catch (Exception eio){
		}
	}
	


	/** レスポンスヘッダーを定義する共通メソッド。 */
	public void makeResponseHeader(HttpServletRequest req, HttpServletResponse res)
//		throws IOException
	{
		// ブラウザに返すデータ形式を指定  
		res.setContentType("text/html; charset=Windows-31J");
		// HttpServletResponseのメソッドを利用してHTTPのヘッダ情報を指定 
		res.setHeader("Expires", "Sat, 01 Jan 2000 00:00:00 GMT");
		res.setHeader("cache-control", "no-store");
		res.setHeader("Pragma", "no-cache");
 		// HttpServletRequestのメソッドを利用してセッションをオブジェクトとして取得 
//		HttpSession session = req.getSession(true);
	}


	/** データベースのコネクションを取得する。 */
	public Connection createConnection()
		
	{
		Connection conn=null;
		try{
			DataSource ds = (DataSource) new InitialContext().lookup(databaseType);
			conn = ds.getConnection();
			conn.setAutoCommit(false);
		}
		catch (Exception e){
		}
		return conn;
	}


	public void make()
		throws IOException
	{

	}

	/** ＤＢ管理ＤＢのチェックを行う。 */
	protected void check() 
		throws Exception
	{
		//Connectionの取得
		Connection con = null;
		Statement stmt = null;
		boolean flg = false;

		try {
			DataSource ds = (DataSource) new InitialContext().lookup("jdbc/Oracle_SP2NM");
			con = ds.getConnection();
			con.setAutoCommit(false);
			stmt = con.createStatement();
			ResultSet rs = null;

			//ＵＤＢ管理ＤＢの検索
			StringBuffer sb = new StringBuffer();
			sb.append("select 処理中ＦＬＧ");
			sb.append(" from DB2.ＵＤＢ管理ＤＢ");
			sb.append(" where ＤＢ名 = 'Ｕ調査カード'");
			rs = stmt.executeQuery(sb.toString());
				
			while(rs.next()){
				if(rs.getLong("処理中ＦＬＧ")==0){
					flg = true;
				}
			}
		} catch (Exception e) {
			e.printStackTrace();
		} finally {
			try {
				if (stmt != null) stmt.close();
				if (con  != null) con.close();
				con = null;
			} catch (SQLException e1) {
				e1.printStackTrace();
			}
		}
		if(!flg){
			throw new CifApplicationException("1056");
		}
	}

	//アクセサメソッド
	
	public void setServletName(String servletName){
		this.servletName=servletName;
	}
	public void setDatabaseType(String databaseType){
		this.databaseType=databaseType;
	}
	public void setOutputType(String outputType){
		this.outputType=outputType;
	}
	public void setInPutHtmlName(String inPutHtmlName){
		this.inPutHtmlName=inPutHtmlName;
	}
	public void setOutPutHtmlName(String outPutHtmlName){
		this.outPutHtmlName=outPutHtmlName;
	}
	public void setOutPutHtmlName2(String outPutHtmlName2){
		this.outPutHtmlName2=outPutHtmlName2;
	}
	public void setPdfFileName(String pdfFileName){
		this.pdfFileName=pdfFileName;
	}
	public void setOutPutListName(String outPutListName){
		this.outPutListName=outPutListName;
	}
	public void setErrorReturnClassName(String errorReturnClassName){
		this.errorReturnClassName=errorReturnClassName;
	}
	public void setErrorReturnHtmlName(String errorReturnHtmlName){
		this.errorReturnHtmlName=errorReturnHtmlName;
	}
	public void setNotUsed(String notUsed){
		this.notUsed=notUsed;
	}

	public String getHtmlSkeleton(){
		return this.htmlSkeleton;
	}
	public String getFilePath(){
		return this.sFilePath;
	}
	public String getOutPutHtmlName(){
		return this.outPutHtmlName;
	}
	public String getInPutHtmlName(){
		return this.inPutHtmlName;
	}
	public String getPdfFileName(){
		return this.pdfFileName;
	}
	public String get47Status(){
		return this.s47Status;
	}
}

