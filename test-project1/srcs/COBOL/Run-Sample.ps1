[CmdletBinding()]
param([string]$RuntimeDirectory = (Join-Path $PSScriptRoot '.tmp/toolchain/msys2/ucrt64/bin'))
$ErrorActionPreference = 'Stop'
$application = Join-Path $PSScriptRoot 'build/app/windows/student-text.exe'
if (-not (Test-Path -LiteralPath $application -PathType Leaf)) { throw 'Build the Windows sample with python -X utf8 build.py first.' }
if (-not (Test-Path -LiteralPath $RuntimeDirectory -PathType Container)) { throw 'Specify the x64 GnuCOBOL/ICU/OpenSSL runtime directory with -RuntimeDirectory.' }
$runtimePath = (Resolve-Path -LiteralPath $RuntimeDirectory).ProviderPath
$previousPath = $env:PATH
try {
    $env:PATH = $runtimePath + [IO.Path]::PathSeparator + $previousPath
    Push-Location -LiteralPath $PSScriptRoot
    try { & $application; $sampleExitCode = $LASTEXITCODE } finally { Pop-Location }
} finally { $env:PATH = $previousPath }
exit $sampleExitCode
