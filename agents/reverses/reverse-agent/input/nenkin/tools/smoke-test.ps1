param([int]$Port = 8089)
$ErrorActionPreference = "Stop"
$Base = "http://127.0.0.1:$Port/n2nenkin"
$Registered = -join ([char[]](0x767B,0x9332,0x7D42,0x4E86))
$LoadedExisting = -join ([char[]](0x65E2,0x5B58,0x30C7,0x30FC,0x30BF,0x3092,0x8AAD,0x307F,0x8FBC,0x307F,0x307E,0x3057,0x305F))
$PermissionPrefix = -join ([char[]](0x6A29,0x9650,0x304C,0x4E0D,0x8DB3,0x3057,0x3066,0x3044,0x307E,0x3059,0x3002))
$Changed = -join ([char[]](0x5909,0x66F4))
$Deleted = -join ([char[]](0x524A,0x9664))
$DeleteCompleted = $Deleted + (-join ([char[]](0x7D42,0x4E86)))

function Invoke-Form([hashtable]$Body) {
    return Invoke-WebRequest -UseBasicParsing "$Base/Action.do" -WebSession $Session -Method Post -Body $Body -TimeoutSec 20
}

function Invoke-FormAs($WebSession, [hashtable]$Body) {
    return Invoke-WebRequest -UseBasicParsing "$Base/Action.do" -WebSession $WebSession -Method Post -Body $Body -TimeoutSec 20
}

function Assert-Contains($Response, [string]$Pattern, [string]$Message) {
    if ($Response.Content -notmatch $Pattern) { throw $Message }
}

$Login = Invoke-WebRequest -UseBasicParsing "$Base/" -SessionVariable Session -TimeoutSec 10
if ($Login.StatusCode -ne 200 -or $Login.Content -notmatch 'DWH_USER_ID') { throw "Login page check failed." }

$Auth = Invoke-Form @{
    APPL_NAME='unify'; FUNCTION_ID='nenkin'; VIEW_ID='Login'; COMMAND_ID=''; UNIFY_FLG='0';
    DWH_USER_ID='00001234'; DWH_PASS_WORD='samplepass'
}
Assert-Contains $Auth 'menuForm' "N2 login and automatic staff verification check failed."
if ($Auth.Content -match 'staffForm') { throw "Manual staff input screen must not be displayed after login." }

$LegacyStaffRoute = Invoke-Form @{
    FUNCTION_ID='nenkin'; VIEW_ID='Staff'; COMMAND_ID='View'
}
Assert-Contains $LegacyStaffRoute 'menuForm' "Legacy staff route redirect check failed."
if ($LegacyStaffRoute.Content -match 'staffForm') { throw "Legacy staff route exposed the removed input screen." }

$UnknownStaffLoginPage = Invoke-WebRequest -UseBasicParsing "$Base/" -SessionVariable UnknownStaffSession -TimeoutSec 10
$UnknownStaffAuth = Invoke-FormAs $UnknownStaffSession @{
    APPL_NAME='unify'; FUNCTION_ID='nenkin'; VIEW_ID='Login'; COMMAND_ID=''; UNIFY_FLG='0';
    DWH_USER_ID='99999999'; DWH_PASS_WORD='samplepass'
}
Assert-Contains $UnknownStaffAuth 'DWH_USER_ID' "Unknown staff login rejection check failed."
if ($UnknownStaffAuth.Content -match 'menuForm') { throw "Unknown staff must not enter the business menu." }

$PensionPage = Invoke-Form @{
    FUNCTION_ID='nenkin'; VIEW_ID='Pension'; COMMAND_ID='View'
}
Assert-Contains $PensionPage 'pensionForm' "Pension screen check failed."
$TokenMatch = [regex]::Match($PensionPage.Content, 'name="CSRF_TOKEN" value="([^"]+)"')
if (-not $TokenMatch.Success) { throw "CSRF token check failed." }
$CsrfToken = $TokenMatch.Groups[1].Value

$GetKey = "GETSMOKE" + [DateTime]::UtcNow.ToString('yyyyMMddHHmmssfff')
$GetPhone = "080" + (Get-Random -Minimum 10000000 -Maximum 99999999)
$GetMutation = "$Base/Action.do?charCommonUID=smoke&FUNCTION_ID=nenkin&VIEW_ID=Pension&COMMAND_ID=Save&CSRF_TOKEN=$CsrfToken&BRANCH_NO=12&KANA_NAME=$GetKey&PHONE_NUMBER=$GetPhone"
Invoke-WebRequest -UseBasicParsing $GetMutation -WebSession $Session -Method Get -TimeoutSec 20 | Out-Null
$GetMutationCheck = Invoke-Form @{
    FUNCTION_ID='nenkin'; VIEW_ID='Pension'; COMMAND_ID='Lookup'; LOOKUP_MODE='key';
    KANA_NAME=$GetKey; PHONE_NUMBER=$GetPhone
}
Assert-Contains $GetMutationCheck '"found":false' "GET mutation guard check failed."

$Pension = Invoke-Form @{
    FUNCTION_ID='nenkin'; VIEW_ID='Pension'; COMMAND_ID='Lookup'; LOOKUP_MODE='customer';
    BRANCH_NO='75'; CUSTOMER_NO='4900'
}
Assert-Contains $Pension '"found":true' "JNDI pension database read failed."

$CustomerMasterOnly = Invoke-Form @{
    FUNCTION_ID='nenkin'; VIEW_ID='Pension'; COMMAND_ID='Lookup'; LOOKUP_MODE='customer';
    BRANCH_NO='75'; CUSTOMER_NO='4999'
}
Assert-Contains $CustomerMasterOnly '"found":true' "N2 customer master read failed."
Assert-Contains $CustomerMasterOnly '"customerNo":4999' "Customer-master-only source check failed."

$Lookup = Invoke-Form @{
    FUNCTION_ID='nenkin'; VIEW_ID='Lookup'; COMMAND_ID='View'; TARGET='customer'; BRANCH_NO='75'; PAGE='1'
}
Assert-Contains $Lookup 'data-kana-name=' "Exact-key lookup screen check failed."

$Report = Invoke-Form @{
    FUNCTION_ID='nenkin'; VIEW_ID='Report'; COMMAND_ID='Preview'; USE_BRANCH_RANGE='1'; BRANCH_FROM='75'; SORT_TYPE='1'
}
Assert-Contains $Report 'report-ledger' "Report preview check failed."
if ([regex]::Matches($Report.Content, '<tr>').Count -lt 2) { throw "Single-branch report semantics check failed." }

$Excel = Invoke-Form @{
    FUNCTION_ID='nenkin'; VIEW_ID='Excel'; COMMAND_ID='Export'; BRANCH_NO='75'
}
if ($Excel.RawContentLength -lt 1000 -or $Excel.Headers['Content-Type'] -notmatch 'spreadsheetml') { throw "Excel export check failed." }

$Key = "SMOKE" + [DateTime]::UtcNow.ToString('yyyyMMddHHmmssfff')
$Phone = "070" + (Get-Random -Minimum 10000000 -Maximum 99999999)
$Created = $false
try {
    $Save = Invoke-Form @{
        FUNCTION_ID='nenkin'; VIEW_ID='Pension'; COMMAND_ID='Save'; CSRF_TOKEN=$CsrfToken;
        BRANCH_NO='12'; CUSTOMER_NO='9999999'; STAFF_CODE='2234'; CUSTOMER_NAME='Smoke Test';
        KANA_NAME=$Key; PHONE_NUMBER=$Phone; GENDER=''; ADDRESS=''; BIRTH_DATE='';
        CLAIM_STATUS=''; CLAIM_SCHEDULED_DATE=''; PLANNED_AGE=''; RESERVATION_REQUEST_DATE='';
        DATA_UPDATE_DATE=''; NOTES=''; SPOUSE_NAME=''; HAS_BENEFIT=''; SPOUSE_BIRTH_DATE='';
        ORIGINAL_KANA=''; ORIGINAL_PHONE=''
    }
    Assert-Contains $Save $Registered "Pension insert check failed."
    $Created = $true

    $Load = Invoke-Form @{
        FUNCTION_ID='nenkin'; VIEW_ID='Pension'; COMMAND_ID='Load'; LOOKUP_KANA=$Key; LOOKUP_PHONE=$Phone
    }
    Assert-Contains $Load $LoadedExisting "Exact-key pension load check failed."

    $Update = Invoke-Form @{
        FUNCTION_ID='nenkin'; VIEW_ID='Pension'; COMMAND_ID='Save'; CSRF_TOKEN=$CsrfToken;
        BRANCH_NO='12'; CUSTOMER_NO='9999999'; STAFF_CODE='2234'; CUSTOMER_NAME='Smoke Updated';
        KANA_NAME=$Key; PHONE_NUMBER=$Phone; GENDER=''; ADDRESS=''; BIRTH_DATE='';
        CLAIM_STATUS=''; CLAIM_SCHEDULED_DATE=''; PLANNED_AGE=''; RESERVATION_REQUEST_DATE='';
        DATA_UPDATE_DATE=''; NOTES=''; SPOUSE_NAME=''; HAS_BENEFIT=''; SPOUSE_BIRTH_DATE='';
        ORIGINAL_KANA=$Key; ORIGINAL_PHONE=$Phone
    }
    Assert-Contains $Update $Registered "Pension update check failed."

    $LowRoleLoginPage = Invoke-WebRequest -UseBasicParsing "$Base/" -SessionVariable LowRoleSession -TimeoutSec 10
    $LowRoleMenu = Invoke-FormAs $LowRoleSession @{
        APPL_NAME='unify'; FUNCTION_ID='nenkin'; VIEW_ID='Login'; COMMAND_ID=''; UNIFY_FLG='0';
        DWH_USER_ID='00001235'; DWH_PASS_WORD='samplepass'
    }
    Assert-Contains $LowRoleMenu 'menuForm' "Low-role automatic staff verification check failed."
    $LowRolePension = Invoke-FormAs $LowRoleSession @{
        FUNCTION_ID='nenkin'; VIEW_ID='Pension'; COMMAND_ID='View'
    }
    $LowTokenMatch = [regex]::Match($LowRolePension.Content, 'name="CSRF_TOKEN" value="([^"]+)"')
    if (-not $LowTokenMatch.Success) { throw "Low-role CSRF token check failed." }
    $LowCsrfToken = $LowTokenMatch.Groups[1].Value
    $DeniedUpdate = Invoke-FormAs $LowRoleSession @{
        FUNCTION_ID='nenkin'; VIEW_ID='Pension'; COMMAND_ID='Save'; CSRF_TOKEN=$LowCsrfToken;
        BRANCH_NO='12'; CUSTOMER_NO='9999999'; STAFF_CODE='2234'; CUSTOMER_NAME='Must Not Update';
        KANA_NAME=$Key; PHONE_NUMBER=$Phone; GENDER=''; ADDRESS=''; BIRTH_DATE='';
        CLAIM_STATUS=''; CLAIM_SCHEDULED_DATE=''; PLANNED_AGE=''; RESERVATION_REQUEST_DATE='';
        DATA_UPDATE_DATE=''; NOTES=''; SPOUSE_NAME=''; HAS_BENEFIT=''; SPOUSE_BIRTH_DATE='';
        ORIGINAL_KANA=$Key; ORIGINAL_PHONE=$Phone
    }
    Assert-Contains $DeniedUpdate ($PermissionPrefix + $Changed) "Branch 75 change permission check failed."
    $DeniedDelete = Invoke-FormAs $LowRoleSession @{
        FUNCTION_ID='nenkin'; VIEW_ID='Pension'; COMMAND_ID='Delete'; CSRF_TOKEN=$LowCsrfToken;
        BRANCH_NO='12'; KANA_NAME=$Key; PHONE_NUMBER=$Phone;
        ORIGINAL_KANA=$Key; ORIGINAL_PHONE=$Phone
    }
    Assert-Contains $DeniedDelete ($PermissionPrefix + $Deleted) "Branch 75 delete permission check failed."

    $Batch = Invoke-Form @{
        FUNCTION_ID='nenkin'; VIEW_ID='Batch'; COMMAND_ID='Daily'; CSRF_TOKEN=$CsrfToken;
        STAFF_NO=''; INCLUDE_NEW='1'; INCLUDE_CHANGED='1'; INCLUDE_DELETED='1';
        DAILY_DATE=(Get-Date).ToString('yyyy/MM/dd');
        DELETE_CUTOFF_DATE=(Get-Date).AddMonths(-2).ToString('yyyy-MM-dd')
    }
    if ($Batch.RawContentLength -lt 1000 -or $Batch.Headers['Content-Type'] -notmatch 'zip|spreadsheetml') { throw "Batch export check failed." }

    $Delete = Invoke-Form @{
        FUNCTION_ID='nenkin'; VIEW_ID='Pension'; COMMAND_ID='Delete'; CSRF_TOKEN=$CsrfToken;
        BRANCH_NO='12'; KANA_NAME=$Key; PHONE_NUMBER=$Phone;
        ORIGINAL_KANA=$Key; ORIGINAL_PHONE=$Phone
    }
    Assert-Contains $Delete $DeleteCompleted "Pension delete check failed."
    $Created = $false

    $Missing = Invoke-Form @{
        FUNCTION_ID='nenkin'; VIEW_ID='Pension'; COMMAND_ID='Lookup'; LOOKUP_MODE='key';
        KANA_NAME=$Key; PHONE_NUMBER=$Phone
    }
    Assert-Contains $Missing '"found":false' "Pension delete persistence check failed."
} finally {
    if ($Created) {
        try {
            Invoke-Form @{
                FUNCTION_ID='nenkin'; VIEW_ID='Pension'; COMMAND_ID='Delete'; CSRF_TOKEN=$CsrfToken;
                BRANCH_NO='12'; KANA_NAME=$Key; PHONE_NUMBER=$Phone;
                ORIGINAL_KANA=$Key; ORIGINAL_PHONE=$Phone
            } | Out-Null
        } catch { }
    }
}

Write-Host "Smoke test passed (login/automatic staff/exact Access tables/lookup/report/xlsx/CRUD/batch): $Base/"
