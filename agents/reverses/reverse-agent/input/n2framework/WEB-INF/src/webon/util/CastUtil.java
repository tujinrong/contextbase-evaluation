package webon.util;

import java.sql.SQLException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * webon汎用照会　キャストユーティリティ
 * 
 * @author Minori 京極
 * 
 * @date	2020.02.13		京極		新規作成
 */
public class CastUtil {
	/** 
	  * DBから取得したList<?>をArrayList<HashMap<String, String>>)の形式にCastする
	  * @param	List<?> DBから取得したlist
	  * @return ArrayList<HashMap<String, String>> Cast変換後の戻り値
	  * @throws SQLException
	  */
	public static ArrayList<HashMap<String, String>> genelicToStringList (List<?> list) {
		ArrayList<HashMap<String,String>> resultList=new ArrayList<HashMap<String,String>>();
		for (int i=0; i<list.size(); i++) {
			HashMap<String,String> resultMap = new HashMap<String,String>();
			resultMap=genelicToStringMap((Map<?,?>)list.get(i));
			resultList.add(resultMap);
		}
		return resultList;
	}
	public static HashMap<String, String> genelicToStringMap (Map<?,?> map) {
		HashMap<String,String> resultMap = new HashMap<String,String>();
		Set<?> keys=map.keySet();
		for (Iterator<?> it = keys.iterator(); it.hasNext();) {
			String key = (String)it.next();
			String value = (String)map.get(key);
			resultMap.put(key, value);
		}
		return resultMap;
	}
	/** 
	  * DBから取得したList<?>をList<Map<String, String>>)の形式にCastする
	  * @param	List<?> DBから取得したlist
	  * @return List<Map<String, String>> Cast変換後の戻り値
	  * @throws SQLException
	  */
	public static List<Map<String, String>> genelicToStringList2 (List<?> list) {
		List<Map<String,String>> resultList=new ArrayList<Map<String,String>>();
		for (int i=0; i<list.size(); i++) {
			Map<String,String> resultMap = new HashMap<String,String>();
			resultMap=genelicToStringMap2((Map<?,?>)list.get(i));
			resultList.add(resultMap);
		}
		return resultList;
	}
	public static Map<String, String> genelicToStringMap2 (Map<?,?> map) {
		Map<String,String> resultMap = new HashMap<String,String>();
		Set<?> keys=map.keySet();
		for (Iterator<?> it = keys.iterator(); it.hasNext();) {
			String key = (String)it.next();
			String value = (String)map.get(key);
			resultMap.put(key, value);
		}
		return resultMap;
	}

}
