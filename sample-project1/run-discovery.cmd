@echo off
setlocal
chcp 65001 >nul
if /I "%~1"=="--no-pause" set "CONTEXTBASE_DISCOVERY_NO_PAUSE=1"
set "DISCOVERY_BOOTSTRAP=%~dp0..\agents\reverses\discovery-agent\launch.py"
set "DISCOVERY_CONFIG=%~dp0contextbase.toml"
where py >nul 2>&1
if errorlevel 1 goto try_python
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if errorlevel 1 goto try_python
py -3 -X utf8 "%DISCOVERY_BOOTSTRAP%" --config "%DISCOVERY_CONFIG%" %*
set "DISCOVERY_EXIT=%ERRORLEVEL%"
goto finished

:try_python
where python >nul 2>&1
if errorlevel 1 goto missing_python
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if errorlevel 1 goto missing_python
python -X utf8 "%DISCOVERY_BOOTSTRAP%" --config "%DISCOVERY_CONFIG%" %*
set "DISCOVERY_EXIT=%ERRORLEVEL%"
goto finished

:missing_python
echo Python 3.11 or later is required. Install Python and run this file again.
set "DISCOVERY_EXIT=1"

:finished
echo.
if "%DISCOVERY_EXIT%"=="0" (echo Launcher finished.) else (echo Discovery stopped. Exit code: %DISCOVERY_EXIT%)
if not "%CONTEXTBASE_DISCOVERY_NO_PAUSE%"=="1" pause
exit /b %DISCOVERY_EXIT%
