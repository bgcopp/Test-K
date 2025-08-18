# Sistema Visual de Correlación HUNTER - Operador

## Resumen

Este documento describe el sistema visual implementado para correlacionar visualmente puntos HUNTER con sus celdas relacionadas en el análisis de correlación, proporcionando una interfaz intuitiva y consistente para la identificación de objetivos.

## Componentes del Sistema

### 1. Sistema de Colores Determinístico (`colorSystem.ts`)

**Funcionalidad Principal:**
- Mapeo determinístico: cada punto HUNTER mantiene el mismo color durante toda la sesión
- Paleta de 16 colores pasteles optimizados para tema oscuro
- Contraste WCAG AA+ para accesibilidad
- Memoización para performance optimizada

**Funciones Principales:**
```typescript
getPointColor(punto: string): ColorDefinition
getPointChipClasses(punto: string): string
getCellIdToPointMapping(cellId: string, cellularData: Array): string | null
getCorrelationCellClasses(cellId: string, role: 'originator' | 'receptor', cellularData: Array): string
```

### 2. Componente PointChip (`PointChip.tsx`)

**Propósito:** Renderizar chips visuales consistentes para puntos HUNTER

**Características:**
- Chips con background pastel y bordes más saturados
- Tooltips informativos con nombre del punto y color asignado
- Soporte para diferentes tamaños (xs, sm, md, lg)
- Accesible con teclado y compatible con lectores de pantalla

**Uso:**
```tsx
<PointChip 
    punto="Punto_Central_A"
    size="sm"
    showTooltip={true}
    tooltipInfo="Punto HUNTER: Punto_Central_A | Cell ID: 12345"
/>
```

### 3. Componente CorrelationCellBadge (`CorrelationCellBadge.tsx`)

**Propósito:** Badges para celdas relacionadas que combinan roles con colores de puntos HUNTER

**Sistema Visual:**
- **Color interno:** Azul para originador, violeta para receptor
- **Borde externo:** Color del punto HUNTER asociado
- **Tooltip completo:** Información de rol, Cell ID y punto HUNTER

**Componente CorrelationCellBadgeGroup:**
- Agrupa múltiples badges de celdas relacionadas
- Limita visualización (configurable, por defecto 8 badges + contador)
- Maneja celdas sin mapeo con badge gris neutral

### 4. Componente CorrelationLegend (`CorrelationLegend.tsx`)

**Propósito:** Leyenda interactiva del sistema visual

**Información Mostrada:**
- Explicación de roles (originador/receptor)
- Demostración de chips de puntos HUNTER con datos reales
- Conexión visual Cell ID ↔ Punto HUNTER
- Estadísticas del sistema (opcional)
- Información colapsable para ahorrar espacio

## Integración en MissionDetail

### Columna "Punto" en Datos Celulares

**Antes:**
```tsx
<td className="px-4 py-3 text-sm text-light font-medium">
    {d.punto}
</td>
```

**Después:**
```tsx
<td className="px-4 py-3 text-sm whitespace-nowrap">
    <PointChip 
        punto={d.punto}
        size="sm"
        showTooltip={true}
        tooltipInfo={`Punto HUNTER: ${d.punto} | Cell ID: ${d.cellId}`}
    />
</td>
```

### Celdas Relacionadas en Correlación

**Antes:**
```tsx
{(result.relatedCells || []).map((cell, idx) => {
    const role = getCellRole(result.targetNumber, cell || '');
    const badgeClasses = role === 'originator' ? "..." : "...";
    return <span className={badgeClasses}>{cell}</span>;
})}
```

**Después:**
```tsx
<CorrelationCellBadgeGroup
    cellIds={result.relatedCells || []}
    targetNumber={result.targetNumber}
    cellularData={mission.cellularData || []}
    maxDisplay={8}
    getCellRole={getCellRole}
    onCellClick={(cellId, punto) => {
        console.log(`Clicked cell: ${cellId}, punto: ${punto}`);
    }}
/>
```

## Algoritmo de Mapeo

### 1. Hash Determinístico

```typescript
function deterministicHash(input: string): number {
    let hash = 0;
    const normalized = input.toString().toLowerCase().trim();
    
    for (let i = 0; i < normalized.length; i++) {
        const char = normalized.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    
    return Math.abs(hash);
}
```

### 2. Mapeo Cell ID → Punto HUNTER

1. **Búsqueda exacta:** Coincidencia directa de Cell ID en datos celulares
2. **Búsqueda parcial:** Coincidencia por contenido si no hay exacta
3. **Resultado:** Nombre del punto HUNTER o null si no se encuentra

### 3. Asignación de Colores

1. **Hash del nombre del punto:** Genera índice consistente
2. **Módulo con paleta:** `hash % COLOR_PALETTE.length`
3. **Cache:** Almacena resultado para consultas futuras
4. **Consistencia:** Mismo punto = mismo color durante toda la sesión

## Paleta de Colores

16 colores pasteles optimizados para tema oscuro:

1. **Esmeralda** - `bg-emerald-100/10 border-emerald-400/60 text-emerald-200`
2. **Azul Cielo** - `bg-blue-100/10 border-blue-400/60 text-blue-200`
3. **Violeta** - `bg-violet-100/10 border-violet-400/60 text-violet-200`
4. **Rosa** - `bg-rose-100/10 border-rose-400/60 text-rose-200`
5. **Ámbar** - `bg-amber-100/10 border-amber-400/60 text-amber-200`
6. **Verde Azulado** - `bg-teal-100/10 border-teal-400/60 text-teal-200`
7. **Índigo** - `bg-indigo-100/10 border-indigo-400/60 text-indigo-200`
8. **Rosa Claro** - `bg-pink-100/10 border-pink-400/60 text-pink-200`
9. **Lima** - `bg-lime-100/10 border-lime-400/60 text-lime-200`
10. **Cian** - `bg-cyan-100/10 border-cyan-400/60 text-cyan-200`
11. **Púrpura** - `bg-purple-100/10 border-purple-400/60 text-purple-200`
12. **Naranja** - `bg-orange-100/10 border-orange-400/60 text-orange-200`
13. **Verde** - `bg-green-100/10 border-green-400/60 text-green-200`
14. **Rojo** - `bg-red-100/10 border-red-400/60 text-red-200`
15. **Amarillo** - `bg-yellow-100/10 border-yellow-400/60 text-yellow-200`
16. **Pizarra** - `bg-slate-100/10 border-slate-400/60 text-slate-200`

## Accesibilidad y UX

### Contraste de Colores
- Todos los colores cumplen WCAG AA en tema oscuro
- Texto con contraste mínimo 4.5:1 contra background
- Bordes visibles con transparencia calibrada

### Interactividad
- Hover effects suaves con `transition-all duration-200`
- Focus states para navegación por teclado
- Tooltips informativos con contexto completo
- Clickable chips con `hover:scale-105` para feedback visual

### Responsividad
- Chips se adaptan a contenedores estrechos
- Texto truncado con tooltip completo
- Wrapping inteligente en grupos de badges

## Performance

### Optimizaciones Implementadas
- **Memoización:** Cache de colores ya calculados
- **Lazy evaluation:** Cálculo solo cuando se necesita
- **Hash optimizado:** Algoritmo DJB2 para distribución uniforme
- **Componentes pure:** Re-render solo cuando props cambian

### Estadísticas del Sistema
```typescript
getColorSystemStats(): {
    totalCachedPoints: number;
    colorsInUse: number;
    cacheHitRate: number;
}
```

## Casos de Uso

### Caso 1: Identificación Rápida
**Problema:** Dificultad para identificar qué celdas pertenecen a qué puntos HUNTER
**Solución:** Cada punto tiene un color único y consistente, celdas relacionadas tienen borde del mismo color

### Caso 2: Análisis de Correlación
**Problema:** Grandes volúmenes de datos dificultan el seguimiento visual
**Solución:** Sistema de colores + roles crea patrón visual distintivo para cada combinación

### Caso 3: Navegación Eficiente
**Problema:** Saltar entre diferentes vistas pierde contexto visual
**Solución:** Colores determinísticos mantienen consistencia en toda la sesión

## Debugging y Mantenimiento

### Funciones de Debug
```typescript
// Limpiar cache (útil para testing)
clearColorCache(): void

// Obtener estadísticas
getColorSystemStats(): object
```

### Logs de Debug
El sistema incluye logs para monitorear:
- Clicks en celdas relacionadas
- Mapeo Cell ID → Punto HUNTER
- Estadísticas de uso de colores

## Extensibilidad

### Agregar Nuevos Colores
1. Agregar definición a `COLOR_PALETTE` en `colorSystem.ts`
2. Verificar contraste WCAG AA
3. Actualizar documentación

### Nuevos Componentes
1. Importar utilidades de `colorSystem.ts`
2. Usar `getPointColor()` para consistencia
3. Implementar tooltips informativos

### Integración con Otros Análisis
El sistema está diseñado para ser reutilizable en:
- Análisis de objetivos clásico
- Reportes de correlación
- Exportación de datos
- Interfaces de administración

---

**Implementado por:** Claude Code  
**Fecha:** Agosto 2025  
**Versión del Sistema:** 1.0.0