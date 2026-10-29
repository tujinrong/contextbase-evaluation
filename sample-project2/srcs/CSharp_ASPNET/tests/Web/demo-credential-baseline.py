"""Capture only the explicitly configured legacy DEMO credential baseline, read-only.

No authentication attempts or counters are changed. Verifiers/passwords stay
in memory; the output contains only identity/role and verification booleans.
"""
from pathlib import Path
from datetime import datetime, timezone
import base64, hashlib, hmac, json, struct, subprocess

root=Path(__file__).resolve().parents[2]
profile_path=root/'.tmp/runtime/profile.json'
profile=json.loads(profile_path.read_text('utf-8-sig'))
assert profile['database']=='SP2_WebFixture_20261029' and profile['url']=='https://localhost:7443'
query="""SET NOCOUNT ON;
IF NOT EXISTS(SELECT 1 FROM sys.extended_properties WHERE class=0 AND name=N'SP2Owner' AND CONVERT(nvarchar(200),value)=N'sample-project2/CSharp_ASPNET/SP2-DEMO-01') THROW 51000,'Owner mismatch',1;
SELECT user_id,login_id,role_id,password_verifier FROM dbo.m_app_user WHERE user_id IN(N'SP2ADMIN',N'SP2STAFF') ORDER BY user_id;"""
result=subprocess.run(['C:/Program Files/Microsoft SQL Server/Client SDK/ODBC/180/Tools/Binn/SQLCMD.EXE','-S','.\\SQLEXPRESS','-E','-C','-b','-W','-h','-1','-s','|','-d',profile['database'],'-Q',query],capture_output=True,check=True)
rows=[]
for line in result.stdout.decode('utf-8','replace').splitlines():
    values=[v.strip() for v in line.split('|')]
    if len(values)!=4:continue
    identity,login,role,verifier=values
    if identity not in ['SP2ADMIN','SP2STAFF']:continue
    encoded=base64.b64decode(verifier,validate=True)
    assert encoded[0]==1
    prf,iterations,salt_length=struct.unpack('>III',encoded[1:13])
    salt=encoded[13:13+salt_length];expected=encoded[13+salt_length:]
    algorithm={0:'sha1',1:'sha256',2:'sha512'}[prf]
    password=profile['adminPassword' if identity=='SP2ADMIN' else 'staffPassword']
    matched=hmac.compare_digest(hashlib.pbkdf2_hmac(algorithm,password.encode(),salt,iterations,len(expected)),expected)
    assert matched and iterations==100000 and salt_length>=16
    rows.append({'userId':identity,'priorLoginId':login,'roleId':role,'profilePasswordMatchedDatabaseBeforeMigration':matched,'identityFormat':'V3','iterations':iterations,'saltBytes':salt_length,'priorVerifierSha256':hashlib.sha256(verifier.encode()).hexdigest()})
assert len(rows)==2
record={'recordedAtUtc':datetime.now(timezone.utc).isoformat(),'database':profile['database'],'ownerMatched':True,'readOnly':True,'authenticationAttempts':0,'accounts':rows,'sourceSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Existing explicitly configured DEMO before migration. Neither verifiers nor passwords are recorded.'}
output=root/'.tmp/credentials-change/baseline.json';output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'BASELINE_MATCHED','accounts':len(rows),'database':profile['database'],'dbWrites':0}))
