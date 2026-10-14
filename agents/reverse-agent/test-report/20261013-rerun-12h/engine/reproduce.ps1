param([ValidatePattern('^[A-Za-z0-9_-]+$')][string]$RunId = (Get-Date -Format 'yyyyMMdd-HHmmss'))
$ErrorActionPreference = 'Stop'
$engineAgent = 'D:\開発\contextbase-evaluation\agents\reverse-agent'
$engineRuntime = 'C:\Users\tujin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$engineReport = Join-Path $engineAgent 'test-report\20261013-rerun-12h\engine'
$env:PYTHONPATH = @(
    (Join-Path $engineAgent 'src'),
    (Join-Path $engineAgent '.tmp\20261013-rerun-12h\engine-runtime-deps'),
    (Join-Path $engineAgent '.tmp\session-python-deps')
) -join ';'
$env:CONTEXTBASE_CHROMIUM_EXE = 'C:\Users\tujin\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe'
$env:CONTEXTBASE_MERMAID_PACKAGE = Join-Path $engineAgent '.tmp\render-tools\node_modules\mermaid'
$env:CONTEXTBASE_RENDER_TEST_RUN = Join-Path $engineReport "synthetic-render-$RunId"
$engineLog = Join-Path $engineReport "ai-tests-$RunId.raw.log"
& $engineRuntime -X utf8 -m unittest discover -s (Join-Path $engineAgent 'src\contextbase\tests') -p 'test_ai*.py' -v *> $engineLog
$engineExit = $LASTEXITCODE
Get-Content -LiteralPath $engineLog -Tail 20
exit $engineExit
