#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear el instalador .exe de ACES Contabilidad
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def print_section(text):
    """Imprime seccion del log"""
    print("\n" + "="*60)
    print("  " + text)
    print("="*60 + "\n")

def main():
    """Funcion principal"""
    print_section("GENERADOR DE INSTALADOR - ACES CONTABILIDAD")

    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    print(f"Directorio: {project_dir}\n")

    # Verificar requisitos
    print_section("Verificando requisitos")

    required = ['flask', 'pandas', 'pyinstaller']
    for package in required:
        try:
            __import__(package)
            print(f"  [OK] {package}")
        except ImportError:
            print(f"  [NO] {package} - instalando...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', package])

    # Limpiar builds anteriores
    print_section("Limpiando directorios previos")

    for dirname in ['build', 'dist']:
        if os.path.isdir(dirname):
            shutil.rmtree(dirname)
            print(f"  Eliminado: {dirname}")

    for filename in os.listdir('.'):
        if filename.endswith('.spec'):
            os.remove(filename)
            print(f"  Eliminado: {filename}")

    # Crear ejecutable
    print_section("Creando ejecutable con PyInstaller")

    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name=ACES_Contabilidad',
        '--distpath=dist',
        '--buildpath=build',
        '--add-data=templates:templates',
        '--add-data=static:static',
        '--add-data=database:database',
        '--add-data=modules:modules',
        '--add-data=routes:routes',
        '--add-data=config.py:.',
        '--collect-all=flask',
        '--collect-all=pandas',
        '--console',
        'app.py'
    ]

    print("Ejecutando PyInstaller...\n")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("\n[ERROR] No se pudo crear el ejecutable")
        return False

    # Crear install.bat
    print_section("Creando script de instalacion")

    install_script = """@echo off
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
    pause
    exit /b 1
)

echo Creando directorio de instalacion...
if not exist "!APP_DIR!" mkdir "!APP_DIR!"

echo Copiando ejecutable...
copy /Y "!SOURCE_EXE!" "!APP_DIR!\\!EXE_NAME!" >nul

if !errorlevel! equ 0 (
    echo [OK] Ejecutable copiado
) else (
    echo [ERROR] Fallo al copiar
    pause
    exit /b 1
)

echo Creando acceso directo...
set DESKTOP=%USERPROFILE%\\Desktop
set SHORTCUT=!DESKTOP!\\%APP_NAME%.lnk

powershell -Command "^
    $shell = New-Object -ComObject WScript.Shell; ^
    $sc = $shell.CreateShortcut('!SHORTCUT!'); ^
    $sc.TargetPath = '!APP_DIR!\\!EXE_NAME!'; ^
    $sc.WorkingDirectory = '!APP_DIR!'; ^
    $sc.Save()" 2>nul

echo.
echo ========================================================
echo   Instalacion completada
echo ========================================================
echo.
echo Ubicacion: !APP_DIR!
echo.
pause
"""

    with open('install.bat', 'w') as f:
        f.write(install_script)
    print("  [OK] install.bat creado")

    # Crear uninstall.bat
    uninstall_script = """@echo off
setlocal enabledelayedexpansion

set APP_NAME=ACES Contabilidad
set APP_DIR=%ProgramFiles%\\ACES_Contabilidad
set DESKTOP=%USERPROFILE%\\Desktop
set SHORTCUT=!DESKTOP!\\%APP_NAME%.lnk

echo.
echo Desinstalando %APP_NAME%...
echo.

if exist "!SHORTCUT!" del /q "!SHORTCUT!" 2>nul
if exist "!APP_DIR!" rmdir /s /q "!APP_DIR!" 2>nul

echo.
echo Desinstalacion completada
echo.
pause
"""

    with open('uninstall.bat', 'w') as f:
        f.write(uninstall_script)
    print("  [OK] uninstall.bat creado")

    # Crear README
    readme = """ACES CONTABILIDAD - MANUAL DE INSTALACION

REQUISITOS:
- Windows 7 o superior
- 500 MB espacio en disco
- Permisos de administrador (para instalar)

INSTALACION:

Opcion 1 - Instalador automatico (recomendado):
1. Ejecuta: install.bat
2. La app se instalara en C:\\Archivos de programa\\ACES_Contabilidad
3. Se creara un acceso directo en el Escritorio

Opcion 2 - Ejecucion directa:
1. Ejecuta directamente: dist/ACES_Contabilidad.exe
2. No requiere instalacion previa

DATOS:
- Los datos se almacenan en aces.db
- Se conservan entre sesiones
- Se recomienda hacer backups regularmente

DESINSTALACION:
- Ejecuta: uninstall.bat

ACCESO:
- La aplicacion se abre en: http://localhost:5000
- Si el puerto 5000 esta ocupado, buscara otro disponible

SOLUCION DE PROBLEMAS:
- Si falla, ejecuta como Administrador
- Verifica que haya 500 MB libres
- Cierra antivirus temporalmente si es necesario

Version 1.0
ACES Alquiler - Abril 2026
"""

    with open('README_INSTALACION.txt', 'w') as f:
        f.write(readme)
    print("  [OK] README_INSTALACION.txt creado")

    # Resumen final
    print_section("Instalador creado correctamente")

    print("""
ARCHIVOS GENERADOS:

1. dist/ACES_Contabilidad.exe (200-300 MB)
   - Ejecutable standalone
   - Incluye Python y dependencias

2. install.bat
   - Instala automaticamente

3. uninstall.bat
   - Desinstala la aplicacion

4. README_INSTALACION.txt
   - Manual de uso

PROXIMOS PASOS:

Para instalar en otro dispositivo:
1. Copia todo el contenido (o crea ZIP)
2. En otra maquina, ejecuta: install.bat
3. Automaticamente se instalara

Para usar directamente sin instalar:
1. Copia dist/ACES_Contabilidad.exe
2. Ejecutalo en cualquier maquina
3. Listo!

CREAR PAQUETE ZIP:
1. Selecciona: install.bat, uninstall.bat,
              README_INSTALACION.txt, dist/ACES_Contabilidad.exe
2. Crea un ZIP
3. Envia el ZIP

VERIFICACION:
- Ejecuta el .exe
- Deberia abrirse en http://localhost:5000
- Carga un archivo CSV para probar

""")

    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
