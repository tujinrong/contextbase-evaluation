[CmdletBinding()]
param([ValidatePattern('^[A-Za-z0-9_-]+$')][string]$DsnName='contextbase_test_project1_cobol',
      [string]$ReportDirectory,
      [ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId=('cobol-sql-smoke-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N')),
      [switch]$Execute)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=(Get-Item -LiteralPath (Join-Path $PSScriptRoot '../..')).FullName
if (-not $Execute) { Write-Output 'PLAN_ONLY: compiled COBOL CGI INITIAL GET; writes encrypted technical search state, never creates a class/student/audit sample.';return }
if (-not [Environment]::Is64BitProcess) { throw '64-bit Windows PowerShell is required.' }
if ([string]::IsNullOrWhiteSpace($ReportDirectory)) { $ReportDirectory=Join-Path $root 'test-report' }
[void][IO.Directory]::CreateDirectory($ReportDirectory)
$prefix=Join-Path $ReportDirectory $RunId
foreach($suffix in @('.json','.raw.log')) { if (Test-Path -LiteralPath ($prefix+$suffix)) { throw 'Existing evidence must not be overwritten.' } }
$binary=Join-Path $root 'build/host/student.cgi.exe'
$buildEvidence=Get-Content -LiteralPath (Join-Path $root 'build/host/build-evidence.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $buildEvidence.succeeded) { throw 'No successful compiled source evidence.' }
foreach($entry in $buildEvidence.compiledInputs.PSObject.Properties) {
    if ((Get-FileHash -LiteralPath (Join-Path $root $entry.Name) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value) { throw "Compiled input mismatch: $($entry.Name)" }
}
$binaryHash=(Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash.ToLowerInvariant()
if ($binaryHash -ne $buildEvidence.binaries.'student.cgi.exe') { throw 'Compiled CGI binary mismatch.' }
$start=New-Object Diagnostics.ProcessStartInfo
$start.FileName=$binary; $start.WorkingDirectory=$root; $start.UseShellExecute=$false
$start.RedirectStandardOutput=$true; $start.RedirectStandardError=$true
$start.StandardOutputEncoding=New-Object Text.UTF8Encoding $false
$start.StandardErrorEncoding=New-Object Text.UTF8Encoding $false
$start.EnvironmentVariables['PATH']=(Join-Path $root 'build/toolchain/msys2/ucrt64/bin')+';'+$env:PATH
$start.EnvironmentVariables['COB_CONFIG_DIR']='build/toolchain/msys2/ucrt64/share/gnucobol/config'
$start.EnvironmentVariables['STUDENT_ODBC_DSN']=$DsnName
$start.EnvironmentVariables['REMOTE_USER']='cobol-local-smoke'
$start.EnvironmentVariables['ST_LOGIN_SESSION_ID']=[Guid]::NewGuid().ToString('N')
$start.EnvironmentVariables['ST_TRUSTED_ROLE']='Viewer'
$start.EnvironmentVariables['REQUEST_METHOD']='GET'
$start.EnvironmentVariables['QUERY_STRING']='action=INITIAL'
$key=New-Object byte[] 32; $rng=[Security.Cryptography.RandomNumberGenerator]::Create()
try { $rng.GetBytes($key) } finally { $rng.Dispose() }
$start.EnvironmentVariables['STUDENT_STATE_KEY_HEX']=([BitConverter]::ToString($key)).Replace('-','').ToLowerInvariant()
[Array]::Clear($key,0,$key.Length)
$process=New-Object Diagnostics.Process; $process.StartInfo=$start
try {
    [void]$process.Start()
    $stdout=$process.StandardOutput.ReadToEndAsync(); $stderr=$process.StandardError.ReadToEndAsync()
    if (-not $process.WaitForExit(60000)) { $process.Kill(); throw 'CGI timed out after 60 seconds.' }
    $out=$stdout.GetAwaiter().GetResult(); $err=$stderr.GetAwaiter().GetResult()
    $passed=$process.ExitCode -eq 0 -and $out.StartsWith("Status: 200`r`n") -and $out -match '<form' -and $out -match 'csrfToken'
    [IO.File]::WriteAllText($prefix+'.raw.log',"COMMAND $binary (GET action=INITIAL)`r`nSTDOUT`r`n$out`r`nSTDERR`r`n$err",(New-Object Text.UTF8Encoding $false))
    $result=[ordered]@{runId=$RunId;recordedAt=[DateTime]::UtcNow.ToString('o');database='contextbase_test_project1_cobol';dsn=$DsnName;scope='Windows compiled production CGI initial search screen + live ODBC; no web server/browser';binary=$binary;binarySha256=$binaryHash;buildRecord=$buildEvidence.buildRecord;exitCode=$process.ExitCode;passed=$passed;businessSamplesCreated=$false;technicalStateWritesExpected=$true;notExecuted=@('student save/update/delete','master maintenance','duplicate confirmation','concurrency','audit rollback','Linux CGI deployment')}
    [IO.File]::WriteAllText($prefix+'.json',($result|ConvertTo-Json -Depth 6),(New-Object Text.UTF8Encoding $false))
    if (-not $passed) { throw "Compiled CGI smoke test failed; inspect $prefix.raw.log" }
    Write-Output "PASS $prefix.json"
} finally { $start.EnvironmentVariables.Remove('STUDENT_STATE_KEY_HEX');$process.Dispose() }
