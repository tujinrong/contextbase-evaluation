"""Loopback evidence host for unchanged production CGI error screens; never connects to SQL."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit
import argparse,datetime,hashlib,json,mimetypes,os,re,subprocess,threading

BASE=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--report-dir',type=Path,required=True)
parser.add_argument('--port',type=int,default=0)
args=parser.parse_args()
REPORT=args.report_dir.resolve()
REPORT.mkdir(parents=True,exist_ok=True)
binary=BASE/'build/host/student.cgi.exe'
lock=threading.Lock()
sequence=0
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def validate_binary():
    import sys
    sys.path.insert(0,str(BASE/'tools'))
    from evidence import compiled_inputs,binary_hashes
    proof=json.loads((BASE/'build/host/build-evidence.json').read_text(encoding='utf-8'))
    if not proof.get('succeeded') or proof['compiledInputs']!=compiled_inputs() or proof['binaries']!=binary_hashes():
        raise RuntimeError('Existing CGI/source build proof mismatch')
validate_binary()
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global sequence
        parsed=urlsplit(self.path)
        if parsed.path.startswith('/student-assets/'):
            asset=(BASE/'assets'/parsed.path.removeprefix('/student-assets/')).resolve()
            if not asset.is_relative_to((BASE/'assets').resolve()) or not asset.is_file():
                self.send_error(404);return
            body=asset.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type',mimetypes.guess_type(asset.name)[0] or 'application/octet-stream')
            self.send_header('Content-Length',str(len(body)))
            self.end_headers();self.wfile.write(body);return
        if parsed.path!='/student.cgi' or parsed.query not in ['action=INITIAL','role=Administrator']:
            self.send_error(404,'Only two DB-free error evidence requests are enabled');return
        validate_binary()
        environment=os.environ.copy()
        for key in ['REMOTE_USER','ST_LOGIN_SESSION_ID','ST_TRUSTED_ROLE','STUDENT_STATE_KEY_HEX',
                    'STUDENT_ODBC_DSN','CONTENT_TYPE','CONTENT_LENGTH']:
            environment.pop(key,None)
        # An empty authenticated owner forces STAUTH failure before STCONNECT.
        environment.update(REQUEST_METHOD='GET',QUERY_STRING=parsed.query,REMOTE_USER='',
                           STUDENT_RENDER_DIR=str(REPORT/'render-temp'))
        environment['PATH']=str(BASE/'build/toolchain/msys2/ucrt64/bin')+os.pathsep+environment.get('PATH','')
        environment['COB_CONFIG_DIR']='build/toolchain/msys2/ucrt64/share/gnucobol/config'
        (REPORT/'render-temp').mkdir(exist_ok=True)
        process=subprocess.run([str(binary)],input=b'',cwd=BASE,env=environment,capture_output=True,timeout=20)
        # Windows text-mode stdout expands the production CGI's CRLF to CRCRLF.
        # Parse only the transport separator; preserve the emitted HTML body bytes.
        parts=re.split(rb'\r*\n\r*\n',process.stdout,maxsplit=1)
        header=parts[0];separator=len(parts)==2;body=parts[1] if separator else b''
        status=502;headers={}
        if separator:
            for line in header.decode('utf-8','replace').splitlines():
                name,_,value=line.partition(':')
                if name.lower()=='status':status=int(value.strip().split()[0])
                elif name:headers[name]=value.strip()
        expected=401 if parsed.query=='action=INITIAL' else 400
        passed=process.returncode==0 and status==expected and b'<!doctype html>' in body
        with lock:
            sequence+=1;stem=REPORT/f'cgi-http-{sequence:03d}'
            stem.with_suffix('.raw.log').open('xb').write(process.stdout+b'\nSTDERR\n'+process.stderr)
            stem.with_suffix('.html').open('xb').write(body)
            record={'runId':'20261012-evidence-01','request':self.path,'command':[str(binary)],
                    'binarySha256':digest(binary),'exitCode':process.returncode,'status':status,
                    'expectedStatus':expected,'passed':passed,'sqlExecuted':False,
                    'authentication':'Intentionally empty owner; production STAUTH rejects before STCONNECT',
                    'capturableScreen':'Production CGI authentication/request error only; not student CRUD UI',
                    'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
            stem.with_suffix('.json').open('x',encoding='utf-8').write(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
        self.send_response(status)
        for name,value in headers.items():
            if name.lower() not in ['content-length','connection','status']:
                self.send_header(name,value)
        self.send_header('Content-Length',str(len(body)))
        self.end_headers();self.wfile.write(body)
    def do_POST(self):self.send_error(405,'No DB-capable requests are enabled')

server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
info={'runId':'20261012-evidence-01','pid':os.getpid(),'address':server.server_address,
      'url':f'http://127.0.0.1:{server.server_port}/student.cgi?action=INITIAL',
      'malformedUrl':f'http://127.0.0.1:{server.server_port}/student.cgi?role=Administrator',
      'binary':str(binary),'binarySha256':digest(binary),'sqlAccessEnabled':False,
      'screens':'Real production CGI 401/400 HTML, no business data or 200 student form'}
with (REPORT/'cgi-host.json').open('x',encoding='utf-8') as target:
    target.write(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(info,ensure_ascii=False),flush=True)
server.serve_forever()
