@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Environnement Python introuvable. Consultez README.md pour installer le projet.
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "windows_app.py"
