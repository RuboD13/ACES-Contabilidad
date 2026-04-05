@echo off
cd /d "%~dp0"
echo Iniciando ACES Contabilidad...
start "" "http://localhost:5000"
python app.py
pause
