"""Read-only HTTPS checks of the final publish and existing owned DEMO database.

Uses the explicit runtime profile, never scans servers/databases, never prints
passwords/cookies/bodies, and performs no employee/career/code writes.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, html, http.cookiejar, json, re, ssl, sys, urllib.error, urllib.parse, urllib.request

ROOT=Path(__file__).resolve().parents[2]
profile_path=ROOT/'.tmp/runtime/profile.json'
profile=json.loads(profile_path.read_text('utf-8-sig'))
assert profile['database']=='SP2_WebFixture_20261029' and profile['url']=='https://localhost:7443'
base=profile['url'];results=[]
input_path=ROOT/'build/generation/inputs.json';input_sha=hashlib.sha256(input_path.read_bytes()).hexdigest()
run_id=json.loads(input_path.read_text('utf-8'))['runId']

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def tree(path):
    records=[{'file':p.relative_to(path).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(path.rglob('*')) if p.is_file()]
    records.sort(key=lambda x:x['file'])
    return {'sha256':hashlib.sha256(json.dumps(records,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),'files':len(records),'kind':'directory'}
before=tree(ROOT/'build/publish')
def source_snapshot():
    return {p.relative_to(ROOT).as_posix():sha(p) for folder in ['src','database','tools','fixtures','tests'] for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
source_before=source_snapshot()

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

class Client:
    def __init__(self):
        self.cookies=http.cookiejar.CookieJar()
        self.opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPCookieProcessor(self.cookies),urllib.request.HTTPSHandler(context=ssl._create_unverified_context()))
    def request(self,path,data=None):
        body=urllib.parse.urlencode(data).encode() if data is not None else None
        headers={'Sec-Fetch-Mode':'navigate'}
        if data is not None:headers['Content-Type']='application/x-www-form-urlencoded'
        try:
            with self.opener.open(urllib.request.Request(base+path,body,headers),timeout=35) as response:return response.status,response.read(),dict(response.headers)
        except urllib.error.HTTPError as error:return error.code,error.read(),dict(error.headers)
    def login(self,user,password,csrf=True):
        status,body,_=self.request('/account/login');assert status==200
        token=re.search(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"',body.decode());assert token
        data={'LoginId':user,'Password':password}
        if csrf:data['__RequestVerificationToken']=html.unescape(token.group(1))
        return self.request('/account/login',data)
    def has_auth_cookie(self):return any(c.name=='__Host-SP2Auth' for c in self.cookies)

def check(identifier,action):
    try:
        action();results.append({'id':identifier,'status':'PASS'});print('PASS '+identifier,flush=True)
    except Exception as error:
        results.append({'id':identifier,'status':'FAIL','errorType':type(error).__name__});print('FAIL '+identifier,flush=True)

def denied(user,password):
    client=Client();status,body,_=client.login(user,password)
    assert status==200 and not client.has_auth_cookie() and b'login-form' in body

def accepted(user,role,code_status):
    client=Client();status,_,headers=client.login(user,'123')
    assert status==303 and headers.get('Location')=='/menu' and client.has_auth_cookie()
    status,body,_=client.request('/menu');assert status==200
    initial=re.search(r'data-initial="([^"]+)"',body.decode());assert initial
    menu=json.loads(html.unescape(initial.group(1)));assert menu['currentRole']==role
    assert (b'href="/codes"' in body)==(role=='ADMIN')
    assert client.request('/employees')[0]==200
    assert client.request('/codes')[0]==code_status

try:
    check('HTTP-DEMO-01-admin-123-current-role',lambda:accepted('admin','ADMIN',200))
    check('HTTP-DEMO-02-staff-123-current-role',lambda:accepted('staff','STAFF',403))
    for user in ['demoadmin','demostaff']:
        check('HTTP-DEMO-03-retired-id-'+user,lambda user=user:denied(user,'123'))
    for user,field in [('admin','adminPassword'),('staff','staffPassword')]:
        prior=profile[field]
        if prior!='123':check('HTTP-DEMO-04-prior-password-'+user,lambda user=user,prior=prior:denied(user,prior))
    for label,password in [('empty',''),('one','1'),('two','12'),('over128','x'*129),('wrong','124')]:
        check('HTTP-DEMO-05-reject-'+label,lambda password=password:denied('admin',password))
    def no_csrf():
        client=Client();assert client.login('admin','123',False)[0]==400 and not client.has_auth_cookie()
    check('HTTP-DEMO-06-csrf-required',no_csrf)
    # Restore successful-auth lock counters after intentionally wrong attempts.
    check('HTTP-DEMO-07-admin-recover-after-errors',lambda:accepted('admin','ADMIN',200))
    check('HTTP-DEMO-08-staff-recover-after-errors',lambda:accepted('staff','STAFF',403))
    assert source_before==source_snapshot() and input_sha==sha(input_path) and before==tree(ROOT/'build/publish')
    passed=all(item['status']=='PASS' for item in results)
    record={'projectId':'sample-project2','profileId':'CSharp_ASPNET','runId':run_id,'recordedAtUtc':datetime.now(timezone.utc).isoformat(),
        'status':'PASS' if passed else 'FAIL','inputManifestSha256':input_sha,'artifact':{'file':'build/publish',**before},
        'testSourceSha256':sha(Path(__file__)),'checks':results,'testedDatabase':profile['database'],'url':base,
        'oldPasswordProofAvailable':all(profile[field]!='123' for field in ['adminPassword','staffPassword']),
        'sourceInputAndArtifactUnchanged':True,'scope':'Final published HTTPS app. Two new IDs/password123, current roles, retired IDs/previous passwords, password bounds, wrong password, CSRF, and recovery. No business POSTs.',
        'tlsScope':'Existing localhost-only fixture self-signed certificate; product certificate defaults unchanged',
        'notExecuted':['Native browser/IME/keyboard','Full UI conformance','Excel/physical print','SQL Server2022 physical host','Formal acceptance/scoring'],'formalScore':None}
    output=ROOT/'build/test-results/demo-credentials-http.json';output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if passed:
        profile.update(adminPassword='123',staffPassword='123',adminLogin='admin',staffLogin='staff')
        profile_path.write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if passed else 1)
except Exception as error:
    output=ROOT/'build/test-results/demo-credentials-http.json';output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'projectId':'sample-project2','profileId':'CSharp_ASPNET','runId':run_id,'status':'FAIL','errorType':type(error).__name__,'checks':results,'formalScore':None},indent=2)+'\n',encoding='utf-8')
    raise
