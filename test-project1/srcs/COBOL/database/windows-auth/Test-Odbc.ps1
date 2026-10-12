[CmdletBinding()]
param([ValidatePattern('^[A-Za-z0-9_-]+$')][string]$DsnName='contextbase_test_project1_cobol',[switch]$Execute)
$ErrorActionPreference='Stop'
if (-not $Execute) { Write-Output "PLAN_ONLY Windows Driver Manager read-only ODBC probe: $DsnName";return }
if (-not [Environment]::Is64BitProcess) { throw 'The compiled COBOL host and this probe require 64-bit ODBC.' }
$connection=New-Object System.Data.Odbc.OdbcConnection "DSN=$DsnName;Encrypt=Yes;TrustServerCertificate=No;"
try {
    $connection.Open()
    $command=$connection.CreateCommand()
    try {
        $command.CommandText="SELECT DB_NAME(),ORIGINAL_LOGIN(),USER_NAME(),IS_ROLEMEMBER('student_admin'),CONNECTIONPROPERTY('auth_scheme'),(SELECT COUNT_BIG(*) FROM dbo.m_code_category),(SELECT COUNT_BIG(*) FROM dbo.m_code);"
        $reader=$command.ExecuteReader()
        try {
            if (-not $reader.Read()) { throw 'ODBC returned no identity row.' }
            $result=[pscustomobject]@{database=$reader.GetValue(0);originalLogin=$reader.GetValue(1);databaseUser=$reader.GetValue(2);isStudentAdmin=$reader.GetValue(3);authScheme=$reader.GetValue(4);categories=$reader.GetValue(5);codes=$reader.GetValue(6);driver=$connection.Driver;serverVersion=$connection.ServerVersion}
            $result | ConvertTo-Json
            if ($result.database -ne 'contextbase_test_project1_cobol' -or $result.authScheme -notin @('NTLM','KERBEROS') -or $result.categories -ne 5 -or $result.codes -ne 70) { throw 'ODBC identity/seed verification failed.' }
        } finally { $reader.Dispose() }
    } finally { $command.Dispose() }
} finally { $connection.Dispose() }
