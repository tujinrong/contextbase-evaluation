"""SQL helpers limited to the newly created author UI fixture; never a user DB."""
import subprocess,json
DATABASE='SP2_WebFixture_UI_R20261029'
OWNER="IF NOT EXISTS(SELECT 1 FROM sys.extended_properties WHERE class=0 AND name=N'SP2Owner' AND CONVERT(nvarchar(200),value)=N'sample-project2/CSharp_ASPNET/SP2-DEMO-01') THROW 51000,'Fixture owner mismatch',1; "
def execute(sql):
    result=subprocess.run(['sqlcmd','-S',r'.\SQLEXPRESS','-E','-C','-b','-d',DATABASE,'-f','65001','-y','0','-Q','SET NOCOUNT ON; '+OWNER+sql],capture_output=True)
    if result.returncode:raise RuntimeError(result.stderr.decode('utf8',errors='replace') or result.stdout.decode('utf8',errors='replace'))
    return result.stdout.decode('utf-8-sig').strip()
def rows(sql):return json.loads(''.join(execute(sql+' FOR JSON PATH,INCLUDE_NULL_VALUES;').splitlines()))
def employee(number='000001'):
    assert len(number)==6 and number.isascii() and number.isdigit()
    return rows("SELECT * FROM dbo.m_employee WHERE employee_no='"+number+"'")[0]
def careers(number='000001'):
    assert len(number)==6 and number.isascii() and number.isdigit()
    return rows("SELECT c.* FROM dbo.t_career c JOIN dbo.m_employee e ON e.employee_id=c.employee_id WHERE e.employee_no='"+number+"' ORDER BY c.career_id")
def search_counter():
    # Read-only execution metadata filtered to this owned DB and parameterized
    # SQL-SEARCH fingerprint. No server settings/trace sessions are changed.
    return rows("SELECT q.execution_count,CONVERT(varchar(130),q.plan_handle,1) AS plan_token FROM sys.dm_exec_query_stats q CROSS APPLY sys.dm_exec_sql_text(q.sql_handle)t CROSS APPLY sys.dm_exec_plan_attributes(q.plan_handle)a WHERE a.attribute='dbid' AND CONVERT(int,a.value)=DB_ID() AND t.text LIKE '%SELECT e.employee_id,e.employee_no%' AND t.text LIKE '%ORDER BY e.employee_no;%' AND t.text NOT LIKE '%sys.dm_exec_query_stats%'")
