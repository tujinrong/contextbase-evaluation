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
$access=$null;$currentProject=$null;$doCmd=$null;$forms=$null;$form=$null;$controls=$null;$control=$null
$fatal=$null;$officeVersion=$null;$databaseOpen=$false;$searchOpened=$false
$cleanupErrors=New-Object 'Collections.Generic.List[string]'
$startedAt=[DateTime]::UtcNow
$existingProcessIds=@(Get-Process MSACCESS -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
$ownedProcessId=0;$ownedProcessStart=$null;$ownedProcess=$null;$ownsAccessProcess=$false
$exitObserved=$false;$processExitCode=$null;$quitRequested=$false;$cleanExit=$false
$paths=@(@($backendPath,$frontendPath)|Select-Object -Unique)
Add-Type -TypeDefinition 'using System;using System.Runtime.InteropServices;public static class AccessFormatProcess{[DllImport("user32.dll")]public static extern uint GetWindowThreadProcessId(IntPtr hwnd,out uint processId);}'
function Check([bool]$ok,[string]$name) {
    $checks.Add([ordered]@{name=$name;passed=$ok})
    Write-Output "$(if($ok){'PASS'}else{'FAIL'}): $name"
}
function Release-FormatCom([ref]$Reference,[string]$Name) {
    try {
        if($null -ne $Reference.Value -and [Runtime.InteropServices.Marshal]::IsComObject($Reference.Value)) {
            [Runtime.InteropServices.Marshal]::FinalReleaseComObject($Reference.Value)|Out-Null
        }
    }catch{$script:cleanupErrors.Add($Name+': '+$_.Exception.Message)}
    finally{$Reference.Value=$null}
}
try {
    $access=New-Object -ComObject Access.Application
    [uint32]$windowProcessId=0
    [void][AccessFormatProcess]::GetWindowThreadProcessId([IntPtr]([long]$access.hWndAccessApp()),[ref]$windowProcessId)
    $ownedProcessId=[int]$windowProcessId
    if($ownedProcessId -eq 0 -or $ownedProcessId -in $existingProcessIds){throw 'Refusing to use an existing or unidentified Access process.'}
    $ownedProcess=Get-Process -Id $ownedProcessId
    [void]$ownedProcess.Handle
    $ownedProcessStart=$ownedProcess.StartTime.ToUniversalTime()
    if($ownedProcessStart -lt $startedAt.AddSeconds(-2)){throw 'Access process predates this format-and-state test.'}
    $ownsAccessProcess=$true
    $access.Visible=$false;$officeVersion=[string]$access.Version
    foreach($path in $paths) {
        $header=[Text.Encoding]::ASCII.GetString([IO.File]::ReadAllBytes($path),0,64)
        Check ($header.Contains('Standard ACE DB')) ('ACE physical header: '+[IO.Path]::GetFileName($path))
        $before=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
        try {
            $databaseOpen=$true
            $access.OpenCurrentDatabase($path)
            $currentProject=$access.CurrentProject
            $format=[int]$currentProject.FileFormat
            Check ($format -eq 12) ('Access FileFormat=12: '+[IO.Path]::GetFileName($path))
            $files.Add([ordered]@{path=$path;fileFormat=$format;header=$header;sha256Before=$before})
            if($path -eq $frontendPath) {
                $doCmd=$access.DoCmd
                $doCmd.OpenForm('frmStudentSearch');$searchOpened=$true
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
                $forms=$access.Forms
                $form=$forms.Item('frmStudentSearch')
                $controls=$form.Controls
                $retired=New-Object 'Collections.Generic.List[string]'
                # Indexed access avoids an implicit COM enumerator retained by a pipeline.
                for($index=0;$index -lt $controls.Count;$index++) {
                    try {
                        $control=$controls.Item($index)
                        $controlName=[string]$control.Name
                        if($controlName -in @('cboPageSize','cmdFirst','cmdPrev','cmdNext','cmdLast','chkUnassignedOnly')){$retired.Add($controlName)}
                    }finally{Release-FormatCom ([ref]$control) 'Search control'}
                }
                Check ($retired.Count -eq 0) 'retired search/range controls absent'
            }
        }finally{
            Release-FormatCom ([ref]$control) 'Search control'
            Release-FormatCom ([ref]$controls) 'Controls'
            Release-FormatCom ([ref]$form) 'Search form'
            Release-FormatCom ([ref]$forms) 'Forms'
            if($searchOpened -and $null -ne $doCmd){
                try{$doCmd.Close(2,'frmStudentSearch',2);$searchOpened=$false}catch{$cleanupErrors.Add('Close search form: '+$_.Exception.Message)}
            }
            Release-FormatCom ([ref]$doCmd) 'DoCmd'
            Release-FormatCom ([ref]$currentProject) 'CurrentProject'
            try{[GC]::Collect();[GC]::WaitForPendingFinalizers()}catch{$cleanupErrors.Add('Pre-close finalizers: '+$_.Exception.Message)}
            if($databaseOpen){
                try{$access.CloseCurrentDatabase();$databaseOpen=$false}catch{$cleanupErrors.Add('CloseCurrentDatabase: '+$_.Exception.Message)}
            }
        }
    }
} catch {$fatal=$_.Exception.ToString()+[Environment]::NewLine+$_.ScriptStackTrace;Write-Output $fatal}
finally {
    Release-FormatCom ([ref]$control) 'Search control'
    Release-FormatCom ([ref]$controls) 'Controls'
    Release-FormatCom ([ref]$form) 'Search form'
    Release-FormatCom ([ref]$forms) 'Forms'
    if($searchOpened -and $null -ne $doCmd -and $ownsAccessProcess){
        try{$doCmd.Close(2,'frmStudentSearch',2);$searchOpened=$false}catch{$cleanupErrors.Add('Final close search form: '+$_.Exception.Message)}
    }
    Release-FormatCom ([ref]$doCmd) 'DoCmd'
    Release-FormatCom ([ref]$currentProject) 'CurrentProject'
    try{[GC]::Collect();[GC]::WaitForPendingFinalizers()}catch{$cleanupErrors.Add('Pre-Quit finalizers: '+$_.Exception.Message)}
    if($null -ne $access -and $ownsAccessProcess) {
        if($databaseOpen){try{$access.CloseCurrentDatabase();$databaseOpen=$false}catch{$cleanupErrors.Add('Final CloseCurrentDatabase: '+$_.Exception.Message)}}
        try{$access.Quit(2);$quitRequested=$true}catch{$cleanupErrors.Add('Quit: '+$_.Exception.Message)}
    }
    Release-FormatCom ([ref]$access) 'Access.Application'
    try{[GC]::Collect();[GC]::WaitForPendingFinalizers()}catch{$cleanupErrors.Add('Post-Quit finalizers: '+$_.Exception.Message)}
    if($null -ne $ownedProcess){
        try{
            if($ownsAccessProcess){
                $exitObserved=$ownedProcess.WaitForExit(10000)
                if($exitObserved){$processExitCode=$ownedProcess.ExitCode}else{$cleanupErrors.Add('Owned Access process did not exit within 10 seconds.')}
                if($exitObserved -and $processExitCode -ne 0){$cleanupErrors.Add('Owned Access process exited abnormally: '+$processExitCode)}
            }
        }catch{$cleanupErrors.Add('Owned process exit observation: '+$_.Exception.Message)}
        finally{$ownedProcess.Dispose();$ownedProcess=$null}
    }
    $cleanExit=$ownsAccessProcess -and $quitRequested -and $exitObserved -and $processExitCode -eq 0 -and $cleanupErrors.Count -eq 0
    foreach($item in $files) {$item.sha256After=(Get-FileHash -LiteralPath $item.path -Algorithm SHA256).Hash}
    $failed=@($checks|Where-Object {-not $_.passed}).Count
    [ordered]@{runId=$RunId;profile='Access';status=$(if(-not $fatal -and $failed -eq 0 -and $checks.Count -eq ($paths.Count*2+6) -and $cleanExit){'Passed'}else{'Failed'});startedAt=$startedAt.ToString('o');completedAt=[DateTime]::UtcNow.ToString('o');passed=@($checks|Where-Object {$_.passed}).Count;failed=$failed;checks=$checks;files=$files;initialControls=$defaults;officeVersion=$officeVersion;fixtureOnly=$true;visible=$false;sharedSqlConnected=$false;screenshots='NOT_RUN';ownedProcess=$ownedProcessId;ownedProcessStart=$(if($ownedProcessStart){$ownedProcessStart.ToString('o')}else{$null});existingProcessIds=$existingProcessIds;quitRequested=$quitRequested;exitObserved=$exitObserved;processExitCode=$processExitCode;cleanExit=$cleanExit;cleanupErrors=@($cleanupErrors);fatal=$fatal}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath $reportPath -Encoding UTF8
}
if($fatal -or $failed -ne 0 -or $checks.Count -ne ($paths.Count*2+6) -or -not $cleanExit){exit 1}
