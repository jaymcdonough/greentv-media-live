@echo off
setlocal EnableExtensions EnableDelayedExpansion
set "PUBLIC_BASE_URL=__PUBLIC_BASE_URL__"

echo.
echo Launching the GreenTV installer...
echo.
where powershell >nul 2>nul
if errorlevel 1 (
  echo PowerShell is required to run this installer.
  pause
  exit /b 1
)

powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue';" ^
  "$base='__PUBLIC_BASE_URL__';" ^
  "$work=Join-Path $env:TEMP 'GREENTV_BROADCASTING_KIT';" ^
  "$banner=Join-Path $work 'GreenTV-ASII.ps1';" ^
  "$bootstrap=Join-Path $work 'install-bootstrap.ps1';" ^
  "New-Item -ItemType Directory -Force -Path $work | Out-Null;" ^
  "Write-Host 'Rendering GreenTV terminal banner...';" ^
  "Invoke-WebRequest -Uri ($base + '/public/GreenTV-ASII%20for%20terminal.txt') -OutFile $banner;" ^
  "& powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File $banner;" ^
  "Write-Host 'Fetching GreenTV installer bootstrap...';" ^
  "Invoke-WebRequest -Uri ($base + '/public/install-bootstrap.ps1') -OutFile $bootstrap;" ^
  "Write-Host 'Starting install...';" ^
  "& powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File $bootstrap -BaseUrl $base"

if errorlevel 1 (
  echo.
  echo Installation failed. Review the messages above.
  pause
  exit /b 1
)

echo.
echo Installation completed successfully.
echo Open OBS and confirm the GREENTV_BROADCASTING_KIT scene collection is selected.
pause
