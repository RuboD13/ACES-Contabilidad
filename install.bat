@echo off
setlocal enabledelayedexpansion

set APP_NAME=ACES Contabilidad
set APP_DIR=%ProgramFiles%\ACES_Contabilidad
set EXE_NAME=ACES_Contabilidad.exe
set SOURCE_EXE=%~dp0dist\!EXE_NAME!

echo.
echo ========================================================
echo   Instalador de %APP_NAME%
echo ========================================================
echo.

if not exist "!SOURCE_EXE!" (
    echo ERROR: Ejecutable no encontrado
    echo.
    echo Ubicacion esperada: !SOURCE_EXE!
    echo.
    pause
    exit /b 1
)

echo Creando directorio de instalacion...
if not exist "!APP_DIR!" mkdir "!APP_DIR!"

echo Copiando ejecutable...
copy /Y "!SOURCE_EXE!" "!APP_DIR!\!EXE_NAME!" >nul

if !errorlevel! equ 0 (
    echo [OK] Ejecutable copiado correctamente
) else (
    echo [ERROR] No se pudo copiar el ejecutable
    pause
    exit /b 1
)

echo.
echo Creando acceso directo en Escritorio...
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT=!DESKTOP!\%APP_NAME%.lnk

powershell -NoProfile -Command ^
    "$sh = New-Object -ComObject WScript.Shell; " ^
    "$sc = $sh.CreateShortcut('!SHORTCUT!'); " ^
    "$sc.TargetPath = '!APP_DIR!\!EXE_NAME!'; " ^
    "$sc.WorkingDirectory = '!APP_DIR!'; " ^
    "$sc.Save()" 2>nul

if exist "!SHORTCUT!" (
    echo [OK] Acceso directo creado en Escritorio
) else (
    echo ! No se pudo crear acceso directo (continuar anyway)
)

echo.
echo ========================================================
echo   Instalacion completada correctamente
echo ========================================================
echo.
echo Ubicacion: !APP_DIR!
echo Acceso directo: !SHORTCUT!
echo.
echo Puedes ejecutar la aplicacion desde:
echo - Escritorio (acceso directo)
echo - Archivo: !APP_DIR!\!EXE_NAME!
echo.
pause
