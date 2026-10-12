package jhkcommon;

/**
 *
 * 指定したHTMLにディスパッチするクラス。HtmlDispatcher
 *
 * @date	H22.8.19	青木・浅見		センター集約対応
 *
 */
import java.io.IOException;
import java.io.PrintWriter;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletContext;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class HtmlDispatcher extends HttpServlet{
	/**
	 * 表示したいＨＴＭＬファイルを指定すると、表示したのち自動的に終了する。
	 */
	public void GoHtml(HttpServletRequest req, HttpServletResponse res, String htmlFileName ,CifComon cCom,String addHtmlData)
		throws IOException
	{
		res.setContentType("text/html; charset=Windows-31J");
		res.setHeader("Expires", "Sat, 01 Jan 2000 00:00:00 GMT");
		res.setHeader("cache-control", "no-store");
		res.setHeader("Pragma", "no-cache");
//		ServletContext scntxt = this.getServletContext();
//		String sFilePath= scntxt.getInitParameter("SFILEPATH");

		String htmlFile = "";
		
//		sFilePath = sFilePath + "\\" + htmlFileName;
		try {
//			htmlFile = cCom.CifComonRead(sFilePath);
			if (addHtmlData==null) addHtmlData="";
			htmlFile =  cCom.CifComonHTMLRead(htmlFileName,addHtmlData);
		}
		catch (Exception e) {
			htmlFile += "<BODY BGCOLOR='#d0d0d0'>";
			htmlFile += "<H1>画面表示ができませんHtmlDispatcher<BR>\n";
			htmlFile += "<!-- Error : SubMenu File Cannot Read\n";
			htmlFile += e.getMessage() + " -->\n";
			htmlFile += "<BR>\n";
			htmlFile += "<BR>\n";
			// htmlFile += "<a href=http://10.10.100.9/ojitest/cif/Ciflogin.html>ログインへ</a>\n";
			htmlFile += "<a href=/webap/n2cif/Ciflogin.html>ログインへ</a>\n";
		}


		PrintWriter pw = res.getWriter();
		pw.println(htmlFile);
		pw.close();

//		HttpSession session = req.getSession();
//		RequestDispatcher rd =req.getRequestDispatcher("/servlet/Bye");
		
		ServletContext sc = this.getServletContext();
		RequestDispatcher rd =sc.getRequestDispatcher("/servlet/Bye");

		
		if (rd !=null){
			try{
				rd.forward(req,res);
			}
			catch (Exception e) {
				htmlFile+="ディスパッチャ・エラー";
			}
		}
	}
}

