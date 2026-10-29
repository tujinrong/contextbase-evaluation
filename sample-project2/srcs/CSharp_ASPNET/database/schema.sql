-- SP2-CSharp_ASPNET-DB-SQLSERVER 1.0 / 5 tables, 48 columns. Apply only to a newly owned empty DB.
SET XACT_ABORT ON;
IF EXISTS (SELECT 1 FROM sys.tables WHERE is_ms_shipped=0) THROW 51000,'Target is not empty; no schema changes applied.',1;
CREATE TABLE dbo.m_app_user(
 user_id nvarchar(40) COLLATE Latin1_General_100_BIN2 NOT NULL CONSTRAINT PK_app_user PRIMARY KEY,
 login_id varchar(20) COLLATE Latin1_General_100_CI_AS NOT NULL CONSTRAINT UQ_app_user_login UNIQUE,
 display_name nvarchar(80) NOT NULL,password_verifier nvarchar(2048) NOT NULL,
 role_id varchar(5) NOT NULL CONSTRAINT CK_user_role CHECK(role_id IN ('ADMIN','STAFF')),
 is_enabled bit NOT NULL CONSTRAINT DF_user_enabled DEFAULT(1),
 failed_count tinyint NOT NULL CONSTRAINT DF_user_failed DEFAULT(0) CONSTRAINT CK_user_failed CHECK(failed_count BETWEEN 0 AND 5),
 locked_until datetime2(7) NULL,
 CONSTRAINT CK_user_login CHECK(LEN(login_id) BETWEEN 1 AND 20 AND login_id COLLATE Latin1_General_100_BIN2 NOT LIKE '%[^A-Za-z0-9]%'),
 CONSTRAINT CK_user_control CHECK((failed_count=5 AND locked_until IS NOT NULL) OR (failed_count<5 AND locked_until IS NULL))
);
CREATE TABLE dbo.m_code_category(
 category_id varchar(24) NOT NULL CONSTRAINT PK_code_category PRIMARY KEY CONSTRAINT CK_category CHECK(category_id IN('DEPARTMENT','EMPLOYMENT_STATUS','PROJECT_ROLE')),
 category_name nvarchar(80) NOT NULL
);
CREATE TABLE dbo.m_code(
 category_id varchar(24) NOT NULL,code char(2) NOT NULL,
 code_name nvarchar(80) NOT NULL,
 sort_order smallint NOT NULL CONSTRAINT DF_code_sort DEFAULT(1) CONSTRAINT CK_code_sort CHECK(sort_order BETWEEN 1 AND 999),
 is_enabled bit NOT NULL CONSTRAINT DF_code_enabled DEFAULT(1),
 updated_at datetime2(7) NOT NULL,updated_by nvarchar(40) NOT NULL,
 revision int NOT NULL CONSTRAINT DF_code_revision DEFAULT(1) CONSTRAINT CK_code_revision CHECK(revision>=1),
 CONSTRAINT PK_code PRIMARY KEY(category_id,code),
 CONSTRAINT FK_code_category FOREIGN KEY(category_id) REFERENCES dbo.m_code_category(category_id),
 CONSTRAINT CK_code CHECK(code COLLATE Latin1_General_100_BIN2 NOT LIKE '%[^0-9]%' AND code BETWEEN '01' AND '99')
);
CREATE TABLE dbo.m_employee(
 employee_id bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_employee PRIMARY KEY,
 employee_no char(6) NOT NULL CONSTRAINT UQ_employee_no UNIQUE,
 employee_name nvarchar(80) NOT NULL,employee_kana nvarchar(160) NOT NULL,
 department_category varchar(24) NOT NULL CONSTRAINT DF_employee_department DEFAULT('DEPARTMENT') CONSTRAINT CK_employee_department CHECK(department_category='DEPARTMENT'),
 department_code char(2) NOT NULL,
 employment_category varchar(24) NOT NULL CONSTRAINT DF_employee_employment DEFAULT('EMPLOYMENT_STATUS') CONSTRAINT CK_employee_employment CHECK(employment_category='EMPLOYMENT_STATUS'),
 employment_status char(2) NOT NULL CONSTRAINT DF_employee_status DEFAULT('01'),
 join_date date NOT NULL CONSTRAINT CK_employee_join CHECK(join_date>='19000101'),
 career_summary nvarchar(2000) NULL,skills nvarchar(2000) NULL,qualifications nvarchar(2000) NULL,self_pr nvarchar(2000) NULL,
 updated_at datetime2(7) NOT NULL,updated_by nvarchar(40) NOT NULL,
 revision int NOT NULL CONSTRAINT DF_employee_revision DEFAULT(1) CONSTRAINT CK_employee_revision CHECK(revision>=1),
 CONSTRAINT CK_employee_no CHECK(employee_no COLLATE Latin1_General_100_BIN2 NOT LIKE '%[^0-9]%' AND DATALENGTH(employee_no)=6),
 CONSTRAINT FK_employee_department FOREIGN KEY(department_category,department_code) REFERENCES dbo.m_code(category_id,code),
 CONSTRAINT FK_employee_employment FOREIGN KEY(employment_category,employment_status) REFERENCES dbo.m_code(category_id,code)
);
CREATE TABLE dbo.t_career(
 career_id bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_career PRIMARY KEY,
 employee_id bigint NOT NULL,start_month date NOT NULL,end_month date NULL,
 company_name nvarchar(200) NOT NULL,project_name nvarchar(200) NOT NULL,description nvarchar(2000) NOT NULL,duties nvarchar(2000) NOT NULL,
 achievements nvarchar(2000) NULL,technologies nvarchar(1000) NULL,
 role_category varchar(24) NOT NULL CONSTRAINT DF_career_role DEFAULT('PROJECT_ROLE') CONSTRAINT CK_career_role CHECK(role_category='PROJECT_ROLE'),
 role_code char(2) NOT NULL,team_size smallint NOT NULL CONSTRAINT CK_career_team CHECK(team_size BETWEEN 1 AND 999),phases nvarchar(400) NULL,
 CONSTRAINT FK_career_employee FOREIGN KEY(employee_id) REFERENCES dbo.m_employee(employee_id),
 CONSTRAINT FK_career_role FOREIGN KEY(role_category,role_code) REFERENCES dbo.m_code(category_id,code),
 CONSTRAINT CK_career_month CHECK(start_month>='19000101' AND DAY(start_month)=1 AND (end_month IS NULL OR (DAY(end_month)=1 AND end_month>=start_month)))
);
CREATE INDEX IX_employee_department_status ON dbo.m_employee(department_category,department_code,employment_category,employment_status,employee_no);
CREATE INDEX IX_career_employee_month ON dbo.t_career(employee_id,start_month DESC,career_id DESC);
