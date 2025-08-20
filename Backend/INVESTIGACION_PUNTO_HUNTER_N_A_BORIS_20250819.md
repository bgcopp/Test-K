# INVESTIGACIÓN CRÍTICA: ¿Por qué algunos registros muestran "N/A" en Punto HUNTER?

**Fecha:** 2025-08-19  
**Investigador:** Claude Code para Boris  
**Problema:** Registros con celda 56124 muestran "N/A" cuando deberían mostrar datos HUNTER

## PROBLEMA IDENTIFICADO

### Caso específico analizado:
- **Número objetivo:** 3009120093
- **Registro problemático:** celda_destino = 56124 
- **Registro funcionando:** celda_destino = 51438

### Datos de la base de datos:

```sql
-- Registro 1: FUNCIONA CORRECTAMENTE
numero_origen: 3009120093
numero_destino: 3143067409  
celda_origen: 22504
celda_destino: 51438
punto_hunter_origen: "CARRERA 17 N° 71 A SUR"
punto_hunter_destino: "CARRERA 17 N° 71 A SUR"

-- Registro 2: MUESTRA "N/A" EN FRONTEND
numero_origen: 3009120093
numero_destino: 3142071141
celda_origen: 56121
celda_destino: 56124  
punto_hunter_origen: NULL (celda 56121 NO existe en cellular_data)
punto_hunter_destino: "CARRERA 17 N° 71 A SUR" (celda 56124 SÍ existe)
```

### Verificación en cellular_data:
```sql
-- ✅ EXISTE
SELECT * FROM cellular_data WHERE cell_id = '56124';
-- Resultado: 33|mission_MPFRBNsb|32|CARRERA 17 N° 71 A SUR|4.55038|-74.13705|732101|CLARO|-73|GSM|56124|...

-- ✅ EXISTE  
SELECT * FROM cellular_data WHERE cell_id = '51438';
-- Resultado: 40|mission_MPFRBNsb|32|CARRERA 17 N° 71 A SUR|4.55038|-74.13705|732101|CLARO|-55|UMTS|51438|...

-- ❌ NO EXISTE
SELECT * FROM cellular_data WHERE cell_id = '56121';
-- Resultado: (vacío)
```

## ROOT CAUSE DEL PROBLEMA

**CÓDIGO PROBLEMÁTICO en `Backend/main.py` línea ~1830:**

```sql
LEFT JOIN cellular_data cd_origen ON (cd_origen.cell_id = ocd.celda_origen AND cd_origen.mission_id = ocd.mission_id)
LEFT JOIN cellular_data cd_destino ON (cd_destino.cell_id = ocd.celda_destino AND cd_destino.mission_id = ocd.mission_id)
```

El endpoint retorna:
- `punto_hunter_origen`: NULL (porque celda 56121 no existe)
- `punto_hunter_destino`: "CARRERA 17 N° 71 A SUR" (porque celda 56124 sí existe)

**PROBLEMA EN EL FRONTEND:**
El frontend está usando una lógica incorrecta que prioriza `punto_hunter_origen` o está usando el campo equivocado, mostrando "N/A" en lugar de usar `punto_hunter_destino` cuando `punto_hunter_origen` es NULL.

## SOLUCIÓN TÉCNICA REQUERIDA

### Opción 1: Corregir endpoint (RECOMENDADO)
Modificar la query para incluir un campo unificado `punto_hunter`:

```sql
-- Agregar campo calculado que priorice destino sobre origen
COALESCE(cd_destino.punto, cd_origen.punto) as punto_hunter,
COALESCE(cd_destino.lat, cd_origen.lat) as lat_hunter,
COALESCE(cd_destino.lon, cd_origen.lon) as lon_hunter
```

### Opción 2: Corregir frontend
Modificar la lógica del frontend para usar `punto_hunter_destino` cuando `punto_hunter_origen` sea null.

### Opción 3: Documentar comportamiento actual
Clarificar en la documentación que se muestran ambos campos y cuál se prioriza.

## IMPACTO

- **Registros afectados:** Todas las llamadas donde `celda_origen` no tiene datos HUNTER pero `celda_destino` sí
- **Datos perdidos:** Información válida de puntos HUNTER que existe pero no se muestra
- **Experiencia de usuario:** Confusión por mostrar "N/A" cuando hay datos válidos disponibles

## INVESTIGACIÓN COMPLETA

### Consulta de verificación LEFT JOIN:
```sql
SELECT 
    ocd.numero_origen,
    ocd.numero_destino,
    ocd.celda_origen,
    ocd.celda_destino,
    cd_origen.punto AS punto_hunter_origen,
    cd_destino.punto AS punto_hunter_destino,
    cd_origen.cell_id AS cellular_cell_id_origen,
    cd_destino.cell_id AS cellular_cell_id_destino
FROM operator_call_data ocd
LEFT JOIN cellular_data cd_origen ON ocd.celda_origen = cd_origen.cell_id AND ocd.mission_id = cd_origen.mission_id
LEFT JOIN cellular_data cd_destino ON ocd.celda_destino = cd_destino.cell_id AND ocd.mission_id = cd_destino.mission_id
WHERE (ocd.numero_origen = '3009120093' OR ocd.numero_destino = '3009120093')
LIMIT 5;
```

### Resultados de investigación:
- La consulta LEFT JOIN funciona correctamente
- Los datos HUNTER existen para celda 56124
- El problema está en la interpretación/mostrado de estos datos en el frontend

## PRÓXIMOS PASOS

1. ✅ **COMPLETADO** - Identificar root cause
2. 🔄 **EN PROGRESO** - Implementar solución en endpoint
3. ⏳ **PENDIENTE** - Verificar funcionamiento correcto
4. ⏳ **PENDIENTE** - Documentar cambios realizados

## ARCHIVOS INVOLUCRADOS

- `Backend/main.py` - Endpoint `get_call_interactions` (línea ~1830)
- `Backend/kronos.db` - Tablas `operator_call_data` y `cellular_data`
- Frontend - Componente que muestra los datos HUNTER

---

**CONCLUSIÓN:** El problema está en que el frontend no maneja correctamente el caso donde `punto_hunter_origen` es NULL pero `punto_hunter_destino` tiene datos válidos. La solución más robusta es modificar el endpoint para proporcionar un campo unificado `punto_hunter` que priorice el primer valor disponible.