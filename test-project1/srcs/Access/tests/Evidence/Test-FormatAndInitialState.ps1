[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Frontend,
    [Parameter(Mandatory=$true)][string]$Backend,
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId,
    [Parameter(Mandatory=$true)][string]$ReportDirectory
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../../tools/GeneratedPaths.ps1')
$profileRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$ownedBuild=Join-Path $profileRoot '.tmp'
$reportRoot=Resolve-AccessGeneratedPath $ReportDirectory '.tmp'
$frontendPath=Resolve-AccessGeneratedPath $Frontend '.tmp'
$backendPath=Resolve-AccessGeneratedPath $Backend '.tmp'
foreach($path in @($frontendPath,$backendPath)) {
    if(-not $path.StartsWith($ownedBuild+'\',[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetExtension($path) -ne '.accdb') {throw 'Disposable files under Access/.tmp required.'}
}
New-Item -ItemType Directory -Path $reportRoot -Force|Out-Null
$reportPath=Join-Path $reportRoot 'format-initial-state.json'
$checks=New-Object 'Collections.Generic.List[object]'
$files=New-Object 'Collections.Generic.List[object]'
$defaults=[ordered]@{}
$access=$null
function Check([bool]$ok,[string]$name) {
    $checks.Add([ordered]@{name=$name;passed=$ok})
    Write-Output "$(if($ok){'PASS'}else{'FAIL'}): $name"
}
try {
    $access=New-Object -ComObject Access.Application
    $access.Visible=$false
    $paths=@($backendPath,$frontendPath | Select-Object -Unique)
    foreach($path in $paths) {
        $header=[Text.Encoding]::ASCII.GetString([IO.File]::ReadAllBytes($path),0,64)
        Check ($header.Contains('Standard ACE DB')) ('ACE physical header: '+[IO.Path]::GetFileName($path))
        $before=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
        $access.OpenCurrentDatabase($path)
        $format=[int]$access.CurrentProject.FileFormat
        Check ($format -eq 12) ('Access FileFormat=12: '+[IO.Path]::GetFileName($path))
        $files.Add([ordered]@{path=$path;fileFormat=$format;header=$header;sha256Before=$before})
        if($path -eq $frontendPath) {
            $access.DoCmd.OpenForm('frmStudentSearch')
            foreach($item in @(
                @('chkEnrolled',$true),@('chkLeave',$true),
                @('chkGraduated',$false),@('chkWithdrawn',$false)
            )) {
                $value=$access.Eval('[Forms]![frmStudentSearch]!['+$item[0]+']')
                $isNull=($null -eq $value -or $value -is [DBNull])
                $defaults[$item[0]]=[ordered]@{isNull=$isNull;value=$(if($isNull){$null}else{[bool]$value})}
                Check (-not $isNull -and [bool]$value -eq $item[1]) ('initial Boolean '+$item[0]+'='+$item[1])
            }
            Check ($access.Eval('[Forms]![frmStudentSearch]![cboSortKey]') -eq 'studentNo' -and $access.Eval('[Forms]![frmStudentSearch]![cboSortDirection]') -eq 'asc') 'initial full-list sort'
            $retired=@($access.Forms.Item('frmStudentSearch').Controls | Where-Object {$_.Name -in @('cboPageSize','cmdFirst','cmdPrev','cmdNext','cmdLast','chkUnassignedOnly')})
            Check ($retired.Count -eq 0) 'retired search/range controls absent'
            $access.DoCmd.Close(2,'frmStudentSearch',2)
        }
        $access.CloseCurrentDatabase()
    }
} catch {$fatal=$_.Exception.ToString()+[Environment]::NewLine+$_.ScriptStackTrace;Write-Output $fatal}
finally {
    if($null -ne $access) {
        $officeVersion=$access.Version
        try{$access.CloseCurrentDatabase()}catch{}
        $access.Quit(2);[Runtime.InteropServices.Marshal]::FinalReleaseComObject($access)|Out-Null;$access=$null
    }
    [GC]::Collect();[GC]::WaitForPendingFinalizers()
    foreach($item in $files) {$item.sha256After=(Get-FileHash -LiteralPath $item.path -Algorithm SHA256).Hash}
    $failed=@($checks|Where-Object {-not $_.passed}).Count
    [ordered]@{runId=$RunId;profile='Access';status=$(if(-not $fatal -and $failed -eq 0 -and $checks.Count -eq ($paths.Count*2+6)){'Passed'}else{'Failed'});passed=@($checks|Where-Object {$_.passed}).Count;failed=$failed;checks=$checks;files=$files;initialControls=$defaults;officeVersion=$officeVersion;fixtureOnly=$true;visible=$false;sharedSqlConnected=$false;screenshots='NOT_RUN';fatal=$fatal}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath $reportPath -Encoding UTF8
}
if($fatal -or $failed -ne 0 -or $checks.Count -ne ($paths.Count*2+6)){exit 1}
