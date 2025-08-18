/**
 * Demostración del Sistema Visual de Correlación
 * 
 * Este archivo contiene funciones de demostración y testing para verificar
 * el funcionamiento del sistema de colores determinístico.
 */

import { 
    getPointColor, 
    getPointChipClasses,
    getCellIdToPointMapping,
    getCorrelationCellClasses,
    getColorSystemStats,
    clearColorCache,
    COLOR_PALETTE 
} from './colorSystem';

/**
 * Datos de ejemplo para demostraciones
 */
export const DEMO_DATA = {
    // Puntos HUNTER de ejemplo
    puntos: [
        'Punto_Central_A',
        'Punto_Norte_B',
        'Punto_Sur_C',
        'Punto_Este_D',
        'Punto_Oeste_E',
        'Base_Principal',
        'Estación_Móvil_1',
        'Repetidor_Montaña',
        'Antena_Urbana_X',
        'Torre_Comunicaciones'
    ],

    // Datos celulares de ejemplo
    cellularData: [
        { cellId: '12345', punto: 'Punto_Central_A' },
        { cellId: '67890', punto: 'Punto_Norte_B' },
        { cellId: '54321', punto: 'Punto_Sur_C' },
        { cellId: '98765', punto: 'Punto_Este_D' },
        { cellId: '11111', punto: 'Punto_Oeste_E' },
        { cellId: '22222', punto: 'Base_Principal' },
        { cellId: '33333', punto: 'Estación_Móvil_1' },
        { cellId: '44444', punto: 'Repetidor_Montaña' },
        { cellId: '55555', punto: 'Antena_Urbana_X' },
        { cellId: '66666', punto: 'Torre_Comunicaciones' }
    ],

    // Resultados de correlación de ejemplo
    correlationResults: [
        {
            targetNumber: '3104277553',
            operator: 'CLARO',
            occurrences: 15,
            firstDetection: '2021-05-20T10:15:00',
            lastDetection: '2021-05-20T14:20:00',
            relatedCells: ['12345', '67890', '54321'],
            confidence: 85
        },
        {
            targetNumber: '3224274851',
            operator: 'MOVISTAR',
            occurrences: 8,
            firstDetection: '2021-05-20T11:30:00',
            lastDetection: '2021-05-20T13:45:00',
            relatedCells: ['98765', '11111'],
            confidence: 72
        },
        {
            targetNumber: '3143534707',
            operator: 'TIGO',
            occurrences: 23,
            firstDetection: '2021-05-20T09:00:00',
            lastDetection: '2021-05-20T16:30:00',
            relatedCells: ['22222', '33333', '44444', '55555'],
            confidence: 91
        }
    ]
};

/**
 * Demostración básica del sistema de colores
 */
export function demoBasicColorSystem(): void {
    console.log('🎨 DEMOSTRACIÓN: Sistema de Colores Determinístico\n');
    
    // Limpiar cache para demo
    clearColorCache();
    
    // Mostrar colores para puntos de ejemplo
    DEMO_DATA.puntos.forEach((punto, index) => {
        const color = getPointColor(punto);
        console.log(`${index + 1}. ${punto}:`);
        console.log(`   Color: ${color.name}`);
        console.log(`   Classes: ${getPointChipClasses(punto)}`);
        console.log('');
    });
    
    // Mostrar estadísticas
    const stats = getColorSystemStats();
    console.log('📊 Estadísticas del Sistema:');
    console.log(`   Puntos mapeados: ${stats.totalCachedPoints}`);
    console.log(`   Colores en uso: ${stats.colorsInUse}`);
    console.log(`   Hit rate: ${stats.cacheHitRate.toFixed(1)}%\n`);
}

/**
 * Demostración de consistencia de colores
 */
export function demoColorConsistency(): void {
    console.log('🔄 DEMOSTRACIÓN: Consistencia de Colores\n');
    
    const testPoint = 'Punto_Test_Consistencia';
    
    // Obtener color múltiples veces
    const colors = [];
    for (let i = 0; i < 5; i++) {
        colors.push(getPointColor(testPoint));
    }
    
    // Verificar que todos los colores son iguales
    const allSame = colors.every(color => 
        color.name === colors[0].name &&
        color.background === colors[0].background &&
        color.border === colors[0].border &&
        color.text === colors[0].text
    );
    
    console.log(`Punto de prueba: ${testPoint}`);
    console.log(`Color asignado: ${colors[0].name}`);
    console.log(`Consistencia en 5 consultas: ${allSame ? '✅ CORRECTO' : '❌ ERROR'}\n`);
    
    if (!allSame) {
        console.log('Colores obtenidos:');
        colors.forEach((color, idx) => {
            console.log(`  ${idx + 1}. ${color.name}`);
        });
    }
}

/**
 * Demostración de mapeo Cell ID → Punto HUNTER
 */
export function demoCellMapping(): void {
    console.log('🔗 DEMOSTRACIÓN: Mapeo Cell ID → Punto HUNTER\n');
    
    DEMO_DATA.cellularData.forEach(data => {
        const mappedPoint = getCellIdToPointMapping(data.cellId, DEMO_DATA.cellularData);
        const color = getPointColor(data.punto);
        
        console.log(`Cell ID: ${data.cellId}`);
        console.log(`  → Punto HUNTER: ${mappedPoint}`);
        console.log(`  → Color: ${color.name}`);
        console.log(`  → Match: ${mappedPoint === data.punto ? '✅' : '❌'}`);
        console.log('');
    });
}

/**
 * Demostración de badges de correlación
 */
export function demoCorrelationBadges(): void {
    console.log('🏷️  DEMOSTRACIÓN: Badges de Correlación\n');
    
    DEMO_DATA.correlationResults.forEach((result, index) => {
        console.log(`${index + 1}. Número: ${result.targetNumber} (${result.operator})`);
        console.log(`   Celdas relacionadas: ${result.relatedCells.join(', ')}`);
        
        result.relatedCells.forEach(cellId => {
            const punto = getCellIdToPointMapping(cellId, DEMO_DATA.cellularData);
            const role = Math.random() > 0.5 ? 'originator' : 'receptor';
            const classes = getCorrelationCellClasses(cellId, role, DEMO_DATA.cellularData);
            
            console.log(`     ${cellId} → ${punto || 'Sin mapeo'} (${role})`);
            console.log(`     Classes: ${classes}`);
        });
        console.log('');
    });
}

/**
 * Test de distribución de colores
 */
export function testColorDistribution(numPoints: number = 50): void {
    console.log(`📈 TEST: Distribución de Colores (${numPoints} puntos)\n`);
    
    clearColorCache();
    
    // Generar puntos de prueba
    const testPoints = Array.from({ length: numPoints }, (_, i) => 
        `Punto_Test_${i.toString().padStart(3, '0')}`
    );
    
    // Mapear colores
    const colorCount = new Map<string, number>();
    testPoints.forEach(punto => {
        const color = getPointColor(punto);
        colorCount.set(color.name, (colorCount.get(color.name) || 0) + 1);
    });
    
    // Mostrar distribución
    console.log('Distribución de colores:');
    Array.from(colorCount.entries())
        .sort((a, b) => b[1] - a[1]) // Ordenar por frecuencia
        .forEach(([colorName, count]) => {
            const percentage = ((count / numPoints) * 100).toFixed(1);
            const bar = '█'.repeat(Math.ceil(count / 2));
            console.log(`  ${colorName.padEnd(20)} ${count.toString().padStart(2)} (${percentage.padStart(4)}%) ${bar}`);
        });
    
    // Estadísticas
    const avgPerColor = numPoints / COLOR_PALETTE.length;
    const maxDeviation = Math.max(...colorCount.values()) - Math.min(...colorCount.values());
    
    console.log(`\n📊 Estadísticas:`);
    console.log(`   Promedio por color: ${avgPerColor.toFixed(1)}`);
    console.log(`   Desviación máxima: ${maxDeviation}`);
    console.log(`   Colores utilizados: ${colorCount.size}/${COLOR_PALETTE.length}`);
    console.log(`   Distribución: ${maxDeviation <= avgPerColor ? '✅ Uniforme' : '⚠️ Desbalanceada'}\n`);
}

/**
 * Test de performance del sistema
 */
export function testPerformance(): void {
    console.log('⚡ TEST: Performance del Sistema\n');
    
    const iterations = 1000;
    const testPoint = 'Punto_Performance_Test';
    
    // Test 1: Primera consulta (sin cache)
    clearColorCache();
    const start1 = performance.now();
    getPointColor(testPoint);
    const time1 = performance.now() - start1;
    
    // Test 2: Consultas con cache
    const start2 = performance.now();
    for (let i = 0; i < iterations; i++) {
        getPointColor(testPoint);
    }
    const time2 = performance.now() - start2;
    
    console.log('Resultados de performance:');
    console.log(`  Primera consulta (sin cache): ${time1.toFixed(3)} ms`);
    console.log(`  ${iterations} consultas con cache: ${time2.toFixed(3)} ms`);
    console.log(`  Promedio con cache: ${(time2 / iterations).toFixed(6)} ms`);
    console.log(`  Mejora con cache: ${((time1 / (time2 / iterations)) - 1) * 100}x más rápido\n`);
}

/**
 * Ejecuta todas las demostraciones
 */
export function runAllDemos(): void {
    console.log('🚀 EJECUTANDO TODAS LAS DEMOSTRACIONES DEL SISTEMA VISUAL\n');
    console.log('='.repeat(60));
    
    try {
        demoBasicColorSystem();
        console.log('='.repeat(60));
        
        demoColorConsistency();
        console.log('='.repeat(60));
        
        demoCellMapping();
        console.log('='.repeat(60));
        
        demoCorrelationBadges();
        console.log('='.repeat(60));
        
        testColorDistribution(30);
        console.log('='.repeat(60));
        
        testPerformance();
        console.log('='.repeat(60));
        
        console.log('✅ TODAS LAS DEMOSTRACIONES COMPLETADAS EXITOSAMENTE');
        
    } catch (error) {
        console.error('❌ ERROR EN DEMOSTRACIÓN:', error);
    }
}

/**
 * Función para usar en consola del navegador
 */
export function quickDemo(): void {
    console.log('🎨 Demo Rápido del Sistema Visual');
    console.log('Ejecuta runAllDemos() para demo completa\n');
    
    const ejemplos = ['Punto_A', 'Punto_B', 'Punto_C'];
    ejemplos.forEach(punto => {
        const color = getPointColor(punto);
        console.log(`${punto} → ${color.name}`);
    });
}

// Para uso en desarrollo
if (typeof window !== 'undefined') {
    (window as any).colorSystemDemo = {
        runAllDemos,
        quickDemo,
        demoBasicColorSystem,
        demoColorConsistency,
        demoCellMapping,
        demoCorrelationBadges,
        testColorDistribution,
        testPerformance
    };
    
    console.log('🎨 Sistema Visual Demo cargado. Usa colorSystemDemo.quickDemo() para probar.');
}