$ErrorActionPreference = 'Stop'
$runDirectory = $PSScriptRoot
$target = Join-Path $runDirectory 'close-verification.json'
if (Test-Path -LiteralPath $target) { throw 'Existing closure verification must not be overwritten.' }
$ports = @(7441, 7442, 49191)
$listeners = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $ports -contains $_.LocalPort } | Select-Object LocalAddress, LocalPort, OwningProcess)
$closed = Get-Content -LiteralPath (Join-Path $runDirectory 'Access-ui-r6-screen/ui-closed.json') -Raw | ConvertFrom-Json
$r6 = Get-Content -LiteralPath (Join-Path $runDirectory 'Access-r6/results.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$projectDirectory = (Resolve-Path -LiteralPath (Join-Path $runDirectory '../..')).Path
$original = Join-Path $projectDirectory 'srcs/Access/StudentManagement.accdb'
$actualHash = (Get-FileHash -LiteralPath $original -Algorithm SHA256).Hash
$expectedHash = 'D1777167FD7423BF4399F05D006519FD5A8E005A6FEF2E56B1A8F11AAD73EC87'
$passed = $listeners.Count -eq 0 -and $closed.originalUnchanged -eq $true -and $closed.originalSha256 -ceq $expectedHash -and $actualHash -ceq $expectedHash
$record = [ordered]@{
    projectId = 'test-project1'
    runId = '20261012-evidence-01'
    verifiedAt = [DateTimeOffset]::UtcNow.ToString('o')
    status = $(if ($passed) { 'PASS' } else { 'FAIL' })
    verificationOnly = $true
    stoppedAnyAdditionalProcess = $false
    evidenceHostPorts = $ports
    listeningEvidenceHosts = $listeners
    accessGuiClosed = $true
    accessGuiClosureRecord = 'Access-ui-r6-screen/ui-closed.json'
    accessProductionUnchangedByGui = $closed.originalUnchanged
    accessProductionSha256 = $actualHash
    productionSha256MatchesR6 = $actualHash -ceq $expectedHash
    finalScreenshot = 'Access/09-invalid-date-after-final-fix.jpg'
    manualObservation = [ordered]@{
        action = 'Clicked Save on the actual empty production new-student form in the disposable R6 ACE fixture.'
        actualMessage = $r6.exactDateMessage
        middleDotCount = 3
        rootVerifiedExactAccessibilityText = $true
        rootInspectedActualScreenshot = $true
        sharedSqlConnected = $false
        successfulStudentSaveTestedByScreenshot = $false
    }
}
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $target -Encoding UTF8
if (-not $passed) { throw 'Closure or final Access original verification failed; see close-verification.json.' }
$record | ConvertTo-Json -Depth 8 -Compress
