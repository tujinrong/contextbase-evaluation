"""Run production HTTP boundaries and real COBOL HTML rendering with fixture candidates.

No database connection is made; rendering fixtures do not prove workflow/state I/O.
"""
from pathlib import Path
import argparse,subprocess,os,json,hashlib,re,urllib.parse
from html.parser import HTMLParser
from evidence import compiled_inputs,binary_hashes,binary_path
from output_paths import result_dir
B=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--report-dir',type=Path);p.add_argument('--run-id',default='current');a=p.parse_args();R=result_dir('compact',a.report_dir)
dest=R/'compact.json'
e=json.loads((B/'.tmp/host/build-evidence.json').read_text('utf8'))
if not e.get('succeeded') or e.get('compiledInputs')!=compiled_inputs() or e.get('binaries')!=binary_hashes():raise SystemExit('Current source/binary mismatch')
env=os.environ.copy();env['PATH']=str(B/'.tmp/toolchain/msys2/ucrt64/bin')+os.pathsep+env.get('PATH','');env['COB_CONFIG_DIR']=str(B/'.tmp/toolchain/msys2/ucrt64/share/gnucobol/config')
checks=[];commands=[]
def check(id,ok,detail=''):checks.append(dict(id=id,passed=bool(ok),detail=detail))
def run(id,exe,args=(),body=None,extra=None):
 command=[str(binary_path(exe)),*args];en=env.copy()
 if body is not None:en.update(REQUEST_METHOD='POST',CONTENT_TYPE='application/x-www-form-urlencoded',CONTENT_LENGTH=str(len(body)),QUERY_STRING='')
 en.update(extra or {})
 x=subprocess.run(command,input=body,env=en,cwd=B,capture_output=True);out=x.stdout.decode('utf8','replace');err=x.stderr.decode('utf8','replace')
 (R/(id+'.log')).write_text('COMMAND '+subprocess.list2cmdline(command)+'\nBODY '+repr(body)+'\nEXIT '+str(x.returncode)+'\nSTDOUT\n'+out+'\nSTDERR\n'+err,'utf8')
 commands.append(dict(id=id,command=command,exitCode=x.returncode));return x.returncode,out
for key in ['studentName','studentNameKana','schoolYear','gradeCode','unassignedOnly','prefectureCode','phoneNumber','admissionFrom','admissionTo','status01','status02','status03','status04','isDeleted','unknown']:
 body=urllib.parse.urlencode(dict(action='SEARCH',**{key:''})).encode();rc,out=run('reject-'+key,'boundary-probe.exe',['http'],body);check('reject-empty-'+key,rc==0 and out.strip()=='-2')
http_cases=[('four',dict(action='SEARCH',studentNo='S',name='見本',classId='1',statusCode=['01','02']),True),('editor',dict(action='UPDATE',studentNameKana='ミホン',schoolYear='2026',gradeCode='00'),True),('search-options',dict(action='OPTIONS',name='見本'),True),('editor-options',dict(action='OPTIONS',editorId='a'*64,studentName='見本'),True),('create',dict(action='CREATE',studentName='見本'),True),('update',dict(action='UPDATE',studentId='1',expectedVersion='1'),True),('unknown-action',dict(action='DOIT'),False),('client-confirm',dict(action='DELETE',confirmed='1'),False),('maintenance-field',dict(action='UPDATE',codeName=''),False),('empty-action',dict(action=''),False),('missing-action',dict(name='見本'),False),('legacy-save',dict(action='SAVE'),False),('legacy-edit-options',dict(action='EDITOPTIONS'),False),('post-new',dict(action='NEW'),False),('post-edit',dict(action='EDIT'),False),('duplicate-status',dict(action='SEARCH',statusCode=['01','01']),False),('undefined-status',dict(action='SEARCH',statusCode='05'),False),('empty-status',dict(action='SEARCH',statusCode=''),False),('csv-status',dict(action='SEARCH',statusCode='01,02'),False)]
for id,fields,good in http_cases:
 body=urllib.parse.urlencode(fields,doseq=True).encode();rc,out=run(id,'boundary-probe.exe',['http'],body);check(id,rc==0 and out.strip()==('0' if good else '-2' if id in ['duplicate-status','undefined-status','empty-status','csv-status'] else '-1'))
for mode,markers in [('stale',['FIX|5|0|0|0','409|Conflict']),('expired',['FIX|5|0|0|0','409|']),('prompt',['FIX|6|1|1|10','200|ActionConfirmation|RESET|6|pending-raw']),('current',['FIX|6|1|1|10','200||DELETE|6|draft-value']),('cancel',['FIX|6|1|1|30','200|PromptCancelled|RESET|6|draft-value']),('unchanged',['FIX|5|0|0|0','200||RESET|5|draft-value']),('background-save',['FIX|5|0|0|0','409|Conflict']),('background-options',['FIX|5|0|0|0','409|Conflict']),('background-reset',['FIX|5|0|0|0','409|Conflict']),('escape-get',['FIX|5|0|0|0','409|Conflict']),('dup-confirm',['FIX|6|1|1|10','200||CONFIRM|6|draft-value']),('dup-cancel',['FIX|6|1|1|30','200||CANCEL|6|draft-value']),('dup-wrong-token',['FIX|5|0|0|0','409|Conflict']),('dup-background',['FIX|5|0|0|0','409|Conflict']),('background-orphan',['FIX|5|0|0|0','409|Conflict']),('recover-cancel',['Status: 422','x'*61,'FIX|7|2|2|30','200||CANCEL|7|draft-value','RECOVERY|-0000000001|CANCEL|']),('recover-correct',['Status: 422','x'*61,'FIX|7|2|2|10','200||CONFIRM|7|draft-value','RECOVERY|-0000000001|CONFIRM|corrected'])]:
 rc,out=run('prompt-'+mode,'prompt-probe.exe',[mode]);check('prompt-'+mode,rc==0 and all(x in out for x in markers),out)
for id,fields,status in [('cgi-create',dict(action='CREATE'),401),('cgi-update',dict(action='UPDATE'),401),('cgi-status',dict(action='SEARCH',statusCode=['01','02']),401),('cgi-post-new',dict(action='NEW'),400),('cgi-empty',dict(action=''),400),('cgi-duplicate-status',dict(action='SEARCH',statusCode=['01','01']),400)]:
 rc,out=run(id,'student.cgi.exe',body=urllib.parse.urlencode(fields,doseq=True).encode(),extra={'REMOTE_USER':''});check(id,rc==0 and f'Status: {status}' in out)
rc,out=run('redirect-no-pii','boundary-probe.exe',['redirect']);location=next((line.strip() for line in out.splitlines() if line.startswith('Location:')),'');keys=set(urllib.parse.parse_qs(urllib.parse.urlsplit(location.removeprefix('Location: ').strip()).query));check('redirect-no-pii',rc==0 and keys=={'action','contextId','tabId','contextRevision','studentId'},location)
for key in ['studentName','schoolYear','status01','unknown']:
 rc,out=run('cgi-search-key-'+key,'student.cgi.exe',body=urllib.parse.urlencode(dict(action='SEARCH',**{key:''})).encode(),extra={'REMOTE_USER':''});check('cgi-search-key-'+key,rc==0 and 'Status: 400' in out and 'E-SRC-002' in out)
class Page(HTMLParser):
 def __init__(self):super().__init__();self.fields=[];self.headers=0;self.editor=False;self.dialog=False;self.basic=False;self.columns=False;self.buttons=[];self.urls=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag in ['input','select','textarea']:self.fields.append(d.get('name'))
  if tag=='button':self.buttons.append(d)
  if d.get('href'):self.urls.append(d['href'])
  if d.get('formaction'):self.urls.append(d['formaction'])
  if tag=='th':self.headers+=1
  if tag=='form' and d.get('class')=='editor':self.editor=True
  if d.get('role')=='dialog':self.dialog=True
  if d.get('class')=='basic-fields':self.basic=True
  if d.get('class')=='editor-columns':self.columns=True
pages={}
for mode in ['search','edit','delete','duplicate','dup-error','delete-error']:
 rc,out=run('render-'+mode,'render-probe.exe',[mode]);check('render-'+mode,rc==0 and ('Status: 422' if mode.endswith('error') else 'Status: 200') in out)
 html=out.split('\r\n\r\n',1)[-1] if '\r\n\r\n' in out else out.split('\n\n',1)[-1];(R/(mode+'.html')).write_text(html,'utf8');page=Page();page.feed(html);pages[mode]=page
for mode in ['dup-error','delete-error']:
 page=pages[mode];html=(R/(mode+'.html')).read_text('utf8');check('reason-error-'+mode,page.dialog and not page.editor and 'x'*61 in html and [b.get('value') for b in page.buttons]==['CANCEL','CONFIRM'] and 'autofocus' in page.buttons[0])
check('post-options-navigation',all('formmethod' not in b for b in pages['search'].buttons) and any('navigation=NEW' in b.get('formaction','') and b.get('value')=='OPTIONS' for b in pages['search'].buttons))
check('no-pii-in-form-urls',all(not ({'name','studentNo','statusCode','studentName'}&set(urllib.parse.parse_qs(urllib.parse.urlsplit(url).query))) for url in pages['search'].urls))
check('editor-candidate-options',any(b.get('value')=='OPTIONS' for b in pages['edit'].buttons) and all(b.get('value')!='EDITOPTIONS' for b in pages['edit'].buttons))
s=pages['search'];check('seven-list-columns',s.headers==7,s.headers)
check('search-only-four-conditions',set(s.fields)-{'contextId','contextRevision','tabId','csrfToken','page','pageSize','sortKey','sortDirection'}=={'studentNo','name','classId','statusCode'},s.fields)
editor={'studentNo','studentName','studentNameKana','birthEra','birthYear','birthMonth','birthDay','genderCode','postalCode','prefectureCode','addressLine1','addressLine2','phoneNumber','emailAddress','admissionDate','enrollmentStatusCode','enrollmentEndDate','classId','emergencyContactName','relationshipCode','emergencyPhoneNumber','remarks','schoolYear','gradeCode','reason'}
check('complete-compact-editor',editor<=set(pages['edit'].fields) and pages['edit'].basic and pages['edit'].columns,sorted(editor-set(pages['edit'].fields)))
check('dedicated-delete-state',pages['delete'].dialog and not pages['delete'].editor and 'deleteReason' in pages['delete'].fields)
check('dedicated-duplicate-state',pages['duplicate'].dialog and not pages['duplicate'].editor and editor<=set(pages['duplicate'].fields))
for sql in sorted((B/'sql').glob('ST-LIST-*.sql')):
 text=sql.read_text('utf8');projection=text[text.index('SELECT '):text.index(' FROM ')]
 check('lean-'+sql.stem,not any(x in projection for x in ['address','phone','updated_at']),projection)
for sql in sorted((B/'sql').glob('ST-*.sql')):
 if sql.stem!='ST-COUNT' and not sql.stem.startswith('ST-LIST-'):continue
 text=sql.read_text('utf8');check('four-predicate-'+sql.stem,all(x not in text for x in ['@kana','@year','@grade','@unassigned','@prefecture','@phone','@from','@to']))
record=dict(runId=a.run_id,scope='Windows production COBOL/C HTTP + HTML fixture lookup + production STPROMPT/STSTATE with isolated state-I/O fixture; no SQL/encryption/real expiry integration/Linux/browser acceptance',formalScore=None,checks=checks,commands=commands,passed=sum(x['passed'] for x in checks),total=len(checks),compiledInputs=compiled_inputs(),binaryHashes=binary_hashes())
dest.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(dict(passed=record['passed'],total=record['total'],failed=[x['id'] for x in checks if not x['passed']]),ensure_ascii=False));raise SystemExit(0 if record['passed']==record['total'] else 1)
