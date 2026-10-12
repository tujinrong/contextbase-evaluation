package jhkcommon;

/**
  *
  * 店番・顧客番号から顧客基本表を検索して、結果をＰＤＦに変換する（テスト）
  *
  * @date	H22.8.19	青木・浅見		センター集約対応なし
  *
  */
  
import java.io.InputStream;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.util.List;
import java.util.Vector;

import javax.servlet.ServletOutputStream;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletResponse;

import com.canon.iw.fm.common.exception.FMPrintException;
import com.canon.iw.fm.common.exception.FMPropertyException;
import com.canon.iw.fm.common.message.FMRequest;
import com.canon.iw.fm.common.message.FMResponse;
import com.canon.iw.fm.common.message.FMResponseOperator;
import com.canon.iw.fm.server.FMComposerAgent;
import com.canon.iw.fm.server.FMJob;


/**
 * PdfFactory3
 *
 *
 * 修正履歴：2005/10/21 NEC Soft, Ltd.
 *   「FormCraft Pro. for Web」から「Form Manager V6.1」へのバージョンアップ
 *    にともない大幅変更。
 *     
 *     各種クラス名の変更、各種メソッドの仕様変更など、Form Manager
 *     のJavaAPIの仕様に合わせ、変更点多数。
 *
 *
 */
public class PdfFactory3 extends HttpServlet {

	/**
	* ResultSetからVector(［行数］[列数])を作成し返す
	*
	* @param  rs   データベースの検索結果（ResultSet型の変数名）
	* @param  
	*
	* @return Vector(［行数］[列数])
	  */
	public Vector makeVector(ResultSet rs) 
      	throws Exception{

       	Vector dataSource = new Vector();

		ResultSetMetaData meta = rs.getMetaData();

		// ResultSetの全データをVectorへ格納する
		while (rs.next()) {
	        Vector row = new Vector();
			for (int i=0; i < meta.getColumnCount(); i++) {
				if(rs.getString(i+1) == null){
					row.addElement("");
				}
				else {
					row.addElement(rs.getString(i+1));
				}
			}
			dataSource.addElement(row);
		}

		return dataSource;
	}

	/**
	* ResultSetからVector(［行数］[列数])を作成し返す
	*
	* @param  rs   データベースの検索結果（ResultSet型の変数名）
	* @param  errorCode 該当データ無い場合に、CifApplicationExceptionにわたすエラーコード
	*
	* @return Vector(［行数］[列数])
	  */
	public Vector makeVector(ResultSet rs,String errorCode) 
      	throws Exception{

       	Vector dataSource = new Vector();

		ResultSetMetaData meta = rs.getMetaData();

		//SELECTされたレコードの有無をチェック
		String selectDataUmu = "NASHI";

		// ResultSetの全データをVectorへ格納する
		while (rs.next()) {

			selectDataUmu = "ARI";

	        Vector row = new Vector();
			for (int i=0; i < meta.getColumnCount(); i++) {
				if(rs.getString(i+1) == null){
					row.addElement("");
				}
				else {
					row.addElement(rs.getString(i+1));
				}
			}
			dataSource.addElement(row);
		}

		if(selectDataUmu.equals("NASHI")){
			 throw new CifApplicationException(errorCode);
		}
		return dataSource;
	}


	/**
	 * フィールドデータの作成
	 */
	public byte[] makeFieldData(String[][] fixedData, List variableData) {

		final String SP = ",";		//データ項目区切り子
		final String QT = "\"";		//リテラル記法引用符
		byte[] fielddata = null;

		/*******************************************
		 * 制御セクション
		 *******************************************/
		StringBuffer sb = new StringBuffer();
		sb.append("[Control Section]\r\n");
		sb.append("VERSION=5.0\r\n");

		/*******************************************
		 * 固定セクション
		 *******************************************/
		if (fixedData==null || fixedData[0][0].equals("")) {
			//固定フィールド無し
		} else {
			//固定フィールドデータセット
			sb.append("[Fixed Data Section]\r\n");
			for(int i=0 ; i < fixedData.length ; i++){
				sb.append(fixedData[i][0] + "=" + QT + fixedData[i][1] + QT + "\r\n");
			}
		}

		/*******************************************
		 * 可変セクション
		 *******************************************/
		sb.append("[Body Data Section]\r\n");
		boolean isFirstRow = true;		//可変セクション内の先頭行かどうか
		boolean isFirstCol = true;		//明細行の先頭列かどうか
		// 行(明細)の数だけ繰り返す
		for (int row = 0; row < variableData.size(); row++) {
			isFirstCol = true;
			// 先頭行以外はまず改行出力
			if (!isFirstRow) sb.append("\r\n");
			isFirstRow = false;
			// １明細分データ取り出し
			List rowdata = (List)variableData.get(row);
			// 要素(列データ)の数だけ繰り返す
			for (int col = 0; col < rowdata.size(); col++) {
				// 列データ取り出し
				//  String dt = (String)rowdata.get(col);
				//  要素がBigDecimalだとClassCastExceptionが発生した為、toString()に変更
				//  かつ、データに￥を含む場合の対処追加
				String dt = rowdata.get(col).toString().replaceAll("\\\\","\\\\\\\\");
				// 先頭データ以外はセパレータ付与
				if (!isFirstCol) sb.append(SP);
				// データ出力
				sb.append(QT + dt + QT);
				isFirstCol = false;
			}
		}

		// デフォルト文字セットにてバイト配列に変換
		fielddata = sb.toString().getBytes();
		return fielddata;
	}


	/**
	* Vector(［行数］[列数])を印字データとしてＰＤＦを作成する
	*
	* @param	res		HttpServletResponse
	* @param	fixedData	固定フィールド格納配列　<不要な場合は、nullをセット>
	* @param	variableData	可変フィールド格納Vector(［行数］[列数])
	* @param	formatFileName	フォーム名
    *
	* @return なし
	*/
	public void writePdf(HttpServletResponse res, String[][] fixedData, Vector variableData, String formatFileName)
                throws Exception {

		// ブラウザに返すデータ形式を指定  
		res.setContentType("application/pdf");

		FMComposerAgent agent = null;
		FMJob job = null;
		FMRequest request = null;

		InputStream stream = null;
		ServletOutputStream out = null;

		try{

			// フィールドデータの作成
			byte[] testdata = makeFieldData(fixedData, variableData);

//			String s = new String(testdata.toString());
//			int ii = testdata.length;

			// エージェント作成
			FMComposerAgent.setRootDirectory("C:\\iWFM");
			//NECIKO FcwJobControl agent = new FcwJobControl (null, null, null);
			agent = new FMComposerAgent(null, null, null);

			// ジョブオブジェクト作成
			job = agent.newJob();
			request = job.getRequest();

			// フォームファイル名の設定
			//NECIKO request.setFormFileName(formatFileName);
			request.put("fm-formfilename", formatFileName);

			// フィールドデータの設定
			//NECIKO request.setFieldData(testdata);
			request.put("fm-fielddata", testdata);

			// 出力先の設定
			//NECIKO request.setDestination(FcwPrintAttribute.DESTINATION_CLIENT);
			request.put("fm-target", "client");

			// 出力方式の設定
			request.put("fm-action", "view");

			// データ形式の設定
			request.put("fm-outputtype", "pdf");
			
			/**テスト用（c:\\iWFM\\storeへＰＤＦファイルを出力する）*************
			request.put("fm-target", "server");
			request.put("fm-action", "print");	
			File testFile = new File("c:\\iWFM\\store",currentTime+".pdf");
			request.put("fm-outfile", testFile);
			*******************************************************************/


			// 非同期式
			FMResponse response = null;
			try {
				job.asynOverlay();
			} catch (FMPropertyException e) {
				//設定属性に問題あり
				//通常、この例外は発生しない。
				throw new CifApplicationException("9001-02設定属性エラー");
			} catch (FMPrintException e) {
				//実行系の問題発生（複数スレッドが呼び出した等）
				//getMessage()はエラーメッセージを返す。
				String errorMessage = e.getMessage();
				//getRuntimeErrorCode()はランタイムでエラーが発生した時、
				//そのステータスコードを返す。"－１"もしくは"０"の場合は
				//ランタイムエラーではない。
				int runtimeCode = e.getRuntimeErrorCode();

				throw new CifApplicationException("9001-02実行系問題発生" + errorMessage + "," + Integer.toString(runtimeCode));
			}

			// ジョブの終了待ち
			int status = job.getStatus();
			for (int i = 0; i < 20; i++) {
				if (status == 0 || status == 1000008 || status == 1000019) {
					// 正常終了、異常終了、キャンセル完了の場合
					response = job.getResponse();
					break;
				}
				Thread.sleep(1000);
				status = job.getStatus();
			}

			// レスポンスのステータス確認
			String errorMessage = null;
			if (status == 0){
				if (response != null) {
					if ( ((Integer)response.get("fm-status")).intValue() == 0) {
						// オーバレイ成功
						//NECIKO stream = response.getInputStream();
						FMResponseOperator operator = job.getResponseOperator();
						stream = operator.getInputStream();
					} else {
						//NECIKO errorMessage = response.getMessage();
						errorMessage = (String)response.get("fm-message");
					}
				} else {
					errorMessage = "利用できるコンポーサがありません。";
				}
			} else {
				//ジョブが中断された
				errorMessage = "ジョブが中断された。";
			}

			//ジョブが未完了な状態。
			if(response == null) {
				switch (job.getStatus()) {
				//NECIKO case FcwStatus.OK:
				case 0:
					//ありえないエラー。
					errorMessage = errorMessage + "　ありえないエラー。"; 
					break;
				//NECIKO case FcwStatus.STATUS_CONFIGURING:
				case 1000002:
					//準備中／設定中
					errorMessage = errorMessage + "　まだオーバーレイメソッドが呼ばれていない。";
					break;
				//NECIKO case FcwStatus.STATUS_BUSY:
				case 1000004:
					//処理中
					errorMessage = errorMessage + "　まだオーバーレイが完了していない。しばらくお待ちください。";
					break;
				case 1000018:
					//キャンセル中
					errorMessage = errorMessage + "　キャンセル中です。しばらくお待ちください。";
					break;
				//NECIKO case FcwStatus.STATUS_INTERRUPTED:
				case 1000019:
					//ジョブは明示的に中断された。
					errorMessage = errorMessage + "　ジョブは明示的に中断された。";
					break;
				default:
					//異常終了
					errorMessage = errorMessage + "　ジョブは異常終了しました。";
					break;
				}
			}

			if(errorMessage != null)throw new CifApplicationException("9001-02" + errorMessage);

		} catch (Exception e) {
			throw new CifApplicationException("9001-02ＰＤＦ作成エラー　" +  e.getMessage());
		}

		//ストリームによるＰＤＦ出力
		out = res.getOutputStream();
		byte[] buf = new byte[2048];
		int nread=0;
		int len = 0;

		while ((nread = stream.read(buf)) != -1) {
			len =len + nread;
			out.write(buf, 0, nread);
		}
		out.flush();

		
		// 後始末
		job.clear();
		agent.removeJob(job);
	}

}
