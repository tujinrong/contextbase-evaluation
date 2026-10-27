package jhkcommon;

/**
 *
 * だんぷちゃん
 * 
 * @date	H22.8.25	青木・浅見		センター集約対応なし
 *
 */
import java.io.IOException;
import java.io.PrintWriter;
import java.util.Iterator;
import java.util.Vector;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletContext;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class DumpChan extends HttpServlet{

	/**
	 * 表示したいオブジェクトをVectorでわたすと、
	 * Htmlを作成してブラウザにリダイレクトしてくれる。
	 *	
	 *  利用の書式例
	 *	DumpChan dc=new DumpChan(); //インスタンスを作成
	 *	Vector v=new Vector(); //Vectorのインスタンスを作成
	 *	v.addElement(new String(userId));   //String型の変数「userId」の中を見たい場合。
	 *	v.addElement(new Boolean(isLogin)); //boolean型の変数「isLogin」の中を見たい場合。
	 *	v.addElement(new Integer(a));       //Integer型の変数「a」の中を見たい場合。
	 *	dc.makeDump(req,res,v); //このメソッドを起動。
	 */
	public boolean makeDump(HttpServletRequest req, HttpServletResponse res, Vector table)
		throws IOException
	{
		res.setContentType("text/html; charset=Windows-31J");
		res.setHeader("Expires", "Sat, 01 Jan 2000 00:00:00 GMT");
		res.setHeader("cache-control", "no-store");
		res.setHeader("Pragma", "no-cache");

		String backhtmlFile = "";
		
		backhtmlFile += "<BODY BGCOLOR='#FFC4FE'>ver1.4";
		backhtmlFile += "<H1><center><table><tr><td><FONT size=7 COLOR=#000080>だんぷちゃん</font></td>\n";
		backhtmlFile += "<td><IMG SRC=\"http://10.10.6.252/cif/onpu.gif\"></td>\n";
		backhtmlFile += "<td><FONT size=7 COLOR=#000080>登場ですぅ～</FONT></td></tr></table></center><BR>\n";
		backhtmlFile += "<pre>";
		backhtmlFile += "<table bgcolor=#ffffff border=0 cellpadding=10 cellspacing=1 width=80%>";

		String[][] decodeTable = {
			{"<",">"},
			{"&lt;","&gt;"}
		};
		
		Iterator it=table.iterator();
		int i=0;
		String s="";
		while(it.hasNext()){
			s = it.next().toString();
			
			
			int count=0;
			for (;count<decodeTable[0].length;count++){
				int index=0;
				while (index!=-1){
					index=s.indexOf(decodeTable[0][count]);
					if (index>-1){
						StringBuffer sb = new StringBuffer(s);
						sb.replace(index,index+1,decodeTable[1][count]);
						s=sb.toString();
					}
				}
			}
			backhtmlFile += "<tr bgcolor=#FFC4FE><td><font SIZE=3><pre>項目" +i+ "=</pre></font></td>\n";
			backhtmlFile += "<td><font SIZE=3><pre>" +s+ "</pre></font></td></tr>\n";
			i++;
		}
		backhtmlFile += "</table><BR>\n </font></pre>";
		PrintWriter pw = res.getWriter();
		pw.println(backhtmlFile);
		pw.close();

		//HttpSession session = req.getSession();
		/*
		RequestDispatcher rd =req.getRequestDispatcher("/servlet/Bye");
		*/
		
		ServletContext sc = this.getServletContext();
		RequestDispatcher rd =sc.getRequestDispatcher("/servlet/Bye");
		
		if (rd !=null){
			try{
				rd.forward(req,res);
			}
			catch (Exception e) {
				backhtmlFile+="ディスパッチャ・エラー";
			}
		}

		boolean flg=false;
		return flg;
	}

	
}

