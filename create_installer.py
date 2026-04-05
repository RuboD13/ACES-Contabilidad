#!/usr/bin/env python3
"""
Script para crear el instalador .exe de ACES Contabilidad
Genera un ejecutable standalone que incluye Python y todas las dependencias
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def print_header(text):
    """Imprime un encabezado formateado"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_requirements():
    """Verifica que estén instaladas las dependencias necesarias"""
    print_header("Verificando requisitos")

    required = ['flask', 'pandas', 'pyinstaller']
    missing = []

    for package in required:
        try:
            __import__(package)
            print(f"✓ {package} instalado")
        except ImportError:
            print(f"✗ {package} NO instalado")
            missing.append(package)

    if missing:
        print(f"\nInstalando paquetes faltantes: {', '.join(missing)}")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-q'
        ] + missing)
        print("Paquetes instalados correctamente")

    return True

def clean_build():
    """Limpia directorios previos de build"""
    print_header("Limpiando directorios previos")

    dirs_to_clean = ['build', 'dist', '__pycache__', '*.spec', '.eggs']

    for pattern in dirs_to_clean:
        if '*' in pattern:
            # Para patrones con wildcard
            if pattern == '*.spec':
                for f in Path('.').glob('*.spec'):
                    if f.name not in ['build_spec.py']:
                        f.unlink()
                        print(f"  Eliminado: {f.name}")
        else:
            # Para directorios
            if os.path.isdir(pattern):
                shutil.rmtree(pattern)
                print(f"  Eliminado: {pattern}/")

def create_executable():
    """Crea el ejecutable con PyInstaller"""
    print_header("Creando ejecutable con PyInstaller")

    # Preparar rutas
    current_dir = os.getcwd()
    print(f"Directorio de trabajo: {current_dir}")

    # Comando PyInstaller
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name=ACES_Contabilidad',
        '--distpath=dist',
        '--buildpath=build',
        '--specpath=.',
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

    print(f"\nEjecutando: {' '.join(cmd)}\n")

    try:
        subprocess.check_call(cmd)
        print("\n✓ Ejecutable creado correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error al crear el ejecutable: {e}")
        return False

def create_installer_script():
    """Crea un script batch para instalar la aplicación"""
    print_header("Creando script de instalación")

    installer_script = """@echo off
setlocal enabledelayedexpansion

REM Script de instalación para ACES Contabilidad
REM Copia el ejecutable a Archivos de programa y crea un acceso directo

set APP_NAME=ACES Contabilidad
set APP_DIR=%ProgramFiles%\\ACES_Contabilidad
set EXE_NAME=ACES_Contabilidad.exe
set SOURCE_EXE=%~dp0dist\\!EXE_NAME!

echo.
echo ========================================================
echo   Instalador de %APP_NAME%
echo ========================================================
echo.

REM Verificar que el ejecutable existe
if not exist "!SOURCE_EXE!" (
    echo ERROR: Ejecutable no encontrado en: !SOURCE_EXE!
    echo.
    echo Por favor, asegúrate de que has ejecutado:
    echo   python create_installer.py
    echo.
    pause
    exit /b 1
)

REM Crear directorio de instalación
echo Creando directorio de instalación...
if not exist "!APP_DIR!" (
    mkdir "!APP_DIR!"
    echo Directorio creado: !APP_DIR!
) else (
    echo Directorio ya existe: !APP_DIR!
)

REM Copiar ejecutable
echo Copiando ejecutable...
copy /Y "!SOURCE_EXE!" "!APP_DIR!\\!EXE_NAME!" >nul
if !errorlevel! equ 0 (
    echo ✓ Ejecutable copiado correctamente
) else (
    echo ✗ Error al copiar el ejecutable
    pause
    exit /b 1
)

REM Crear acceso directo en el Escritorio
echo Creando acceso directo en el Escritorio...
set DESKTOP=%USERPROFILE%\\Desktop
set SHORTCUT=!DESKTOP!\\%APP_NAME%.lnk

REM Crear acceso directo usando PowerShell
powershell -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; ^
    $Shortcut = $WshShell.CreateShortcut('!SHORTCUT!'); ^
    $Shortcut.TargetPath = '!APP_DIR!\\!EXE_NAME!'; ^
    $Shortcut.WorkingDirectory = '!APP_DIR!'; ^
    $Shortcut.IconLocation = '!APP_DIR!\\!EXE_NAME!'; ^
    $Shortcut.Save()" 2>nul

if exist "!SHORTCUT!" (
    echo ✓ Acceso directo creado en el Escritorio
) else (
    echo ! No se pudo crear acceso directo automáticamente
)

REM Crear acceso directo en Inicio
echo Creando acceso directo en Menú Inicio...
set START_MENU=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs
set START_SHORTCUT=!START_MENU!\\%APP_NAME%.lnk

powershell -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; ^
    $Shortcut = $WshShell.CreateShortcut('!START_SHORTCUT!'); ^
    $Shortcut.TargetPath = '!APP_DIR!\\!EXE_NAME!'; ^
    $Shortcut.WorkingDirectory = '!APP_DIR!'; ^
    $Shortcut.Save()" 2>nul

echo.
echo ========================================================
echo   Instalación completada
echo ========================================================
echo.
echo Ubicación: !APP_DIR!
echo.
echo Puedes ejecutar la aplicación desde:
echo   • Escritorio (acceso directo)
echo   • Menú Inicio
echo   • !APP_DIR!\\!EXE_NAME!
echo.
pause
"""

    with open('install.bat', 'w', encoding='utf-8') as f:
        f.write(installer_script)

    print("✓ Script de instalación creado: install.bat")

def create_readme():
    """Crea un archivo README con instrucciones"""
    print_header("Creando instrucciones de instalación")

    readme = """# ACES Contabilidad - Instalación

## Requisitos
- Windows 7 o superior
- 500 MB de espacio en disco
- Conexión a internet (opcional, solo para actualizaciones)

## Instalación Paso a Paso

### Opción 1: Instalador Automático (Recomendado)
1. Ejecuta `python create_installer.py` en este directorio
2. Ejecuta el archivo `install.bat` generado
3. La aplicación se instalará en `C:\\Archivos de programa\\ACES_Contabilidad`
4. Se crearán accesos directos en el Escritorio y Menú Inicio

### Opción 2: Ejecución Manual
1. Ejecuta `python create_installer.py` para crear el ejecutable
2. Navega a la carpeta `dist/`
3. Ejecuta `ACES_Contabilidad.exe`

## Uso

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:5000`

### Primeros pasos:
1. **Cargar CSV**: Ve a la sección "Cargar" y sube un extracto bancario en formato CSV
2. **Ver Dashboard**: Visualiza automáticamente los cuadres, métricas e ingresos
3. **Gestionar Transacciones**: Revisa y categoriza transacciones manualmente si es necesario
4. **Configurar Reglas**: Ajusta reglas de categorización automática en "Opciones"

## Características

- ✓ Cuadre automático de banco y caja
- ✓ Categorización automática por palabras clave
- ✓ Dashboard visual con gráficos en tiempo real
- ✓ Gestión de facturas
- ✓ Etiquetado flexible de transacciones
- ✓ Registro completo de acciones
- ✓ Exportación de datos a CSV
- ✓ Base de datos local SQLite

## Base de Datos

Los datos se almacenan en `aces.db` en el mismo directorio que la aplicación.
Se recomienda hacer copias de seguridad regularmente.

## Solución de Problemas

### Puerto 5000 ya está en uso
Si el puerto 5000 está ocupado, la aplicación intentará usar el siguiente puerto disponible.

### Problemas de rendimiento
- Cierra otras aplicaciones para liberar memoria
- Si hay muchas transacciones, considera dividirlas en períodos más pequeños

### Datos no se guardan
- Verifica permisos de escritura en el directorio de instalación
- Asegúrate de que no hay versiones conflictivas ejecutándose

## Contacto y Soporte

Para reportar problemas o sugerencias, documenta:
- La acción que estabas realizando
- El mensaje de error (si lo hay)
- Pasos para reproducir el problema

## Licencia

ACES Contabilidad - Sistema de contabilidad para alquileres
"""

    with open('README_INSTALACION.txt', 'w', encoding='utf-8') as f:
        f.write(readme)

    print("✓ Instrucciones creadas: README_INSTALACION.txt")

def create_uninstaller():
    """Crea un script desinstalador"""
    print_header("Creando script desinstalador")

    uninstaller = """@echo off
setlocal enabledelayedexpansion

REM Desinstalador para ACES Contabilidad

set APP_NAME=ACES Contabilidad
set APP_DIR=%ProgramFiles%\\ACES_Contabilidad
set DESKTOP=%USERPROFILE%\\Desktop
set SHORTCUT=!DESKTOP!\\%APP_NAME%.lnk
set START_MENU=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs
set START_SHORTCUT=!START_MENU!\\%APP_NAME%.lnk

echo.
echo ========================================================
echo   Desinstalador de %APP_NAME%
echo ========================================================
echo.
echo Esto eliminará la aplicación de tu sistema.
echo Tu base de datos (aces.db) se conservará.
echo.
set /p confirm="¿Deseas continuar? (S/N): "

if /i not "%confirm%"=="S" (
    echo Desinstalación cancelada
    exit /b 0
)

REM Eliminar accesos directos
echo Eliminando accesos directos...
if exist "!SHORTCUT!" del /q "!SHORTCUT!" 2>nul
if exist "!START_SHORTCUT!" del /q "!START_SHORTCUT!" 2>nul

REM Eliminar directorio de aplicación
echo Eliminando aplicación...
if exist "!APP_DIR!" (
    rmdir /s /q "!APP_DIR!" 2>nul
    echo ✓ Aplicación eliminada
) else (
    echo ! La aplicación no se encontró en !APP_DIR!
)

echo.
echo Desinstalación completada
echo.
pause
"""

    with open('uninstall.bat', 'w', encoding='utf-8') as f:
        f.write(uninstaller)

    print("✓ Desinstalador creado: uninstall.bat")

def main():
    """Función principal"""
    print("\n")
    print("=" * 60)
    print("  GENERADOR DE INSTALADOR - ACES CONTABILIDAD")
    print("=" * 60)

    try:
        # Cambiar a directorio de proyecto
        project_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(project_dir)
        print(f"\nDirectorio del proyecto: {project_dir}")

        # Verificar requisitos
        if not check_requirements():
            return False

        # Limpiar builds previos
        clean_build()

        # Crear ejecutable
        if not create_executable():
            print("\n✗ Error: No se pudo crear el ejecutable")
            print("Verifica que app.py existe y tiene la estructura correcta")
            return False

        # Crear scripts
        create_installer_script()
        create_uninstaller()
        create_readme()

        # Resumen final
        print_header("Instalador creado exitosamente")

        print("""
[ARCHIVOS GENERADOS]:

1. dist/ACES_Contabilidad.exe
   - Ejecutable standalone de la aplicacion
   - Incluye Python y todas las dependencias
   - Tamano: ~200-300 MB

2. install.bat
   - Script de instalacion automatica
   - Copia el ejecutable a Archivos de programa
   - Crea accesos directos en Escritorio y Menu Inicio

3. uninstall.bat
   - Script de desinstalacion
   - Elimina la aplicacion pero conserva la base de datos

4. README_INSTALACION.txt
   - Instrucciones detalladas de instalacion y uso

------------------------------------------------------------

[PROXIMOS PASOS]:

Para instalar en otro dispositivo:

1. Copia este directorio completo o crea un archivo ZIP

2. En la maquina destino, extrae el contenido

3. Ejecuta: install.bat

   Automaticamente:
   * Instalara en C:\\Archivos de programa\\ACES_Contabilidad
   * Creara accesos directos
   * Estara listo para usar

------------------------------------------------------------

[ALTERNATIVA - Ejecutable Directo]:

Si prefieres no usar el instalador, simplemente copia
dist/ACES_Contabilidad.exe a otro dispositivo y ejecutalo
directamente (sin instalacion).

------------------------------------------------------------
""")

        return True

    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
