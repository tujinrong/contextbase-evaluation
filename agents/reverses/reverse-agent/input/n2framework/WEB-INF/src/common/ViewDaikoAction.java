/*
 * ì¬“ú: 2017/05/15
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

import common.base.SelectTenpoKanriDaichoBase;
import common.bean.DaikoBean;
import common.bean.TenpoListBean;
import common.util.CommonConverter;

/**
 * ‘ãs“X•Ü‘I‘ğ‰æ–Ê@•\¦‹¤’ÊƒAƒNƒVƒ‡ƒ“ƒNƒ‰ƒX
 *
 * @author Minoei RŒû
 * 
 * @date
 *   
 */
public class ViewDaikoAction extends CommonAction {

	/**
	 * ƒAƒNƒVƒ‡ƒ“Àsƒƒ\ƒbƒh
	 * 
	 * @param req ƒŠƒNƒGƒXƒg
	 * @param res ƒŒƒXƒ|ƒ“ƒX
	 * @return ‚i‚r‚o–¼
	 */
	public String perform(HttpServletRequest req, HttpServletResponse res) throws Exception {
		HttpSession session = req.getSession();


		//‚c‚aŒŸõ
		Connection con = null;

		try {
			//DBÚ‘±
			InitialContext ic = new InitialContext();
			con = getConnection(ic, CommonConst.JDBC_ORACLE_SP2NM);

			//“X•Üˆê——æ“¾
			List lsView1 = new ArrayList();
			List lsView2 = new ArrayList();
			List lsView3 = new ArrayList();
			List lsView4 = new ArrayList();
			List lsView5 = new ArrayList();

			DaikoBean beanDaiko = new DaikoBean();


			//“X•ÜŠÇ—‘ä’ ‚Ì“Ç‚İ‚İ
			SelectTenpoKanriDaichoBase baseSelectTenpoKanriDaicho = new SelectTenpoKanriDaichoBase(con);
			baseSelectTenpoKanriDaicho.selectTenpoIchiran();
			List lsTenpo = baseSelectTenpoKanriDaicho.getList();

			int cnt = 0;
			if(lsTenpo != null && !lsTenpo.isEmpty()){

				for(int i=0; i<lsTenpo.size(); i++){

					Map map = (Map)lsTenpo.get(i);
					cnt++;
					
					if(cnt <= 17){
						TenpoListBean beanList = new TenpoListBean();
						beanList.set“X•Ü”Ô†(CommonConverter.getAdd0String(((String)map.get("“X”Ô")),3));
						beanList.set“X•Ü–¼((String)map.get("Š¿š“X–¼"));
						beanList.set“X•Ü((CommonConverter.getAdd0String(((String)map.get("“X”Ô")),3)) + "@" + (String)map.get("Š¿š“X–¼"));

						lsView1.add(beanList);
					}


					if(cnt >= 18  &&  cnt <= 34){
						TenpoListBean beanList = new TenpoListBean();
						beanList.set“X•Ü”Ô†(CommonConverter.getAdd0String(((String)map.get("“X”Ô")),3));
						beanList.set“X•Ü–¼((String)map.get("Š¿š“X–¼"));
						beanList.set“X•Ü((CommonConverter.getAdd0String(((String)map.get("“X”Ô")),3)) + "@" + (String)map.get("Š¿š“X–¼"));

						lsView2.add(beanList);
					}


					if(cnt >= 35  &&  cnt <= 51){
						TenpoListBean beanList = new TenpoListBean();
						beanList.set“X•Ü”Ô†(CommonConverter.getAdd0String(((String)map.get("“X”Ô")),3));
						beanList.set“X•Ü–¼((String)map.get("Š¿š“X–¼"));
						beanList.set“X•Ü((CommonConverter.getAdd0String(((String)map.get("“X”Ô")),3)) + "@" + (String)map.get("Š¿š“X–¼"));

						lsView3.add(beanList);
					}


					if(cnt >= 52  &&  cnt <= 68){
						TenpoListBean beanList = new TenpoListBean();
						beanList.set“X•Ü”Ô†(CommonConverter.getAdd0String(((String)map.get("“X”Ô")),3));
						beanList.set“X•Ü–¼((String)map.get("Š¿š“X–¼"));
						beanList.set“X•Ü((CommonConverter.getAdd0String(((String)map.get("“X”Ô")),3)) + "@" + (String)map.get("Š¿š“X–¼"));

						lsView4.add(beanList);
					}
					
					
					
					if(cnt >= 69  &&  cnt <= 85){
						TenpoListBean beanList = new TenpoListBean();
						beanList.set“X•Ü”Ô†(CommonConverter.getAdd0String(((String)map.get("“X”Ô")),3));
						beanList.set“X•Ü–¼((String)map.get("Š¿š“X–¼"));
						beanList.set“X•Ü((CommonConverter.getAdd0String(((String)map.get("“X”Ô")),3)) + "@" + (String)map.get("Š¿š“X–¼"));

						lsView5.add(beanList);
					}
					
				}
			}
			beanDaiko.set“X•Üˆê——‚P(lsView1);
			beanDaiko.set“X•Üˆê——‚Q(lsView2);
			beanDaiko.set“X•Üˆê——‚R(lsView3);
			beanDaiko.set“X•Üˆê——‚S(lsView4);
			beanDaiko.set“X•Üˆê——‚T(lsView5);


			session.setAttribute(CommonConst.SS_JSP_BEAN, beanDaiko);

			return "./JSP/MENU/Daiko.jsp";

		} catch (Exception e) {
			try {
				if (con != null) con.rollback();
			} catch (SQLException e1) {
				FWLog.error(e1);
			}
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

}
