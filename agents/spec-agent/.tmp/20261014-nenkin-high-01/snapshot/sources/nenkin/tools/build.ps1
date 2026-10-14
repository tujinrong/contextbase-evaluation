param(
    [string]$RuntimeRoot = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$AppRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$OutputRoot = (Resolve-Path (Join-Path $AppRoot "..")).Path
$FrameworkRoot = (Resolve-Path (Join-Path $OutputRoot "n2framework")).Path

if ([string]::IsNullOrEmpty($RuntimeRoot)) {
    $RuntimeRoot = (Resolve-Path (Join-Path $OutputRoot "runtime")).Path
}

$JdkHome = (Get-ChildItem -LiteralPath (Join-Path $RuntimeRoot "jdk") -Directory | Select-Object -First 1).FullName
$TomcatHome = (Get-ChildItem -LiteralPath (Join-Path $RuntimeRoot "tomcat") -Directory | Select-Object -First 1).FullName
$LibDir = Join-Path $AppRoot "WEB-INF\lib"
$ClassesDir = Join-Path $AppRoot "WEB-INF\classes"

if (Test-Path -LiteralPath $ClassesDir) {
    Remove-Item -LiteralPath $ClassesDir -Recurse -Force
}
New-Item -ItemType Directory -Path $LibDir, $ClassesDir -Force | Out-Null

& (Join-Path $JdkHome "bin\jar.exe") cf (Join-Path $LibDir "FW.jar") -C (Join-Path $FrameworkRoot "WEB-INF\classes") .
if ($LASTEXITCODE -ne 0) { throw "FW.jar build failed." }

foreach ($Name in @("commons-logging.jar", "log4j.jar", "itextpdf-5.3.4.jar")) {
    Copy-Item -LiteralPath (Join-Path $FrameworkRoot "WEB-INF\lib\$Name") -Destination (Join-Path $LibDir $Name) -Force
}

$H2Version = "2.1.214"
$H2FileName = "h2-$H2Version.jar"
$H2ExpectedSha256 = "d623cdc0f61d218cf549a8d09f1c391ff91096116b22e2475475fce4fbe72bd0"
$H2DownloadDir = Join-Path $RuntimeRoot "downloads"
$H2Source = Join-Path $H2DownloadDir $H2FileName
if (-not (Test-Path -LiteralPath $H2Source)) {
    New-Item -ItemType Directory -Path $H2DownloadDir -Force | Out-Null
    Invoke-WebRequest -UseBasicParsing "https://repo1.maven.org/maven2/com/h2database/h2/$H2Version/$H2FileName" -OutFile $H2Source
}
if ((Get-FileHash -LiteralPath $H2Source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $H2ExpectedSha256) {
    throw "H2 SHA-256 verification failed."
}
Copy-Item -LiteralPath $H2Source -Destination (Join-Path $LibDir $H2FileName) -Force

$Sources = @(Get-ChildItem -LiteralPath (Join-Path $AppRoot "WEB-INF\src") -File -Recurse -Filter "*.java" | ForEach-Object FullName)
$ClassPath = (Join-Path $TomcatHome "lib\servlet-api.jar") + ";" + (Join-Path $LibDir "*")
& (Join-Path $JdkHome "bin\javac.exe") -encoding UTF-8 -source 1.7 -target 1.7 -Xlint:-options -classpath $ClassPath -d $ClassesDir @Sources
if ($LASTEXITCODE -ne 0) { throw "Application compilation failed." }

Copy-Item -LiteralPath (Join-Path $AppRoot "WEB-INF\resources\log4j.properties") -Destination (Join-Path $ClassesDir "log4j.properties") -Force
$ClassCount = @(Get-ChildItem -LiteralPath $ClassesDir -File -Recurse -Filter "*.class").Count
Write-Host "Build completed. Class count: $ClassCount"

