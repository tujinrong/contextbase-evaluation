"""Current-artifact authentication regression on one private, owned Access copy."""
from pathlib import Path
import argparse, datetime as dt, gc, hashlib, hmac, json, shutil, sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build

HARNESS=r'''
Option Explicit
Private report As String
Private Sub Need(ByVal id As String, ByVal okay As Boolean)
 report=report & id & "|" & IIf(okay,"PASS","FAIL") & vbLf
 If Not okay Then Err.Raise vbObjectError+980,,id
End Sub
Private Sub Reset(ByVal userId As String)
 CurrentDb.Execute "UPDATE m_app_user SET failed_count=0,locked_until=Null WHERE user_id='" & userId & "'",dbFailOnError
End Sub
Private Function RefusedVerifier(ByVal password As String) As Boolean
 On Error GoTo Rejected
 Dim v As String:v=NewVerifier(password):Exit Function
Rejected:
 RefusedVerifier=True
End Function
Public Function CredentialRegression(ByVal oldAdmin As String,ByVal oldStaff As String) As String
 Dim r As clsResult,v As String,i As Long,mark As Date,emoji As String
 On Error GoTo Failed
 report="":Reset "SP2ADMIN":Reset "SP2STAFF"
 Need "policy-minimum-three",MinimumPasswordScalars=3
 Set r=Authenticate("admin","123"):Need "admin-123-login",r.Kind="OK" And gSession.UserId="SP2ADMIN" And gSession.RoleId="ADMIN"
 Set r=Authorize("ADMIN"):Need "admin-authorization",r.Kind="OK"
 Set r=Authenticate("staff","123"):Need "staff-123-login",r.Kind="OK" And gSession.UserId="SP2STAFF" And gSession.RoleId="STAFF"
 Set r=Authorize("ADMIN"):Need "staff-not-admin",r.MessageId="MSG-003"
 Set r=Authenticate("  AdMiN  ","123"):Need "login-trim-case-rule",r.Kind="OK"
 Set r=Authenticate("demoadmin","123"):Need "old-admin-id-rejected",r.MessageId="MSG-001"
 Set r=Authenticate("demostaff","123"):Need "old-staff-id-rejected",r.MessageId="MSG-001"
 Set r=Authenticate("admin",oldAdmin):Need "old-admin-password-rejected",r.MessageId="MSG-001":Reset "SP2ADMIN"
 Set r=Authenticate("staff",oldStaff):Need "old-staff-password-rejected",r.MessageId="MSG-001":Reset "SP2STAFF"
 Need "empty-verifier-refused",RefusedVerifier("")
 Need "one-scalar-verifier-refused",RefusedVerifier("1")
 Need "two-scalar-verifier-refused",RefusedVerifier("12")
 Need "over-max-verifier-refused",RefusedVerifier(String$(129,"a"))
 v=NewVerifier("123"):Need "three-scalar-roundtrip",VerifyPassword("123",v)
 Need "wrong-password-no-bypass",Not VerifyPassword("124",v)
 Need "leading-space-preserved",Not VerifyPassword(" 123",v)
 Need "trailing-space-preserved",Not VerifyPassword("123 ",v)
 v=NewVerifier(String$(128,"a")):Need "maximum128-roundtrip",VerifyPassword(String$(128,"a"),v)
 emoji=ChrW(&HD83D) & ChrW(&HDE00)
 Need "unicode-two-scalars-refused",RefusedVerifier(emoji & "a")
 v=NewVerifier(emoji & "ab"):Need "unicode-three-scalars-roundtrip",VerifyPassword(emoji & "ab",v)
 For i=0 To 2
  Set r=Authenticate("admin",Left$("12",i)):Need "login-under-min-" & CStr(i),r.MessageId="MSG-001"
 Next
 Set r=Authenticate("admin",String$(129,"a")):Need "login-over-max",r.MessageId="MSG-001"
 Reset "SP2STAFF"
 For i=1 To 5
  Set r=Authenticate("staff","124"):Need "wrong-three-scalar-failure-" & CStr(i),r.MessageId="MSG-001" And DLookup("failed_count","m_app_user","user_id='SP2STAFF'")=i
 Next
 mark=DLookup("locked_until","m_app_user","user_id='SP2STAFF'")
 Set r=Authenticate("staff","123"):Need "correct-password-locked",r.MessageId="MSG-001" And DLookup("locked_until","m_app_user","user_id='SP2STAFF'")=mark
 Reset "SP2STAFF"
 Set r=Authenticate("staff","123"):Need "unlocked-valid-login",r.Kind="OK"
 Reset "SP2ADMIN":Reset "SP2STAFF"
 CredentialRegression=report:Exit Function
Failed:
 CredentialRegression=report & "harness|FAIL|" & CStr(Err.Number)
End Function
'''

def field(record,name):
    fields=record.Fields;item=fields(name);value=item.Value;item=None;fields=None;return value

def snapshot(db):
    answer={}
    tables=db.TableDefs
    names=[]
    for index in range(tables.Count):
        table=tables(index);name=str(table.Name);table=None
        if not name.startswith('MSys'):names.append(name)
    tables=None
    for name in sorted(names):
        rows=[];r=db.OpenRecordset('SELECT * FROM ['+name+']',4)
        fields=r.Fields;columns=[]
        for index in range(fields.Count):
            item=fields(index);columns.append(str(item.Name));item=None
        fields=None
        while not r.EOF:
            row={column:field(r,column) for column in columns}
            rows.append(row);r.MoveNext()
        r.Close();r=None
        answer[name]=sorted(rows,key=lambda row:json.dumps(row,ensure_ascii=False,sort_keys=True,default=str))
    return answer

def stable_snapshot(data):
    # Only the two approved credential/control column sets may differ.
    clean={name:[dict(row) for row in rows] for name,rows in data.items()}
    for row in clean.get('m_app_user',[]):
        if str(row.get('user_id','')).upper() in ('SP2ADMIN','SP2STAFF'):
            for name in ('login_id','password_verifier','failed_count','locked_until'):row.pop(name,None)
    return clean

def digest(data):return hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,default=str).encode()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--database',type=Path,default=build.ROOT/'build/CareerManagement.accdb');p.add_argument('--record',type=Path,default=build.ROOT/'build/test-results/credentials.json');p.add_argument('--run-id',required=True);args=p.parse_args()
    source=args.database.resolve();source_hash=build.sha(source);work=build.ROOT/'.tmp/credentials';work.mkdir(parents=True,exist_ok=True)
    target=work/'CareerManagement-auth-test.accdb';shutil.copy2(source,target)
    prior=work/'previous-test-secrets.dpapi'
    old=json.loads(build.win32crypt.CryptUnprotectData(prior.read_bytes(),None,None,None,0)[1]) if prior.exists() else ['prior-admin-credential-unavailable','prior-staff-credential-unavailable']
    if old[0]=='123' or old[1]=='123':old=['previous-generated-admin-value','previous-generated-staff-value']
    before_pids=set(build.win32process.EnumProcesses());app=None;db=None;handle=None;checks=[];record={'status':'FAIL','projectId':'sample-project2','profileId':'Access','runId':args.run_id,'artifactSha256':source_hash,'startedAtUtc':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'Authentication/authorization and credential boundaries on private copy only; no user authentication UI or reseed','formalScore':None}
    try:
        app=build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application'));app.Visible=False
        window=app.hWndAccessApp;window=window() if callable(window) else window;pid=build.win32process.GetWindowThreadProcessId(window)[1]
        if pid in before_pids:raise RuntimeError('New owned Access required')
        handle=build.win32api.OpenProcess(0x100000|0x400,False,pid);app.OpenCurrentDatabase(str(target))
        db=app.CurrentDb();before=snapshot(db);db.Close();db=None
        salts=[]
        for identity,role in [('ADMIN','ADMIN'),('STAFF','STAFF')]:
            rows=[row for row in before['m_app_user'] if str(row['login_id']).upper()==identity]
            assert len(rows)==1 and rows[0]['role_id']==role and rows[0]['is_enabled']
            parts=rows[0]['password_verifier'].split('$');assert parts[:3]==['PBKDF2-SHA256','v=1','i=600000']
            salt=bytes.fromhex(parts[3][2:]);actual=hashlib.pbkdf2_hmac('sha256',b'123',salt,600000,32)
            assert len(salt)==32 and hmac.compare_digest(actual,bytes.fromhex(parts[4][3:]));salts.append(salt)
            checks.append({'id':'independent-pbkdf2-'+identity.lower(),'status':'PASS'})
        assert salts[0]!=salts[1];checks.append({'id':'distinct-random-salts','status':'PASS'})
        component=app.VBE.ActiveVBProject.VBComponents.Add(1);component.Name='CredentialRegressionModule';module=component.CodeModule
        if module.CountOfLines:module.DeleteLines(1,module.CountOfLines)
        module.AddFromString(build.vbe_text(HARNESS));module=None;component=None;app.DoCmd.RunCommand(126)
        assert app.IsCompiled
        result=app.Run('CredentialRegression',*old);old.clear()
        if isinstance(result,tuple):result=result[0]
        for line in str(result).splitlines():
            parts=line.split('|',2);checks.append({'id':parts[0],'status':parts[1],**({'detail':parts[2]} if len(parts)>2 else {})})
        db=app.CurrentDb();after=snapshot(db);db.Close();db=None
        assert stable_snapshot(before)==stable_snapshot(after)
        checks.append({'id':'all-business-audit-pk-role-values-preserved','status':'PASS'})
        record.update(checks=checks,businessStableDigest=digest(stable_snapshot(after)),rows={name:len(rows) for name,rows in after.items()},testSourceSha256=build.sha(Path(__file__)))
        app.CloseCurrentDatabase();app.Quit(2);app=None;build.release()
        exited=build.win32event.WaitForSingleObject(handle,10000)==0;code=build.win32process.GetExitCodeProcess(handle)
        unchanged=build.sha(source)==source_hash
        record.update(ownedProcess={'pid':pid,'newInstance':True,'exited':exited,'exitCode':code},sourceArtifactUnchanged=unchanged)
        if checks and all(c['status']=='PASS' for c in checks) and exited and code==0 and unchanged:record['status']='PASS'
    except BaseException as error:
        record.update(errorType=type(error).__name__,checks=checks)
        raise
    finally:
        old.clear();db=None
        if app is not None:
            try:app.CloseCurrentDatabase();app.Quit(2)
            except Exception:pass
        app=None;build.release()
        if handle is not None:handle.Close()
        record['completedAtUtc']=dt.datetime.now(dt.timezone.utc).isoformat();args.record.parent.mkdir(parents=True,exist_ok=True);args.record.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':record['status'],'checks':len(checks),'artifactSha256':source_hash,'ownedExitCode':record.get('ownedProcess',{}).get('exitCode')}));return int(record['status']!='PASS')

if __name__=='__main__':raise SystemExit(main())
