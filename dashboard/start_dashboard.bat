@echo off
setlocal
cd /d "%~dp0.."
if not exist "dashboard\.vendor\fastapi\__init__.py" (
  echo Installing Python dashboard dependencies...
  python -m pip install --target dashboard\.vendor -r dashboard\backend\requirements.txt || exit /b 1
)
if not exist "dashboard\frontend\node_modules\vite" (
  echo Installing frontend dependencies...
  pushd dashboard\frontend
  call npm install || exit /b 1
  popd
)
set "PYTHONPATH=%CD%\dashboard\.vendor;%CD%"
if not exist "dashboard\database\dashboard.sqlite3" (
  echo Importing V5.4 frozen artifacts...
  python -m dashboard.backend.import_lab --lab v5.4 || exit /b 1
)
start "QuantLab API" cmd /k call dashboard\run_backend.bat
start "QuantLab UI" cmd /k call dashboard\run_frontend.bat
timeout /t 3 >nul
start "" http://localhost:3000
echo QuantLab dashboard: http://localhost:3000
endlocal
