[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$SourceDatabase,
 [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId,
 [Parameter(Mandatory=$true)][string]$ReportDirectory
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../../tools/GeneratedPaths.ps1')
$profileRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$source=Resolve-AccessGeneratedPath $SourceDatabase '.tmp'
$build=Join-Path $profileRoot '.tmp/evidence'
if(-not $source.StartsWith($build+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'R6 disposable source required.'}
$fixture=Join-Path $build 'ui-encoding.accdb'
$report=Resolve-AccessGeneratedPath $ReportDirectory '.tmp'
New-Item -ItemType Directory -Path $report -Force | Out-Null
$output=Join-Path $report 'ui-encoding.json'
Remove-AccessIntermediate $fixture
Copy-Item -LiteralPath $source -Destination $fixture -Force
$sourceHash=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
$checks=@();$access=$null;$db=$null;$fatal=$null
function Check-Value([string]$name,[bool]$condition,$actual,$expected){
 $script:checks+=[ordered]@{name=$name;passed=$condition;actual=$actual;expected=$expected}
 Write-Output ((@('FAIL','PASS')[[int]$condition])+': '+$name)
}
function Check-CandidateSql([string]$form,[string]$control){
 $sql=[string]$access.Eval('[Forms]!['+$form+']!['+$control+'].RowSource')
 $marker='[停止'+[char]0x30FB+'期間外]'
 Check-Value ($form+'/'+$control+' Unicode SQL marker') ($sql.Contains($marker) -and -not $sql.Contains('[停止?期間外]')) $sql $marker
 $rows=$db.OpenRecordset($sql)
 try{if(-not $rows.EOF){$rows.MoveLast()};$rowCount=[int]$rows.RecordCount;Check-Value ($form+'/'+$control+' actual DAO query') ($rowCount -ge 0) $rowCount 'query executes'}
 finally{$rows.Close();[Runtime.InteropServices.Marshal]::FinalReleaseComObject($rows)|Out-Null}
}
try{
 $access=New-Object -ComObject Access.Application;$access.Visible=$false;$access.OpenCurrentDatabase($fixture);$db=$access.CurrentDb()
 $access.DoCmd.OpenForm('frmStudentSearch')
 Check-CandidateSql 'frmStudentSearch' 'cboClass'
 $access.DoCmd.OpenForm('frmStudentEdit')
 Check-CandidateSql 'frmStudentEdit' 'cboClass'
 foreach($control in @('cboGender','cboPrefecture','cboEnrollmentStatus','cboRelationship')){Check-CandidateSql 'frmStudentEdit' $control}
 $access.DoCmd.OpenForm('frmDuplicateConfirm')
 $actual=[string]$access.Eval('[Forms]![frmDuplicateConfirm]![lblPrompt].Caption')
 $expected='0件の同一人物候補があります。表示は最大20件です。氏名'+[char]0x30FB+'生年月日'+[char]0x30FB+'クラスを確認し、別人として続行する理由を入力してください。'
 Check-Value 'production duplicate confirmation Unicode caption' ([StringComparer]::Ordinal.Equals($actual,$expected)) $actual $expected
}catch{$fatal=$_.Exception.ToString();Write-Output $fatal}
finally{
 if($null -ne $db){$db.Close();[Runtime.InteropServices.Marshal]::FinalReleaseComObject($db)|Out-Null;$db=$null}
 if($null -ne $access){try{$access.CloseCurrentDatabase()}catch{};$access.Quit(2);[Runtime.InteropServices.Marshal]::FinalReleaseComObject($access)|Out-Null;$access=$null}
 [GC]::Collect();[GC]::WaitForPendingFinalizers()
 $sourceUnchanged=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -eq $sourceHash
 $passed=@($checks|Where-Object {$_.passed}).Count;$failed=@($checks|Where-Object {-not $_.passed}).Count
 $status=if(-not $fatal -and $failed -eq 0 -and $checks.Count -eq 13 -and $sourceUnchanged){'Passed'}else{'Failed'}
 [ordered]@{runId=$RunId;status=$status;passed=$passed;failed=$failed;checks=$checks;fixture=$fixture;source=$source;sourceSha256=$sourceHash;sourceUnchanged=$sourceUnchanged;visible=$false;productionOpened=$false;sqlConnectionsOpened=0;closed=$true;fatal=$fatal}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $output -Encoding UTF8
}
if($status -ne 'Passed'){exit 1}
