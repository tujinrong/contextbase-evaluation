package jhkcommon;

/**
 *
 * HttpServletRequestのgetAttribute･setAttributeを利用し、
 * セッション管理、ユーザーログインの実行、状態の確認を行うクラス
 *
 * @date	H22.8.19	青木・浅見		センター集約対応
 *
 */
import java.io.IOException;

import javax.servlet.ServletContext;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

public class UserIdKit extends HttpServlet{


//	String htmlFileName = "";
	
	/**
	 * ログインを行うメソッド。
	 * getParameterも行ここで行い、ユーザＩＤをsetAttributeする。
	 * HtmlPicUpからのみ実行することができる。
	 * 他のクラスから起動した場合はログアウト状態となる。
	 */
	public void doLogin(HttpServletRequest req,HttpServletResponse res,CifComon cCom,ServletContext sc)
		throws IOException
	{

		String userId		="";
		String userIdUpper	=req.getParameter("USER_ID");
		String passWord		=req.getParameter("PASS_WORD");
		String cnPassWord   =sc.getInitParameter("CN_PASS");
		
		boolean loginStatus = false;
		HttpSession session = req.getSession();
		String backhtmlFile="PassWordErr.html";
		StringBuffer errMessage=new StringBuffer(20);

		if ((userIdUpper==null)|(userIdUpper.equals(""))|(passWord==null)|(passWord.equals(""))){
//			session.setAttribute("login","false");
			errMessage.append("ユーザ名・パスワードを入力してください。");
			loginStatus = false ;
		}else{
			userId=userIdUpper.toUpperCase();
			if(passWord.equals(cnPassWord)){
				loginStatus = true;
			}else{
				loginStatus = false;
				errMessage.append("ユーザ名・パスワードに誤りがあります。");
			}	
			
		}
		if(loginStatus){
			session.setAttribute("login","true");
			session.setAttribute("userId",userId);
			sc.log("***ログイン***"+userId);
		}else{
			HtmlDispatcher hd=new HtmlDispatcher();
			hd.GoHtml(req,res,backhtmlFile,cCom,errMessage.toString());
		}
	}

	
	
	

	/**
	 * ログアウトを行うメソッド。
	 */
	public void doLogOut(HttpServletRequest req,HttpServletResponse res,CifComon cCom,String backhtmlFile,ServletContext sc)
		throws IOException
	{
		HttpSession session = req.getSession();
		String userId = (String)session.getAttribute("userId");
		sc.log("***ログアウト***"+userId);
		session.setAttribute("login","false");
		session.setAttribute("userId","");
//		String backhtmlFile="Ciflogin.html";
		HtmlDispatcher hd=new HtmlDispatcher();
		hd.GoHtml(req,res,backhtmlFile,cCom,"");
	}



	/**
	 * ログインされているユーザＩＤを取得する。
	 * ユーザＩＤをgetAttributeし、戻り値としてString型のユーザＩＤを返す。
	 * ログインが行われていない状態で起動すると、空白「""」を返す。
	 */
	public String getUserId(HttpServletRequest req, HttpServletResponse res)
		throws IOException
	{
		String userId = "";
		HttpSession session = req.getSession();
		userId = (String)session.getAttribute("userId");

		return userId;
	}
	
	public String getUserId(HttpServletRequest req)
		throws IOException
	{
		String userId = "";
		HttpSession session = req.getSession();
		userId = (String)session.getAttribute("userId");

		return userId;
	}
	
	
	
	/**
	 * ログインされている職員番号を取得する。(８桁で返す)
	 * ユーザＩＤをgetAttributeし、戻り値としてString型のユーザＩＤを返す。
	 * ログインが行われていない状態で起動すると、空白「""」を返す。
	 */
	public String getSyokuinBango(HttpServletRequest req, HttpServletResponse res)
		throws IOException
	{
		String userId = "";
		HttpSession session = req.getSession();
		userId = (String)session.getAttribute("userId");
		
		String syokuinBango = userId;

		if(userId.length() > 8){
			//後ろの８桁をセット
			syokuinBango = userId.substring(userId.length() - 8);
		}
		else {
			//桁を8桁に補充する
			while (syokuinBango.length()<8){
				syokuinBango = syokuinBango + " " ;
			}
		}
		
		return syokuinBango;
	}
	
	
	
	/**
	 * デバック用メソッド、使用禁止！。
	 */
	public boolean getLogin(HttpServletRequest req, HttpServletResponse res)
		throws IOException
	{
		String loginText = "";
		boolean islogin=false;
		HttpSession session = req.getSession();
		loginText = (String)session.getAttribute("login");
		if (loginText==null) loginText="";
		if (loginText.equals("true")) islogin=true;
		
		return islogin;
	}

	
	
	/**
	 * デバック用メソッド、使用禁止！。
	 */
	public boolean checkUserId(HttpServletRequest req, HttpServletResponse res)
		throws IOException
	{
		String login = "";
		HttpSession session = req.getSession();
		login=(String)session.getAttribute("login");
		boolean islogin=false;
		if ((login.equals(null)) || (login.equals("")) || (login.equals("false"))){
			islogin=false;
		}else if(login.equals("true")){
			islogin=true;
		}
		return islogin;
	}

	
	
	/**
	 * ログインの状態をgetAttributeして調べ、
	 * ログインが行われていればtrueを戻り値として返す。
	 * 行われていない場合falseを返す。
	 * ログインが行われていない場合PreaseLogin.htmlに、
	 * ログインが行われているが、引数のhtmlFileNameが""の場合BackMenue.htmlに
	 * 制御をforwardする。
	 * 
	 */
	public boolean checkLogin(HttpServletRequest req, HttpServletResponse res, String htmlFileName,CifComon cCom)
		throws IOException
	{
		String backhtmlFile = "";
		String logintext = "";
		boolean islogin=false;
		HttpSession session = req.getSession();
		logintext=(String)session.getAttribute("login");
		if (logintext==null) logintext="";
		if ((logintext.equals("")) || (logintext.equals("false"))){
			backhtmlFile = "PreaseLogin.html";
		} else {
			if ((htmlFileName==null) || (htmlFileName.equals(""))){
				backhtmlFile = "BackMenue.html";
			} else {
				backhtmlFile = htmlFileName;
				islogin=true;
			}
		}
		if (islogin==false){
			String s="";
			HtmlDispatcher hd=new HtmlDispatcher();
			hd.GoHtml(req,res,backhtmlFile,cCom,s);
		}
		return islogin;
	}


}

