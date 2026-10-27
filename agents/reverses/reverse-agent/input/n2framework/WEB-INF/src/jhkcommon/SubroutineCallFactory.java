package jhkcommon;

/**
 *
 * 引数で与えられたサブルーチンコールを行い
 * エラー時にはエラーメッセージの表示を行うクラス
 * 
 * @date	H22.8.25	青木・浅見		センター集約対応
 * 
 */
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class SubroutineCallFactory extends HttpServlet{

	
	/**
	 * String search　で指定されたサブルーチンを起動して、正常終了なら値を返す。異常終了ならエラーの画面を返す。
	 * 
	 */
	public String callSubroutine(HttpServletRequest req, HttpServletResponse res, String search,String value,String returnHtmlName,CifComon cCom)
		throws Exception
	{
		String returnValue = "";
		String mes="";
		
		if((search==null) || (search.equals("")) ||(returnHtmlName==null) || (returnHtmlName.equals("")) ){
			 mes = "アプリケーションエラー：引数未入力";
		}
		else if(search.equals("seireki")){
			returnValue = cCom.getSeireki(value);

			if(returnValue.equals("PARAMERR")){
				 mes = "日付エラー：" + value ;
			}
		}
		else if(search.equals("searchError")){
				 mes = value;
		}
		if(mes.length() > 0){
			throw new CifApplicationException("9000-02"+mes);
		}

		return returnValue;

	}
	
}

