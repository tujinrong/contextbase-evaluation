param([string]$Configuration='Release')
$ErrorActionPreference='Stop'
& python -X utf8 (Join-Path $PSScriptRoot 'generate_api.py')
if ($LASTEXITCODE -ne 0) { throw 'Native SQL generation failed.' }
& python -X utf8 (Join-Path $PSScriptRoot 'generate_master_api.py')
if ($LASTEXITCODE -ne 0) { throw 'Native master SQL generation failed.' }
& dotnet build (Join-Path $PSScriptRoot 'Normalization/StudentNativeNormalization.csproj') --configuration $Configuration --disable-build-servers -m:1 /p:UseSharedCompilation=false --nologo
if ($LASTEXITCODE -ne 0) { throw 'SQLCLR build failed.' }
$taskDll=Join-Path $PSScriptRoot "Normalization/bin/$Configuration/net472/StudentNativeNormalization.dll"
$taskBytes=[IO.File]::ReadAllBytes($taskDll)
$taskHex=[BitConverter]::ToString($taskBytes).Replace('-','')
$taskHasher=[Security.Cryptography.SHA512]::Create()
try { $taskSha512=[BitConverter]::ToString($taskHasher.ComputeHash($taskBytes)).Replace('-','') }
finally { $taskHasher.Dispose() }
$taskDeployment=@"
-- VB.NET WinForms-only SQLCLR, exact compiled assembly hash. Apply in the approved application DB.
-- DBA action: enable CLR if approved; strict security is kept ON, TRUSTWORTHY is not enabled.
IF CONVERT(int,(SELECT value_in_use FROM sys.configurations WHERE name='clr enabled'))<>1
    THROW 51020,'Enable CLR explicitly through the approved DBA configuration before deployment.',1;
IF NOT EXISTS(SELECT 1 FROM sys.trusted_assemblies WHERE hash=0x$taskSha512)
    EXEC sys.sp_add_trusted_assembly @hash=0x$taskSha512,@description=N'VB.NET WinForms StudentNativeNormalization reviewed exact binary';
GO
IF SCHEMA_ID('student_api') IS NULL EXEC('CREATE SCHEMA student_api AUTHORIZATION dbo');
GO
CREATE ASSEMBLY StudentNativeNormalization FROM 0x$taskHex WITH PERMISSION_SET=SAFE;
GO
CREATE FUNCTION student_api.normalize_raw(@raw nvarchar(max),@business_day datetime) RETURNS nvarchar(max)
AS EXTERNAL NAME StudentNativeNormalization.[StudentManagement.Native.NativeNormalizer].NormalizeRaw;
GO
CREATE FUNCTION student_api.normalize_reason(@raw nvarchar(max)) RETURNS nvarchar(max)
AS EXTERNAL NAME StudentNativeNormalization.[StudentManagement.Native.NativeNormalizer].NormalizeReason;
GO
CREATE FUNCTION student_api.normalize_class(@raw nvarchar(max)) RETURNS nvarchar(max)
AS EXTERNAL NAME StudentNativeNormalization.[StudentManagement.Native.NativeNormalizer].NormalizeClass;
GO
CREATE FUNCTION student_api.normalize_code(@raw nvarchar(max)) RETURNS nvarchar(max)
AS EXTERNAL NAME StudentNativeNormalization.[StudentManagement.Native.NativeNormalizer].NormalizeCode;
GO
"@
[IO.File]::WriteAllText((Join-Path $PSScriptRoot '000_sqlclr.sql'),$taskDeployment,[Text.UTF8Encoding]::new($false))
Write-Output "SQLCLR SHA512: $taskSha512"
