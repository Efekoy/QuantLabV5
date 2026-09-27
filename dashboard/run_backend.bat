@echo off
cd /d "%~dp0.."
set "PYTHONPATH=%CD%\dashboard\.vendor;%CD%"
python -m uvicorn dashboard.backend.main:app --host 127.0.0.1 --port 8000
