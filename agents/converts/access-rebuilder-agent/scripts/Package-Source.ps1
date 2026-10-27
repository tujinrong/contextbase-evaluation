[CmdletBinding()]
param([Parameter(Mandatory)][string]$TargetRoot)
$ErrorActionPreference='Stop'
$method=(Resolve-Path -LiteralPath $TargetRoot).Path.TrimEnd('\','/')
if ($method -notmatch '[\\/]test-project[^\\/]+[\\/]srcs[\\/][^\\/]+$') { throw 'Expected an explicit project method root.' }
$temporary=Join-Path $method '.tmp'
$stage=Join-Path $temporary 'source-package'
$stagedZip=Join-Path $temporary 'source-package.zip'
foreach($candidate in @($stage,$stagedZip)) {
  $full=[IO.Path]::GetFullPath($candidate)
  if (-not $full.StartsWith($method+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Staging escaped method root.' }
}
foreach($item in Get-ChildItem -LiteralPath $method -Recurse -Force | Where-Object { $_.FullName -notlike "$temporary\*" }) {
  if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Linked artifacts cannot be packaged.' }
}
if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
New-Item -ItemType Directory -Path $stage -Force | Out-Null
$files=Get-ChildItem -LiteralPath $method -Recurse -File | Where-Object {
  $relative=$_.FullName.Substring($method.Length+1).Replace('\','/')
  $segments=$relative.Split('/')
  -not ($segments | Where-Object { $_ -in @('.tmp','build','bin','obj','tests','spec','spec-eval','node_modules','.git') }) -and
  $_.Extension -notin @('.accdb','.mdb','.laccdb','.dll','.exe','.pdb')
}
foreach($file in $files) {
  $relative=$file.FullName.Substring($method.Length+1)
  $destination=Join-Path $stage $relative
  New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
  Copy-Item -LiteralPath $file.FullName -Destination $destination
}
# Reverse-analysis source package deliberately excludes test expectations. Its
# solution contains only production projects so the package still builds alone.
$solution=Get-ChildItem -LiteralPath $stage -Filter '*.slnx' -File
if ($solution.Count -ne 1) { throw 'Expected exactly one root solution.' }
[xml]$xml=Get-Content -LiteralPath $solution.FullName -Raw
foreach($project in @($xml.SelectNodes('//Project'))) { if ($project.Path -notlike 'src/*') { [void]$project.ParentNode.RemoveChild($project) } }
$xml.Save($solution.FullName)
if (Test-Path -LiteralPath $stagedZip) { Remove-Item -LiteralPath $stagedZip -Force }
[IO.Compression.ZipFile]::CreateFromDirectory($stage,$stagedZip,[IO.Compression.CompressionLevel]::Optimal,$false)
$build=Join-Path $method 'build';New-Item -ItemType Directory -Path $build -Force|Out-Null
Move-Item -LiteralPath $stagedZip -Destination (Join-Path $build 'source.zip') -Force
[ordered]@{status='PASS';files=@($files).Count;solutionPolicy='Production projects only in source.zip; working-tree solution includes formal tests.';sha256=(Get-FileHash -LiteralPath (Join-Path $build 'source.zip') -Algorithm SHA256).Hash}|ConvertTo-Json
