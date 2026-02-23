@echo off
setlocal

set SCRIPT_DIR=%~dp0
set REPO_ROOT=%SCRIPT_DIR%..

powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%build_windows.ps1" %*
if errorlevel 1 exit /b %errorlevel%

echo Build finished.
