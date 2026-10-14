/*
 * 作成日: 2007/05/14
 *
 */
package common;

import java.sql.Connection;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import javax.naming.InitialContext;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import common.base.SearchLoginInfoBase;
import common.base.SelectJigyosyoCodeHyo2Base;
import common.bean.LoginInfoBean;
import common.bean.OtherUserBean;
import common.util.CommonConverter;

/**
 * フレームワーク　ログイン処理アクションクラス
 *
 * @author JSC kengo murayama
 * 
 * @date	H22.9.6		青木・浅見		センター集約対応
 * 			H23.12.21	Minori米持		事務ナビ対応
 * 			H25.9.19	Minori米持		所属課係コードの取得を共通に
 * 										性別コード取得対応
 * 			H26.6.30	Minori吉津		職員カナ氏名取得対応
 * 			H26.7.18	Minori吉津		システム事務統括部職員判定対応
 * 			H27.8.28	岩渕			ＴＭ連携対応
 * 			H28.04.02	Minori山口		アプリ超え対応（cif ⇔ unify）
 * 			H29.05.15	Minori山口		当庫ＷＥＢシステムに代行登録の機能追加について
 *  		H29.09.26	Minori山口		unifyアプリ追加
 *   		H30.04.05	Minori山口		【稟議支援】融資情報システムとの連携
 *  		R02.06.03	Minori山口		店舗グループ統合対応
 *  		R02.09.30	佐原			n2bat対応
 *  		R02.10.01	Minori山口		Unify対応
 *  		R06.11.11	Minori山口		窓口支援／渉外支援システム連携対応  
 */

public class LoginAction extends CommonAction {

	/**
	 * アクション実行メソッド
	 * 
	 * @param req リクエスト
	 * @param res レスポンス
	 * @return ＪＳＰ名
	 */
	public String perform(HttpServletRequest req, HttpServletResponse res) throws Exception {

		//変数の初期化
		String dwhUserId ="";
		String dwhPassWord ="";
		String creditUserId ="";
		String creditPassWord ="";
		String applName ="";
		String OTHER_USER_ID ="";
		String OTHER_PASS_WORD ="";
		String unify_flg = "";

		//認証前提準備
		String sUser = null;
		String sPass = null;
		
		//一元化識別の取得
		String o_apl  = req.getParameter("Otheflg");
		String tm_opk = req.getParameter("OPK");
		
		//渉外支援からの識別をget
		String charCommonuid = req.getParameter("charCommonUID");
		
		//セッションの取得
		HttpSession session = req.getSession();	
		OtherUserBean OtherUserInfo = (OtherUserBean)session.getAttribute(CommonConst.SS_OTHER_INFO_BEAN);
		
		//ログイン情報Beanをセッションにセット
		LoginInfoBean loginInfo = new LoginInfoBean();

		if(tm_opk!=null || o_apl!=null || charCommonuid != null){
			
			//稟議支援からの場合
			if("ringi".equals(o_apl)){
				
				dwhUserId = req.getParameter("DWH_USER_ID");
				dwhPassWord =req.getParameter("DWH_PASS_WORD");
				applName = req.getParameter("APPL_NAME");
				
			//一元化系ユーザーはこっち
			}else{				
				
				OTHER_USER_ID = OtherUserInfo.getユーザ();
				OTHER_PASS_WORD = OtherUserInfo.getパスワード();
				applName = OtherUserInfo.getアプリケーション名();
			
			}
			
			
			
			if(charCommonuid != null){

				String wk_CustNr =req.getParameter("intCustNr");
				String wk_Br = req.getParameter("intBr");

				if((wk_CustNr == null && wk_Br == null) || (wk_CustNr.isEmpty() && wk_Br.isEmpty())){
					
					unify_flg = "1";
				}else{
					
					unify_flg = "2";
				}
				
				loginInfo.setＵＮＩＦＹフラグ(unify_flg);
			}
			
			
		} else {
		//情報系ユーザーは職員番号
			dwhUserId =req.getParameter("DWH_USER_ID");
			dwhPassWord =req.getParameter("DWH_PASS_WORD");
			creditUserId =req.getParameter("CREDIT_USER_ID");
			creditPassWord =req.getParameter("CREDIT_PASS_WORD");
			applName =req.getParameter("APPL_NAME");

			//０：城北ＭＣＲシステムメニュー画面
			//１：顧客情報一元化システムメニュー画面
			//２：顧客情報一元化システム（ＨＴ）メニュー画面
			unify_flg = req.getParameter("UNIFY_FLG"); 
		}

		boolean loginStatus = false;
		List lsMessage = new ArrayList();
		List lsWebLogin = null;
		List lsSyokuinMeibo = null;
		//HttpSession session = req.getSession();


		if ("dwh".equals(applName)) {
			sUser = applName;
			sPass = dwhPassWord;
		} else if ("credit".equals(applName)) {
			sUser = creditUserId;
			sPass = creditPassWord;
		} else if ("navi".equals(applName)) {
			sUser = applName;
			sPass = dwhPassWord;
		} else if ("bat".equals(applName)) {
			sUser = dwhUserId;
			sPass = dwhPassWord;
		} else if ("unify".equals(applName) || "cif".equals(applName)){
						
			//顧客情報一元化からの場合
			if(tm_opk!=null || o_apl!=null || charCommonuid != null){
				
				dwhUserId = OTHER_USER_ID;
				sUser = applName;
				sPass = OTHER_PASS_WORD;
			
			//unifyからログインした場合
			}else{
				sUser = applName;
				sPass = dwhPassWord;				
			}
		}else if ("ringi".equals(applName)) {
				sUser = applName;
				sPass = dwhPassWord;	
			
		}

		//認証処理
		if ((sUser==null) || (sUser.equals("")) || (sPass==null) || (sPass.equals(""))){
			loginStatus = false ;
			lsMessage.add("ユーザ名・パスワードを入力してください。");
		}else if((applName==null) || (applName.equals("")) || (dwhUserId==null) || (dwhUserId.equals(""))){
			loginStatus = false ;
			lsMessage.add("ログインに失敗しました。");
		} else {
			//ＤＢ検索
			Connection con = null;

			try {
				//DB接続
				con = getConnection(new InitialContext(), CommonConst.JDBC_ORACLE_SP2NM);
				
				
				if ("ringi".equals(applName)) {
					
					if(!"".equals(dwhUserId) || dwhUserId != null){
						
						try {
							SearchLoginInfoBase base = new SearchLoginInfoBase(con);
							//職員番号が数値以外の場合（数値変換に失敗した場合）はＵ職員名簿表を取得させない
							Long.parseLong(dwhUserId);
	
							//ログインＯＫの場合、Ｕ職員名簿表を取得
							base.select職員名簿表(dwhUserId);
							lsSyokuinMeibo = base.getList();
							
						} catch (NumberFormatException e2) {
							lsSyokuinMeibo = null;
						}					
					}
										
					loginStatus = true ;
					loginInfo.set債権書類権限(50);
					
				}else{

					//ＷＥＢログイン状況表検索データ取得
					SearchLoginInfoBase base = new SearchLoginInfoBase(con);
					base.selectＷＥＢログイン情報表(applName,sUser,sPass);
					lsWebLogin = base.getList();
	
					//検索結果が０件の場合、ログインＮＧ
					if(lsWebLogin == null || lsWebLogin.isEmpty()){
						loginStatus = false ;
						lsMessage.add("ログインに失敗しました。ユーザ名・パスワードを確認してください。");
					} else {
						try {
							
							//n2batはログインＯＫであれば、専用のユーザ情報を作成し、メニュー画面へ遷移する
							if("bat".equals(applName)){
								loginInfo.setログイン可否(true);
								loginInfo.setアプリケーション名("bat");
								loginInfo.set遷移元アプリケーション名("");
								loginInfo.set職員番号("00000000");
								loginInfo.set性別コード("");
								loginInfo.set職員氏名("バッチ専用ユーザ");
								loginInfo.set職員カナ氏名("");
								loginInfo.set所属店番("010");
								loginInfo.set詳細部室店コード("00");
								loginInfo.set詳細部室店枝番("65");
								loginInfo.set所属店名("システム部");
								
								session.setAttribute(CommonConst.SS_LOGIN_INFO_BEAN, loginInfo);
								
								return "./JSP/MENU/Menu.jsp";
							}
							
							//職員番号が数値以外の場合（数値変換に失敗した場合）はＵ職員名簿表を取得させない
							Long.parseLong(dwhUserId);
	
							//ログインＯＫの場合、Ｕ職員名簿表を取得
							base.select職員名簿表(dwhUserId);
							lsSyokuinMeibo = base.getList();
							
						} catch (NumberFormatException e2) {
							lsSyokuinMeibo = null;
						}
	
						loginStatus = true ;
					}
				
				}
			} catch (Exception e) {
				throw e;
			} finally {
				try {
					if (con != null) con.close();
					con = null;
				} catch (SQLException e1) {
					FWLog.error(e1);
				}
			}
		}

		loginInfo.setログイン可否(loginStatus);
		loginInfo.setアプリケーション名(applName);
		if((dwhUserId==null) || (dwhUserId.equals(""))){
			loginInfo.set職員番号("00000000");
		}else{
			loginInfo.set職員番号(CommonConverter.getAdd0String(dwhUserId,8));
		}

		//ログインＯＫの場合、その他のユーザー情報をログイン情報Beanにセットしてメニュー画面に遷移
		if(loginStatus){

			//アプリケーション共通の情報をセット
			String syozokuTenban = null;
			String syosaiBushitsuCode = null;
			String syosaiBushitsuEdaban = null;
			String yakusyokuCode = null;
			String yakusyoku = null;
			
			
			//他アプリ連携用データをセット
			String from_applName = req.getParameter("FROM_APPL_NAME");
			if(null != from_applName &&  "" != from_applName){
				loginInfo.set遷移元アプリケーション名(from_applName);
			}

			//職員名簿表データをセット
			if(lsSyokuinMeibo != null && !lsSyokuinMeibo.isEmpty()){
				Map mapSyokuinMeibo = (Map)lsSyokuinMeibo.get(0);
				//先頭０埋め４桁揃えが必要。
				syozokuTenban = CommonConverter.getAdd0String((String)mapSyokuinMeibo.get("所属店番"),4);
				syosaiBushitsuCode = syozokuTenban.substring(0,2);
				syosaiBushitsuEdaban = syozokuTenban.substring(2,4);
				if (Integer.parseInt(syozokuTenban) < 100) {
					loginInfo.set所属店番("010");
				} else {
					loginInfo.set所属店番(syozokuTenban.substring(0,3));
				}
				loginInfo.set詳細部室店コード(syosaiBushitsuCode);
				loginInfo.set詳細部室店枝番(syosaiBushitsuEdaban);
				loginInfo.set職員氏名((String)mapSyokuinMeibo.get("漢字氏名"));
				loginInfo.set職員カナ氏名((String)mapSyokuinMeibo.get("カナ氏名"));
				loginInfo.set性別コード((String)mapSyokuinMeibo.get("性別"));
				yakusyokuCode = (String)mapSyokuinMeibo.get("役職コード");
				if(Integer.parseInt(syozokuTenban)==65 || Integer.parseInt(syozokuTenban)==70){
					loginInfo.setシステム事務統括部職員(true);
				}else{
					loginInfo.setシステム事務統括部職員(false);
				}
			} else {
				loginInfo.set所属店番("999");
				loginInfo.set詳細部室店コード("99");
				loginInfo.set詳細部室店枝番("99");
				loginInfo.set職員氏名(dwhUserId);
				loginInfo.set性別コード("0");
				yakusyokuCode = "0";
				loginInfo.setシステム事務統括部職員(false);
			}
			loginInfo.set役職コード(yakusyokuCode);

			//所属店番が取得できた場合のみ所属店名をN2_DWHに取りに行く
			if(syozokuTenban != null && !"".equals(syozokuTenban)){
				//ＤＢ検索
				Connection con = null;

				try {
					//DB接続
					con = getConnection(new InitialContext(), CommonConst.JDBC_ORACLE_DWH);

					//Ｊ事業所コード表２検索データ取得
					SelectJigyosyoCodeHyo2Base base = new SelectJigyosyoCodeHyo2Base(con);
					base.select(syosaiBushitsuCode,syosaiBushitsuEdaban);
					List lsJigyoCode2 = base.getList();

					//検索結果がある場合、事業所名をセット。０件の場合、「該当なし」。
					if(lsJigyoCode2 != null && !lsJigyoCode2.isEmpty()){
						Map mapJigyoCode2 = (Map)lsJigyoCode2.get(0);
						loginInfo.set所属店名((String)mapJigyoCode2.get("事業所名"));
					} else {
						loginInfo.set所属店名("該当なし");
					}
				} catch (Exception e) {
					throw e;
				} finally {
					try {
						if (con != null) con.close();
						con = null;
					} catch (SQLException e1) {
						FWLog.error(e1);
					}
				}
			} else {
				loginInfo.set所属店名("該当なし");
			}

			//役職名・所属課係コード・所属課係名の取得
			List lsYakusyokuCode = null;
			List lsSyokuinSyozoku = null;
			
			//ＤＢ検索
			Connection con = null;

			try {
				//DB接続
				con = getConnection(new InitialContext(), CommonConst.JDBC_ORACLE_SP2NM);

				//Ｕ職員所属課係一覧表・ＵＪＶ役職コード表を取得
				SearchLoginInfoBase base = new SearchLoginInfoBase(con);

				//役職コードが取得できた場合のみ役職名を取りに行く
				if(yakusyokuCode != null && !"".equals(yakusyokuCode) && !"0".equals(yakusyokuCode)){

					//ＵＪＶ役職コード表データ取得
					base.select役職コード表(yakusyokuCode);
					lsYakusyokuCode = base.getList();
										
					//検索結果がある場合、融資系ユーザー名をセット。０件の場合、「該当なし」
					if(lsYakusyokuCode != null && !lsYakusyokuCode.isEmpty()){
						Map mapyakusyokucode = (Map)lsYakusyokuCode.get(0);
						loginInfo.set役職名((String)mapyakusyokucode.get("役職"));
						yakusyoku = (String)mapyakusyokucode.get("役職");
					}else{
						loginInfo.set役職名("該当なし");
						yakusyoku = "該当なし";
					}
				}else{
					loginInfo.set役職名("該当なし");
					yakusyoku = "該当なし";
				}

				try {
					//職員番号が数値以外の場合（数値変換に失敗した場合）はＵ職員名簿表を取得させない
					Long.parseLong(dwhUserId);

					//ログインＯＫの場合、Ｕ職員所属課係一覧表を取得
					base.select職員所属課係一覧表(dwhUserId);
					lsSyokuinSyozoku = base.getList();
					
				} catch (NumberFormatException e2) {
					lsSyokuinSyozoku = null;
				}

				if(lsSyokuinSyozoku != null && !lsSyokuinSyozoku.isEmpty()){
					Map mapSyokuinSyozoku = (Map)lsSyokuinSyozoku.get(0);

					String code = (String)mapSyokuinSyozoku.get("所属課係コード");
					loginInfo.set所属課係コード(code);

					if (CommonConverter.convertInt(code) == 10){
						loginInfo.set所属課係名("店長席");
					} else if (CommonConverter.convertInt(code) == 100){
						loginInfo.set所属課係名("融資Ｍ・リレーションＧ");
					} else if (CommonConverter.convertInt(code) == 600){
						loginInfo.set所属課係名("事務グループ");
					}else {
						loginInfo.set所属課係名("その他");
					}							
				} else {
					loginInfo.set所属課係コード("0");
					loginInfo.set所属課係名("");
				}
			} catch (Exception e) {
				throw e;
			} finally {
				try {
					if (con != null) con.close();
					con = null;
				} catch (SQLException e1) {
					FWLog.error(e1);
				}
			}

			//アプリケーションＩＤごとの情報をセット
			if("credit".equals(applName)){
				Map mapWebLogin = (Map)lsWebLogin.get(0);
				loginInfo.set融資系ユーザーＩＤ(creditUserId);
				loginInfo.set融資系ユーザー名((String)mapWebLogin.get("融資系ユーザー名"));
				loginInfo.set所属店番(CommonConverter.getAdd0String((String)mapWebLogin.get("融資系所属店番"),3));

				loginInfo.set債権書類権限(CommonConverter.convertInt((String)mapWebLogin.get("債権書類権限")));
				loginInfo.set決算書権限(CommonConverter.convertInt((String)mapWebLogin.get("決算書権限")));
				loginInfo.setＣＲＤ権限(CommonConverter.convertInt((String)mapWebLogin.get("ＣＲＤ権限")));
				loginInfo.set格付権限(CommonConverter.convertInt((String)mapWebLogin.get("格付権限")));
				loginInfo.set自己査定権限(CommonConverter.convertInt((String)mapWebLogin.get("自己査定権限")));

			} else if("cif".equals(applName)){
				//情報系の場合の所属店番制御
				loginInfo.set融資系ユーザーＩＤ(null);
				loginInfo.set融資系ユーザー名(yakusyoku);


			} else if("ringi".equals(applName)){
				//情報系の場合の所属店番制御
				loginInfo.set融資系ユーザーＩＤ(null);
				loginInfo.set融資系ユーザー名(yakusyoku);
				loginInfo.set債権書類権限(50);
			
			} else {
				//情報系の場合の所属店番制御
				loginInfo.set融資系ユーザーＩＤ(null);
				loginInfo.set融資系ユーザー名(yakusyoku);
			//	loginInfo.set融資系格付権限(null);
			}

			session.setAttribute(CommonConst.SS_LOGIN_INFO_BEAN, loginInfo);						
			
			if("credit".equals(applName)){

				return new ViewDaikoAction().perform(req , res);
/*
				try {
					
					//DB接続
					con = getConnection(new InitialContext(), CommonConst.JDBC_ORACLE_SP2NM);

					//マーケティングプランナーの判定
					SelectDaikoSyokuinBase baseDaiko = new SelectDaikoSyokuinBase(con);
					baseDaiko.selectCredit代行(dwhUserId);
					List lsDaiko = baseDaiko.getList();
					if(lsDaiko == null || lsDaiko.isEmpty()){
						
						//マーケティングプランナーではない場合はメニュー画面へ
						return "./JSP/MENU/Menu.jsp";

					}else{
						//マーケティングプランナーの場合は代行店舗選択画面へ
						return new ViewDaikoAction().perform(req , res);
					}
					
				} catch (Exception e) {
					throw e;
				} finally {
					try {
						if (con != null) con.close();
						con = null;
					} catch (SQLException e1) {
						FWLog.error(e1);
					}
				}
*/
			}else if("unify".equals(applName)){
				
				loginInfo.setＵＮＩＦＹフラグ(unify_flg);

				//城北ＣＲＭシステムメニュー画面
				if("0".equals(unify_flg)){
					return "./JSP/MENU/Menu.jsp";

				//一元化メニュー画面
				}else if("1".equals(unify_flg)){
					return "./JSP/LIST/Menu.jsp";
					
				//ハンディー端末用メニュー画面
				}else if("3".equals(unify_flg)){
					return "./JSP/LIST/MenuHT.jsp";

				}else{
					return "./JSP/MENU/Menu.jsp";
				}

			}else{
				return "./JSP/MENU/Menu.jsp";
			}

		}else{
			//ログインＮＧの場合、メッセージをセッションにセットしてログイン画面に遷移
			session.setAttribute(CommonConst.SS_LOGIN_INFO_BEAN, loginInfo);
			session.setAttribute(CommonConst.ERROR_MSG_LIST, lsMessage);
			return "./JSP/MENU/Login.jsp";
		}

	}
}
