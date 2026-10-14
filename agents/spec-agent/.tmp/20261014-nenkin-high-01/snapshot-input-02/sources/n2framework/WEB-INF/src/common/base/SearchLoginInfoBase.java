/*
 * 作成日: 2009/02/17
 *
 */
package common.base;


import java.sql.Connection;
import java.sql.SQLException;

import common.base.CommonBaseSelect;

/**
 * フレームワーク　ログイン情報検索Baseクラス
 * 
 * @author JSC kengo murayama
 * 
 * @date	H22.9.6		青木・浅見		センター集約対応
 */
public class SearchLoginInfoBase extends CommonBaseSelect {

	/**
	 * コンストラクタ
	 * 
	 * @param connection
	 */
	public SearchLoginInfoBase(Connection connection) {
		super(connection);
	}

	/**
	 * ＵＷＥＢログイン情報表のＰＫ検索を実行する
	 * 
	 * @param applName
	 * @param userId
	 * @param password
	 * @return
	 * @throws SQLException
	 */
	public boolean selectＷＥＢログイン情報表(String applName, String userId, String password) throws SQLException {

		try {

			StringBuffer sb = new StringBuffer();

			sb.append("select *");
			sb.append(" from DB2.ＵＷＥＢログイン情報表");
			sb.append(" where アプリケーション名 = '").append(applName).append("'");
			sb.append(" and ユーザーＩＤ = '").append(userId).append("'");
			sb.append(" and パスワード = '").append(password).append("'");

			execute(sb.toString());

		} catch (SQLException e) {
			throw e;
		}

		if (getList() != null) {
			return true;
		} else{
			return false;
		}
	}

	
	/**
	 * ＵＷＥＢログイン情報表のＰＫ検索を実行する
	 * 
	 * @param applName
	 * @param userId
	 * @param password
	 * @return
	 * @throws SQLException
	 */
	public boolean selectＷＥＢログイン情報表(String applName, String userId) throws SQLException {

		try {

			StringBuffer sb = new StringBuffer();

			sb.append("select *");
			sb.append(" from DB2.ＵＷＥＢログイン情報表");
			sb.append(" where アプリケーション名 = '").append(applName).append("'");
			sb.append(" and ユーザーＩＤ = '").append(userId).append("'");

			execute(sb.toString());

		} catch (SQLException e) {
			throw e;
		}

		if (getList() != null) {
			return true;
		} else{
			return false;
		}
	}	
	
	
	/**
	 * Ｕ職員名簿表のＰＫ検索を実行する
	 * 
	 * @param shokuinNo
	 * @return
	 * @throws SQLException
	 */
	public boolean select職員名簿表(String shokuinNo) throws SQLException {

		try {

			StringBuffer sb = new StringBuffer();

			sb.append("select *");
			sb.append(" from DB2.Ｕ職員名簿表");
			sb.append(" where 職員番号 = ").append(shokuinNo);

			execute(sb.toString());

		} catch (SQLException e) {
			throw e;
		}

		if (getList() != null) {
			return true;
		} else{
			return false;
		}
	}

	/**
	 * Ｕ職員所属課係一覧表のＰＫ検索を実行する
	 * 
	 * @param shokuinNo
	 * @return
	 * @throws SQLException
	 */
	public boolean select職員所属課係一覧表(String shokuinNo) throws SQLException {

		try {

			StringBuffer sb = new StringBuffer();

			sb.append("select *");
			sb.append(" from DB2.Ｕ職員所属課係一覧表");
			sb.append(" where 職員番号 = ").append(shokuinNo);

			execute(sb.toString());

		} catch (SQLException e) {
			throw e;
		}

		if (getList() != null) {
			return true;
		} else{
			return false;
		}
	}

	/**
	 * SELECT文を実行する
	 * 
	 * @param yakusyokucode
	 * @return
	 * @throws SQLException
	 */
	public boolean select役職コード表(String yakusyokucode) throws SQLException{
		try{
			//ＵＪＶ役職コード表
			StringBuffer sb = new StringBuffer();

			sb.append("SELECT");
			sb.append(" 役職");
			sb.append(" FROM DB2.ＵＪＶ役職コード表");
			sb.append(" WHERE 役職コード = ").append(yakusyokucode);

			execute(sb.toString());

		}catch (SQLException e){
			throw e;
		}

		if(getList() != null){
			return true;
		}else{
			return false;
		}
	}
}
