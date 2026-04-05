# 📦 ACES Contabilidad - Guía de Instalación

## 🎯 Descripción General

ACES Contabilidad es una aplicación de escritorio para la gestión de contabilidad de alquileres. Incluye todo lo necesario (Python, dependencias) en un único archivo ejecutable.

**Tamaño estimado del instalador:** 200-300 MB

---

## 🚀 Instalación en Otra Máquina

### Opción 1: Instalador Automático (Recomendado)

#### Paso 1: Preparar el instalador
```bash
# En tu máquina actual:
python create_installer.py
```

Esto genera:
- `dist/ACES_Contabilidad.exe` - Ejecutable standalone
- `install.bat` - Script de instalación automática
- `uninstall.bat` - Script de desinstalación
- `README_INSTALACION.txt` - Instrucciones de uso

#### Paso 2: Empaquetar para envío
```bash
# Crear un ZIP con todo lo necesario
# Incluir solo estos archivos:
# - dist/ACES_Contabilidad.exe
# - install.bat
# - uninstall.bat
# - README_INSTALACION.txt
# - config.py (contiene configuración por defecto)
```

#### Paso 3: Instalar en otra máquina
1. Descarga el ZIP enviado
2. Extrae el contenido en cualquier carpeta
3. Ejecuta `install.bat`
4. La aplicación se instalará automáticamente en:
   ```
   C:\Archivos de programa\ACES_Contabilidad\
   ```

---

### Opción 2: Ejecutable Directo (Sin Instalador)

Si no deseas usar el instalador:

1. Copia `dist/ACES_Contabilidad.exe` a otra máquina
2. Ejecuta el archivo directamente
3. ¡Listo! No requiere instalación adicional

**Ventaja:** Muy portátil, puedes ejecutarlo desde USB
**Desventaja:** No crea accesos directos ni instala archivos del sistema

---

## 📂 Estructura de Archivos

Después de instalar, la estructura es:

```
C:\Archivos de programa\ACES_Contabilidad\
├── ACES_Contabilidad.exe          # Ejecutable principal
└── aces.db                        # Base de datos (se crea en primer uso)
```

Los datos se almacenan en `aces.db`. Se recomienda hacer backups.

---

## 🔧 Requisitos del Sistema

| Requisito | Mínimo | Recomendado |
|-----------|--------|------------|
| Windows | 7 SP1 | 10/11 |
| RAM | 2 GB | 4 GB |
| Disco | 500 MB | 1 GB |
| CPU | Dual-core | Dual-core+ |
| Navegador | Incluido | Edge/Chrome |

**Nota:** Python y dependencias están incluidas en el ejecutable.

---

## 🌐 Acceso a la Aplicación

Una vez instalada, la aplicación se abre automáticamente en:
```
http://localhost:5000
```

### Acceso Manual
- **Escritorio:** Doble-clic en el acceso directo
- **Menú Inicio:** ACES Contabilidad
- **Directamente:** `C:\Archivos de programa\ACES_Contabilidad\ACES_Contabilidad.exe`

---

## 💾 Backup y Datos

### Ubicación de la Base de Datos
```
C:\Archivos de programa\ACES_Contabilidad\aces.db
```

### Hacer Backup
```bash
# Copia el archivo aces.db a un lugar seguro
# Por ejemplo: D:\Backups\aces_backup_2026_04.db
```

### Restaurar desde Backup
```bash
# Copia el backup anterior sobre el archivo actual
# Reinicia la aplicación
```

---

## 🔄 Actualización

Para actualizar a una versión más nueva:

1. Ejecuta `uninstall.bat` (conserva los datos)
2. Descarga la nueva versión
3. Ejecuta el nuevo `install.bat`
4. La base de datos se conservará automáticamente

---

## ❌ Desinstalación

Para desinstalar completamente:

1. Ejecuta `uninstall.bat`
2. O manualmente:
   - Elimina `C:\Archivos de programa\ACES_Contabilidad\`
   - Elimina acceso directo del Escritorio
   - Elimina acceso directo del Menú Inicio

**Nota:** Tu base de datos `aces.db` se conservará si copias el archivo antes.

---

## 🐛 Solución de Problemas

### Problema: "Puerto 5000 ya está en uso"
**Solución:** La aplicación automáticamente busca otro puerto disponible.

### Problema: "El ejecutable no se abre"
**Solución:**
- Intenta ejecutar como Administrador
- Verifica espacio en disco (500 MB mínimo)
- Asegúrate de descargar todo el ZIP

### Problema: "No puedo acceder a localhost:5000"
**Solución:**
- Abre `http://127.0.0.1:5000` manualmente en tu navegador
- Verifica que la aplicación está ejecutándose (icono en bandeja)
- Intenta reiniciar la aplicación

### Problema: "Los datos no se guardan"
**Solución:**
- Verifica permisos de escritura en `C:\Archivos de programa\ACES_Contabilidad\`
- Intenta ejecutar como Administrador
- Verifica espacio disponible en el disco

### Problema: "Antivirus bloquea el archivo"
**Solución:**
- El archivo es seguro (creado con PyInstaller)
- Agrega a excepciones del antivirus
- Ejecuta desde carpeta de confianza

---

## 📝 Notas Técnicas

### Qué incluye el ejecutable
- Python 3.x embebido
- Flask 3.1
- Pandas y NumPy
- SQLite
- Todos los módulos necesarios

### Cómo se genera
```bash
# Comando utilizado:
pyinstaller --onefile --windowed \
  --add-data templates:templates \
  --add-data static:static \
  --collect-all=flask \
  app.py
```

### Tamaño
- Ejecutable: 200-300 MB (primera ejecución)
- Base de datos: ~5-50 MB (depende de datos)
- Total instalado: ~250-350 MB

---

## 🔐 Seguridad

- **Datos locales:** Todo se almacena en SQLite local (no cloud)
- **Puerto:** Solo accesible en `localhost` (máquina local)
- **Privacidad:** Ningún dato se envía a internet
- **Cifrado:** Los datos están en formato SQLite estándar

---

## 📞 Soporte

Para problemas o sugerencias:
1. Verifica el archivo `README_INSTALACION.txt`
2. Consulta el registro de acciones en la aplicación (Opciones)
3. Intenta desinstalar y reinstalar si los problemas persisten

---

## ✅ Checklist de Instalación

- [ ] Archivo `ACES_Contabilidad.exe` presente
- [ ] `install.bat` presente
- [ ] `README_INSTALACION.txt` presente
- [ ] Ejecutado `install.bat` en máquina destino
- [ ] Acceso directo creado en Escritorio
- [ ] Aplicación abre en `http://localhost:5000`
- [ ] Base de datos `aces.db` creada
- [ ] Primeros datos importados correctamente

---

**Versión:** 1.0
**Fecha:** Abril 2026
**Licencia:** Uso interno - ACES Alquiler
