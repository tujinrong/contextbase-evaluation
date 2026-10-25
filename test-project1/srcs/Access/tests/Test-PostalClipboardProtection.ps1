param([ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId='manual')
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
. (Join-Path $taskRoot 'tools/GeneratedPaths.ps1')
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Security
$taskTestScript=Join-Path $taskRoot 'tests/Test-PostalPaste.ps1'
$taskErrors=$null;$taskTokens=$null
$taskAst=[System.Management.Automation.Language.Parser]::ParseFile($taskTestScript,[ref]$taskTokens,[ref]$taskErrors)
if($taskErrors.Count){throw 'Postal runner has parse errors.'}
foreach($taskFunction in $taskAst.FindAll({param($Node)$Node -is [System.Management.Automation.Language.FunctionDefinitionAst]},$false)){Invoke-Expression $taskFunction.Extent.Text}
$taskWork=Resolve-AccessGeneratedPath (Join-Path $taskRoot '.tmp/postal-paste/protection-fixture') '.tmp'
New-Item -ItemType Directory -Path $taskWork -Force|Out-Null
$taskClipboardBackup=Resolve-AccessGeneratedPath (Join-Path $taskWork 'clipboard-backup.bin') '.tmp'
if(Test-Path -LiteralPath $taskClipboardBackup){throw 'A synthetic protection-test backup unexpectedly exists.'}
$taskChecks=New-Object 'Collections.Generic.List[object]'
function Test-Protected($Condition,[string]$Name){$taskChecks.Add([ordered]@{name=$Name;passed=[bool]$Condition});if(-not $Condition){throw $Name}}
try{
    $taskData=New-Object Windows.Forms.DataObject
    $taskData.SetData('UnicodeText',$false,'synthetic-sensitive-marker')
    $taskData.SetData('HTML Format',$false,'<html>synthetic marker</html>')
    $taskData.SetData('SyntheticBytes',$false,[byte[]](0,1,2,255))
    $taskData.SetData('SyntheticStream',$false,[IO.MemoryStream]::new([byte[]](9,8,7,0)))
    $taskData.SetData('SyntheticPaths',$false,[string[]]@('C:\synthetic\one.txt','C:\synthetic\two.txt'))
    $taskData.SetData('SyntheticLocale',$false,[int]1041)
    $taskFormats=@($taskData.GetFormats($false))
    Save-PostalClipboardBackup -Snapshot $taskData -Formats $taskFormats -Empty $false
    Test-Protected (Test-Path -LiteralPath $taskClipboardBackup) 'durable DPAPI-protected backup created before any clipboard mutation'
    $taskCipher=[IO.File]::ReadAllBytes($taskClipboardBackup)
    Test-Protected (-not [Text.Encoding]::Unicode.GetString($taskCipher).Contains('synthetic-sensitive-marker')) 'backup does not contain plaintext Unicode test marker'
    Test-Protected (-not [Text.Encoding]::UTF8.GetString($taskCipher).Contains('synthetic-sensitive-marker')) 'backup does not contain plaintext UTF8 test marker'
    $taskSaved=Read-PostalClipboardBackup
    Test-Protected (-not $taskSaved.empty -and @($taskSaved.payloads).Count -eq 6) 'six explicitly supported payload types survive DPAPI roundtrip'
    foreach($taskFormat in $taskFormats){Test-Protected ((Get-PostalClipboardDigest ($taskSaved.snapshot.GetData($taskFormat,$false))) -ceq (Get-PostalClipboardDigest ($taskData.GetData($taskFormat,$false)))) ('private payload digest survives roundtrip: '+$taskFormat)}
    $taskBefore=(Get-FileHash -LiteralPath $taskClipboardBackup -Algorithm SHA256).Hash
    $taskRefused=$false
    try{Save-PostalClipboardBackup -Snapshot $taskData -Formats $taskFormats -Empty $false}catch{$taskRefused=$_.Exception.Message -like '*earlier clipboard backup*'}
    Test-Protected ($taskRefused -and (Get-FileHash -LiteralPath $taskClipboardBackup -Algorithm SHA256).Hash -ceq $taskBefore) 'an earlier backup cannot be overwritten by another test'
    Remove-Item -LiteralPath $taskClipboardBackup -Force
    Save-PostalClipboardBackup -Snapshot (New-Object Windows.Forms.DataObject) -Formats @() -Empty $true
    $taskSaved=Read-PostalClipboardBackup
    Test-Protected ($taskSaved.empty -and @($taskSaved.payloads).Count -eq 0) 'empty clipboard state can be durably represented'
    Remove-Item -LiteralPath $taskClipboardBackup -Force
    $taskUnsafe=New-Object Windows.Forms.DataObject;$taskUnsafe.SetData('UnsafeObject',$false,[object]::new())
    $taskRefused=$false
    try{Save-PostalClipboardBackup -Snapshot $taskUnsafe -Formats @('UnsafeObject') -Empty $false}catch{$taskRefused=$_.Exception.Message -like '*cannot be durably preserved*'}
    Test-Protected ($taskRefused -and -not (Test-Path -LiteralPath $taskClipboardBackup)) 'unsupported live objects fail before any clipboard mutation or backup overwrite'
    $taskLock=New-Object Threading.Mutex($false,('Local\ContextbaseAccessPostalClipboard-'+[Security.Principal.WindowsIdentity]::GetCurrent().User.Value))
    $taskLocked=$false
    try{
        $taskLocked=$taskLock.WaitOne(0)
        Test-Protected $taskLocked 'synthetic test owns the same user-level mutex as normal and recovery paths'
        $taskOldPreference=$ErrorActionPreference;$ErrorActionPreference='Continue'
        try{$taskContender=(& powershell.exe -NoProfile -STA -File $taskTestScript -Database (Join-Path $taskRoot '.tmp/native-quality/source.accdb') -RestoreClipboardOnly 2>&1|Out-String);$taskExit=$LASTEXITCODE}finally{$ErrorActionPreference=$taskOldPreference}
        Test-Protected ($taskExit -ne 0 -and $taskContender -like '*Another postal Clipboard test or restoration owns*') 'a concurrent restore-only process refuses before Clipboard or fixture mutation'
        Test-Protected (-not (Test-Path -LiteralPath (Join-Path $taskRoot '.tmp/postal-paste/clipboard-backup.bin'))) 'concurrent restore probe creates or deletes no real protected Clipboard backup'
    }finally{if($taskLocked){$taskLock.ReleaseMutex()};$taskLock.Dispose()}
    $taskStatus='Passed'
}catch{$taskStatus='Failed';$taskFatal=$_.Exception.ToString();Write-Output $taskFatal}
finally{
    if(Test-Path -LiteralPath $taskClipboardBackup){Remove-Item -LiteralPath $taskClipboardBackup -Force}
    [ordered]@{status=$taskStatus;runId=$RunId;completedAt=[DateTime]::UtcNow.ToString('o');checks=$taskChecks;count=$taskChecks.Count;runnerSha256=(Get-FileHash -LiteralPath $taskTestScript -Algorithm SHA256).Hash;testFile='tests/Test-PostalClipboardProtection.ps1';testSha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash;scope='Synthetic DataObject serialization and DPAPI only; no Windows Clipboard or Access calls';privatePayloadLogged=$false;protectedSyntheticBackupRemoved=(-not (Test-Path -LiteralPath $taskClipboardBackup));fatal=$taskFatal}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $taskRoot 'build/test-results/postal-clipboard-protection.json') -Encoding UTF8
}
if($taskStatus -ne 'Passed'){exit 1};Write-Output ('PASS '+$taskChecks.Count+' synthetic payload protection checks; no Windows Clipboard or Access calls.')
