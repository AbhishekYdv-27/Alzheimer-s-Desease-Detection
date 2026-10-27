@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"

start "Alzheimer API" cmd /k "python run_backend.py"
start "Alzheimer Frontend" cmd /k call "%~dp0frontend\start_frontend.bat"

exit /b 0
