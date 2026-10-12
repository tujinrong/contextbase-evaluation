"""Run compiled production boundary/date programs, never replace SQL with a fake DB."""
from pathlib import Path
import os,sys,subprocess,json,datetime,hashlib,urllib.parse
from evidence import compiled_inputs,binary_hashes
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
report=Path(os.environ.get('COBOL_TEST_REPORT_DIR',ROOT/'test-report')).resolve()
report.mkdir(parents=True,exist_ok=True)
prefix=report/f'20261012-build-04-cobol-{sys.argv[1]}-host-tests'
if prefix.with_suffix('.json').exists():raise RuntimeError('Evidence already exists')
compiled=json.loads((ROOT/'build/host/build-evidence.json').read_text(encoding='utf-8'))
if not compiled.get('succeeded') or compiled.get('compiledInputs')!=compiled_inputs() or compiled.get('binaries')!=binary_hashes():
 prefix.with_suffix('.raw.log').write_text('ABORT: binaries do not prove a successful build of these exact source inputs.\n',encoding='utf-8')
 prefix.with_suffix('.json').write_text(json.dumps({'runId':'20261012-build-04','status':'ABORT_SOURCE_OR_BUILD_MISMATCH','passed':0,'total':0},indent=2)+'\n',encoding='utf-8')
 raise SystemExit('Build/source/binary mismatch; tests not executed.')
env=os.environ.copy();env['PATH']=str(ROOT/'build/toolchain/msys2/ucrt64/bin')+os.pathsep+env.get('PATH','')
env['COB_CONFIG_DIR']='build/toolchain/msys2/ucrt64/share/gnucobol/config'
rows=[];log=[]
def case(name,args,expected=None,stdin=b'',extra=None,contains=None):
 e=env.copy();e.update(extra or {})
 p=subprocess.run([str(ROOT/'build/host'/args[0]),*args[1:]],input=stdin,env=e,capture_output=True)
 out=p.stdout.decode('utf-8','replace').replace('\r\n','\n').rstrip('\n')
 passed=p.returncode==0 and (expected is None or out==expected) and (contains is None or all(x in out for x in contains))
 rows.append({'id':name,'passed':passed,'exitCode':p.returncode,'expected':expected,'output':out,'stderr':p.stderr.decode('utf-8','replace')})
 log.append(name+' '+('PASS' if passed else 'FAIL')+'\n'+out+'\n'+p.stderr.decode('utf-8','replace'))
 print(name,'PASS' if passed else 'FAIL',flush=True)
case('ABI-01',['abi-probe.exe'],contains=['PASS COPY C pointer int32 int64 NULL roundtrip'])
dates=[('MEIJI','33','01','01','1900-01-01'),('MEIJI','32','12','31','INVALID'),
 ('TAISHO','GAN','07','29','INVALID'),('TAISHO','GAN','07','30','1912-07-30'),
 ('TAISHO','15','12','24','1926-12-24'),('TAISHO','15','12','25','INVALID'),
 ('SHOWA','GAN','12','24','INVALID'),('SHOWA','GAN','12','25','1926-12-25'),
 ('SHOWA','64','01','07','1989-01-07'),('SHOWA','64','01','08','INVALID'),
 ('HEISEI','GAN','01','07','INVALID'),('HEISEI','GAN','01','08','1989-01-08'),
 ('HEISEI','31','04','30','2019-04-30'),('HEISEI','31','05','01','INVALID'),
 ('REIWA','GAN','04','30','INVALID'),('REIWA','GAN','05','01','2019-05-01'),
 ('REIWA','0','05','01','INVALID'),('REIWA','-1','05','01','INVALID'),
 ('REIWA','99999','05','01','INVALID'),('OTHER','1','01','01','INVALID'),
 ('HEISEI','12','02','29','2000-02-29'),('HEISEI','13','02','29','INVALID'),
 ('REIWA','8','10','10','2026-10-10'),('REIWA','8','10','11','INVALID'),
 ('REIWA','9','01','01','INVALID'),('REIWA','8','04','31','INVALID')]
for i,(era,year,month,day,expected) in enumerate(dates,1):
 case(f'DATE-{i:02}', ['date-probe.exe',era,year,month,day,'2026-10-10',expected],contains=['PASS '+expected])
for raw,expected in [('0','0|0'),('9223372036854775807','0|9223372036854775807'),('9223372036854775808','-1|0'),('-1','-1|0'),('1x','-1|0'),('１２','-1|0')]:
 case('INTEGER-'+raw,['boundary-probe.exe','integer','@stdin'],expected,raw.encode())
vectors=[('ａ１２-',4,15,15,'A12-'),('ﾊﾟ'*18,3,36,18,'パ'*18),('やまだ　たろう',3,36,18,'ヤマダ タロウ'),
 ('　Ａ　Ｂ　',2,8,160,'AB'),('ﬃ',2,8,160,'FFI'),('😀'*8,1,8,8,'😀'*8),('😀'*9,1,8,8,None),
 ('（０９０）１２３４－５６７８',7,20,16,'09012345678'),('１２３－４５６７',6,10,7,'1234567'),
 ('a\nb',1,8,8,None),('a\r\nb',8,120,120,'a\nb'),('abcde',1,4,4,None)]
for i,(raw,mode,rmax,smax,normalized) in enumerate(vectors,1):
 case(f'UNICODE-{i:02}',['boundary-probe.exe','unicode','@stdin',str(mode),str(rmax),str(smax)],'-1|' if normalized is None else '0|'+normalized,raw.encode())
case('LIKE-01',['boundary-probe.exe','pattern','!%_[','0'],'0|%!!!%!_![%')
case('LIKE-02',['boundary-probe.exe','pattern','AB','1'],'0|AB%')
for raw,expected in [('a'*64,'0'),('x'*64,'-1'),('a'*63,'-1')]:case('HEX-'+raw[0]+str(len(raw)),['boundary-probe.exe','hex',raw],expected)
forms=[('valid',b'action=SEARCH',0,None),('duplicate',b'action=SEARCH&action=SEARCH',-1,None),
 ('bad-percent',b'studentName=%Q1',-1,None),('bad-utf8',b'studentName=%FF',-1,None),('nul',b'studentName=%00',-1,None),
 ('unknown',b'role=Administrator',-1,None),('short',b'action=SEARCH',-1,20),('excess',b'action=SEARCH',-1,5),
 ('length-limit',b'',-1,65537),('encoded-japanese',b'studentName=%E5%B1%B1%E7%94%B0',0,None)]
for name,body,rc,length in forms:
 case('HTTP-'+name,['boundary-probe.exe','http'],str(rc),body,{'REQUEST_METHOD':'POST','CONTENT_TYPE':'application/x-www-form-urlencoded','CONTENT_LENGTH':str(len(body) if length is None else length),'QUERY_STRING':''})
case('HTTP-query-body-duplicate',['boundary-probe.exe','http'],'-1',b'action=SEARCH',{'REQUEST_METHOD':'POST','CONTENT_TYPE':'application/x-www-form-urlencoded','CONTENT_LENGTH':'13','QUERY_STRING':'action=SEARCH'})
case('CGI-unauthenticated',['student.cgi.exe'],extra={'REQUEST_METHOD':'GET','QUERY_STRING':'action=INITIAL','REMOTE_USER':''},contains=['Status: 401','Cache-Control: no-store','E-COM-001'])
case('CGI-malformed',['student.cgi.exe'],extra={'REQUEST_METHOD':'GET','QUERY_STRING':'role=Administrator'},contains=['Status: 400','E-COM-003'])
base={'studentNo':'S2026-1','studentName':'見本太郎','studentNameKana':'ミホンタロウ','birthEra':'HEISEI','birthYear':'20','birthMonth':'05','birthDay':'15','genderCode':'0','postalCode':'100-0000','prefectureCode':'13','addressLine1':'見本市1','phoneNumber':'03-1234-5678','admissionDate':'2026-04-01','enrollmentStatusCode':'01','classId':'1','schoolYear':'2026','gradeCode':'00'}
vectors=[('valid',{},'200|00|2026'),('fullwidth-hints',{'gradeCode':'００','schoolYear':'２０２６'},'200|00|2026'),('missing-name',{'studentName':''},'422'),('kana-hiragana',{'studentNameKana':'みほんたろう'},'200|00|2026'),('missing-birth',{'birthEra':''},'422'),('birth-after-admission',{'birthEra':'REIWA','birthYear':'8','birthMonth':'05','birthDay':'01'},'422'),('invalid-grade-length',{'gradeCode':'0'},'422'),('invalid-grade-letters',{'gradeCode':'AB'},'422'),('year-low',{'schoolYear':'1899'},'422'),('year-high',{'schoolYear':'9999'},'422'),('year-letters',{'schoolYear':'2x26'},'422'),('end-active',{'enrollmentEndDate':'2026-10-01'},'422'),('no-active-class',{'classId':''},'422'),('graduated-end',{'enrollmentStatusCode':'03','enrollmentEndDate':'2026-10-01','classId':''},'200|00|2026'),('graduated-no-end',{'enrollmentStatusCode':'03'},'422'),('no-contacts',{'phoneNumber':''},'422'),('partial-emergency',{'emergencyContactName':'見本保護者'},'422'),('complete-emergency',{'emergencyContactName':'見本保護者','relationshipCode':'01','emergencyPhoneNumber':'090-1234-5678'},'200|00|2026'),('bad-phone',{'phoneNumber':'1'},'422'),('bad-mail',{'emailAddress':'a b@c.example'},'422'),('bad-class',{'classId':'x'},'422'),('bad-number',{'studentNo':'-ABC'},'422'),('supplementary-name',{'studentName':'😀'*8},'200|00|2026')]
for name,changes,expected in vectors:
 fields=base.copy();fields.update(changes);body=urllib.parse.urlencode(fields).encode('ascii')
 case('VALIDATION-'+name,['validation-probe.exe'],expected,body,{'REQUEST_METHOD':'POST','CONTENT_TYPE':'application/x-www-form-urlencoded','CONTENT_LENGTH':str(len(body)),'QUERY_STRING':''})
sources=[p for folder in ['cobol','copy','bridge','sql','assets','database'] for p in sorted((ROOT/folder).rglob('*')) if p.is_file()]
result={'runId':'20261012-build-04','inputManifest':'build/input-manifest.json','inputManifestSha256':hashlib.sha256((ROOT/'build/input-manifest.json').read_bytes()).hexdigest(),'sourceHashes':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'profile':'Windows x64, compiled production COBOL/C boundaries; Linux and live SQL Server not tested','passed':sum(x['passed'] for x in rows),'total':len(rows),'results':rows}
prefix.with_suffix('.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
prefix.with_suffix('.raw.log').write_text('\n'.join(log),encoding='utf-8')
print(f"{result['passed']}/{result['total']} passed")
raise SystemExit(0 if result['passed']==result['total'] else 1)
