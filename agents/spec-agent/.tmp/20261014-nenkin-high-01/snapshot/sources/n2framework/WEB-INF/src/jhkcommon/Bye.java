package jhkcommon;

/**
 *
 * 何もしないで終わるすクラス
 *
 * @date	H22.8.19	青木・浅見		センター集約対応なし
 *
 */
import java.io.IOException;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class Bye extends HttpServlet {


	
	
	/** グローバル変数のイニシャライズ */
	public void init(ServletConfig config) throws ServletException {
		// HttpServletのinitメソッドを起動
		super.init(config);
	}


	/** http Postリクエスト時の起動スレッド */
	public void doPost(HttpServletRequest req, HttpServletResponse res)
		throws IOException
	{
		mainControl(req, res);
	}


	/** http Getリクエスト時の起動スレッド */
	public void doGet(HttpServletRequest req, HttpServletResponse res)
		throws IOException
	{
		mainControl(req, res);
	}



	/** メインコントロールメソッド */
	public void mainControl(HttpServletRequest req, HttpServletResponse res)
		throws IOException
	{

	}
}

