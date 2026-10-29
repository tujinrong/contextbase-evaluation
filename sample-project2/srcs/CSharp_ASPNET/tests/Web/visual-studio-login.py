"""Verify the VS Development host with the public DEMO credentials.

Only the explicitly configured owned localhost fixture is read. Login is the
only POST; employee, career and code data must remain byte-for-byte unchanged.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib, html, http.cookiejar, json, os, re, shutil, ssl, subprocess
import urllib.error, urllib.parse, urllib.request

ROOT = Path(__file__).resolve().parents[2]
BASE = os.environ.get('SP2_DEBUG_URL', 'https://localhost:61184')
sqlcmd = shutil.which('sqlcmd') or 'C:/Program Files/Microsoft SQL Server/Client SDK/ODBC/180/Tools/Binn/SQLCMD.EXE'
checks = []
output = ROOT/os.environ.get('SP2_LOGIN_REPORT', 'build/test-results/visual-studio-login.json')
output.parent.mkdir(parents=True, exist_ok=True)
record = {'projectId': 'sample-project2', 'profileId': 'CSharp_ASPNET', 'status': 'RUNNING', 'formalScore': None}
output.write_text(json.dumps(record)+'\n', encoding='utf-8')

def sql(query):
    result = subprocess.run([sqlcmd, '-S', server, '-E', '-C', '-b', '-w', '65535', '-y', '0', '-d', database, '-Q', 'SET NOCOUNT ON; ' + query], capture_output=True, check=True)
    return result.stdout.strip()

def snapshot():
    return {table: hashlib.sha256(sql(f'SELECT * FROM dbo.{table} ORDER BY {key} FOR JSON PATH,INCLUDE_NULL_VALUES;')).hexdigest()
            for table, key in [('m_employee', 'employee_id'), ('t_career', 'career_id'), ('m_code_category', 'category_id'), ('m_code', 'category_id,code'), ('m_app_user', 'user_id')]}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None

class Client:
    def __init__(self):
        self.cookies = http.cookiejar.CookieJar()
        # Verification is restricted above to this localhost development host.
        self.opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPCookieProcessor(self.cookies), urllib.request.HTTPSHandler(context=ssl._create_unverified_context()))
    def request(self, path, data=None):
        body = urllib.parse.urlencode(data).encode() if data is not None else None
        headers = {'Content-Type': 'application/x-www-form-urlencoded'} if data is not None else {}
        try:
            with self.opener.open(urllib.request.Request(BASE + path, body, headers), timeout=30) as response:
                return response.status, response.read(), dict(response.headers)
        except urllib.error.HTTPError as error:
            return error.code, error.read(), dict(error.headers)
    def login(self, user):
        status, body, _ = self.request('/account/login')
        assert status == 200, f'Login GET status {status}'
        token = re.search(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"', body.decode())
        assert token, 'Login CSRF token missing'
        status, response, headers = self.request('/account/login', {'LoginId': user, 'Password': '123', '__RequestVerificationToken': html.unescape(token.group(1))})
        message_id = 'HTML-login' if b'id="login-form"' in response else 'other-response'
        if 'application/json' in headers.get('Content-Type', ''):
            message_id = json.loads(response).get('outcome', {}).get('messageId', 'JSON')
        assert status == 303 and headers.get('Location') == '/menu', f'Login POST status {status} {message_id}'
        assert any(cookie.name == '__Host-SP2Auth' and cookie.secure for cookie in self.cookies), 'Authentication cookie missing'

def check(name, action):
    try:
        action()
        checks.append({'id': name, 'status': 'PASS'})
        print('PASS ' + name, flush=True)
    except Exception as error:
        detail = str(error) if isinstance(error, AssertionError) else type(error).__name__
        checks.append({'id': name, 'status': 'FAIL', 'errorType': type(error).__name__, 'detail': detail})
        print('FAIL ' + name + ' ' + detail, flush=True)

def account(user, role, code_status):
    client = Client()
    client.login(user)
    status, body, _ = client.request('/menu')
    assert status == 200
    initial = re.search(r'data-initial="([^"]+)"', body.decode())
    assert initial and json.loads(html.unescape(initial.group(1)))['currentRole'] == role
    assert client.request('/employees')[0] == 200
    assert client.request('/codes')[0] == code_status

try:
    parsed = urllib.parse.urlsplit(BASE)
    assert parsed.scheme == 'https' and parsed.hostname == 'localhost' and parsed.path in ('', '/')
    profile = json.loads((ROOT / '.tmp/runtime/profile.json').read_text('utf-8-sig'))
    database = profile['database']
    assert re.fullmatch(r'SP2_WebFixture_[A-Za-z0-9_]{1,48}', database)
    server_match = re.search(r'(?:^|;)(?:Server|Data Source)\s*=\s*([^;]+)', profile['connectionString'], re.I)
    assert server_match
    server = server_match.group(1).strip()
    assert server.lower() in [r'.\sqlexpress', r'localhost\sqlexpress', r'127.0.0.1\sqlexpress']
    host = json.loads((ROOT/os.environ.get('SP2_LOGIN_HOST_RECORD', '.tmp/vs-debug/host.json')).read_text('utf-8-sig'))
    assert host['port'] == parsed.port and isinstance(host['pid'], int)
    assert hashlib.sha256(Path(host['productFile']).read_bytes()).hexdigest() == host['productSha256']
    assert re.fullmatch(r'[0-9T:.+-]+Z', host['startedAt'])
    live = subprocess.run(['powershell', '-NoProfile', '-Command', f"$sp2DebugProcess=Get-Process -Id {host['pid']} -ErrorAction Stop; if($sp2DebugProcess.StartTime.ToUniversalTime().ToString('o') -cne '{host['startedAt']}'){{exit 2}}; if(-not(Get-NetTCPConnection -LocalPort {parsed.port} -ErrorAction Stop | Where-Object OwningProcess -eq {host['pid']})){{exit 3}}"], capture_output=True)
    assert live.returncode == 0
    record.update(runId=host['runId'], host=host, url=BASE, database=database,
                  inputManifestSha256=hashlib.sha256((ROOT/'build/generation/inputs.json').read_bytes()).hexdigest())
    sql("IF NOT EXISTS(SELECT 1 FROM sys.extended_properties WHERE class=0 AND name=N'SP2Owner' AND CONVERT(nvarchar(200),value)=N'sample-project2/CSharp_ASPNET/SP2-DEMO-01') THROW 51000,'Owner mismatch',1;")
    before = snapshot()
    check('VS-ADMIN-123', lambda: account('admin', 'ADMIN', 200))
    check('VS-STAFF-123', lambda: account('staff', 'STAFF', 403))
    after = snapshot()
    def unchanged():
        assert before == after
    check('VS-EXISTING-DATA-UNCHANGED', unchanged)
    record.update(status='PASS' if all(c['status'] == 'PASS' for c in checks) else 'FAIL',
                  beforeTableDigests=before, afterTableDigests=after)
except Exception as error:
    record.update(status='FAIL', errorType=type(error).__name__)
finally:
    record.update(recordedAtUtc=datetime.now(timezone.utc).isoformat(), checks=checks,
                  testSourceSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  programSha256=hashlib.sha256((ROOT/'src/CareerManagement.Web/Program.cs').read_bytes()).hexdigest(),
                  scope='Explicit localhost HTTPS host; CSRF, authentication cookie, roles, search and code permissions. Five existing tables compared. Launch method is recorded in the host evidence.',
                  notExecuted=['Native browser login/keyboard', 'Full UI conformance', 'Excel/printing', 'Formal acceptance'])
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
raise SystemExit(0 if record['status'] == 'PASS' else 1)
