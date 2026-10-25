[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$Database,
 [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId,
 [Parameter(Mandatory=$true)][string]$ReportDirectory,
 [Parameter(Mandatory=$true)][ValidateSet('Before','After')][string]$Phase
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../../tools/GeneratedPaths.ps1')
$profileRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$ownedBuild=Join-Path $profileRoot '.tmp'
$fixture=Resolve-AccessGeneratedPath $Database '.tmp'
if(-not $fixture.StartsWith($ownedBuild+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Disposable Access/.tmp copy required.'}
$report=Resolve-AccessGeneratedPath $ReportDirectory '.tmp'
New-Item -ItemType Directory -Path $report -Force|Out-Null
$outputPath=Join-Path $report 'message-encoding.json'
Add-Type -TypeDefinition 'using System;using System.Runtime.InteropServices;public static class AccessVbaCodePage{[DllImport("kernel32.dll")]public static extern uint GetACP();[DllImport("user32.dll")]public static extern uint GetWindowThreadProcessId(IntPtr hwnd,out uint processId);}'
$ansiCodePage=[int][AccessVbaCodePage]::GetACP()
$encoding=[Text.Encoding]::GetEncoding($ansiCodePage,[Text.EncoderFallback]::ExceptionFallback,[Text.DecoderFallback]::ExceptionFallback)
$sourceScan=@()
foreach($file in (Get-ChildItem -LiteralPath (Join-Path $profileRoot 'Modules'),(Join-Path $profileRoot 'Classes') -File|Where-Object {$_.Extension -in @('.bas','.cls')})) {
 $lineNumber=0
 foreach($line in (Get-Content -LiteralPath $file.FullName -Encoding UTF8)) {
  $lineNumber++
  foreach($literal in [regex]::Matches($line,'"(?:""|[^"])*"')) {
   $value=$literal.Value.Substring(1,$literal.Value.Length-2).Replace('""','"')
   foreach($character in $value.ToCharArray()) {
    try {[void]$encoding.GetBytes([string]$character)}
    catch {$sourceScan+=[ordered]@{path=$file.FullName;line=$lineNumber;character=[string]$character;codePoint=('U+{0:X4}' -f [int]$character);literal=$value}}
   }
  }
 }
}
$spec=Join-Path $profileRoot '../../spec/Access/共通/05_チェック・メッセージ設計.md'
$parameters=[ordered]@{field='検証項目';max='8';fromField='開始日';toField='終了日';correlationId='TEST-REQ';count='3';minDate='1900-01-01';maxDate='2026-10-12';minYear='1900';maxYear='9998';studentNo='TEST-ACE-099'}
$suffix=(@($parameters.GetEnumerator()|ForEach-Object {$_.Key+'='+$_.Value}) -join '|')
$expected=@()
foreach($line in (Get-Content -LiteralPath $spec -Encoding UTF8)) {
 if($line -match '^\| ([IEW]-[A-Z]+-[0-9]{3}) \| (.+) \|$') {
  $id=$Matches[1];$text=$Matches[2]
  foreach($parameter in $parameters.GetEnumerator()) {$text=$text.Replace('{'+$parameter.Key+'}',[string]$parameter.Value)}
  $expected+=[ordered]@{id=$id;expected=$id+': '+$text;input=$id+'|'+$suffix}
 }
}
if($expected.Count -eq 0){throw 'No message definitions found.'}
$access=$null;$checks=@();$modules=@();$fatal=$null;$fieldCheck=$null;$fileFormat=$null;$officeVersion=$null
$currentProject=$null;$vbe=$null;$project=$null;$components=$null;$component=$null;$codeModule=$null
$cleanupErrors=New-Object 'Collections.Generic.List[string]'
$startedAt=[DateTime]::UtcNow
$existingProcessIds=@(Get-Process MSACCESS -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
$ownedProcessId=0;$ownedProcessStart=$null;$ownedProcess=$null;$ownsAccessProcess=$false
$exitObserved=$false;$processExitCode=$null;$quitRequested=$false;$cleanExit=$false
function Release-MessageCom([ref]$Reference,[string]$Name) {
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
 [void][AccessVbaCodePage]::GetWindowThreadProcessId([IntPtr]([long]$access.hWndAccessApp()),[ref]$windowProcessId)
 $ownedProcessId=[int]$windowProcessId
 if($ownedProcessId -eq 0 -or $ownedProcessId -in $existingProcessIds){throw 'Refusing to use an existing or unidentified Access process.'}
 $ownedProcess=Get-Process -Id $ownedProcessId
 [void]$ownedProcess.Handle
 $ownedProcessStart=$ownedProcess.StartTime.ToUniversalTime()
 if($ownedProcessStart -lt $startedAt.AddSeconds(-2)){throw 'Access process predates this message-encoding test.'}
 $ownsAccessProcess=$true
 $access.Visible=$false;$officeVersion=[string]$access.Version
 $beforeHash=(Get-FileHash -LiteralPath $fixture -Algorithm SHA256).Hash
 $access.OpenCurrentDatabase($fixture)
 $currentProject=$access.CurrentProject
 $fileFormat=[int]$currentProject.FileFormat
 foreach($item in $expected) {
  $actual=[string]$access.Eval('MessageText("'+$item.input.Replace('"','""')+'")')
  $checks+=[ordered]@{id=$item.id;expected=$item.expected;actual=$actual;passed=([StringComparer]::Ordinal.Equals($actual,$item.expected))}
 }
 $fieldExpected='卒業'+[char]0x30FB+'退学日'
 $fieldActual=[string]$access.Eval('FieldLabel("enrollment_end_date")')
 $fieldCheck=[ordered]@{id='FieldLabel(enrollment_end_date)';expected=$fieldExpected;actual=$fieldActual;passed=([StringComparer]::Ordinal.Equals($fieldExpected,$fieldActual))}
 $vbe=$access.VBE
 $project=$vbe.ActiveVBProject
 $components=$project.VBComponents
 foreach($name in @('modMessages','modCandidates','modConfirmationForms')) {
  $component=$components.Item($name)
  $codeModule=$component.CodeModule
  $code=$codeModule.Lines(1,$codeModule.CountOfLines)
  $codePath=Join-Path $report ($name+'.vba.txt')
  [IO.File]::WriteAllText($codePath,$code,(New-Object Text.UTF8Encoding($true)))
  $modules+=[ordered]@{name=$name;runtimeSource=$codePath;sha256=(Get-FileHash -LiteralPath $codePath -Algorithm SHA256).Hash}
  Release-MessageCom ([ref]$codeModule) ($name+'.CodeModule')
  Release-MessageCom ([ref]$component) $name
 }
}catch{$fatal=$_.Exception.ToString();Write-Output $fatal}
finally {
 # Release every named child RCW before closing the project or quitting its parent.
 # In particular CodeModule/VBE finalizers must not run against a terminated Access server.
 Release-MessageCom ([ref]$codeModule) 'CodeModule'
 Release-MessageCom ([ref]$component) 'Component'
 Release-MessageCom ([ref]$components) 'VBComponents'
 Release-MessageCom ([ref]$project) 'VBProject'
 Release-MessageCom ([ref]$vbe) 'VBE'
 Release-MessageCom ([ref]$currentProject) 'CurrentProject'
 try{[GC]::Collect();[GC]::WaitForPendingFinalizers()}catch{$cleanupErrors.Add('Pre-Quit finalizers: '+$_.Exception.Message)}
 if($null -ne $access -and $ownsAccessProcess){
  try{$access.CloseCurrentDatabase()}catch{$cleanupErrors.Add('CloseCurrentDatabase: '+$_.Exception.Message)}
  try{$access.Quit(2);$quitRequested=$true}catch{$cleanupErrors.Add('Quit: '+$_.Exception.Message)}
 }
 Release-MessageCom ([ref]$access) 'Access.Application'
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
 $passed=@($checks|Where-Object {$_.passed}).Count
 $failed=@($checks|Where-Object {-not $_.passed}).Count
 $status=if($fatal -or -not $cleanExit){'Failed'}elseif($Phase -eq 'Before' -and $failed -gt 0){'BEFORE_CORRUPTION_OBSERVED'}elseif($Phase -eq 'After' -and $failed -eq 0 -and $fieldCheck.passed -and $sourceScan.Count -eq 0 -and $fileFormat -eq 12){'Passed'}else{'Failed'}
 [ordered]@{runId=$RunId;phase=$Phase;status=$status;startedAt=$startedAt.ToString('o');completedAt=[DateTime]::UtcNow.ToString('o');systemAnsiCodePage=$ansiCodePage;spec=$spec;specSha256=(Get-FileHash -LiteralPath $spec -Algorithm SHA256).Hash;messageDefinitions=$expected.Count;messagePassed=$passed;messageFailed=$failed;messageChecks=$checks;dateMessage=($checks|Where-Object {$_.id -eq 'E-DATE-001'});fieldLabel=$fieldCheck;sourceLiteralScan=[ordered]@{unrepresentableOccurrenceCount=$sourceScan.Count;uniqueCharacters=@($sourceScan.codePoint|Sort-Object -Unique);occurrences=$sourceScan};runtimeModules=$modules;fileFormat=$fileFormat;officeVersion=$officeVersion;fixture=$fixture;fixtureBeforeSha256=$beforeHash;fixtureAfterSha256=(Get-FileHash -LiteralPath $fixture -Algorithm SHA256).Hash;visible=$false;sqlConnectionsOpened=0;productionOpened=$false;ownedProcess=$ownedProcessId;ownedProcessStart=$(if($ownedProcessStart){$ownedProcessStart.ToString('o')}else{$null});existingProcessIds=$existingProcessIds;quitRequested=$quitRequested;exitObserved=$exitObserved;processExitCode=$processExitCode;cleanExit=$cleanExit;cleanupErrors=@($cleanupErrors);fatal=$fatal}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $outputPath -Encoding UTF8
 Write-Output ('Phase='+$Phase+' status='+$status+' noticeMatches='+$passed+' mismatches='+$failed+' nonANSI='+$sourceScan.Count)
}
if($status -eq 'Failed'){exit 1}
