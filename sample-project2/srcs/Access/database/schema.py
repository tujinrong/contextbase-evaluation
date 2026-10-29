"""ACE 5-table / 48-column creation recipe. No connection on import."""
TEXT, MEMO, LONG, SHORT, BYTE, BOOL, DATE = 10, 12, 4, 3, 2, 1, 8
# name, DAO type, physical UTF-16 capacity, required, default, validation
TABLES = {
 "m_app_user": [
  ("user_id",TEXT,40,True,None,None),("login_id",TEXT,20,True,None,None),
  ("display_name",TEXT,80,True,None,None),("password_verifier",MEMO,0,True,None,None),
  ("role_id",TEXT,5,True,None,'In ("ADMIN","STAFF")'),("is_enabled",BOOL,0,True,"True",None),
  ("failed_count",BYTE,0,True,"0","Between 0 And 5"),("locked_until",DATE,0,False,None,None)],
 "m_employee": [
  ("employee_id",LONG,0,True,"COUNTER",None),("employee_no",TEXT,6,True,None,'Like "######"'),
  ("employee_name",TEXT,80,True,None,None),("employee_kana",TEXT,160,True,None,None),
  ("department_category",TEXT,24,True,'"DEPARTMENT"','="DEPARTMENT"'),("department_code",TEXT,2,True,None,'Between "01" And "99"'),
  ("employment_category",TEXT,24,True,'"EMPLOYMENT_STATUS"','="EMPLOYMENT_STATUS"'),("employment_status",TEXT,2,True,'"01"','In ("01","02","03")'),
  ("join_date",DATE,0,True,None,">=#1900-01-01#"),
  ("career_summary",MEMO,0,False,None,None),("skills",MEMO,0,False,None,None),
  ("qualifications",MEMO,0,False,None,None),("self_pr",MEMO,0,False,None,None),
  ("updated_at",DATE,0,True,None,None),("updated_by",TEXT,40,True,None,None),
  ("revision",LONG,0,True,"1","Between 1 And 2147483647")],
 "t_career": [
  ("career_id",LONG,0,True,"COUNTER",None),("employee_id",LONG,0,True,None,None),
  ("start_month",DATE,0,True,None,">=#1900-01-01#"),("end_month",DATE,0,False,None,None),
  ("company_name",TEXT,200,True,None,None),("project_name",TEXT,200,True,None,None),
  ("description",MEMO,0,True,None,None),("duties",MEMO,0,True,None,None),
  ("achievements",MEMO,0,False,None,None),("technologies",MEMO,0,False,None,None),
  ("role_category",TEXT,24,True,'"PROJECT_ROLE"','="PROJECT_ROLE"'),("role_code",TEXT,2,True,None,'Between "01" And "99"'),
  ("team_size",SHORT,0,True,None,"Between 1 And 999"),("phases",MEMO,0,False,None,None)],
 "m_code_category": [("category_id",TEXT,24,True,None,'In ("DEPARTMENT","EMPLOYMENT_STATUS","PROJECT_ROLE")'),("category_name",TEXT,80,True,None,None)],
 "m_code": [("category_id",TEXT,24,True,None,None),("code",TEXT,2,True,None,'Between "01" And "99"'),
  ("code_name",TEXT,80,True,None,None),("sort_order",SHORT,0,True,"1","Between 1 And 999"),
  ("is_enabled",BOOL,0,True,"True",None),("updated_at",DATE,0,True,None,None),
  ("updated_by",TEXT,40,True,None,None),("revision",LONG,0,True,"1","Between 1 And 2147483647")]
}
INDEXES = [
 ("m_app_user","PK_T01",["user_id"],True,True),("m_app_user","UK_T01_login",["login_id"],True,False),
 ("m_employee","PK_T02",["employee_id"],True,True),("m_employee","UK_T02_no",["employee_no"],True,False),
 ("t_career","PK_T03",["career_id"],True,True),("m_code_category","PK_T04",["category_id"],True,True),
 ("m_code","PK_T05",["category_id","code"],True,True),
 ("m_employee","IX_T02_filter",["department_category","department_code","employment_category","employment_status"],False,False),
 ("t_career","IX_T03_employee_start",["employee_id","start_month"],False,False)]
RELATIONS = [
 ("FK01","m_employee","t_career",[("employee_id","employee_id")]),
 ("FK02","m_code_category","m_code",[("category_id","category_id")]),
 ("FK03","m_code","m_employee",[("category_id","department_category"),("code","department_code")]),
 ("FK04","m_code","m_employee",[("category_id","employment_category"),("code","employment_status")]),
 ("FK05","m_code","t_career",[("category_id","role_category"),("code","role_code")])]

def create(db):
    for name, fields in TABLES.items():
        table = db.CreateTableDef(name)
        for name_, kind, size, required, default, rule in fields:
            field = table.CreateField(name_, kind, size) if size else table.CreateField(name_, kind)
            field.Required = required
            if kind in (TEXT, MEMO): field.AllowZeroLength = False
            if default == "COUNTER": field.Attributes = field.Attributes | 16
            elif default is not None: field.DefaultValue = default
            if rule: field.ValidationRule = rule; field.ValidationText = "保存データの型または範囲が不正です。"
            table.Fields.Append(field)
        db.TableDefs.Append(table)
    for table, name, fields, unique, primary in INDEXES:
        td = db.TableDefs(table); index = td.CreateIndex(name)
        index.Unique = unique; index.Primary = primary
        for column in fields: index.Fields.Append(index.CreateField(column))
        td.Indexes.Append(index)
    for name, parent, child, fields in RELATIONS:
        rel = db.CreateRelation(name, parent, child, 0)
        for source, target in fields:
            field = rel.CreateField(source); field.ForeignName = target; rel.Fields.Append(field)
        db.Relations.Append(rel)
    db.TableDefs("m_employee").ValidationRule = "[join_date]=DateValue([join_date])"
    db.TableDefs("t_career").ValidationRule = "Day([start_month])=1 And [start_month]=DateValue([start_month]) And ([end_month] Is Null Or (Day([end_month])=1 And [end_month]=DateValue([end_month]) And [end_month]>=[start_month]))"
