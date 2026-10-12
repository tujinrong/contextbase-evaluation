[CmdletBinding()]
param([string] $ReportStem = '20261012-web-deployment-column-validation-r3')
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if ($ReportStem -notmatch '^[A-Za-z0-9_-]+$') { throw 'Report stem must be a simple new file name.' }
$outputPaths = @('json','md','raw.log') | ForEach-Object { Join-Path $PSScriptRoot ($ReportStem+'.'+$_) }
foreach ($path in $outputPaths) { if (Test-Path -LiteralPath $path) { throw "Old evidence must not be overwritten: $path" } }
$utf8 = [Text.UTF8Encoding]::new($false)
function Text-Sha256([string] $Value) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($sha.ComputeHash($utf8.GetBytes($Value))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose() }
}
function File-Sha256([string] $Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Read-DdlColumns([string] $Sql) {
    # Count actual physical column declarations, including derived matching keys.
    # Table-level CONSTRAINT clauses are not column declarations.
    $found = [regex]::Matches($Sql,'(?ms)^CREATE TABLE dbo\.(?<name>[a-z_][a-z_0-9]*)\s*\(\r?\n(?<body>.*?)^\);')
    $tables = [ordered]@{}
    $knownTypes = @('bigint','smallint','int','varchar','nvarchar','date','datetimeoffset','datetime2','bit','uniqueidentifier','binary','varbinary','char')
    foreach ($table in $found) {
        $name = $table.Groups['name'].Value
        if ($tables.Contains($name)) { throw "Duplicate table: $name" }
        $columns = @()
        foreach ($line in ($table.Groups['body'].Value -split '\r?\n')) {
            $definition = $line.Trim()
            if ($definition -eq '' -or $definition -match '^CONSTRAINT\b') { continue }
            $column = [regex]::Match($definition,'^(?<name>[a-z_][a-z_0-9]*)\s+(?<type>[a-z]+)\b')
            if (-not $column.Success -or $column.Groups['type'].Value -notin $knownTypes) { throw "Unsupported column definition in ${name}: $definition" }
            $columns += $column.Groups['name'].Value
        }
        if (@($columns | Select-Object -Unique).Count -ne $columns.Count) { throw "Duplicate physical column in $name" }
        $tables[$name] = $columns
    }
    if ($tables.Count -eq 0) { throw 'No physical CREATE TABLE blocks were parsed.' }
    return $tables
}
function Read-VerifyCounts([string] $Sql) {
    $section = [regex]::Match($Sql,'(?s)INSERT @tables VALUES\s+(?<values>.*?);')
    if (-not $section.Success) { throw 'Verification table-count contract was not found.' }
    $tables = [ordered]@{}
    foreach ($value in [regex]::Matches($section.Groups['values'].Value,"\(N'(?<name>[a-z_][a-z_0-9]*)',(?<count>\d+)\)")) {
        $name = $value.Groups['name'].Value
        if ($tables.Contains($name)) { throw "Duplicate expected table: $name" }
        $tables[$name] = [int]$value.Groups['count'].Value
    }
    return $tables
}
function Compare-Counts($Physical,$Expected) {
    $mismatch = @()
    foreach ($name in $Physical.Keys) {
        if (-not $Expected.Contains($name)) { $mismatch += "Expected contract omits $name" }
        elseif ($Physical[$name].Count -ne $Expected[$name]) { $mismatch += "${name}: actual=$($Physical[$name].Count) expected=$($Expected[$name])" }
    }
    foreach ($name in $Expected.Keys) { if (-not $Physical.Contains($name)) { $mismatch += "DDL omits $name" } }
    return ,$mismatch
}
$beforeVerify = @{ CSharp_ASPNET='80d9a7c01f809f749acaade923c507878cc74b03595e88a09adab6a4d21ec4a4'; Vue_CSharpAPI='95074bc573d27408cde841fd45a725d16b139f45acad7472b44e0ba98729cb3e' }
$checks = [Collections.Generic.List[object]]::new()
$raw = [Collections.Generic.List[string]]::new()
$projects = [Collections.Generic.List[object]]::new()
function Check([string] $Name,[bool] $Passed,[string] $Evidence) {
    $checks.Add([pscustomobject]@{name=$Name;passed=$Passed;evidence=$Evidence})
    $raw.Add("$(if($Passed){'PASS'}else{'FAIL'}) $Name : $Evidence")
}
$raw.Add('Static-only DDL-to-verifier validation. No SQLCMD, SQL connection, app server, or elevation.')
$raw.Add('PowerShell '+$PSVersionTable.PSVersion.ToString())
foreach ($way in @('CSharp_ASPNET','Vue_CSharpAPI')) {
    $directory = Join-Path $projectRoot ('srcs/'+$way+'/database')
    $ddlPath = Join-Path $directory '001_schema.sql'
    $verifyPath = Join-Path $directory '004_verify_deployment.sql'
    $ddl = [IO.File]::ReadAllText($ddlPath)
    $verify = [IO.File]::ReadAllText($verifyPath)
    $physical = Read-DdlColumns $ddl
    $expected = Read-VerifyCounts $verify
    $mismatch = Compare-Counts $physical $expected
    $sum = 0
    $counts = foreach ($name in $physical.Keys) { $sum += $physical[$name].Count; [pscustomobject]@{table=$name;physicalColumns=$physical[$name].Count;expectedColumns=$expected[$name];columns=$physical[$name]} }
    Check "$way-seven-physical-tables" ($physical.Count -eq 7) "parsed=$($physical.Count)"
    Check "$way-seven-verification-entries" ($expected.Count -eq 7) "expected=$($expected.Count)"
    Check "$way-all-counts-match" ($mismatch.Count -eq 0) ('differences='+($mismatch -join '; '))
    Check "$way-student35-total106" ($physical['m_student'].Count -eq 35 -and $sum -eq 106) "student=$($physical['m_student'].Count); total=$sum"
    $negativeVerify = Read-VerifyCounts ($verify.Replace("(N'm_student',35)","(N'm_student',33)"))
    $negative = Compare-Counts $physical $negativeVerify
    Check "$way-reject-original33" ($negative.Count -eq 1 -and $negative[0] -eq 'm_student: actual=35 expected=33') ($negative -join '; ')
    $removed = Read-DdlColumns ([regex]::Replace($ddl,'(?m)^  name_key [^\r\n]*\r?\n',''))
    $missingColumn = Compare-Counts $removed $expected
    Check "$way-detect-missing-physical-column" ($missingColumn.Count -eq 1 -and $missingColumn[0] -eq 'm_student: actual=34 expected=35') ($missingColumn -join '; ')
    $renamed = Read-DdlColumns ($ddl.Replace('CREATE TABLE dbo.m_class (','CREATE TABLE dbo.m_class_unexpected ('))
    $renamedMismatch = Compare-Counts $renamed $expected
    Check "$way-detect-renamed-table" ($renamedMismatch.Count -eq 2) ($renamedMismatch -join '; ')
    $reconstructed = $verify.Replace("(N'm_student',35)","(N'm_student',33)")
    Check "$way-only-authorized-value-changed" ((Text-Sha256 $reconstructed) -ceq $beforeVerify[$way]) ('reconstructed before SHA='+ (Text-Sha256 $reconstructed))
    $ddlHash = File-Sha256 $ddlPath
    $seedHash = File-Sha256 (Join-Path $directory '002_seed.sql')
    Check "$way-ddl-unchanged" ($ddlHash -ceq 'e6872d042fed6e1d795fde72e29adef5cecda6a0887348444ea905661de1178a') $ddlHash
    Check "$way-seed-unchanged" ($seedHash -ceq 'b4b6745e5c6e7d1ed3a22b07b2bb4607b5a6bf173ad08ba5bf32f0e4bb2322ee') $seedHash
    $projects.Add([pscustomobject]@{project=$way;ddlSha256=$ddlHash;seedSha256=$seedHash;verificationBeforeSha256=$beforeVerify[$way];verificationAfterSha256=(File-Sha256 $verifyPath);totalPhysicalColumns=$sum;tables=$counts})
}
$failed = @($checks | Where-Object { -not $_.passed }).Count
$record = [ordered]@{id=$ReportStem;recordedAtUtc=[DateTime]::UtcNow.ToString('o');testDriverSha256=(File-Sha256 $PSCommandPath);scope='Current local DDL physical declarations versus read-only deployment verifier; no database execution';result=$(if($failed -eq 0){'PASS'}else{'FAIL'});checkCount=$checks.Count;failed=$failed;projects=$projects;checks=$checks;sqlcmdExecutions=0;sqlConnections=0;sqlExecutions=0;elevations=0;unexecuted=@('SQL Server Express deployment','live sys.columns verification','shared role/SQLCLR resolution','application authorization and CRUD')}
$raw.Add("RESULT $($record.result) $($checks.Count-$failed)/$($checks.Count)")
$markdown = @('# Web導入検証の列数修正・R3非接続検査','','2026-10-12／projectId=test-project1／build。現在の001 DDLから物理列を独立に解析し、004の期待件数と全7表で比較。','',('結果：'+$record.result+' '+($checks.Count-$failed)+'/'+$checks.Count+'。各方式は学生35列・全106列。原バグ33列への戻し、列欠落、表名不一致の負例を検出した。'),'','修正はMVC/Vue 004の学生期待値33→35のみ。逆変換SHAが修正前SHAと一致し、その他byteの不変更を検査した。001と002は変更なし。既存R1/R2報告は保存する。','','| 方式 | 004修正前SHA256 | 004修正後SHA256 |','| --- | --- | --- |')
foreach ($project in $projects) { $markdown += '| '+$project.project+' | '+$project.verificationBeforeSha256+' | '+$project.verificationAfterSha256+' |' }
$markdown += @('','実行装置は同名.ps1、詳細はJSONとraw.log。SQLCMD実行、SQL接続、SQL実行、昇格はすべて0件。','','これは静的列数照合の合格であり、Express17の導入成功・共有DB接続・権限・業務動作の合格ではない。共有role/SQLCLRの構造衝突は20261012-shared-sql-schema-assessment.mdに記録し、解消前の導入停止を維持する。')
[IO.File]::WriteAllText($outputPaths[0],($record | ConvertTo-Json -Depth 8)+"`n",$utf8)
[IO.File]::WriteAllText($outputPaths[1],($markdown -join "`n")+"`n",$utf8)
[IO.File]::WriteAllText($outputPaths[2],($raw -join "`n")+"`n",$utf8)
Write-Output ($record | ConvertTo-Json -Depth 2)
if ($failed -ne 0) { exit 1 }
