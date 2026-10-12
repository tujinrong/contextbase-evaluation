[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$profileRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$projectRoot=[IO.Path]::GetFullPath((Join-Path $profileRoot '../..'))
$outputRoot=Join-Path $profileRoot 'build/20261012-evidence-01-ui'
$frontend=Join-Path $outputRoot '20261012-build-04-access-single-evidence-01-ui.accdb'
$backend=Join-Path $outputRoot 'initial-staging.accdb'
$reportRoot=Join-Path $projectRoot 'test-report/20261012-evidence-01/Access-ui'
$production=Join-Path $profileRoot 'StudentManagement.accdb'
$expectedProduction='838F5FE63826FCE58FACE6C5102D363AF41C3EF433D6B2D7229C8D5DE0C93DE5'
if((Get-FileHash -LiteralPath $production -Algorithm SHA256).Hash -ne $expectedProduction){throw 'Production hash differs; stop without opening it.'}
if(Test-Path -LiteralPath $outputRoot){throw 'Historical fixture directory exists; do not overwrite.'}
if(Test-Path -LiteralPath $reportRoot){throw 'Historical UI report directory exists; do not overwrite.'}
New-Item -ItemType Directory -Path $outputRoot,$reportRoot | Out-Null
$inputFiles=@(Get-ChildItem -LiteralPath (Join-Path $profileRoot 'spec'),(Join-Path $profileRoot 'Modules'),(Join-Path $profileRoot 'Classes'),(Join-Path $profileRoot 'database') -Recurse -File | Where-Object {$_.FullName -notmatch '[\/](bin|obj|build)[\/]'} | Sort-Object FullName | ForEach-Object {
    $meta=if($_.Extension -eq '.md'){Get-Content -LiteralPath $_.FullName -TotalCount 1}else{''}
    $version=if($meta -match '"version"\s*:\s*"([^"]+)"'){$Matches[1]}else{$null}
    [ordered]@{path=$_.FullName;version=$version;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
})
$inputFiles+=@([ordered]@{path=(Join-Path $profileRoot 'Build-Access.ps1');sha256=(Get-FileHash -LiteralPath (Join-Path $profileRoot 'Build-Access.ps1') -Algorithm SHA256).Hash})
$state=[ordered]@{runId='20261012-evidence-01-ui';profile='Access';status='RUNNING';inputs=$inputFiles;productionDatabase=$production;productionHashBefore=$expectedProduction;productionOpened=$false;sharedSqlConnected=$false;frontend=$frontend;backendStaging=$backend;visible=$false;interactiveScreenshots='NOT_RUN_DELEGATED_TO_ROOT';error=$null}
function Save-Evidence {$state|ConvertTo-Json -Depth 14|Set-Content -LiteralPath (Join-Path $reportRoot 'results.json') -Encoding UTF8}
function Read-Rows([string]$sql){
    $rs=$db.OpenRecordset($sql)
    try {
        $rows=@()
        while(-not $rs.EOF){
            $row=[ordered]@{}
            for($index=0;$index -lt $rs.Fields.Count;$index++){
                $field=$rs.Fields.Item($index);$value=$field.Value
                if($value -is [DBNull]){$value=$null}
                $row[$field.Name]=$value
            }
            $rows+=$row;$rs.MoveNext()
        }
        return ,$rows
    }finally{$rs.Close();[Runtime.InteropServices.Marshal]::FinalReleaseComObject($rs)|Out-Null}
}
$access=$null;$db=$null;$component=$null
try {
    Save-Evidence
    & (Join-Path $profileRoot 'Build-Access.ps1') -Frontend $frontend -Backend $backend -CreateBackend -SingleFile -Compile -IncludeTests -NoStartup 2>&1 | Tee-Object -FilePath (Join-Path $reportRoot 'create.log')
    $access=New-Object -ComObject Access.Application
    $access.Visible=$false
    $access.OpenCurrentDatabase($frontend)
    $state.officeVersion=$access.Version
    $component=$access.VBE.ActiveVBProject.VBComponents.Add(1)
    $component.Name='modEvidenceUiSeed'
    if($component.CodeModule.CountOfLines -gt 0){$component.CodeModule.DeleteLines(1,$component.CodeModule.CountOfLines)}
    $seedCode=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'modEvidenceUiSeed.bas') -Raw -Encoding UTF8
    $component.CodeModule.AddFromString(($seedCode -replace '(?m)^Attribute VB_Name.*\r?\n',''))
    $access.DoCmd.Save(5,'modEvidenceUiSeed')
    $access.DoCmd.RunCommand(126)
    $state.seedModuleCompiled=$true
    $seedResult=$access.Run('EvidenceSeedUi')
    $seedResult|Set-Content -LiteralPath (Join-Path $reportRoot 'seed.raw.log') -Encoding UTF8
    $state.seedResult=$seedResult
    if($seedResult -notmatch '^PASS\|'){throw ('Seed failed: '+$seedResult)}
    $db=$access.CurrentDb()
    $state.backendProperty=[string]$db.Properties.Item('StudentBackendPath').Value
    $state.externalLinks=@($db.TableDefs|Where-Object {$_.Name -notlike 'MSys*' -and $_.Connect -ne ''}|Select-Object -ExpandProperty Name)
    if($state.backendProperty -ne 'SELF' -or $state.externalLinks.Count -ne 0){throw 'Fixture is not independent SingleFile.'}
    $state.students=Read-Rows 'SELECT * FROM m_student ORDER BY student_no'
    $state.classes=Read-Rows 'SELECT * FROM m_class ORDER BY class_id'
    $state.audits=Read-Rows 'SELECT target_table,target_key,operation_type,before_version,after_version,executed_by FROM t_operation_log ORDER BY log_id'
    if($state.students.Count -ne 3 -or $state.classes.Count -ne 1 -or $state.audits.Count -ne 4){throw 'DAO readback row counts differ.'}
    foreach($row in $state.students){
        if($row.student_no -notmatch '^TEST-ACE-00[1-3]$' -or $row.row_version -ne 1 -or $row.is_deleted){throw 'Unexpected student identity/version/deletion.'}
        if($null -ne $row.relationship_category -or $null -ne $row.relationship_code){throw 'Optional relationship pair should remain NULL.'}
    }
    if(@($state.audits|Where-Object {$_.operation_type -ne 'CREATE'}).Count -ne 0){throw 'Expected production CREATE audits.'}
    $state.testCounts=[ordered]@{classCommitted=1;studentsCommitted=3;daoStudents=3;daoClasses=1;daoCreateAudits=4;externalLinks=0;fourNullRelationshipStudents=3}
    [ordered]@{schema='student-ui-fixture/1.0';profile='Access';fixtureOnly=$true;sharedSqlConnected=$false;synthetic=$true;description='Production MaintainClass/SaveStudent committed fictional records only to the fresh single-file ACCDB.';students=$state.students;classes=$state.classes}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $reportRoot 'synthetic-data.json') -Encoding UTF8
    $state.status='FRESH_ACE_DAO_UI_FIXTURE_READY'
}catch{$state.status='FAILED';$state.error=$_.Exception.ToString();Write-Error -Message $state.error -ErrorAction Continue}
finally {
    if($null -ne $component){[Runtime.InteropServices.Marshal]::FinalReleaseComObject($component)|Out-Null;$component=$null}
    if($null -ne $db){$db.Close();[Runtime.InteropServices.Marshal]::FinalReleaseComObject($db)|Out-Null;$db=$null}
    if($null -ne $access){try{$access.CloseCurrentDatabase()}catch{};$access.Quit(2);[Runtime.InteropServices.Marshal]::FinalReleaseComObject($access)|Out-Null;$access=$null}
    [GC]::Collect();[GC]::WaitForPendingFinalizers()
    $state.productionHashAfter=(Get-FileHash -LiteralPath $production -Algorithm SHA256).Hash
    if($state.productionHashAfter -ne $expectedProduction){$state.status='FAILED';$state.error='Production hash changed externally; preserve and report.'}
    $state.inputsStable=@($inputFiles|Where-Object {(Get-FileHash -LiteralPath $_.path -Algorithm SHA256).Hash -ne $_.sha256}).Count -eq 0
    if(-not $state.inputsStable){$state.status='FAILED';$state.error='Input hash changed; results not valid for new input.'}
    if(Test-Path -LiteralPath $frontend){$state.frontendSha256=(Get-FileHash -LiteralPath $frontend -Algorithm SHA256).Hash}
    $state.finished=(Get-Date).ToUniversalTime().ToString('o');Save-Evidence
}
if($state.status -eq 'FAILED'){exit 1}
$state|ConvertTo-Json -Depth 5
