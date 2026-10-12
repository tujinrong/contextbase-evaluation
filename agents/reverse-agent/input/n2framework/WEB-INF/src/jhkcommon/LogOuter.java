package jhkcommon;

/**
 *
 * 情報系データベース検索のＬｏｇｏｕｔを行うクラス、UserIdKitのdoLogOutを利用する。
 *
 * @date	H22.8.19	青木・浅見		センター集約対応なし
 *
 */

import java.io.IOException;

import javax.servlet.ServletConfig;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

public class LogOuter extends HttpServlet {

	String sDBServer = "";
	String sDBUser = "";
	String sDBPass = "";
	// データベースドライバのタイプを指定する定義 
	String sClass = "";
	// HTMLのスケルトン格納ディレクトリを定義
	String sFilePath = "";
	CifComon cCom;
	
	
	/** イニシャライズ */
	public void init(ServletConfig config) throws ServletException {
	
		// HttpServletのinitメソッドを起動
		super.init(config);
		// ServletConfigのメソッドを利用してサーブレットのパラメータを取得
		ServletContext scntxt = this.getServletContext();
		sFilePath= scntxt.getInitParameter("SFILEPATH");
		cCom = new CifComon(sFilePath, sDBServer, sDBUser, sDBPass);
	}



	/** Postメソッドリクエスト時の起動スレッド */
	public void doPost(HttpServletRequest req, HttpServletResponse res)
		throws IOException
	{
		mainControl(req, res);
	}


	/** Getメソッドリクエスト時の起動スレッド */
	public void doGet(HttpServletRequest req, HttpServletResponse res)
		throws IOException
	{
		mainControl(req, res);
	}



	/** メインコントロールメソッド */
	public void mainControl(HttpServletRequest req, HttpServletResponse res)
		throws IOException
	{
		String inputParams;
		inputParams=req.getParameter("BACK_HTML");
		if (inputParams == null) inputParams = "";
		String backHtmlName=new String(inputParams.getBytes("iso-8859-1"),"Windows-31J");
		inputParams=req.getParameter("IS_LOAN");
		if (inputParams == null) inputParams = "";
		String isLoan=new String(inputParams.getBytes("iso-8859-1"),"Windows-31J");
		if(isLoan.equals("true")){
			HttpSession session = req.getSession();

			session.removeAttribute("CifProfile");
		}
		
		UserIdKit uik = new UserIdKit();
		uik.doLogOut(req,res,cCom,backHtmlName,this.getServletContext());
	}
}

