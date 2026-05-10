@echo off
setlocal
cd /d D:\Code\CEM_Test\LabCEM_SDF
call D:\Code\CEM_Test\LabCEM_SDF\.venv\Scripts\activate.bat
python main.py
if errorlevel 1 (
  echo.
  echo LabCEM_SDF failed to start. Press any key to close.
  pause >nul
)
endlocal
