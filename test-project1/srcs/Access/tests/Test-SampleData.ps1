param(
    [string]$Database='',
    [ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId='sample-data',
    [string]$ReportDirectory=''
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../tools/GeneratedPaths.ps1')
if(-not $Database){$Database=Join-Path $script:AccessMethodRoot '.tmp/tests/sample-data.accdb'}
if(-not $ReportDirectory){$ReportDirectory=Join-Path $script:AccessMethodRoot 'build/test-results'}
$taskDatabase=Resolve-AccessGeneratedPath $Database '.tmp'
$taskReport=Resolve-AccessReportPath $ReportDirectory
New-Item -ItemType Directory -Path $taskReport -Force | Out-Null
if(-not (Test-Path -LiteralPath $taskDatabase -PathType Leaf)){throw 'Build an empty -IncludeTests fixture at the specified Access/.tmp path first.'}
$taskBeforeHash=(Get-FileHash -LiteralPath $taskDatabase -Algorithm SHA256).Hash
$taskSourceBefore=@('Modules/modSampleData.bas','tests/modSampleDataTests.bas','tests/Test-SampleData.ps1','database/sample-data.json')|ForEach-Object{
    $taskPath=Join-Path $script:AccessMethodRoot $_
    [ordered]@{path=$_;sha256=(Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash}
}
$taskAccess=$null;$taskDb=$null;$taskState='Failed';$taskOutput='';$taskFatal='';$taskVersion='';$taskChecks='';$taskUnicodeChecks=@()
try{
    $taskAccess=New-Object -ComObject Access.Application;$taskAccess.Visible=$false
    $taskAccess.OpenCurrentDatabase($taskDatabase)
    $taskDb=$taskAccess.CurrentDb()
    if(-not [bool]$taskDb.Properties.Item('StudentTestFixture').Value){throw 'Refusing sample tests in a non-fixture database.'}
    $taskCode=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'modSampleDataTests.bas') -Encoding UTF8 -Raw
    try{$taskOld=$taskAccess.VBE.ActiveVBProject.VBComponents.Item('modSampleDataTests');$taskAccess.VBE.ActiveVBProject.VBComponents.Remove($taskOld)}catch{}
    $taskComponent=$taskAccess.VBE.ActiveVBProject.VBComponents.Add(1);$taskComponent.Name='modSampleDataTests'
    if($taskComponent.CodeModule.CountOfLines -gt 0){$taskComponent.CodeModule.DeleteLines(1,$taskComponent.CodeModule.CountOfLines)}
    $taskComponent.CodeModule.AddFromString(($taskCode -replace '(?m)^Attribute VB_Name.*\r?\n',''))
    $taskAccess.DoCmd.Save(5,'modSampleDataTests')
    $taskCompiler=$taskAccess.VBE.CommandBars.FindControl(1,578)
    if($null -eq $taskCompiler){throw 'Native VBE compiler unavailable.'}
    if($taskCompiler.Enabled){try{$taskCompiler.Execute()}catch{if($taskCompiler.Enabled){throw}}}
    if($taskCompiler.Enabled){
        $taskPane=$taskAccess.VBE.ActiveCodePane
        $taskLine=0;$taskColumn=0;$taskEndLine=0;$taskEndColumn=0
        $taskPane.GetSelection([ref]$taskLine,[ref]$taskColumn,[ref]$taskEndLine,[ref]$taskEndColumn)
        throw "Native VBE compilation failed in $($taskPane.CodeModule.Name):$taskLine`n$($taskPane.CodeModule.Lines([Math]::Max(1,$taskLine-2),5))"
    }
    $taskOutput=[string]$taskAccess.Run('RunSampleDataTests');Write-Output $taskOutput
    $taskChecks=[string]$taskAccess.Run('SampleDataTestLog');Write-Output $taskChecks
    if($taskOutput -match '^\d+ assertions passed$'){
        # Expectations are code points in PowerShell, independent of the VBE source code page.
        $taskExactCases=@(
            @{name='class DEMO-A exact Unicode';sql="SELECT class_name FROM m_class WHERE class_code='DEMO-A'";points=@(0x898B,0x672C,0x30FB,0x901A,0x5E38)},
            @{name='class DEMO-B exact Unicode';sql="SELECT class_name FROM m_class WHERE class_code='DEMO-B'";points=@(0x898B,0x672C,0x30FB,0x6E80,0x54E1)},
            @{name='class DEMO-H exact Unicode';sql="SELECT class_name FROM m_class WHERE class_code='DEMO-H'";points=@(0x898B,0x672C,0x30FB,0x524D,0x5E74,0x5EA6)},
            @{name='supplementary student name exact Unicode';sql="SELECT student_name FROM m_student WHERE student_no Like 'DEMO-*-010'";points=@(0x898B,0x672C,0x20BB7,0x5B50)}
        )
        foreach($taskCase in $taskExactCases){
            $taskRs=$taskDb.OpenRecordset($taskCase.sql)
            if($taskRs.EOF){throw "Missing Unicode probe row: $($taskCase.name)"}
            $taskActual=[string]$taskRs.Fields.Item(0).Value;$taskRs.Close();$taskRs=$null
            $taskExpected=-join @($taskCase.points|ForEach-Object{[char]::ConvertFromUtf32($_)})
            $taskEqual=[string]::Equals($taskActual,$taskExpected,[StringComparison]::Ordinal)
            $taskUnicodeChecks+=@{name=$taskCase.name;passed=$taskEqual;expectedCodePoints=$taskCase.points;actualUtf16Units=@([int[]][char[]]$taskActual);expectedUtf16Units=@([int[]][char[]]$taskExpected)}
            if(-not $taskEqual){throw "Unicode data differs from independent code-point expectation: $($taskCase.name)"}
        }
        $taskRs=$taskDb.OpenRecordset("SELECT remarks FROM m_student WHERE student_no Like 'DEMO-*-010'")
        $taskNote=[string]$taskRs.Fields.Item(0).Value;$taskRs.Close();$taskRs=$null
        $taskNoteExact=$taskNote.Contains([string][char]0x30FB) -and -not $taskNote.Contains('?')
        $taskUnicodeChecks+=@{name='sample note keeps U+30FB without replacement question mark';passed=$taskNoteExact;actualUtf16Units=@([int[]][char[]]$taskNote)}
        if(-not $taskNoteExact){throw 'Unicode sample note contains ANSI conversion loss.'}
        $taskState='Passed'
    }
}catch{$taskFatal=$_.Exception.Message;Write-Output $taskFatal}
finally{
    if($null -ne $taskRs){try{$taskRs.Close()}catch{};$taskRs=$null}
    if($null -ne $taskDb){$taskDb.Close();[Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskDb)|Out-Null;$taskDb=$null}
    $taskComponent=$null;$taskOld=$null;$taskCompiler=$null;$taskPane=$null
    if($null -ne $taskAccess){
        $taskVersion=$taskAccess.Version
        [GC]::Collect();[GC]::WaitForPendingFinalizers()
        try{$taskAccess.CloseCurrentDatabase()}catch{}
        $taskAccess.Quit(2);[Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskAccess)|Out-Null;$taskAccess=$null
        [GC]::Collect();[GC]::WaitForPendingFinalizers()
    }
    $taskSources=@('Modules/modSampleData.bas','tests/modSampleDataTests.bas','tests/Test-SampleData.ps1','database/sample-data.json')|ForEach-Object{
        $taskPath=Join-Path $script:AccessMethodRoot $_
        [ordered]@{path=$_;sha256=(Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash}
    }
    $taskSourcesUnchanged=(($taskSourceBefore|ConvertTo-Json -Compress)-ceq($taskSources|ConvertTo-Json -Compress))
    if(-not $taskSourcesUnchanged){$taskState='Failed';$taskFatal='Sample sources changed during verification.'}
    $taskInputs=@(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot '../../../spec/Access') -Recurse -File|Sort-Object FullName|ForEach-Object{[ordered]@{path=$_.FullName;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}})
    [ordered]@{runId=$RunId;completedAt=[DateTime]::UtcNow.ToString('o');status=$taskState;database=$taskDatabase;databaseBeforeSha256=$taskBeforeHash;databaseAfterSha256=(Get-FileHash -LiteralPath $taskDatabase -Algorithm SHA256).Hash;officeVersion=$taskVersion;fixtureOnly=$true;output=$taskOutput;checks=$taskChecks;independentUnicodeChecks=$taskUnicodeChecks;fatal=$taskFatal;sourcesBefore=$taskSourceBefore;sources=$taskSources;sourcesUnchanged=$taskSourcesUnchanged;inputs=$taskInputs;notTested=@('actual recipient mail or telephone contact','production data migration','Office 32-bit')}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $taskReport 'sample-data.json') -Encoding UTF8
}
if($taskState -ne 'Passed'){exit 1}
