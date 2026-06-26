@echo off
setlocal EnableExtensions
set "PUBLIC_BASE_URL=__PUBLIC_BASE_URL__"
set "GITHUB_OWNER=__GITHUB_OWNER__"
set "GITHUB_REPO=__GITHUB_REPO__"
set "GITHUB_ASSET_NAME=__GITHUB_ASSET_NAME__"

echo GREENTV Broadcasting Kit Installer
echo Public base URL: %PUBLIC_BASE_URL%
echo GitHub repo: %GITHUB_OWNER%/%GITHUB_REPO%
echo Release asset: %GITHUB_ASSET_NAME%
echo Download endpoint: %PUBLIC_BASE_URL%/download/kit.zip

echo.
echo Download the kit ZIP from the endpoint above, then unzip it and run install.cmd from the extracted folder.
echo If you are automating this, use PowerShell or curl to fetch the ZIP from the download endpoint.
pause
