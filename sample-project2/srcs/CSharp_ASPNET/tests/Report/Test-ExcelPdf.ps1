param([string]$RunId='20261029-sp2-ui-conformance')
$ErrorActionPreference='Stop'
$sp2Root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location -LiteralPath $sp2Root
$sp2Stage=[IO.Path]::GetFullPath((Join-Path $sp2Root '.tmp/report-print'))
$sp2Final=[IO.Path]::GetFullPath((Join-Path $sp2Root 'build/test-results/print-review'))
if(-not $sp2Stage.StartsWith((Join-Path $sp2Root '.tmp')+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Print stage escaped the method scratch directory.'}
foreach($sp2Path in @($sp2Stage,$sp2Final)){
  $sp2Parent=$sp2Path
  while($sp2Parent -and $sp2Parent.StartsWith($sp2Root,[StringComparison]::OrdinalIgnoreCase)){
    if((Test-Path -LiteralPath $sp2Parent) -and ((Get-Item -LiteralPath $sp2Parent -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Reparse-point print path refused.'}
    if($sp2Parent -eq $sp2Root){break}
    $sp2Parent=[IO.Path]::GetDirectoryName($sp2Parent)
  }
}
New-Item -ItemType Directory -Path $sp2Final -Force|Out-Null
[ordered]@{schema='print-review/2.0';projectId='sample-project2';profileId='CSharp_ASPNET';runId=$RunId;status='RUNNING';startedAtUtc=[DateTimeOffset]::UtcNow.ToString('o');formalScore=$null}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $sp2Final 'record.json') -Encoding UTF8
if(Test-Path -LiteralPath $sp2Stage){Remove-Item -LiteralPath $sp2Stage -Recurse -Force}
New-Item -ItemType Directory -Path $sp2Stage -Force|Out-Null
if(-not ('SP2ExcelNative' -as [type])){Add-Type -TypeDefinition 'using System;using System.Runtime.InteropServices;public static class SP2ExcelNative{[DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd,out uint processId);}' }
$sp2Before=@(Get-Process EXCEL -ErrorAction SilentlyContinue|ForEach-Object Id)
$sp2CleanupErrors=[Collections.Generic.List[string]]::new()
function Release-SP2Com([object]$Value,[string]$Name){
  if($null -ne $Value -and [Runtime.InteropServices.Marshal]::IsComObject($Value)){
    try{[void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)}catch{$sp2CleanupErrors.Add($Name+': '+$_.Exception.Message)}
  }
}
$sp2Excel=$null;$sp2Books=$null;$sp2Book=$null;$sp2Sheets=$null;$sp2Sheet=$null;$sp2Setup=$null
$sp2OwnedProcess=$null;$sp2OwnedId=0;$sp2OwnsExcel=$false;$sp2CleanExit=$false;$sp2ExitCode=$null;$sp2Failure=$null
$sp2Records=[Collections.Generic.List[object]]::new()
$sp2Generation=Get-Content -LiteralPath 'build/test-results/report-format-generation.json' -Raw -Encoding UTF8|ConvertFrom-Json
$sp2InputsHash=(Get-FileHash -LiteralPath 'build/generation/inputs.json' -Algorithm SHA256).Hash.ToLowerInvariant()
$sp2ReportDll=Join-Path $sp2Root 'build/publish/CareerManagement.Infrastructure.dll'
if((Get-FileHash -LiteralPath $sp2ReportDll -Algorithm SHA256).Hash.ToLowerInvariant() -cne $sp2Generation.reportAssemblySha256){throw 'Report generator must use the same published production assembly.'}
$sp2MeasurementHash=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
$sp2PdfInfo=(Get-Command pdfinfo -ErrorAction Stop).Source
try{
  $sp2Excel=New-Object -ComObject Excel.Application
  [uint32]$sp2FoundId=0
  [void][SP2ExcelNative]::GetWindowThreadProcessId([IntPtr]$sp2Excel.Hwnd,[ref]$sp2FoundId)
  if($sp2FoundId -eq 0 -or $sp2FoundId -in $sp2Before){throw 'Excel did not provide a newly owned process; existing instance preserved.'}
  $sp2OwnedId=[int]$sp2FoundId;$sp2OwnsExcel=$true
  $sp2OwnedProcess=Get-Process -Id $sp2OwnedId -ErrorAction Stop
  [void]$sp2OwnedProcess.Handle
  $sp2Excel.Visible=$false;$sp2Excel.DisplayAlerts=$false;$sp2Excel.EnableEvents=$false;$sp2Excel.AutomationSecurity=3
  $sp2Version=[string]$sp2Excel.Version
  $sp2Books=$sp2Excel.Workbooks
  foreach($sp2Pair in @(@('normal-seed-career','seed-career'),@('normal-literal-career','literal-career'),@('maximum-report','maximum-report'))){
    $sp2Source=Join-Path $sp2Root ('.tmp/report-format-review/'+$sp2Pair[0]+'.xlsx')
    $sp2Expected=@($sp2Generation.records|Where-Object file -EQ ('.tmp/report-format-review/'+$sp2Pair[0]+'.xlsx'))
    if($sp2Expected.Count -ne 1 -or (Get-FileHash -LiteralPath $sp2Source -Algorithm SHA256).Hash.ToLowerInvariant() -cne $sp2Expected[0].sha256){throw 'Saved report fixture differs from generation evidence.'}
    $sp2Workbook=Join-Path $sp2Stage ($sp2Pair[1]+'.xlsx');Copy-Item -LiteralPath $sp2Source -Destination $sp2Workbook -Force
    $sp2Pdf=Join-Path $sp2Stage ($sp2Pair[1]+'.pdf')
    $sp2SheetRecords=[Collections.Generic.List[object]]::new()
    try{
      $sp2Book=$sp2Books.Open($sp2Workbook,0,$true)
      if(-not $sp2Book.ReadOnly){throw 'Report must be opened read-only.'}
      $sp2Sheets=$sp2Book.Worksheets
      if($sp2Sheets.Count -ne 2){throw 'Report sheet count is not two.'}
      for($sp2Index=1;$sp2Index -le $sp2Sheets.Count;$sp2Index++){
        try{
          $sp2Sheet=$sp2Sheets.Item($sp2Index);$sp2Setup=$sp2Sheet.PageSetup
          if([int]$sp2Setup.PaperSize -ne 9 -or [int]$sp2Setup.Orientation -ne 1 -or [int]$sp2Setup.FitToPagesWide -ne 1){throw 'Native Excel page setup differs from A4 portrait one-page-width contract.'}
          $sp2SheetRecords.Add([ordered]@{name=[string]$sp2Sheet.Name;paperSize=[int]$sp2Setup.PaperSize;orientation=[int]$sp2Setup.Orientation;printArea=[string]$sp2Setup.PrintArea;fitToPagesWide=[int]$sp2Setup.FitToPagesWide})
        }finally{Release-SP2Com $sp2Setup 'PageSetup';$sp2Setup=$null;Release-SP2Com $sp2Sheet 'Worksheet';$sp2Sheet=$null}
      }
      $sp2Book.ExportAsFixedFormat(0,$sp2Pdf)
    }finally{
      Release-SP2Com $sp2Sheets 'Worksheets';$sp2Sheets=$null
      if($sp2Book){try{$sp2Book.Close($false)}catch{$sp2CleanupErrors.Add('Workbook.Close: '+$_.Exception.Message)}}
      Release-SP2Com $sp2Book 'Workbook';$sp2Book=$null
    }
    $sp2Info=& $sp2PdfInfo $sp2Pdf
    if($LASTEXITCODE -ne 0){throw 'PDF metadata extraction failed.'}
    $sp2PageLine=@($sp2Info|Select-String '^Pages:\s+(\d+)\s*$')
    if($sp2PageLine.Count -ne 1){throw 'PDF page count was not available.'}
    $sp2Pages=[int]$sp2PageLine[0].Matches[0].Groups[1].Value
    if($sp2Pages -lt 2){throw 'Both report sheets must be present in the native PDF.'}
    $sp2Records.Add([ordered]@{workbook=('build/test-results/print-review/'+$sp2Pair[1]+'.xlsx');workbookSha256=(Get-FileHash -LiteralPath $sp2Workbook -Algorithm SHA256).Hash.ToLowerInvariant();pdf=('build/test-results/print-review/'+$sp2Pair[1]+'.pdf');pdfSha256=(Get-FileHash -LiteralPath $sp2Pdf -Algorithm SHA256).Hash.ToLowerInvariant();pages=$sp2Pages;sheets=$sp2SheetRecords.ToArray();readOnly=$true;status='EXPORTED_FOR_VISUAL_REVIEW'})
    Write-Output ('Native Excel PDF exported: '+$sp2Pair[1]+' ('+$sp2Pages+' pages).')
  }
}catch{$sp2Failure=$_.Exception.Message}
finally{
  Release-SP2Com $sp2Setup 'PageSetup.finally';$sp2Setup=$null
  Release-SP2Com $sp2Sheet 'Worksheet.finally';$sp2Sheet=$null
  Release-SP2Com $sp2Sheets 'Worksheets.finally';$sp2Sheets=$null
  if($sp2Book){try{$sp2Book.Close($false)}catch{$sp2CleanupErrors.Add('Workbook.Close.finally: '+$_.Exception.Message)}}
  Release-SP2Com $sp2Book 'Workbook.finally';$sp2Book=$null
  Release-SP2Com $sp2Books 'Workbooks';$sp2Books=$null
  [GC]::Collect();[GC]::WaitForPendingFinalizers();[GC]::Collect();[GC]::WaitForPendingFinalizers()
  if($sp2Excel -and $sp2OwnsExcel){try{$sp2Excel.Quit()}catch{$sp2CleanupErrors.Add('Excel.Quit: '+$_.Exception.Message)}}
  Release-SP2Com $sp2Excel 'Excel.Application';$sp2Excel=$null
  [GC]::Collect();[GC]::WaitForPendingFinalizers()
  if($sp2OwnedProcess){
    try{if(-not $sp2OwnedProcess.WaitForExit(10000)){throw 'Owned Excel did not exit within 10 seconds.'};$sp2ExitCode=$sp2OwnedProcess.ExitCode;$sp2CleanExit=$sp2ExitCode -eq 0;if(-not $sp2CleanExit){throw ('Owned Excel exit code was '+$sp2ExitCode)}}catch{$sp2CleanupErrors.Add($_.Exception.Message)}
    $sp2OwnedProcess.Dispose()
  }
}
if($sp2MeasurementHash -cne (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant() -or $sp2InputsHash -cne (Get-FileHash -LiteralPath 'build/generation/inputs.json' -Algorithm SHA256).Hash.ToLowerInvariant()){$sp2CleanupErrors.Add('Measurement source or frozen input changed during native export.')}
$sp2Record=[ordered]@{schema='print-review/2.0';projectId='sample-project2';profileId='CSharp_ASPNET';runId=$RunId;recordedAtUtc=[DateTimeOffset]::UtcNow.ToString('o');status=$(if($sp2Failure -or $sp2CleanupErrors.Count -or -not $sp2CleanExit){'FAIL'}else{'EXPORTED_FOR_INDEPENDENT_VISUAL_REVIEW'});frozenInputManifestSha256=$sp2InputsHash;reportSourceSha256=$sp2Generation.reportSourceSha256;reportAssemblySha256=$sp2Generation.reportAssemblySha256;measurementSources=@(@{file='tests/Report/Test-ExcelPdf.ps1';sha256=$sp2MeasurementHash});excel=@{version=$sp2Version;newlyOwnedPid=$sp2OwnedId;preExistingPids=$sp2Before;cleanExit=$sp2CleanExit;exitCode=$sp2ExitCode;waitLimitMs=10000;cleanupErrors=$sp2CleanupErrors.ToArray()};records=$sp2Records.ToArray();failure=$sp2Failure;notExecuted=@('physical paper printing','formal user acceptance and scoring');formalScore=$null}
$sp2Record|ConvertTo-Json -Depth 15|Set-Content -LiteralPath (Join-Path $sp2Stage 'record.json') -Encoding UTF8
if($sp2Record.status -eq 'FAIL'){$sp2Record|ConvertTo-Json -Depth 15|Set-Content -LiteralPath (Join-Path $sp2Final 'record.json') -Encoding UTF8;$sp2Record|ConvertTo-Json -Depth 4;exit 1}
if(-not $sp2Final.StartsWith((Join-Path $sp2Root 'build/test-results')+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Final print path escaped method results.'}
if(Test-Path -LiteralPath $sp2Final){Remove-Item -LiteralPath $sp2Final -Recurse -Force}
New-Item -ItemType Directory -Path $sp2Final -Force|Out-Null
Get-ChildItem -LiteralPath $sp2Stage -File|ForEach-Object{Copy-Item -LiteralPath $_.FullName -Destination $sp2Final -Force}
Write-Output 'Native Excel export and owned-process clean-exit verification complete. Visual review remains required.'
