# MEJORAS DIAGRAMA DE CORRELACIÓN - REDISEÑO VISUAL

## ANÁLISIS INICIAL - Problemas Identificados

### PROBLEMA 1: Jerarquía Visual Incorrecta
**Estado Actual:**
- El nombre del operador está debajo del icono/avatar (línea 681-698 PersonNode.tsx)
- El número de teléfono está en el avatar como últimos 4 dígitos (línea 143 getPhoneInitials)
- La información más importante (número) es la menos visible

**Solución Requerida:**
- Número de teléfono DEBAJO del icono como información principal
- Operador como información secundaria/contextual
- Mejor jerarquía visual de la información

### PROBLEMA 2: Falta Distinción Originador vs Receptor
**Estado Actual:**
- No hay distinción visual entre quien origina vs quien recibe llamadas
- Todos los nodos se ven iguales independientemente del rol
- Aristas no indican dirección de comunicación claramente

**Solución Requerida:**
- Iconografía diferenciada para originador vs receptor
- Colores o formas que distingan roles
- Aristas con mejor indicación direccional

### PROBLEMA 3: Comunicación Visual Poco Clara
**Estado Actual:**
- Avatar con iniciales no es intuitivo
- Información crítica solo en tooltips
- UX confusa para análisis rápido

**Solución Requerida:**
- Información crítica visible directamente
- UX intuitiva para análisis profesional
- Presentación más clara de datos de correlación

## PLAN DE IMPLEMENTACIÓN

### FASE 1: Rediseño PersonNode.tsx
1. **Restructurar layout del nodo:**
   - Avatar/icono en la parte superior
   - Número de teléfono prominente debajo del avatar
   - Operador como badge secundario

2. **Implementar distinción visual de roles:**
   - Iconos diferenciados para originador vs receptor
   - Bordes y colores específicos por rol
   - Indicadores visuales claros

3. **Mejorar jerarquía de información:**
   - Número como elemento principal
   - Información secundaria menos prominente
   - Mejor contraste y legibilidad

### FASE 2: Optimizar graphTransformations.ts
1. **Determinar roles de comunicación:**
   - Analizar datos para identificar originador vs receptor
   - Crear tipos para roles de comunicación
   - Implementar lógica de clasificación

2. **Mejorar representación de aristas:**
   - Aristas direccionales más claras
   - Colores específicos por tipo de comunicación
   - Grosor basado en intensidad de comunicación

### FASE 3: Pruebas y Validación
1. **Testing visual:**
   - Verificar legibilidad en tema oscuro
   - Probar con diferentes tamaños de pantalla
   - Validar accesibilidad

2. **UX Testing:**
   - Confirmar intuitividad de la nueva interfaz
   - Verificar facilidad de análisis
   - Optimizar basado en feedback

## ESPECIFICACIONES TÉCNICAS

### Estructura Visual Nueva (PersonNode):
```
┌─────────────────┐
│   [ICONO/AVATAR] │  ← Rol específico (originador/receptor)
│   3143534707     │  ← Número principal (prominente)
│   ┌─────────┐   │  ← Badge operador (secundario)
│   │  CLARO  │   │
│   └─────────┘   │
└─────────────────┘
```

### Códigos de Color por Rol:
- **Originador**: Tonos cálidos (naranjas/rojos) con icono de salida
- **Receptor**: Tonos fríos (azules/verdes) con icono de entrada
- **Mixto**: Tonos neutros (grises/púrpuras) con icono bidireccional

### Aristas Mejoradas:
- **Salientes**: Flechas naranjas más gruesas
- **Entrantes**: Flechas azules estándar
- **Bidireccionales**: Líneas grises con doble flecha

## ARCHIVOS A MODIFICAR

1. **Frontend/components/ui/PersonNode.tsx** (Principal)
   - Restructurar layout del nodo
   - Implementar nuevos tipos de iconos
   - Mejorar jerarquía visual

2. **Frontend/utils/graphTransformations.ts**
   - Agregar lógica de roles de comunicación
   - Mejorar clasificación de tipos de aristas
   - Optimizar colores y estilos

3. **Frontend/types.ts** (Opcional)
   - Agregar tipos para roles de comunicación
   - Extender interfaces existentes

## CRONOGRAMA

- **Análisis y diseño**: ✅ Completado  
- **Implementación PersonNode**: ✅ Completado
- **Optimización transformaciones**: ✅ Completado
- **Testing y ajustes**: ✅ Compilación exitosa
- **Documentación final**: ✅ Completado

## RESULTADO ESPERADO

Una interfaz de correlación telefónica profesional y intuitiva que permita:
- Identificación rápida de números de teléfono
- Distinción clara de roles de comunicación (originador/receptor)
- Análisis visual eficiente de correlaciones
- UX optimizada para investigadores forenses

---
*Documento de seguimiento - Mejoras Diagrama de Correlación*
*Fecha: 2025-08-19*
*Desarrollador: Claude Code con Boris*