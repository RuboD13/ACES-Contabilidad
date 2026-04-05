@echo off
setlocal enabledelayedexpansion

set APP_NAME=ACES Contabilidad
set APP_DIR=%ProgramFiles%\ACES_Contabilidad
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT=!DESKTOP!\%APP_NAME%.lnk

echo.
echo ========================================================
echo   Desinstalador de %APP_NAME%
echo ========================================================
echo.
echo Esto eliminara la aplicacion de tu sistema.
echo Tu base de datos (aces.db) sera conservada.
echo.

set /p confirm="Deseas continuar (S/N)? "

if /i not "%confirm%"=="S" (
    echo Desinstalacion cancelada
    exit /b 0
)

echo.
echo Eliminando acceso directo...
if exist "!SHORTCUT!" del /q "!SHORTCUT!" 2>nul

echo Eliminando aplicacion...
if exist "!APP_DIR!" (
    rmdir /s /q "!APP_DIR!" 2>nul
    echo [OK] Aplicacion eliminada
)

echo.
echo ========================================================
echo   Desinstalacion completada
echo ========================================================
echo.
pause
