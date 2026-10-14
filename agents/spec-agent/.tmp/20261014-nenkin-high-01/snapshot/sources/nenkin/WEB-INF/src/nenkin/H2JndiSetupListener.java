package nenkin;

import java.io.File;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.sql.Connection;
import java.sql.Statement;

import javax.naming.Context;
import javax.naming.InitialContext;
import javax.naming.NameAlreadyBoundException;
import javax.naming.NamingException;
import javax.servlet.ServletContext;
import javax.servlet.ServletContextEvent;
import javax.servlet.ServletContextListener;

import org.h2.jdbcx.JdbcDataSource;
import org.h2.tools.RunScript;

/** Local JNDI compatibility database for the bundled N2 runtime. */
public final class H2JndiSetupListener implements ServletContextListener {
	private static final String LOCAL_DATABASE_PROPERTY = "n2nenkin.localDb";

	private static final String[] JNDI_NAMES = {
		"jdbc/Oracle_SP2NM", "jdbc/Oracle_DWH", "jdbc/RAROA_DB", "jdbc/RAROA_SHARE"
	};

	private JdbcDataSource dataSource;

	public void contextInitialized(ServletContextEvent event) {
		ServletContext context = event.getServletContext();
		if (!Boolean.parseBoolean(System.getProperty(LOCAL_DATABASE_PROPERTY, "false"))) {
			context.log("Local H2 compatibility database is disabled; using the N2 container JNDI database.");
			return;
		}
		try {
			File databaseFile = resolveDatabaseFile(context);
			File directory = databaseFile.getParentFile();
			if (!directory.exists() && !directory.mkdirs()) {
				throw new IllegalStateException("Cannot create database directory: " + directory);
			}

			dataSource = new JdbcDataSource();
			dataSource.setURL(createJdbcUrl(databaseFile));
			dataSource.setUser("sa");
			dataSource.setPassword("");
			initializeDatabase(context);
			bindDataSource();
			context.log("N2 pension compatibility database initialized: " + databaseFile.getAbsolutePath());
		} catch (Exception e) {
			context.log("N2 pension compatibility database initialization failed.", e);
			throw new IllegalStateException("Database initialization failed.", e);
		}
	}

	public void contextDestroyed(ServletContextEvent event) {
		if (dataSource == null) return;
		unbindDataSource();
		shutdownDatabase(event.getServletContext());
	}

	private File resolveDatabaseFile(ServletContext context) {
		String overridePath = System.getProperty("n2nenkin.db.path");
		if (overridePath != null && overridePath.trim().length() > 0) {
			return new File(overridePath.trim()).getAbsoluteFile();
		}
		String directory = context.getRealPath("/WEB-INF/local-db");
		if (directory == null) throw new IllegalStateException("Expanded deployment is required for local H2.");
		return new File(directory, "nenkin").getAbsoluteFile();
	}

	private String createJdbcUrl(File databaseFile) {
		return "jdbc:h2:file:" + databaseFile.getAbsolutePath().replace('\\', '/')
			+ ";MODE=Oracle;DATABASE_TO_UPPER=TRUE;CASE_INSENSITIVE_IDENTIFIERS=FALSE";
	}

	private void initializeDatabase(ServletContext context) throws Exception {
		Connection connection = null;
		try {
			connection = dataSource.getConnection();
			runScript(context, connection, "/WEB-INF/resources/db/schema.sql");
			runScript(context, connection, "/WEB-INF/resources/db/data.sql");
		} finally {
			if (connection != null) connection.close();
		}
	}

	private void runScript(ServletContext context, Connection connection, String path) throws Exception {
		InputStream stream = context.getResourceAsStream(path);
		if (stream == null) throw new IllegalStateException("Database resource not found: " + path);
		Reader reader = null;
		try {
			reader = new InputStreamReader(stream, "UTF-8");
			RunScript.execute(connection, reader);
		} finally {
			if (reader != null) reader.close(); else stream.close();
		}
	}

	private void bindDataSource() throws NamingException {
		InitialContext context = new InitialContext();
		try { context.createSubcontext("jdbc"); } catch (NameAlreadyBoundException e) { }
		for (int i = 0; i < JNDI_NAMES.length; i++) context.rebind(JNDI_NAMES[i], dataSource);
	}

	private void unbindDataSource() {
		try {
			Context context = new InitialContext();
			for (int i = 0; i < JNDI_NAMES.length; i++) {
				try { context.unbind(JNDI_NAMES[i]); } catch (NamingException e) { }
			}
		} catch (NamingException e) { }
	}

	private void shutdownDatabase(ServletContext context) {
		if (dataSource == null) return;
		Connection connection = null;
		Statement statement = null;
		try {
			connection = dataSource.getConnection();
			statement = connection.createStatement();
			statement.execute("SHUTDOWN");
		} catch (Exception e) {
			context.log("H2 shutdown failed.", e);
		} finally {
			try { if (statement != null) statement.close(); } catch (Exception e) { }
			try { if (connection != null) connection.close(); } catch (Exception e) { }
		}
	}
}
