#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build executable con PyInstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def build():
    """Construye el ejecutable"""

    print("\n" + "="*60)
    print("GENERADOR DE INSTALADOR - ACES CONTABILIDAD")
    print("="*60 + "\n")

    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    # Verificar que existen los archivos necesarios
    print("[1] Verificando archivos...")
    required = ['app.py', 'config.py', 'templates', 'static', 'database', 'modules', 'routes']
    for item in required:
        if not os.path.exists(item):
            print(f"  ERROR: No encontrado: {item}")
            return False
        print(f"  OK: {item}")

    # Limpiar builds anteriores
    print("\n[2] Limpiando directorios anteriores...")
    for dirname in ['build', 'dist']:
        if os.path.isdir(dirname):
            shutil.rmtree(dirname)
            print(f"  Eliminado: {dirname}/")

    for filename in os.listdir('.'):
        if filename.endswith('.spec'):
            os.remove(filename)
            print(f"  Eliminado: {filename}")

    # Crear el ejecutable
    print("\n[3] Creando ejecutable con PyInstaller...")

    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name=ACES_Contabilidad',
        '--distpath=dist',
        '--workpath=build',
        '--specpath=build_spec',
        '--add-data=templates:templates',
        '--add-data=static:static',
        '--add-data=database:database',
        '--add-data=modules:modules',
        '--add-data=routes:routes',
        '--add-data=config.py:.',
        '--collect-all=flask',
        '--collect-all=jinja2',
        '--collect-all=werkzeug',
        '--console',
        'app.py'
    ]

    print("  Ejecutando: PyInstaller...")
    print("  (Esto puede tomar 30-60 minutos)\n")

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("\n[ERROR] PyInstaller retorno error")
        return False

    # Verificar que se creo
    exe_path = os.path.join('dist', 'ACES_Contabilidad.exe')
    if not os.path.exists(exe_path):
        print(f"\n[ERROR] No se creo el ejecutable: {exe_path}")
        return False

    exe_size = os.path.getsize(exe_path) / (1024*1024)
    print(f"\n[OK] Ejecutable creado: {exe_size:.1f} MB")

    return True

if __name__ == '__main__':
    success = build()

    if success:
        print("\n" + "="*60)
        print("EXITO: Ejecutable generado correctamente")
        print("="*60)
        print("""
Ubicacion: dist/ACES_Contabilidad.exe

Proximos pasos:
1. Ejecuta: python create_scripts.py
   (Crea install.bat, uninstall.bat, etc.)

2. Prueba el ejecutable:
   dist/ACES_Contabilidad.exe

3. Crea el paquete ZIP:
   python package_installer.py
""")
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("ERROR: No se pudo generar el ejecutable")
        print("="*60)
        sys.exit(1)
