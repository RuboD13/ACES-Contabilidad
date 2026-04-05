#!/usr/bin/env python3
"""
Crea los scripts batch e instrucciones para el instalador
"""

import os

def create_scripts():
    """Crea los scripts"""

    print("\n" + "="*60)
    print("CREANDO SCRIPTS DE INSTALACION")
    print("="*60 + "\n")

    # install.bat
    install_bat = """@echo off
setlocal enabledelayedexpansion

set APP_NAME=ACES Contabilidad
set APP_DIR=%ProgramFiles%\\ACES_Contabilidad
set EXE_NAME=ACES_Contabilidad.exe
set SOURCE_EXE=%~dp0dist\\!EXE_NAME!

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
copy /Y "!SOURCE_EXE!" "!APP_DIR!\\!EXE_NAME!" >nul

if !errorlevel! equ 0 (
    echo [OK] Ejecutable copiado correctamente
) else (
    echo [ERROR] No se pudo copiar el ejecutable
    pause
    exit /b 1
)

echo.
echo Creando acceso directo en Escritorio...
set DESKTOP=%USERPROFILE%\\Desktop
set SHORTCUT=!DESKTOP!\\%APP_NAME%.lnk

powershell -NoProfile -Command ^
    "$sh = New-Object -ComObject WScript.Shell; " ^
    "$sc = $sh.CreateShortcut('!SHORTCUT!'); " ^
    "$sc.TargetPath = '!APP_DIR!\\!EXE_NAME!'; " ^
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
echo - Archivo: !APP_DIR!\\!EXE_NAME!
echo.
pause
"""

    with open('install.bat', 'w') as f:
        f.write(install_bat)
    print("[OK] install.bat creado")

    # uninstall.bat
    uninstall_bat = """@echo off
setlocal enabledelayedexpansion

set APP_NAME=ACES Contabilidad
set APP_DIR=%ProgramFiles%\\ACES_Contabilidad
set DESKTOP=%USERPROFILE%\\Desktop
set SHORTCUT=!DESKTOP!\\%APP_NAME%.lnk

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
"""

    with open('uninstall.bat', 'w') as f:
        f.write(uninstall_bat)
    print("[OK] uninstall.bat creado")

    # README
    readme = """ACES CONTABILIDAD - MANUAL DE INSTALACION

========================================================
REQUISITOS DEL SISTEMA
========================================================

- Windows 7 SP1 o superior
- 500 MB de espacio en disco libre
- Permisos de Administrador (para instalar)
- Navegador web (Edge, Chrome, Firefox, etc.)

Nota: Python y dependencias estan incluidas en el instalador.

========================================================
INSTALACION
========================================================

OPCION 1 - INSTALADOR AUTOMATICO (RECOMENDADO)

1. Ejecuta: install.bat (como Administrador)
2. Espera a que finalice la instalacion
3. Se creara un acceso directo en el Escritorio
4. Haz doble clic en el acceso directo para iniciar

OPCION 2 - EJECUCION DIRECTA (SIN INSTALAR)

1. Ejecuta directamente: dist/ACES_Contabilidad.exe
2. No requiere instalacion previa
3. Los datos se guardaran en la misma carpeta

========================================================
USO DE LA APLICACION
========================================================

Una vez iniciada:
- Se abrira automaticamente en: http://localhost:5000
- Si no abre, ingresa manualmente en tu navegador
- Los datos se almacenan en aces.db

========================================================
DATOS Y BACKUPS
========================================================

Tu base de datos se guarda en:
- Si instalaste: C:\Archivos de programa\ACES_Contabilidad\aces.db
- Si ejecutas directo: Misma carpeta que ACES_Contabilidad.exe

RECOMENDACION: Hacer backups regularmente
- Copia aces.db a una carpeta segura
- Copia en cloud (Google Drive, OneDrive, etc.)

========================================================
DESINSTALACION
========================================================

Para desinstalar sin perder datos:
1. Ejecuta: uninstall.bat
2. Tu archivo aces.db se conservara (copia de seguridad)

Para desinstalar manualmente:
1. Elimina la carpeta: C:\Archivos de programa\ACES_Contabilidad\
2. Elimina acceso directo del Escritorio

========================================================
SOLUCION DE PROBLEMAS
========================================================

PROBLEMA: "El ejecutable no abre"
- Intenta ejecutar como Administrador
- Verifica espacio en disco (500+ MB)
- Actualiza Windows (puede necesitar parches)
- Desactiva temporalmente el antivirus

PROBLEMA: "Puerto 5000 ya esta en uso"
- La aplicacion buscara otro puerto automaticamente
- Si no abre, intenta manualmente en:
  http://localhost:5001
  http://localhost:5002
  etc.

PROBLEMA: "No puedo acceder a localhost:5000"
- Verifica que la aplicacion esta ejecutandose
- Prueba: http://127.0.0.1:5000
- Verifica que el navegador esta actualizado

PROBLEMA: "Los datos no se guardan"
- Verifica permisos de carpeta
- Intenta ejecutar como Administrador
- Verifica espacio en disco disponible
- Prueba desinstalar/reinstalar

========================================================
INFORMACION TECNICA
========================================================

Sistema: Windows (Python 3 embebido)
Aplicacion: Flask 3.1 + SQLite
Base de datos: aces.db (SQLite)
Puerto por defecto: 5000
Datos: Locales (sin conexion a internet requerida)

========================================================
SOPORTE
========================================================

Para mas informacion:
- Lee INSTALADOR.md (documentacion completa)
- Consulta GUIA_DISTRIBUCION.md (distribucion)

Para reportar problemas:
- Documenta los pasos que realizabas
- Incluye mensajes de error completos
- Verifica que tienes la ultima version

========================================================

Creado: Abril 2026
Version: 1.0
Producto: ACES Contabilidad
Empresa: ACES Alquiler
"""

    with open('README_INSTALACION.txt', 'w') as f:
        f.write(readme)
    print("[OK] README_INSTALACION.txt creado")

    print("\n" + "="*60)
    print("SCRIPTS CREADOS CORRECTAMENTE")
    print("="*60)
    return True

if __name__ == '__main__':
    create_scripts()
