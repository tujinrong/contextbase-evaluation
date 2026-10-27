param(
    [int]$Port = 8089,
    [string]$RuntimeRoot = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$AppRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$OutputRoot = (Resolve-Path (Join-Path $AppRoot "..")).Path
if ([string]::IsNullOrEmpty($RuntimeRoot)) { $RuntimeRoot = (Resolve-Path (Join-Path $OutputRoot "runtime")).Path }
$JdkHome = (Get-ChildItem -LiteralPath (Join-Path $RuntimeRoot "jdk") -Directory | Select-Object -First 1).FullName
$TomcatHome = (Get-ChildItem -LiteralPath (Join-Path $RuntimeRoot "tomcat") -Directory | Select-Object -First 1).FullName
$CatalinaBase = Join-Path $AppRoot ".runtime"

if (-not (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)) {
    Write-Host "Application is already stopped."
    exit 0
}

$Arguments = @(
    "-Djava.util.logging.config.file=$CatalinaBase\conf\logging.properties",
    "-Djava.util.logging.manager=org.apache.juli.ClassLoaderLogManager",
    "-Dcatalina.base=$CatalinaBase", "-Dcatalina.home=$TomcatHome", "-Djava.io.tmpdir=$CatalinaBase\temp",
    "-classpath", "$TomcatHome\bin\bootstrap.jar;$TomcatHome\bin\tomcat-juli.jar",
    "org.apache.catalina.startup.Bootstrap", "stop"
)
& (Join-Path $JdkHome "bin\java.exe") @Arguments | Out-Null
for ($Index = 0; $Index -lt 40; $Index++) {
    if (-not (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)) { Write-Host "Application stopped."; exit 0 }
    Start-Sleep -Milliseconds 250
}
throw "Application could not be stopped."

