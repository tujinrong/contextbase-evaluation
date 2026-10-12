$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath('test-project1/srcs/Access')
$results=@()
foreach($name in @('Build-Access.ps1','tests/Test-Race.ps1','tests/Evidence/Test-FormatAndInitialState.ps1','tests/Evidence/Seed-UiFixtureR4.ps1')) {
 $path=Join-Path $root $name
 $tokens=$null;$errors=$null
 [void][Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors)
 $results += [ordered]@{path=$path;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash;errors=@($errors|ForEach-Object {$_.Message});passed=($errors.Count -eq 0)}
}
[ordered]@{powershell=$PSVersionTable.PSVersion.ToString();passed=@($results|Where-Object {$_.passed}).Count;failed=@($results|Where-Object {-not $_.passed}).Count;checks=$results;sqlConnectionsOpened=0}|ConvertTo-Json -Depth 6
if(@($results|Where-Object {-not $_.passed}).Count){exit 1}