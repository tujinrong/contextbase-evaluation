package webon.operation;

import java.util.ArrayList;

import org.w3c.dom.Node;

import webon.WebonBase;
import webon.util.FixedValue;

/**
 * webonオペレーションクラスのスーパークラス。
 * 各種webon照会のオペレーションクラスは、必ずこのクラスを継承する。
 *
 * @author shinsuke Kyogoku
 *
 * @date	2020.02.13		京極		新規作成
 */
public abstract class CommonOperation {
	//webon情報
	protected WebonBase webonBase;
	
	//以下UTILITY
	//以下、ユーティリティ的メソッド
	/**
	 * Nodeの直下にあるテキストエレメントのVALUEを取得する
	 * 
	 * @param Node 親ノード
	 * @return String VALUE値
	 */
	protected String getChildText(Node elem) {
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
	 * 次のエレメントノードを取得する
	 * 
	 * @param Node
	 * @return Node
	 */
	protected Node getNextElement(Node elem){
		while (true) {
			elem=elem.getNextSibling();
			if (elem==null) {return elem;}
			if (elem.getNodeType()==Node.ELEMENT_NODE){
				return elem;
			}
		}
	}
	/**
	 * 次のエレメントノードを取得する(現ノード含む)
	 * 
	 * @param Node
	 * @return Node
	 */
	protected Node getNextElement2(Node elem){
		while (true) {
			if (elem==null) {return elem;}
			if (elem.getNodeType()==Node.ELEMENT_NODE){
				return elem;
			}
			elem=elem.getNextSibling();
		}
	}
	/**
	 * LINE行抽出メソッド
	 * （webon問合せ結果のXMLからLINE行を抽出し、リストに変換する）
	 * @param  WebonBase webon問合せ結果
	 * @retrun List
	 * 
	 * @throws Exception 
	 */
	public ArrayList<String> getLineByXML() throws Exception {
		final String WOKEY_TSUCYO="通帳部宛";
		final String WOKEY_LINE="LINE";
		ArrayList<String> lineList = new ArrayList<String>();
		
		//出力データの取得
		Node output = webonBase.getOutputData();

		//Line行の最上位ノードを取得する
		Node root=output.getFirstChild();
		for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
        	//取得できなかったら終わり
        	if (root==null){break;}
	    	if (root.getNodeType()==Node.ELEMENT_NODE) {
	    		//要素名の解析
	    		if (root.getNodeName().equals(WOKEY_TSUCYO)) {
	    			//rootの内容保持したままループをぬける
	    			break;
	    		}
	    	}
	    	//次のノード取得
	    	root = root.getNextSibling();
		}
		
		//Line行の取得
		Node line=root.getFirstChild();
		String lineString;
		//Line行を順次読み込んでいく
		for (int roopCount=0;roopCount<FixedValue.SYS_WBNUMLIMIT;roopCount++){
        	//取得できなかったら終わり
        	if (line==null){break;}
	    	if (line.getNodeType()==Node.ELEMENT_NODE) {
	    		//要素名の解析
	    		if (line.getNodeName().equals(WOKEY_LINE)) {
	    			//Line行なら、結果をリストに保管
	    			lineString=WebonBase.getChildText(line);
	    			if (lineString==null) {lineString="";}
	    			lineList.add(lineString);
	    		}
	    	}
	    	//次のノード取得
	    	line = line.getNextSibling();
		}
		
		//LINE行を格納したリストを返却
		return lineList;
	}
}
