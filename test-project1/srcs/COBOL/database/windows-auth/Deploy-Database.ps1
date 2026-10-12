[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$ServerInstance, [switch]$Apply)
. "$PSScriptRoot/Common.ps1"
$files = @('001_schema.sql','002_seed.sql') | ForEach-Object { Join-Path $script:CobolDatabaseDirectory $_ }
$files += Join-Path $PSScriptRoot '003_permissions.sql'
foreach ($path in $files) { if (-not (Test-Path -LiteralPath $path)) { throw "Missing independent resource: $path" } }
if (-not $Apply) {
    [pscustomobject]@{ Status='PLAN_ONLY'; Server=$ServerInstance; Database=$script:CobolDatabase; Authentication='Windows'; Encrypt=$true; TrustServerCertificate=$false; NewDatabaseOnly=$true; Files=$files }
    return
}
$master = New-CobolSqlConnection $ServerInstance 'master'
$database = $null
try {
    $master.Open()
    if ([int](Invoke-CobolSqlScalar $master "SELECT CONVERT(int,SERVERPROPERTY('ProductMajorVersion'))") -ne 17) { throw 'Expected SQL Server 17.x.' }
    if ([int](Invoke-CobolSqlScalar $master "SELECT CONVERT(int,SERVERPROPERTY('EngineEdition'))") -ne 4) { throw 'Expected SQL Server Express.' }
    if ([int](Invoke-CobolSqlScalar $master "SELECT CASE WHEN DB_ID(N'contextbase_test_project1_cobol') IS NULL THEN 0 ELSE 1 END") -ne 0) {
        throw 'Database already exists. No overwrite, drop, migration, or automatic repair is permitted.'
    }
    $command = $master.CreateCommand()
    try { $command.CommandText = 'CREATE DATABASE [contextbase_test_project1_cobol];'; $command.CommandTimeout=120; [void]$command.ExecuteNonQuery() }
    finally { $command.Dispose() }
    $database = New-CobolSqlConnection $ServerInstance $script:CobolDatabase
    $database.Open()
    foreach ($path in $files) { Write-Output "APPLY $path"; Invoke-CobolSqlFile $database $path }
    Write-Output 'APPLIED_NEW_COBOL_DATABASE; initial class/student/audit rows remain empty.'
}
catch {
    Write-Warning 'A failed deployment can leave the newly created dedicated database partially populated. Nothing is dropped or automatically repaired.'
    throw
}
finally { if ($null -ne $database) { $database.Dispose() }; $master.Dispose() }
