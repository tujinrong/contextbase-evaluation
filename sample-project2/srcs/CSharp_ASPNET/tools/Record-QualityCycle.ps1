param([Parameter(Mandatory)][ValidateRange(1,3)][int]$Cycle,[Parameter(Mandatory)][string]$ResultsPath,[Parameter(Mandatory)][string[]]$Findings,[Parameter(Mandatory)][string[]]$Fixes,[Parameter(Mandatory)][string[]]$Commands)
$ErrorActionPreference = 'Stop'
$sp2Root = Split-Path -Parent $PSScriptRoot
$sp2Output = Join-Path $sp2Root 'build/test-results/quality-cycles.json'
$sp2Inputs = Join-Path $sp2Root 'build/generation/inputs.json'
$sp2SourceFiles = Get-ChildItem -LiteralPath (Join-Path $sp2Root 'src') -Recurse -File | Where-Object { $_.Extension -in '.cs','.cshtml','.js','.css','.csproj' }
$sp2Hashes = @($sp2SourceFiles | Sort-Object FullName | ForEach-Object { @{path=[IO.Path]::GetRelativePath($sp2Root,$_.FullName).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()} })
$sp2Result = Get-Content -LiteralPath $ResultsPath -Raw -Encoding UTF8 | ConvertFrom-Json
$sp2Entry = @{cycle=$Cycle;recordedUtc=[DateTimeOffset]::UtcNow.ToString('o');inputManifestSha256=(Get-FileHash -LiteralPath $sp2Inputs -Algorithm SHA256).Hash.ToLowerInvariant();commands=$Commands;exitCode= $(if($sp2Result.passed){0}else{1});evidence=[IO.Path]::GetRelativePath($sp2Root,(Resolve-Path -LiteralPath $ResultsPath).Path).Replace('\','/');passed=$sp2Result.passed;findings=$Findings;fixes=$Fixes;regression='Tests were re-executed after the listed fixes; results are retained separately for this cycle.';sourceFiles=$sp2Hashes;unperformed=$sp2Result.unperformed}
$sp2Record = if(Test-Path -LiteralPath $sp2Output){Get-Content -LiteralPath $sp2Output -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable}else{@{projectId='sample-project2';methodId='CSharp_ASPNET';runId='20261029-sp2-build';quality='high';requestedCycles=3;formalScore=$null;cycles=@()}}
$sp2Record.runId=(Get-Content -LiteralPath $sp2Inputs -Raw -Encoding UTF8|ConvertFrom-Json).runId
$sp2PriorCycle = @($sp2Record.cycles | Where-Object { $_.cycle -eq $Cycle }) | Select-Object -First 1
$sp2Entry.observedFailures = @($sp2PriorCycle.observedFailures | Where-Object {$null -ne $_})
if(-not $sp2Result.passed){$sp2Entry.observedFailures += @($sp2Result.tests | Where-Object status -EQ 'FAIL')}
$sp2Record.cycles = @($sp2Record.cycles | Where-Object { $_.cycle -ne $Cycle }) + @($sp2Entry)
$sp2Record.cycles = @($sp2Record.cycles | Sort-Object cycle)
$sp2Record | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath $sp2Output -Encoding UTF8
