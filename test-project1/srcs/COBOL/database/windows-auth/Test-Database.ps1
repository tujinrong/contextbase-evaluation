[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$ServerInstance,[switch]$RequirePristineSeed,[switch]$Execute)
. "$PSScriptRoot/Common.ps1"
if (-not $Execute) { Write-Output "PLAN_ONLY read-only verification: $script:CobolDatabase / $ServerInstance"; return }
$connection = New-CobolSqlConnection $ServerInstance $script:CobolDatabase
$checks=@(); $baseline=@(); $identity=@()
try {
    $connection.Open()
    $command=$connection.CreateCommand()
    try {
        $command.CommandText=[IO.File]::ReadAllText((Join-Path $PSScriptRoot '004_verify.sql'),[Text.Encoding]::UTF8)
        $reader=$command.ExecuteReader()
        try {
            while ($reader.Read()) { $checks += [pscustomobject]@{id=$reader.GetString(0);passed=$reader.GetBoolean(1);observed=$reader.GetString(2)} }
            [void]$reader.NextResult()
            while ($reader.Read()) { $baseline += [pscustomobject]@{id=$reader.GetString(0);rows=$reader.GetInt64(1)} }
            [void]$reader.NextResult()
            while ($reader.Read()) { $identity += [pscustomobject]@{originalLogin=$reader.GetValue(0);executionLogin=$reader.GetValue(1);databaseUser=$reader.GetValue(2);isStudentAdmin=$reader.GetValue(3);authScheme=$reader.GetValue(4)} }
        } finally { $reader.Dispose() }
    } finally { $command.Dispose() }
} finally { $connection.Dispose() }
$failures=@($checks | Where-Object { -not $_.passed })
if ($RequirePristineSeed) { $failures += @($baseline | Where-Object { $_.rows -ne 0 }) }
[pscustomobject]@{status=$(if($failures.Count -eq 0){'PASS'}else{'FAIL'});checks=$checks;initialBaseline=$baseline;identity=$identity} | ConvertTo-Json -Depth 6
if ($failures.Count -ne 0) { throw 'COBOL database verification failed.' }
