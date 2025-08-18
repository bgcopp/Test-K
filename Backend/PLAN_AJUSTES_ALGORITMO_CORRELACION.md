# PLAN DE AJUSTES - ALGORITMO DE CORRELACIÓN
## Análisis Profundo de Números Faltantes

**Fecha:** 15 de Agosto 2025  
**Solicitado por:** Boris  
**Números investigados:** 3224274851, 3208611034, 3104277553, 3102715509, 3143534707

---

## 🔍 DIAGNÓSTICO PRINCIPAL

### PROBLEMA IDENTIFICADO
Los números **SÍ EXISTEN** en la base de datos, pero están almacenados con **prefijo 57** (código de país Colombia).

**Evidencia encontrada:**
- `3224274851` → Encontrado como `573224274851` (4 registros)
- `3208611034` → Encontrado como `573208611034` (2 registros)  
- `3102715509` → Encontrado como `573102715509` (1 registro)
- `3143534707` → Encontrado como `573143534707` (7 registros)
- `3104277553` → **NO encontrado** (posiblemente error de datos)

### CAUSA RAÍZ
El algoritmo de normalización está **removiendo el prefijo 57** correctamente, pero la **búsqueda inicial** en `_extract_operator_numbers()` no está considerando esta normalización de manera bidireccional.

---

## 🛠️ PLAN DE AJUSTES

### AJUSTE 1: Mejorar Extracción de Números de Operadores
**Archivo:** `Backend/services/correlation_analysis_service.py`  
**Función:** `_extract_operator_numbers()`

**Problema actual:**
```python
# Busca solo el número exacto
WHERE numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?
```

**Solución:**
```python
# Buscar tanto formato original como normalizado
normalized_search = self._normalize_phone_number(search_number)
WHERE (numero_origen = ? OR numero_origen = ? OR 
       numero_destino = ? OR numero_destino = ? OR 
       numero_objetivo = ? OR numero_objetivo = ?)
```

### AJUSTE 2: Normalización Bidireccional
**Función:** `_normalize_phone_number()`

**Agregar variaciones de búsqueda:**
```python
def _get_number_variations(self, number: str) -> List[str]:
    """Generar variaciones de un número para búsqueda."""
    variations = [number]
    
    # Normalizado (sin 57)
    normalized = self._normalize_phone_number(number)
    if normalized != number:
        variations.append(normalized)
    
    # Con prefijo 57 si no lo tiene
    if not number.startswith('57') and len(number) == 10:
        variations.append(f"57{number}")
    
    return list(set(variations))
```

### AJUSTE 3: Mejorar Consultas SQL
**Implementar búsqueda por variaciones:**

```sql
SELECT ... FROM operator_call_data 
WHERE numero_origen IN (?, ?, ?) 
   OR numero_destino IN (?, ?, ?) 
   OR numero_objetivo IN (?, ?, ?)
```

### AJUSTE 4: Logging Mejorado
**Agregar trazabilidad de normalización:**

```python
self.logger.info(f"Buscando número {original_number}")
self.logger.info(f"Variaciones: {variations}")
self.logger.info(f"Encontrados {len(results)} registros")
```

---

## 📋 IMPLEMENTACIÓN PRIORITARIA

### FASE 1: Corrección Inmediata (30 minutos)
1. **Modificar `_extract_operator_numbers()`**
   - Implementar búsqueda por variaciones
   - Agregar logging detallado

2. **Probar con números específicos**
   - Verificar que aparezcan los 4 números encontrados
   - Confirmar que `3104277553` realmente no existe

### FASE 2: Mejoras Adicionales (1 hora)
1. **Implementar función `_get_number_variations()`**
2. **Optimizar consultas SQL**
3. **Mejorar función de normalización**
4. **Agregar validación de formatos**

### FASE 3: Validación Completa (30 minutos)
1. **Ejecutar análisis de correlación completo**
2. **Verificar aparición de números objetivo**
3. **Documentar cambios realizados**

---

## 🎯 RESULTADOS ESPERADOS

### Después de los ajustes:
- `3224274851` → **APARECERÁ** en resultados (4 registros encontrados)
- `3208611034` → **APARECERÁ** en resultados (2 registros encontrados)
- `3102715509` → **APARECERÁ** en resultados (1 registro encontrado)
- `3143534707` → **APARECERÁ** en resultados (7 registros encontrados)
- `3104277553` → **NO APARECERÁ** (no existe en datos)

### Beneficios adicionales:
- Mejora la captura de números con diferentes formatos
- Robusto ante variaciones de prefijos internacionales
- Mejor logging para debugging futuro
- Algoritmo más confiable para análisis de correlación

---

## 🚨 PUNTOS CRÍTICOS

1. **No modificar la lógica de correlación por celdas únicas**
2. **Mantener la normalización para comparación**
3. **Asegurar que no se dupliquen números en resultados**
4. **Verificar rendimiento con mejora de consultas**

---

## 📊 MÉTRICAS DE ÉXITO

- ✅ 4 de 5 números objetivo aparecen en correlación
- ✅ Sin duplicados en resultados
- ✅ Tiempo de procesamiento similar o mejor
- ✅ Logging claro de proceso de búsqueda

---

**Prioridad:** 🔴 **ALTA** - Problema afecta precisión del análisis  
**Impacto:** 📈 **ALTO** - Mejora significativa en captura de números objetivo  
**Complejidad:** 🟡 **MEDIA** - Requiere modificación cuidadosa de consultas SQL