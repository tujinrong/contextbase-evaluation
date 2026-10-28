param()
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../tools/GeneratedPaths.ps1')
$taskRoot=$script:AccessMethodRoot
$taskFinal=Join-Path $taskRoot 'build/StudentManagement.accdb'
$taskBefore=(Get-FileHash -LiteralPath $taskFinal -Algorithm SHA256).Hash
$taskResults=New-Object 'Collections.Generic.List[object]'
function Test-RefusedPath([string]$Name,[string]$ExpectedMessage,[scriptblock]$Operation) {
    $taskRefused=$false
    $taskMessage=''
    try { & $Operation | Out-Null } catch { $taskMessage=$_.Exception.Message;$taskRefused=$taskMessage.Contains($ExpectedMessage) }
    $taskResults.Add([ordered]@{name=$Name;passed=$taskRefused;message=$taskMessage})
}
Test-RefusedPath 'fixture traversal outside .tmp' 'Generated path must stay' { Resolve-AccessGeneratedPath (Join-Path $taskRoot '.tmp/../outside.accdb') '.tmp' }
Test-RefusedPath 'similar prefix is outside .tmp' 'Generated path must stay' { Resolve-AccessGeneratedPath (Join-Path $taskRoot '.tmp-other/fixture.accdb') '.tmp' }
Test-RefusedPath 'report outside generated areas' 'Generated path must stay' { Resolve-AccessReportPath (Join-Path $taskRoot 'tests/results') }
Test-RefusedPath 'intermediate root cannot be removed' 'Cannot remove the intermediate root.' { Remove-AccessIntermediate (Join-Path $taskRoot '.tmp') }
Test-RefusedPath 'final cannot contain test modules' 'Test modules belong' { & (Join-Path $taskRoot 'Build-Access.ps1') -IncludeTests }
Test-RefusedPath 'generator cannot publish arbitrary build output' 'Generated path must stay' { & (Join-Path $taskRoot 'Build-Access.ps1') -Frontend (Join-Path $taskRoot 'build/other.accdb') }
Test-RefusedPath 'generator cannot use external backend' 'Generated path must stay' { & (Join-Path $taskRoot 'Build-Access.ps1') -Backend (Join-Path $taskRoot '../outside.accdb') }
$taskAfter=(Get-FileHash -LiteralPath $taskFinal -Algorithm SHA256).Hash
$taskResults.Add([ordered]@{name='invalid requests preserve final artifact';passed=$taskBefore -eq $taskAfter;message=''})
$taskPassed=@($taskResults|Where-Object {-not $_.passed}).Count -eq 0
[ordered]@{status=$(if($taskPassed){'Passed'}else{'Failed'});completedAt=[DateTime]::UtcNow.ToString('o');checks=$taskResults;sourceBeforeSha256=$taskBefore;sourceAfterSha256=$taskAfter;nativeAccessOpened=$false} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Resolve-AccessReportPath (Join-Path $taskRoot 'build/test-results/path-validation.json')) -Encoding UTF8
if(-not $taskPassed){throw 'Generated path validation failed.'}
Write-Output "$($taskResults.Count) generated path checks passed."
