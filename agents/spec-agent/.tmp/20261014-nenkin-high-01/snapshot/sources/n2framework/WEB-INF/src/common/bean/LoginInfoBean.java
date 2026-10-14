/*
 * 作成日: 2009/02/13
 *
 */
package common.bean;

import java.io.Serializable;

/**
 * フレームワーク<BR>
 * ログイン情報Beanクラス
 *
 * @author JSC kengo murayama
 * 
 * @date	H22.9.3		青木・浅見		センター集約対応なし
 * 			H23.12.21	Minori米持		事務ナビ対応
 * 			H25.9.19	Minori米持		性別コード取得対応
 * 			H26.6.30	Minori吉津		職員カナ氏名取得対応
 * 			H26.7.18	Minori吉津		システム事務統括部職員判定対応
 * 			H28.4.1 	Minori山口		一元化対応
 * 			R04.07.15 	Minori山口		所属コードの追加
 */
public class LoginInfoBean implements Serializable {

	/** ログイン可否 */
	private boolean ログイン可否 = false;

	/** アプリケーション名 */
	private String アプリケーション名 = null;
	
	/** 遷移元アプリケーション名 */
	private String 遷移元アプリケーション名 = null;

	/** 職員番号 */
	private String 職員番号 = null;

	/** 性別コード */
	private String 性別コード = null;

	/** 職員氏名 */
	private String 職員氏名 = null;
	
	/** 職員カナ氏名 */
	private String 職員カナ氏名 = null;
	
	/** 所属店番 */
	private String 所属店番 = null;

	/** 詳細部室店コード */
	private String 詳細部室店コード = null;

	/** 詳細部室店枝番 */
	private String 詳細部室店枝番 = null;

	/** 所属店名 */
	private String 所属店名 = null;

	/** 役職コード */
	private String 役職コード = null;

	/** 役職名 */
	private String 役職名 = null;

	/** 融資系ユーザーＩＤ */
	private String 融資系ユーザーＩＤ = null;

	/** 融資系ユーザー名 */
	private String 融資系ユーザー名 = null;

	/** 所属課係コード */
	private String 所属課係コード = null;
	
	/** 所属コード */
	private String 所属コード = null;

	/** 所属課係名 */
	private String 所属課係名 = null;

	/** 債権書類権限 */
	private int 債権書類権限 = 0;

	/** 決算書権限 */
	private int 決算書権限 = 0;

	/** ＣＲＤ権限 */
	private int ＣＲＤ権限 = 0;

	/** 格付権限 */
	private int 格付権限 = 0;

	/** 自己査定権限 */
	private int 自己査定権限 = 0;
	
	/** ＵＮＩＦＹフラグ */
	private String ＵＮＩＦＹフラグ = null;
	
	/** システム事務統括部職員 */
	private boolean システム事務統括部職員 = false;

	public String getアプリケーション名() {
		return アプリケーション名;
	}

	public void setアプリケーション名(String アプリケーション名) {
		this.アプリケーション名 = アプリケーション名;
	}

	public String get遷移元アプリケーション名() {
		return 遷移元アプリケーション名;
	}

	public void set遷移元アプリケーション名(String 遷移元アプリケーション名) {
		this.遷移元アプリケーション名 = 遷移元アプリケーション名;
	}

	public boolean isログイン可否() {
		return ログイン可否;
	}

	public void setログイン可否(boolean ログイン可否) {
		this.ログイン可否 = ログイン可否;
	}

	public int get格付権限() {
		return 格付権限;
	}

	public void set格付権限(int 格付権限) {
		this.格付権限 = 格付権限;
	}

	public int get決算書権限() {
		return 決算書権限;
	}

	public void set決算書権限(int 決算書権限) {
		this.決算書権限 = 決算書権限;
	}

	public int get債権書類権限() {
		return 債権書類権限;
	}

	public void set債権書類権限(int 債権書類権限) {
		this.債権書類権限 = 債権書類権限;
	}

	public int get自己査定権限() {
		return 自己査定権限;
	}

	public void set自己査定権限(int 自己査定権限) {
		this.自己査定権限 = 自己査定権限;
	}

	public String get所属課係コード() {
		return 所属課係コード;
	}

	public void set所属課係コード(String 所属課係コード) {
		this.所属課係コード = 所属課係コード;
	}
	
	public String get所属コード() {
		return 所属コード;
	}

	public void set所属コード(String 所属コード) {
		this.所属コード = 所属コード;
	}

	public String get所属課係名() {
		return 所属課係名;
	}

	public void set所属課係名(String 所属課係名) {
		this.所属課係名 = 所属課係名;
	}

	public String get所属店番() {
		return 所属店番;
	}

	public void set所属店番(String 所属店番) {
		this.所属店番 = 所属店番;
	}

	public String get所属店名() {
		return 所属店名;
	}

	public void set所属店名(String 所属店名) {
		this.所属店名 = 所属店名;
	}

	public String get詳細部室店コード() {
		return 詳細部室店コード;
	}

	public void set詳細部室店コード(String 詳細部室店コード) {
		this.詳細部室店コード = 詳細部室店コード;
	}

	public String get詳細部室店枝番() {
		return 詳細部室店枝番;
	}

	public void set詳細部室店枝番(String 詳細部室店枝番) {
		this.詳細部室店枝番 = 詳細部室店枝番;
	}

	public String get職員氏名() {
		return 職員氏名;
	}

	public void set職員氏名(String 職員氏名) {
		this.職員氏名 = 職員氏名;
	}

	public String get職員カナ氏名() {
		return 職員カナ氏名;
	}

	public void set職員カナ氏名(String 職員カナ氏名) {
		this.職員カナ氏名 = 職員カナ氏名;
	}

	public String get職員番号() {
		return 職員番号;
	}

	public void set職員番号(String 職員番号) {
		this.職員番号 = 職員番号;
	}

	public String get役職コード() {
		return 役職コード;
	}

	public void set役職コード(String 役職コード) {
		this.役職コード = 役職コード;
	}

	public String get役職名() {
		return 役職名;
	}

	public void set役職名(String 役職名) {
		this.役職名 = 役職名;
	}

	public String get融資系ユーザー名() {
		return 融資系ユーザー名;
	}

	public void set融資系ユーザー名(String 融資系ユーザー名) {
		this.融資系ユーザー名 = 融資系ユーザー名;
	}

	public String get融資系ユーザーＩＤ() {
		return 融資系ユーザーＩＤ;
	}

	public void set融資系ユーザーＩＤ(String 融資系ユーザーｉｄ) {
		融資系ユーザーＩＤ = 融資系ユーザーｉｄ;
	}

	public int getＣＲＤ権限() {
		return ＣＲＤ権限;
	}

	public void setＣＲＤ権限(int ｄ権限) {
		ＣＲＤ権限 = ｄ権限;
	}

	public String get性別コード() {
		return 性別コード;
	}

	public void set性別コード(String 性別コード) {
		this.性別コード = 性別コード;
	}

	public boolean isシステム事務統括部職員() {
		return システム事務統括部職員;
	}

	public void setシステム事務統括部職員(boolean システム事務統括部職員) {
		this.システム事務統括部職員 = システム事務統括部職員;
	}

	public String getＵＮＩＦＹフラグ() {
		return ＵＮＩＦＹフラグ;
	}

	public void setＵＮＩＦＹフラグ(String ｕＮＩＦＹフラグ) {
		ＵＮＩＦＹフラグ = ｕＮＩＦＹフラグ;
	}
	
}