[CmdletBinding()]
param([string]$TargetRoot = 'test-project1/srcs/Access-To-CSharp_ASPNET')
$ErrorActionPreference = 'Stop'
$target = [IO.Path]::GetFullPath($TargetRoot)
$fixtureDir = Join-Path $target '.tmp/extractor-safety'
New-Item -ItemType Directory -Path $fixtureDir -Force | Out-Null
$fixture = Join-Path $fixtureDir 'startup-fixture.accdb'
if (Test-Path -LiteralPath $fixture) { Remove-Item -LiteralPath $fixture -Force }
$app = $null
try {
    $app = New-Object -ComObject Access.Application
    $app.Visible = $false
    $app.AutomationSecurity = 3
    $app.NewCurrentDatabase($fixture)
    $db = $app.CurrentDb()
    $db.Execute('CREATE TABLE startup_sentinel (id LONG)',128)
    $form = $app.CreateForm()
    $formName = $form.Name
    $form.HasModule = $true
    $form.OnLoad = '[Event Procedure]'
    $form.Module.InsertLines(1,"Private Sub Form_Load()`r`n    CurrentDb.Execute `"INSERT INTO startup_sentinel (id) VALUES (1)`"`r`nEnd Sub")
    $app.DoCmd.Save(2,$formName)
    $app.DoCmd.Close(2,$formName,1)
    $app.DoCmd.Rename('frmStartupProbe',2,$formName)
    $db.Properties.Append($db.CreateProperty('StartupForm',10,'frmStartupProbe'))
    $macroFile = Join-Path $fixtureDir 'AutoExec.txt'
    $macroText = @'
Version =196611
ColumnsShown =0
Begin
    Action ="RunSQL"
    Argument ="INSERT INTO startup_sentinel (id) VALUES (2)"
    Argument ="-1"
End
'@
    [IO.File]::WriteAllText($macroFile,$macroText,[Text.UnicodeEncoding]::new($false,$true))
    $app.LoadFromText(4,'AutoExec',$macroFile)
    $unicodeModuleName = 'modUnicodeProbe'
    $unicodeModuleFile = Join-Path $fixtureDir 'modUnicodeProbe.txt'
    [IO.File]::WriteAllText($unicodeModuleFile,"Option Explicit`r`nPublic Function JapaneseLiteral() As String`r`n    JapaneseLiteral = `"学籍番号`"`r`nEnd Function",[Text.Encoding]::GetEncoding((Get-WinSystemLocale).TextInfo.ANSICodePage))
    $app.LoadFromText(5,$unicodeModuleName,$unicodeModuleFile)
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($form); $form = $null
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($db); $db = $null
    $app.CloseCurrentDatabase()
    $app.Quit(2)
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($app); $app = $null
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
    & (Join-Path $PSScriptRoot '../scripts/Export-Access.ps1') -SourceFile $fixture -TargetRoot (Join-Path $fixtureDir 'result') -SafetyFixtureVerified | Out-Null
    $dao = New-Object -ComObject DAO.DBEngine.120
    $probe = $dao.OpenDatabase($fixture,$false,$true,'')
    $rows = $probe.OpenRecordset('SELECT Count(*) FROM startup_sentinel',4)
    $originalCount = [int]$rows.Fields.Item(0).Value
    $rows.Close(); $probe.Close()
    $importDb = $dao.OpenDatabase((Join-Path $fixtureDir 'result/.tmp/extraction/export-host.accdb'),$false,$true,'')
    $importedText = Get-Content -LiteralPath (Join-Path $fixtureDir 'result/build/generation/access-export/forms/frmStartupProbe.txt') -Raw
    $importDb.Close()
    if ($originalCount -ne 0) { throw 'Startup form unexpectedly executed.' }
    if ($importedText -notmatch 'INSERT INTO startup_sentinel') { throw 'Fixture form code was not extracted.' }
    $manifest = Get-Content -LiteralPath (Join-Path $fixtureDir 'result/build/generation/access-extraction.json') -Raw | ConvertFrom-Json
    if ($manifest.status -ne 'PASS') { throw 'Fixture export was incomplete.' }
    $macroExported = Test-Path -LiteralPath (Join-Path $fixtureDir 'result/build/generation/access-export/macros/AutoExec.txt')
    if (-not $macroExported) { throw 'AutoExec macro fixture was not extracted.' }
    $unicodeCode = Get-Content -LiteralPath (Join-Path $fixtureDir ('result/build/generation/access-export/modules/' + $unicodeModuleName + '.txt')) -Raw
    if ($unicodeCode -notmatch '学籍番号') { throw 'Unicode module literal changed during export.' }
    $obsoleteExport = Join-Path $fixtureDir 'result/build/generation/access-export/modules/obsolete-object.txt'
    Set-Content -LiteralPath $obsoleteExport -Value 'old export must be removed' -Encoding utf8
    & (Join-Path $PSScriptRoot '../scripts/Export-Access.ps1') -SourceFile $fixture -TargetRoot (Join-Path $fixtureDir 'result') -SafetyFixtureVerified | Out-Null
    if (Test-Path -LiteralPath $obsoleteExport) { throw 'Stale resource survived evidence replacement.' }
    $out = Join-Path $target 'build/test-results'
    New-Item -ItemType Directory -Path $out -Force | Out-Null
    [ordered]@{schema='access-extractor-safety/1.0';status='PASS';checks=@{startupFormNotRun=($originalCount -eq 0);autoExecNotRun=($originalCount -eq 0);autoExecDefinitionExtracted=$macroExported;unicodeModuleLiteralPreserved=$true;staleResourcesReplaced=$true;formEventCodeExtracted=$true;originalHashUnchanged=($manifest.sourceSha256 -eq $manifest.safety.originalSha256After);sourceNotOpenedInAccess=($manifest.safety.sourceOpenedInAccess -eq $false)};limitations=@('Sentinel tests cover startup form and AutoExec in a disposable fixture; do not prove arbitrary third-party ActiveX initialization safety.');formalScore=$null} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $out 'extractor-safety.json') -Encoding utf8
    Write-Output 'PASS: startup form and AutoExec stayed unexecuted; definitions extracted; original hash unchanged.'
} finally {
    if ($app) {try {$app.CloseCurrentDatabase()} catch {};try {$app.Quit(2)} catch {};[void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($app)}
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}
