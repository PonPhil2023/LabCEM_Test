@echo off
setlocal
cd /d D:\Code\CEM_Test
call D:\Code\CEM_Test\venv\Scripts\activate.bat
python -m labcem.gui
if errorlevel 1 (
  echo.
  echo LabCEM GUI failed to start. Press any key to close.
  pause >nul
)
endlocal
