$ErrorActionPreference='Stop'
$repoRoot=[IO.Path]::GetFullPath((Get-Location).Path)
$reportRoot=Join-Path $repoRoot 'agents/reverse-agent/test-report/20261013-session-pilot-01'
$baselinePath=Join-Path $reportRoot 'protected-before.json'
$outputPath=Join-Path $reportRoot 'focus-protected-check-06-native-preparation-01.json'
if(Test-Path -LiteralPath $outputPath){throw 'Independent protected record already exists; preserve it'}
$baselineSha=(Get-FileHash -LiteralPath $baselinePath -Algorithm SHA256).Hash.ToLowerInvariant()
$baseline=Get-Content -LiteralPath $baselinePath -Raw | ConvertFrom-Json
if($baseline.Count -ne 179 -or ($baseline.path | Select-Object -Unique).Count -ne 179){throw 'Expected 179 distinct protected pins'}
$results=@(foreach($entry in $baseline){
    $target=[IO.Path]::GetFullPath($entry.path)
    if(-not $target.StartsWith($repoRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Protected hash target outside named workspace'}
    if(-not (Test-Path -LiteralPath $target -PathType Leaf)){
        [ordered]@{path=$target;expectedSha256=$entry.sha256;currentSha256=$null;status='MISSING'}
    }else{
        $current=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
        [ordered]@{path=$target;expectedSha256=$entry.sha256;currentSha256=$current;status=$(if($current -eq $entry.sha256){'UNCHANGED'}else{'CHANGED'})}
    }
})
if((Get-FileHash -LiteralPath $baselinePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $baselineSha){throw 'Protected baseline changed during check'}
$unchanged=@($results | Where-Object status -eq 'UNCHANGED').Count
$changed=@($results | Where-Object status -eq 'CHANGED').Count
$missing=@($results | Where-Object status -eq 'MISSING').Count
$record=[ordered]@{schema='reverse-independent-protected-sha-check/1';checkedAt=[DateTimeOffset]::UtcNow.ToString('o');round=6;phase='NATIVE_REVIEW_PREPARATION';baselinePath=$baselinePath;baselineSha256=$baselineSha;checkScope='SHA256 only against179 original pins; no protected-file semantic reading';total=$results.Count;unchanged=$unchanged;changed=$changed;missing=$missing;evaluatorContentsSemanticallyRead=$false;originalSpecContentsSemanticallyRead=$false;applicationExecuted=$false;results=$results}
$json=$record | ConvertTo-Json -Depth 7
$stream=[IO.File]::Open($outputPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
try{$bytes=[Text.UTF8Encoding]::new($false).GetBytes($json+"`n");$stream.Write($bytes,0,$bytes.Length)}finally{$stream.Dispose()}
[ordered]@{total=$results.Count;unchanged=$unchanged;changed=$changed;missing=$missing;sha256=(Get-FileHash -LiteralPath $outputPath -Algorithm SHA256).Hash.ToLowerInvariant()} | ConvertTo-Json -Compress
