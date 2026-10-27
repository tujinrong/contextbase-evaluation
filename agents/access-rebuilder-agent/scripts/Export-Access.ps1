[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$SourceFile,
    [Parameter(Mandatory)][string]$TargetRoot,
    [string]$ExpectedSha256,
    [switch]$SafetyFixtureVerified
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Release-Com($Value) {
    if ($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}
function Read-Value($Object, [string]$Name) {
    try { $value = $Object.$Name; if ($value -is [System.DBNull]) { return $null }; return $value } catch { return $null }
}
function Read-Properties($Object) {
    $result = [ordered]@{}
    foreach ($property in $Object.Properties) {
        if ($property.Name -match '^(Connect|Password|Jet OLEDB:Database Password)$') { continue }
        try {
            $value = $property.Value
            if ($null -eq $value -or $value -is [System.DBNull]) { $result[$property.Name] = $null }
            elseif ($value -is [byte[]]) { $result[$property.Name] = @{ binaryBytes = $value.Length } }
            elseif ($value -is [string] -or $value -is [ValueType]) { $result[$property.Name] = $value }
        } catch { $result[$property.Name] = @{ unreadable = $true } }
    }
    return $result
}
function Write-Json($Object, [string]$Path) {
    $Object | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $Path -Encoding utf8
}
function Safe-Name([string]$Name) {
    $value = $Name -replace '[\x00-\x1f<>:"/\\|?*]', '_'
    if ($value -match '^\.+$' -or $value.Length -eq 0 -or $value.EndsWith('.') -or $value.EndsWith(' ')) { throw "Unsafe Access object name: $Name" }
    return $value
}
function Remove-OwnedDirectory([string]$Path,[string]$Owner) {
    $resolved = [IO.Path]::GetFullPath($Path)
    $ownedRoot = [IO.Path]::GetFullPath($Owner).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    if (-not $resolved.StartsWith($ownedRoot,[StringComparison]::OrdinalIgnoreCase)) { throw "Refusing removal outside owner: $resolved" }
    if (Test-Path -LiteralPath $resolved) {
        if (((Get-Item -LiteralPath $resolved -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Refusing removal of a reparse point.' }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}

$sourcePath = (Resolve-Path -LiteralPath $SourceFile).Path
$targetPath = [IO.Path]::GetFullPath($TargetRoot)
if ([IO.Path]::GetExtension($sourcePath) -notin '.accdb','.mdb') { throw 'Only .accdb and .mdb are supported.' }
if ($sourcePath.StartsWith($targetPath + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Source file must be outside the generated target root.' }
foreach ($p in @($sourcePath, $targetPath)) {
    $probePath = $p
    while ($probePath) {
        if ((Test-Path -LiteralPath $probePath) -and (((Get-Item -LiteralPath $probePath -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) { throw "Reparse point is not allowed: $probePath" }
        $probePath = Split-Path -Parent $probePath
    }
}
if (-not $SafetyFixtureVerified) { throw 'Run Test-AccessExtractor.ps1 before real extraction and supply -SafetyFixtureVerified.' }
$inputHash = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash
if ($ExpectedSha256 -and $ExpectedSha256 -ne $inputHash) { throw 'Input hash differs from the authorized snapshot.' }
$work = Join-Path $targetPath '.tmp/extraction'
$final = Join-Path $targetPath 'build/generation'
$publishedExports = Join-Path $final 'access-export'
$exports = Join-Path $work 'access-export'
Remove-OwnedDirectory $exports $work
New-Item -ItemType Directory -Path $work,$final,$exports -Force | Out-Null
Write-Json @{schema='access-binary-extraction/1.0';sourceFile=$sourcePath;sourceSha256=$inputHash;status='RUNNING';reason='Prior extraction manifest invalidated before a new acquisition.';formalScore=$null} (Join-Path $final 'access-extraction.json')
$snapshot = Join-Path $work ('source' + [IO.Path]::GetExtension($sourcePath))
$hostPath = Join-Path $work 'export-host.accdb'
if (Test-Path -LiteralPath $snapshot) { Remove-Item -LiteralPath $snapshot -Force }
if (Test-Path -LiteralPath $hostPath) { Remove-Item -LiteralPath $hostPath -Force }
Copy-Item -LiteralPath $sourcePath -Destination $snapshot
if ((Get-FileHash -LiteralPath $snapshot -Algorithm SHA256).Hash -ne $inputHash) { throw 'Snapshot copy hash mismatch.' }
$engine = $null; $db = $null; $access = $null
$failures = [Collections.Generic.List[object]]::new()
$objects = [Collections.Generic.List[object]]::new()
$tables = [Collections.Generic.List[object]]::new()
$queries = [Collections.Generic.List[object]]::new()
$relations = [Collections.Generic.List[object]]::new()
$counts = [ordered]@{}
$databaseProperties = $null
$ansiCodePage = (Get-WinSystemLocale).TextInfo.ANSICodePage
$usedExportNames = @{}
try {
    $engine = New-Object -ComObject DAO.DBEngine.120
    $db = $engine.OpenDatabase($snapshot,$false,$true,'')
    $databaseProperties = Read-Properties $db
    foreach ($table in $db.TableDefs) {
        if ($table.Name -match '^MSys|^~') { continue }
        $linked = -not [string]::IsNullOrEmpty([string](Read-Value $table 'Connect'))
        $fields = @($table.Fields | ForEach-Object {
            [ordered]@{ name=$_.Name; type=[int]$_.Type; size=[int]$_.Size; attributes=[int]$_.Attributes; properties=(Read-Properties $_) }
        })
        $indexes = @($table.Indexes | ForEach-Object {
            [ordered]@{ name=$_.Name; primary=[bool]$_.Primary; unique=[bool]$_.Unique; required=[bool]$_.Required; ignoreNulls=[bool]$_.IgnoreNulls; fields=@($_.Fields | ForEach-Object { @{name=$_.Name;attributes=[int]$_.Attributes} }) }
        })
        $count = $null
        if (-not $linked) {
            $rs = $db.OpenRecordset('SELECT Count(*) AS row_count FROM [' + $table.Name.Replace(']',']]') + ']',4)
            try { $count = [long]$rs.Fields.Item('row_count').Value } finally { $rs.Close(); Release-Com $rs }
        }
        $counts[$table.Name] = $count
        $tables.Add([ordered]@{name=$table.Name;attributes=[int]$table.Attributes;linked=$linked;sourceTableName=(Read-Value $table 'SourceTableName');properties=(Read-Properties $table);fields=$fields;indexes=$indexes;rowCount=$count;evidence=@{sourceSha256=$inputHash;objectType='TableDef';objectName=$table.Name}})
    }
    foreach ($query in $db.QueryDefs) {
        $queries.Add([ordered]@{name=$query.Name;type=[int]$query.Type;sql=$query.SQL;parameters=@($query.Parameters | ForEach-Object { @{name=$_.Name;type=[int]$_.Type} });hasExternalConnection=(-not [string]::IsNullOrEmpty([string](Read-Value $query 'Connect')));evidence=@{sourceSha256=$inputHash;objectType='QueryDef';objectName=$query.Name}})
    }
    foreach ($relation in $db.Relations) {
        if ($relation.Name -match '^MSys') { continue }
        $relations.Add([ordered]@{name=$relation.Name;table=$relation.Table;foreignTable=$relation.ForeignTable;attributes=[int]$relation.Attributes;fields=@($relation.Fields | ForEach-Object { @{name=$_.Name;foreignName=$_.ForeignName} });evidence=@{sourceSha256=$inputHash;objectType='Relation';objectName=$relation.Name}})
    }
    $objectSpecs = @(@{container='Forms';type=2;kind='forms'},@{container='Reports';type=3;kind='reports'},@{container='Scripts';type=4;kind='macros'},@{container='Modules';type=5;kind='modules'})
    $inventory = foreach ($spec in $objectSpecs) {
        foreach ($doc in $db.Containers.Item($spec.container).Documents) { @{name=$doc.Name;type=$spec.type;kind=$spec.kind;properties=(Read-Properties $doc)} }
    }
    $db.Close(); Release-Com $db; $db = $null
    $access = New-Object -ComObject Access.Application
    $access.Visible = $false
    $access.AutomationSecurity = 3
    $access.NewCurrentDatabase($hostPath)
    foreach ($object in @($inventory)) {
        $directory = Join-Path $exports $object.kind
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
        $out = Join-Path $directory ((Safe-Name $object.name) + '.txt')
        if ($usedExportNames.ContainsKey($out.ToLowerInvariant())) { throw 'Access object export filename collision.' }
        $usedExportNames[$out.ToLowerInvariant()] = $true
        try {
            $access.DoCmd.TransferDatabase(0,'Microsoft Access',$snapshot,$object.type,$object.name,$object.name,$false,$false)
            $raw = Join-Path $work 'object-export.txt'
            if (Test-Path -LiteralPath $raw) { Remove-Item -LiteralPath $raw -Force }
            $access.SaveAsText($object.type,$object.name,$raw)
            $bytes = [IO.File]::ReadAllBytes($raw)
            if ($bytes.Length -ge 2 -and $bytes[0] -eq 255 -and $bytes[1] -eq 254) { $text = [Text.Encoding]::Unicode.GetString($bytes).TrimStart([char]0xFEFF); $sourceEncoding = 'UTF-16LE-BOM' }
            elseif ($bytes.Length -ge 3 -and $bytes[0] -eq 239 -and $bytes[1] -eq 187 -and $bytes[2] -eq 191) { $text = [Text.Encoding]::UTF8.GetString($bytes).TrimStart([char]0xFEFF); $sourceEncoding = 'UTF-8-BOM' }
            else { $text = [Text.Encoding]::GetEncoding($ansiCodePage).GetString($bytes); $sourceEncoding = "Windows-ANSI-$ansiCodePage" }
            $moduleKind = $null
            if ($object.kind -eq 'modules') {
                # SaveAsText(acModule) uses a legacy ANSI encoding. The Access
                # Module object returns a Unicode BSTR and avoids lossy decoding.
                # OpenModule opens the code designer only; no procedure is called.
                $access.DoCmd.OpenModule($object.name)
                $codeModule = $access.Modules.Item($object.name)
                $moduleKind = [int]$codeModule.Type
                if ($codeModule.CountOfLines -gt 0) { $text = [string]$codeModule.Lines(1,$codeModule.CountOfLines) }
                else { $text = '' }
                $sourceEncoding = 'Access.Module.Lines-Unicode-BSTR'
                $access.DoCmd.Close(5,$object.name,2)
                Release-Com $codeModule
            }
            [IO.File]::WriteAllText($out,$text,[Text.UTF8Encoding]::new($false))
            $objects.Add([ordered]@{name=$object.name;kind=$object.kind;type=$object.type;moduleKind=$moduleKind;status='extracted';path=('access-export/' + $object.kind + '/' + [IO.Path]::GetFileName($out));sha256=(Get-FileHash -LiteralPath $out -Algorithm SHA256).Hash;lines=($text -split '\r?\n').Count;sourceEncoding=$sourceEncoding;outputEncoding='UTF-8';properties=$object.properties;evidence=@{sourceSha256=$inputHash;objectType=$object.kind;objectName=$object.name;method='TransferDatabase into empty host; SaveAsText for resources, Module.Lines Unicode for code; business procedures never run'}})
        } catch {
            $failures.Add(@{name=$object.name;kind=$object.kind;error=$_.Exception.Message})
            $objects.Add(@{name=$object.name;kind=$object.kind;type=$object.type;status='not-extracted'})
        }
    }
    $access.CloseCurrentDatabase()
    $access.Quit(2)
    Release-Com $access; $access = $null
    $record = [ordered]@{
        schema='access-binary-extraction/1.0';recordedDate='2026-10-27';sourceFile=$sourcePath;sourceSha256=$inputHash;snapshotSha256=(Get-FileHash -LiteralPath $snapshot -Algorithm SHA256).Hash
        method='DAO read-only sealed copy; blank host imports object definitions; source database never opened in Access UI'
        safety=@{fixtureVerified=[bool]$SafetyFixtureVerified;automationSecurity=3;sourceOpenedInAccess=$false;formsOpened=$false;savedQueriesExecuted=$false;linkedRowsRead=$false;localCountQueriesExecuted=$true;originalSha256After=(Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash}
        databaseProperties=$databaseProperties;tables=@($tables);relations=@($relations);queries=@($queries);objects=@($objects);rowCounts=$counts;failures=@($failures)
        status=$(if ($failures.Count -eq 0) {'PASS'} else {'PARTIAL'});limitations=@('External linked table rows are not read.','No VBA business procedures, forms, reports or macros are run.','References and unsupported database properties may require follow-up inspection.');formalScore=$null
    }
    if ($record.safety.originalSha256After -ne $inputHash) { throw 'Original file hash changed.' }
    Write-Json @{sourceSha256=$inputHash;tables=@($tables);relations=@($relations);queries=@($queries)} (Join-Path $exports 'schema.json')
    $previousExports = Join-Path $work 'previous-export'
    Remove-OwnedDirectory $previousExports $work
    if (Test-Path -LiteralPath $publishedExports) { Move-Item -LiteralPath $publishedExports -Destination $previousExports }
    try { Move-Item -LiteralPath $exports -Destination $publishedExports }
    catch {
        if ((Test-Path -LiteralPath $previousExports) -and -not (Test-Path -LiteralPath $publishedExports)) { Move-Item -LiteralPath $previousExports -Destination $publishedExports }
        throw
    }
    Remove-OwnedDirectory $previousExports $work
    Write-Json $record (Join-Path $final 'access-extraction.json')
    [ordered]@{status=$record.status;tables=$tables.Count;relations=$relations.Count;queries=$queries.Count;objects=$objects.Count;failures=$failures.Count;manifest=(Join-Path $final 'access-extraction.json')} | ConvertTo-Json
} catch {
    Write-Json @{schema='access-binary-extraction/1.0';sourceFile=$sourcePath;sourceSha256=$inputHash;status='FAIL';error=$_.Exception.Message;formalScore=$null} (Join-Path $final 'access-extraction.json')
    throw
} finally {
    if ($db) { try {$db.Close()} catch {}; Release-Com $db }
    if ($access) { try {$access.CloseCurrentDatabase()} catch {}; try {$access.Quit(2)} catch {}; Release-Com $access }
    Release-Com $engine
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}
