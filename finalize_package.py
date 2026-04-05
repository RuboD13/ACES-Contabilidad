#!/usr/bin/env python3
"""
Script final para empaquetar todo en un ZIP listo para distribuir
Se ejecuta automaticamente cuando build_exe.py termina
"""

import os
import sys
import zipfile
from pathlib import Path
from datetime import datetime

def main():
    """Crea el paquete ZIP final"""

    print("\n" + "="*60)
    print("FINALIZADOR DE PAQUETE - ACES CONTABILIDAD")
    print("="*60 + "\n")

    project_dir = Path.cwd()

    # Verificar que el exe existe
    exe_path = project_dir / 'dist' / 'ACES_Contabilidad.exe'
    if not exe_path.exists():
        print("ERROR: Ejecutable no encontrado")
        print(f"Esperado en: {exe_path}")
        return False

    exe_size_mb = exe_path.stat().st_size / (1024*1024)
    print(f"[OK] Ejecutable encontrado: {exe_size_mb:.1f} MB")

    # Archivos a incluir en el ZIP
    files_to_zip = [
        ('dist/ACES_Contabilidad.exe', 'ACES_Contabilidad.exe'),
        ('install.bat', 'install.bat'),
        ('uninstall.bat', 'uninstall.bat'),
        ('README_INSTALACION.txt', 'README_INSTALACION.txt'),
        ('INSTALADOR.md', 'INSTALADOR.md'),
        ('GUIA_DISTRIBUCION.md', 'GUIA_DISTRIBUCION.md'),
        ('config.py', 'config.py'),
    ]

    # Crear ZIP
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_name = f'ACES_Contabilidad_Instalador_{timestamp}.zip'
    zip_path = project_dir / zip_name

    print(f"\n[INFO] Creando paquete: {zip_name}\n")

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for source_path, zip_path_name in files_to_zip:
                full_path = project_dir / source_path

                if not full_path.exists():
                    print(f"  SKIP: {source_path} (no encontrado)")
                    continue

                zf.write(full_path, arcname=zip_path_name)

                if full_path.stat().st_size > 1024*1024:
                    size_str = f"{full_path.stat().st_size / (1024*1024):.1f} MB"
                else:
                    size_str = f"{full_path.stat().st_size / 1024:.1f} KB"

                print(f"  [OK] {zip_path_name:40s} ({size_str})")

        # Info del ZIP
        zip_final_size_mb = zip_path.stat().st_size / (1024*1024)

        print(f"\n" + "="*60)
        print(f"PAQUETE CREADO CORRECTAMENTE")
        print(f"="*60)
        print(f"""
Archivo: {zip_name}
Tamano: {zip_final_size_mb:.1f} MB
Ubicacion: {zip_path}

INSTRUCCIONES PARA DISTRIBUIR:

1. Enviar el archivo ZIP a:
   - Email (si soporta 200+ MB)
   - Google Drive / OneDrive
   - WeTransfer u otro servicio
   - USB o DVD

2. El usuario debera:
   a) Descargar el ZIP
   b) Extraer el contenido
   c) Ejecutar install.bat
   d) Seguir las instrucciones en pantalla

3. Incluir nota sobre:
   - Ejecutar como Administrador si es necesario
   - La instalacion puede tardar unos minutos
   - Se creara un acceso directo en Escritorio

CONTENIDO DEL ZIP:

- ACES_Contabilidad.exe (~250 MB)
  Ejecutable principal con Python incluido

- install.bat
  Script que instala automaticamente

- uninstall.bat
  Script para desinstalar

- README_INSTALACION.txt
  Manual de instalacion y uso

- INSTALADOR.md
  Documentacion completa del instalador

- GUIA_DISTRIBUCION.md
  Guia para distribuir a otros usuarios

PROXIMOS PASOS:

1. Prueba el instalador en tu maquina:
   - Copia install.bat a otra carpeta
   - Ejecuta install.bat
   - Verifica que funciona correctamente

2. Comparte el ZIP con el destinatario

3. Proporciona soporte si es necesario

""")

        return True

    except Exception as e:
        print(f"\nERROR al crear ZIP: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
