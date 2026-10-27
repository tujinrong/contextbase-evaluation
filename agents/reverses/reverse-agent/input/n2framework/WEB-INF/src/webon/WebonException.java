package webon;

import java.util.List;
import java.util.Map;

/**
 * Webon汎用照会　Webon汎用照会用エクセプションクラス
 * webon照会結果のエラー情報を管理する
 * 
 * @author Minori 加瀬
 * 
 * @date	H24.11.01			新規作成
 * @date 	R02.02.06	京極		webonのFW化対応
 */
public class WebonException extends Exception {
	
	private static final long serialVersionUID = 1L;
	
	//コンストラクタ
	public WebonException (String msg)
	{
		super(msg);
	}
	public WebonException (String msg,WebonBase wob) {
		super(msg);
		setWebonBase(wob);
		setResult(webonBase.getStringResult());
		setErrcode(webonBase.getErrCode());
		setErrdetail(webonBase.getErrDetail());
	}
	//フィールド
	//webon情報
	private WebonBase webonBase;
	private String operationId;
	private String errcode;			//エラーコード
	private String errdetail;		//詳細
	private String result;			//結果表示
	//顧客情報
	private String cif;
	private String brno;
	private String subcode;
	private String accno;
	//エラーステータス(0:Error、1:Warning)
	private int errStat;
	//エラー箇所(0:取得、1:解析、2:成型)
	private String errSpot;
	//追加情報　個々にエラー項目を足していく
	private List<Map<String, String>> etc;
	
	//getter,setter
	public WebonBase getWebonBase() {
		return webonBase;
	}
	public void setWebonBase(WebonBase webonBase) {
		this.webonBase = webonBase;
	}
	public String getOperationId() {
		return operationId;
	}
	public void setOperationId(String operationId) {
		this.operationId = operationId;
	}
	public String getErrcode() {
		return errcode;
	}
	public void setErrcode(String errcode) {
		this.errcode = errcode;
	}
	public String getErrdetail() {
		return errdetail;
	}
	public void setErrdetail(String errdetail) {
		this.errdetail = errdetail;
	}
	public String getResult() {
		return result;
	}
	public void setResult(String result) {
		this.result = result;
	}
	public String getCif() {
		return cif;
	}
	public void setCif(String cif) {
		this.cif = cif;
	}
	public String getBrno() {
		return brno;
	}
	public void setBrno(String brno) {
		this.brno = brno;
	}
	public String getSubcode() {
		return subcode;
	}
	public void setSubcode(String subcode) {
		this.subcode = subcode;
	}
	public String getAccno() {
		return accno;
	}
	public void setAccno(String accno) {
		this.accno = accno;
	}
	public List<Map<String, String>> getEtc() {
		return etc;
	}
	public void setEtc(List<Map<String, String>> etc) {
		this.etc = etc;
	}
	public int getErrStat() {
		return errStat;
	}
	public void setErrStat(int errStat) {
		this.errStat = errStat;
	}
	public String getErrSpot() {
		return errSpot;
	}
	public void setErrSpot(String errSpot) {
		this.errSpot = errSpot;
	}
}
