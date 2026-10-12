# Windows PowerShell 5.1. Helpers never connect merely by being loaded.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:CobolDatabase = 'contextbase_test_project1_cobol'
$script:CobolDatabaseDirectory = Split-Path -Parent $PSScriptRoot
function New-CobolSqlConnection([string]$ServerInstance, [string]$Database) {
    if ($Database -notin @('master', $script:CobolDatabase)) { throw 'Unexpected database target.' }
    if ([string]::IsNullOrWhiteSpace($ServerInstance) -or $ServerInstance -match '[;\r\n]') { throw 'Invalid server instance.' }
    $builder = New-Object System.Data.SqlClient.SqlConnectionStringBuilder
    $builder.DataSource = $ServerInstance
    $builder.InitialCatalog = $Database
    $builder.IntegratedSecurity = $true
    $builder.Encrypt = $true
    $builder.TrustServerCertificate = $false
    $builder.ConnectTimeout = 15
    $builder.ApplicationName = 'COBOL independent database deployment'
    return New-Object System.Data.SqlClient.SqlConnection $builder.ConnectionString
}
function Invoke-CobolSqlScalar($Connection, [string]$Sql) {
    $command = $Connection.CreateCommand()
    try { $command.CommandText = $Sql; $command.CommandTimeout = 120; return $command.ExecuteScalar() }
    finally { $command.Dispose() }
}
function Invoke-CobolSqlFile($Connection, [string]$Path) {
    $text = [IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8)
    foreach ($batch in [regex]::Split($text, '(?im)^\s*GO\s*(?:--[^\r\n]*)?$')) {
        if ([string]::IsNullOrWhiteSpace($batch)) { continue }
        $command = $Connection.CreateCommand()
        try { $command.CommandText = $batch; $command.CommandTimeout = 120; [void]$command.ExecuteNonQuery() }
        finally { $command.Dispose() }
    }
}
