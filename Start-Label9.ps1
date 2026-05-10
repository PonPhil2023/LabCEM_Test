param(
  [string]$RepoPath = "D:\Code\Label9_desktop-windows_fix"
)

$runtimeDir = "D:\Code\CEM_Test\Label9_runtime"
$cliPath = Join-Path $RepoPath "Electron_app\bin\labelnine.js"

if (!(Test-Path $cliPath)) {
  Write-Error "labelnine.js not found: $cliPath"
  exit 1
}

$env:LABELNINE_APP_DATA_DIR = $runtimeDir
Set-Location $RepoPath
node $cliPath start
