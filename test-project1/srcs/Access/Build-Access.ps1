param(
    [string]$Frontend = (Join-Path $PSScriptRoot 'build/StudentFrontend.accdb'),
    [string]$Backend = (Join-Path $PSScriptRoot 'build/StudentBackend.accdb'),
    [switch]$CreateBackend,
    [switch]$Compile,
    [switch]$NoStartup
)
$ErrorActionPreference = 'Stop'
$taskOutputRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'build'))
foreach ($taskPath in @($Frontend, $Backend)) {
    $taskFullPath = [IO.Path]::GetFullPath($taskPath)
    if (-not $taskFullPath.StartsWith($taskOutputRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Build outputs must stay under Access/build.' }
    if ((Test-Path -LiteralPath $taskFullPath) -and ($taskPath -eq $Frontend -or $CreateBackend)) { throw "Output already exists; move it explicitly before rebuilding: $taskFullPath" }
}
New-Item -ItemType Directory -Path $taskOutputRoot -Force | Out-Null
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
    $taskControl = $taskAccess.CreateControl($form.Name, $kind, 0, '', '', $left, $top, $width, 330)
    $taskControl.Name = $name
    if ($kind -in @(100,104)) { $taskControl.Caption = $label }
    elseif ($label) {
        $taskLabel = $taskAccess.CreateControl($form.Name, 100, 0, $name, '', $left, $top - 300, $width, 270)
        $taskLabel.Caption = $label
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
    $taskButton.OnClick = "=$action"
    return $taskButton
}
function Save-Form($form, [string]$name) {
    $taskOldName = $form.Name
    $taskAccess.DoCmd.Save(2, $taskOldName); $taskAccess.DoCmd.Close(2, $taskOldName, 1)
    if ($taskOldName -ne $name) { $taskAccess.DoCmd.Rename($name, 2, $taskOldName) }
}
function Create-NamedForm([string]$name) {
    $taskAccess.DoCmd.OpenForm($name,1)
    return ,$taskAccess.Forms.Item($name)
}
try {
    if ($CreateBackend) {
        $taskAccess.NewCurrentDatabase([IO.Path]::GetFullPath($Backend), 10)
        $taskDb = $taskAccess.CurrentDb()
        $taskDdl = (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'database/schema.sql') -Encoding UTF8 -Raw) -replace '(?m)^--.*$', ''
        foreach ($taskStatement in $taskDdl.Split(';')) { if ($taskStatement.Trim()) { $taskDb.Execute(($taskStatement.Trim() -replace ' DEFAULT (True|False|\d+)',''), 128) } }
        $taskSchema = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'database/schema.json') -Encoding UTF8 -Raw | ConvertFrom-Json
        foreach ($taskTable in $taskSchema) {
            foreach ($taskColumn in $taskTable.columns) {
                $taskField = $taskDb.TableDefs.Item($taskTable.name).Fields.Item($taskColumn.name)
                if ($taskColumn.type -match '^(TEXT|LONGTEXT)') { $taskField.AllowZeroLength = $false }
                if ($taskColumn.default -match '^(True|False|[0-9]+)$') { $taskField.DefaultValue = [string]$taskColumn.default }
                if ($taskColumn.name -eq 'row_version') { $taskField.ValidationRule = '>0' }
            }
        }
        $taskValidationTable=$taskDb.TableDefs.Item('m_class'); $taskValidationTable.ValidationRule='[school_year]>=1900 And [school_year]<=9998 And ([capacity] Is Null Or ([capacity]>=1 And [capacity]<=9999)) And [display_order]>=0 And [grade_category]="GRADE" And [valid_from]<=[valid_to]'
        $taskValidationTable=$taskDb.TableDefs.Item('m_student'); $taskValidationTable.ValidationRule='[birth_date]>="1900-01-01" And [birth_date]<=[admission_date] And (([enrollment_status_code] In ("01","02") And [class_id] Is Not Null And [enrollment_end_date] Is Null) Or ([enrollment_status_code] In ("03","04") And [enrollment_end_date] Is Not Null And [admission_date]<=[enrollment_end_date])) And ([phone_number] Is Not Null Or [email_address] Is Not Null Or [emergency_phone_number] Is Not Null) And (([emergency_contact_name] Is Null And [relationship_code] Is Null And [emergency_phone_number] Is Null) Or ([emergency_contact_name] Is Not Null And [relationship_code] Is Not Null And [emergency_phone_number] Is Not Null)) And (([is_deleted]=False And [deleted_at] Is Null And [deleted_by] Is Null And [delete_reason] Is Null) Or ([is_deleted]=True And [deleted_at] Is Not Null And [deleted_by] Is Not Null And [delete_reason] Is Not Null))'
        $taskValidationTable=$taskDb.TableDefs.Item('t_write_guard'); $taskValidationTable.ValidationRule='[guard_id]=1'
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
    $taskAccess.NewCurrentDatabase([IO.Path]::GetFullPath($Frontend), 10)
    $taskBlankForm=$taskAccess.CreateForm()
    Save-Form $taskBlankForm 'frmStudentSearch'
    $taskBlankForm=$null
    $taskAccess.DoCmd.CopyObject('', 'frmStudentEdit', 2, 'frmStudentSearch')
    $taskAccess.DoCmd.CopyObject('', 'frmDuplicateConfirm', 2, 'frmStudentSearch')
    $taskAccess.DoCmd.CopyObject('', 'frmDeleteConfirm', 2, 'frmStudentSearch')
    $taskDb = $taskAccess.CurrentDb()
    Set-DaoProperty $taskDb 'StudentBackendPath' 10 ([IO.Path]::GetFullPath($Backend))
    if (Test-Path -LiteralPath $Backend) {
        $taskSchema = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'database/schema.json') -Encoding UTF8 -Raw | ConvertFrom-Json
        foreach ($taskTable in $taskSchema) {
            $taskLink=$taskDb.CreateTableDef($taskTable.name); $taskLink.Connect=";DATABASE=$([IO.Path]::GetFullPath($Backend))"; $taskLink.SourceTableName=$taskTable.name; $taskDb.TableDefs.Append($taskLink)
        }
    }
    foreach ($taskSource in Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'Modules') -Filter '*.bas') {
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
    if ($Compile) { $taskAccess.DoCmd.RunCommand(126); Write-Output 'VBA modules compiled.' }
    $taskCodeSql=@{}
    foreach ($taskCategory in @('GENDER','PREFECTURE','ENROLLMENT_STATUS','RELATIONSHIP','GRADE')) { $taskCodeSql[$taskCategory]="SELECT code_value,code_name FROM m_code WHERE category_id='$taskCategory' ORDER BY display_order,code_value" }
    $taskClassSql='SELECT class_id, CStr(school_year) & " " & class_code & " " & class_name & IIf(is_active,""," [停止]") FROM m_class ORDER BY school_year,display_order,class_code,class_id'
    $taskYearSql='SELECT DISTINCT school_year,school_year FROM m_class ORDER BY school_year DESC'
    $taskForm=Create-NamedForm 'frmStudentSearch'; $taskForm.RecordSource=''; $taskForm.Width=15000; $taskForm.Section(0).Height=10500; $taskForm.Caption='学生検索'; $taskForm.OnLoad='[Event Procedure]'
    $taskForm.HasModule=$true; $taskFormModule=$taskForm.Module
    if ($taskFormModule.CountOfLines -gt 0) { $taskFormModule.DeleteLines(1,$taskFormModule.CountOfLines) }
    $taskForm.OnUnload='[Event Procedure]'
    $taskFormModule.AddFromString("Option Explicit`r`nOption Compare Binary`r`nPrivate Sub Form_Load()`r`n    InitSearch Me`r`nEnd Sub`r`nPrivate Sub Form_Unload(Cancel As Integer)`r`n    CloseSearch Me`r`nEnd Sub")
    foreach ($taskItem in @(@('txtStudentNo','学生番号'),@('txtName','氏名'),@('txtKana','フリガナ'),@('txtPhone','電話番号'),@('txtAdmissionFrom','入学日 From'),@('txtAdmissionTo','入学日 To'))) {
        $taskIndex=[Array]::IndexOf(@('txtStudentNo','txtName','txtKana','txtPhone','txtAdmissionFrom','txtAdmissionTo'),$taskItem[0]); $null=Add-Text $taskForm $taskItem[0] (300+($taskIndex%3)*4600) (650+[Math]::Floor($taskIndex/3)*800) $taskItem[1]
    }
    $null=Add-Combo $taskForm 'cboSchoolYear' 300 2250 '年度' $taskYearSql; $null=Add-Combo $taskForm 'cboGrade' 4900 2250 '学年' $taskCodeSql.GRADE; $null=Add-Combo $taskForm 'cboClass' 9500 2250 'クラス' $taskClassSql
    foreach ($taskBinding in @(@('cboSchoolYear','YEAR'),@('cboGrade','GRADE'),@('cboClass','CLASS'))) { $taskControl=$taskForm.Controls.Item($taskBinding[0]); $taskControl.AfterUpdate='=ClassChanged("' + $taskBinding[1] + '")' }
    $null=Add-Combo $taskForm 'cboPrefecture' 300 3050 '都道府県' $taskCodeSql.PREFECTURE
    foreach ($taskItem in @(@('chkEnrolled','在学'),@('chkLeave','休学'),@('chkGraduated','卒業'),@('chkWithdrawn','退学'),@('chkUnassignedOnly','クラス未割当'))) {
        $taskIndex=[Array]::IndexOf(@('chkEnrolled','chkLeave','chkGraduated','chkWithdrawn','chkUnassignedOnly'),$taskItem[0]); $taskCtl=Add-Control $taskForm $taskItem[0] 106 (300+$taskIndex*2700) 3750 $taskItem[1]; $taskCtl.AfterUpdate='=ClassChanged()'
    }
    foreach ($taskItem in @(@('cboPageSize','ページ件数','20;50;100'),@('cboSortKey','並び順','studentNo;name;admissionDate;updatedAt'),@('cboSortDirection','方向','asc;desc'))) {
        $taskIndex=[Array]::IndexOf(@('cboPageSize','cboSortKey','cboSortDirection'),$taskItem[0]); $taskCtl=Add-Combo $taskForm $taskItem[0] (300+$taskIndex*4600) 4500 $taskItem[1] $taskItem[2]; $taskCtl.RowSourceType='Value List'; $taskCtl.ColumnCount=1; $taskCtl.ColumnWidths='4cm'; $taskCtl.AfterUpdate='=SearchClick("SORT")'
    }
    $taskList=Add-Control $taskForm 'lstStudents' 110 300 5700 '' 14400; $taskList.Height=3100; $taskList.ColumnCount=12; $taskList.ColumnWidths='0cm;2cm;2cm;2cm;2.5cm;2cm;3cm;2cm;4cm;2cm;3cm;1cm'; $taskList.BoundColumn=1; $taskList.RowSourceType='StudentListCallback'; $taskList.OnDblClick='=OpenStudent(False)'
    $null=Add-Control $taskForm 'lblCount' 100 300 5100 '未検索'; $null=Add-Control $taskForm 'lblSearchedAt' 100 4900 5100 ''; $taskMsg=Add-Control $taskForm 'lblMessage' 100 300 9500 '' 14000; $taskMsg.Height=600
    $taskBusy=Add-Text $taskForm 'IsBusy' 100 100 ''; $taskBusy.Visible=$false
    $null=Add-Button $taskForm 'cmdSearch' 300 8900 '検索' 'SearchClick("SEARCH")'; $null=Add-Button $taskForm 'cmdClear' 2100 8900 'クリア' 'ClearSearch()'; $null=Add-Button $taskForm 'cmdNew' 3900 8900 '新規登録' 'OpenStudent(True)'
    $null=Add-Button $taskForm 'cmdFirst' 6500 8900 '先頭' 'SearchClick("FIRST")'; $null=Add-Button $taskForm 'cmdPrev' 8300 8900 '前' 'SearchClick("PREV")'; $null=Add-Button $taskForm 'cmdNext' 10100 8900 '次' 'SearchClick("NEXT")'; $null=Add-Button $taskForm 'cmdLast' 11900 8900 '末尾' 'SearchClick("LAST")'
    Save-Form $taskForm 'frmStudentSearch'
    $taskForm=Create-NamedForm 'frmStudentEdit'; $taskForm.RecordSource=''; $taskForm.Width=12000; $taskForm.Section(0).Height=15200; $taskForm.Caption='学生登録・編集'; $taskForm.OnLoad='[Event Procedure]'; $taskForm.OnUnload='[Event Procedure]'
    $taskForm.HasModule=$true; $taskFormModule=$taskForm.Module
    if ($taskFormModule.CountOfLines -gt 0) { $taskFormModule.DeleteLines(1,$taskFormModule.CountOfLines) }
    $taskFormModule.AddFromString("Option Explicit`r`nOption Compare Binary`r`nPrivate Sub Form_Load()`r`n    InitEdit Me`r`nEnd Sub`r`nPrivate Sub Form_Unload(Cancel As Integer)`r`n    Cancel = Not CanCloseEdit(Me)`r`nEnd Sub")
    $taskInput=@(@('txtStudentNo','学生番号'),@('txtStudentName','氏名'),@('txtStudentNameKana','フリガナ'),@('txtBirthYear','年'),@('txtBirthMonth','月'),@('txtBirthDay','日'),@('txtPostalCode','郵便番号'),@('txtAddressLine1','住所1'),@('txtAddressLine2','住所2'),@('txtPhoneNumber','電話番号'),@('txtEmailAddress','メールアドレス'),@('txtAdmissionDate','入学日 YYYY-MM-DD'),@('txtEnrollmentEndDate','在籍終了日 YYYY-MM-DD'),@('txtEmergencyContactName','緊急連絡先氏名'),@('txtEmergencyPhoneNumber','緊急連絡先電話'),@('txtRemarks','備考'),@('txtOperationReason','操作理由'))
    for ($taskIndex=0;$taskIndex -lt $taskInput.Count;$taskIndex++) { $taskCtl=Add-Text $taskForm $taskInput[$taskIndex][0] (300+($taskIndex%2)*5700) (650+[Math]::Floor($taskIndex/2)*800) $taskInput[$taskIndex][1]; $taskCtl.AfterUpdate='=DirtyEdit()'; if ($taskCtl.Name -eq 'txtRemarks') { $taskCtl.EnterKeyBehavior=$true } }
    $taskEra=Add-Combo $taskForm 'cboBirthEra' 300 8050 '元号' 'MEIJI;明治;TAISHO;大正;SHOWA;昭和;HEISEI;平成;REIWA;令和'; $taskEra.RowSourceType='Value List'
    $null=Add-Combo $taskForm 'cboGender' 6000 8050 '性別' $taskCodeSql.GENDER; $null=Add-Combo $taskForm 'cboPrefecture' 300 8850 '都道府県' $taskCodeSql.PREFECTURE
    $taskStatus=Add-Combo $taskForm 'cboEnrollmentStatus' 6000 8850 '在籍区分' $taskCodeSql.ENROLLMENT_STATUS; $taskStatus.AfterUpdate='=StatusChanged()'
    $null=Add-Combo $taskForm 'cboSchoolYear' 300 9650 '年度' $taskYearSql; $null=Add-Combo $taskForm 'cboGrade' 6000 9650 '学年' $taskCodeSql.GRADE
    $null=Add-Combo $taskForm 'cboClass' 300 10450 'クラス' $taskClassSql; $null=Add-Combo $taskForm 'cboRelationship' 6000 10450 '続柄' $taskCodeSql.RELATIONSHIP
    foreach ($taskControlName in @('cboBirthEra','cboGender','cboPrefecture','cboSchoolYear','cboGrade','cboClass','cboRelationship')) { $taskControl=$taskForm.Controls.Item($taskControlName); $taskControl.AfterUpdate='=DirtyEdit()' }
    foreach ($taskBinding in @(@('cboSchoolYear','YEAR'),@('cboGrade','GRADE'),@('cboClass','CLASS'))) { $taskControl=$taskForm.Controls.Item($taskBinding[0]); $taskControl.AfterUpdate='=ClassChanged("' + $taskBinding[1] + '")' }
    $taskId=Add-Text $taskForm 'txtStudentId' 300 11250 '学生ID'; $taskId.Locked=$true
    $null=Add-Control $taskForm 'lblUpdated' 100 300 11900 '' 11000; $taskMsg=Add-Control $taskForm 'lblMessage' 100 300 13600 '' 11000; $taskMsg.Height=1200
    $null=Add-Button $taskForm 'cmdSave' 300 12800 '保存' 'SaveEdit()'; $null=Add-Button $taskForm 'cmdDelete' 2100 12800 '削除' 'DeleteEdit()'; $null=Add-Button $taskForm 'cmdReset' 3900 12800 '元に戻す' 'ResetEdit(False)'; $null=Add-Button $taskForm 'cmdReload' 5700 12800 '最新再読込' 'ResetEdit(True)'; $null=Add-Button $taskForm 'cmdBack' 7500 12800 '戻る' 'BackEdit()'
    Save-Form $taskForm 'frmStudentEdit'
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
    if ($Compile) { $taskAccess.DoCmd.RunCommand(126) }
    Write-Output "Frontend generated: $Frontend"
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
