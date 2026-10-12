[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$ServerInstance,
      [ValidatePattern('^[A-Za-z0-9_-]+$')][string]$DsnName='contextbase_test_project1_cobol',
      [ValidateSet('User','System')][string]$DsnType='User',[switch]$Apply)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if ([string]::IsNullOrWhiteSpace($ServerInstance) -or $ServerInstance -match '[;\r\n]') { throw 'Invalid server instance.' }
$properties=@("Server=$ServerInstance",'Database=contextbase_test_project1_cobol','Trusted_Connection=Yes','Encrypt=Yes','TrustServerCertificate=No')
if (-not $Apply) { [pscustomobject]@{status='PLAN_ONLY';dsn=$DsnName;type=$DsnType;platform='64-bit';driver='ODBC Driver 18 for SQL Server';properties=$properties};return }
if (-not (Get-OdbcDriver -Name 'ODBC Driver 18 for SQL Server' -Platform '64-bit' -ErrorAction SilentlyContinue)) { throw '64-bit Microsoft ODBC Driver 18 is required.' }
if (Get-OdbcDsn -Name $DsnName -DsnType $DsnType -Platform '64-bit' -ErrorAction SilentlyContinue) { throw 'DSN already exists; nothing is replaced.' }
Add-OdbcDsn -Name $DsnName -DriverName 'ODBC Driver 18 for SQL Server' -DsnType $DsnType -Platform '64-bit' -SetPropertyValue $properties
Write-Output "REGISTERED_NEW_DSN $DsnName"
