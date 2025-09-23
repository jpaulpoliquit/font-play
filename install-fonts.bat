@echo off
setlocal

set SCRIPT_DIR=%~dp0
set PS1=%SCRIPT_DIR%dist\fonts-renamed\install.ps1

if not exist "%PS1%" (
  echo Cannot find installer script: %PS1%
  exit /b 1
)

powershell -ExecutionPolicy Bypass -NoProfile -File "%PS1%"

if %ERRORLEVEL% NEQ 0 (
  echo Installer reported an error (code %ERRORLEVEL%). Try running as Administrator.
  exit /b %ERRORLEVEL%
)

echo Done.
exit /b 0
