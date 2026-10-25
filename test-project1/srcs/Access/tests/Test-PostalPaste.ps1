[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Database,
    [ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId='postal-paste',
    [string]$ReportDirectory='',
    [switch]$RestoreClipboardOnly
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../tools/GeneratedPaths.ps1')
$taskRoot=$script:AccessMethodRoot
$taskSource=[IO.Path]::GetFullPath($Database)
if($taskSource -eq [IO.Path]::GetFullPath((Join-Path $taskRoot 'build/StudentManagement.accdb'))){$taskSource=Resolve-AccessGeneratedPath $taskSource 'build'}else{$taskSource=Resolve-AccessGeneratedPath $taskSource '.tmp'}
if(-not $ReportDirectory){$ReportDirectory=Join-Path $taskRoot 'build/test-results'}
$taskReport=Resolve-AccessReportPath $ReportDirectory
$taskFinalReports=[IO.Path]::GetFullPath((Join-Path $taskRoot 'build/test-results'))
if($taskReport -ne $taskFinalReports -and -not $taskReport.StartsWith($taskFinalReports+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Postal report must stay under Access/build/test-results.'}
$taskWork=Resolve-AccessGeneratedPath (Join-Path $taskRoot '.tmp/postal-paste') '.tmp'
New-Item -ItemType Directory -Path $taskWork,$taskReport -Force|Out-Null
$taskFixture=Resolve-AccessGeneratedPath (Join-Path $taskWork 'fixture.accdb') '.tmp'
if($taskSource -eq $taskFixture){throw 'The source cannot be the owned postal fixture.'}
$taskRecord=Resolve-AccessGeneratedPath (Join-Path $taskReport 'postal-paste.json') 'build'
$taskClipboardBackup=Resolve-AccessGeneratedPath (Join-Path $taskWork 'clipboard-backup.bin') '.tmp'
$taskStarted=[DateTime]::UtcNow.ToString('o')
function Get-PostalSourceInventory(){
    $taskPaths=@('Build-Access.ps1','tools/GeneratedPaths.ps1','tests/Test-PostalPaste.ps1','tests/modPostalPasteTests.bas')
    $taskPaths+=@(Get-ChildItem -LiteralPath (Join-Path $taskRoot 'Modules'),(Join-Path $taskRoot 'Classes'),(Join-Path $taskRoot 'database') -Recurse -File|Where-Object{$_.Extension -in @('.bas','.cls','.json','.sql')}|ForEach-Object{
        if(($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'Reparse-point product input refused.'}
        $_.FullName.Substring($taskRoot.Length+1).Replace('\','/')
    })
    return @($taskPaths|Sort-Object -Unique|ForEach-Object{[ordered]@{file=$_;sha256=(Get-FileHash -LiteralPath (Join-Path $taskRoot $_) -Algorithm SHA256).Hash}})
}
function Write-PostalRecord($Value){
    $taskStage=Resolve-AccessGeneratedPath (Join-Path $taskWork ([Guid]::NewGuid().ToString('N')+'.json')) '.tmp'
    try{$Value|ConvertTo-Json -Depth 10|Set-Content -LiteralPath $taskStage -Encoding UTF8;Move-Item -LiteralPath $taskStage -Destination $taskRecord -Force}finally{if(Test-Path -LiteralPath $taskStage){Remove-Item -LiteralPath $taskStage -Force}}
}
function Get-PostalClipboardDigest($Value){
    if($Value -is [IO.MemoryStream]){$taskBytes=$Value.ToArray()}
    elseif($Value -is [byte[]]){$taskBytes=$Value}
    elseif($Value -is [Drawing.Image]){
        $taskStream=[IO.MemoryStream]::new()
        try{$Value.Save($taskStream,[Drawing.Imaging.ImageFormat]::Bmp);$taskBytes=$taskStream.ToArray()}finally{$taskStream.Dispose()}
    }
    elseif($Value -is [string[]]){$taskBytes=[Text.Encoding]::Unicode.GetBytes(($Value|ConvertTo-Json -Compress))}
    elseif($Value -is [string] -or $Value -is [ValueType]){$taskBytes=[Text.Encoding]::Unicode.GetBytes([string]$Value)}
    else{throw 'Clipboard payload cannot be verified without retaining a live external object.'}
    $taskHasher=[Security.Cryptography.SHA256]::Create()
    try{return [Convert]::ToBase64String($taskHasher.ComputeHash([byte[]]$taskBytes))}finally{$taskHasher.Dispose()}
}
function Invoke-PostalVba([string]$Name,[object[]]$Values=@()){
    # Access.Application.Run exposes optional ByRef VARIANT arguments even for a VBA ByVal parameter.
    if($Values.Count -eq 0){return $taskApp.Run($Name)}
    $taskArg0=[object]$Values[0]
    if($Values.Count -eq 1){return $taskApp.Run($Name,[ref]$taskArg0)}
    $taskArg1=[object]$Values[1]
    if($Values.Count -eq 2){return $taskApp.Run($Name,[ref]$taskArg0,[ref]$taskArg1)}
    if($Values.Count -ne 4){throw 'Unsupported postal fixture argument count.'}
    $taskArg2=[object]$Values[2];$taskArg3=[object]$Values[3]
    return $taskApp.Run($Name,[ref]$taskArg0,[ref]$taskArg1,[ref]$taskArg2,[ref]$taskArg3)
}
function Release-PostalCom([ref]$Reference,[string]$Name){
    try{
        if($null -ne $Reference.Value -and [Runtime.InteropServices.Marshal]::IsComObject($Reference.Value)){
            [Runtime.InteropServices.Marshal]::FinalReleaseComObject($Reference.Value)|Out-Null
        }
    }catch{$script:taskCleanupErrors.Add($Name+': '+$_.Exception.Message)}
    finally{$Reference.Value=$null}
}
function Save-PostalClipboardBackup($Snapshot,[string[]]$Formats,[bool]$Empty){
    if(Test-Path -LiteralPath $taskClipboardBackup){throw 'An earlier clipboard backup still exists. Restore it before running another test.'}
    $taskPayloads=@($Formats|ForEach-Object{
        $taskFormatName=$_;$taskValue=$Snapshot.GetData($taskFormatName,$false);$taskKind='';$taskType=''
        if($taskValue -is [string]){$taskKind='text';$taskData=[Text.Encoding]::Unicode.GetBytes($taskValue)}
        elseif($taskValue -is [IO.MemoryStream]){$taskKind='stream';$taskData=$taskValue.ToArray()}
        elseif($taskValue -is [byte[]]){$taskKind='bytes';$taskData=$taskValue}
        elseif($taskValue -is [string[]]){$taskKind='strings';$taskData=[Text.Encoding]::UTF8.GetBytes(($taskValue|ConvertTo-Json -Compress))}
        elseif($taskValue -is [Drawing.Image]){
            $taskKind='image';$taskBuffer=[IO.MemoryStream]::new()
            try{$taskValue.Save($taskBuffer,[Drawing.Imaging.ImageFormat]::Bmp);$taskData=$taskBuffer.ToArray()}finally{$taskBuffer.Dispose()}
        }
        elseif($taskValue.GetType().FullName -in @('System.Int16','System.Int32','System.Int64','System.UInt16','System.UInt32','System.UInt64','System.Boolean','System.Byte','System.SByte','System.Single','System.Double','System.Decimal')){
            $taskKind='scalar';$taskType=$taskValue.GetType().FullName;$taskData=[Text.Encoding]::UTF8.GetBytes([Convert]::ToString($taskValue,[Globalization.CultureInfo]::InvariantCulture))
        }else{throw "Clipboard format cannot be durably preserved before mutation: $taskFormatName"}
        [ordered]@{format=$taskFormatName;kind=$taskKind;type=$taskType;bytes=[Convert]::ToBase64String([byte[]]$taskData);digest=(Get-PostalClipboardDigest $taskValue)}
    })
    $taskPlain=[Text.Encoding]::UTF8.GetBytes(([ordered]@{version=1;empty=$Empty;payloads=$taskPayloads}|ConvertTo-Json -Depth 6 -Compress))
    $taskEntropy=[Text.Encoding]::UTF8.GetBytes('AccessPostalClipboardV1')
    $taskEncrypted=[Security.Cryptography.ProtectedData]::Protect($taskPlain,$taskEntropy,[Security.Cryptography.DataProtectionScope]::CurrentUser)
    $taskBackupStage=Resolve-AccessGeneratedPath (Join-Path $taskWork ([Guid]::NewGuid().ToString('N')+'.protected')) '.tmp'
    try{[IO.File]::WriteAllBytes($taskBackupStage,$taskEncrypted);Move-Item -LiteralPath $taskBackupStage -Destination $taskClipboardBackup}finally{if(Test-Path -LiteralPath $taskBackupStage){Remove-Item -LiteralPath $taskBackupStage -Force};[Array]::Clear($taskPlain,0,$taskPlain.Length)}
}
function Read-PostalClipboardBackup(){
    $taskEntropy=[Text.Encoding]::UTF8.GetBytes('AccessPostalClipboardV1')
    $taskPlain=[Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($taskClipboardBackup),$taskEntropy,[Security.Cryptography.DataProtectionScope]::CurrentUser)
    try{$taskSaved=[Text.Encoding]::UTF8.GetString($taskPlain)|ConvertFrom-Json}finally{[Array]::Clear($taskPlain,0,$taskPlain.Length)}
    if($taskSaved.version -ne 1){throw 'Unsupported protected clipboard backup version.'}
    $taskObject=New-Object Windows.Forms.DataObject
    foreach($taskPayload in $taskSaved.payloads){
        $taskData=[Convert]::FromBase64String($taskPayload.bytes)
        switch($taskPayload.kind){
            'text'{$taskValue=[Text.Encoding]::Unicode.GetString($taskData)}
            'stream'{$taskValue=[IO.MemoryStream]::new($taskData)}
            'bytes'{$taskValue=$taskData}
            'strings'{$taskValue=[string[]]([Text.Encoding]::UTF8.GetString($taskData)|ConvertFrom-Json)}
            'image'{$taskBuffer=[IO.MemoryStream]::new($taskData);try{$taskTemporaryImage=[Drawing.Image]::FromStream($taskBuffer);try{$taskValue=$taskTemporaryImage.Clone()}finally{$taskTemporaryImage.Dispose()}}finally{$taskBuffer.Dispose()}}
            'scalar'{
                if($taskPayload.type -notin @('System.Int16','System.Int32','System.Int64','System.UInt16','System.UInt32','System.UInt64','System.Boolean','System.Byte','System.SByte','System.Single','System.Double','System.Decimal')){throw 'Unsupported clipboard scalar type.'}
                $taskValue=[Convert]::ChangeType([Text.Encoding]::UTF8.GetString($taskData),[Type]::GetType($taskPayload.type),[Globalization.CultureInfo]::InvariantCulture)
            }
            default{throw 'Unsupported clipboard backup payload type.'}
        }
        if((Get-PostalClipboardDigest $taskValue) -cne $taskPayload.digest){throw 'Protected clipboard payload verification failed.'}
        $taskObject.SetData([string]$taskPayload.format,$false,$taskValue)
    }
    return [pscustomobject]@{snapshot=$taskObject;empty=[bool]$taskSaved.empty;payloads=$taskSaved.payloads}
}
function Restore-PostalClipboardBackup(){
    $taskSaved=Read-PostalClipboardBackup
    $taskLastError=''
    for($taskAttempt=0;$taskAttempt -lt 8;$taskAttempt++){
        try{
            [Windows.Forms.Application]::DoEvents()
            if($taskSaved.empty){[Windows.Forms.Clipboard]::Clear()}else{[Windows.Forms.Clipboard]::SetDataObject($taskSaved.snapshot,$true,20,100)}
            $taskCurrent=[Windows.Forms.Clipboard]::GetDataObject()
            $taskFormats=if($null -eq $taskCurrent){@()}else{@($taskCurrent.GetFormats($false))}
            if($taskSaved.empty -and $taskFormats.Count -ne 0){throw 'The original empty clipboard was not restored.'}
            foreach($taskPayload in $taskSaved.payloads){
                if($taskPayload.format -notin $taskFormats -or (Get-PostalClipboardDigest ($taskCurrent.GetData($taskPayload.format,$false))) -cne $taskPayload.digest){throw ('Clipboard format or payload was not restored: '+$taskPayload.format)}
            }
            Remove-Item -LiteralPath $taskClipboardBackup -Force
            return $true
        }catch{$taskLastError=$_.Exception.Message;[Threading.Thread]::Sleep(125)}
    }
    throw ('Clipboard restoration failed; DPAPI-protected backup remains for -RestoreClipboardOnly: '+$taskLastError)
}
function Set-PostalTestClipboard([string]$Value){
    $taskClipboardValue=New-Object Windows.Forms.DataObject
    $taskClipboardValue.SetText($Value,[Windows.Forms.TextDataFormat]::UnicodeText)
    [Windows.Forms.Application]::DoEvents()
    [Windows.Forms.Clipboard]::SetDataObject($taskClipboardValue,$true,30,100)
}
$taskMutex=New-Object Threading.Mutex($false,('Local\ContextbaseAccessPostalClipboard-'+[Security.Principal.WindowsIdentity]::GetCurrent().User.Value))
$taskMutexAcquired=$false
try{$taskMutexAcquired=$taskMutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$taskMutexAcquired=$true}
if(-not $taskMutexAcquired){$taskMutex.Dispose();throw 'Another postal Clipboard test or restoration owns this user Clipboard. No Clipboard or fixture changes were made.'}
if($RestoreClipboardOnly){
    try{
        if([Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA){throw 'Clipboard restoration requires an STA host.'}
        Add-Type -AssemblyName System.Windows.Forms;Add-Type -AssemblyName System.Drawing;Add-Type -AssemblyName System.Security
        if(-not (Test-Path -LiteralPath $taskClipboardBackup)){throw 'No protected clipboard backup exists.'}
        [void](Restore-PostalClipboardBackup)
        Write-Output 'PASS clipboard payloads restored and protected backup removed; no Access calls executed.'
    }finally{$taskMutex.ReleaseMutex();$taskMutex.Dispose()}
    exit 0
}
$taskBefore=(Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash
$taskHashes=@(Get-PostalSourceInventory)
Write-PostalRecord ([ordered]@{status='Running';runId=$RunId;startedAt=$taskStarted;sourceSha256=$taskBefore;formalScore=$null})
$taskApp=$null;$taskVbe=$null;$taskProject=$null;$taskComponents=$null;$taskComponent=$null;$taskCodeModule=$null;$taskVbeCommandBars=$null;$taskCompiler=$null;$taskDoCmd=$null
$taskOwnedPid=0;$taskOwnedProcess=$null;$taskOwnedStart=$null;$taskOwnsProcess=$false;$taskExistingProcessIds=@();$taskExitObserved=$false;$taskProcessExitCode=$null;$taskQuitRequested=$false;$taskCleanExit=$false
$taskDatabaseOpened=$false;$taskModuleReady=$false;$taskFixtureCleaned=$false;$taskCleanupErrors=New-Object 'Collections.Generic.List[string]'
$taskClipboardSnapshot=$null;$taskClipboardCaptured=$false;$taskClipboardMutated=$false;$taskClipboardRestored=$false
$taskEmptyClipboard=$false;$taskClipboardFormats=@();$taskClipboardDigests=@{};$taskRestoreError='';$taskFatal='';$taskOfficeVersion='';$taskCopiedHash='';$taskChecks=New-Object 'Collections.Generic.List[object]';$taskProbes=New-Object 'Collections.Generic.List[object]';$taskDiagnostics=New-Object 'Collections.Generic.List[object]';$taskVbaLog='';$taskVbaAssertions=0
$taskPreviousTemp=$env:TEMP;$taskPreviousTmp=$env:TMP
try{
    if([Threading.Thread]::CurrentThread.GetApartmentState() -ne [Threading.ApartmentState]::STA){throw 'Run this suite in an STA host, for example powershell.exe -STA -File tests/Test-PostalPaste.ps1.'}
    $taskCompilerTemp=Resolve-AccessGeneratedPath (Join-Path $taskWork 'compiler') '.tmp'
    New-Item -ItemType Directory -Path $taskCompilerTemp -Force|Out-Null
    $env:TEMP=$taskCompilerTemp;$env:TMP=$taskCompilerTemp
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    Add-Type -AssemblyName System.Security
    if(Test-Path -LiteralPath $taskClipboardBackup){throw 'Protected clipboard backup from an earlier run exists. Use -RestoreClipboardOnly first.'}
    # Resolve every explicit format now: retaining the original IDataObject alone can defer reads until after it is overwritten.
    $taskClipboardOriginal=[Windows.Forms.Clipboard]::GetDataObject()
    $taskClipboardSnapshot=New-Object Windows.Forms.DataObject
    if($null -eq $taskClipboardOriginal){$taskEmptyClipboard=$true}else{
        $taskClipboardFormats=@($taskClipboardOriginal.GetFormats($false))
        if($taskClipboardFormats.Count -eq 0){$taskEmptyClipboard=$true}
        foreach($taskFormat in $taskClipboardFormats){
            $taskValue=$taskClipboardOriginal.GetData($taskFormat,$false)
            if($null -eq $taskValue){throw "Clipboard format could not be preserved before any mutation: $taskFormat"}
            if($taskValue -is [IO.MemoryStream]){$taskValue=[IO.MemoryStream]::new($taskValue.ToArray())}
            elseif($taskValue -is [Drawing.Image]){$taskValue=$taskValue.Clone()}
            elseif($taskValue -is [Array]){$taskValue=$taskValue.Clone()}
            elseif($taskValue -isnot [string] -and $taskValue -isnot [ValueType]){
                if($taskValue -is [ICloneable]){$taskValue=$taskValue.Clone()}else{throw "Clipboard format cannot be safely materialized before mutation: $taskFormat"}
            }
            $taskClipboardDigests[$taskFormat]=Get-PostalClipboardDigest $taskValue
            $taskClipboardSnapshot.SetData($taskFormat,$false,$taskValue)
        }
    }
    $taskClipboardCaptured=$true
    Save-PostalClipboardBackup -Snapshot $taskClipboardSnapshot -Formats $taskClipboardFormats -Empty $taskEmptyClipboard
    Remove-AccessIntermediate $taskFixture
    Copy-Item -LiteralPath $taskSource -Destination $taskFixture
    $taskCopiedHash=(Get-FileHash -LiteralPath $taskFixture -Algorithm SHA256).Hash
    if($taskCopiedHash -ne $taskBefore){throw 'Source-to-fixture copy hash mismatch.'}
    Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
public static class AccessPostalProbeWindows {
    delegate bool WindowCallback(IntPtr window,IntPtr state);
    [DllImport("user32.dll")] static extern bool EnumWindows(WindowCallback callback,IntPtr state);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr window,out uint process);
    [DllImport("user32.dll")] static extern int GetClassName(IntPtr window,StringBuilder name,int max);
    [DllImport("user32.dll")] static extern int GetWindowText(IntPtr window,StringBuilder name,int max);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr window);
    [DllImport("user32.dll")] static extern IntPtr GetDlgItem(IntPtr window,int id);
    [DllImport("user32.dll")] static extern bool PostMessage(IntPtr window,uint message,IntPtr w,IntPtr l);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr window,IntPtr after,int x,int y,int width,int height,uint flags);
    static Thread watcher;static volatile bool stop;static uint owned;static readonly List<string> dialogs=new List<string>();
    public static void Start(uint process) {
        owned=process;stop=false;lock(dialogs){dialogs.Clear();}
        watcher=new Thread(delegate(){while(!stop){EnumWindows(delegate(IntPtr window,IntPtr state){
            uint windowProcess;GetWindowThreadProcessId(window,out windowProcess);if(windowProcess!=owned||!IsWindowVisible(window))return true;
            var cls=new StringBuilder(128);GetClassName(window,cls,cls.Capacity);if(cls.ToString()!="#32770")return true;
            var title=new StringBuilder(256);GetWindowText(window,title,title.Capacity);lock(dialogs){dialogs.Add(title.ToString());}
            int id=GetDlgItem(window,2)!=IntPtr.Zero?2:1;PostMessage(window,0x111,new IntPtr(id),IntPtr.Zero);return true;
        },IntPtr.Zero);Thread.Sleep(100);}});watcher.IsBackground=true;watcher.Start();
    }
    public static string[] Stop(){stop=true;if(watcher!=null)watcher.Join(2000);lock(dialogs){return dialogs.ToArray();}}
}
'@
    $taskExistingProcessIds=@(Get-Process MSACCESS -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
    $taskApp=New-Object -ComObject Access.Application
    $taskHwnd=[IntPtr]([long]$taskApp.hWndAccessApp());[uint32]$taskProcessId=0
    [void][AccessPostalProbeWindows]::GetWindowThreadProcessId($taskHwnd,[ref]$taskProcessId);$taskOwnedPid=[int]$taskProcessId
    if($taskOwnedPid -eq 0 -or $taskOwnedPid -in $taskExistingProcessIds){throw 'Refusing to use an existing or unidentified Access process.'}
    $taskOwnedProcess=Get-Process -Id $taskOwnedPid
    [void]$taskOwnedProcess.Handle
    $taskOwnedStart=$taskOwnedProcess.StartTime.ToUniversalTime()
    if($taskOwnedStart -lt [DateTime]::Parse($taskStarted).ToUniversalTime().AddSeconds(-2)){throw 'Access process predates this postal test.'}
    $taskOwnsProcess=$true
    [ordered]@{pid=$taskOwnedPid;database=$taskFixture;startedAt=$taskStarted}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $taskWork 'owned-process.json') -Encoding UTF8
    [void][AccessPostalProbeWindows]::SetWindowPos($taskHwnd,[IntPtr]::Zero,-18000,0,1450,1000,0x14)
    $taskApp.Visible=$true
    $taskApp.OpenCurrentDatabase($taskFixture)
    $taskDatabaseOpened=$true;$taskOfficeVersion=[string]$taskApp.Version
    # Name every Office child RCW once; no chained property access may defer its release until after Quit.
    $taskVbe=$taskApp.VBE
    $taskProject=$taskVbe.ActiveVBProject
    $taskComponents=$taskProject.VBComponents
    $taskComponent=$taskComponents.Add(1);$taskComponent.Name='modPostalPasteTests'
    $taskCodeModule=$taskComponent.CodeModule
    $taskExistingLines=[int]$taskCodeModule.CountOfLines
    if($taskExistingLines -gt 0){$taskCodeModule.DeleteLines(1,$taskExistingLines)}
    $taskCode=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'modPostalPasteTests.bas') -Encoding UTF8 -Raw
    $taskCodeModule.AddFromString(($taskCode -replace '(?m)^Attribute VB_Name[^\r\n]*\r?\n',''))
    $taskDoCmd=$taskApp.DoCmd
    $taskDoCmd.Save(5,'modPostalPasteTests')
    $taskVbeCommandBars=$taskVbe.CommandBars
    $taskCompiler=$taskVbeCommandBars.FindControl(1,578)
    if($null -eq $taskCompiler){throw 'Native VBE compiler unavailable.'}
    if($taskCompiler.Enabled){try{$taskCompiler.Execute()}catch{if($taskCompiler.Enabled){throw}}}
    if($taskCompiler.Enabled){throw 'Postal fixture VBE compilation failed.'}
    $taskModuleReady=$true
    # The form/paste tests need only Application.Run; do not retain VBE wrappers throughout native UI activity.
    Release-PostalCom ([ref]$taskCompiler) 'VBE compiler command'
    Release-PostalCom ([ref]$taskVbeCommandBars) 'VBE CommandBars'
    Release-PostalCom ([ref]$taskCodeModule) 'CodeModule'
    Release-PostalCom ([ref]$taskComponent) 'VBComponent'
    Release-PostalCom ([ref]$taskComponents) 'VBComponents'
    Release-PostalCom ([ref]$taskProject) 'VBProject'
    Release-PostalCom ([ref]$taskVbe) 'VBE'
    Release-PostalCom ([ref]$taskDoCmd) 'DoCmd'
    [GC]::Collect();[GC]::WaitForPendingFinalizers();[GC]::Collect();[GC]::WaitForPendingFinalizers()
    if($taskCleanupErrors.Count -ne 0){throw 'Office child COM references could not be released before the form tests.'}
    $taskProductContract=[string]$taskApp.Run('PostalProductPasteContract')
    $taskChecks.Add([ordered]@{name='Built application VBA does not call the programmatic native paste API';passed=$taskProductContract.StartsWith('PASS|');detail=$taskProductContract})
    if(-not $taskProductContract.StartsWith('PASS|')){throw $taskProductContract}
    $taskValue=[string]$taskApp.Run('PostalFixtureInitialize')
    $taskChecks.Add([ordered]@{name='Initialize real new form';passed=$taskValue -eq 'PASS';detail=$taskValue})
    if($taskValue -ne 'PASS'){throw $taskValue}
    $taskFullwidth=-join (@(0xFF10,0xFF10,0xFF10,0xFF0D,0xFF10,0xFF10,0xFF10,0xFF12)|ForEach-Object{[char]$_})
    $taskCases=@(
        @('seven ASCII digits','1234567','1234567',$true),@('leading zeros','0012345','0012345',$true),
        @('3-4 separator','000-0001','0000001',$true),@('fullwidth digits and hyphen',$taskFullwidth,'0000002',$true),
        @('U+2010 separator',('000'+[char]0x2010+'0003'),'0000003',$true),@('U+2011 separator',('000'+[char]0x2011+'0004'),'0000004',$true),
        @('U+2212 separator',('000'+[char]0x2212+'0005'),'0000005',$true),@('allowed whitespace',' 0000006 ','0000006',$true),
        @('six digits','123456','',$false),@('eight digits','12345678','',$false),@('nondigit','123A567','',$false),
        @('raw over ten normalizes short','000-0001   ','',$false),@('raw over ten all digits','12345678901','',$false)
    )
    foreach($taskRoute in @('CtrlV','ShiftInsert')){
        foreach($taskCase in $taskCases){
            $taskClipboardMutated=$true;Set-PostalTestClipboard ([string]$taskCase[1])
            $taskLabel=$taskRoute+': '+[string]$taskCase[0]
            $taskValue=[string](Invoke-PostalVba 'PostalFixtureCase' @($taskLabel,$taskRoute,[string]$taskCase[2],[bool]$taskCase[3]))
            $taskChecks.Add([ordered]@{name=$taskLabel;passed=$taskValue -eq 'PASS';detail=$taskValue});Write-Output ($taskLabel+' '+$taskValue)
        }
    }
    $taskValue=[string]$taskApp.Run('PostalFixtureExisting');$taskChecks.Add([ordered]@{name='Existing record mask and immutable key';passed=$taskValue -eq 'PASS';detail=$taskValue})
    foreach($taskCase in @(@('123456','E-STU-015'),@('12345678','E-STU-002'),@('123A567','E-STU-015'),@('000-0001   ','E-STU-002'))){
        $taskValue=[string](Invoke-PostalVba 'PostalFixtureServiceRejects' @([string]$taskCase[0],[string]$taskCase[1]))
        $taskChecks.Add([ordered]@{name=('Unmasked service rejection '+$taskCase[1]+' length '+$taskCase[0].Length);passed=$taskValue -eq 'PASS';detail=$taskValue})
    }
    foreach($taskRoute in @('RunCommand','Ribbon','Popup','WM_PASTE')){
        foreach($taskNativeCase in @(@('0012345','0012345',$true),@('000-0001','0000001',$true),@('12345678','',$false),@('000-0001   ','',$false))){
            $taskPaste=[string]$taskNativeCase[0]
            $taskClipboardMutated=$true;Set-PostalTestClipboard $taskPaste
            [AccessPostalProbeWindows]::Start([uint32]$taskOwnedPid)
            try{$taskValue=[string](Invoke-PostalVba 'PostalFixtureNativeProbe' @($taskRoute,[bool]$taskNativeCase[2]))}finally{$taskDialogs=@([AccessPostalProbeWindows]::Stop())}
            $taskParts=$taskValue -split '\|',9
            $taskNativeError=0L;if($taskParts.Count -ne 9 -or -not [long]::TryParse($taskParts[0],[ref]$taskNativeError)){throw ('Invalid native probe output: '+$taskValue)}
            $taskText=$taskParts[1];$taskNativeValue=$taskParts[2];$taskNativeMessage=$taskParts[3];$taskOverlong=-not [bool]$taskNativeCase[2]
            $taskTruncated=$taskOverlong -and $taskNativeError -eq 0 -and $taskText -match '^\d{3}-\d{4}$' -and $taskText -ne '555-5555'
            $taskObservation=[ordered]@{route=$taskRoute;raw=$taskPaste;rawLength=$taskPaste.Length;errorNumber=$taskNativeError;text=$taskText;value=$taskNativeValue;messageKind=$taskNativeMessage;ribbonName=$taskParts[4];activeControl=$taskParts[5];postalInputActive=$taskParts[6];guardActive=$taskParts[7];shortcutMenuBar=$taskParts[8];dialogsDismissed=$taskDialogs;silentTruncationObserved=$taskTruncated;supportedApplicationRoute=$taskRoute -ne 'RunCommand'}
            $taskProbes.Add($taskObservation)
            if($taskOverlong){
                $taskPassed=$taskNativeError -eq 0 -and $taskText -ceq '555-5555' -and $taskNativeValue -ceq '5555555' -and $taskNativeMessage -ceq 'POSTAL_ERROR' -and $taskDialogs.Count -eq 0
                $taskCheckName=$taskRoute+' rejects overlong clipboard, keeps prior Value/Text, and shows postal error length '+$taskPaste.Length
            }else{
                $taskExpected=[string]$taskNativeCase[1]
                $taskPassed=$taskNativeError -eq 0 -and $taskNativeValue -ceq $taskExpected -and $taskText -ceq ($taskExpected.Substring(0,3)+'-'+$taskExpected.Substring(3)) -and $taskNativeMessage -ceq 'EMPTY' -and $taskDialogs.Count -eq 0
                $taskCheckName=$taskRoute+' valid full clipboard displays 3-4 and stores exact seven digits length '+$taskPaste.Length
            }
            if($taskRoute -eq 'RunCommand'){
                $taskDiagnostics.Add([ordered]@{kind='Programmatic Access native command API boundary';supportedApplicationRoute=$false;applicationUsageVerifiedAbsent=$taskProductContract.StartsWith('PASS|');name=$taskCheckName;uiContractSatisfied=$taskPassed;observation=$taskObservation;detail=$taskValue;interpretation='DoCmd.RunCommand acCmdPaste is not used by the application and does not guarantee complete raw clipboard validation; observed truncation remains recorded as a boundary finding.'})
            }else{$taskChecks.Add([ordered]@{name=$taskCheckName;passed=$taskPassed;detail=$taskValue})}
        }
    }
    $taskValue=[string]$taskApp.Run('PostalFixtureCleanup');$taskChecks.Add([ordered]@{name='Disposable form cleanup and no inserted students';passed=$taskValue -eq 'PASS';detail=$taskValue});$taskFixtureCleaned=$taskValue -eq 'PASS'
    $taskVbaLog=[string]$taskApp.Run('PostalPasteTestLog');$taskVbaAssertions=[long]$taskApp.Run('PostalPasteAssertions')
}catch{$taskFatal=$_.Exception.ToString()+[Environment]::NewLine+$_.ScriptStackTrace;Write-Output $taskFatal}
finally{
    # Restore the user's clipboard before any remote COM cleanup that could block.
    if($taskClipboardCaptured){
        try{
            if(Test-Path -LiteralPath $taskClipboardBackup){$taskClipboardRestored=Restore-PostalClipboardBackup}else{$taskClipboardRestored=-not $taskClipboardMutated}
        }catch{$taskRestoreError=$_.Exception.Message;$taskClipboardRestored=$false}
    }else{$taskClipboardRestored=-not $taskClipboardMutated}
    if($null -ne $taskApp -and $taskOwnsProcess -and $taskModuleReady){
        if(-not $taskFixtureCleaned){
            try{
                $taskCleanupResult=[string]$taskApp.Run('PostalFixtureCleanup')
                $taskFixtureCleaned=$taskCleanupResult -eq 'PASS'
                if(-not $taskFixtureCleaned){$taskCleanupErrors.Add('PostalFixtureCleanup: '+$taskCleanupResult)}
            }catch{$taskCleanupErrors.Add('PostalFixtureCleanup: '+$_.Exception.Message)}
        }
        try{$taskVbaLog=[string]$taskApp.Run('PostalPasteTestLog');$taskVbaAssertions=[long]$taskApp.Run('PostalPasteAssertions')}catch{$taskCleanupErrors.Add('Final VBA result read: '+$_.Exception.Message)}
    }
    # Release nested VBE/Office RCWs while their Access server and project still exist.
    Release-PostalCom ([ref]$taskCompiler) 'VBE compiler command'
    Release-PostalCom ([ref]$taskVbeCommandBars) 'VBE CommandBars'
    Release-PostalCom ([ref]$taskCodeModule) 'CodeModule'
    Release-PostalCom ([ref]$taskComponent) 'VBComponent'
    Release-PostalCom ([ref]$taskComponents) 'VBComponents'
    Release-PostalCom ([ref]$taskProject) 'VBProject'
    Release-PostalCom ([ref]$taskVbe) 'VBE'
    Release-PostalCom ([ref]$taskDoCmd) 'DoCmd'
    try{[GC]::Collect();[GC]::WaitForPendingFinalizers();[GC]::Collect();[GC]::WaitForPendingFinalizers()}catch{$taskCleanupErrors.Add('Pre-Quit finalizers: '+$_.Exception.Message)}
    if($null -ne $taskApp -and $taskOwnsProcess){
        if($taskDatabaseOpened){try{$taskApp.CloseCurrentDatabase();$taskDatabaseOpened=$false}catch{$taskCleanupErrors.Add('CloseCurrentDatabase: '+$_.Exception.Message)}}
        try{$taskApp.Quit(2);$taskQuitRequested=$true}catch{$taskCleanupErrors.Add('Quit: '+$_.Exception.Message)}
    }
    Release-PostalCom ([ref]$taskApp) 'Access.Application'
    try{[GC]::Collect();[GC]::WaitForPendingFinalizers()}catch{$taskCleanupErrors.Add('Post-Quit finalizers: '+$_.Exception.Message)}
    if($null -ne $taskOwnedProcess){
        try{
            if($taskOwnsProcess){
                $taskExitObserved=$taskOwnedProcess.WaitForExit(10000)
                if($taskExitObserved){$taskProcessExitCode=$taskOwnedProcess.ExitCode}else{$taskCleanupErrors.Add('Owned Access process did not exit within 10 seconds.')}
                if($taskExitObserved -and $taskProcessExitCode -ne 0){$taskCleanupErrors.Add('Owned Access process exited abnormally: '+$taskProcessExitCode)}
            }
        }catch{$taskCleanupErrors.Add('Owned process exit observation: '+$_.Exception.Message)}
        finally{try{$taskOwnedProcess.Dispose()}catch{$taskCleanupErrors.Add('Owned process handle disposal: '+$_.Exception.Message)}finally{$taskOwnedProcess=$null}}
    }
    $taskCleanExit=$taskOwnsProcess -and $taskQuitRequested -and $taskExitObserved -and $taskProcessExitCode -eq 0 -and $taskCleanupErrors.Count -eq 0
    $env:TEMP=$taskPreviousTemp;$env:TMP=$taskPreviousTmp
    $taskAfter=(Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash
    $taskSourceAfter=@(Get-PostalSourceInventory)
    $taskSourcesUnchanged=($taskHashes|ConvertTo-Json -Compress) -ceq ($taskSourceAfter|ConvertTo-Json -Compress)
    $taskChecks.Add([ordered]@{name='Source ACCDB unchanged';passed=$taskBefore -eq $taskAfter;detail=$taskAfter})
    $taskChecks.Add([ordered]@{name='Source copy initially identical';passed=$taskCopiedHash -eq $taskBefore;detail=$taskCopiedHash})
    $taskChecks.Add([ordered]@{name='Product and test source inventory unchanged including added or removed files';passed=$taskSourcesUnchanged;detail=('start='+$taskHashes.Count+';end='+$taskSourceAfter.Count)})
    $taskChecks.Add([ordered]@{name='User clipboard restored';passed=$taskClipboardRestored;detail=$taskRestoreError})
    $taskFailed=@($taskChecks|Where-Object{-not $_.passed}).Count
    $taskStatus=if(-not $taskFatal -and $taskFailed -eq 0 -and $taskVbaAssertions -gt 100 -and $taskCleanExit){'Passed'}else{'Failed'}
    $taskRecoveryRecord=Join-Path $taskWork 'clipboard-recovery.json'
    $taskRecovery=if(Test-Path -LiteralPath $taskRecoveryRecord){Get-Content -LiteralPath $taskRecoveryRecord -Raw -Encoding UTF8|ConvertFrom-Json}else{$null}
    try{Write-PostalRecord ([ordered]@{status=$taskStatus;runId=$RunId;startedAt=$taskStarted;completedAt=[DateTime]::UtcNow.ToString('o');sourceFile=$taskSource;sourceSha256=$taskBefore;sourceSha256After=$taskAfter;fixture=$taskFixture;fixtureInitialSha256=$taskCopiedHash;sourceFiles=$taskHashes;sourceFilesAfter=$taskSourceAfter;officeVersion=$taskOfficeVersion;ownedProcess=$taskOwnedPid;ownedProcessStart=$(if($taskOwnedStart){$taskOwnedStart.ToString('o')}else{$null});existingProcessIds=$taskExistingProcessIds;quitRequested=$taskQuitRequested;exitObserved=$taskExitObserved;processExitCode=$taskProcessExitCode;cleanExit=$taskCleanExit;cleanupErrors=@($taskCleanupErrors);fixtureOnly=$true;passed=@($taskChecks|Where-Object{$_.passed}).Count;failed=$taskFailed;checks=$taskChecks;vbaAssertions=$taskVbaAssertions;vbaLog=$taskVbaLog;nativePasteProbes=$taskProbes;diagnostics=$taskDiagnostics;productPasteContract=$taskProductContract;clipboardCaptured=$taskClipboardCaptured;clipboardMutated=$taskClipboardMutated;clipboardRestored=$taskClipboardRestored;clipboardRestoreError=$taskRestoreError;protectedClipboardBackupRemaining=(Test-Path -LiteralPath $taskClipboardBackup);priorTrialClipboardRecovery=$taskRecovery;inputMethod='Focused Access controls and STA Unicode clipboard: CtrlV/ShiftInsert event bridges, actual Ribbon ExecuteMso, native popup Paste button, and WM_PASTE; unused programmatic RunCommand API kept as separate diagnostics';notExecuted=@('physical keyboard and Japanese IME composition','Office 32-bit','production database');formalScore=$null;fatal=$taskFatal})}finally{$taskMutex.ReleaseMutex();$taskMutex.Dispose()}
}
if($taskStatus -ne 'Passed'){exit 1}
