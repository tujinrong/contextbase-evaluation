param([Parameter(Mandatory=$true)][string]$Plan,[Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$qaRoot=[System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $qaRoot -ErrorAction Stop | Out-Null
$qaPlan=[System.IO.Path]::GetFullPath($Plan)
$qaSpec=Get-Content -LiteralPath $qaPlan -Encoding UTF8 -Raw | ConvertFrom-Json
$qaInput=[System.IO.Path]::GetFullPath($qaSpec.workbook)
$qaBefore=(Get-FileHash -LiteralPath $qaInput -Algorithm SHA256).Hash.ToLowerInvariant()
if($qaBefore -cne $qaSpec.workbookSha256){throw 'Workbook exact SHA mismatch'}
$qaPlanBefore=(Get-FileHash -LiteralPath $qaPlan -Algorithm SHA256).Hash.ToLowerInvariant()
$qaBaseline=@(Get-Process -Name EXCEL -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
$qaExcel=$null;$qaBook=$null;$qaSheet=$null;$qaCell=$null;$qaOwnedId=$null
$qaResult=[ordered]@{scope='READ_ONLY_EXCEL_RANGE_BITMAP_QA';workbook=$qaInput;beforeSha256=$qaBefore;plan=$qaPlan;planSha256=$qaPlanBefore;baselineExcelProcessIds=$qaBaseline;macrosDisabled=$false;updateLinks=0;readOnly=$true;visible=$false;saved=$false;pageSetupChanged=$false;cellsOrFormatsChanged=$false;originalApplicationExecuted=$false;status='NOT_COMPLETED';cells=@();sheets=@();geometryApproved=$false}
function Write-QaStage([string]$stage){[ordered]@{utc=[DateTime]::UtcNow.ToString('o');stage=$stage;helperPid=$PID;excelPid=$qaOwnedId} | ConvertTo-Json -Compress | Add-Content -LiteralPath (Join-Path $qaRoot 'stages.jsonl') -Encoding utf8}
try {
 Write-QaStage 'baseline-checked'
 if($qaBaseline.Count -ne 0){throw 'Existing Excel detected; no attach or second instance allowed'}
 Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class StaticQaWindow { [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd,out uint processId); }'
 $qaExcel=New-Object -ComObject Excel.Application
 [uint32]$qaWindowId=0;[void][StaticQaWindow]::GetWindowThreadProcessId([IntPtr]$qaExcel.Hwnd,[ref]$qaWindowId)
 if($qaWindowId -eq 0 -or $qaBaseline -contains [int]$qaWindowId){throw 'Newly owned Excel cannot be proven'}
 $qaOwnedId=[int]$qaWindowId;$qaProcess=Get-Process -Id $qaOwnedId
 if($qaProcess.ProcessName -ne 'EXCEL'){throw 'COM owned process is not Excel'}
 [ordered]@{excelPid=$qaOwnedId;helperPid=$PID;excelStartTimeUtc=$qaProcess.StartTime.ToUniversalTime().ToString('o');baselineExcelProcessIds=$qaBaseline;ownership='NEW_COM_APPLICATION_HWND'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $qaRoot 'owned-excel.json') -Encoding utf8
 $qaExcel.Visible=$false;$qaExcel.DisplayAlerts=$false;$qaExcel.AskToUpdateLinks=$false;$qaExcel.EnableEvents=$false;$qaExcel.AutomationSecurity=3
 $qaResult.macrosDisabled=$true;Write-QaStage 'macro-link-events-disabled'
 $qaBook=$qaExcel.Workbooks.Open($qaInput,0,$true)
 if(-not $qaBook.ReadOnly){throw 'Excel did not open read-only'}
 $qaResult.excelVersion=[string]$qaExcel.Version;$qaResult.excelBuild=[string]$qaExcel.Build
 Write-QaStage 'read-only-opened'
 foreach($qaItem in $qaSpec.cells){
  $qaSheet=$qaBook.Worksheets.Item([string]$qaItem.sheet);$qaCell=$qaSheet.Range([string]$qaItem.cell)
  $qaValue=$qaCell.Value2
  if(([string]$qaItem.value -ne '' -and (-not($qaValue -is [string]) -or $qaValue -cne [string]$qaItem.value)) -or ([string]$qaItem.value -eq '' -and $null -ne $qaValue -and $qaValue -cne '')){throw ('Exact literal Value2 mismatch: '+$qaItem.sheet+'!'+$qaItem.cell)}
  $qaResult.cells+= [ordered]@{sheet=[string]$qaItem.sheet;cell=[string]$qaItem.cell;value2=$qaValue;value2Type=$(if($null -eq $qaValue){"null"}else{$qaValue.GetType().FullName});text=[string]$qaCell.Text;numberFormat=[string]$qaCell.NumberFormat;widthPoints=[double]$qaCell.Width;heightPoints=[double]$qaCell.Height}
  [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($qaCell);$qaCell=$null
  [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($qaSheet);$qaSheet=$null
 }
 Write-QaStage 'all-literal-value2-cells-verified'
 Add-Type -AssemblyName System.Windows.Forms
 Add-Type -AssemblyName System.Drawing
 Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class OwnClipboardSequence { [DllImport("user32.dll")] public static extern uint GetClipboardSequenceNumber(); }'
 $qaResult.clipboardSideEffect='Own Excel Range.CopyPicture temporarily overwrites clipboard; no prior content is read or output.'
 $qaIndex=0
 foreach($qaPreview in $qaSpec.previews){
  $qaIndex++;$qaSheet=$qaBook.Worksheets.Item([string]$qaPreview.sheet)
  $qaCell=$qaSheet.Range([string]$qaPreview.range)
  Write-QaStage ('copy-own-static-picture-'+$qaIndex)
  $qaSequenceBefore=[OwnClipboardSequence]::GetClipboardSequenceNumber()
  $qaCell.CopyPicture(1,2)
  $qaSequenceOwn=[OwnClipboardSequence]::GetClipboardSequenceNumber()
  if($qaSequenceOwn -eq $qaSequenceBefore){throw 'CopyPicture did not change clipboard; preexisting contents will not be read'}
  $qaImage=$null
  for($qaRetry=0;$qaRetry -lt 10 -and $null -eq $qaImage;$qaRetry++){
   Start-Sleep -Milliseconds 100
   if([OwnClipboardSequence]::GetClipboardSequenceNumber() -ne $qaSequenceOwn){throw 'Clipboard changed after own CopyPicture; refuse content read'}
   $qaImage=[System.Windows.Forms.Clipboard]::GetImage()
   if([OwnClipboardSequence]::GetClipboardSequenceNumber() -ne $qaSequenceOwn){if($null -ne $qaImage){$qaImage.Dispose()};throw 'Clipboard raced during own bitmap read; no output'}
  }
  if($null -eq $qaImage){throw 'Own Range.CopyPicture returned no bitmap'}
  try{
   $qaPng=Join-Path $qaRoot ('preview-'+$qaIndex.ToString('000')+'.png')
   $qaImage.Save($qaPng,[System.Drawing.Imaging.ImageFormat]::Png)
   $qaResult.sheets+=[ordered]@{sheet=[string]$qaPreview.sheet;range=[string]$qaPreview.range;png=$qaPng;width=$qaImage.Width;height=$qaImage.Height;pngSha256=(Get-FileHash -LiteralPath $qaPng -Algorithm SHA256).Hash.ToLowerInvariant();projection='Excel Range.CopyPicture xlScreen xlBitmap';clipboardSequenceBefore=$qaSequenceBefore;clipboardOwnSequence=$qaSequenceOwn;clipboardOnlyOwnContentRead=$true;cellOrFormatChanges=$false}
  }finally{$qaImage.Dispose()}
  [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($qaCell);$qaCell=$null
  [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($qaSheet);$qaSheet=$null
 }
 $qaResult.status='STATIC_EXCEL_BITMAP_EXPORTED_VISUAL_REVIEW_PENDING';Write-QaStage 'static-display-export-completed'
} catch {$qaResult.status='FAILED_OR_NOT_TESTED';$qaResult.error=$_.Exception.Message}
finally {
 if($null -ne $qaBook){try{$qaBook.Close($false);Write-QaStage 'closed-without-save'}catch{$qaResult.closeError=$_.Exception.Message}}
 if($null -ne $qaExcel -and $null -ne $qaOwnedId){try{$qaExcel.Quit();Write-QaStage 'owned-excel-quit'}catch{$qaResult.quitError=$_.Exception.Message}}
 foreach($qaObject in @($qaCell,$qaSheet,$qaBook,$qaExcel)){if($null -ne $qaObject){try{[void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($qaObject)}catch{}}}
 [GC]::Collect();[GC]::WaitForPendingFinalizers()
 $qaResult.ownedExcelProcessId=$qaOwnedId;$qaResult.afterSha256=(Get-FileHash -LiteralPath $qaInput -Algorithm SHA256).Hash.ToLowerInvariant()
 $qaResult.workbookBytesUnchanged=$qaBefore -ceq $qaResult.afterSha256
 $qaResult.planBytesUnchanged=$qaPlanBefore -ceq (Get-FileHash -LiteralPath $qaPlan -Algorithm SHA256).Hash.ToLowerInvariant()
 if(-not $qaResult.workbookBytesUnchanged -or -not $qaResult.planBytesUnchanged){$qaResult.status='FAILED_BYTES_CHANGED'}
 $qaResult | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $qaRoot 'result.json') -Encoding utf8
 [ordered]@{status=$qaResult.status;workbookBytesUnchanged=$qaResult.workbookBytesUnchanged;literalCount=$qaResult.cells.Count;sheets=$qaResult.sheets.Count;error=$qaResult.error} | ConvertTo-Json -Compress | Write-Output
}
