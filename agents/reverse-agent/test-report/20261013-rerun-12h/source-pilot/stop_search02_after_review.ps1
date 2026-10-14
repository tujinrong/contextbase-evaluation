$ErrorActionPreference = 'Stop'
$jobBase = 'D:\開発\contextbase-evaluation\agents\reverse-agent\.tmp\20261013-rerun-12h\source-only\jobs'
$reportBase = 'D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h\source-pilot'
$snapshotManifest = 'D:\開発\contextbase-evaluation\agents\reverse-agent\.tmp\20261013-rerun-12h\source-only\snapshot\manifest.json'
$codexExecutable = 'C:\Users\tujin\AppData\Local\OpenAI\Codex\bin\2e5e00daee91c61d\codex.exe'
$deadline = [DateTimeOffset]::Parse('2026-10-13T20:15:58Z')
$handled = @{}
while ([DateTimeOffset]::UtcNow -lt $deadline) {
    foreach ($jobName in @('search-basic-02', 'search-detail-02')) {
        if ($handled.ContainsKey($jobName)) { continue }
        $job = Join-Path $jobBase $jobName
        $context = Join-Path $job 'round-01\next-round-context.json'
        if (Test-Path -LiteralPath $context) {
            $nextStagePrefix = Join-Path $job 'round-02\'
            $providers = @(Get-CimInstance Win32_Process -Filter "Name = 'codex.exe'" | Where-Object {
                $_.ExecutablePath -eq $codexExecutable -and $_.CommandLine.Contains($nextStagePrefix)
            })
            if ($providers.Count -gt 1) { throw "More than one owned next-round provider found for $jobName" }
            if ($providers.Count -eq 1) {
                $provider = $providers[0]
                $receiptPath = Join-Path $reportBase "$jobName-switch03-interruption.json"
                if (Test-Path -LiteralPath $receiptPath) { throw "Interruption receipt already exists" }
                $draftResult = Join-Path $job 'round-01\draft-result.json'
                $reviewVerified = Join-Path $job 'round-01\independent-review\review-verified.json'
                if (-not (Test-Path -LiteralPath $reviewVerified)) { throw "First-round independent review has not been saved" }
                $receipt = [ordered]@{
                    schema = 'source-pilot-authorized-provider-interruption/1'
                    recordedAt = [DateTimeOffset]::UtcNow.ToString('o')
                    authorization = 'root explicitly authorized new round interruption after saved R1 review for runtime03 format clarification and analysis checkpoint reuse'
                    job = $job
                    reason = 'Preserve R1 AI analysis, draft and independent review; avoid repeating source analysis while switching a fresh AI manuscript to frozen runtime03'
                    processId = $provider.ProcessId
                    parentProcessId = $provider.ParentProcessId
                    executable = $provider.ExecutablePath
                    commandLine = $provider.CommandLine
                    snapshotManifestSha256 = (Get-FileHash -LiteralPath $snapshotManifest -Algorithm SHA256).Hash.ToLowerInvariant()
                    draftResultSha256 = (Get-FileHash -LiteralPath $draftResult -Algorithm SHA256).Hash.ToLowerInvariant()
                    reviewVerifiedSha256 = (Get-FileHash -LiteralPath $reviewVerified -Algorithm SHA256).Hash.ToLowerInvariant()
                    nextRoundContextSha256 = (Get-FileHash -LiteralPath $context -Algorithm SHA256).Hash.ToLowerInvariant()
                    action = 'Stop-Process on the exact next-round codex provider PID only; original application source and R1 artifacts preserved'
                }
                $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receiptPath -Encoding utf8NoBOM -NoNewline
                Stop-Process -Id $provider.ProcessId -Force
                [ordered]@{job=$jobName; stoppedProcessId=$provider.ProcessId; receipt=$receiptPath} | ConvertTo-Json -Compress
                $handled[$jobName] = $true
            }
        }
        $iterationResult = Join-Path $job 'iteration-result.json'
        if (Test-Path -LiteralPath $iterationResult) {
            $handled[$jobName] = $true
        }
    }
    if ($handled.Count -eq 2) { break }
    Start-Sleep -Seconds 2
}
