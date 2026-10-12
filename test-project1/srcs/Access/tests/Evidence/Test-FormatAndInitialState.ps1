[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Frontend,
    [Parameter(Mandatory=$true)][string]$Backend,
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId,
    [Parameter(Mandatory=$true)][string]$ReportDirectory
)
$ErrorActionPreference='Stop'
$profileRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$ownedBuild=Join-Path $profileRoot 'build'
$reportRoot=[IO.Path]::GetFullPath($ReportDirectory)
$frontendPath=[IO.Path]::GetFullPath($Frontend)
$backendPath=[IO.Path]::GetFullPath($Backend)
foreach($path in @($frontendPath,$backendPath)) {
    if(-not $path.StartsWith($ownedBuild+'\',[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetExtension($path) -ne '.accdb') {throw 'Disposable files under Access/build required.'}
}
New-Item -ItemType Directory -Path $reportRoot -Force|Out-Null
$reportPath=Join-Path $reportRoot ($RunId+'.json')
if(Test-Path -LiteralPath $reportPath) {throw 'Historical report exists; choose a new RunId.'}
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
    foreach($path in @($backendPath,$frontendPath)) {
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
                @('chkGraduated',$false),@('chkWithdrawn',$false),@('chkUnassignedOnly',$false)
            )) {
                $value=$access.Eval('[Forms]![frmStudentSearch]!['+$item[0]+']')
                $isNull=($null -eq $value -or $value -is [DBNull])
                $defaults[$item[0]]=[ordered]@{isNull=$isNull;value=$(if($isNull){$null}else{[bool]$value})}
                Check (-not $isNull -and [bool]$value -eq $item[1]) ('initial Boolean '+$item[0]+'='+$item[1])
            }
            Check ($access.Eval('[Forms]![frmStudentSearch]![cboPageSize]') -eq 20) 'initial page size=20'
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
    [ordered]@{runId=$RunId;profile='Access';status=$(if(-not $fatal -and $failed -eq 0 -and $checks.Count -eq 10){'Passed'}else{'Failed'});passed=@($checks|Where-Object {$_.passed}).Count;failed=$failed;checks=$checks;files=$files;initialControls=$defaults;officeVersion=$officeVersion;fixtureOnly=$true;visible=$false;sharedSqlConnected=$false;screenshots='NOT_RUN';fatal=$fatal}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath $reportPath -Encoding UTF8
}
if($fatal -or $failed -ne 0 -or $checks.Count -ne 10){exit 1}
