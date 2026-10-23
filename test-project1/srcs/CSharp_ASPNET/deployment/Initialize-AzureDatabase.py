"""Initialize this deployment's empty Azure SQL database; secrets arrive only in environment variables."""
import json
import os
from pathlib import Path
import re
import hashlib
import pyodbc

ROOT = Path(__file__).resolve().parent.parent
DATABASE = "contextbase_test_project1_mvc"
SERVER = "sql-contextbase-student-8a14b4.database.windows.net"
SOURCE = (ROOT / "database/001_schema.sql").read_text(encoding="utf-8-sig")
CODE_COLUMNS = {("m_student", "gender_code"): (1, False), ("m_student", "prefecture_code"): (2, False), ("m_student", "enrollment_status_code"): (2, False), ("m_student", "relationship_code"): (2, True), ("m_class", "grade_code"): (2, False)}
EXPECTED_TABLES = dict(re.findall(r"CREATE TABLE dbo\.(\w+) \((.*?)\n\);", SOURCE, re.S))
ADAPTED = SOURCE
for (table, column), (width, nullable) in CODE_COLUMNS.items():
    declaration = f"  {column} varchar({width}) COLLATE Latin1_General_100_BIN2 {'NULL' if nullable else 'NOT NULL'}"
    assert ADAPTED.count(declaration) == 1, f"Unexpected source declaration: {column}"
    ADAPTED = ADAPTED.replace(declaration, declaration.replace(f"varchar({width})", "varchar(10)"))
WIDTH_CHECKS = "\n".join(f"ALTER TABLE dbo.{table} WITH CHECK ADD CONSTRAINT ck_{table}_{column}_width CHECK ({column} IS NULL OR DATALENGTH({column})<={width});" for (table, column), (width, _) in CODE_COLUMNS.items())
ADAPTED += "\n" + WIDTH_CHECKS + "\n"
SEED_SOURCE = (ROOT / 'database/002_seed.sql').read_text(encoding='utf-8-sig')
SEED = SEED_SOURCE
for declaration, collation, expected_count in (
    ('category_id varchar(24)', 'Latin1_General_100_BIN2', 2),
    ('category_name nvarchar(24)', 'Latin1_General_100_CS_AS_SC', 1),
    ('code_value varchar(10)', 'Latin1_General_100_BIN2', 1),
    ('code_name nvarchar(24)', 'Latin1_General_100_CS_AS_SC', 1),
):
    assert SEED.count(declaration) == expected_count, 'Unexpected seed table-variable declaration.'
    SEED = SEED.replace(declaration, f'{declaration} COLLATE {collation}')


def connect(user, password):
    escaped = password.replace("}", "}}")
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER=tcp:{SERVER},1433;"
        f"DATABASE={DATABASE};UID={user};PWD={{{escaped}}};Encrypt=yes;"
        "TrustServerCertificate=no;Connection Timeout=120;",
        autocommit=True,
    )


def execute_text(connection, text):
    for batch in re.split(r"^\s*GO\s*$", text, flags=re.M | re.I):
        if batch.strip():
            cursor = connection.execute(batch)
            while cursor.nextset():
                pass


def verify_columns(connection, adapted):
    actual_tables = {row[0] for row in connection.execute("SELECT name FROM sys.tables WHERE is_ms_shipped=0 AND schema_id=SCHEMA_ID('dbo')")}
    assert actual_tables == set(EXPECTED_TABLES), "Unexpected table identities."
    for table, body in EXPECTED_TABLES.items():
        expected = []
        for line in body.splitlines():
            column = re.match(r"\s+(\w+) (\w+)(?:\((\w+)\))?(?: IDENTITY\(1,1\))?(?: COLLATE (\w+))? (NOT NULL|NULL)", line)
            if not column:
                continue
            name, data_type, size, collation, nullable = column.groups()
            if adapted and (table, name) in CODE_COLUMNS:
                size = "10"
            length = -1 if size == "max" else int(size) if data_type in ("varchar", "nvarchar", "binary", "varbinary") else None
            expected.append((name, data_type, length, collation, nullable == "NULL"))
        actual = [(r.COLUMN_NAME, r.DATA_TYPE, r.CHARACTER_MAXIMUM_LENGTH, r.COLLATION_NAME, r.IS_NULLABLE == "YES") for r in connection.execute("SELECT COLUMN_NAME,DATA_TYPE,CHARACTER_MAXIMUM_LENGTH,COLLATION_NAME,IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=? ORDER BY ORDINAL_POSITION", table)]
        assert actual == expected, f"Unexpected column definitions: {table}"


def foreign_keys(connection):
    return {tuple(r) for r in connection.execute("SELECT fk.name,OBJECT_NAME(fk.parent_object_id),p.name,OBJECT_NAME(fk.referenced_object_id),r.name FROM sys.foreign_keys fk JOIN sys.foreign_key_columns f ON f.constraint_object_id=fk.object_id JOIN sys.columns p ON p.object_id=f.parent_object_id AND p.column_id=f.parent_column_id JOIN sys.columns r ON r.object_id=f.referenced_object_id AND r.column_id=f.referenced_column_id")}


def verify_keys(connection, complete):
    expected = {(name, table, kind, columns.replace(" ", "")) for table, name, kind, columns in re.findall(r"ALTER TABLE dbo\.(\w+) ADD CONSTRAINT (\w+) (UNIQUE)\(([^)]+)\)", SOURCE)}
    expected |= {(name, table, "PRIMARY KEY", columns.replace(" ", "")) for table, body in EXPECTED_TABLES.items() for name, columns in re.findall(r"CONSTRAINT (\w+) PRIMARY KEY \(([^)]+)\)", body)}
    actual = {(r.name, r.table_name, "PRIMARY KEY" if r.type == "PK" else "UNIQUE", r.columns) for r in connection.execute("SELECT k.name,OBJECT_NAME(k.parent_object_id) table_name,k.type,STRING_AGG(CONVERT(nvarchar(max),c.name),',') WITHIN GROUP(ORDER BY ic.key_ordinal) columns FROM sys.key_constraints k JOIN sys.index_columns ic ON ic.object_id=k.parent_object_id AND ic.index_id=k.unique_index_id AND ic.key_ordinal>0 JOIN sys.columns c ON c.object_id=ic.object_id AND c.column_id=ic.column_id GROUP BY k.name,k.parent_object_id,k.type")}
    assert actual == expected, "Unexpected primary/unique key definitions."
    expected_fks = set()
    for table, name, columns, parent, references in re.findall(r"ALTER TABLE dbo\.(\w+) ADD CONSTRAINT (\w+) FOREIGN KEY\(([^)]+)\) REFERENCES dbo\.(\w+)\(([^)]+)\)", SOURCE):
        expected_fks |= {(name, table, col, parent, ref) for col, ref in zip(columns.split(','), references.split(','))}
    assert foreign_keys(connection) == (expected_fks if complete else {item for item in expected_fks if item[0] == 'fk_code_category'}), "Unexpected foreign key column mapping."


def finish_partial_schema(connection):
    verify_columns(connection, False)
    verify_keys(connection, False)
    for table in EXPECTED_TABLES:
        assert connection.execute(f"SELECT COUNT(*) FROM dbo.{table}").fetchval() == 0, "Recovery requires all seven tables to be empty."
    assert connection.execute("SELECT COUNT(*) FROM sys.database_principals WHERE name IN ('student_viewer','student_staff','student_admin','student_web')").fetchval() == 0
    for (table, column), (_, nullable) in CODE_COLUMNS.items():
        connection.execute(f"ALTER TABLE dbo.{table} ALTER COLUMN {column} varchar(10) COLLATE Latin1_General_100_BIN2 {'NULL' if nullable else 'NOT NULL'}")
    tail = SOURCE[SOURCE.index("ALTER TABLE dbo.m_class ADD CONSTRAINT fk_class_grade"):]
    execute_text(connection, tail + "\n" + WIDTH_CHECKS)


def verify_initialized_schema(connection):
    counts = connection.execute("SELECT (SELECT COUNT(*) FROM sys.tables WHERE is_ms_shipped=0), (SELECT COUNT(*) FROM dbo.m_code_category),(SELECT COUNT(*) FROM dbo.m_code),(SELECT COUNT(*) FROM dbo.m_student),(SELECT COUNT(*) FROM dbo.m_class)").fetchone()
    assert tuple(counts) == (7, 5, 70, 0, 0), "Unexpected initial schema or business data counts."
    assert connection.execute("SELECT snapshot_isolation_state FROM sys.databases WHERE database_id=DB_ID()").fetchval() == 1
    assert connection.execute("SELECT COUNT(*) FROM sys.foreign_keys WHERE is_disabled=1 OR is_not_trusted=1").fetchval() == 0
    assert connection.execute("SELECT COUNT(*) FROM sys.foreign_keys").fetchval() == 7
    assert connection.execute("SELECT COUNT(*) FROM sys.foreign_key_columns f JOIN sys.columns p ON p.object_id=f.parent_object_id AND p.column_id=f.parent_column_id JOIN sys.columns r ON r.object_id=f.referenced_object_id AND r.column_id=f.referenced_column_id WHERE p.max_length<>r.max_length OR p.scale<>r.scale").fetchval() == 0
    assert connection.execute("SELECT COUNT(*) FROM sys.check_constraints WHERE is_disabled=1 OR is_not_trusted=1").fetchval() == 0
    checks = {r[0] for r in connection.execute("SELECT name FROM sys.check_constraints")}
    expected_checks = set(re.findall(r'CONSTRAINT (\w+) CHECK', SOURCE)) | {f'ck_{table}_{column}_width' for table, column in CODE_COLUMNS}
    assert checks == expected_checks, 'Unexpected CHECK constraint identities.'
    expected_indexes = set(re.findall(r'CREATE INDEX (\w+) ON', SOURCE))
    assert {r[0] for r in connection.execute("SELECT name FROM sys.indexes WHERE object_id IN(SELECT object_id FROM sys.tables WHERE is_ms_shipped=0) AND is_primary_key=0 AND is_unique_constraint=0 AND index_id>0")} == expected_indexes


with connect("cbsetup", os.environ["CB_SQL_ADMIN_PASSWORD"]) as connection:
    assert tuple(connection.execute("SELECT DB_NAME(), CONVERT(int,SERVERPROPERTY('EngineEdition'))").fetchone()) == (DATABASE, 5)
    count = connection.execute("SELECT COUNT(*) FROM sys.tables WHERE is_ms_shipped=0").fetchval()
    if count not in (0, 7):
        raise RuntimeError("Database is not empty or a complete seven-table installation; refusing to overwrite it.")
    if count == 7:
        for table in ("m_student", "m_class", "t_operation_log", "t_confirmation", "t_runtime_state"):
            assert connection.execute(f"SELECT COUNT(*) FROM dbo.{table}").fetchval() == 0, "Initial deployment refuses databases with business/session data."
    connection.execute("ALTER DATABASE CURRENT SET ALLOW_SNAPSHOT_ISOLATION ON")
    connection.execute("SET XACT_ABORT ON; BEGIN TRANSACTION;")
    try:
        if count == 0:
            schema = ADAPTED[ADAPTED.index('CREATE TABLE dbo.m_student'):]
            execute_text(connection, schema)
        elif not connection.execute("SELECT USER_ID('student_staff')").fetchval():
            finish_partial_schema(connection)
        verify_columns(connection, True)
        verify_keys(connection, True)
        execute_text(connection, SEED)
        execute_text(connection, (ROOT / 'database/003_web_permissions.sql').read_text(encoding='utf-8-sig'))
        verify_initialized_schema(connection)
        connection.execute("COMMIT TRANSACTION")
    except BaseException:
        connection.execute("IF @@TRANCOUNT>0 ROLLBACK TRANSACTION")
        raise
    password = os.environ["CB_SQL_APP_PASSWORD"].replace("'", "''")
    if not connection.execute("SELECT USER_ID('student_web')").fetchval():
        connection.execute(f"CREATE USER [student_web] WITH PASSWORD=N'{password}'")
        connection.execute("ALTER ROLE student_staff ADD MEMBER student_web")
with connect("student_web", os.environ["CB_SQL_APP_PASSWORD"]) as connection:
    assert tuple(connection.execute("SELECT IS_ROLEMEMBER('student_staff'), IS_ROLEMEMBER('db_owner')").fetchone()) == (1, 0)
    assert tuple(connection.execute("SELECT HAS_PERMS_BY_NAME('dbo.m_student','OBJECT','SELECT'), HAS_PERMS_BY_NAME('dbo.m_student','OBJECT','UPDATE'), HAS_PERMS_BY_NAME('dbo.m_student','OBJECT','DELETE'), HAS_PERMS_BY_NAME('dbo.t_operation_log','OBJECT','UPDATE')").fetchone()) == (1, 1, 0, 0)
    assert connection.execute("SELECT COUNT(*) FROM dbo.m_code").fetchval() == 70
print(json.dumps({"tables": 7, "categories": 5, "codes": 70, "students": 0, "classes": 0, "foreignKeys": 7, "applicationUser": "student_web", "role": "student_staff", "tlsCertificateVerified": True,"sourceSchemaSha256":hashlib.sha256(SOURCE.encode()).hexdigest(),"adaptedSchemaSha256":hashlib.sha256(ADAPTED.encode()).hexdigest()}))
