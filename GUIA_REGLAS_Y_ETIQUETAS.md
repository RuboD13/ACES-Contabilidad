# Guía de Reglas y Etiquetas — ACES Contabilidad

## ¿Qué diferencia hay entre una Regla y una Etiqueta?

| | Reglas de Categorización | Etiquetas de Usuario |
|---|---|---|
| **Aplicación** | Automática al importar | Manual (o futura auto-aplicación) |
| **Resultado** | Categoría única por transacción | Múltiples etiquetas por transacción |
| **Quién las crea** | Sistema + usuario | Usuario |
| **Palabras clave** | Obligatorias | Opcionales |
| **Uso típico** | Clasificar tipo de ingreso/gasto | Marcar para seguimiento fiscal, por inmueble, por propietario |

---

## 1. Reglas de Categorización

Las reglas categorizan transacciones **automáticamente** al importar un extracto CSV. El motor compara el texto del concepto con las palabras clave de cada regla, en orden de prioridad.

### Cómo funcionan

1. Al importar un CSV, cada transacción pasa por el motor de categorización
2. Las reglas se ordenan por prioridad (número menor = mayor prioridad)
3. La primera regla cuyas palabras clave coincidan con el concepto "gana"
4. Si ninguna coincide, la transacción queda como `sin_categoria`

### Sistema de prioridades

- **P10–P30**: Reglas muy específicas (ej. honorarios, nóminas, marketing)
- **P40–P60**: Reglas de categorías claras (ej. gestoría, seguros, liquidaciones)
- **P70–P89**: Reglas generales secundarias
- **P90–P99**: Comodines (ej. "Otros Ingresos", "Otros Gastos")

### Override manual

Si corriges la categoría de una transacción a mano, queda marcada con el icono ✏️ y **no se sobreescribe** al reaplicar reglas.

### Reaplicar reglas

Tras crear o modificar una regla, pulsa **Reaplicar período** para recategorizar el período activo sin perder correcciones manuales. Usa **Aplicar a todos** para recategorizar todos los períodos.

---

## 2. Reglas predefinidas del sistema

### Ingresos

| Clave | Etiqueta | Prioridad |
|-------|----------|-----------|
| `honorarios_gestion` | Honorarios Gestión Integral | P10 |
| `renta_inquilinos` | Renta de Inquilinos (tránsito) | P15 |
| `busqueda_inquilinos` | Búsqueda de Inquilinos | P20 |
| `fee_garantia` | Fee Garantía de Pago | P30 |
| `fee_suministros` | Fee Gestión Suministros | P40 |
| `fee_reparaciones` | Fee Reparaciones | P50 |
| `otros_ingresos` | Otros Ingresos | P90 |

### Gastos

| Clave | Etiqueta | Prioridad |
|-------|----------|-----------|
| `nominas` | Nóminas y Personal | P10 |
| `marketing` | Marketing y Publicidad | P20 |
| `software` | Software y Suscripciones | P30 |
| `gestoria` | Gestoría y Asesoría Legal | P40 |
| `seguros` | Seguros | P50 |
| `liquidacion_propietarios` | **Liquidación a Propietarios** | **P55** |
| `comisiones_banco` | Comisiones Bancarias | P60 |
| `otros_gastos` | Otros Gastos | P95 |

---

## 3. Nueva categoría: Liquidación a Propietarios

**Clave:** `liquidacion_propietarios`
**Tipo:** Gasto
**Color:** Púrpura (#9333ea)
**Prioridad:** P55

### ¿Para qué sirve?

Captura las **transferencias de dinero que ACES facilita a cada propietario** — el importe de la renta cobrada al inquilino, descontada la comisión de gestión.

### Palabras clave predefinidas

```
liquidacion, liquidación, pago propietario, transferencia propietario,
abono propietario, dinero propietario, liquidacion propietario, liquidación propietario
```

### Ejemplo de uso

```
Concepto en extracto: "Liquidación Propietario Marzo - C/ Mayor 5"
→ Categoría automática: Liquidación a Propietarios (P55)
```

> **Consejo:** Si tus transferencias a propietarios usan un texto específico en el extracto (ej. el nombre del propietario), añade esa palabra clave a esta regla desde el modal de edición.

---

## 4. Etiquetas de Usuario

Las etiquetas son **marcas personalizadas** que puedes aplicar a transacciones individuales. A diferencia de las categorías, una transacción puede tener **múltiples etiquetas**.

### Cuándo usar etiquetas

- **Marcado fiscal:** `IVA deducible`, `IRPF 15%`, `Mod. 303 T1`
- **Por inmueble:** `Calle Mayor 5`, `Piso 3B`, `Local Comercial`
- **Por propietario:** `García López`, `Martínez Ruiz`
- **Estado:** `Revisado`, `Facturado`, `Pendiente`

### Cómo crear una etiqueta

1. Ve a **Reglas y Etiquetas** → click en **Gestionar etiquetas**
2. Pulsa **+ Nueva etiqueta**
3. Rellena:
   - **Nombre:** nombre visible de la etiqueta
   - **Color:** selecciona uno de los 8 colores disponibles
   - **Palabras clave** *(opcional)*: términos para identificación futura
   - **Aplicar automáticamente** *(opcional)*: reservado para uso futuro
4. Pulsa **Crear**

### Cómo asignar etiquetas a una transacción

1. Ve a **Transacciones**
2. Haz click en cualquier transacción para abrir el detalle
3. En la sección **Etiquetas**, selecciona/deselecciona las que quieras
4. Los cambios se guardan al momento

---

## 5. Interfaz de Chips (Palabras Clave)

La interfaz de palabras clave usa **cajetines individuales** en lugar de texto separado por comas. Cada palabra clave es un chip independiente que puedes añadir o eliminar.

### Cómo añadir palabras clave

**Opción A — Tecla Enter:**
```
1. Escribe la palabra clave en el campo
2. Pulsa Enter
3. La palabra clave se convierte en chip
```

**Opción B — Coma:**
```
1. Escribe la palabra clave
2. Pulsa coma (,)
3. La palabra clave se convierte en chip automáticamente
```

**Opción C — Botón +:**
```
1. Escribe la palabra clave
2. Pulsa el botón + al final del campo
```

### Cómo eliminar palabras clave

Haz click en la **× del chip** que quieras eliminar.

### Reglas de validación

- Las palabras clave se normalizan a **minúsculas**
- No se permiten **duplicados** (si ya existe, se ignora)
- Se eliminan **espacios** al inicio y al final

---

## 6. Ejemplos Prácticos

### Crear una regla para pagos de plataforma

```
Tipo: Gasto
Clave: fee_plataforma
Etiqueta: Fee Plataforma Digital
Palabras clave: [fee plataforma] [comision plataforma] [plataforma gestion]
Prioridad: 35
```

### Crear etiqueta por propietario

```
Nombre: García López (Propietario)
Color: Cian
Palabras clave: [garcía] [garcia lopez]
```
→ Aplica esta etiqueta manualmente a las liquidaciones de ese propietario para tener su resumen filtrado.

### Filtrar transacciones por etiqueta

1. Ve a **Transacciones**
2. En la barra de filtros, despliega **Etiqueta**
3. Selecciona la etiqueta que quieras ver
4. La tabla muestra solo las transacciones etiquetadas

---

## 7. Troubleshooting

### La regla no categoriza las transacciones

- ✅ Comprueba que la regla está **activa** (no desactivada)
- ✅ Verifica que las palabras clave coincidan con el texto exacto del concepto en el extracto
- ✅ La búsqueda ignora mayúsculas/minúsculas y acentos
- ✅ Si la transacción fue corregida manualmente, **no se sobreescribirá**; edítala directamente
- ✅ Reaaplica las reglas tras modificarlas

### Una palabra clave no coincide aunque parece correcta

- El motor normaliza acentos: `gestión` = `gestion`, `liquidación` = `liquidacion`
- Añade ambas variantes como precaución
- Comprueba que no hay espacios extra en la palabra clave

### Conflicto entre dos reglas

La regla con **menor número de prioridad** tiene preferencia. Si quieres que una regla más específica gane, bájale el número de prioridad.

### La etiqueta no aparece en el modal de transacción

- Recarga la página de Transacciones
- Comprueba que la etiqueta está asociada a la cuenta correcta (o sin cuenta específica)

---

## 8. Referencia rápida de atajos

| Acción | Cómo |
|--------|------|
| Nueva regla | Botón "+ Nueva regla" (arriba dcha.) |
| Gestionar etiquetas | Botón "Gestionar etiquetas" (arriba) |
| Añadir chip | Enter, Coma o botón + |
| Eliminar chip | Click en × del chip |
| Reaplicar reglas | Banner "¿Modificaste reglas?" → "Reaplicar período" |
| Reaplicar a todo | Banner "¿Modificaste reglas?" → "Aplicar a todos" |
| Editar regla | Icono ✏️ en la tarjeta de regla |
| Editar etiqueta | Icono ✏️ en la etiqueta |
| Asignar etiqueta | Click en transacción → sección Etiquetas |
| Filtrar por etiqueta | Transacciones → filtro "Etiqueta" |
