#!/usr/bin/env python3
"""
Script para empaquetar el instalador en un ZIP listo para enviar
"""

import os
import sys
import zipfile
from pathlib import Path
from datetime import datetime

def create_package_zip():
    """Crea un archivo ZIP con el instalador"""

    print("\n" + "="*60)
    print("  EMPAQUETADOR DE INSTALADOR - ACES CONTABILIDAD")
    print("="*60 + "\n")

    # Directorio actual
    current_dir = Path.cwd()

    # Verificar que el ejecutable existe
    exe_path = current_dir / 'dist' / 'ACES_Contabilidad.exe'
    if not exe_path.exists():
        print("✗ Error: ACES_Contabilidad.exe no encontrado")
        print(f"  Ejecuta primero: python create_installer.py")
        print(f"  Buscado en: {exe_path}")
        return False

    print(f"✓ Ejecutable encontrado: {exe_path.name}")
    print(f"  Tamaño: {exe_path.stat().st_size / (1024*1024):.1f} MB")

    # Archivos a incluir
    files_to_include = [
        ('dist/ACES_Contabilidad.exe', 'ACES_Contabilidad.exe'),
        ('install.bat', 'install.bat'),
        ('uninstall.bat', 'uninstall.bat'),
        ('README_INSTALACION.txt', 'README_INSTALACION.txt'),
        ('INSTALADOR.md', 'INSTALADOR.md'),
        ('config.py', 'config.py'),
    ]

    # Crear nombre del ZIP con fecha
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f'ACES_Contabilidad_Instalador_{timestamp}.zip'
    zip_path = current_dir / zip_filename

    print(f"\nCreando paquete: {zip_filename}\n")

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for source, arcname in files_to_include:
                full_source = current_dir / source

                if not full_source.exists():
                    print(f"! Archivo no encontrado (omitiendo): {source}")
                    continue

                zf.write(full_source, arcname=arcname)
                size = full_source.stat().st_size
                print(f"  ✓ {arcname:40s} ({size/(1024*1024):.1f} MB)")

        # Estadísticas del ZIP
        zip_size = zip_path.stat().st_size / (1024*1024)
        print(f"\n{'='*60}")
        print(f"✓ Paquete creado correctamente")
        print(f"\n📦 {zip_filename}")
        print(f"   Tamaño: {zip_size:.1f} MB")
        print(f"   Ubicación: {zip_path}\n")

        # Instrucciones
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("\n📋 Pasos para instalar en otra máquina:\n")
        print("1. Descarga el archivo ZIP")
        print("2. Extrae el contenido en cualquier carpeta")
        print("3. Ejecuta: install.bat")
        print("4. ¡Listo! La aplicación está instalada\n")

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"\n✓ Archivo listo para enviar")

        return True

    except Exception as e:
        print(f"\n✗ Error al crear el ZIP: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = create_package_zip()
    sys.exit(0 if success else 1)
