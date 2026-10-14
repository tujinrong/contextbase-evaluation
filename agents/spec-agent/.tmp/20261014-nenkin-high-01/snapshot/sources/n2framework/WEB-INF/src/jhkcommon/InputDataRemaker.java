package jhkcommon;

/**
 *
 * 入力データを入力画面に復帰させる為のクラス
 * 
 * @date	H22.8.26	青木・浅見		センター集約対応
 *
 */
import java.util.Enumeration;
import java.util.Iterator;
import java.util.Vector;

import javax.servlet.RequestDispatcher;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

public class InputDataRemaker extends HttpServlet{

	HttpServletRequest req=null;
	HttpServletResponse res=null;
	Vector inputParams=null;	//{項目名,値,OK}

	public InputDataRemaker(HttpServletRequest req,HttpServletResponse res)
		throws Exception
	{
		this.req=req;
		this.res=res;
		this.inputParams=new Vector();
		Enumeration enum2=req.getParameterNames();
		String params;
		String paramsUnicode;
		String name;
		while(enum2.hasMoreElements()){
			name=enum2.nextElement().toString();
			params=req.getParameter(name);
			if (params == null) params = "";
			paramsUnicode=new String(params.getBytes("iso-8859-1"),"Windows-31J");
			String[] ss={name,paramsUnicode,"OK",""};
//			String[] ss={name,req.getParameter(name),"OK",""};
			inputParams.addElement(ss);
		}
	}
	/**
	 * エラーの項目ごとのメッセージを受取りテーブルにセット。
	 */
	
	public void setErrorLetter(String name,String letter){
		Iterator it=inputParams.iterator();
		String[] s=null;
		while(it.hasNext()){
			s = (String[])it.next();
			if(s[0].equals(name)){
				s[2]=letter;
				it.remove();
				inputParams.addElement(s);
				break;
			}
		}
	}


	
	/**
	 * 入力エラー発生時にinputDataError.htmlを表示する為に、HtmlPicUpへforwardする。
	 */
	public boolean reOpenInputHtml(String nextHtmlName){
		String path="/servlet/HtmlPicUp?HTML_NAME=inputDataError.html&SERVLET_LINE=LineMakeInputDataError";
		boolean status=forwardNextHtml(nextHtmlName,path);
		return status;
	}


	/**
	 * pathに指定されたservletにforwardする。
	 * REMAKE_VECTORに入力パラメータ
	 * NEXT_HTML_NAMEにnextHtmlNameをsetAttributeする。
	 */
	public boolean forwardNextHtml(String nextHtmlName,String path){
		boolean status=true;
		HttpSession session = req.getSession();
		session.setAttribute("REMAKE_VECTOR",inputParams);
		session.setAttribute("NEXT_HTML_NAME",nextHtmlName);
//		ServletContext sc = this.getServletContext();
//		RequestDispatcher rd =sc.getRequestDispatcher(path);
		RequestDispatcher rd =req.getRequestDispatcher(path);
		if (rd !=null){
			try{
				rd.forward(req,res);
			}
			catch (Exception e) {
				status=false;
			}
		}
		return status;
	}
	
	
	
}

