param([ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId='relationship',[string]$ReportDirectory='')
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../tools/GeneratedPaths.ps1')
if (-not $ReportDirectory) { $ReportDirectory=Join-Path $script:AccessMethodRoot 'build/test-results' }
$taskReport=Resolve-AccessReportPath $ReportDirectory
$taskFixture=Resolve-AccessGeneratedPath (Join-Path $PSScriptRoot '../.tmp/tests/relationship.accdb') '.tmp'
New-Item -ItemType Directory -Path $taskReport -Force | Out-Null
New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($taskFixture)) -Force | Out-Null
$taskInputs=@(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot '../spec') -Recurse -File | Sort-Object FullName | ForEach-Object { @{path=$_.FullName;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash} })
Remove-AccessIntermediate $taskFixture
$taskEngine=New-Object -ComObject DAO.DBEngine.120
$taskDb=$taskEngine.CreateDatabase([IO.Path]::GetFullPath($taskFixture),';LANGID=0x0409;CP=1252;COUNTRY=0',128)
$taskResults=[Collections.Generic.List[object]]::new()
$taskDdl=@(
 'CREATE TABLE m_code(category_id TEXT(48) NOT NULL,code_value TEXT(20) NOT NULL,CONSTRAINT pk_code PRIMARY KEY(category_id,code_value))',
 'CREATE TABLE probe(probe_id COUNTER CONSTRAINT pk_probe PRIMARY KEY,emergency_contact_name TEXT(16),relationship_category TEXT(48),relationship_code TEXT(4),emergency_phone_number TEXT(32))'
)
function Invoke-Probe([string]$Name,[string]$Sql,[bool]$Allowed) {
    $taskAccepted=$false; $taskError=''; $taskErrors=@()
    try { $taskDb.Execute($Sql,128); $taskAccepted=$true }
    catch {
        $taskError=$_.Exception.Message
        foreach ($taskDaoError in $taskEngine.Errors) { $taskErrors+=@{number=$taskDaoError.Number;description=$taskDaoError.Description} }
    }
    $taskOk=$taskAccepted -eq $Allowed
    $taskResults.Add([ordered]@{name=$Name;sql=$Sql;expectedAccepted=$Allowed;actualAccepted=$taskAccepted;passed=$taskOk;exception=$taskError;daoErrors=$taskErrors})
    Write-Output "$Name expected=$Allowed actual=$taskAccepted passed=$taskOk $taskError"
    if (-not $taskOk) { throw "Structural revalidation failed: $Name" }
}
try {
 foreach ($taskSql in $taskDdl) { $taskDb.Execute($taskSql,128) }
 foreach ($taskFieldName in @('emergency_contact_name','relationship_category','relationship_code','emergency_phone_number')) {
    $taskField=$taskDb.TableDefs.Item('probe').Fields.Item($taskFieldName)
    $taskField.Required=$false; $taskField.AllowZeroLength=$false; $taskField.DefaultValue=''
 }
 $taskRule='(([emergency_contact_name] Is Null) And ([relationship_category] Is Null) And ([relationship_code] Is Null) And ([emergency_phone_number] Is Null)) Or (([emergency_contact_name] Is Not Null) And ([relationship_category] Is Not Null) And ([relationship_code] Is Not Null) And ([emergency_phone_number] Is Not Null) And ([relationship_category]="RELATIONSHIP"))'
 $taskTable=$taskDb.TableDefs.Item('probe'); $taskTable.ValidationRule=$taskRule
 $taskRelation=$taskDb.CreateRelation('fk_probe_relationship','m_code','probe',0)
 $taskField=$taskRelation.CreateField('category_id'); $taskField.ForeignName='relationship_category'; $taskRelation.Fields.Append($taskField)
 $taskField=$taskRelation.CreateField('code_value'); $taskField.ForeignName='relationship_code'; $taskRelation.Fields.Append($taskField)
 $taskDb.Relations.Append($taskRelation)
 $taskDb.Execute("INSERT INTO m_code VALUES('RELATIONSHIP','01')",128)
 $taskDb.Execute("INSERT INTO m_code VALUES('GRADE','01')",128)
 for ($taskMask=0; $taskMask -lt 16; $taskMask++) {
    $taskValues=@()
    $taskNonNull=@("'fixture'","'RELATIONSHIP'","'01'","'0312345678'")
    for ($taskBit=0; $taskBit -lt 4; $taskBit++) { if ($taskMask -band (1 -shl $taskBit)) { $taskValues+=$taskNonNull[$taskBit] } else { $taskValues+='NULL' } }
    Invoke-Probe "NULL-pattern-$taskMask" "INSERT INTO probe(emergency_contact_name,relationship_category,relationship_code,emergency_phone_number) VALUES($($taskValues -join ','))" ($taskMask -in @(0,15))
 }
 Invoke-Probe 'nonexistent-code' "INSERT INTO probe(emergency_contact_name,relationship_category,relationship_code,emergency_phone_number) VALUES('fixture','RELATIONSHIP','99','0312345678')" $false
 Invoke-Probe 'other-category-same-code' "INSERT INTO probe(emergency_contact_name,relationship_category,relationship_code,emergency_phone_number) VALUES('fixture','GRADE','01','0312345678')" $false
 Invoke-Probe 'referenced-parent-delete' "DELETE FROM m_code WHERE category_id='RELATIONSHIP' AND code_value='01'" $false
 Invoke-Probe 'referenced-parent-key-update' "UPDATE m_code SET code_value='02' WHERE category_id='RELATIONSHIP' AND code_value='01'" $false
 Invoke-Probe 'unreferenced-parent-delete' "DELETE FROM m_code WHERE category_id='GRADE' AND code_value='01'" $true
 $taskRead=$taskDb.OpenRecordset('SELECT * FROM probe ORDER BY probe_id')
 $taskReadback=@()
 while (-not $taskRead.EOF) {
    $taskReadback+=@{categoryIsNull=($null -eq $taskRead.Fields.Item('relationship_category').Value -or $taskRead.Fields.Item('relationship_category').Value -is [DBNull]);codeIsNull=($null -eq $taskRead.Fields.Item('relationship_code').Value -or $taskRead.Fields.Item('relationship_code').Value -is [DBNull])}
    $taskRead.MoveNext()
 }
 $taskRead.Close()
 $taskState='Passed'
} catch { $taskState='Failed'; $taskFatal=$_.Exception.Message; Write-Output $taskFatal }
finally {
 $taskOutput=[ordered]@{runId=$RunId;completedAt=[DateTime]::UtcNow.ToString('o');specConfigurationVersion='8.1';specDatabaseIndexVersion='8.2';specBusinessVersion='8.0';relationshipRuleOriginVersion='7.4';inputs=$taskInputs;problemId='STR-ACCESS-001';status=$taskState;fatal=$taskFatal;engineVersion=$taskEngine.Version;fixtureOnly=$true;fixture=[IO.Path]::GetFullPath($taskFixture);ddl=$taskDdl;validationRule=$taskRule;relationAttributes=0;tests=$taskResults;readback=$taskReadback}
 $taskDb.Close()
 $taskOutput.fixtureSha256=(Get-FileHash -LiteralPath $taskFixture -Algorithm SHA256).Hash
 $taskOutput | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $taskReport 'relationship.json') -Encoding UTF8
 [Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskDb) | Out-Null
 [Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskEngine) | Out-Null
}
if ($taskState -ne 'Passed') { exit 1 }
