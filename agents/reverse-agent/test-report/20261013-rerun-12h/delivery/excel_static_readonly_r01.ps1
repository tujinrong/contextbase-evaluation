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
$qaResult=[ordered]@{scope='READ_ONLY_EXCEL_STATIC_DISPLAY_QA';workbook=$qaInput;beforeSha256=$qaBefore;plan=$qaPlan;planSha256=$qaPlanBefore;baselineExcelProcessIds=$qaBaseline;macrosDisabled=$false;updateLinks=0;readOnly=$true;visible=$false;saved=$false;pageSetupChanged=$false;cellsOrFormatsChanged=$false;originalApplicationExecuted=$false;status='NOT_COMPLETED';cells=@();sheets=@();geometryApproved=$false}
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
  if(-not($qaValue -is [string]) -or $qaValue -cne [string]$qaItem.value){throw ('Exact literal Value2 mismatch: '+$qaItem.sheet+'!'+$qaItem.cell)}
  $qaResult.cells+= [ordered]@{sheet=[string]$qaItem.sheet;cell=[string]$qaItem.cell;value2=$qaValue;value2Type=$qaValue.GetType().FullName;text=[string]$qaCell.Text;numberFormat=[string]$qaCell.NumberFormat;widthPoints=[double]$qaCell.Width;heightPoints=[double]$qaCell.Height}
  [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($qaCell);$qaCell=$null
  [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($qaSheet);$qaSheet=$null
 }
 Write-QaStage 'all-literal-value2-cells-verified'
 $qaIndex=0
 foreach($qaName in $qaSpec.sheets){
  $qaIndex++;$qaSheet=$qaBook.Worksheets.Item([string]$qaName)
  $qaPdf=Join-Path $qaRoot ('sheet-'+$qaIndex.ToString('000')+'.pdf')
  $qaLayout=$qaSheet.PageSetup
  $qaSheetMeta=[ordered]@{sheet=[string]$qaName;printArea=[string]$qaLayout.PrintArea;printTitleRows=[string]$qaLayout.PrintTitleRows;orientation=[int]$qaLayout.Orientation;paperSize=[int]$qaLayout.PaperSize;zoom=$qaLayout.Zoom;fitToPagesWide=$qaLayout.FitToPagesWide;fitToPagesTall=$qaLayout.FitToPagesTall;pdf=$qaPdf}
  [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($qaLayout)
  Write-QaStage ('export-read-only-sheet-'+$qaIndex)
  $qaSheet.ExportAsFixedFormat(0,$qaPdf,0,$true,$false)
  if(-not(Test-Path -LiteralPath $qaPdf)){throw 'Read-only export produced no PDF'}
  $qaSheetMeta.pdfSha256=(Get-FileHash -LiteralPath $qaPdf -Algorithm SHA256).Hash.ToLowerInvariant();$qaResult.sheets+=$qaSheetMeta
  [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($qaSheet);$qaSheet=$null
 }
 $qaResult.status='STATIC_EXCEL_PDF_EXPORTED_VISUAL_REVIEW_PENDING';Write-QaStage 'static-display-export-completed'
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
