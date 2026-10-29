$ErrorActionPreference='Stop'
$sp2Root=Split-Path -Parent $PSScriptRoot
$sp2Spec=[IO.Path]::GetFullPath((Join-Path $sp2Root '../../spec/CSharp_ASPNET'))
$sp2Views=@{'F01'='src/CareerManagement.Web/Views/Account/Login.cshtml';'F02'='src/CareerManagement.Web/Views/Menu/Index.cshtml';'F03'='src/CareerManagement.Web/Views/Employees/Index.cshtml';'F04'='src/CareerManagement.Web/Views/Employees/Edit.cshtml';'F06'='src/CareerManagement.Web/Views/Codes/Index.cshtml'}
$sp2Events=@{
 'F01-E01'=@('src/CareerManagement.Web/Controllers/AccountController.cs','Login','src/CareerManagement.Infrastructure/Authentication/AuthService.cs','AuthenticateAsync');'F01-E02'=@('src/CareerManagement.Web/Controllers/AccountController.cs','Exit')
 'F02-E01'=@('src/CareerManagement.Web/Controllers/AccountController.cs','MenuController','src/CareerManagement.Web/Views/Menu/Index.cshtml','F02-I02');'F02-E02'=@('src/CareerManagement.Web/Controllers/AccountController.cs','Logout')
 'F03-E01'=@('src/CareerManagement.Web/Controllers/EmployeesController.cs','Search','src/CareerManagement.Infrastructure/Sql/Repository.cs','SearchAsync');'F03-E02'=@('src/CareerManagement.Web/Controllers/EmployeesController.cs','Invalidate','src/CareerManagement.Web/wwwroot/js/site.js','invalidate');'F03-E03'=@('src/CareerManagement.Web/Controllers/EmployeesController.cs','Open','src/CareerManagement.Web/Views/Employees/Index.cshtml','F03-I13')
 'F04-E01'=@('src/CareerManagement.Web/Controllers/EmployeesController.cs','Edit','src/CareerManagement.Infrastructure/Sql/EmployeeService.cs','ReadAsync');'F04-E02'=@('src/CareerManagement.Web/Controllers/EmployeesController.cs','Draft');'F04-E03'=@('src/CareerManagement.Web/Controllers/EmployeesController.cs','Save','src/CareerManagement.Infrastructure/Sql/EmployeeService.cs','SaveAsync');'F04-E04'=@('src/CareerManagement.Web/Controllers/EmployeesController.cs','Cancel')
 'F05-E01'=@('src/CareerManagement.Infrastructure/Sql/EmployeeService.cs','ReportAsync');'F05-E02'=@('src/CareerManagement.Infrastructure/Reports/ReportService.cs','Create','src/CareerManagement.Web/Controllers/EmployeesController.cs','Export');'F05-E03'=@('src/CareerManagement.Infrastructure/State/StateStore.cs','ExportOperationRegistry','src/CareerManagement.Web/Controllers/EmployeesController.cs','ExportCancel')
 'F06-E01'=@('src/CareerManagement.Web/Controllers/CodesController.cs','Open');'F06-E02'=@('src/CareerManagement.Web/Controllers/CodesController.cs','Save','src/CareerManagement.Infrastructure/Sql/CodeService.cs','SaveAsync');'F06-E03'=@('src/CareerManagement.Web/Controllers/CodesController.cs','Cancel')
}
function Sp2-Refs([string[]]$Values){
 $sp2Refs=@()
 for($sp2Index=0;$sp2Index -lt $Values.Length;$sp2Index+=2){
  $sp2Path=Join-Path $sp2Root $Values[$sp2Index]
  $sp2Match=Select-String -LiteralPath $sp2Path -SimpleMatch $Values[$sp2Index+1] | Select-Object -First 1
  if(-not $sp2Match){throw "Missing implementation symbol $($Values[$sp2Index+1])"}
  $sp2Refs+=@{path=$Values[$sp2Index];symbol=$Values[$sp2Index+1];line=$sp2Match.LineNumber}
 }
 return $sp2Refs
}
$sp2Items=@();$sp2EventRows=@();$sp2Inputs=@()
Get-ChildItem -LiteralPath (Join-Path $sp2Spec '詳細仕様書') -Filter '*.md' | Sort-Object Name | ForEach-Object {
 $sp2Text=Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8
 $sp2Feature=[regex]::Match($sp2Text,'"featureId":"(F[0-9]{2})"').Groups[1].Value
 $sp2Inputs+=@{path=[IO.Path]::GetRelativePath($sp2Spec,$_.FullName).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
 foreach($sp2Item in [regex]::Matches($sp2Text,'(?m)^\| (F[0-9]{2}-I[0-9]{2}) \|')){
  $sp2Id=$sp2Item.Groups[1].Value
  $sp2Values=if($sp2Feature -eq 'F05'){
   switch($sp2Id){
    'F05-I04' {@('src/CareerManagement.Web/Controllers/EmployeesController.cs','Selected')}
    'F05-I05' {@('src/CareerManagement.Infrastructure/Sql/EmployeeService.cs','ValidateStored')}
    'F05-I18' {@('src/CareerManagement.Web/Controllers/EmployeesController.cs','filename=')}
    default {@('src/CareerManagement.Infrastructure/Reports/ReportService.cs','Create')}
   }
  }else{@($sp2Views[$sp2Feature],$sp2Id)}
  $sp2Items+=@{itemId=$sp2Id;implementation=@(Sp2-Refs $sp2Values);verification='static mapping; runtime evidence is recorded separately'}
 }
 foreach($sp2Event in [regex]::Matches($sp2Text,'(?m)^### (F[0-9]{2}-E[0-9]{2}) (.+)')){
  $sp2Id=$sp2Event.Groups[1].Value
  $sp2EventRows+=@{eventId=$sp2Id;name=$sp2Event.Groups[2].Value.Trim();implementation=@(Sp2-Refs $sp2Events[$sp2Id])}
 }
}
if($sp2Items.Count -ne 83 -or $sp2EventRows.Count -ne 17){throw 'Item/event count mismatch.'}
$sp2Checks=@(
 @{id='CHK-C01';symbols=@('AuthService.AuthenticateAsync','CurrentUserService.RequireInAsync','SessionRegistry.IsValid')},
 @{id='CHK-C02';symbols=@('ScreenStateStore.Check','ScreenState.Gate','DraftInput','ExportOperationRegistry')},
 @{id='CHK-C03';symbols=@('Validation.Text','Validation.ScalarLength','HttpJson.Shape')},
 @{id='CHK-C04';symbols=@('Validation.Text','Validation.SearchKey','ReportText.SetExact')},
 @{id='CHK-C05';symbols=@('Validation.Employee','Validation.Career','Validation.Field')},
 @{id='CHK-C06';symbols=@('Validation.Career','Validation.Careers','CareerValues')},
 @{id='CHK-C07';symbols=@('Validation.Reference','Validation.FixedCodes','Repository.ValidateCategoriesAsync')},
 @{id='CHK-C08';symbols=@('Validation.Reference','EmployeeService.SaveAsync','CodeService.SaveAsync')},
 @{id='CHK-C09';symbols=@('Validation.ChildSet','Repository.EmployeeIdAsync','EmployeeService.ValidateStructure')},
 @{id='CHK-C10';symbols=@('EmployeeService.SaveAsync','Repository.SearchAsync','CodeService.SaveAsync')},
 @{id='CHK-C11';symbols=@('EmployeeService.SaveAsync','CodeService.SaveAsync')},
 @{id='CHK-C12';symbols=@('Database.BeginAsync','DbUnit.CommitAsync','DbUnit.DisposeAsync','EmployeeService.ReportAsync')}
)
$sp2PilotTests=@{
1=@('AUTH-01');2=@('AUTH-02');3=@('AUTH-03');4=@('AUTH-03');5=@('F06-01','SEC-01');6=@();7=@('STATE-01');8=@('F03-01','F03-02');9=@('F03-02','F03-04');10=@('F04-17');11=@('HTTP-12-old-result-disabled');12=@('F04-06','F05-01');13=@('TEXT-01','TEXT-02');14=@();15=@();16=@('HTTP-08-escaped-maximum20-save');17=@('F04-08','F04-09');18=@();19=@('F04-10');20=@('IR-S03-retained-and-removed','IR-S04-duplicate-retained','IR-S05-unknown-retained');21=@('F04-04');22=@('F04-16');23=@();24=@('F04-03');25=@('F04-02');26=@('F04-01');27=@('F04-17');28=@('F04-13');29=@('F04-11');30=@('F04-14');31=@('F04-11','F04-12');32=@();33=@('F06-03','F06-04');34=@();35=@();36=@();37=@('F04-08','HTTP-11-maximum20-response-xlsx');38=@();39=@();40=@('Cancel/Finish independent interleaving','root browser export');41=@()
}
$sp2Pilots=@(1..41 | ForEach-Object {@{pilotId=('PILOT-P{0:00}' -f $_);relatedTests=@($sp2PilotTests[$_]);status= $(if($sp2PilotTests[$_].Count){'partial-or-covered-at-recorded-layer'}else{'not-executed-as-full-pilot-scenario'});note='Mapping is not a formal Pilot PASS. Read exact assertions, result scope and independent browser evidence.'}})
($sp2Pilots | Where-Object pilotId -EQ 'PILOT-P20').note='Independent Application tests cover overlapping retained/removed sets, duplicate retained IDs and unknown retained IDs. Real DB/HTTP cross-employee ownership fixture is not executed as the full P20 scenario.'
($sp2Pilots | Where-Object pilotId -EQ 'PILOT-P35').note='Reference-loss, stored 11-value duplicate and foreign-employee read-contamination fixtures are unexecuted. F04-15 invalid-name correction/report refusal is a separate scenario and does not substitute for P35.'
$sp2OpenBoundaries=@(@{id='PH05';reportId='PH-05';status='OPEN';evidenceStatus='REQUIRES_DETAIL_DESIGN_FIX';relatedEvents=@('F03-E03','F04-E04');relatedItems=@('F03-I01','F03-I02','F03-I03','F03-I04','F04-I29');scenario='Unsearched raw criteria edited -> New -> Cancel without employee edits';expectedRaw='777777';actualRaw='';databaseWrites=0;evidence='build/test-results/design-boundary.json';test='tests/Web/design-boundary.cjs';note='Unapplied raw criteria retention fails. StateCommand/OpenInput do not carry those values. Not a PASS. The specified save return using AppliedCriteria is unaffected.'})
foreach($sp2EventRow in $sp2EventRows){if($sp2EventRow.eventId -in @('F03-E03','F04-E04')){$sp2EventRow.openDesignBoundaries=@('PH05');$sp2EventRow.verificationNote='PH05 unapplied-raw New/Cancel boundary is OPEN and excluded from successful functional/browser coverage.'}}
$sp2Record=@{projectId='sample-project2';methodId='CSharp_ASPNET';stage='build';runId='20261029-sp2-build';inputManifestSha256=(Get-FileHash -LiteralPath (Join-Path $sp2Root 'build/generation/inputs.json') -Algorithm SHA256).Hash.ToLowerInvariant();detailInputs=$sp2Inputs;items=$sp2Items;events=$sp2EventRows;commonChecks=$sp2Checks;pilots=$sp2Pilots;formalScore=$null;acceptance='not-performed';evidence=@('build/test-results/self-cycle-1.json','build/test-results/self-cycle-2.json','build/test-results/self-cycle-3.json','build/test-results/http-contract.json','build/test-results/independent-review/application.json','build/test-results/independent-review/infrastructure.json','build/test-results/independent-browser/review.json')}
$sp2Record.openDesignBoundaries=$sp2OpenBoundaries
$sp2Record.evidence+=@('build/test-results/design-boundary.json')
$sp2Record.finalInputRefresh='../../build/final-input-refresh.json'
$sp2Record.cycleEvidencePolicy='Current input metadata may differ from execution-time inputs. Retain each original cycle input SHA; do not convert PH05 or unexecuted Pilot conditions into PASS.'
$sp2Record.reportSourceSha256=(Get-FileHash -LiteralPath (Join-Path $sp2Root 'src/CareerManagement.Infrastructure/Reports/ReportService.cs') -Algorithm SHA256).Hash.ToLowerInvariant()
$sp2Record.evidence+=@('build/test-results/report-format-generation.json','build/test-results/report-format-geometry.json')
$sp2PrintPath=Join-Path $sp2Root 'build/test-results/print-review/record.json'
if(Test-Path -LiteralPath $sp2PrintPath){
 $sp2Print=Get-Content -LiteralPath $sp2PrintPath -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable
 if($sp2Print.status -eq 'PASS' -and $sp2Print.sourceSnapshot['src/CareerManagement.Infrastructure/Reports/ReportService.cs'] -eq $sp2Record.reportSourceSha256){
  $sp2Record.printReview=@{file='build/test-results/print-review/record.json';sha256=(Get-FileHash -LiteralPath $sp2PrintPath -Algorithm SHA256).Hash.ToLowerInvariant();status='PASS';reportSourceSha256=$sp2Record.reportSourceSha256}
  $sp2Record.evidence+=@('build/test-results/print-review/record.json')
 }
}
$sp2Record | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath (Join-Path $sp2Root 'build/generation/spec-implementation-map.json') -Encoding UTF8
Write-Output 'Mapped 83 items, 17 events, 12 common checks and 41 Pilot scenarios; no formal Pilot status inferred.'
