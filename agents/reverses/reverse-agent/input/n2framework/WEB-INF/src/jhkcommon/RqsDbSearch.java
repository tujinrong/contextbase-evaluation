package jhkcommon;

/**
 * ＲＩＱＳのデータベースの項目の中で
 * 利用頻度が高い項目（例えば、店舗名）を
 * ＳＴＡＴＩＣ変数として保有し、
 * メソッドにてアプリケーションに返すクラス
 *
 * @date	H17.6.24	高橋			ＡＣＯＳ → 日次サーバ
 *  		H22.8.19	青木・浅見		センター集約対応
 *  		R04.12.21	Minori山口		渋谷支店店舗化対応
 *
 */

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.Hashtable;

import javax.naming.InitialContext;
import javax.sql.DataSource;

public  class RqsDbSearch  {

	//配列・ハッシュＴＡＢＬＥ作成ＦＬＡＧ（"OK":作成済）
	private	static String dbSearch;

	//配列（店舗名）
	private	static String[] tenbanTable = new String[600];

	//配列（店舗名２）
	private	static String[] tenbanTable2 = new String[600];

	//配列（店舗名３）
	private	static String[] tenbanTable3 = new String[600];

	//配列（店舗名４）
	private	static String[] tenbanTable4 = new String[6000];

	//配列（店舗名５）//getTenpomei5  2004/07/16追加　高柳
	private	static String[] tenbanTable5 = new String[600];

	//配列（店舗名６）//getTenpomei6  2004/08/04追加　高柳
	private	static String[] tenbanTable6 = new String[600];

	//配列（店舗名７）//getTenpomei7  2004/11/22追加　高柳
	private	static String[] tenbanTable7 = new String[600];

	
	//ハッシュＴＡＢＬＥ（業種）
	private	static Hashtable gyosyuTable = new Hashtable();

	//ハッシュＴＡＢＬＥ（科目）
	private	static Hashtable kamokuTable = new Hashtable();
	
	//ハッシュＴＡＢＬＥ（祭日）
	private	static Hashtable saijituTable2 = new Hashtable();

	//配列（祭日）
//	private	static String[] saijituTable = new String[500];
	
//	public static String startTime ;
//	public static String endTime ;
	/** 
	  * 
	　* ＲＩＱＳのデータベースに接続し
	　* ＳＴＡＴＩＣ変数を作成する
	　* ①DB.ＵＪ店舗管理台帳を読み、副店番 = 0 且 状態 = 0
     	　*   の店舗名を保有する
     	　* 
	  */
	public RqsDbSearch() throws Exception
	{

		String selectData="";
		String selectData2="";


		// ＳＱＬ編集

		String sql = "";

		String sqlTenpo = "SELECT 店番,漢字店名 ";
		sqlTenpo = sqlTenpo + "FROM DB2.ＵＪ店舗管理台帳 ";
		sqlTenpo = sqlTenpo + "WHERE 副店番 = 0 AND 状態 = 0" ;
		sqlTenpo = sqlTenpo + " ORDER BY 店番 " ;

		String sqlTenpo2 = "SELECT 店番,漢字店名 ";
		sqlTenpo2 = sqlTenpo2 + "FROM DB2.ＵＪ店舗管理台帳 ";
		sqlTenpo2 = sqlTenpo2 + "WHERE 副店番 = 0" ;
		sqlTenpo2 = sqlTenpo2 + " ORDER BY 店番 " ;
//
		String sqlTenpo3 = "SELECT 店番,漢字店名 ";
		sqlTenpo3 = sqlTenpo3 + "FROM DB2.ＵＪ店舗管理台帳 ";
		sqlTenpo3 = sqlTenpo3 + "WHERE 副店番 = 0" ;
		sqlTenpo3 = sqlTenpo3 + " ORDER BY 店番 " ;
//

		//String sqlTenpo4 = "SELECT ＢＲＫＥＹ,漢字店名 ";
		//sqlTenpo4 = sqlTenpo4 + "FROM DB.ＵＪ店舗管理台帳 ";
		//sqlTenpo4 = sqlTenpo4 + "WHERE 状態 = 0" ;
		String sqlTenpo4 = "SELECT 店番,副店番,漢字店名 ";
		sqlTenpo4 = sqlTenpo4 + "FROM DB2.ＵＪ店舗管理台帳 ";
		sqlTenpo4 = sqlTenpo4 + "WHERE 状態 = 0" ;
		sqlTenpo4 = sqlTenpo4 + " ORDER BY 店番 " ;


//getTenpomei5  2004/07/16追加　高柳

		String sqlTenpo5 = "SELECT 店番,漢字店名 ";
		sqlTenpo5 = sqlTenpo5 + "FROM DB2.ＵＪ店舗管理台帳 ";
		sqlTenpo5 = sqlTenpo5 + "WHERE 副店番 = 0" ;
		sqlTenpo5 = sqlTenpo5 + " ORDER BY 店番 " ;

//getTenpomei6  2004/08/04追加　高柳

		String sqlTenpo6 = "SELECT 店番,漢字店名 ";
		sqlTenpo6 = sqlTenpo6 + "FROM DB2.ＵＪ店舗管理台帳 ";
		sqlTenpo6 = sqlTenpo6 + "WHERE 副店番 = 0 AND 状態 = 0" ;
		sqlTenpo6 = sqlTenpo6 + " ORDER BY 店番 " ;


//getTenpomei7  2004/11/22追加　高柳

		String sqlTenpo7 = "SELECT 店番,漢字店名 ";
		sqlTenpo7 = sqlTenpo7 + "FROM DB2.ＵＪ店舗管理台帳 ";
		sqlTenpo7 = sqlTenpo7 + "WHERE 副店番 = 0"  ;
		sqlTenpo7 = sqlTenpo7 + " ORDER BY 店番 " ;

		
		String sqlGyosyu = "SELECT コード,項目１ ";
		sqlGyosyu = sqlGyosyu + "FROM DB2.ＵＪ業種 ";
		sqlGyosyu = sqlGyosyu + " ORDER BY コード " ;

		String sqlKamoku = "SELECT コード,項目１ ";
		sqlKamoku = sqlKamoku + "FROM DB2.ＵＪ科目 ";
		sqlKamoku = sqlKamoku + " ORDER BY コード " ;

		String sqlSaijitu = "SELECT 日付 ";
		sqlSaijitu = sqlSaijitu + "FROM DB2.Ｕ祭日 ";
		sqlSaijitu = sqlSaijitu + " ORDER BY 日付 " ;

		Connection conn =null;
		Statement stmt =null;

		try{

			// データベースへの接続を行う
			DataSource ds = (DataSource) new InitialContext().lookup("jdbc/Oracle_SP2NM");
			conn = ds.getConnection();
			conn.setAutoCommit(false);

			// ＳＱＬをデータベースに送るためのStatementオブジェクトの作成
			stmt = conn.createStatement();

			// ＳＱＬの結果をResultSetオブジェクトを作成し格納する

			sql = sqlTenpo;
			ResultSet rst = stmt.executeQuery(sql);

			// ＳＱＬの結果格納ResultSetオブジェクトから読み込み
			while(rst.next()){
				selectData=rst.getString(1);
				if(selectData==null) selectData="";
				int cnt = Integer.parseInt(selectData);

				selectData=rst.getString(2);
				if(selectData==null) selectData="";

				tenbanTable[cnt] = selectData ; 
			}

			// ＳＱＬの結果をResultSetオブジェクトを作成し格納する

			sql = sqlTenpo2;
			rst = stmt.executeQuery(sql);

			// ＳＱＬの結果格納ResultSetオブジェクトから読み込み
			while(rst.next()){
				selectData=rst.getString(1);
				if(selectData==null) selectData="";
				int cnt = Integer.parseInt(selectData);

				selectData=rst.getString(2);
				if(selectData==null) selectData="";

				tenbanTable2[cnt] = selectData ; 
			}
			// ＳＱＬの結果をResultSetオブジェクトを作成し格納する

			sql = sqlTenpo3;
			rst = stmt.executeQuery(sql);

			// ＳＱＬの結果格納ResultSetオブジェクトから読み込み
			while(rst.next()){
				selectData=rst.getString(1);
				if(selectData==null) selectData="";
				int cnt = Integer.parseInt(selectData);

				selectData=rst.getString(2);
				if(selectData==null) selectData="";

				tenbanTable3[cnt] = selectData ; 
			}

			sql = sqlTenpo4;
			rst = stmt.executeQuery(sql);

			// ＳＱＬの結果格納ResultSetオブジェクトから読み込み
			while(rst.next()){
				selectData=rst.getString(1);
				if(selectData==null) selectData="";

				selectData=selectData+rst.getString(2);
				if(selectData==null) selectData="";
				int cnt = Integer.parseInt(selectData);

				selectData=rst.getString(3);
				if(selectData==null) selectData="";

				tenbanTable4[cnt] = selectData ; 
			}


//   
			// ＳＱＬの結果をResultSetオブジェクトを作成し格納する
			//getTenpomei5  2004/07/16追加　高柳

			sql = sqlTenpo5;
			rst = stmt.executeQuery(sql);


			// ＳＱＬの結果格納ResultSetオブジェクトから読み込み
			while(rst.next()){
				selectData=rst.getString(1);
				if(selectData==null) selectData="";
				int cnt = Integer.parseInt(selectData);

				selectData=rst.getString(2);
				if(selectData==null) selectData="";

				tenbanTable5[cnt] = selectData ; 
			}


			// ＳＱＬの結果をResultSetオブジェクトを作成し格納する
			//getTenpomei6  2004/08/04追加　高柳

			sql = sqlTenpo6;
			rst = stmt.executeQuery(sql);

			// ＳＱＬの結果格納ResultSetオブジェクトから読み込み
			while(rst.next()){
				selectData=rst.getString(1);
				if(selectData==null) selectData="";
				int cnt = Integer.parseInt(selectData);

				selectData=rst.getString(2);
				if(selectData==null) selectData="";

				tenbanTable6[cnt] = selectData ; 
			}


			// ＳＱＬの結果をResultSetオブジェクトを作成し格納する
			//getTenpomei7  2004/11/22追加　高柳

			sql = sqlTenpo7;
			rst = stmt.executeQuery(sql);

			// ＳＱＬの結果格納ResultSetオブジェクトから読み込み
			while(rst.next()){
				selectData=rst.getString(1);
				if(selectData==null) selectData="";
				int cnt = Integer.parseInt(selectData);

				selectData=rst.getString(2);
				if(selectData==null) selectData="";

				tenbanTable7[cnt] = selectData ; 
			}


			// ＳＱＬの結果をResultSetオブジェクトに格納する
			sql = sqlGyosyu;
			rst = stmt.executeQuery(sql);

			// ＳＱＬの結果格納ResultSetオブジェクトから読み込み
			while(rst.next()){
				selectData=rst.getString(1);
				if(selectData==null) selectData="";

				while (selectData.length() < 4){
					selectData = "0" + selectData;
				}

				selectData2=rst.getString(2);
				if(selectData2==null) selectData2="";

				gyosyuTable.put(selectData,selectData2);
			}


			// ＳＱＬの結果をResultSetオブジェクトに格納する
			sql = sqlKamoku;
			rst = stmt.executeQuery(sql);

			// ＳＱＬの結果格納ResultSetオブジェクトから読み込み
			while(rst.next()){
				selectData=rst.getString(1);
				if(selectData==null) selectData="";

				while (selectData.length() < 2){
					selectData = "0" + selectData;
				}

				selectData2=rst.getString(2);
				if(selectData2==null) selectData2="";

				kamokuTable.put(selectData,selectData2);
			}

			// ＳＱＬの結果をResultSetオブジェクトに格納する
			sql = sqlSaijitu;
			rst = stmt.executeQuery(sql);

			int i = 0;
			// ＳＱＬの結果格納ResultSetオブジェクトから読み込み
			while(rst.next()){
				selectData=rst.getString(1);
				if(selectData==null) selectData="";
				saijituTable2.put(selectData,"0");
				
//				saijituTable[i] = selectData ; 
				i++;
			}
		
		dbSearch = "OK";

		}
		catch (Exception e){
			e.printStackTrace();
			throw new CifApplicationException("9000-02ＤＢ接続エラー;SQL=" + sql);
		}
		finally{
			try{
				// 自動コミットは無効なのでここでcommitする
				conn.commit();
				// Statement オブジェクトのデータベースと JDBC リソースを直ちに解放する
				stmt.close();
				// Statement オブジェクトのデータベースと JDBC リソースを直ちに解放する
				conn.close();
			}
			catch (Exception e){
				e.printStackTrace();
				throw new CifApplicationException("9000-02ＤＢ解放エラー;SQL=" + sql);
			}
		}
	}

	/** 
	  * 引数の店舗名を返す。
	　* ただし、①　引数が４桁以上なら先頭の３桁でサーチする。３桁未満なら先頭に"0"があるとみなす。
	  * 　　　　②　"999"入力時は、「総括」を返す。
	  * 　　　　③　副店番 = 0 且 状態 = 0の店舗名のみ返す。
     	　*         ④　②③以外なら、CifApplicationExceptionをthrowする。
     	　* 
	  */
	public static String getTenpomei(String tenban) throws Exception
	{
		String some_tenban;
//		String error ="該当店舗なし";

		//nullチェック
		if(tenban == null){
			throw new CifApplicationException("9000-01店舗コード;getParameter設定不具合");
		}

		//""チェック
		if(tenban.equals("")){
			throw new CifApplicationException("1003-03店舗コード:未入力");
		}
		
		//３桁に調整
		if(tenban.length() > 3){
			some_tenban = tenban.substring(0,3);
		}
		else {
			some_tenban = tenban;
		}

		//入力「999」なら「総括」を返す
		if(some_tenban.equals("999")){
			String sokatu = "総括";
			return  sokatu;
		}

		int cnt = 0;
		//引数の型変換（String 型　→　int型）
		try {
			cnt = Integer.parseInt(some_tenban);
		}
		catch(NumberFormatException e){
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}

		//配列・Hashtableが未作成ならば、RqsDbSearch()にて作成
		if(dbSearch == null){
			RqsDbSearch rqs = new RqsDbSearch() ;
		}
		else if(!(dbSearch.equals("OK")) ){
				RqsDbSearch rqs = new RqsDbSearch();
		}

		if(tenbanTable.length <= cnt ) {
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}
		
		
		if(tenbanTable[cnt] == null){
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}

		return tenbanTable[cnt];
	}


	/** 
	  * 引数（int型をString型に変換後）の店舗名を返す。
	　* ただし、①　引数が４桁以上なら先頭の３桁でサーチする。３桁未満なら先頭に"0"があるとみなす。
	  * 　　　　②　"999"入力時は、「総括」を返す。
	  * 　　　　③　副店番 = 0 且 状態 = 0の店舗名のみ返す。
     	　*         ④　②③以外なら、CifApplicationExceptionをthrowする。
     	　* 
	  */
	public static String getTenpomei(int tenban) throws Exception
	{
		return getTenpomei(Integer.toString(tenban));
	}

	/** 
	  * 引数の店舗名を返す。
	　* ただし、①　引数が４桁以上なら先頭の３桁でサーチする。３桁未満なら先頭に"0"があるとみなす。
	  * 　　　　②　"999"入力時は、「総括」を返す。
	  * 　　　　③　副店番 = 0の店舗名のみ返す。
     	　*         ④　②③以外なら、CifApplicationExceptionをthrowする。
     	　* 
	  */
	public static String getTenpomei2(String tenban) throws Exception
	{
		String some_tenban;
//		String error ="該当店舗なし";

		//nullチェック
		if(tenban == null){
			throw new CifApplicationException("9000-01店舗コード;getParameter設定不具合");
		}

		//""チェック
		if(tenban.equals("")){
			throw new CifApplicationException("1003-03店舗コード:未入力");
		}
		
		//３桁に調整
		if(tenban.length() > 3){
			some_tenban = tenban.substring(0,3);
		}
		else {
			some_tenban = tenban;
		}

		//入力「999」なら「総括」を返す
		if(some_tenban.equals("999")){
			String sokatu = "総括";
			return  sokatu;
		}

		int cnt = 0;
		//引数の型変換（String 型　→　int型）
		try {
			cnt = Integer.parseInt(some_tenban);
		}
		catch(NumberFormatException e){
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}

		//配列・Hashtableが未作成ならば、RqsDbSearch()にて作成
		if(dbSearch == null){
			RqsDbSearch rqs = new RqsDbSearch() ;
		}
		else if(!(dbSearch.equals("OK")) ){
				RqsDbSearch rqs = new RqsDbSearch();
		}

		if(tenbanTable2.length <= cnt ) {
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}

		if(tenbanTable2[cnt] == null){
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}

		return tenbanTable2[cnt];

	}


	/** 
	  * 引数（int型をString型に変換後）の店舗名を返す。
	　* ただし、①　引数が４桁以上なら先頭の３桁でサーチする。３桁未満なら先頭に"0"があるとみなす。
	  * 　　　　②　"999"入力時は、「総括」を返す。
	  * 　　　　③　副店番 = 0店舗名のみ返す。
     	　*         ④　②③以外なら、CifApplicationExceptionをthrowする。
     	　* 
	  */
	public static String getTenpomei2(int tenban) throws Exception
	{
		return getTenpomei2(Integer.toString(tenban));
	}


//getTenpomei3 2003/10/21追加 高橋
	/** 
	  * 引数の店舗名を返す。
	　* ただし、①　引数が４桁以上なら先頭の３桁でサーチする。３桁未満なら先頭に"0"があるとみなす。
	  * 　　　　②　"999"入力時は、「総括」を返す。
	  * 　　　　③　副店番 = 0の店舗名のみ返す。
     	　*         ④　該当店舗なしでもエラーにせず、店舗名をnullで返す。
     	　* 
	  */
	public static String getTenpomei3(String tenban) throws Exception
	{
		String some_tenban;
//		String error ="該当店舗なし";

		//nullチェック
		if(tenban == null){
			throw new CifApplicationException("9000-01店舗コード;getParameter設定不具合");
		}

		//""チェック
		if(tenban.equals("")){
			throw new CifApplicationException("1003-03店舗コード:未入力");
		}
		
		//３桁に調整
		if(tenban.length() > 3){
			some_tenban = tenban.substring(0,3);
		}
		else {
			some_tenban = tenban;
		}

		//入力「999」なら「総括」を返す
		if(some_tenban.equals("999")){
			String sokatu = "総括";
			return  sokatu;
		}

		int cnt = 0;
		//引数の型変換（String 型　→　int型）
		try {
			cnt = Integer.parseInt(some_tenban);
		}
		catch(NumberFormatException e){
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}

		//配列・Hashtableが未作成ならば、RqsDbSearch()にて作成
		if(dbSearch == null){
			RqsDbSearch rqs = new RqsDbSearch() ;
		}
		else if(!(dbSearch.equals("OK")) ){
				RqsDbSearch rqs = new RqsDbSearch();
		}

		if(tenbanTable3.length <= cnt ) {
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}
		
		//エラーにしない　店舗名をnullで返す。
		//if(tenbanTable3[cnt] == null){
		//	throw new CifApplicationException("1003-03店舗コード:" + tenban);
		//}

		return tenbanTable3[cnt];

	}


	/** 
	  * 引数（int型をString型に変換後）の店舗名を返す。
	　* ただし、①　引数が４桁以上なら先頭の３桁でサーチする。３桁未満なら先頭に"0"があるとみなす。
	  * 　　　　②　"999"入力時は、「総括」を返す。
	  * 　　　　③　副店番 = 0店舗名のみ返す。
     	　*         ④　該当店舗なしでもエラーにせず、店舗名をnullで返す。
     	　* 
	  */
	public static String getTenpomei3(int tenban) throws Exception
	{
		return getTenpomei3(Integer.toString(tenban));
	}


	/** 
	  * 引数の店舗名を返す。
	　* ただし、①　引数が５桁以上なら先頭の４桁でサーチする。４桁未満なら先頭に"0"があるとみなす。
	  * 　　　　②　"9999"入力時は、「総括」を返す。
	  * 　　　　③　状態 = 0の店舗名のみ返す。（営業している母店、有人出張所のみ）
  	　*         ④　②③以外なら、CifApplicationExceptionをthrowする。
     	　* 
	  */
	public static String getTenpomei4(String tenban) throws Exception
	{
		String some_tenban;
//		String error ="該当店舗なし";

		//nullチェック
		if(tenban == null){
			throw new CifApplicationException("9000-01店舗コード;getParameter設定不具合");
		}

		//""チェック
		if(tenban.equals("")){
			throw new CifApplicationException("1003-03店舗コード:未入力");
		}
		
		//４桁に調整
		if(tenban.length() > 4){
			some_tenban = tenban.substring(0,4);
		}
		else {
			some_tenban = tenban;
		}

		//入力「9999」なら「総括」を返す
		if(some_tenban.equals("9999")){
			String sokatu = "総括";
			return  sokatu;
		}

		int cnt = 0;
		//引数の型変換（String 型　→　int型）
		try {
			cnt = Integer.parseInt(some_tenban);
		}
		catch(NumberFormatException e){
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}

		//配列・Hashtableが未作成ならば、RqsDbSearch()にて作成
		if(dbSearch == null){
			RqsDbSearch rqs = new RqsDbSearch() ;
		}
		else if(!(dbSearch.equals("OK")) ){
				RqsDbSearch rqs = new RqsDbSearch();
		}

		if(tenbanTable4.length <= cnt ) {
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}
		
		
		if(tenbanTable4[cnt] == null){
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}

		return tenbanTable4[cnt];
	}


	/** 
	  * 引数（int型をString型に変換後）の店舗名を返す。
	　* ただし、①　引数が５桁以上なら先頭の４桁でサーチする。４桁未満なら先頭に"0"があるとみなす。
	  * 　　　　②　"9999"入力時は、「総括」を返す。
	  * 　　　　③　状態 = 0の店舗名のみ返す。（営業している母店、有人出張所のみ）
   	　*         ④　②③以外なら、CifApplicationExceptionをthrowする。
     	　* 
	  */
	public static String getTenpomei4(int tenban) throws Exception
	{
		return getTenpomei4(Integer.toString(tenban));
	}



//getTenpomei5  2004/07/16追加　高柳
	/** 
	  * 引数の店舗名を返す。
	　* ただし、①　引数が４桁以上なら先頭の３桁でサーチする。３桁未満なら先頭に"0"があるとみなす。
	  * 　　　　②　"999"入力時は、「総括」を返す。
	  * 　　　　③　副店番 = 0の店舗名のみ返す。
     	　*         ④　②③以外なら、CifApplicationExceptionをthrowする。
     	　* 
	  */
	public static String getTenpomei5(String tenban) throws Exception
	{
		String some_tenban;
//		String error ="該当店舗なし";

		//nullチェック
		if(tenban == null){
			throw new CifApplicationException("9000-01店舗コード;getParameter設定不具合");
		}

		//""チェック
		if(tenban.equals("")){
			throw new CifApplicationException("1003-03店舗コード:未入力");
		}
		
		//３桁に調整
		if(tenban.length() > 3){
			some_tenban = tenban.substring(0,3);
		}
		else {
			some_tenban = tenban;
		}

		//入力「999」なら「総括」を返す
		if(some_tenban.equals("999")){
			String sokatu = "総括";
			return  sokatu;
		}

		int cnt = 0;
		//引数の型変換（String 型　→　int型）
		try {
			cnt = Integer.parseInt(some_tenban);
		}
		catch(NumberFormatException e){
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}

		//配列・Hashtableが未作成ならば、RqsDbSearch()にて作成
		if(dbSearch == null){
			RqsDbSearch rqs = new RqsDbSearch() ;
		}
		else if(!(dbSearch.equals("OK")) ){
				RqsDbSearch rqs = new RqsDbSearch();
		}

		if(tenbanTable5.length <= cnt ) {
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}

		if(tenbanTable5[cnt] == null){
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}

		return tenbanTable5[cnt];

	}


	/** 
	  * 引数（int型をString型に変換後）の店舗名を返す。
	　* ただし、①　引数が４桁以上なら先頭の３桁でサーチする。３桁未満なら先頭に"0"があるとみなす。
	  * 　　　　②　"999"入力時は、「総括」を返す。
	  * 　　　　③　副店番 = 0店舗名のみ返す。
     	　*         ④　②③以外なら、CifApplicationExceptionをthrowする。
     	　* 
	  */
	public static String getTenpomei5(int tenban) throws Exception
	{
		return getTenpomei5(Integer.toString(tenban));
	}



//getTenpomei6  2004/08/04追加　高柳
	/** 
	  * 引数の店舗名を返す。
	　* ただし、①　引数が４桁以上なら先頭の３桁でサーチする。３桁未満なら先頭に"0"があるとみなす。
	  * 　　　　②　副店番 = 0 且 状態 = 0の店舗名のみ返す。
     	　*         ③　②以外なら、CifApplicationExceptionをthrowする。
     	　* 
	  */
	public static String getTenpomei6(String tenban) throws Exception
	{
		String some_tenban;
//		String error ="該当店舗なし";

		//nullチェック
		if(tenban == null){
			throw new CifApplicationException("9000-01店舗コード;getParameter設定不具合");
		}

		//""チェック
		if(tenban.equals("")){
			throw new CifApplicationException("1003-03店舗コード:未入力");
		}
		
		//３桁に調整
		if(tenban.length() > 3){
			some_tenban = tenban.substring(0,3);
		}
		else {
			some_tenban = tenban;
		}


		int cnt = 0;
		//引数の型変換（String 型　→　int型）
		try {
			cnt = Integer.parseInt(some_tenban);
		}
		catch(NumberFormatException e){
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}

		//配列・Hashtableが未作成ならば、RqsDbSearch()にて作成
		if(dbSearch == null){
			RqsDbSearch rqs = new RqsDbSearch() ;
		}
		else if(!(dbSearch.equals("OK")) ){
				RqsDbSearch rqs = new RqsDbSearch();
		}

		if(tenbanTable6.length <= cnt ) {
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}
		
		
		if(tenbanTable6[cnt] == null){
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}

		return tenbanTable6[cnt];
	}


	/** 
	  * 引数（int型をString型に変換後）の店舗名を返す。
	　* ただし、①　引数が４桁以上なら先頭の３桁でサーチする。３桁未満なら先頭に"0"があるとみなす。
	  * 　　　　②　副店番 = 0 且 状態 = 0の店舗名のみ返す。
     	　*         ③　②以外なら、CifApplicationExceptionをthrowする。
     	　* 
	  */
	public static String getTenpomei6(int tenban) throws Exception
	{
		return getTenpomei6(Integer.toString(tenban));
	}



//getTenpomei7  2004/11/22追加　高柳
	/** 
	  * 引数の店舗名を返す。
	　* ただし、①　引数が４桁以上なら先頭の３桁でサーチする。３桁未満なら先頭に"0"があるとみなす。
	  * 　　　　②　副店番 = 0 の店舗名のみ返す。
     	　*         ③　②以外なら、CifApplicationExceptionをthrowする。
     	　* 
	  */
	public static String getTenpomei7(String tenban) throws Exception
	{
		String some_tenban;
//		String error ="該当店舗なし";

		//nullチェック
		if(tenban == null){
			throw new CifApplicationException("9000-01店舗コード;getParameter設定不具合");
		}

		//""チェック
		if(tenban.equals("")){
			throw new CifApplicationException("1003-03店舗コード:未入力");
		}
		
		//３桁に調整
		if(tenban.length() > 3){
			some_tenban = tenban.substring(0,3);
		}
		else {
			some_tenban = tenban;
		}


		int cnt = 0;
		//引数の型変換（String 型　→　int型）
		try {
			cnt = Integer.parseInt(some_tenban);
		}
		catch(NumberFormatException e){
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}

		//配列・Hashtableが未作成ならば、RqsDbSearch()にて作成
		if(dbSearch == null){
			RqsDbSearch rqs = new RqsDbSearch() ;
		}
		else if(!(dbSearch.equals("OK")) ){
				RqsDbSearch rqs = new RqsDbSearch();
		}

		if(tenbanTable7.length <= cnt ) {
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}
		
		
		if(tenbanTable7[cnt] == null){
			throw new CifApplicationException("1003-03店舗コード:" + tenban);
		}

		return tenbanTable7[cnt];
	}


	/** 
	  * 引数（int型をString型に変換後）の店舗名を返す。
	　* ただし、①　引数が４桁以上なら先頭の３桁でサーチする。３桁未満なら先頭に"0"があるとみなす。
	  * 　　　　②　副店番 = 0 且 状態 = 0の店舗名のみ返す。
     	　*         ③　②以外なら、CifApplicationExceptionをthrowする。
     	　* 
	  */
	public static String getTenpomei7(int tenban) throws Exception
	{
		return getTenpomei7(Integer.toString(tenban));
	}





	/** 
	  * 引数の業種名を返す。
	　* ただし、①　引数が４桁以上なら先頭の４桁でサーチする。４桁未満なら先頭に"0"があるとみなす。
	  * 　　　　②　"2000"入力時は、「その他製造業」を返す。(ACCESS仕様継承)
	  * 　　　　③　DB.ＵＪ業種が保有しているコードの業種名称を返す。
     	　*         ④　②③以外なら、CifApplicationExceptionをthrowする。
     	　* 
	  */
	public static String getGyosyu(String gyosyuCode)throws Exception
	{

		
		if(searchGyosyu(gyosyuCode).equals("該当業種なし")){
			throw new CifApplicationException("1001-03業種コード:" + gyosyuCode);
		}


		return searchGyosyu(gyosyuCode);

	}
	/** 
	  * 引数の業種名を返す。
	　* ただし、①　引数が４桁以上なら先頭の４桁でサーチする。４桁未満なら先頭に"0"があるとみなす。
	  * 　　　　②　"2000"入力時は、「その他製造業」を返す。(ACCESS仕様継承)
	  * 　　　　③　DB.ＵＪ業種が保有しているコードの業種名称を返す。
     	　*         ④　②③以外なら、"該当業種なし"+業種コードを返す。
     	　* 
	  */
	public static String getGyosyu2(String gyosyuCode)throws Exception
	{

		
		if(searchGyosyu(gyosyuCode).equals("該当業種なし")){
			return  searchGyosyu(gyosyuCode) + gyosyuCode ;
		}

		return searchGyosyu(gyosyuCode);

	}

	/** 
	  * 引数の業種名を返す。
	　* ただし、①　引数が４桁以上なら先頭の４桁でサーチする。４桁未満なら先頭に"0"があるとみなす。
	  * 　　　　②　"2000"入力時は、「その他製造業」を返す。(ACCESS仕様継承)
	  * 　　　　③　DB.ＵＪ業種が保有しているコードの業種名称を返す。
     	　*         ④　②③以外なら、"該当業種なし"を返す。
     	　* 
	  */
	public static String searchGyosyu(String gyosyuCode)throws Exception
	{
		String some_gyosyuCode;
		String error ="該当業種なし";

		//nullチェック
		if(gyosyuCode == null){
			throw new CifApplicationException("9000-01業種コード;getParameter設定不具合");
		}

		//""チェック
		if(gyosyuCode.equals("")){
			throw new CifApplicationException("1001-03業種コード:未入力");
		}

		//４桁に調整
		if(gyosyuCode.length() > 4){
			some_gyosyuCode = gyosyuCode.substring(0,4);
		}
		else {
			some_gyosyuCode = gyosyuCode;
			while (some_gyosyuCode.length() < 4){
				some_gyosyuCode = "0" + some_gyosyuCode; 
			}
		}



		
		if(some_gyosyuCode.equals("2000")){
			String sonota = "その他製造業";
			return  sonota;
		}


		//配列・Hashtableが未作成ならば、RqsDbSearch()にて作成
		if(dbSearch == null){
			RqsDbSearch rqs = new RqsDbSearch();
		}
		else if(!(dbSearch.equals("OK")) ){
				RqsDbSearch rqs = new RqsDbSearch();
		}

		String gyosyumei = (String)gyosyuTable.get(some_gyosyuCode);
		if(gyosyumei == null){
//			error = error ;
			return error; 
		}


		return gyosyumei;

	}


	/** 
	  * 引数の科目名を返す。
	　* ただし、①　引数が３桁以上なら先頭の２桁でサーチする。２桁未満なら先頭に"0"があるとみなす。
	  * 　　　　②　DB.ＵＪ業種が保有しているコードの業種名称を返す。
     	　*         ③　②以外なら、CifApplicationExceptionをthrowする。
     	　* 
	  */
	public static String getKamoku(String kamokuCode)throws Exception
	{
		String some_kamokuCode;
//		String error ="該当科目なし";

		//nullチェック
		if(kamokuCode == null){
			throw new CifApplicationException("9000-01科目コード;getParameter設定不具合");
		}

		//""チェック
		if(kamokuCode.equals("")){
			throw new CifApplicationException("1001-03科目コード:未入力");
		}

		//２桁に調整
		if(kamokuCode.length() > 2){
			some_kamokuCode = kamokuCode.substring(0,2);
		}
		else {
			some_kamokuCode = kamokuCode;
			while (some_kamokuCode.length() < 2){
				some_kamokuCode = "0" + some_kamokuCode; 
			}
		}

		//配列・Hashtableが未作成ならば、RqsDbSearch()にて作成
		if(dbSearch == null){
			RqsDbSearch rqs = new RqsDbSearch();
		}
		else if(!(dbSearch.equals("OK")) ){
				RqsDbSearch rqs = new RqsDbSearch();
		}

		String kamokumei = (String)kamokuTable.get(some_kamokuCode);
		if(kamokumei == null){
			throw new CifApplicationException("1001-03科目コード:" + kamokuCode);
//			error = error + kamokuCode ;
//			return error; 
		}


		return kamokumei;

	}


	/** 
	  * 入力日付（８桁）が土・日以外の休業日であればtrueを返す、それ以外の場合falseを返す。
	　* ただし、①　引数が８桁以外なら、エラーを返す。
	  */
	public static boolean checkHoliday(String date)throws Exception
	{

		//nullチェック
		if(date == null){
			throw new CifApplicationException("9000-01日付;getParameter設定不具合");
		}

		//""チェック
		if(date.equals("")){
			throw new CifApplicationException("1008-03日付:未入力");
		}

		//８桁チェック
		if(date.length() != 8){
			throw new CifApplicationException("1008-03日付:" + date);
		}

		//配列・Hashtableが未作成ならば、RqsDbSearch()にて作成
		if(dbSearch == null){
			RqsDbSearch rqs = new RqsDbSearch();
		}
		else if(!(dbSearch.equals("OK")) ){
				RqsDbSearch rqs = new RqsDbSearch();
		}

		String flag = (String)saijituTable2.get(date);
		if(flag == null){
			return false; 
		}
		else {
			return true ;
		}
		
/**		
		SimpleDateFormat gSDFTime = new SimpleDateFormat("HH:mm:ss.SSS");
		Calendar cal = new GregorianCalendar();
		gSDFTime.setTimeZone(TimeZone.getTimeZone("JST"));
		startTime= gSDFTime.format(new java.util.Date());

		int cnt= 0;
		for(int i=0 ; i < saijituTable.length ; i++){

			if(saijituTable[i]== null){	
				gSDFTime.setTimeZone(TimeZone.getTimeZone("JST"));
				endTime= gSDFTime.format(new java.util.Date());
				return false; 
			}
			
			if(saijituTable[i].equals(date)){	
				gSDFTime.setTimeZone(TimeZone.getTimeZone("JST"));
				endTime= gSDFTime.format(new java.util.Date());
				return true; 
			}
		}
		gSDFTime.setTimeZone(TimeZone.getTimeZone("JST"));
		endTime= gSDFTime.format(new java.util.Date());
		return false ;
*/

	}

}
