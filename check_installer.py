#!/usr/bin/env python3
"""
Script para verificar el estado de construcción del instalador
"""

import os
import sys
from pathlib import Path

def check_installer():
    """Verifica si el instalador está listo"""

    project_dir = Path.cwd()

    print("\n" + "="*60)
    print("  VERIFICADOR DE CONSTRUCCION")
    print("="*60 + "\n")

    # Archivos esperados
    expected_files = {
        'dist/ACES_Contabilidad.exe': 'Ejecutable principal',
        'install.bat': 'Script de instalacion',
        'uninstall.bat': 'Script de desinstalacion',
        'README_INSTALACION.txt': 'Manual de uso',
        'INSTALADOR.md': 'Documentacion',
        'config.py': 'Archivo de configuracion',
    }

    all_ready = True
    total_size = 0

    print("[VERIFICACION DE ARCHIVOS]:\n")
    for file_path, description in expected_files.items():
        full_path = project_dir / file_path

        if full_path.exists():
            size = full_path.stat().st_size
            if size > 1024*1024:  # Mayor a 1 MB
                size_str = f"{size / (1024*1024):.1f} MB"
            else:
                size_str = f"{size / 1024:.1f} KB"

            print(f"  [OK] {file_path:40s} ({size_str})")
            total_size += size
        else:
            print(f"  [NO] {file_path:40s} - FALTA")
            all_ready = False

    print(f"\nTamano total: {total_size / (1024*1024):.1f} MB")

    if all_ready:
        print("\n" + "="*60)
        print("  INSTALADOR LISTO")
        print("="*60)
        print("""
PROXIMOS PASOS:

1. Crear ZIP para distribucion:
   python package_installer.py

2. Compartir con el destinatario:
   - Archivo ZIP (~200 MB)
   - INSTALADOR.md (instrucciones)
   - README_INSTALACION.txt (manual)

3. En la maquina destino:
   - Extraer ZIP
   - Ejecutar: install.bat
   - Listo!

ALTERNATIVA - Ejecutable directo:
   Copia dist/ACES_Contabilidad.exe a una USB y ejecutalo
   en cualquier maquina (sin necesidad de instalar)
""")
        return True
    else:
        print("\n" + "="*60)
        print("  EN CONSTRUCCION")
        print("="*60)
        print("""
El instalador aun se esta generando.

Por favor espera:
- Primera vez: 30-60 minutos
- Verifica que Python sigue ejecutando
- Asegúrate de que hay 5+ GB libres en disco

Vuelve a ejecutar este script en unos minutos:
  python check_installer.py

O monitorea el archivo de log en:
  C:\\Users\\Ru\\AppData\\Local\\Temp\\claude\\...\\bzmg5kdr9.output
""")
        return False

if __name__ == '__main__':
    success = check_installer()
    sys.exit(0 if success else 1)
