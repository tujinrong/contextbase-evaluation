param([Parameter(Mandatory=$true)][string]$InputWorkbook,[Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$literalRoot=[System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $literalRoot -ErrorAction Stop | Out-Null
$literalInput=[System.IO.Path]::GetFullPath($InputWorkbook)
$literalBefore=(Get-FileHash -LiteralPath $literalInput -Algorithm SHA256).Hash.ToLowerInvariant()
$literalBaseline=@(Get-Process -Name EXCEL -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
$literalExcel=$null;$literalBook=$null;$literalSheet=$null;$literalCell=$null;$literalOwnedId=$null
$literalResult=[ordered]@{scope='READ_ONLY_EXCEL_LITERAL_QA';workbook=$literalInput;beforeSha256=$literalBefore;baselineExcelProcessIds=$literalBaseline;macrosDisabled=$false;updateLinks=0;readOnly=$true;visible=$false;saved=$false;originalApplicationExecuted=$false;status='NOT_COMPLETED'}
function Write-LiteralStage([string]$stage){
    [ordered]@{utc=[DateTime]::UtcNow.ToString('o');stage=$stage;helperPid=$PID;excelPid=$literalOwnedId} | ConvertTo-Json -Compress | Add-Content -LiteralPath (Join-Path $literalRoot 'stages.jsonl') -Encoding utf8
}
try {
    Write-LiteralStage 'baseline-checked'
    if($literalBaseline.Count -ne 0){throw 'Existing Excel process detected; read-only QA refuses to attach or create another instance.'}
    Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class LiteralExcelWindow { [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd,out uint processId); }'
    $literalExcel=New-Object -ComObject Excel.Application
    [uint32]$literalWindowId=0
    [void][LiteralExcelWindow]::GetWindowThreadProcessId([IntPtr]$literalExcel.Hwnd,[ref]$literalWindowId)
    if($literalWindowId -eq 0 -or $literalBaseline -contains [int]$literalWindowId){throw 'Cannot prove newly owned Excel process.'}
    $literalOwnedId=[int]$literalWindowId
    $literalProcess=Get-Process -Id $literalOwnedId
    if($literalProcess.ProcessName -ne 'EXCEL'){throw 'Owned COM window is not Excel.'}
    [ordered]@{excelPid=$literalOwnedId;helperPid=$PID;excelStartTimeUtc=$literalProcess.StartTime.ToUniversalTime().ToString('o');baselineExcelProcessIds=$literalBaseline;ownership='NEW_COM_APPLICATION_HWND'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $literalRoot 'owned-excel.json') -Encoding utf8
    Write-LiteralStage 'owned-excel-created'
    $literalExcel.Visible=$false
    $literalExcel.DisplayAlerts=$false
    $literalExcel.AskToUpdateLinks=$false
    $literalExcel.EnableEvents=$false
    $literalExcel.AutomationSecurity=3
    $literalResult.macrosDisabled=$true
    Write-LiteralStage 'macro-link-events-disabled'
    $literalBook=$literalExcel.Workbooks.Open($literalInput,0,$true)
    if(-not $literalBook.ReadOnly){throw 'Excel did not open workbook read-only.'}
    Write-LiteralStage 'read-only-workbook-opened'
    $literalSheet=$literalBook.Worksheets.Item('表紙')
    $literalCell=$literalSheet.Range('X18')
    $literalValue=$literalCell.Value2
    $literalResult.cell='表紙!X18'
    $literalResult.value2=$literalValue
    $literalResult.value2Type=if($null -eq $literalValue){'null'}else{$literalValue.GetType().FullName}
    $literalResult.text=[string]$literalCell.Text
    $literalResult.numberFormat=[string]$literalCell.NumberFormat
    $literalResult.excelVersion=[string]$literalExcel.Version
    $literalResult.excelBuild=[string]$literalExcel.Build
    $literalResult.status=if($literalValue -is [string] -and $literalValue -ceq '1.0' -and $literalResult.text -ceq '1.0'){'PASS_LITERAL_VALUE_AND_DISPLAY'}else{'DISPLAY_OR_VALUE_MISMATCH'}
    Write-LiteralStage 'literal-values-read'
} catch {
    $literalResult.status='FAILED_OR_NOT_TESTED'
    $literalResult.error=$_.Exception.Message
} finally {
    if($null -ne $literalBook){try{$literalBook.Close($false);Write-LiteralStage 'workbook-closed-without-save'}catch{$literalResult.closeError=$_.Exception.Message}}
    if($null -ne $literalExcel -and $null -ne $literalOwnedId){try{$literalExcel.Quit();Write-LiteralStage 'owned-excel-quit'}catch{$literalResult.quitError=$_.Exception.Message}}
    foreach($literalObject in @($literalCell,$literalSheet,$literalBook,$literalExcel)){
        if($null -ne $literalObject){try{[void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($literalObject)}catch{}}
    }
    [GC]::Collect();[GC]::WaitForPendingFinalizers()
    $literalResult.ownedExcelProcessId=$literalOwnedId
    $literalResult.afterSha256=(Get-FileHash -LiteralPath $literalInput -Algorithm SHA256).Hash.ToLowerInvariant()
    $literalResult.workbookBytesUnchanged=$literalResult.beforeSha256 -ceq $literalResult.afterSha256
    if(-not $literalResult.workbookBytesUnchanged){$literalResult.status='FAILED_WORKBOOK_BYTES_CHANGED'}
    $literalResult | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $literalRoot 'result.json') -Encoding utf8
    $literalResult | ConvertTo-Json -Depth 6 -Compress | Write-Output
}
