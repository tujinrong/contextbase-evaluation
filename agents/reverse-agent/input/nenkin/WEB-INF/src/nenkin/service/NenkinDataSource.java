package nenkin.service;

import java.sql.Connection;
import java.sql.SQLException;

import javax.naming.InitialContext;
import javax.naming.NamingException;
import javax.sql.DataSource;

/** n2framework/WebOTX とローカル H2 で共通の JNDI 接続取得。 */
final class NenkinDataSource {
    private static final String[] BUSINESS_JNDI_NAMES = {
        "jdbc/RAROA_DB",
        "java:comp/env/jdbc/RAROA_DB"
    };
    private static final String[] STAFF_JNDI_NAMES = {
        "jdbc/Oracle_SP2NM",
        "java:comp/env/jdbc/Oracle_SP2NM"
    };
    private static final String[] CUSTOMER_JNDI_NAMES = {
        "jdbc/Oracle_DWH",
        "java:comp/env/jdbc/Oracle_DWH"
    };

    private static volatile DataSource businessCached;
    private static volatile DataSource staffCached;
    private static volatile DataSource customerCached;

    private NenkinDataSource() {
    }

    static Connection openConnection() throws SQLException {
        DataSource dataSource = businessCached;
        if (dataSource == null) {
            synchronized (NenkinDataSource.class) {
                dataSource = businessCached;
                if (dataSource == null) {
                    dataSource = lookup(BUSINESS_JNDI_NAMES,
                            "年金業務用JNDI DataSourceを取得できません。");
                    businessCached = dataSource;
                }
            }
        }
        return dataSource.getConnection();
    }

    static Connection openStaffConnection() throws SQLException {
        DataSource dataSource = staffCached;
        if (dataSource == null) {
            synchronized (NenkinDataSource.class) {
                dataSource = staffCached;
                if (dataSource == null) {
                    dataSource = lookup(STAFF_JNDI_NAMES,
                            "N2職員名簿用JNDI DataSourceを取得できません。");
                    staffCached = dataSource;
                }
            }
        }
        return dataSource.getConnection();
    }

    static Connection openCustomerConnection() throws SQLException {
        DataSource dataSource = customerCached;
        if (dataSource == null) {
            synchronized (NenkinDataSource.class) {
                dataSource = customerCached;
                if (dataSource == null) {
                    dataSource = lookup(CUSTOMER_JNDI_NAMES,
                            "N2顧客基本表用JNDI DataSourceを取得できません。");
                    customerCached = dataSource;
                }
            }
        }
        return dataSource.getConnection();
    }

    private static DataSource lookup(String[] jndiNames, String message) throws SQLException {
        NamingException last = null;
        for (int i = 0; i < jndiNames.length; i++) {
            try {
                Object value = new InitialContext().lookup(jndiNames[i]);
                if (value instanceof DataSource) {
                    return (DataSource) value;
                }
            } catch (NamingException e) {
                last = e;
            }
        }
        SQLException failure = new SQLException(message);
        if (last != null) {
            failure.initCause(last);
        }
        throw failure;
    }
}
