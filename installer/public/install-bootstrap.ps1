param(
  [string]$BaseUrl = 'https://greentv.media'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$WorkDir = Join-Path $env:TEMP 'GREENTV_BROADCASTING_KIT'
$ZipPath = Join-Path $WorkDir 'kit.zip'
$ExtractDir = Join-Path $WorkDir 'extract'
New-Item -ItemType Directory -Force -Path $WorkDir, $ExtractDir | Out-Null

function Test-ObsInstalled {
  $paths = @()
  if ($env:ProgramFiles) {
    $paths += (Join-Path $env:ProgramFiles 'obs-studio\bin\64bit\obs64.exe')
  }
  if (${env:ProgramFiles(x86)}) {
    $paths += (Join-Path ${env:ProgramFiles(x86)} 'obs-studio\bin\64bit\obs64.exe')
  }
  if ($env:LOCALAPPDATA) {
    $paths += (Join-Path $env:LOCALAPPDATA 'Programs\obs-studio\bin\64bit\obs64.exe')
    $paths += (Join-Path $env:LOCALAPPDATA 'obs-studio\bin\64bit\obs64.exe')
  }
  return $paths | Where-Object { $_ -and (Test-Path $_) }
}

function Get-ObsExePath {
  Test-ObsInstalled | Select-Object -First 1
}

function Configure-ObsDefaults {
  $obsAppData = Join-Path $env:APPDATA 'obs-studio'
  $basicDir = Join-Path $obsAppData 'basic'
  $profilesDir = Join-Path $basicDir 'profiles'
  $profileName = 'GreenTV'
  $profileDir = Join-Path $profilesDir $profileName
  $sceneCollectionName = 'GREENTV BROADCASTING KIT'
  $sceneCollectionFile = 'GREENTV_BROADCASTING_KIT.json'

  New-Item -ItemType Directory -Force -Path $profileDir | Out-Null
  New-Item -ItemType Directory -Force -Path (Join-Path $basicDir 'scenes') | Out-Null

  $basicIni = @"
[General]
Name=$profileName

[Video]
BaseCX=1920
BaseCY=1080
OutputCX=1920
OutputCY=1080
FPSType=0
FPSCommon=30

[Output]
Mode=Simple
"@
  Set-Content -Path (Join-Path $profileDir 'basic.ini') -Value $basicIni -Encoding UTF8

  $obsUserIni = Join-Path $obsAppData 'user.ini'
  $userIni = @"
[Basic]
Profile=$profileName
ProfileDir=$profileName
SceneCollection=$sceneCollectionName
SceneCollectionFile=$sceneCollectionFile
"@
  Set-Content -Path $obsUserIni -Value $userIni -Encoding UTF8
}

function Install-Obs {
  if (Test-ObsInstalled) {
    Write-Host 'OBS already installed.' -ForegroundColor Green
    return
  }

  $winget = Get-Command winget -ErrorAction SilentlyContinue
  if ($winget) {
    Write-Host 'OBS Studio not found. Trying winget first...' -ForegroundColor Yellow
    & winget install --id OBSProject.OBSStudio -e --source winget --silent --disable-interactivity --accept-source-agreements --accept-package-agreements | Write-Host
    if ($LASTEXITCODE -eq 0 -and (Test-ObsInstalled)) {
      Write-Host 'OBS installed via winget.' -ForegroundColor Green
      return
    }
    Write-Host 'winget did not complete cleanly; falling back to the OBS GitHub installer.' -ForegroundColor Yellow
  }

  $release = Invoke-RestMethod -Headers @{ Accept = 'application/vnd.github+json'; 'User-Agent' = 'GreenTV-Installer' } -Uri 'https://api.github.com/repos/obsproject/obs-studio/releases/latest'
  $arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64' -or $env:PROCESSOR_ARCHITEW6432 -eq 'ARM64') { 'arm64' } else { 'x64' }
  $asset = $release.assets | Where-Object { $_.name -match ('OBS-Studio-.*-Windows-' + $arch + '-Installer\.exe$') } | Select-Object -First 1
  if (-not $asset) {
    throw 'Could not find an OBS Studio Windows installer asset in the latest release.'
  }

  $InstallerPath = Join-Path $WorkDir $asset.name
  Write-Host ('Downloading OBS installer: ' + $asset.name) -ForegroundColor Cyan
  Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $InstallerPath

  Write-Host 'Running OBS installer silently...' -ForegroundColor Cyan
  $proc = Start-Process -FilePath $InstallerPath -ArgumentList '/S' -Wait -PassThru
  if ($proc.ExitCode -ne 0) {
    throw ('OBS installer returned exit code ' + $proc.ExitCode)
  }

  if (-not (Test-ObsInstalled)) {
    throw 'OBS installation completed, but obs64.exe was not found in the expected locations.'
  }

  Write-Host 'OBS installation verified.' -ForegroundColor Green
}

function Invoke-KitInstall {
  Write-Host 'Downloading kit zip...' -ForegroundColor Cyan
  Invoke-WebRequest -Uri ($BaseUrl + '/download/kit.zip') -OutFile $ZipPath

  Write-Host 'Extracting kit...' -ForegroundColor Cyan
  Expand-Archive -Path $ZipPath -DestinationPath $ExtractDir -Force

  $InstallScript = Join-Path $ExtractDir 'payload\kit\install.ps1'
  if (-not (Test-Path $InstallScript)) {
    throw 'Install script not found in downloaded kit.'
  }

  $scriptText = Get-Content -Raw -Path $InstallScript
  $oldBlock = @'
$obsCandidates = @(
  Join-Path ${env:ProgramFiles} ''obs-studio\bin\64bit\obs64.exe'',
  Join-Path ${env:ProgramFiles(x86)} ''obs-studio\bin\64bit\obs64.exe''
) | Where-Object { $_ -and (Test-Path $_) }
'@
  $newBlock = @'
$obsCandidates = @(
  Join-Path ${env:ProgramFiles} ''obs-studio\bin\64bit\obs64.exe'',
  Join-Path ${env:ProgramFiles(x86)} ''obs-studio\bin\64bit\obs64.exe'',
  Join-Path $env:LOCALAPPDATA ''Programs\obs-studio\bin\64bit\obs64.exe'',
  Join-Path $env:LOCALAPPDATA ''obs-studio\bin\64bit\obs64.exe''
) | Where-Object { $_ -and (Test-Path $_) }
'@
  $scriptText = $scriptText.Replace($oldBlock, $newBlock)
  Set-Content -Path $InstallScript -Value $scriptText -Encoding UTF8

  Write-Host 'Launching GreenTV kit installer...' -ForegroundColor Cyan
  & powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File $InstallScript -InstallRoot 'C:\Users\Public\Documents\GREENTV BROADCASTING KIT' -MakeDefault
}

Write-Host 'GREENTV BROADCASTING KIT bootstrap' -ForegroundColor Green
Install-Obs
Invoke-KitInstall
Configure-ObsDefaults
$obsExe = Get-ObsExePath
if ($obsExe) {
  Write-Host ('Opening OBS: ' + $obsExe) -ForegroundColor Green
  Start-Process -FilePath $obsExe | Out-Null
} else {
  Write-Host 'OBS executable not found after install.' -ForegroundColor Yellow
}
Write-Host 'Installation completed successfully.' -ForegroundColor Green
