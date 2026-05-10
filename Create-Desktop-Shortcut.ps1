$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "LabCEM GUI.lnk"
$TargetPath = "D:\Code\CEM_Test\Run-LabCEM-GUI.bat"
$IconPath = "D:\Code\CEM_Test\venv\Scripts\python.exe"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = "D:\Code\CEM_Test"
$Shortcut.IconLocation = "$IconPath,0"
$Shortcut.Description = "Launch LabCEM GUI"
$Shortcut.Save()

Write-Output "Created: $ShortcutPath"
