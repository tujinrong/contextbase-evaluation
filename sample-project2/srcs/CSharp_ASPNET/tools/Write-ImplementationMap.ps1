$ErrorActionPreference='Stop'
$sp2Root=Split-Path -Parent $PSScriptRoot
$sp2Spec=[IO.Path]::GetFullPath((Join-Path $sp2Root '../../spec/CSharp_ASPNET'))
$sp2Views=@{'F01'='src/CareerManagement.Web/Views/Account/Login.cshtml';'F02'='src/CareerManagement.Web/Views/Menu/Index.cshtml';'F03'='src/CareerManagement.Web/Views/Employees/Index.cshtml';'F04'='src/CareerManagement.Web/Views/Employees/Edit.cshtml';'F06'='src/CareerManagement.Web/Views/Codes/Index.cshtml'}
$sp2Events=@{
 'F01-E01'=@('src/CareerManagement.Web/Controllers/AccountController.cs','Login','src/CareerManagement.Infrastructure/Authentication/AuthService.cs','AuthenticateAsync');'F01-E02'=@('src/CareerManagement.Web/Controllers/AccountController.cs','Exit')
 'F02-E01'=@('src/CareerManagement.Web/Controllers/UiController.cs','Navigate','src/CareerManagement.Web/Views/Shared/_Layout.cshtml','F02-I02');'F02-E02'=@('src/CareerManagement.Web/Controllers/UiController.cs','Logout')
 'F03-E01'=@('src/CareerManagement.Web/Controllers/EmployeesController.cs','Search','src/CareerManagement.Infrastructure/Sql/Repository.cs','SearchAsync');'F03-E02'=@('src/CareerManagement.Web/Controllers/EmployeesController.cs','Invalidate','src/CareerManagement.Web/wwwroot/js/site.js','invalidate');'F03-E03'=@('src/CareerManagement.Web/Controllers/EmployeesController.cs','Open','src/CareerManagement.Web/Views/Shared/_Layout.cshtml','F03-I13')
 'F04-E01'=@('src/CareerManagement.Web/Controllers/EmployeesController.cs','Edit','src/CareerManagement.Infrastructure/Sql/EmployeeService.cs','ReadAsync');'F04-E02'=@('src/CareerManagement.Web/Controllers/EmployeesController.cs','Draft');'F04-E03'=@('src/CareerManagement.Web/Controllers/EmployeesController.cs','Save','src/CareerManagement.Infrastructure/Sql/EmployeeService.cs','SaveAsync');'F04-E04'=@('src/CareerManagement.Web/Controllers/EmployeesController.cs','Cancel')
 'F05-E01'=@('src/CareerManagement.Infrastructure/Sql/EmployeeService.cs','ReportAsync');'F05-E02'=@('src/CareerManagement.Infrastructure/Reports/ReportService.cs','Create','src/CareerManagement.Web/Controllers/EmployeesController.cs','Export');'F05-E03'=@('src/CareerManagement.Infrastructure/State/StateStore.cs','ExportOperationRegistry','src/CareerManagement.Web/Controllers/EmployeesController.cs','ExportCancel')
 'F06-E01'=@('src/CareerManagement.Web/Controllers/CodesController.cs','Open');'F06-E02'=@('src/CareerManagement.Web/Controllers/CodesController.cs','Save','src/CareerManagement.Infrastructure/Sql/CodeService.cs','SaveAsync');'F06-E03'=@('src/CareerManagement.Web/Controllers/CodesController.cs','Cancel')
}
function Sp2-Refs([string[]]$Values){
 $sp2Refs=@()
 for($sp2Index=0;$sp2Index -lt $Values.Length;$sp2Index+=2){
  $sp2Path=Join-Path $sp2Root $Values[$sp2Index]
  $sp2Match=Select-String -LiteralPath $sp2Path -SimpleMatch $Values[$sp2Index+1] | Select-Object -First 1
  if(-not $sp2Match -and $Values[$sp2Index+1] -match '^F[0-9]{2}-I[0-9]{2}$'){
   $sp2Match=Get-ChildItem -LiteralPath (Join-Path $sp2Root 'src/CareerManagement.Web') -Recurse -File | Where-Object {$_.Extension -in '.cshtml','.js'} | Select-String -SimpleMatch $Values[$sp2Index+1] | Select-Object -First 1
   if($sp2Match){$sp2Path=$sp2Match.Path}
  }
  if(-not $sp2Match){throw "Missing implementation symbol $($Values[$sp2Index+1])"}
  $sp2Refs+=@{path=[IO.Path]::GetRelativePath($sp2Root,$sp2Path).Replace('\','/');symbol=$Values[$sp2Index+1];line=$sp2Match.LineNumber;sha256=(Get-FileHash -LiteralPath $sp2Path -Algorithm SHA256).Hash.ToLowerInvariant()}
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
  }else{
   $sp2View=$sp2Views[$sp2Feature]
   if(-not(Select-String -LiteralPath (Join-Path $sp2Root $sp2View) -SimpleMatch $sp2Id)){
    $sp2View='src/CareerManagement.Web/Views/Shared/_Layout.cshtml'
   }
   @($sp2View,$sp2Id)
  }
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
$sp2ContractPath=Join-Path $sp2Root 'tests/ui-contract.json'
$sp2Contract=Get-Content -LiteralPath $sp2ContractPath -Raw -Encoding UTF8|ConvertFrom-Json -AsHashtable
$sp2UiMappings=@($sp2Contract.rules|ForEach-Object {@{ruleId=$_.id;componentId=$_.target;kind=$_.kind;scenario=$_.scenario;basisIds=$_.basisIds;sourceFiles=$_.sourceFiles;implementation=@('src/CareerManagement.Web/Views/Shared/_Layout.cshtml','src/CareerManagement.Web/wwwroot/css/site.css','src/CareerManagement.Web/wwwroot/js/site.js');verification='Inspect exact rule and final-artifact observation; static mapping is not runtime PASS.'}})
$sp2Record=@{projectId='sample-project2';methodId='CSharp_ASPNET';stage='build';runId=(Get-Content -LiteralPath (Join-Path $sp2Root 'build/generation/inputs.json') -Raw|ConvertFrom-Json).runId;inputManifestSha256=(Get-FileHash -LiteralPath (Join-Path $sp2Root 'build/generation/inputs.json') -Algorithm SHA256).Hash.ToLowerInvariant();detailInputs=$sp2Inputs;items=$sp2Items;events=$sp2EventRows;commonChecks=$sp2Checks;uiContract=@{file='tests/ui-contract.json';version=$sp2Contract.version;sha256=(Get-FileHash -LiteralPath $sp2ContractPath -Algorithm SHA256).Hash.ToLowerInvariant()};uiMappings=$sp2UiMappings;pilots=@(1..41|ForEach-Object {@{pilotId=('PILOT-P{0:00}' -f $_);status='NOT_FORMALLY_EXECUTED';note='Read layer-specific tests and exact artifact hashes; partial checks are not full Pilot acceptance.'}});formalScore=$null;acceptance='not-performed';evidence=@('build/test-results/self-cycle-1.json','build/test-results/self-cycle-2.json','build/test-results/self-cycle-3.json','build/test-results/ui-state-unit.json','build/test-results/ui-regeneration/history/result.json','build/test-results/ui-regeneration/functional/result.json','build/test-results/ui-regeneration/boundaries/result.json','build/test-results/ui-observations.json','build/test-results/ui-conformance.json','build/test-results/quality-cycles.json','build/test-results/final-verification.json')}
$sp2Record.designBoundaries=@(@{id='PH05';status='RESOLVED_AT_TESTED_BROWSER_SCOPE';source='Current basic/detail SearchRaw/OpenInput/SearchReturnCoordinator contract';evidence='build/test-results/ui-regeneration/history/result.json';unexecuted='Full formal Pilot/native environment acceptance is separate.'})
$sp2Record.cycleEvidencePolicy='Each original cycle/artifact/input SHA is retained; old-candidate evidence is not reassigned to the final candidate.'
$sp2Record.reportSourceSha256=(Get-FileHash -LiteralPath (Join-Path $sp2Root 'src/CareerManagement.Infrastructure/Reports/ReportService.cs') -Algorithm SHA256).Hash.ToLowerInvariant()
$sp2Record|ConvertTo-Json -Depth 20|Set-Content -LiteralPath (Join-Path $sp2Root 'build/generation/spec-implementation-map.json') -Encoding UTF8
Write-Output 'Mapped 83 items, 17 events, 12 common checks and UI rules; no formal Pilot status inferred.'
