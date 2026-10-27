[CmdletBinding()]
param([string]$Server='.\SQLEXPRESS', [string]$Database='AccessRebuilderTraining_01a17be7')
$ErrorActionPreference='Stop'
if ($Server -ne '.\SQLEXPRESS' -or $Database -notmatch '^AccessRebuilderTraining_[A-Za-z0-9_]+$') { throw 'This helper only creates a named local training database.' }
$methodRoot=Split-Path -Parent $PSScriptRoot
$schema=Join-Path $methodRoot 'database/sql/001-schema.sql'
$seed=Join-Path $methodRoot 'database/sql/002-seed.sql'
if (-not (Test-Path -LiteralPath $schema) -or -not (Test-Path -LiteralPath $seed)) { throw 'Generate schema and seed first.' }
# A pre-existing database is never dropped, reset or adopted by this creation helper.
$create="IF DB_ID(N'$Database') IS NOT NULL THROW 51000,'Training database already exists; no changes.',1; EXEC(N'CREATE DATABASE [$Database]');"
& sqlcmd -S $Server -E -C -b -Q $create
if ($LASTEXITCODE -ne 0) { throw 'Database creation failed.' }
& sqlcmd -S $Server -d $Database -E -C -b -Q "EXEC sys.sp_addextendedproperty @name=N'AccessRebuilderOwner',@value=N'test-project1/Access-CSharp_ASPNET';"
if ($LASTEXITCODE -ne 0) { throw 'Database ownership marker failed.' }
& sqlcmd -S $Server -d $Database -E -C -b -f 65001 -i $schema
if ($LASTEXITCODE -ne 0) { throw 'Schema creation failed; dedicated DB retained for inspection.' }
& sqlcmd -S $Server -d $Database -E -C -b -f 65001 -i $seed
if ($LASTEXITCODE -ne 0) { throw 'Seed failed; dedicated DB retained for inspection.' }
