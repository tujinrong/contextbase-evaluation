"""Verify the configured SQL login from the Windows App Service worker via authenticated SCM."""
import base64
import json
from pathlib import Path
import subprocess
import urllib.request

state = json.loads((Path(__file__).resolve().parent.parent / 'build/azure-free-state/resources.json').read_text(encoding='utf-8-sig'))
token = json.loads(subprocess.check_output(['az.cmd', 'account', 'get-access-token', '--subscription', state['subscription'], '--resource', 'https://management.azure.com/', '-o', 'json'], text=True))['accessToken']
script = r"""
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
Add-Type -AssemblyName System.Data
$connectionString=$env:ConnectionStrings__StudentDb
if(-not $connectionString){$connectionString=$env:APPSETTING_ConnectionStrings__StudentDb}
if(-not $connectionString){throw 'Database app setting is missing from worker environment.'}
$connection=[System.Data.SqlClient.SqlConnection]::new($connectionString)
try {
 $connection.Open()
 $command=$connection.CreateCommand()
 $command.CommandText="SELECT (SELECT COUNT(*) FROM dbo.m_code),(SELECT COUNT(*) FROM dbo.m_student),IS_ROLEMEMBER('student_staff'),IS_ROLEMEMBER('db_owner')"
 $reader=$command.ExecuteReader()
 if(-not $reader.Read()){throw 'No database verification result.'}
 if($reader.GetInt32(0)-ne 70 -or $reader.GetInt32(1)-ne 0 -or $reader.GetInt32(2)-ne 1 -or $reader.GetInt32(3)-ne 0){throw 'Unexpected database contents or permissions.'}
 Write-Output 'PASS: Azure worker connected with configured SQL login; 70 codes, 0 students, student_staff role, no db_owner.'
} finally {$connection.Dispose()}
"""
encoded = base64.b64encode(script.encode('utf-16-le')).decode()
body = json.dumps({'command': f'powershell.exe -NoProfile -NonInteractive -EncodedCommand {encoded}', 'dir': 'D:\\home'}).encode()
request = urllib.request.Request(f"https://{state['app']}.scm.azurewebsites.net/api/command", data=body, headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
with urllib.request.urlopen(request, timeout=150) as response:
    result = json.load(response)
print(json.dumps(result))
if result.get('ExitCode') != 0:
    raise SystemExit('Remote Azure SQL verification failed.')
