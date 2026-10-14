/*
 * 作成日: 2009/02/13
 *
 */
package common.bean;

import java.io.Serializable;

/**
 * フレームワーク<BR>
 * ＴＭ連携情報格納Beanクラス
 *
 * @author  H27.8.28	岩渕
 * 
 */
public class OtherUserBean implements Serializable {

	/** ユーザ */
	private String ユーザ = null;

	/** パスワード */
	private String パスワード = null;

	/** アプリケーション名*/
	private String アプリケーション名 = null;

	/** パッケージ名 */
	private String パッケージ名 = null;
	
	/** 画面ＩＤ */
	private String 画面ＩＤ = null;
	

	public String getユーザ() {
		return ユーザ;
	}

	public void setユーザ(String ユーザ) {
		this.ユーザ = ユーザ;
	}

	public String getパスワード() {
		return パスワード;
	}

	public void setパスワード(String パスワード) {
		this.パスワード = パスワード;
	}

	public String getアプリケーション名() {
		return アプリケーション名;
	}

	public void setアプリケーション名(String アプリケーション名) {
		this.アプリケーション名 = アプリケーション名;
	}

	public String getパッケージ名() {
		return パッケージ名;
	}

	public void setパッケージ名(String パッケージ名) {
		this.パッケージ名 = パッケージ名;
	}

	public String get画面ＩＤ() {
		return 画面ＩＤ;
	}

	public void set画面ＩＤ(String 画面ＩＤ) {
		this.画面ＩＤ = 画面ＩＤ;
	}
}