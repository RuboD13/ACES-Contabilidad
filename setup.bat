@echo off
echo Instalando dependencias de ACES Contabilidad...
python -m ensurepip --upgrade
python -m pip install --upgrade pip
python -m pip install flask pandas
echo.
echo Instalacion completada. Ejecuta run.bat para iniciar la aplicacion.
pause
