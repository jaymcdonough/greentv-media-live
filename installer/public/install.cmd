@echo off
setlocal EnableExtensions EnableDelayedExpansion
set "PUBLIC_BASE_URL=__PUBLIC_BASE_URL__"
set "GITHUB_OWNER=__GITHUB_OWNER__"
set "GITHUB_REPO=__GITHUB_REPO__"
set "GITHUB_ASSET_NAME=__GITHUB_ASSET_NAME__"

echo.
echo   _____ _____ _____ _____ _____ _____   __
echo  / ____|  __ \_   _/ ____|  __ \_   _| /_ ^|
echo | |  __| |__) || || |  __| |  | || |     | ^|
echo | | |_ |  _  / | || | |_ | |  | || |     | ^|
echo | |__| | | \ \_| || |__| | |__| || |_    | ^|
echo  \_____|_|  \_\_____\_____|_____/_____|   |_|
echo.
echo GREENTV Broadcasting Kit Installer
echo Public base URL: %PUBLIC_BASE_URL%
echo GitHub repo: %GITHUB_OWNER%/%GITHUB_REPO%
echo Release asset: %GITHUB_ASSET_NAME%
echo.
echo This bootstrapper will:
echo   1^) Download the latest kit ZIP from %PUBLIC_BASE_URL%/download/kit.zip
echo   2^) Extract the kit to a temp folder
echo   3^) Install OBS Studio if needed
echo   4^) Install the GreenTV scene collection and bundled assets
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
  "$zip=Join-Path $work 'kit.zip';" ^
  "$extract=Join-Path $work 'extract';" ^
  "New-Item -ItemType Directory -Force -Path $work,$extract | Out-Null;" ^
  "Write-Host 'Rendering GreenTV terminal banner...';" ^
  "Invoke-WebRequest -Uri ($base + '/public/GreenTV-ASII%20for%20terminal.txt') -OutFile (Join-Path $work 'GreenTV-ASII.ps1');" ^
  "& powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File (Join-Path $work 'GreenTV-ASII.ps1');" ^
  "Write-Host 'Downloading kit zip...';" ^
  "Invoke-WebRequest -Uri ($base + '/download/kit.zip') -OutFile $zip;" ^
  "Write-Host 'Extracting kit...';" ^
  "Expand-Archive -Path $zip -DestinationPath $extract -Force;" ^
  "$script=Join-Path $extract 'payload\kit\install.ps1';" ^
  "if (!(Test-Path $script)) { throw 'Install script not found in downloaded kit.' }" ^
  "Write-Host 'Launching OBS + GreenTV installer...';" ^
  "& powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File $script -InstallRoot 'C:\Users\Public\Documents\GREENTV BROADCASTING KIT' -MakeDefault"

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
