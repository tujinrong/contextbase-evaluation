$script:AccessMethodRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))

function Resolve-AccessGeneratedPath([string]$Path, [ValidateSet('build','.tmp')][string]$Area) {
    $taskFull = [IO.Path]::GetFullPath($Path)
    $taskArea = [IO.Path]::GetFullPath((Join-Path $script:AccessMethodRoot $Area))
    if ($taskFull -ne $taskArea -and -not $taskFull.StartsWith($taskArea + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Generated path must stay under Access/$Area`: $taskFull"
    }
    $taskCursor = $taskFull
    while ($taskCursor -and $taskCursor.StartsWith($script:AccessMethodRoot, [StringComparison]::OrdinalIgnoreCase)) {
        if (Test-Path -LiteralPath $taskCursor) {
            $taskItem = Get-Item -LiteralPath $taskCursor -Force
            if (($taskItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Reparse point refused: $taskCursor" }
        }
        if ($taskCursor -eq $script:AccessMethodRoot) { break }
        $taskCursor = [IO.Path]::GetDirectoryName($taskCursor)
    }
    return $taskFull
}

function Resolve-AccessReportPath([string]$Path) {
    $taskFull = [IO.Path]::GetFullPath($Path)
    $taskFinal = [IO.Path]::GetFullPath((Join-Path $script:AccessMethodRoot 'build/test-results'))
    if ($taskFull -eq $taskFinal -or $taskFull.StartsWith($taskFinal + '\', [StringComparison]::OrdinalIgnoreCase)) {
        return Resolve-AccessGeneratedPath $taskFull 'build'
    }
    return Resolve-AccessGeneratedPath $taskFull '.tmp'
}

function Remove-AccessIntermediate([string]$Path) {
    $taskFull = Resolve-AccessGeneratedPath $Path '.tmp'
    if ($taskFull -eq [IO.Path]::GetFullPath((Join-Path $script:AccessMethodRoot '.tmp'))) { throw 'Cannot remove the intermediate root.' }
    if (Test-Path -LiteralPath $taskFull) { Remove-Item -LiteralPath $taskFull -Recurse -Force }
}
