# Cwd: D:\開発\contextbase-evaluation\agents\reverse-agent
$env:PYTHONPATH=(Join-Path (Get-Location) 'src')+';'+(Join-Path (Get-Location) '.tmp/pydeps')
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:CONTEXTBASE_CHROMIUM_EXE='C:\Users\tujin\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe'
$env:CONTEXTBASE_MERMAID_PACKAGE=(Join-Path (Get-Location) '.tmp/render-tools/node_modules/mermaid')
# Set a NEW nonexistent directory for each execution.
$env:CONTEXTBASE_RENDER_TEST_RUN=(Join-Path (Get-Location) '.tmp/publication/rendering-01-next-unique-id')
python -B -m unittest contextbase.tests.test_ai_rendering -v
