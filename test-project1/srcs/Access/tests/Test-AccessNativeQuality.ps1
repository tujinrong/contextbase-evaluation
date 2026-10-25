[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Database,
    [ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId='manual',
    [string]$ReportDirectory=''
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../tools/GeneratedPaths.ps1')
$taskRoot=$script:AccessMethodRoot
$taskSource=[IO.Path]::GetFullPath($Database)
if($taskSource -eq [IO.Path]::GetFullPath((Join-Path $taskRoot 'build/StudentManagement.accdb'))) {
    $taskSource=Resolve-AccessGeneratedPath $taskSource 'build'
} else {$taskSource=Resolve-AccessGeneratedPath $taskSource '.tmp'}
if(-not $ReportDirectory){$ReportDirectory=Join-Path $taskRoot 'build/test-results'}
$taskReport=Resolve-AccessReportPath $ReportDirectory
$taskWork=Resolve-AccessGeneratedPath (Join-Path $taskRoot '.tmp/native-quality') '.tmp'
New-Item -ItemType Directory -Path $taskWork,$taskReport -Force|Out-Null
$taskFixture=Resolve-AccessGeneratedPath (Join-Path $taskWork 'fixture.accdb') '.tmp'
$taskRecord=Join-Path $taskReport 'native-quality.json'
$taskImage=Join-Path $taskReport 'native-quality.png'
$taskBefore=(Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash
$taskStarted=[DateTime]::UtcNow.ToString('o')
$taskSourceFiles=@('Build-Access.ps1','tests/modNativeQualityTests.bas','tests/Test-AccessNativeQuality.ps1')
foreach($taskSourceFolder in @('Modules','Classes','database')) {
    $taskSourceFiles+=@(Get-ChildItem -LiteralPath (Join-Path $taskRoot $taskSourceFolder) -Recurse -File | ForEach-Object {$_.FullName.Substring($taskRoot.Length+1).Replace('\','/')})
}
$taskSourceFiles=@($taskSourceFiles|Sort-Object -Unique)
$taskHashes=@($taskSourceFiles|ForEach-Object {[ordered]@{file=$_;sha256=(Get-FileHash -LiteralPath (Join-Path $taskRoot $_) -Algorithm SHA256).Hash}})
[ordered]@{status='Running';runId=$RunId;startedAt=$taskStarted;sourceSha256=$taskBefore;formalScore=$null}|ConvertTo-Json|Set-Content -LiteralPath $taskRecord -Encoding UTF8
if(Test-Path -LiteralPath $taskImage){Remove-Item -LiteralPath $taskImage -Force}
Copy-Item -LiteralPath $taskSource -Destination $taskFixture -Force
# Disable startup only in the disposable copy before Access opens it. The first
# regression must initialize the edit form without a search form preparing maps.
$taskDaoEngine=$null;$taskBootstrapDb=$null
try {
    $taskDaoEngine=New-Object -ComObject DAO.DBEngine.120
    $taskBootstrapDb=$taskDaoEngine.OpenDatabase($taskFixture)
    $taskStartupProperty=$null
    try{$taskStartupProperty=$taskBootstrapDb.Properties.Item('StartupForm')}catch{}
    if($null -ne $taskStartupProperty){$taskBootstrapDb.Properties.Delete('StartupForm')}
    $taskStartupProperty=$null
    $taskBootstrapDb.Close()
} finally {
    $taskBootstrapDb=$null
    if($null -ne $taskDaoEngine){[Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskDaoEngine)|Out-Null;$taskDaoEngine=$null}
    [GC]::Collect();[GC]::WaitForPendingFinalizers()
}
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
public static class AccessNativeQualityWindow {
    [StructLayout(LayoutKind.Sequential)] public struct Rect { public int Left,Top,Right,Bottom; }
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd,out uint process);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hwnd,IntPtr after,int x,int y,int width,int height,uint flags);
    [DllImport("user32.dll")] public static extern uint GetDpiForWindow(IntPtr hwnd);
    [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr hwnd,out Rect rect);
    [DllImport("user32.dll")] static extern bool PrintWindow(IntPtr hwnd,IntPtr dc,uint flags);
    public static void Capture(IntPtr hwnd,string path) {
        Rect r;if(!GetWindowRect(hwnd,out r))throw new InvalidOperationException("Window rectangle missing");
        using(var b=new Bitmap(r.Right-r.Left,r.Bottom-r.Top))using(var g=Graphics.FromImage(b)) {
            IntPtr dc=g.GetHdc();bool ok;try{ok=PrintWindow(hwnd,dc,2);}finally{g.ReleaseHdc(dc);}
            if(!ok)throw new InvalidOperationException("Native PrintWindow failed");
            b.Save(path,ImageFormat.Png);
        }
    }
}
'@
$taskApp=$null;$taskChecks=New-Object 'Collections.Generic.List[object]';$taskFatal=$null;$taskOwnedPid=0;$taskScreenshot=$false
$taskVbe=$null;$taskProject=$null;$taskComponents=$null;$taskComponent=$null;$taskCodeModule=$null;$taskBars=$null;$taskCompiler=$null;$taskDoCmd=$null
$taskDisplayDb=$null;$taskDisplayRows=$null;$taskDisplayFields=$null;$taskDisplayField=$null
$taskProcess=$null;$taskOwnsProcess=$false;$taskExitObserved=$false;$taskExitCode=$null
$taskCleanupErrors=New-Object 'Collections.Generic.List[string]'
$taskExistingPids=@(Get-Process MSACCESS -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
function Release-NativeCom([ref]$Reference,[string]$Name) {
    try{if($null -ne $Reference.Value -and [Runtime.InteropServices.Marshal]::IsComObject($Reference.Value)){[Runtime.InteropServices.Marshal]::FinalReleaseComObject($Reference.Value)|Out-Null}}
    catch{$taskCleanupErrors.Add($Name+': '+$_.Exception.Message)}
    finally{$Reference.Value=$null}
}
function Release-NativeVbe {
    Release-NativeCom ([ref]$script:taskCompiler) 'Compiler'
    Release-NativeCom ([ref]$script:taskBars) 'CommandBars'
    Release-NativeCom ([ref]$script:taskCodeModule) 'CodeModule'
    Release-NativeCom ([ref]$script:taskComponent) 'Component'
    Release-NativeCom ([ref]$script:taskComponents) 'VBComponents'
    Release-NativeCom ([ref]$script:taskProject) 'VBProject'
    Release-NativeCom ([ref]$script:taskVbe) 'VBE'
}
try {
    $taskApp=New-Object -ComObject Access.Application
    $taskHwnd=[IntPtr]([long]$taskApp.hWndAccessApp())
    [uint32]$taskPidValue=0
    [void][AccessNativeQualityWindow]::GetWindowThreadProcessId($taskHwnd,[ref]$taskPidValue)
    $taskOwnedPid=[int]$taskPidValue
    if($taskOwnedPid -eq 0 -or $taskOwnedPid -in $taskExistingPids){throw 'Refusing an existing or unidentified Access process.'}
    $taskProcess=Get-Process -Id $taskOwnedPid
    [void]$taskProcess.Handle
    if($taskProcess.StartTime.ToUniversalTime() -lt [DateTime]::Parse($taskStarted).ToUniversalTime().AddSeconds(-2)){throw 'Access process predates this test.'}
    $taskOwnsProcess=$true
    $taskDpi=[int][AccessNativeQualityWindow]::GetDpiForWindow($taskHwnd)
    [ordered]@{pid=$taskOwnedPid;createdAt=[DateTime]::UtcNow.ToString('o');database=$taskFixture}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $taskWork 'owned-process.json') -Encoding UTF8
    # Position only this newly created test instance away from the user's desktop.
    [void][AccessNativeQualityWindow]::SetWindowPos($taskHwnd,[IntPtr]::Zero,-16000,0,1450,1000,0x14)
    $taskApp.Visible=$true
    $taskApp.OpenCurrentDatabase($taskFixture)
    $taskVbe=$taskApp.VBE;$taskProject=$taskVbe.ActiveVBProject;$taskComponents=$taskProject.VBComponents
    $taskComponent=$taskComponents.Add(1)
    $taskComponent.Name='modNativeQualityTests'
    $taskCodeModule=$taskComponent.CodeModule
    if($taskCodeModule.CountOfLines -gt 0){$taskCodeModule.DeleteLines(1,$taskCodeModule.CountOfLines)}
    $taskCode=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'modNativeQualityTests.bas') -Raw -Encoding UTF8
    $taskCodeModule.AddFromString(($taskCode -replace '(?m)^Attribute VB_Name[^\r\n]*\r?\n',''))
    $taskDoCmd=$taskApp.DoCmd;$taskDoCmd.Save(5,'modNativeQualityTests')
    $taskBars=$taskVbe.CommandBars;$taskCompiler=$taskBars.FindControl(1,578)
    if($taskCompiler.Enabled){try{$taskCompiler.Execute()}catch{if($taskCompiler.Enabled){throw}}}
    if($taskCompiler.Enabled){throw 'Test fixture VBE compilation failed.'}
    $taskOutput=[string]$taskApp.Run('NativeQualityTests')
    $taskOutput|Set-Content -LiteralPath (Join-Path $taskWork 'native-quality.raw.log') -Encoding UTF8
    foreach($taskLine in ($taskOutput -split '\r?\n')) {
        if(-not $taskLine){continue}
        $taskParts=$taskLine -split '\|',3
        if($taskParts.Count -ne 3 -or $taskParts[0] -notin @('PASS','FAIL')){throw ('Unrecognized native result: '+$taskLine)}
        $taskChecks.Add([ordered]@{name=$taskParts[1];passed=$taskParts[0] -eq 'PASS';detail=$taskParts[2]})
        Write-Output $taskLine
    }
    if($taskChecks.Count -lt 40){throw 'Native quality suite did not reach its expected scope.'}
    # Render a fresh untouched product copy; test writes and test-only modules do not
    # appear in the delivered screenshot or inflate the initial sample occupancy.
    Release-NativeVbe
    [GC]::Collect();[GC]::WaitForPendingFinalizers()
    $taskApp.CloseCurrentDatabase()
    $taskDisplay=Resolve-AccessGeneratedPath (Join-Path $taskWork 'display.accdb') '.tmp'
    Copy-Item -LiteralPath $taskSource -Destination $taskDisplay -Force
    $taskApp.OpenCurrentDatabase($taskDisplay)
    $taskDisplayDb=$taskApp.CurrentDb()
    $taskDisplayRows=$taskDisplayDb.OpenRecordset('SELECT TOP 1 student_id FROM m_student WHERE is_deleted=False ORDER BY student_id',4)
    if($taskDisplayRows.EOF){throw 'Fresh product screenshot requires its initial sample students.'}
    $taskDisplayFields=$taskDisplayRows.Fields;$taskDisplayField=$taskDisplayFields.Item('student_id')
    $taskDisplayId=[int]$taskDisplayField.Value
    Release-NativeCom ([ref]$taskDisplayField) 'DisplayField'
    Release-NativeCom ([ref]$taskDisplayFields) 'DisplayFields'
    $taskDisplayRows.Close();Release-NativeCom ([ref]$taskDisplayRows) 'DisplayRows'
    $taskDisplayDb.Close();Release-NativeCom ([ref]$taskDisplayDb) 'DisplayDb'
    $taskDoCmd.OpenForm('frmStudentEdit',0,[Type]::Missing,[Type]::Missing,[Type]::Missing,0,([string]$taskDisplayId+'|'))
    [void][AccessNativeQualityWindow]::SetWindowPos($taskHwnd,[IntPtr]::Zero,-16000,0,1450,1000,0x14)
    [AccessNativeQualityWindow]::Capture($taskHwnd,$taskImage)
    $taskScreenshot=$true
    $taskDoCmd.Close(2,'frmStudentEdit',2)
} catch {$taskFatal=$_.Exception.ToString()+[Environment]::NewLine+$_.ScriptStackTrace;Write-Output $taskFatal}
finally {
    Release-NativeCom ([ref]$taskDisplayField) 'DisplayField'
    Release-NativeCom ([ref]$taskDisplayFields) 'DisplayFields'
    if($null -ne $taskDisplayRows){try{$taskDisplayRows.Close()}catch{$taskCleanupErrors.Add($_.Exception.Message)}}
    Release-NativeCom ([ref]$taskDisplayRows) 'DisplayRows'
    if($null -ne $taskDisplayDb){try{$taskDisplayDb.Close()}catch{$taskCleanupErrors.Add($_.Exception.Message)}}
    Release-NativeCom ([ref]$taskDisplayDb) 'DisplayDb'
    Release-NativeVbe
    Release-NativeCom ([ref]$taskDoCmd) 'DoCmd'
    [GC]::Collect();[GC]::WaitForPendingFinalizers()
    if($null -ne $taskApp -and $taskOwnsProcess) {
        try{$taskOfficeVersion=$taskApp.Version}catch{$taskCleanupErrors.Add($_.Exception.Message)}
        try{$taskApp.CloseCurrentDatabase()}catch{$taskCleanupErrors.Add($_.Exception.Message)}
        try{$taskApp.Quit(2)}catch{$taskCleanupErrors.Add($_.Exception.Message)}
    }
    Release-NativeCom ([ref]$taskApp) 'Access.Application'
    [GC]::Collect();[GC]::WaitForPendingFinalizers()
    if($null -ne $taskProcess){
        try{
            if($taskOwnsProcess){$taskExitObserved=$taskProcess.WaitForExit(10000);if($taskExitObserved){$taskExitCode=$taskProcess.ExitCode}}
        }catch{$taskCleanupErrors.Add('Process exit: '+$_.Exception.Message)}
        finally{$taskProcess.Dispose();$taskProcess=$null}
    }
    $taskCleanExit=$taskOwnsProcess -and $taskExitObserved -and $taskExitCode -eq 0 -and $taskCleanupErrors.Count -eq 0
    $taskAfter=(Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash
    $taskChanged=@($taskHashes|Where-Object {(Get-FileHash -LiteralPath (Join-Path $taskRoot $_.file) -Algorithm SHA256).Hash -ne $_.sha256})
    $taskChecks.Add([ordered]@{name='Canonical source ACCDB remains unchanged';passed=$taskBefore -eq $taskAfter;detail=$taskAfter})
    $taskChecks.Add([ordered]@{name='Tested source files remain unchanged during suite';passed=$taskChanged.Count -eq 0;detail=($taskChanged.file -join ';')})
    $taskFailed=@($taskChecks|Where-Object {-not $_.passed}).Count
    $taskStatus=if(-not $taskFatal -and $taskFailed -eq 0 -and $taskScreenshot -and $taskCleanExit){'Passed'}else{'Failed'}
    [ordered]@{status=$taskStatus;runId=$RunId;startedAt=$taskStarted;completedAt=[DateTime]::UtcNow.ToString('o');sourceFile=$taskSource;sourceSha256=$taskBefore;sourceSha256After=$taskAfter;sourceFiles=$taskHashes;fixtureOnly=$true;startupFormClearedInFixture=$true;officeVersion=$taskOfficeVersion;ownedProcess=$taskOwnedPid;cleanExit=$taskCleanExit;exitObserved=$taskExitObserved;processExitCode=$taskExitCode;cleanupErrors=@($taskCleanupErrors);windowDpi=$taskDpi;passed=@($taskChecks|Where-Object {$_.passed}).Count;failed=$taskFailed;checks=$taskChecks;screenshot=$(if($taskScreenshot){'native-quality.png'}else{$null});inputMethod='WM_CHAR messages sent to the focused native Access edit window; focus and commit through Access controls';formalScore=$null;notExecuted=@('physical keyboard and Japanese IME composition','Office 32-bit','production or shared database');fatal=$taskFatal}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $taskRecord -Encoding UTF8
}
if($taskStatus -ne 'Passed'){exit 1}
