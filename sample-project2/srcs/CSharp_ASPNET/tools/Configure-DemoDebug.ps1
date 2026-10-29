param(
    [string]$ProfilePath = '.tmp/runtime/profile.json',
    [switch]$ValidateOnly
)
$ErrorActionPreference = 'Stop'
$sp2Root = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$sp2Scratch = [IO.Path]::GetFullPath((Join-Path $sp2Root '.tmp'))

function Assert-Sp2ScratchPath([string]$Path, [bool]$Directory) {
    $sp2Resolved = [IO.Path]::GetFullPath($Path)
    if (-not $sp2Resolved.StartsWith($sp2Scratch + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'The DEMO profile and data-protection keys must belong to this method .tmp directory.'
    }
    $sp2PathType = if ($Directory) { 'Container' } else { 'Leaf' }
    if (-not (Test-Path -LiteralPath $sp2Resolved -PathType $sp2PathType)) {
        throw 'The explicit DEMO profile or keys directory is missing. No database is created by this command.'
    }
    $sp2Current = Get-Item -LiteralPath $sp2Resolved -Force
    while ($null -ne $sp2Current -and $sp2Current.FullName.StartsWith($sp2Scratch, [StringComparison]::OrdinalIgnoreCase)) {
        if (($sp2Current.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'Linked DEMO profiles or keys directories are not accepted.'
        }
        $sp2Current = if ($sp2Current.PSIsContainer) { $sp2Current.Parent } else { $sp2Current.Directory }
    }
    return $sp2Resolved
}

if ($env:OS -ne 'Windows_NT') { throw 'This DEMO debug setup requires Windows.' }
$sp2ProfileFile = if ([IO.Path]::IsPathRooted($ProfilePath)) { $ProfilePath } else { Join-Path $sp2Root $ProfilePath }
$sp2ProfileFile = Assert-Sp2ScratchPath $sp2ProfileFile $false
try {
    $sp2Profile = Get-Content -LiteralPath $sp2ProfileFile -Raw -Encoding UTF8 | ConvertFrom-Json
} catch { throw 'The explicit DEMO profile is not valid JSON.' }
if ($sp2Profile.database -cnotmatch '^SP2_WebFixture_[A-Za-z0-9_]{1,48}$') {
    throw 'Only an explicitly selected sample-project2 fixture database is accepted.'
}
if ([string]::IsNullOrWhiteSpace($sp2Profile.connectionString) -or [string]::IsNullOrWhiteSpace($sp2Profile.keys)) {
    throw 'The DEMO profile must contain its connection and keys settings.'
}
try {
    $sp2Connection = New-Object System.Data.Common.DbConnectionStringBuilder
    $sp2Connection.set_ConnectionString([string]$sp2Profile.connectionString)
} catch { throw 'The DEMO SQL connection setting is invalid.' }
$sp2AllowedKeys = @('Server', 'Data Source', 'Database', 'Initial Catalog', 'Integrated Security', 'Trusted_Connection', 'Encrypt', 'TrustServerCertificate', 'Connect Timeout', 'Connection Timeout', 'Application Name')
foreach ($sp2Key in $sp2Connection.get_Keys()) {
    if ($sp2Key -notin $sp2AllowedKeys) { throw 'The DEMO connection contains an unsupported setting. SQL passwords and alternate authentication are not accepted.' }
}
function Get-Sp2ConnectionValue([string[]]$Names) {
    $sp2Present = @($Names | Where-Object { $sp2Connection.ContainsKey($_) })
    if ($sp2Present.Count -ne 1) { throw 'The DEMO connection has a missing or ambiguous required setting.' }
    return [string]$sp2Connection[$sp2Present[0]]
}
$sp2Server = Get-Sp2ConnectionValue @('Server', 'Data Source')
$sp2Database = Get-Sp2ConnectionValue @('Database', 'Initial Catalog')
$sp2Integrated = Get-Sp2ConnectionValue @('Integrated Security', 'Trusted_Connection')
$sp2Encrypt = Get-Sp2ConnectionValue @('Encrypt')
$sp2Trust = Get-Sp2ConnectionValue @('TrustServerCertificate')
$sp2LocalMachine = [regex]::Escape($env:COMPUTERNAME)
if ($sp2Server -notmatch ('^(?:(?:\.|localhost|127\.0\.0\.1|' + $sp2LocalMachine + ')\\SQLEXPRESS|\(localdb\)\\[A-Za-z0-9_]{1,64})$')) {
    throw 'Only an explicit local SQLEXPRESS or LocalDB server is accepted for DEMO debugging.'
}
if ($sp2Database -cne $sp2Profile.database -or $sp2Integrated -notmatch '^(true|yes|sspi)$' -or $sp2Encrypt -notmatch '^(true|yes|mandatory)$' -or $sp2Trust -notmatch '^(true|false|yes|no)$') {
    throw 'The DEMO connection must use the exact fixture database, Windows integrated authentication, encryption and an explicit certificate policy.'
}
$sp2Keys = if ([IO.Path]::IsPathRooted($sp2Profile.keys)) { $sp2Profile.keys } else { Join-Path $sp2Root $sp2Profile.keys }
$sp2Keys = Assert-Sp2ScratchPath $sp2Keys $true
$sp2LaunchPath = Join-Path $sp2Root 'src/CareerManagement.Web/Properties/launchSettings.json'
try {
    $sp2Launch = Get-Content -LiteralPath $sp2LaunchPath -Raw -Encoding UTF8 | ConvertFrom-Json
} catch { throw 'The Web launch settings are missing or invalid. No debug settings were changed.' }
$sp2LaunchProfile = $sp2Launch.profiles.'CareerManagement.Web'
if ($null -eq $sp2LaunchProfile -or $sp2LaunchProfile.commandName -ne 'Project') {
    throw 'The CareerManagement.Web project launch profile is required. No debug settings were changed.'
}
if ($null -eq $sp2LaunchProfile.environmentVariables) {
    $sp2LaunchProfile | Add-Member -NotePropertyName environmentVariables -NotePropertyValue ([pscustomobject]@{})
}
$sp2LaunchEnvironment = [ordered]@{
    ASPNETCORE_ENVIRONMENT = 'Development'
    DOTNET_ENVIRONMENT = 'Development'
    SP2_DATABASE = [string]$sp2Profile.database
    SP2_FIXTURE = 'true'
    SP2_CONNECTION_STRING = [string]$sp2Profile.connectionString
}
foreach ($sp2Setting in $sp2LaunchEnvironment.GetEnumerator()) {
    $sp2LaunchProfile.environmentVariables | Add-Member -NotePropertyName $sp2Setting.Key -NotePropertyValue $sp2Setting.Value -Force
}
$sp2LaunchProfile | Add-Member -NotePropertyName launchUrl -NotePropertyValue 'account/login' -Force
$sp2LaunchJson = ($sp2Launch | ConvertTo-Json -Depth 100) + [Environment]::NewLine
if ($ValidateOnly) {
    Write-Output 'Development DEMO and Web launch profiles validated; files and user-secrets are unchanged. No database operations were performed.'
    exit 0
}
$sp2Settings = [ordered]@{
    SP2_DATABASE = [string]$sp2Profile.database
    SP2_FIXTURE = 'true'
    SP2_CONNECTION_STRING = [string]$sp2Profile.connectionString
    SP2_DATA_KEYS = $sp2Keys
}
$sp2WebProject = Join-Path $sp2Root 'src/CareerManagement.Web/CareerManagement.Web.csproj'
# Piped JSON avoids placing settings in process arguments or printing the profile.
$sp2PreviousOutputEncoding = $OutputEncoding
try {
    # Windows PowerShell 5.1 otherwise sends native stdin as ASCII, corrupting Japanese paths.
    $OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $sp2Settings | ConvertTo-Json -Compress | & dotnet user-secrets set --project $sp2WebProject 2>&1 | Out-Null
} finally {
    $OutputEncoding = $sp2PreviousOutputEncoding
}
if ($LASTEXITCODE -ne 0) { throw 'Development user-secrets could not be configured. No database operations were performed.' }
# The validated local integrated connection contains no SQL password. Explicit launch
# environment values override stale settings inherited by an already running Visual Studio.
[IO.File]::WriteAllText($sp2LaunchPath, $sp2LaunchJson, (New-Object System.Text.UTF8Encoding($false)))
Write-Output 'Development DEMO user-secrets and the CareerManagement.Web launch profile are configured. Select that startup project in Visual Studio and restart debugging. No database operations were performed.'
