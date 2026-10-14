/*
 * 作成日: 2009/07/13
 *
 */
package common.bean;

import java.io.Serializable;

/**
 * フレームワーク<BR>
 * サブウィンドウ表示Beanクラス
 *
 * @author JSC kengo murayama
 * 
 * @date	H22.9.6		青木・浅見		センター集約対応なし
 */
public abstract class SubWindowBean implements Serializable {

	/** ＪＳＰ名 */
	private String ＪＳＰ名 = null;

	/** サブウィンドウ横幅 */
	private int 横幅 = 0;

	/** サブウィンドウ高さ */
	private int 高さ = 0;


	/**
	 * @return 横幅 を戻します。
	 */
	public int get横幅() {
		return 横幅;
	}

	/**
	 * @param 横幅 設定する 横幅。
	 */
	public void set横幅(int 横幅) {
		this.横幅 = 横幅;
	}

	/**
	 * @return 高さ を戻します。
	 */
	public int get高さ() {
		return 高さ;
	}

	/**
	 * @param 高さ 設定する 高さ。
	 */
	public void set高さ(int 高さ) {
		this.高さ = 高さ;
	}

	/**
	 * @return ｊＳＰ名 を戻します。
	 */
	public String getＪＳＰ名() {
		return ＪＳＰ名;
	}

	/**
	 * @param ｐ名 設定する ｊＳＰ名。
	 */
	public void setＪＳＰ名(String ｐ名) {
		ＪＳＰ名 = ｐ名;
	}

}
