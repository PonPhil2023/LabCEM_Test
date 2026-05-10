$projectRoot = "D:\Code\CEM_Test"
$runtimeDir = Join-Path $projectRoot "Label9_runtime"
$configDir = Join-Path $runtimeDir "config"
$configPath = Join-Path $configDir "app.json"
$exe = "D:\Code\Label9_desktop-windows_fix\Electron_app\out\Label9-win32-x64\Label9.exe"

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
New-Item -ItemType Directory -Force -Path $configDir | Out-Null

$config = @{}
if (Test-Path $configPath) {
  try { $config = Get-Content $configPath -Raw | ConvertFrom-Json -AsHashtable } catch { $config = @{} }
}
if (-not $config.ContainsKey('workspace')) { $config['workspace'] = @{} }
$config['workspace']['localRoot'] = $projectRoot
if (-not $config.ContainsKey('runtime')) { $config['runtime'] = @{} }
if (-not $config['runtime'].ContainsKey('pythonBin')) { $config['runtime']['pythonBin'] = "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" }

$json = $config | ConvertTo-Json -Depth 100
$enc = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($configPath, $json + "`n", $enc)

$env:LABELNINE_APP_DATA_DIR = $runtimeDir
if (!(Test-Path $exe)) { Write-Error "Label9.exe not found: $exe"; exit 1 }
Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe)
