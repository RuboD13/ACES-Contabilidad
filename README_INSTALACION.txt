ACES CONTABILIDAD - MANUAL DE INSTALACION

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
- Si instalaste: C:\Archivos de programa\ACES_Contabilidadces.db
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
1. Elimina la carpeta: C:\Archivos de programa\ACES_Contabilidad2. Elimina acceso directo del Escritorio

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
