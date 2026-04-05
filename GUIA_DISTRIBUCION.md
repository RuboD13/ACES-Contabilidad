# GUIA DE DISTRIBUCION - ACES Contabilidad

## Resumen Ejecutivo

Tu aplicación ACES Contabilidad se está empaquetando en un instalador `.exe` de forma automática. Este documento explica qué ocurre y cómo distribuir el resultado.

---

## Estado Actual

**Proceso en ejecución:** Generación del instalador
**Tiempo estimado:** 30-60 minutos (primera vez)
**Script activo:** `build_installer.py`

Cuando termine, encontrarás:
- ✓ `dist/ACES_Contabilidad.exe` (~250 MB) - El programa ejecutable
- ✓ `install.bat` - Script de instalación automática
- ✓ `uninstall.bat` - Script de desinstalación
- ✓ `README_INSTALACION.txt` - Manual para el usuario final

---

## ¿Qué es cada archivo?

### ACES_Contabilidad.exe
- Ejecutable único que contiene la aplicación completa
- Incluye Python 3, Flask, Pandas y todas las dependencias
- No requiere instalación previa de Python en la máquina destino
- Tamaño: 200-300 MB
- Funciona sin conexión a internet (excepto actualizaciones)

### install.bat
Script Windows que:
1. Copia el ejecutable a `C:\Archivos de programa\ACES_Contabilidad\`
2. Crea accesos directos en:
   - Escritorio
   - Menú Inicio
3. Automatiza todo lo necesario

### uninstall.bat
- Elimina la aplicación y accesos directos
- **Conserva la base de datos** (`aces.db`) para no perder datos
- Permite una reinstalación limpia si es necesario

---

## Método 1: Distribución por ZIP (Recomendado)

### Paso 1: Crear el paquete ZIP

Cuando el instalador esté listo, ejecuta:

```bash
python package_installer.py
```

Esto crea: `ACES_Contabilidad_Instalador_YYYYMMDD_HHMMSS.zip` (~200 MB)

### Paso 2: Enviar el ZIP

Opciones de envío:
- **Email:** Si el proveedor permite 200+ MB
- **Google Drive/Dropbox:** Compartir enlace
- **OneDrive:** Crear carpeta compartida
- **Servidor FTP:** Subir a servidor
- **USB/DVD:** Grabar el ZIP físicamente
- **Servicios de transferencia:** WeTransfer, Send.Firefox, etc.

### Paso 3: Instrucciones para el destinatario

Proporciona estas instrucciones:

```
1. Descarga el archivo ACES_Contabilidad_Instalador_*.zip
2. Extrae el contenido en cualquier carpeta
3. Abre la carpeta extraída
4. Haz doble clic en: install.bat
5. Sigue las instrucciones en pantalla
6. ¡Listo! Ejecuta la aplicación desde el Escritorio
```

---

## Método 2: Ejecutable Directo (Alternativa)

Si prefieres máxima simplecidad:

1. Copia solo: `dist/ACES_Contabilidad.exe`
2. Envía por email o URL
3. El usuario ejecuta directamente
4. **Ventaja:** Muy portátil
5. **Desventaja:** No crea accesos directos, datos en carpeta del exe

---

## Método 3: Instalación Manual

Para usuarios avanzados o sin scripts batch:

1. Envía: `dist/ACES_Contabilidad.exe`
2. Instruye:
   ```
   1. Copia el .exe a C:\Archivos de programa\
   2. Renombra la carpeta a "ACES_Contabilidad"
   3. Crea acceso directo en Escritorio
   4. Ejecuta
   ```

---

## Estructura Esperada del ZIP

Cuando ejecutes `package_installer.py`, contendrá:

```
ACES_Contabilidad_Instalador_20260404_123456.zip
├── ACES_Contabilidad.exe        (~250 MB)
├── install.bat                  (1 KB)
├── uninstall.bat                (1 KB)
├── README_INSTALACION.txt       (2 KB)
├── INSTALADOR.md                (6 KB)
└── config.py                    (6 KB)

Total: ~250 MB
```

---

## Verificación Antes de Enviar

Antes de distribuir, verifica en tu máquina:

```bash
python check_installer.py
```

Debería mostrar [OK] en todos los archivos.

Luego prueba ejecutando:
```
dist/ACES_Contabilidad.exe
```

Debe abrirse en http://localhost:5000 sin errores.

---

## Soporte Post-Distribución

### Si el usuario reporta problemas:

**"El .exe no se abre"**
- Ejecutar como Administrador
- Verificar espacio en disco (500+ MB)
- Descargar completamente el ZIP
- Ejecutar desde carpeta local (no USB ni Red)

**"install.bat no funciona"**
- Ejecutar como Administrador: Botón derecho > Ejecutar como admin
- Verificar que dist/ACES_Contabilidad.exe existe
- Actualizar Windows (puede necesitar parches)

**"Los datos se pierden"**
- Verificar que aces.db existe en la carpeta de instalación
- No mover la carpeta de instalación después de instalar
- Hacer backup de aces.db regularmente

**"Puerto 5000 ocupado"**
- Está documentado: la app buscará otro puerto automáticamente
- Si no abre, verificar que no hay otra instancia ejecutándose

---

## Actualizaciones Futuras

Para distribuir una versión nueva:

1. Edita el código
2. Ejecuta: `python build_installer.py` (nuevamente)
3. Ejecuta: `python package_installer.py`
4. Envía el nuevo ZIP con fecha en el nombre

Los usuarios simplemente desinstalan la versión vieja y instalan la nueva. Los datos se conservan.

---

## Notas Técnicas

### ¿Por qué 250 MB?

El ejecutable contiene:
- Python 3.x completo (120 MB)
- Dependencias (Flask, Pandas, etc.) (80 MB)
- Tu aplicación y datos estáticos (50 MB)

En máquinas donde ya está Python instalado, podría ser más pequeño, pero así garantizamos compatibilidad universal.

### ¿Es seguro?

- El .exe está firmado implícitamente por PyInstaller
- Se crea desde el código fuente visible
- No se modifica en tránsito
- El usuario puede inspeccionar el código si lo desea

### ¿Qué ocurre al ejecutarse?

1. Windows descomprime el ejecutable en temp
2. Se ejecuta Python embebido con tu app
3. Se abre el navegador en http://localhost:5000
4. Los datos se guardan en aces.db local

---

## Checklist Final

Antes de distribuir:

- [ ] Ejecuta: `python build_installer.py`
- [ ] Espera 30-60 minutos
- [ ] Verifica con: `python check_installer.py`
- [ ] Prueba ejecutando dist/ACES_Contabilidad.exe
- [ ] Prueba install.bat en una carpeta limpia
- [ ] Ejecuta: `python package_installer.py`
- [ ] Comprime/envía el ZIP resultante
- [ ] Proporciona README_INSTALACION.txt al usuario
- [ ] Documenta que ejecute como Administrador si hay problemas

---

## Comandos Útiles

```bash
# Generar instalador (primera vez, 30-60 min)
python build_installer.py

# Verificar estado
python check_installer.py

# Crear ZIP para distribuir
python package_installer.py

# Limpiar builds previos
rm -rf build dist *.spec

# Ejecutar la app para probar
dist/ACES_Contabilidad.exe
```

---

## Soporte Técnico

Si necesitas ayuda:

1. Verifica que Python está actualizado: `python --version`
2. Reinstala dependencias: `pip install -r requirements.txt`
3. Limpia y recompila: `rm -rf build dist && python build_installer.py`
4. Verifica espacio: Al menos 5 GB temporales + 500 MB destino

---

**Versión:** 1.0
**Creado:** Abril 2026
**Producto:** ACES Contabilidad v1.0
