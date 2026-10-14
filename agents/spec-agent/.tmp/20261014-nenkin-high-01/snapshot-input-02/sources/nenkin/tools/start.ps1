param(
    [int]$Port = 8089,
    [string]$RuntimeRoot = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$AppRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$OutputRoot = (Resolve-Path (Join-Path $AppRoot "..")).Path
if ([string]::IsNullOrEmpty($RuntimeRoot)) {
    $RuntimeRoot = (Resolve-Path (Join-Path $OutputRoot "runtime")).Path
}

& (Join-Path $PSScriptRoot "build.ps1") -RuntimeRoot $RuntimeRoot

$JdkHome = (Get-ChildItem -LiteralPath (Join-Path $RuntimeRoot "jdk") -Directory | Select-Object -First 1).FullName
$TomcatHome = (Get-ChildItem -LiteralPath (Join-Path $RuntimeRoot "tomcat") -Directory | Select-Object -First 1).FullName
$CatalinaBase = Join-Path $AppRoot ".runtime"

foreach ($Dir in @($CatalinaBase, "$CatalinaBase\logs", "$CatalinaBase\temp", "$CatalinaBase\work", "$CatalinaBase\webapps")) {
    if (-not (Test-Path -LiteralPath $Dir)) { New-Item -ItemType Directory -Path $Dir | Out-Null }
}
if (-not (Test-Path -LiteralPath (Join-Path $CatalinaBase "conf"))) {
    Copy-Item -LiteralPath (Join-Path $TomcatHome "conf") -Destination (Join-Path $CatalinaBase "conf") -Recurse
}

$ServerXml = Join-Path $CatalinaBase "conf\server.xml"
$ServerText = [IO.File]::ReadAllText($ServerXml)
$ServerText = [regex]::Replace($ServerText, 'port="[0-9]+" shutdown="SHUTDOWN"', 'port="8019" shutdown="SHUTDOWN"', 1)
$Connector = 'port="{0}" protocol="HTTP/1.1"' -f $Port
$ServerText = [regex]::Replace($ServerText, 'port="(?:8080|8088|8089)" protocol="HTTP/1.1"', $Connector)
[IO.File]::WriteAllText($ServerXml, $ServerText, (New-Object Text.UTF8Encoding($false)))

$DeployPath = Join-Path $CatalinaBase "webapps\n2nenkin"
if (-not (Test-Path -LiteralPath $DeployPath)) {
    New-Item -ItemType Junction -Path $DeployPath -Target $AppRoot | Out-Null
}

$Existing = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if (-not $Existing) {
    $Stdout = Join-Path $CatalinaBase "logs\console.out.log"
    $Stderr = Join-Path $CatalinaBase "logs\console.err.log"
    $Arguments = @(
        "-Djava.util.logging.config.file=$CatalinaBase\conf\logging.properties",
        "-Djava.util.logging.manager=org.apache.juli.ClassLoaderLogManager",
        "-Djdk.tls.ephemeralDHKeySize=2048",
        "-Djava.protocol.handler.pkgs=org.apache.catalina.webresources",
		"-Dn2nenkin.localDb=true",
        "-Dcatalina.base=$CatalinaBase",
        "-Dcatalina.home=$TomcatHome",
        "-Djava.io.tmpdir=$CatalinaBase\temp",
        "-classpath", "$TomcatHome\bin\bootstrap.jar;$TomcatHome\bin\tomcat-juli.jar",
        "org.apache.catalina.startup.Bootstrap", "start"
    )
    $Process = Start-Process -FilePath (Join-Path $JdkHome "bin\java.exe") -ArgumentList $Arguments -WindowStyle Hidden -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -PassThru
    [IO.File]::WriteAllText((Join-Path $CatalinaBase "tomcat.pid"), [string]$Process.Id)
}

$Url = "http://127.0.0.1:$Port/n2nenkin/"
$Ready = $false
for ($Index = 0; $Index -lt 80; $Index++) {
    try {
        $Response = Invoke-WebRequest -UseBasicParsing $Url -TimeoutSec 2
        if ($Response.StatusCode -eq 200) { $Ready = $true; break }
    } catch { }
    Start-Sleep -Milliseconds 500
}
if (-not $Ready) {
    Get-Content -LiteralPath (Join-Path $CatalinaBase "logs\console.err.log") -Tail 100 -ErrorAction SilentlyContinue
    throw "Application did not become ready."
}
Write-Host "Application started. HTTP $($Response.StatusCode)"
Write-Host "URL: $Url"
