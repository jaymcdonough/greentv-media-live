param(
  [string]$BaseUrl = 'https://greentv.media',
  [string]$GitHubOwner = 'jaymcdonough',
  [string]$GitHubRepo = 'GREENTV_BROADCASTING_KIT_INSTALLER',
  [string]$GitHubAssetName = 'GREENTV_BROADCASTING_KIT_RELEASE_v2.0.zip'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$WorkDir = Join-Path $env:TEMP 'GREENTV_BROADCASTING_KIT'
$ZipPath = Join-Path $WorkDir 'kit.zip'
$ExtractDir = Join-Path $WorkDir 'extract'
$InstallRoot = Join-Path $env:PUBLIC 'Documents\GREENTV BROADCASTING KIT'
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
  param(
    [string]$DefaultSceneCollectionName = 'GreenTV - Interview Scene (1 Guest)',
    [string]$DefaultSceneCollectionFile = 'greentv-studio.json'
  )
  $obsAppData = Join-Path $env:APPDATA 'obs-studio'
  $basicDir = Join-Path $obsAppData 'basic'
  $profilesDir = Join-Path $basicDir 'profiles'
  $profileName = 'GreenTV'
  $profileDir = Join-Path $profilesDir $profileName

  if (Test-Path $obsAppData) {
    $backupDir = Join-Path $WorkDir 'obs-config-backup'
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    Copy-Item -Path $obsAppData -Destination (Join-Path $backupDir 'obs-studio') -Recurse -Force -ErrorAction SilentlyContinue
    # Only remove this profile, never the whole basic\ dir (that would delete scenes\ too)
    Remove-Item -Path $profileDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path (Join-Path $obsAppData 'global.ini') -Force -ErrorAction SilentlyContinue
    Remove-Item -Path (Join-Path $obsAppData 'user.ini') -Force -ErrorAction SilentlyContinue
  }

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
SceneCollection=$DefaultSceneCollectionName
SceneCollectionFile=$DefaultSceneCollectionFile
"@
  Set-Content -Path $obsUserIni -Value $userIni -Encoding UTF8
}

function Install-Obs {
  if (Test-ObsInstalled) {
    Write-Host 'OBS already installed. Skipping OBS install.' -ForegroundColor Green
    return $true
  }

  $winget = Get-Command winget -ErrorAction SilentlyContinue
  if ($winget) {
    Write-Host 'OBS Studio not found. Trying winget first...' -ForegroundColor Yellow
    & winget install --id OBSProject.OBSStudio -e --source winget --silent --disable-interactivity --accept-source-agreements --accept-package-agreements | Write-Host
    if ($LASTEXITCODE -eq 0 -and (Test-ObsInstalled)) {
      Write-Host 'OBS installed via winget.' -ForegroundColor Green
      return $true
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
  return $true
}

function Invoke-KitInstall {
  $downloaded = $false

  Write-Host 'Checking GitHub for the latest kit release...' -ForegroundColor Cyan
  try {
    $release = Invoke-RestMethod -Headers @{ Accept = 'application/vnd.github+json'; 'User-Agent' = 'GreenTV-Installer' } -Uri ('https://api.github.com/repos/' + $GitHubOwner + '/' + $GitHubRepo + '/releases/latest')
    $asset = $release.assets | Where-Object { $_.name -eq $GitHubAssetName } | Select-Object -First 1
    if (-not $asset) {
      # Exact name not found -- fall back to "first .zip asset" so a version bump in the
      # filename doesn't silently break this the way the old static-folder-name check did.
      $asset = $release.assets | Where-Object { $_.name -match '\.zip$' } | Select-Object -First 1
    }
    if ($asset) {
      Write-Host ('Downloading kit release asset: ' + $asset.name) -ForegroundColor Cyan
      Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $ZipPath
      $downloaded = $true
    } else {
      Write-Host 'No zip asset found on the latest GitHub release. Falling back to greentv.media.' -ForegroundColor Yellow
    }
  } catch {
    Write-Host ('GitHub release check failed (' + $_.Exception.Message + '). Falling back to greentv.media.') -ForegroundColor Yellow
  }

  if (-not $downloaded) {
    Write-Host 'Downloading kit zip from greentv.media...' -ForegroundColor Cyan
    Invoke-WebRequest -Uri ($BaseUrl + '/download/kit.zip') -OutFile $ZipPath
  }

  Write-Host 'Extracting kit...' -ForegroundColor Cyan
  Expand-Archive -Path $ZipPath -DestinationPath $ExtractDir -Force

  $TopLevelDir = Get-ChildItem -LiteralPath $ExtractDir -Directory |
    Where-Object { $_.Name -match '^GREENTV_BROADCASTING_KIT' } |
    Select-Object -First 1
  if (-not $TopLevelDir) {
    throw 'Downloaded kit root (GREENTV_BROADCASTING_KIT*) not found.'
  }
  $PackageRoot = Join-Path $TopLevelDir.FullName 'package'
  $SceneCollectionsDir = Join-Path $PackageRoot 'scene-collections'
  if (-not (Test-Path $SceneCollectionsDir)) {
    throw 'scene-collections folder not found in downloaded kit.'
  }

  # Single consolidated scene collection -- exactly one file expected now.
  $SceneFile = Get-ChildItem -LiteralPath $SceneCollectionsDir -Filter '*.json' | Select-Object -First 1
  if (-not $SceneFile) {
    throw 'No scene collection JSON file found in downloaded kit.'
  }

  New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
  $obsScenesDir = Join-Path $env:APPDATA 'obs-studio\basic\scenes'
  New-Item -ItemType Directory -Force -Path $obsScenesDir | Out-Null

  Write-Host 'Copying GreenTV kit package into install root...' -ForegroundColor Cyan
  New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
  Get-ChildItem -LiteralPath $InstallRoot -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
  Copy-Item -Path (Join-Path $PackageRoot '*') -Destination $InstallRoot -Recurse -Force

  # Animated Lower Thirds installs under %APPDATA%\obs-studio\animated-lower-thirds\
  # (clean lowercase/hyphenated naming -- avoids the spaces and "--" prefix that caused
  # URL-encoding and quoting issues in the original local folder name).
  $kitLowerThirdsSource = Join-Path $PackageRoot 'Assets\lower-thirds'
  $obsLowerThirdsDest = Join-Path $env:APPDATA 'obs-studio\animated-lower-thirds'
  if (Test-Path $kitLowerThirdsSource) {
    New-Item -ItemType Directory -Force -Path $obsLowerThirdsDest | Out-Null
    Copy-Item -Path (Join-Path $kitLowerThirdsSource '*') -Destination $obsLowerThirdsDest -Recurse -Force
    Write-Host ('Installed Animated Lower Thirds to: ' + $obsLowerThirdsDest) -ForegroundColor Green
  } else {
    Write-Host 'No Assets\lower-thirds folder found in kit package -- skipping lower thirds install.' -ForegroundColor Yellow
  }

  $kitRootPath = ($InstallRoot -replace '\\', '/')
  $kitRootUrl = $kitRootPath -replace ' ', '%20'

  # browser-source.html now lives directly in the lower-thirds install folder (flattened
  # structure, no nested "lower-thirds\lower-thirds\" duplication from the original package).
  $lowerThirdsFsPath = Join-Path $obsLowerThirdsDest 'browser-source.html'
  $lowerThirdsUrl = 'file:///' + ($lowerThirdsFsPath -replace '\\', '/' -replace ' ', '%20')

  function Set-KitTokens {
    param([string]$Content)
    $Content = $Content.Replace('__KIT_ROOT_URL__', $kitRootUrl)
    $Content = $Content.Replace('__KIT_ROOT__', $kitRootPath)
    $Content = $Content.Replace('__LOWER_THIRDS_URL__', $lowerThirdsUrl)
    # Guest solo links and the director control link are per-broadcast VDO.Ninja URLs.
    # They are NOT known at install time -- leave them as placeholders for the user/Hermes
    # to fill in per-broadcast, same as the original kit's manual workflow.
    return $Content
  }

  $raw = Get-Content -Raw -Path $SceneFile.FullName
  $raw = Set-KitTokens -Content $raw
  $destPath = Join-Path $obsScenesDir $SceneFile.Name
  Set-Content -Path $destPath -Value $raw -Encoding UTF8

  $parsed = $null
  try { $parsed = $raw | ConvertFrom-Json } catch { }
  $collectionName = if ($parsed -and $parsed.name) { $parsed.name } else { [IO.Path]::GetFileNameWithoutExtension($SceneFile.Name) }
  Write-Host ('Wrote scene collection: ' + $collectionName + ' -> ' + $destPath) -ForegroundColor Green

  if ($raw -match '__GUEST_\d+_SOLO_LINK__' -or $raw -match '__DIRECTOR_CONTROL_LINK__') {
    Write-Host 'NOTE: Scene collection contains unfilled VDO.Ninja link placeholders (__GUEST_N_SOLO_LINK__ / __DIRECTOR_CONTROL_LINK__).' -ForegroundColor Yellow
    Write-Host '      Set the real solo links in OBS before going live for this broadcast.' -ForegroundColor Yellow
  }

  # Template any other JSON assets that reference these tokens.
  $otherJsonFiles = Get-ChildItem -LiteralPath $InstallRoot -Recurse -Filter '*.json' -File
  foreach ($jsonFile in $otherJsonFiles) {
    $content = Get-Content -Raw -Path $jsonFile.FullName
    if ($content -match '__KIT_ROOT__' -or $content -match '__KIT_ROOT_URL__' -or $content -match '__LOWER_THIRDS_URL__') {
      $content = Set-KitTokens -Content $content
      Set-Content -Path $jsonFile.FullName -Value $content -Encoding UTF8
      Write-Host ('Templated asset paths in: ' + $jsonFile.FullName) -ForegroundColor DarkGray
    }
  }

  Write-Host ('Installed kit copied to: ' + $InstallRoot) -ForegroundColor Green
  return $collectionName
}

function Install-MoveTransitionPlugin {
  $obsExe = Get-ObsExePath
  if (-not $obsExe) {
    Write-Host 'Skipping Move Transition: OBS not found.' -ForegroundColor Yellow
    return
  }
  # OBS root is two levels up from bin\64bit\obs64.exe
  $obsRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $obsExe))
  $pluginMarker = Join-Path $obsRoot 'obs-plugins\64bit\move-transition.dll'
  if (Test-Path $pluginMarker) {
    Write-Host 'Move Transition plugin already installed. Skipping.' -ForegroundColor Green
    return
  }

  Write-Host 'Installing Move Transition plugin...' -ForegroundColor Cyan
  $release = Invoke-RestMethod -Headers @{ Accept = 'application/vnd.github+json'; 'User-Agent' = 'GreenTV-Installer' } -Uri 'https://api.github.com/repos/exeldro/obs-move-transition/releases/latest'
  $asset = $release.assets | Where-Object { $_.name -match '(?i)windows.*Installer\.exe$|x64.*Installer\.exe$' } | Select-Object -First 1
  if (-not $asset) {
    Write-Host 'Could not find a Windows installer asset for Move Transition. Skipping plugin install.' -ForegroundColor Yellow
    return
  }

  $pluginInstaller = Join-Path $WorkDir $asset.name
  Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $pluginInstaller
  Write-Host 'Running Move Transition installer silently...' -ForegroundColor Cyan
  # /S = silent. Most exeldro plugin installers are Inno/NSIS based and honor /S like the OBS installer does.
  # Pointing it at the existing OBS root via /D ensures it lands inside this OBS install rather than guessing.
  $proc = Start-Process -FilePath $pluginInstaller -ArgumentList @('/S', "/D=$obsRoot") -Wait -PassThru
  if ($proc.ExitCode -ne 0) {
    Write-Host ('Move Transition installer returned exit code ' + $proc.ExitCode + '. You may need to install it manually.') -ForegroundColor Yellow
    return
  }

  if (Test-Path $pluginMarker) {
    Write-Host 'Move Transition plugin installed.' -ForegroundColor Green
  } else {
    Write-Host 'Move Transition installer ran, but the plugin DLL was not found where expected. Verify manually.' -ForegroundColor Yellow
  }
}

function Install-LowerThirdsPack {
  # The animated lower-thirds pack is delivered as part of your own kit.zip (not a third-party
  # plugin), so it gets copied alongside scene-collections/ during Invoke-KitInstall. This function
  # is a placeholder in case you want to source it from a separate URL instead -- fill in $BaseUrl
  # path below once you confirm where the lower-thirds asset pack actually lives.
  Write-Host 'Lower-thirds assets are installed as part of the kit package (see Invoke-KitInstall).' -ForegroundColor DarkGray
}

Write-Host 'GREENTV BROADCASTING KIT bootstrap' -ForegroundColor Green
Install-Obs
Install-MoveTransitionPlugin
Configure-ObsDefaults
$installedCollectionName = Invoke-KitInstall
$obsExe = Get-ObsExePath
if ($obsExe) {
  $obsWorkDir = Split-Path -Parent $obsExe
  Write-Host ('Opening OBS: ' + $obsExe) -ForegroundColor Green
  Start-Process -FilePath $obsExe -WorkingDirectory $obsWorkDir -ArgumentList @('--profile', 'GreenTV', '--collection', $installedCollectionName) | Out-Null
} else {
  Write-Host 'OBS executable not found after install.' -ForegroundColor Yellow
}
Write-Host ('Installed scene collection: ' + $installedCollectionName) -ForegroundColor Green
Write-Host 'Installation completed successfully.' -ForegroundColor Green
