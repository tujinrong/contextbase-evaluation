package common.util;

import java.io.BufferedOutputStream;
import java.io.ByteArrayOutputStream;
import java.util.Vector;

import javax.servlet.http.HttpServletResponse;

public class CSVUtil {

	/**
	* Vector(［行数］[列数])を明細データとしてＣＳＶを作成する
	*
	* @param	res				HttpServletResponse
	* @param	fixedData		タイトル部格納配列　<不要な場合は、nullをセット>
	* @param	variableData	可変フィールド格納Vector(［行数］[列数])
	*
	* @return なし
	* 
	* @date	H22.9.6		青木・浅見		センター集約対応なし
	*/

	public void writeCsv(HttpServletResponse res,String[] fixedData,Vector variableData) 
      	throws Exception {


		StringBuffer sb = new StringBuffer ( 1024 ); 

		//固定フィールド有無チェック
		//NECIKO if ( fixedData==null || fixedData[0]==""){
		if ( fixedData==null || fixedData[0].equals("")){
		} 
		else {
			// 項目名をセット
			for (int i = 0; i < fixedData.length; i++) {
				sb.append( "\"" + new String(fixedData[i].getBytes(), "Windows-31J") + "\"," );
			}
			//タイトル行の最後の","を"\r"に置換
			sb.replace(sb.length() - 1,sb.length(), "\r" );
		}


		//selectされたレコード数だけ繰り返す
		for(int i = 0 ; i < variableData.size(); i++){
			//selectされた１レコード分の項目がvecに格納されている
			Vector vec= (Vector)variableData.get(i);
			
			for(int ii = 0 ; ii < vec.size(); ii++){

				sb.append( "\"" + new String(vec.get(ii).toString().getBytes(), "Windows-31J") + "\"," );
			
			}
			//各明細行の最後の","を"\r"に置換
			sb.replace(sb.length() - 1,sb.length(), "\r" );
			
		}

		String fileName= CommonUtil.getCurrentDate("HHmmss") + ".csv";
		res.setContentType("application/octet-dummy-stream");
		res.setHeader("Content-Disposition", "attachment; filename=" + fileName);

	    try {
			//バイト配列出力ストリームを新しく作成します
			ByteArrayOutputStream baos = new ByteArrayOutputStream();

			byte[] data = sb.toString().getBytes();
			if(data != null) {
				baos.write(data);
			}	
			//出力ストリームのバッファリング 
			BufferedOutputStream bout = new BufferedOutputStream(res.getOutputStream());
				
			//バイト配列出力ストリームのすべての内容を、指定された出力ストリーム引数に書き込みます
			baos.writeTo(bout);

			baos.close();
			bout.close();

		} catch(Exception e){
			throw e;
			//throw new CifApplicationException("9001-02ＣＳＶ作成エラー　" +  e.getMessage());
		}
	}

}
