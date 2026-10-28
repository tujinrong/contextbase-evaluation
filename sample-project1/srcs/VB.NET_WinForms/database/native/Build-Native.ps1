param([string]$Configuration='Release',[switch]$NoAudit)
$taskSavedEnvironment=@{}
foreach($taskEnvName in @('STUDENT_NATIVE_OUTPUT','DOTNET_CLI_HOME','NUGET_HTTP_CACHE_PATH','TEMP','TMP')) { $taskSavedEnvironment[$taskEnvName]=[Environment]::GetEnvironmentVariable($taskEnvName,'Process') }
try {
$methodRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$output=[IO.Path]::GetFullPath((Join-Path $methodRoot 'build/database/native'))
if (-not $output.StartsWith($methodRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Native output must stay in this method.' }
[void][IO.Directory]::CreateDirectory($output)
$env:STUDENT_NATIVE_OUTPUT=$output
$taskResults=Join-Path $methodRoot 'build/test-results'
[void][IO.Directory]::CreateDirectory($taskResults)
@{status='VERIFICATION_REQUIRED';reason='Native deployment resources rebuilt; rerun integrated verification';recordedAt=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskResults 'results.json') -Encoding UTF8
'VERIFICATION_REQUIRED: native deployment resources rebuilt; rerun integrated verification.' | Set-Content -LiteralPath (Join-Path $taskResults 'README.md') -Encoding UTF8
$taskAudit=@(if($NoAudit){'-p:NuGetAudit=false'})
$env:DOTNET_CLI_HOME=Join-Path $methodRoot '.tmp/dotnet-home'
$env:NUGET_HTTP_CACHE_PATH=Join-Path $methodRoot '.tmp/nuget/http-cache'
$env:TEMP=Join-Path $methodRoot '.tmp/runtime'
$env:TMP=$env:TEMP
[void][IO.Directory]::CreateDirectory($env:TEMP)
$ErrorActionPreference='Stop'
& python -X utf8 (Join-Path $PSScriptRoot 'generate_api.py')
if ($LASTEXITCODE -ne 0) { throw 'Native SQL generation failed.' }
& python -X utf8 (Join-Path $PSScriptRoot 'generate_master_api.py')
if ($LASTEXITCODE -ne 0) { throw 'Native master SQL generation failed.' }
& dotnet build (Join-Path $PSScriptRoot 'Normalization/StudentNativeNormalization.csproj') --configuration $Configuration --disable-build-servers -m:1 /p:UseSharedCompilation=false --nologo @taskAudit
if ($LASTEXITCODE -ne 0) { throw 'SQLCLR build failed.' }
$taskDll=(& dotnet msbuild (Join-Path $PSScriptRoot 'Normalization/StudentNativeNormalization.csproj') -getProperty:TargetPath "-p:Configuration=$Configuration" -nologo | Select-Object -Last 1).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve SQLCLR output.' }
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
[IO.File]::WriteAllText((Join-Path $output '000_sqlclr.sql'),$taskDeployment,[Text.UTF8Encoding]::new($false))
Write-Output "SQLCLR SHA512: $taskSha512"

} finally {
    foreach($taskEnvName in $taskSavedEnvironment.Keys) { [Environment]::SetEnvironmentVariable($taskEnvName,$taskSavedEnvironment[$taskEnvName],'Process') }
}
