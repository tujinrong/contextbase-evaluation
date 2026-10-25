param(
    [string]$Frontend = '',
    [string]$Backend = '',
    [switch]$CreateBackend = $true,
    [switch]$Compile = $true,
    [switch]$NoStartup,
    [switch]$IncludeTests,
    [switch]$SingleFile = $true,
    [ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId = 'manual',
    [string]$InitialUser = ([Security.Principal.WindowsIdentity]::GetCurrent().Name.Split('\')[-1]),
    [ValidateSet('Reader','Staff','Admin')][string]$InitialRole = 'Admin'
)
$ErrorActionPreference = 'Stop'
# Generation history is managed by Git. Only the completed single-file result is published.
. (Join-Path $PSScriptRoot 'tools/GeneratedPaths.ps1')
if (-not $Frontend) { $Frontend=Join-Path $script:AccessMethodRoot 'build/StudentManagement.accdb' }
if (-not $Backend) { $Backend=Join-Path $script:AccessMethodRoot '.tmp/generation/backend.accdb' }
$taskRequestedFrontend = [IO.Path]::GetFullPath($Frontend)
$taskFinalPath = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'build/StudentManagement.accdb'))
if ($taskRequestedFrontend -eq $taskFinalPath) {
    $taskRequestedFrontend = Resolve-AccessGeneratedPath $taskRequestedFrontend 'build'
    if ($IncludeTests) { throw 'Test modules belong in a disposable Access/.tmp fixture.' }
} else {
    $taskRequestedFrontend = Resolve-AccessGeneratedPath $taskRequestedFrontend '.tmp'
}
$Backend = Resolve-AccessGeneratedPath $Backend '.tmp'
$Frontend = Resolve-AccessGeneratedPath (Join-Path $PSScriptRoot '.tmp/generation/frontend.accdb') '.tmp'
if ($taskRequestedFrontend -eq $Frontend -or $Frontend -eq $Backend -or $taskRequestedFrontend -eq $Backend) { throw 'Output and staging paths must be distinct.' }
if (-not $SingleFile) { throw 'The final output must remain one standalone ACCDB.' }
foreach ($taskPath in @($Frontend, $Backend)) {
    if ([IO.Path]::GetExtension($taskPath) -ne '.accdb') { throw 'ACCDB output required.' }
}
if ([IO.Path]::GetExtension($taskRequestedFrontend) -ne '.accdb') { throw 'ACCDB output required.' }
foreach ($taskDirectory in @([IO.Path]::GetDirectoryName($Frontend),[IO.Path]::GetDirectoryName($Backend),[IO.Path]::GetDirectoryName($taskRequestedFrontend))) { New-Item -ItemType Directory -Path $taskDirectory -Force | Out-Null }
Remove-AccessIntermediate $Frontend
if ($CreateBackend) { Remove-AccessIntermediate $Backend }
if ($SingleFile -and -not $CreateBackend) { throw 'SingleFile requires a freshly generated staging backend.' }
$taskGenerated = $false
$taskAccess = New-Object -ComObject Access.Application
$taskAccess.Visible = $false
function Set-DaoProperty($object, [string]$name, [int]$type, $value) {
    try { $taskProperty=$object.Properties.Item($name); $taskProperty.Value = $value }
    catch {
        $taskOriginalPropertyError=$_.Exception.Message
        try { $object.Properties.Append($object.CreateProperty($name, $type, $value)) }
        catch { throw "DAO property $name on $($object.Name): $taskOriginalPropertyError / $($_.Exception.Message)" }
    }
}
function Sql-Literal($value) {
    if ($null -eq $value) { return 'NULL' }
    if ($value -is [bool]) { if ($value) { return 'True' } else { return 'False' } }
    if ($value -is [DateTime]) { return '#' + $value.ToString('yyyy-MM-dd HH:mm:ss',[Globalization.CultureInfo]::InvariantCulture) + '#' }
    if ($value -is [int] -or $value -is [long]) { return $value.ToString([Globalization.CultureInfo]::InvariantCulture) }
    return "'" + ([string]$value).Replace("'", "''") + "'"
}
function Insert-SeedRow([string]$table, $pairs) {
    $taskColumns=@(); $taskValues=@()
    foreach ($taskPair in $pairs) { $taskColumns += $taskPair[0]; $taskValues += Sql-Literal $taskPair[1] }
    $taskDb.Execute("INSERT INTO $table ($($taskColumns -join ',')) VALUES ($($taskValues -join ','))",128)
}
function Add-Control($form, [string]$name, [int]$kind, [int]$left, [int]$top, [string]$label, [int]$width = 2500) {
    $taskControl = $taskAccess.CreateControl($form.Name, $kind, 0, '', '', $left, $top, $width, 360)
    $taskControl.Name = $name
    if($kind -ne 106){$taskControl.FontName = "Yu Gothic UI"; $taskControl.FontSize = 9}
    if ($kind -in @(100,104)) { $taskControl.Caption = $label }
    elseif ($label) {
        $taskLabel = $taskAccess.CreateControl($form.Name, 100, 0, $name, '', $left, $top - 300, $width, 270)
        $taskLabel.Caption = $label
        $taskLabel.FontName="Yu Gothic UI"; $taskLabel.FontSize=9
    }
    return $taskControl
}
function Add-Text($form, [string]$name, [int]$left, [int]$top, [string]$label) { Add-Control $form $name 109 $left $top $label }
function Add-Combo($form, [string]$name, [int]$left, [int]$top, [string]$label, [string]$sql) {
    $taskCombo = Add-Control $form $name 111 $left $top $label
    $taskCombo.RowSource = $sql; $taskCombo.ColumnCount = 2; $taskCombo.ColumnWidths = '0cm;4cm'; $taskCombo.BoundColumn = 1; $taskCombo.LimitToList = $true
    return $taskCombo
}
function Add-Button($form, [string]$name, [int]$left, [int]$top, [string]$label, [string]$action) {
    $taskButton = Add-Control $form $name 104 $left $top $label 1500
    $taskButton.Height = 390
    $taskButton.OnClick = "=$action"
    return $taskButton
}
function Add-RowLabel($form,[string]$name,[int]$left,[int]$top,[string]$caption,[int]$width=1800) {
    $taskLabel=Add-Control $form ('lbl'+$name) 100 $left ($top+30) $caption $width
    $taskLabel.Height=300
    return $taskLabel
}
function Add-Group($form,[string]$name,[int]$left,[int]$top,[int]$width,[int]$height,[string]$caption) {
    $taskGroup=$taskAccess.CreateControl($form.Name,107,0,'','',$left,$top,$width,$height)
    $taskGroup.Name=$name;$taskGroup.BorderStyle=1;$taskGroup.BackStyle=0
    $taskLabel=Add-Control $form ('lbl'+$name) 100 ($left+120) ($top-30) $caption 3300
    $taskLabel.Height=270;$taskLabel.BackStyle=1;$taskLabel.BackColor=15790320
}
function Save-Form($form, [string]$name) {
    $taskOldName = $form.Name
    $taskAccess.DoCmd.Save(2, $taskOldName); $taskAccess.DoCmd.Close(2, $taskOldName, 1)
    if ($taskOldName -ne $name) { $taskAccess.DoCmd.Rename($name, 2, $taskOldName) }
}
function Compile-Vba {
    $taskCompiler=$taskAccess.VBE.CommandBars.FindControl(1,578)
    if($null -eq $taskCompiler){throw 'Native VBE compiler command unavailable.'}
    if($taskCompiler.Enabled){
        try{$taskCompiler.Execute()}catch{if($taskCompiler.Enabled){throw}}
    }
    if($taskCompiler.Enabled){throw 'Native VBE compilation failed; compiler remains enabled.'}
    Write-Output 'Native VBE compiler completed (command 578 disabled).'
}
function Create-NamedForm([string]$name) {
    $taskAccess.DoCmd.OpenForm($name,1)
    return ,$taskAccess.Forms.Item($name)
}
try {
    if ($CreateBackend) {
        $taskAccess.NewCurrentDatabase([IO.Path]::GetFullPath($Backend), 12)
        $taskDb = $taskAccess.CurrentDb()
        $taskDdl = (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'database/schema.sql') -Encoding UTF8 -Raw) -replace '(?m)^--.*$', ''
        foreach ($taskStatement in $taskDdl.Split(';')) {
            if ($taskStatement.Trim() -and $taskStatement.Trim() -notmatch '^ALTER TABLE .* FOREIGN KEY') {
                $taskDb.Execute(($taskStatement.Trim() -replace ' DEFAULT (True|False|\d+)',''), 128)
            }
        }
        $taskSchema = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'database/schema.json') -Encoding UTF8 -Raw | ConvertFrom-Json
        foreach ($taskTable in $taskSchema) {
            foreach ($taskColumn in $taskTable.columns) {
                $taskField = $taskDb.TableDefs.Item($taskTable.name).Fields.Item($taskColumn.name)
                if ($taskColumn.type -match '^(TEXT|LONGTEXT)') { $taskField.AllowZeroLength = $false }
                if ($taskColumn.default -match '^(True|False|[0-9]+)$') { $taskField.DefaultValue = [string]$taskColumn.default }
                if ($taskColumn.name -eq 'row_version') { $taskField.ValidationRule = '>0' }
            }
        }
        $taskValidationTable=$taskDb.TableDefs.Item('m_class'); $taskValidationTable.ValidationRule='[school_year]>=1900 And [school_year]<=9998 And ([capacity] Is Null Or ([capacity]>=1 And [capacity]<=9999)) And [display_order]>=0 And [grade_category]="GRADE" And [valid_from]<=[valid_to] And [valid_from]>=CStr([school_year]) & "-04-01" And [valid_to]<=CStr([school_year]+1) & "-03-31"'
        $taskValidationTable=$taskDb.TableDefs.Item('m_code_category'); $taskValidationTable.ValidationRule='[code_length]>=1 And [code_length]<=10'
        $taskValidationTable=$taskDb.TableDefs.Item('m_code'); $taskValidationTable.ValidationRule='[display_order]>=0 And ([valid_to] Is Null Or [valid_from]<=[valid_to]) And [code_value] Not Like "*[!0-9]*"'
        $taskValidationTable=$taskDb.TableDefs.Item('t_operation_log'); $taskValidationTable.ValidationRule='[after_version]>0 And ([before_version] Is Null Or [before_version]>0) And [operation_type] In ("CREATE","UPDATE","DELETE","DISABLE","ENABLE")'
        $taskValidationTable=$taskDb.TableDefs.Item('m_student'); $taskValidationTable.ValidationRule='[gender_category]="GENDER" And [prefecture_category]="PREFECTURE" And [enrollment_category]="ENROLLMENT_STATUS" And [birth_date]>="1900-01-01" And [birth_date]<=[admission_date] And (([enrollment_status_code] In ("01","02") And [class_id] Is Not Null And [enrollment_end_date] Is Null) Or ([enrollment_status_code] In ("03","04") And [enrollment_end_date] Is Not Null And [admission_date]<=[enrollment_end_date])) And ([phone_number] Is Not Null Or [email_address] Is Not Null Or [emergency_phone_number] Is Not Null) And (([emergency_contact_name] Is Null And [relationship_category] Is Null And [relationship_code] Is Null And [emergency_phone_number] Is Null) Or ([emergency_contact_name] Is Not Null And [relationship_category] Is Not Null And [relationship_category]="RELATIONSHIP" And [relationship_code] Is Not Null And [emergency_phone_number] Is Not Null)) And (([is_deleted]=False And [deleted_at] Is Null And [deleted_by] Is Null And [delete_reason] Is Null) Or ([is_deleted]=True And [deleted_at] Is Not Null And [deleted_by] Is Not Null And [delete_reason] Is Not Null))'
        foreach ($taskColumnName in @('relationship_category','relationship_code')) {
            $taskField=$taskDb.TableDefs.Item('m_student').Fields.Item($taskColumnName)
            $taskField.Required=$false; $taskField.AllowZeroLength=$false; $taskField.DefaultValue=''
        }
        $taskValidationTable=$taskDb.TableDefs.Item('t_write_guard'); $taskValidationTable.ValidationRule='[guard_id]=1'
        $taskRelations=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'database/relations.json') -Encoding UTF8 -Raw | ConvertFrom-Json
        foreach ($taskRelationSpec in $taskRelations) {
            $taskRelation=$taskDb.CreateRelation($taskRelationSpec.name,$taskRelationSpec.parent,$taskRelationSpec.child,0)
            for ($taskRelationColumn=0; $taskRelationColumn -lt $taskRelationSpec.parent_columns.Count; $taskRelationColumn++) {
                $taskRelationField=$taskRelation.CreateField($taskRelationSpec.parent_columns[$taskRelationColumn])
                $taskRelationField.ForeignName=$taskRelationSpec.child_columns[$taskRelationColumn]
                $taskRelation.Fields.Append($taskRelationField)
            }
            $taskDb.Relations.Append($taskRelation)
        }
        $taskSeed = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'database/seed.json') -Encoding UTF8 -Raw | ConvertFrom-Json
        $taskAt = [DateTime]::UtcNow
        foreach ($taskCategory in $taskSeed.categories) {
            Insert-SeedRow 'm_code_category' @(@('category_id',$taskCategory.id),@('category_name',$taskCategory.name),@('code_length',$taskCategory.length),@('allow_add',$taskCategory.allow_add),@('is_active',$true),@('row_version',1),@('created_at',$taskAt),@('updated_at',$taskAt),@('created_by','bootstrap'),@('updated_by','bootstrap'))
        }
        foreach ($taskCode in $taskSeed.codes) {
            Insert-SeedRow 'm_code' @(@('category_id',$taskCode.category),@('code_value',$taskCode.value),@('code_name',$taskCode.name),@('display_order',$taskCode.order),@('is_active',$true),@('valid_from','1900-01-01'),@('is_protected',$taskCode.protected),@('row_version',1),@('created_at',$taskAt),@('updated_at',$taskAt),@('created_by','bootstrap'),@('updated_by','bootstrap'))
        }
        $taskDb.Close(); $taskAccess.CloseCurrentDatabase()
    }
    $taskAccess.NewCurrentDatabase([IO.Path]::GetFullPath($Frontend), 12)
    $taskBlankForm=$taskAccess.CreateForm()
    Save-Form $taskBlankForm 'frmStudentSearch'
    $taskBlankForm=$null
    $taskAccess.DoCmd.CopyObject('', 'frmStudentEdit', 2, 'frmStudentSearch')
    $taskAccess.DoCmd.CopyObject('', 'frmDuplicateConfirm', 2, 'frmStudentSearch')
    $taskAccess.DoCmd.CopyObject('', 'frmDeleteConfirm', 2, 'frmStudentSearch')
    $taskAccess.DoCmd.CopyObject('', 'frmDiscardConfirm', 2, 'frmStudentSearch')
    $taskDb = $taskAccess.CurrentDb()
    Set-DaoProperty $taskDb 'StudentTestFixture' 1 ([bool]$IncludeTests)
    Set-DaoProperty $taskDb 'StudentBackendPath' 10 $(if ($SingleFile) { 'SELF' } else { [IO.Path]::GetFullPath($Backend) })
    if (Test-Path -LiteralPath $Backend) {
        $taskSchema = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'database/schema.json') -Encoding UTF8 -Raw | ConvertFrom-Json
        foreach ($taskTable in $taskSchema) {
            if ($SingleFile) {
                $taskAccess.DoCmd.TransferDatabase(0,'Microsoft Access',[IO.Path]::GetFullPath($Backend),0,$taskTable.name,$taskTable.name,$false)
            } else {
                $taskLink=$taskDb.CreateTableDef($taskTable.name); $taskLink.Connect=";DATABASE=$([IO.Path]::GetFullPath($Backend))"; $taskLink.SourceTableName=$taskTable.name; $taskDb.TableDefs.Append($taskLink)
            }
        }
        if ($SingleFile) {
            $taskDb=$taskAccess.CurrentDb()
            $taskRelations=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'database/relations.json') -Encoding UTF8 -Raw | ConvertFrom-Json
            foreach ($taskRelationSpec in $taskRelations) {
                $taskExisting=$null
                try { $taskExisting=$taskDb.Relations.Item($taskRelationSpec.name) } catch { }
                if ($null -ne $taskExisting) { continue }
                $taskRelation=$taskDb.CreateRelation($taskRelationSpec.name,$taskRelationSpec.parent,$taskRelationSpec.child,0)
                for ($taskRelationColumn=0; $taskRelationColumn -lt $taskRelationSpec.parent_columns.Count; $taskRelationColumn++) {
                    $taskRelationField=$taskRelation.CreateField($taskRelationSpec.parent_columns[$taskRelationColumn])
                    $taskRelationField.ForeignName=$taskRelationSpec.child_columns[$taskRelationColumn]; $taskRelation.Fields.Append($taskRelationField)
                }
                $taskDb.Relations.Append($taskRelation)
            }
            $taskDb.Execute('CREATE TABLE t_app_role(user_id TEXT(128) CONSTRAINT pk_app_role PRIMARY KEY,role_name TEXT(10) NOT NULL)',128)
            $taskRoleTable=$taskDb.TableDefs.Item('t_app_role'); $taskRoleTable.ValidationRule='[role_name] In ("Reader","Staff","Admin")'
            $taskField=$taskRoleTable.Fields.Item('user_id'); $taskField.AllowZeroLength=$false
            $taskField=$taskRoleTable.Fields.Item('role_name'); $taskField.AllowZeroLength=$false
            $taskDb.Execute("INSERT INTO t_app_role(user_id,role_name) VALUES($(Sql-Literal $InitialUser),$(Sql-Literal $InitialRole))",128)
        }
    }
    foreach ($taskSource in Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'Modules') -Filter '*.bas') {
        if ($taskSource.BaseName -eq 'modSelfTests' -and -not $IncludeTests) { continue }
        $taskCode=Get-Content -LiteralPath $taskSource.FullName -Encoding UTF8 -Raw
        $taskComponent=$taskAccess.VBE.ActiveVBProject.VBComponents.Add(1); $taskComponent.Name=$taskSource.BaseName
        if ($taskComponent.CodeModule.CountOfLines -gt 0) { $taskComponent.CodeModule.DeleteLines(1,$taskComponent.CodeModule.CountOfLines) }
        $taskComponent.CodeModule.AddFromString(($taskCode -replace '(?m)^Attribute VB_Name.*\r?\n',''))
        $taskAccess.DoCmd.Save(5,$taskSource.BaseName)
    }
    foreach ($taskSource in Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'Classes') -Filter '*.cls') {
        $taskCode=Get-Content -LiteralPath $taskSource.FullName -Encoding UTF8 -Raw
        $taskCode=$taskCode.Substring($taskCode.IndexOf('Option Explicit'))
        $taskComponent=$taskAccess.VBE.ActiveVBProject.VBComponents.Add(2); $taskComponent.Name=$taskSource.BaseName
        if ($taskComponent.CodeModule.CountOfLines -gt 0) { $taskComponent.CodeModule.DeleteLines(1,$taskComponent.CodeModule.CountOfLines) }
        $taskComponent.CodeModule.AddFromString($taskCode)
        $taskAccess.DoCmd.Save(5,$taskSource.BaseName)
    }
    if ($Compile) { Compile-Vba }
    $taskCodeSql=@{}
    foreach ($taskCategory in @('GENDER','PREFECTURE','ENROLLMENT_STATUS','RELATIONSHIP','GRADE')) { $taskCodeSql[$taskCategory]="SELECT code_value,code_name FROM m_code WHERE category_id='$taskCategory' ORDER BY display_order,code_value" }
    $taskClassSql='SELECT class_id, CStr(school_year) & " " & class_code & " " & class_name & IIf(is_active,""," [停止]") FROM m_class ORDER BY school_year,display_order,class_code,class_id'
    $taskYearSql='SELECT DISTINCT school_year,school_year FROM m_class ORDER BY school_year DESC'
    $taskForm=Create-NamedForm 'frmStudentSearch';$taskForm.RecordSource='';$taskForm.DefaultView=0;$taskForm.Width=18240;$taskForm.Section(0).Height=8640;$taskForm.Section(0).BackColor=15790320;$taskForm.Caption='学生検索';$taskForm.OnLoad='[Event Procedure]';$taskForm.ScrollBars=3;$taskForm.AutoCenter=$true
    $taskCtl=Add-Control $taskForm 'lblTitle' 100 180 60 '学生検索 ／ 4条件・全件一覧' 17880;$taskCtl.Height=300
    $taskCtl=Add-Control $taskForm 'lblMessage' 100 180 390 '' 17880;$taskCtl.Height=300
    $null=Add-RowLabel $taskForm 'StudentNo' 180 810 '学籍番号' 1200
    $taskCtl=Add-Text $taskForm 'txtStudentNo' 1470 810 '';$taskCtl.Width=2040;$taskCtl.AfterUpdate='=ClassChanged()'
    $null=Add-RowLabel $taskForm 'Name' 3780 810 '氏名' 900
    $taskCtl=Add-Text $taskForm 'txtName' 4770 810 '';$taskCtl.Width=1800;$taskCtl.AfterUpdate='=ClassChanged()'
    $null=Add-RowLabel $taskForm 'Class' 6840 810 'クラス' 900
    $taskCtl=Add-Combo $taskForm 'cboClass' 7830 810 '' $taskClassSql;$taskCtl.Width=6600;$taskCtl.ColumnWidths='0cm;17cm';$taskCtl.ListWidth=11000;$taskCtl.AfterUpdate='=ClassChanged()'
    $null=Add-RowLabel $taskForm 'Statuses' 180 1230 '在籍区分' 1200
    foreach($taskItem in @(@('chkEnrolled','在学'),@('chkLeave','休学'),@('chkGraduated','卒業'),@('chkWithdrawn','退学'))){
        $taskIndex=[Array]::IndexOf(@('chkEnrolled','chkLeave','chkGraduated','chkWithdrawn'),$taskItem[0]);$taskLeft=1470+$taskIndex*1530
        $taskCtl=Add-Control $taskForm $taskItem[0] 106 $taskLeft 1290 '' 210;$taskCtl.Height=210;$taskCtl.AfterUpdate='=ClassChanged()'
        $null=Add-RowLabel $taskForm $taskItem[0] ($taskLeft+330) 1230 $taskItem[1] 1050
    }
    $null=Add-Button $taskForm 'cmdSearch' 180 1650 '検索' 'SearchClick("SEARCH")';$null=Add-Button $taskForm 'cmdClear' 1860 1650 'クリア' 'ClearSearch()'
    $null=Add-Button $taskForm 'cmdNew' 14700 1650 '新規登録' 'OpenStudent(True)';$null=Add-Button $taskForm 'cmdMenu' 16380 1650 'メニューへ' 'SearchMenu()'
    $taskCtl=Add-Control $taskForm 'lblCount' 100 180 2145 '未検索' 7200;$taskCtl.Height=300
    $null=Add-RowLabel $taskForm 'SortKey' 9690 2100 '並び順' 1050
    $taskCtl=Add-Combo $taskForm 'cboSortKey' 10830 2100 '' 'studentNo;学籍番号;name;氏名;admissionDate;入学日;updatedAt;更新日時';$taskCtl.RowSourceType='Value List';$taskCtl.Width=3300;$taskCtl.AfterUpdate='=SearchClick("SORT")'
    $taskCtl=Add-Combo $taskForm 'cboSortDirection' 14400 2100 '' 'asc;昇順;desc;降順';$taskCtl.RowSourceType='Value List';$taskCtl.Width=3480;$taskCtl.AfterUpdate='=SearchClick("SORT")'
    $taskColumnWidths=@(2040,5100,2280,2460,3660,1080,1200);$taskHeaders=@('学籍番号','氏名 ／ カナ','生年月日','年度／学年','クラス','在籍','操作案内');$taskLeft=180
    for($taskIndex=0;$taskIndex -lt $taskHeaders.Count;$taskIndex++){$taskCtl=Add-Control $taskForm ('lblColumn'+$taskIndex) 100 $taskLeft 2520 $taskHeaders[$taskIndex] $taskColumnWidths[$taskIndex];$taskCtl.Height=270;$taskLeft+=$taskColumnWidths[$taskIndex]}
    $taskList=Add-Control $taskForm 'lstStudents' 110 180 2910 '' 17880;$taskList.Height=4020;$taskList.ColumnCount=8
    $taskList.ColumnWidths='0;2040;5100;2280;2460;3660;1080;1200'
    $taskList.BoundColumn=1;$taskList.RowSourceType='StudentListCallback';$taskList.OnDblClick='=OpenStudent(False)';$taskList.AfterUpdate='=SelectedStudentDetails()'
    $taskCtl=Add-Control $taskForm 'lblSelectedDetails' 100 180 6990 '選択行全文（長い値は Shift+F2 で拡大）' 17880;$taskCtl.Height=270
    $taskDetails=Add-Text $taskForm 'txtSelectedDetails' 180 7260 '';$taskDetails.Width=17880;$taskDetails.Height=510;$taskDetails.Locked=$true;$taskDetails.TabStop=$true;$taskDetails.ScrollBars=2;$taskDetails.TextFormat=0
    foreach($taskHidden in @('IsBusy','txtContextId','txtContextRevision')){$taskCtl=Add-Text $taskForm $taskHidden 100 100 '';$taskCtl.Visible=$false}
    $taskCtl=Add-Button $taskForm 'cmdOpenSelected' 180 7890 '選択行の編集／参照' 'OpenStudent(False)';$taskCtl.Width=3300
    $taskCtl=Add-Control $taskForm 'lblSearchedAt' 100 180 8340 '' 17880;$taskCtl.Height=240
    $taskForm.HasModule=$true;$taskFormModule=$taskForm.Module
    if($taskFormModule.CountOfLines -gt 0){$taskFormModule.DeleteLines(1,$taskFormModule.CountOfLines)}
    $taskForm.OnUnload='[Event Procedure]'
    $taskFormModule.AddFromString("Option Explicit`r`nOption Compare Binary`r`nPrivate Sub Form_Load()`r`n    InitSearch Me`r`nEnd Sub`r`nPrivate Sub Form_Unload(Cancel As Integer)`r`n    CloseSearch Me`r`nEnd Sub")
    $taskForm.Section(0).Height=8640
    Save-Form $taskForm 'frmStudentSearch'
    $taskForm=Create-NamedForm 'frmStudentEdit';$taskForm.RecordSource='';$taskForm.DefaultView=0;$taskForm.Width=18240;$taskForm.Section(0).Height=8640;$taskForm.Section(0).BackColor=15790320;$taskForm.Caption='学生登録・編集';$taskForm.OnLoad='[Event Procedure]';$taskForm.OnUnload='[Event Procedure]';$taskForm.ScrollBars=3;$taskForm.AutoCenter=$true
    $taskCtl=Add-Control $taskForm 'lblTitle' 100 180 60 '学生登録・編集 ／ 必須項目は * ／ 長文は Shift+F2' 17880;$taskCtl.Height=300
    $taskCtl=Add-Control $taskForm 'lblMessage' 100 180 390 '' 17880;$taskCtl.Height=270
    Add-Group $taskForm 'grpBasic' 180 690 8775 2940 '基本情報'
    Add-Group $taskForm 'grpContact' 180 3750 8775 2940 '住所・本人連絡先'
    Add-Group $taskForm 'grpEnrollment' 9225 690 8775 3240 '在籍・所属'
    Add-Group $taskForm 'grpEmergency' 9225 4050 8775 1680 '緊急連絡先'
    Add-Group $taskForm 'grpRemarks' 9225 5850 8775 1890 '備考・確認変更理由'
    $taskTextRows=@(
        @('txtStudentId','学生管理番号',270,2190,1020,1440),@('txtStudentNo','学籍番号 *',270,2190,1440,2040),@('txtStudentName','氏名 *',270,2190,1860,1800),@('txtStudentNameKana','氏名カナ *',270,2190,2280,6600),
        @('txtPostalCode','郵便番号 *',270,2190,4080,1800),@('txtAddressLine1','住所1 *',270,2190,4920,6600),@('txtAddressLine2','住所2',270,2190,5340,6600),@('txtPhoneNumber','本人電話',270,2190,5760,2640),@('txtEmailAddress','本人メール',270,2190,6180,6600),
        @('txtAdmissionDate','入学日 *',9315,11235,1020,1680),@('txtEnrollmentEndDate','卒業・退学日',9315,11235,1860,1680),@('txtEmergencyContactName','緊急氏名',9315,11235,4380,1800),@('txtEmergencyPhoneNumber','緊急電話',9315,11235,5220,2640),
        @('txtRemarks','備考（120文字）',9315,11235,6180,6600),@('txtOperationReason','確認・変更理由',9315,11235,6960,6600))
    foreach($taskItem in $taskTextRows){$null=Add-RowLabel $taskForm $taskItem[0] $taskItem[2] $taskItem[4] $taskItem[1];$taskCtl=Add-Text $taskForm $taskItem[0] $taskItem[3] $taskItem[4] '';$taskCtl.Width=$taskItem[5];$taskCtl.AfterUpdate='=DirtyEdit()';if($taskItem[0] -in @('txtRemarks','txtOperationReason')){$taskCtl.Height=690;$taskCtl.EnterKeyBehavior=$true;$taskCtl.ScrollBars=2}}
    $taskForm.Controls.Item('txtStudentId').Locked=$true
    $null=Add-RowLabel $taskForm 'BirthDate' 270 2700 '生年月日 *'
    $taskCtl=Add-Combo $taskForm 'cboBirthEra' 2190 2700 '' 'MEIJI;明治;TAISHO;大正;SHOWA;昭和;HEISEI;平成;REIWA;令和';$taskCtl.RowSourceType='Value List';$taskCtl.Width=1200
    foreach($taskItem in @(@('txtBirthYear',3450,780),@('txtBirthMonth',4470,630),@('txtBirthDay',5340,630))){$taskCtl=Add-Text $taskForm $taskItem[0] $taskItem[1] 2700 '';$taskCtl.Width=$taskItem[2];$taskCtl.AfterUpdate='=DirtyEdit()'}
    foreach($taskItem in @(@('Year',4260,'年'),@('Month',5130,'月'),@('Day',6000,'日'))){$null=Add-RowLabel $taskForm $taskItem[0] $taskItem[1] 2700 $taskItem[2] 180}
    foreach($taskItem in @(@('cboGender','性別 *',270,2190,3120,1560,$taskCodeSql.GENDER),@('cboPrefecture','都道府県 *',270,2190,4500,1680,$taskCodeSql.PREFECTURE),@('cboEnrollmentStatus','在籍区分 *',9315,11235,1440,2640,$taskCodeSql.ENROLLMENT_STATUS),@('cboSchoolYear','年度',9315,11235,2280,1200,$taskYearSql),@('cboGrade','学年',9315,11235,2700,2640,$taskCodeSql.GRADE),@('cboClass','クラス *',9315,11235,3120,6600,$taskClassSql),@('cboRelationship','緊急続柄',9315,11235,4800,2640,$taskCodeSql.RELATIONSHIP))){$null=Add-RowLabel $taskForm $taskItem[0] $taskItem[2] $taskItem[4] $taskItem[1];$taskCtl=Add-Combo $taskForm $taskItem[0] $taskItem[3] $taskItem[4] '' $taskItem[6];$taskCtl.Width=$taskItem[5];$taskCtl.ListWidth=9000}
    $taskForm.Controls.Item('cboClass').ColumnWidths='0cm;10cm'
    foreach($taskControlName in @('cboBirthEra','cboGender','cboPrefecture','cboRelationship')){$taskForm.Controls.Item($taskControlName).AfterUpdate='=DirtyEdit()'}
    $taskForm.Controls.Item('cboEnrollmentStatus').AfterUpdate='=StatusChanged()'
    foreach($taskBinding in @(@('cboSchoolYear','YEAR'),@('cboGrade','GRADE'),@('cboClass','CLASS'))){$taskForm.Controls.Item($taskBinding[0]).AfterUpdate='=ClassChanged("'+$taskBinding[1]+'")'}
    $null=Add-RowLabel $taskForm 'CapacityTitle' 9315 3540 '所属人数・定員'
    $taskCtl=Add-Control $taskForm 'lblCapacity' 100 11235 3570 '人数／定員：－' 6600;$taskCtl.Height=300
    $taskCtl=Add-Control $taskForm 'lblUpdated' 100 180 7830 '' 17880;$taskCtl.Height=270
    $null=Add-Button $taskForm 'cmdSave' 180 8190 '保存' 'SaveEdit()';$null=Add-Button $taskForm 'cmdReset' 1860 8190 '編集取消' 'ResetEdit(False)';$null=Add-Button $taskForm 'cmdReload' 3540 8190 '最新再読込' 'ResetEdit(True)';$null=Add-Button $taskForm 'cmdBack' 5220 8190 '検索へ戻る' 'BackEdit()';$null=Add-Button $taskForm 'cmdDelete' 16380 8190 '論理削除' 'DeleteEdit()'
    $taskForm.HasModule=$true;$taskFormModule=$taskForm.Module
    if($taskFormModule.CountOfLines -gt 0){$taskFormModule.DeleteLines(1,$taskFormModule.CountOfLines)}
    $taskFormModule.AddFromString("Option Explicit`r`nOption Compare Binary`r`nPrivate Sub Form_Load()`r`n    InitEdit Me`r`nEnd Sub`r`nPrivate Sub Form_Unload(Cancel As Integer)`r`n    Cancel = Not CanCloseEdit(Me)`r`nEnd Sub")
    $taskForm.Section(0).Height=8640
    Save-Form $taskForm 'frmStudentEdit'
    $taskForm=Create-NamedForm 'frmDiscardConfirm';$taskForm.RecordSource='';$taskForm.Width=9000;$taskForm.Section(0).Height=2400;$taskForm.Caption='未保存変更の確認';$taskForm.Modal=$true;$taskForm.PopUp=$true
    $taskCtl=Add-Control $taskForm 'lblPrompt' 100 300 300 '保存していない入力を破棄しますか。' 8400;$taskCtl.Height=900
    $null=Add-Button $taskForm 'cmdConfirm' 300 1600 '変更を破棄' 'DiscardOk()'
    $taskCtl=Add-Button $taskForm 'cmdCancel' 2300 1600 '取消' 'DiscardCancel()';$taskCtl.Default=$true;$taskCtl.Cancel=$true
    Save-Form $taskForm 'frmDiscardConfirm'
    foreach ($taskDialogName in @('frmDuplicateConfirm','frmDeleteConfirm')) {
        $taskForm=Create-NamedForm $taskDialogName; $taskForm.RecordSource=''; $taskForm.Width=11000; $taskForm.Section(0).Height=6700; $taskForm.Caption='操作の確認'; $taskForm.Modal=$true; $taskForm.PopUp=$true; $taskForm.OnLoad='[Event Procedure]'
        $taskForm.HasModule=$true; $taskFormModule=$taskForm.Module
        if ($taskFormModule.CountOfLines -gt 0) { $taskFormModule.DeleteLines(1,$taskFormModule.CountOfLines) }
        $taskFormModule.AddFromString("Option Explicit`r`nOption Compare Binary`r`nPrivate Sub Form_Load()`r`n    InitConfirmation Me`r`nEnd Sub")
        $taskPrompt=Add-Control $taskForm 'lblPrompt' 100 300 300 '' 10000; $taskPrompt.Height=900
        if ($taskDialogName -eq 'frmDuplicateConfirm') { $taskList=Add-Control $taskForm 'lstCandidates' 110 300 1400 '' 10000; $taskList.Height=3000; $taskList.RowSourceType='CandidateListCallback'; $taskList.ColumnCount=4; $taskList.ColumnWidths='2cm;2.5cm;3cm;4.5cm' }
        $taskReason=Add-Text $taskForm 'txtReason' 300 4900 '理由（60文字以内）'; $taskReason.Width=10000; $taskReason.Height=650
        $taskErrorLabel=Add-Control $taskForm 'lblError' 100 300 5650 '' 10000; $taskErrorLabel.Height=400
        $taskAccept=Add-Button $taskForm 'cmdConfirm' 300 6150 '確認して続行' 'ConfirmationOk()'
        $taskCancel=Add-Button $taskForm 'cmdCancel' 2400 6150 'キャンセル' 'ConfirmationCancel()'; $taskCancel.Default=$true; $taskCancel.Cancel=$true
        Save-Form $taskForm $taskDialogName
    }
    if (-not $NoStartup) { Set-DaoProperty $taskDb 'StartupForm' 10 'frmStudentSearch' }
    $taskDb.Close()
    if ($Compile) { Compile-Vba }
    $taskGenerated = $true
} catch {
    try {
        $taskPane = $taskAccess.VBE.ActiveCodePane
        $taskStartLine=0; $taskStartColumn=0; $taskEndLine=0; $taskEndColumn=0
        $taskPane.GetSelection([ref]$taskStartLine,[ref]$taskStartColumn,[ref]$taskEndLine,[ref]$taskEndColumn)
        Write-Output "VBA diagnostic: $($taskPane.CodeModule.Name):$taskStartLine"
        Write-Output ($taskPane.CodeModule.Lines([Math]::Max(1,$taskStartLine-2),5))
    } catch { Write-Output 'VBA diagnostic selection unavailable.' }
    throw
} finally {
    $taskAccess.Quit(2)
    [Runtime.InteropServices.Marshal]::FinalReleaseComObject($taskAccess) | Out-Null
}

# Access is closed before replacing the previous completed artifact.
if ($taskGenerated) {
    Copy-Item -LiteralPath $Frontend -Destination $taskRequestedFrontend -Force
    $taskHash = (Get-FileHash -LiteralPath $taskRequestedFrontend -Algorithm SHA256).Hash
    if ($taskHash -ne (Get-FileHash -LiteralPath $Frontend -Algorithm SHA256).Hash) { throw 'Completed artifact copy hash mismatch.' }
    if ($taskRequestedFrontend -eq $taskFinalPath) {
        $taskReport = Resolve-AccessReportPath (Join-Path $PSScriptRoot 'build/test-results')
        New-Item -ItemType Directory -Path $taskReport -Force | Out-Null
        # A new artifact has no inherited test acceptance. Keep only records for this artifact.
        foreach ($taskPreviousName in @('application.json','application.log','relationship.json','relationship.log','race.json','race.log','deployment.json','deployment.log','syntax.json','build.log','build-fixture.log','build-publication.json','path-validation.json','path-validation.log','source-inventory.json','layout.json')) {
            $taskPrevious = Resolve-AccessReportPath (Join-Path $taskReport $taskPreviousName)
            if (Test-Path -LiteralPath $taskPrevious) { Remove-Item -LiteralPath $taskPrevious -Force }
        }
        @(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot '../../spec/Access') -Recurse -File | Sort-Object FullName | ForEach-Object {
            [ordered]@{file=('../../spec/Access/'+$_.FullName.Substring(([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../spec/Access'))).Length+1).Replace('\','/'));sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
        }) | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskReport 'inputs.json') -Encoding UTF8
        [ordered]@{status='Generated';runId=$RunId;generatedAt=[DateTime]::UtcNow.ToString('o');database='build/StudentManagement.accdb';sha256=$taskHash;bytes=(Get-Item -LiteralPath $taskRequestedFrontend).Length;singleFile=$true;testModulesIncluded=[bool]$IncludeTests;compiled=[bool]$Compile;stagingArea='.tmp/generation';specificationChangedDuringBuild=$false} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskReport 'build.json') -Encoding UTF8
        [ordered]@{status='VerificationRequired';runId=$RunId;completedAt=[DateTime]::UtcNow.ToString('o');artifact=[ordered]@{file='build/StudentManagement.accdb';sha256=$taskHash;bytes=(Get-Item -LiteralPath $taskRequestedFrontend).Length};specificationChangedDuringBuild=$false;formalScore=$null;verification='Run tests/Invoke-Verification.ps1 for the current artifact.'} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $taskReport 'summary.json') -Encoding UTF8
    }
    Write-Output "Frontend generated: $taskRequestedFrontend"
}
