package webon;

import java.io.BufferedInputStream;
import java.io.IOException;
import java.io.StringWriter;
import java.io.UnsupportedEncodingException;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLDecoder;
import java.net.URLEncoder;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;

import javax.naming.InitialContext;
import javax.naming.NamingException;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerException;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;

import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.xml.sax.SAXException;

import webon.base.InsertPathMngStatBase;
import webon.base.SelectFunctionMasterBase;
import webon.base.SelectOnlineOperationMastBase;
import webon.base.SelectPathMngMstBase;
import webon.base.SelectPathMngStatBase;
import webon.base.UpdatePathMngStatBase;
import webon.util.CastUtil;
import webon.base.SelectOperationBranchMstBase;
import common.CommonConst;
import common.FWLog;
import common.bean.LoginInfoBean;
import common.util.CommonConverter;
import common.util.CommonUtil;

public class WebonBase {
	/**
	* Webon汎用照会　Webon接続用モジュール (ダミー)
	* 
	* @author Minori 加瀬
	* 
	* @date	H24.11.01			新規作成
	* @date R02.02.06	京極		webonのFW化対応
	* 
	* 使い方①
	* 1.インスタンスを取得(getInstance)
	* 2.入力項目を設定(put)
	* 4.問い合わせを実施(doQuery,doQueryPdf)
	* 5.各種結果を取得(getResult～)
	* 
	* 使い方②
	* 1.インスタンス生成(new WebonBase、引数あり)
	* 2.入力項目を設定(put)
	* 4.問い合わせを実施(doQuery,doQueryPdf)
	* 5.各種結果を取得(getResult～)
	* 
	* 使い方③
	* 1.インスタンス生成(new WebonBase、引数なし)
	* 2.クエリ雛形生成(setQuery)
	* 3.入力項目を設定(put)
	* 4.問い合わせを実施(doQuery,doQueryPdf)
	* 5.各種結果を取得(getResult～)
	* 
	*/
	//メンバ変数
	protected String operationId = "";											//オペレーションID
	protected HashMap<String, String> query = new HashMap<String, String>();	//検索用クエリ
	protected String serverUrl = "";											//WEBONサーバのURL文字
	protected String serverUrlHead = "http://";									//WEBONサーバの接頭URL文字
	protected String serverUrlTail = "/woadp/DealFacade?";						//WEBONサーバの接尾URL文字【スケルトンなし】
	protected String serverUrlTailSkelton = "/woadp/DealFacadeSkeleton?";		//WEBONサーバの接尾URL文字【スケルトンあり】
	protected String encodedQueries = "";										//クエリ文字列
	protected HashMap<String, String> result = new HashMap<String, String>();	//戻り値
	public Node outputData=null;												//以下、結果
	public Node editData=null;
	public Node resultId=null;
	public Node message=null;
	public Node opeCode=null;
	public Node tradeName=null;
	public Node uplinkData=null;
	protected BufferedInputStream stream;			//XML生データ＆PDF結果データ
	protected Map<String, List<String>> headers;
	protected boolean XmlFlag=false;				//XML取得＆解析フラグ

	protected String serverAddress;	//Webonサーバ
	protected String passBrno;			//取引店舗コード
	
	protected boolean BackGroundFlag = false;	//バックグラウンド(子スレッドで取得)の時trueにする
	
	//定数
	private static int RETRY_MAX_ROOT=100;			//無限ループ回避
	//パス取得時のパラメータ
	private static int RETRY_MAX_PATHGET=10;
	private static int RETRY_INTERVAL_PATHGET=5000;	//ミリ秒
	//輻輳タイムアウトエラー時のパラメータ
	private static int RETRY_MAX_TIMEOUTERR=5;
	private static int RETRY_INTERVAL_TIMEOUTERR=1000;	//ミリ秒
	
	/**
	 * コンストラクタ
	 * 
	 * @param Connection
	 */
	public WebonBase (){
	}
	/**
	 * コンストラクタ
	 * 
	 * @param String	オペレーションＩＤ
	 * @param LoginInfoBean		ログイン情報
	 * @param Connection	DB接続
	 */
	public WebonBase (String oid, LoginInfoBean loginInfo, Connection con) throws Exception {
		setQuery (oid, loginInfo, con);
	}
	/**
	 * メンバ変数のqueryからURLエンコードされたクエリを作成し、
	 * encodedQueriesにセットする
	 * 
	 * @throws UnsupportedEncodingException エンコード失敗時
	 */
	public void encodeQuery () throws UnsupportedEncodingException {
		//クエリが空だったら、そのまま復帰
		if (query.isEmpty()) {
			FWLog.warn(getClass(), "クエリがセットされていません");
			return;
		}
		StringBuilder queries = new StringBuilder();
		StringBuilder logQueries = new StringBuilder();
		
		Iterator<String> it = query.keySet().iterator();
		while (it.hasNext()) {
			String key = it.next();
			String value = query.get(key);
			//FWLog.debug(getClass(),"★★★WEBONクエリエンコード　キー："+key+" 値："+value);
			//ログ出力用文字列作成
			logQueries.append(key+"="+value+"&");
			//エンコード実施
			String encKey;
			String encValue;
			try {
				encKey = URLEncoder.encode(key, "UTF-8");
				encValue = URLEncoder.encode(value, "UTF-8");
			} catch (UnsupportedEncodingException e) {
				FWLog.error("URLエンコードに失敗しました 文字列：" + key + " " + value);
				throw e;
			}
			queries.append(encKey+"="+encValue+"&");
		}
		
		//ログ出力
		FWLog.info(getClass(), "Webon問い合わせクエリ(エンコード前)："+ serverUrl + logQueries.toString());		
		//フィールドにセット
		encodedQueries = queries.toString();
		return;
	}
	/**
	 * 与えられたエンコード済みクエリをデコードする
	 * 
	 * @param String URLエンコード済みクエリ
	 * @return String デコード済みクエリ
	 * @throws Exception 
	 */
	public HashMap<String,String> decodeQuery (String encodedQuery) throws Exception {
		String decodedQuery = "";
		HashMap<String,String> query = new HashMap<String,String>();

		try {
			decodedQuery = URLDecoder.decode(encodedQuery, "UTF-8");
		} catch (UnsupportedEncodingException e) {
			FWLog.error("URLデコードに失敗しました");
			throw e;
		}
		
		//文字列を分割 「&」で分割→「=」で分割
		String[] queries = decodedQuery.split("&");
		for (int i=0; i<queries.length; i++) {
			String[] elements = queries[i].split("=");
			if (elements.length>2) {
				throw new Exception("クエリ分割失敗(分割文字が複数) 文字列:"+queries[i]);
			} else if (elements.length<2) {
				throw new Exception("クエリ分割失敗(分割文字が無い) 文字列:"+queries[i]);
			}
			query.put(elements[0], elements[1]);
		}
		return query;
	}
	/**
	 * Webonに指定されたクエリで問い合わせを行う(非推奨)
	 *  
	 * @throws Exception 
	 */
	public void doQuery () throws Exception {

		//PDF取得との共通のため、どうするか？
		doQueryPdf();
		
		return;
	}
	/**
	 * Webonに指定されたクエリで問い合わせを行う
	 * パス輻輳によるタイムアウトが発生した場合はリトライを行う
	 *  
	 * @throws Exception 
	 */
	public void doQueryPdf () throws Exception {
		
		for (int i=1;i<RETRY_MAX_ROOT;i++){		//無限ループ回避用
		
			//制限数分リトライチェック
			if (RETRY_MAX_TIMEOUTERR!=0 && i>RETRY_MAX_TIMEOUTERR) {
				//リトライオーバーのエラー処理
				StringBuilder sb = new StringBuilder();
				sb.append("輻輳により、Webonへの問い合わせが完了しませんでした。");
				sb.append(" 接続先：").append(serverAddress);
				sb.append(" 取引店舗コード：").append(passBrno);
				sb.append(" リトライ回数：").append(i-1);
				throw new Exception(sb.toString());
			}
			//結果判定 輻輳エラーが出手いなければループを抜ける
			//輻輳エラーの場合はリトライ続行

			//問い合わせ本体
			doQueryExecute();
			
			if (!checkFukusoErr()) {
				break;
			}
			//５秒SLEEP
			retrySleep(RETRY_INTERVAL_TIMEOUTERR);
		
		}
		return;
	}
	/**
	 * Webonに指定されたクエリで問い合わせを行う(XML、PDF兼用)
	 *  
	 * @throws IOException 
	 * @throws Exception 
	 */
	public void doQueryExecute () throws Exception {

		//コネクションを独自に取得
		InitialContext ic = new InitialContext();
		Connection con=getConnection(ic, CommonConst.JDBC_ORACLE_SP2NM);

		//コネクションを独自に取得しているので、エラー処理も独自に行う
		try{
			
			//WEBONサーバのパスが使用可能かどうかを取得する
			for (int i=1;i<RETRY_MAX_ROOT;i++){		//無限ループ回避用
				if (getWebonPath(serverAddress,con)) {
					//パスが取得できたらループを抜ける
					break;
				}
				
				//リトライチェック
				if (RETRY_MAX_PATHGET!=0 && i>RETRY_MAX_PATHGET) {
					//リトライオーバーのエラー処理
					StringBuilder sb = new StringBuilder();
					sb.append("WEBONサーバへの接続パスが取得できませんでした。");
					sb.append(" 接続先：").append(serverAddress);
					sb.append(" 取引店舗コード：").append(passBrno);
					sb.append(" リトライ回数：").append(i-1);
					throw new Exception(sb.toString());
				}
				//５秒SLEEP
				retrySleep(RETRY_INTERVAL_PATHGET);
			}
			
			//WEBONパス取得後のエラー処理
			//エラー発生時は必ずパスを開放する
			try {
			
				//クエリのエンコードを実施
				encodeQuery();
				
				URL url = new URL(serverUrl + encodedQueries);
				//HTTPコネクションを実施
				HttpURLConnection httpCon = (HttpURLConnection)url.openConnection();
				httpCon.setRequestMethod("GET");
				httpCon.setInstanceFollowRedirects(false);
				httpCon.setRequestProperty("Accept-Language", "ja");
				FWLog.info(getClass(), "Webon問合せ："+ serverUrl + encodedQueries);
				httpCon.connect();
				
				//ヘッダ情報の取得
				headers = httpCon.getHeaderFields(); 
				FWLog.info(getClass(), "結果Content-type："+getContentType());
				//結果のInputStreamを取得
				stream = new BufferedInputStream(httpCon.getInputStream());
				
				//結果がXMLだったら、解析する
				if (getContentType().startsWith("application/xml")) {
					analyzeXml();
					XmlFlag=true;
				} else {
					XmlFlag=false;
				}
	
			}catch (Exception e){
				throw e;
			} finally {
				//パス管理を開放する
				releasWebonPath(serverAddress,con);
			}
			//パス管理取得後のエラー処理ここまで
		
		} catch (Exception e) {
			try {
				if (con != null) con.rollback();
			} catch (SQLException e1) {
				FWLog.error(e1);
			}
			throw e;
		} finally {
			try {
				if (con != null) con.close();
				con = null;
			} catch (SQLException e1) {
				FWLog.error(e1);
			}
		}
		//コネクション取得後のエラー処理ここまで
		
	}
	/**
	 * Webonに指定されたクエリで問い合わせを行う
	 *  
	 * @return CustomerInfoBean 検索結果
	 * @throws IOException 
	 * @throws ParserConfigurationException 
	 * @throws SAXException 
	 */
	public void analyzeXml() throws IOException, ParserConfigurationException, SAXException {

		//ドキュメントの生成
		DocumentBuilder builder = null;
		try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            builder = factory.newDocumentBuilder();
        } catch (ParserConfigurationException e) {
            throw e;
        }
        Document document = null;
        try {
            document = builder.parse( stream );
        } catch (SAXException e) {
            throw e;
        } 
        Node root=document.getDocumentElement();
        Node child = root.getFirstChild();
        //子ノードのノード名により、それぞれメンバに振分
        while (true) {
        	//取得できなかったら終わり
        	if (child==null){break;}
       	if (child.getNodeName().equals("出力データ")) {
        		outputData=child;
        	} else if (child.getNodeName().equals("編集データ")) {
        		editData=child;
        	} else if (child.getNodeName().equals("結果識別")) {
        		resultId=child;
        	} else if (child.getNodeName().equals("メッセージ")) {
        		message=child;
        	} else if (child.getNodeName().equals("オペコード")) {
        		opeCode=child;
        	} else if (child.getNodeName().equals("取引名")) {
        		tradeName=child;
        	} else if (child.getNodeName().equals("上りデータ")) {
        		uplinkData=child;
        	}
        	//次の子ノードを取得
        	child = child.getNextSibling();
        }
		
		return;
	}
	/**
	 * クエリの雛形を作成する
	 * 
	 * @param String オペレーションＩＤ
	 * @param LoginInfoBean ログイン情報
	 * @param Connection DBコネクション
	 * @throws Exception 
	 */
	public void setQuery(String oid, LoginInfoBean loginInfo, Connection con)	throws Exception{
			//オペレーションIDを設定
			operationId = oid;
			
		try{
			//NAVI.ＵＭ機能マスタから開発機か本番機かの判定用フラグを取得
			SelectFunctionMasterBase baseSelectFunctionMaster = new SelectFunctionMasterBase(con);
			baseSelectFunctionMaster.selectValueByFunctionIdAndKey("NAVICOMMON","本番切替フラグ");
			List<Map<String,String>> lsFunctionMaster = CastUtil.genelicToStringList2(baseSelectFunctionMaster.getList());
			
			Map<String,String> mapFunctionMaster = lsFunctionMaster.get(0);
			String modeFlg = mapFunctionMaster.get("値");
			
			//所属店番
			String branchNo = CommonConverter.getAdd0String(loginInfo.get所属店番(),3);
			
			//ユーザの所属店番をキーに、稼動店舗マスタＤＢからサーバのＩＰアドレスと取引店舗コードを取得する。
			SelectOperationBranchMstBase base = new SelectOperationBranchMstBase(con);
			base.selectByBrno(branchNo);
			List<Map<String, String>>list = CastUtil.genelicToStringList2(base.getList());
			
			//取引店舗コードとサーバのアドレスを取得
//			String passBrno = "";
//			String serverAddress="";
			StringBuilder sbUrl = new StringBuilder();
			if(0<list.size()){
				Map<String, String>map=list.get(0);
				//取引店舗コード
				passBrno=map.get("取引店舗コード");
				//WEBONサーバーＩＰアドレス
				serverAddress=map.get("接続先");
				
				//開発機か本番機かの判定用フラグを元にスケルトンの有無を判定する。
				if(modeFlg.equals("1")){
					//開発機
					//FWLog.debug(getClass(),"★☆★新規開発モード");
					//FWLog.debug(getClass(),"webon－URL:"+sbUrl.append(serverUrlHead).append(serverAddress).append(serverUrlTailSkelton).toString());
					//sbUrl=new StringBuilder();
					sbUrl.append(serverUrlHead).append(serverAddress).append(serverUrlTailSkelton);
					serverUrl=sbUrl.toString();
				}else{
					//本番機
					//FWLog.debug(getClass(),"☆★☆新規本番モード");
					//FWLog.debug(getClass(),"webon－URL:"+sbUrl.append(serverUrlHead).append(serverAddress).append(serverUrlTail).toString());
					//sbUrl=new StringBuilder();
					sbUrl.append(serverUrlHead).append(serverAddress).append(serverUrlTail);
					serverUrl=sbUrl.toString();
				}
			}else{
				StringBuilder sb = new StringBuilder();
				sb.append("ログインしているユーザの所属店番は、稼動店舗マスタＤＢに登録されていません。");
				sb.append(" 所属店番：").append(branchNo);
				String msg = sb.toString();
				FWLog.error(getClass(), msg);
				throw new Exception(msg);
			}
			
			//設定系ＯＰ本番ＵＲＬ変換（一部勘定連動しない設定系ＯＰについては開発機の場合、スケルトンをはずす）
			//統一名寄せ情報照会、諸届証跡照会、残高証明書作成照会、定期解約試算照会、証書貸付返済予定表作成照会
			if(modeFlg.equals("1")){
				if (oid.equals("OP-UNAYOSEJ-0001") || oid.equals("OP-UNAYOSEJ-0002") || oid.equals("OP-UNAYOSEJ-0003") || oid.equals("OP-UNAYOSEJ-0004")
						|| oid.equals("OP-SYOTODOPDF-01") || oid.equals("OP-ZANDAKA-0001") || oid.equals("OP-TEIKIKAI-0001") || oid.equals("OP-SHGASIHE-0001")) {
					StringBuilder sbUrl2 = new StringBuilder();
					sbUrl2.append(serverUrlHead).append(serverAddress).append(serverUrlTail);
					serverUrl=sbUrl2.toString();
					FWLog.info(getClass(), "＊＊＊＊＊統一顧客照会、諸届証跡照会のため、ServerUrlを書き換えます＊＊＊＊＊");
					FWLog.info(getClass(), "(試験)書き換え後のURL："+serverUrl);
				}
			}
			
			//オンラインＯＰマスタＤＢから、オペレーションＩＤをキーに必要項目を取得
			SelectOnlineOperationMastBase base1 = new SelectOnlineOperationMastBase(con);
			base1.selectByOperationId(operationId);
			ArrayList<HashMap<String, String>> list1 = new ArrayList<HashMap<String,String>>();
			list1 = CastUtil.genelicToStringList(base1.getList());
			
			//件数チェック
			if (list1.size()<1){
				StringBuilder sb = new StringBuilder();
				sb.append("該当するオペレーションＩＤがありません。");
				sb.append(" オペレーションＩＤ：").append(operationId);
				String msg = sb.toString();
				FWLog.error(getClass(), msg);
				throw new Exception(msg);
			}
			
			//1件目をクエリ（マップ）の結果として取得
			query = list1.get(0);
			//不要項目を削除
			query.remove("オペレーションＩＤ");
			query.remove("コメント");
			
			//職員コードを取得
			String staffCode = loginInfo.get職員番号();
			query.put("職員コード", staffCode);

			//取引店舗を取得
			//=====================================本番用=========================================//
			query.put("取引店舗コード", passBrno);
			//====================================================================================//
			
			//====================================試験用==========================================//
			//query.put("取引店舗コード", FixedValue.WEBON_BRNO);				//試験用固定値
			//====================================================================================//
			
		} catch (Exception e) {
			FWLog.error(getClass(), "クエリ作成に失敗しました。");
			throw e;
		}
		
		return;
	}
	/**
	 * クエリに項目を追加する
	 * 
	 * @param String 項目名
	 * @param String 項目にセットする内容
	 * @throws Exception 設定できないキー項目が指定された場合
	 */
	public void put(String key, String value) throws Exception{
		//クエリに項目を追加
		query.put(key, value);
		//FWLog.debug(getClass(),"★★★WEBON項目値設定　キー："+key+" 値："+value);

		//原店番号チェック
		//原店番号が、取引店舗コードと同一だった場合は、原店番号を設定しない
		if (key.equals("原店番号")){
			if (query.get("原店番号").equals(query.get("取引店舗コード"))) {
				FWLog.debug(getClass(), "原店番号=取引店舗コードのため、原店番号の設定をはずします。");
				query.put("原店番号","");
			}
		}
		
	}
	/**
	 * クエリの項目を参照する
	 * 
	 * @param String 項目名
	 * @return String クエリにセットされている内容、未設定の場合Null
	 */
	public String get(String key) {
		if (query.containsKey(key)) {
			return query.get(key);
		} else {
			return null;
		}
	}
	/**
	 * クエリに項目を追加する
	 * 
	 * @param HashMap<String,String> 項目名と内容のセット
	 * @throws Exception 設定できないキー項目が指定された場合
	 */
	public void put(HashMap<String,String> map) throws Exception{
		String key;
		String value;
		Set<String> ks = map.keySet();
		for (Iterator<String> ksIt = ks.iterator(); ksIt.hasNext();) {
			key=ksIt.next();
			value=map.get(key);
			this.put(key,value);
		}
	}
	/**
	 * 取得結果を返却する
	 *  
	 * @return HashMap<String, String> Webonへの問い合わせ結果
	 */
	public HashMap<String, String> getResult() {
		return result;
	}
	/**
	 * クエリ雛形設定済みインスタンスを生成する
	 * 
	 * @param String オペレーションＩＤ
	 * @param LLoginInfoBean ログイン情報
	 * @param Connection DBコネクション
	 * @return WebonBase 生成したインスタンス
	 * @throws Exception 
	 */
	public static WebonBase getInstance(String operationId, LoginInfoBean loginInfo, Connection con)	throws Exception{
		WebonBase wob = new WebonBase(operationId, loginInfo, con);
		return wob;
	}
	/**
	 * 結果取得用ゲッタ
	 * 
	 * @return Node XML解析結果
	 */
	public Node getOutputData() {
		return outputData;
	}
	public Node getEditData() {
		return editData;
	}
	public Node getResultId() {
		return resultId;
	}
	public Node getMessage() {
		return message;
	}
	public Node getOpeCode() {
		return opeCode;
	}
	public Node getTradeName() {
		return tradeName;
	}
	public Node getUplinkData() {
		return uplinkData;
	}
	/**
	 * 結果の成否
	 * 
	 * @return boolean XML取得結果
	 */
	public boolean checkResult() {
		boolean res=false;
		if (resultId!=null){
			if (resultId.getFirstChild().getNodeValue().equals("正常")){
				res=true;
			}
		}
		return res;
	}
	/**
	 * 結果の取得
	 * @return String 結果のString
	 */
	public String getStringResult(){
		return getChildText(resultId);
	}
	/**
	 * WEBONメッセージ項目をStringで取得
	 * 
	 * @return String エラーメッセージ(正常値)
	 * 
	 */
	public String getErrMessage(){
		String result=null;
		String code=null;
		String detail=null;
		//結果識別解析
		result=getChildText(resultId);
        //メッセージ解析
//        Node child = message.getFirstChild();
//        //子ノードのノード名により、それぞれメンバに振分
//        while (true) {
//        	//取得できなかったら終わり
//        	if (child==null){break;}
//        	if (child.getNodeName().equals("コード")) {
//        		code=getChildText(child);
//        		if (code==null) { code="";}
//        	} else if (child.getNodeName().equals("詳細")) {
//        		detail=getChildText(child);
//        		if (detail==null) { detail="";}
//        	}
//        	//次の子ノードを取得
//        	child = child.getNextSibling();
//        }
		//それぞれ個別メソッド化(2014.01.06)
		code=getErrCode();
		detail=getErrDetail();
        
		StringBuilder sb = new StringBuilder();
		sb.append(" 結果識別：").append(result);
		sb.append(" コード：").append(code);
		sb.append(" 詳細：").append(detail);
		
		return sb.toString();
	}
	/**
	 * WEBONエラーコードを取得
	 * 
	 * @return String エラーメッセージ詳細
	 */
	public String getErrCode(){
		String code=null;
        //メッセージ解析
        Node child = message.getFirstChild();
        //子ノードのノード名により、それぞれメンバに振分
        while (true) {
        	//取得できなかったら終わり
        	if (child==null){break;}
           	if (child.getNodeName().equals("コード")) {
        		code=getChildText(child);
        		if (code==null) { code="";}
         	}
        	//次の子ノードを取得
        	child = child.getNextSibling();
        }
		return code;
	}
	/**
	 * WEBONエラーの詳細を取得
	 * 
	 * @return String エラーメッセージ詳細
	 */
	public String getErrDetail(){
		String detail=null;
        //メッセージ解析
        Node child = message.getFirstChild();
        //子ノードのノード名により、それぞれメンバに振分
        while (true) {
        	//取得できなかったら終わり
        	if (child==null){break;}
        	if (child.getNodeName().equals("詳細")) {
        		detail=getChildText(child);
        		if (detail==null) { detail="";}
        	}
        	//次の子ノードを取得
        	child = child.getNextSibling();
        }
		return detail;
	}
	/**
	 * ＰＤＦ結果の取得
	 * 
	 * @return BufferedInputStream ＰＤＦ等取得結果
	 */
	public BufferedInputStream getStream() {
		return stream;
	}
	/**
	 * ヘッダー情報の取得
	 * 
	 * @return Map<String, List<String>> ＰＤＦ等取得結果
	 */
	public Map<String, List<String>> getHeaders() {
		return headers;
	}
	/**
	 * Content-type(ヘッダー情報)の取得
	 * 
	 * @return Map<String, List<String>> ＰＤＦ等取得結果
	 */
	public String getContentType() {
		return headers.get("Content-Type").get(0);
	}

	/**
	 * Nodeの直下にあるテキストエレメントのVALUEを取得する
	 * 
	 * @param Node 親ノード
	 * @return String VALUE値
	 */
	public static String getChildText(Node elem) {
		String textValue="";
		Node child =elem.getFirstChild();
        while (true) {
        	//取得できてなかったら終わり
        	if (child==null){break;}
	     	if (child.getNodeType()==Node.TEXT_NODE){
        		textValue=child.getNodeValue();
        		break;
        	}
        	//次の子ノードを取得
        	child = child.getNextSibling();
        }
		return textValue;
	}
	/**
	 * 未編集のXMLデータをStringWriterとして取得
	 * @return StringWriter 未編集XMLをテキスト変換したソース
	 */
    public StringWriter getSourceWriter() throws TransformerException {
        Node srcNode = outputData;
        
        StringWriter writer = new StringWriter();
        
        Transformer transformer = TransformerFactory.newInstance().newTransformer();
        transformer.transform(new DOMSource(srcNode), new StreamResult(writer));
        
        //FWLog.info(getClass(),writer.toString() );
        return writer;
    }
	/**
	 * サーバパス管理ＤＢから、接続可能かどうかを判定・パスの取得を行う
	 * @param String 接続先WEBONサーバＩＰアドレス
	 * @return boolean パスの取得結果
	 * @throws Exception 
	 */
    private boolean getWebonPath(String ip,Connection con) throws Exception {
    	
    	boolean result = false;	//パスの取得成功
    	
    	//パス管理マスタから、該当店舗の最大パス数を取得する
		SelectPathMngMstBase base1 = new SelectPathMngMstBase(con);
		base1.selectPathMax(ip);
		List<Map<String, String>>list1 = CastUtil.genelicToStringList2(base1.getList());
   	
    	if (list1.size()!=1) {
			StringBuilder sb = new StringBuilder();
			sb.append("データベース レコード数異常");
			sb.append(" ＤＢ名：").append(SelectPathMngMstBase.DBNAME);
			sb.append(" 接続先：").append(ip);
			sb.append(" レコード数：").append(list1.size());
			throw new SQLException(sb.toString());
    	}
    	
    	Map<String,String> map1 = list1.get(0);
    	int pathMax = Integer.parseInt(map1.get(SelectPathMngMstBase.DBKEY_PATHMAX));
    	int pathMaxLim = Integer.parseInt(map1.get(SelectPathMngMstBase.DBKEY_LIMPATHMAX));
    	
    	//パス管理ステータスからロックを取得し、現在の使用パス数を取得する
    	//トランザクション開始（ここからロック取得する）
    	con.setAutoCommit(false);	//自動コミットOFF
    	
		SelectPathMngStatBase sbase = new SelectPathMngStatBase(con);
		InsertPathMngStatBase ibase = new InsertPathMngStatBase(con);
		UpdatePathMngStatBase ubase = new UpdatePathMngStatBase(con);
		try {  	
			//ステータスＤＢのレコード存在チェック
			//データが存在しない場合は挿入する
			boolean check = sbase.checkPathNo(ip);
			if (!check) {
				try {
					ibase.insertPathNo(ip);
				} catch(SQLException e) {
					//既に挿入されていた場合はそのまま次へ
					int errCode = e.getErrorCode();
					if (errCode==1) {
						StringBuilder sb = new StringBuilder();
						sb.append("既にレコードが挿入されています。");
						sb.append(" ＤＢ名：").append(InsertPathMngStatBase.DBNAME);
						sb.append(" 接続先：").append(ip);
						sb.append(" ORACLEエラーコード：").append(errCode);
						FWLog.warn(getClass(), sb.toString());
					} else {
						throw (e);
					}
				}
			}
			//パス数取得（ForUpdate）
			try {
				sbase.selectPathNoForUp(ip);
			} catch (SQLException e) {
				int errCode = e.getErrorCode();
				if (errCode==1) {
					StringBuilder sb = new StringBuilder();
					sb.append("データベースがビジー状態です。");
					sb.append(" ＤＢ名：").append(InsertPathMngStatBase.DBNAME);
					sb.append(" 接続先：").append(ip);
					sb.append(" ORACLEエラーコード：").append(errCode);
					FWLog.error(getClass(), sb.toString());
					throw (e);
				} else {
					throw (e);
				}
			}
			//結果取得
			List<HashMap<String, String>> list2 = CastUtil.genelicToStringList(sbase.getList());
	    	if (list2.size()!=1) {
				StringBuilder sb = new StringBuilder();
				sb.append("データベース レコード数異常");
				sb.append(" ＤＢ名：").append(InsertPathMngStatBase.DBNAME);
				sb.append(" 接続先：").append(ip);
				sb.append(" レコード数：").append(list2.size());
				throw new SQLException(sb.toString());
	    	}
	    	//現在のパス数取得
	    	Map<String,String> map2 = list2.get(0);
	    	int pathNum = Integer.parseInt(map2.get(SelectPathMngStatBase.DBKEY_PATHNUM));
	    	int pathNumLim = Integer.parseInt(map2.get(SelectPathMngStatBase.DBKEY_LIMPATHNUM));
			
			//パスの取得成否確認
	    	if (pathNum<pathMax) {
	    		//パス取得成功なら、パス数をインクリメントしてＤＢ反映
	    		pathNum++;
	    		
	    		//バックグラウンドの場合は更に制限パスの取得も行う
	    		if (BackGroundFlag) {
	    			if (pathNumLim<pathMaxLim){
	    				pathNumLim++;
			    		//ＤＢ反映
			    		ubase.updatePathNo(ip, pathNum,pathNumLim);
			    		result=true;	//パス取得成功
	    			}
	    		} else {
		    		//ＤＢ反映
		    		ubase.updatePathNo(ip, pathNum);
	    			//メイン処理の場合は、そのままパス取得成功
		    		result=true;	//パス取得成功
	    		}
	    		
	    	}
			//コミット（ロック開放）
			con.commit();

			//ログ出力(INFOレベル)
			StringBuilder sb=new StringBuilder();
			if (result) {
				sb.append("WEBONパス取得成功 WEBONサーバアドレス：").append(ip);
				sb.append(" パス数：").append(pathNum).append("/").append(pathMax);
				sb.append(" 制限パス数：").append(pathNumLim).append("/").append(pathMaxLim);
				sb.append(" BackGroundFlag：").append(BackGroundFlag);
			} else {
				sb.append("WEBONパス取得失敗 WEBONサーバアドレス：").append(ip);
				sb.append(" パス数：").append(pathNum).append("/").append(pathMax);
				sb.append(" 制限パス数：").append(pathNumLim).append("/").append(pathMaxLim);
				sb.append(" BackGroundFlag：").append(BackGroundFlag);
			}
			FWLog.info(getClass(),sb.toString());
    	
		} catch (Exception e) {
			try {
				if (con != null) con.rollback();
			} catch (SQLException e1) {
				FWLog.error(e1);
			}
			throw e;
		} finally {
			try {
				if (con != null) {
					con.setAutoCommit(true);
				}
				con = null;
			} catch (SQLException e1) {
				FWLog.error(e1);
			}
		}
    	
    	return result;
    }
	/**
	 * サーバパス管理ＤＢのパスを開放する
	 * @param String 接続先WEBONサーバＩＰアドレス
	 * @return boolean パスの開放結果
	 * @throws Exception 
	 */
    private boolean releasWebonPath(String ip,Connection con) throws Exception {
    	
    	boolean result=false;
    	
    	//パス管理ステータスからロックを取得し、現在の使用パス数を取得する
    	//トランザクション開始（ここからロック取得する）
    	con.setAutoCommit(false);	//自動コミットOFF
    	
		SelectPathMngStatBase sbase = new SelectPathMngStatBase(con);
		UpdatePathMngStatBase ubase = new UpdatePathMngStatBase(con);
		try {  	
			//パス数取得（ForUpdate）
			try {
				sbase.selectPathNoForUp(ip);
			} catch (SQLException e) {
				int errCode = e.getErrorCode();
				if (errCode==1) {
					StringBuilder sb = new StringBuilder();
					sb.append("データベースがビジー状態です。");
					sb.append(" ＤＢ名：").append(InsertPathMngStatBase.DBNAME);
					sb.append(" 接続先：").append(ip);
					sb.append(" ORACLEエラーコード：").append(errCode);
					FWLog.error(getClass(), sb.toString());
					throw (e);
				} else {
					throw (e);
				}
			}
			//結果取得
			List<HashMap<String, String>> list2 = CastUtil.genelicToStringList(sbase.getList());
	    	if (list2.size()!=1) {
				StringBuilder sb = new StringBuilder();
				sb.append("データベース レコード数異常");
				sb.append(" ＤＢ名：").append(InsertPathMngStatBase.DBNAME);
				sb.append(" 接続先：").append(ip);
				sb.append(" レコード数：").append(list2.size());
				throw new SQLException(sb.toString());
	    	}
	    	//現在のパス数取得
	    	Map<String,String> map2 = list2.get(0);
	    	int pathNum = Integer.parseInt(map2.get(InsertPathMngStatBase.DBKEY_PATHNUM));
	    	int pathNumLim = Integer.parseInt(map2.get(InsertPathMngStatBase.DBKEY_LIMPATHNUM));
			
    		//パス取得成功なら、パス数をインクリメントしてＤＢ反映
    		pathNum--;
    		
    		//バックグラウンドだったら、制限パス数もデクリメント
    		if (BackGroundFlag){
    			//バックグラウンド時の処理
    			pathNumLim--;
        		//ＤＢ反映
        		ubase.updatePathNo(ip, pathNum,pathNumLim);
        		result=true;	//パス取得成功
    		} {
    			//主処理の時の処理
        		//ＤＢ反映
        		ubase.updatePathNo(ip, pathNum);
        		result=true;	//パス取得成功
    		}
    		
			//コミット（ロック開放）
			con.commit();
    	
			//成功ログ出力(INFOレベル)
			StringBuilder sb=new StringBuilder();
			sb.append("WEBONパス解放 WEBONサーバアドレス：").append(ip);
			sb.append(" パス数：").append(pathNum);
			sb.append(" 制限パス数：").append(pathNumLim);
			sb.append(" BackGroundFlag：").append(BackGroundFlag);
			FWLog.info(getClass(),sb.toString());
    	
		} catch (Exception e) {
			try {
				if (con != null) con.rollback();
			} catch (SQLException e1) {
				FWLog.error(e1);
			}
			throw e;
		} finally {
			try {
				if (con != null) {
					con.setAutoCommit(true);
				}
				con = null;
			} catch (SQLException e1) {
				FWLog.error(e1);
			}
		}
    	
    	return result;
    }
    /**
	 * 与えられた秒数(msec)分SLEEPする
	 * @param long SLEEPする時間（msec）
	 */
    private static void retrySleep(long msec) {
		try{
			Thread.sleep(msec);
		}catch(InterruptedException e){}
		return;
    }
	/**
	 * コネクションの取得
	 * 
	 * @param ic		InitialContext
	 * @param strDS	ＪＤＢＣ名
	 * @return
	 * @throws NamingException
	 * @throws SQLException
	 */
	protected Connection getConnection(InitialContext ic, String strDS)
		throws NamingException, SQLException {

		return CommonUtil.getConnection(ic, strDS);
	}
	/**
	 * 輻輳タイムアウト(MWON50)によるエラーチェック
	 *  
	 * @return boolean チェック結果(true:輻輳エラーあり、false:輻輳エラーなし) 
	 */
	private boolean checkFukusoErr(){
		
		//結果がXMLであった場合のみチェック
		if (XmlFlag) {
			//Webonの取得成功している場合はFalse復帰
			if (checkResult()){
				FWLog.debug("★★★輻輳チェック　Webon取得成功");
				return false;
			}
			//エラーコードMWON50は輻輳エラー
			if (getErrCode().equals("MWON50")){
				FWLog.debug("★★★輻輳チェック　輻輳エラー！！！");
				return true;
			}
		}
		
		return false;
	}
}
