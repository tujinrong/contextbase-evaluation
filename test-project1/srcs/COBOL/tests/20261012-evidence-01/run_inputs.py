"""Use fictional input files against exact existing production validation binaries."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, subprocess, urllib.parse

BASE = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--report-dir', type=Path, required=True)
args = parser.parse_args()
report = args.report_dir.resolve()
report.mkdir(parents=True, exist_ok=True)
fixture = Path(__file__).with_name('input-fixtures.json')
records = json.loads(fixture.read_text(encoding='utf-8'))['records']
env = os.environ.copy()
env['PATH'] = str(BASE / 'build/toolchain/msys2/ucrt64/bin') + os.pathsep + env.get('PATH', '')
env['COB_CONFIG_DIR'] = 'build/toolchain/msys2/ucrt64/share/gnucobol/config'
for key in ['STUDENT_ODBC_DSN', 'REMOTE_USER', 'ST_LOGIN_SESSION_ID', 'ST_TRUSTED_ROLE', 'STUDENT_STATE_KEY_HEX']:
    env.pop(key, None)
rows = []
log = []
def execute(name, program, arguments, body, expected, environment=None):
    command = [str(BASE / 'build/host' / program), *arguments]
    active = env.copy()
    active.update(environment or {})
    process = subprocess.run(command, input=body, cwd=BASE, env=active, capture_output=True, timeout=30)
    text = process.stdout.decode('utf-8', 'replace').strip()
    error = process.stderr.decode('utf-8', 'replace')
    row = {'id': name, 'command': command, 'stdinUtf8': body.decode('utf-8'),
           'exitCode': process.returncode, 'expected': expected, 'actual': text,
           'passed': process.returncode == 0 and text == expected, 'stderr': error}
    rows.append(row)
    log.append(json.dumps(row, ensure_ascii=False))

base = {'birthEra':'HEISEI','birthYear':'20','birthMonth':'05','birthDay':'15','genderCode':'0',
        'postalCode':'100-0000','prefectureCode':'13','addressLine1':'試験市架空1',
        'phoneNumber':'03-1234-5678','admissionDate':'2026-04-01','enrollmentStatusCode':'01',
        'classId':'1','schoolYear':'2026','gradeCode':'00'}
for row in records:
    fields = {**base, **{key:row[key] for key in ['studentNo','studentName','studentNameKana']}}
    body = urllib.parse.urlencode(fields).encode('ascii')
    execute(row['id']+'-validation', 'validation-probe.exe', [], body,
            '200|00|2026' if row['expectedValid'] else '422',
            {'REQUEST_METHOD':'POST','CONTENT_TYPE':'application/x-www-form-urlencoded',
             'CONTENT_LENGTH':str(len(body)), 'QUERY_STRING':''})
    if row['expectedValid']:
        for field, mode, raw, saved, normalized in [
            ('studentNo',4,15,15,row['normalizedNo']),
            ('studentName',1,8,8,row['studentName']),
            ('studentNameKana',3,36,18,row['normalizedKana'])]:
            execute(row['id']+'-'+field,'boundary-probe.exe',
                    ['unicode','@stdin',str(mode),str(raw),str(saved)],
                    row[field].encode('utf-8'),'0|'+normalized)

result = {'runId':'20261012-evidence-01','profile':'COBOL',
          'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'fixture':str(fixture.relative_to(BASE)), 'fixtureSha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),
          'businessRecordsPersisted':False, 'sqlExecuted':False,
          'syntheticClassIdMeaning':'1 is an unpersisted input hint; no class existence is asserted',
          'binaryHashes':{name:hashlib.sha256((BASE/'build/host'/name).read_bytes()).hexdigest()
                          for name in ['boundary-probe.exe','validation-probe.exe']},
          'passed':sum(row['passed'] for row in rows),'total':len(rows),'results':rows}
with (report/'input-fixture-results.json').open('x',encoding='utf-8') as target:
    target.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
with (report/'input-fixture-results.raw.log').open('x',encoding='utf-8') as target:
    target.write('\n'.join(log)+'\n')
print(str(result['passed'])+'/'+str(result['total'])+' fictional input checks passed')
raise SystemExit(0 if result['passed']==result['total'] else 1)
