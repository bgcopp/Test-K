/**
 * Testing Unitario - Transformación de Datos para Diagrama de Red
 * Analiza el algoritmo implementado en NetworkDiagramModal.tsx
 */

console.log('🧪 INICIANDO TESTING UNITARIO - TRANSFORMACIÓN DE DATOS');
console.log('=' .repeat(70));

// Simulando datos de ejemplo basados en la estructura UnifiedInteraction
const mockInteractions = [
    {
        numero_objetivo: "3001234567",
        numero_secundario: "3009876543", 
        fecha_hora: "2024-05-15 10:30:00",
        duracion_segundos: 120,
        operador: "CLARO",
        celda_inicio: "CELDA001",
        celda_final: "CELDA002",
        punto_hunter: "HUNTER001",
        lat_hunter: 4.6097,
        lon_hunter: -74.0817,
        tipo_interaccion: "llamada"
    },
    {
        numero_objetivo: "3001234567",
        numero_secundario: "3005555555",
        fecha_hora: "2024-05-15 11:15:00", 
        duracion_segundos: 90,
        operador: "MOVISTAR",
        celda_inicio: "CELDA003",
        celda_final: "CELDA004", 
        tipo_interaccion: "llamada"
    },
    {
        numero_objetivo: "3009876543",
        numero_secundario: "3001234567",
        fecha_hora: "2024-05-15 12:00:00",
        duracion_segundos: 200,
        operador: "CLARO", 
        celda_inicio: "CELDA002",
        celda_final: "CELDA001",
        tipo_interaccion: "llamada"
    },
    {
        numero_objetivo: "3001234567",
        numero_secundario: "3009876543",
        fecha_hora: "2024-05-15 13:30:00",
        duracion_segundos: 45,
        operador: "CLARO",
        celda_inicio: "CELDA001", 
        celda_final: "CELDA002",
        tipo_interaccion: "llamada"
    },
    {
        numero_objetivo: "3001234567",
        numero_secundario: "3007777777",
        fecha_hora: "2024-05-15 14:00:00",
        duracion_segundos: 30,
        operador: "TIGO",
        celda_inicio: "CELDA005",
        celda_final: "",
        tipo_interaccion: "datos"
    },
    {
        numero_objetivo: "3007777777",
        numero_secundario: "3001234567", 
        fecha_hora: "2024-05-15 15:00:00",
        duracion_segundos: 180,
        operador: "TIGO",
        celda_inicio: "CELDA006",
        celda_final: "CELDA005",
        tipo_interaccion: "llamada"
    }
];

const targetNumber = "3001234567";

// Implementación del algoritmo de transformación (copiado de NetworkDiagramModal.tsx)
function transformDataForDiagram(interactions, targetNumber) {
    const nodes = [];
    const edges = [];
    const numberMap = new Map();

    // Contar interacciones por número para determinar nivel de correlación
    interactions.forEach(interaction => {
        const count1 = numberMap.get(interaction.numero_objetivo) || 0;
        const count2 = numberMap.get(interaction.numero_secundario) || 0;
        numberMap.set(interaction.numero_objetivo, count1 + 1);
        if (interaction.numero_secundario) {
            numberMap.set(interaction.numero_secundario, count2 + 1);
        }
    });

    // Crear nodos únicos
    const uniqueNumbers = Array.from(numberMap.keys());
    uniqueNumbers.forEach(number => {
        const count = numberMap.get(number) || 0;
        const isTarget = number === targetNumber;
        
        let correlationLevel = 'indirect';
        if (isTarget) correlationLevel = 'target';
        else if (count >= 5) correlationLevel = 'high';
        else if (count >= 3) correlationLevel = 'medium';
        else correlationLevel = 'low';

        // Buscar operador del número
        const interaction = interactions.find(i => 
            i.numero_objetivo === number || i.numero_secundario === number
        );
        const operator = interaction?.operador || 'Desconocido';

        nodes.push({
            id: number,
            number,
            name: undefined, // TODO: Implementar nombres de contactos si disponible
            operator,
            correlationLevel,
            interactionCount: count,
            isTarget
        });
    });

    // Crear enlaces basados en interacciones
    interactions.forEach((interaction, index) => {
        if (!interaction.numero_secundario) return; // Skip datos móviles sin secundario
        
        const edgeId = `${interaction.numero_objetivo}-${interaction.numero_secundario}-${index}`;
        const cellIds = [interaction.celda_inicio, interaction.celda_final].filter(Boolean);
        
        edges.push({
            id: edgeId,
            source: interaction.numero_objetivo,
            target: interaction.numero_secundario,
            cellIds,
            isDirectional: true, // Siempre direccional basado en origen->destino
            interactionType: interaction.tipo_interaccion || 'llamada'
        });
    });

    return { nodes, edges };
}

// Ejecutar transformación
console.log('📊 DATOS DE ENTRADA:');
console.log(`   - Total interacciones: ${mockInteractions.length}`);
console.log(`   - Número objetivo: ${targetNumber}`);
console.log(`   - Tipos de interacción: ${[...new Set(mockInteractions.map(i => i.tipo_interaccion))].join(', ')}`);
console.log(`   - Operadores: ${[...new Set(mockInteractions.map(i => i.operador))].join(', ')}`);
console.log('');

const result = transformDataForDiagram(mockInteractions, targetNumber);

console.log('🔍 RESULTADOS DE TRANSFORMACIÓN:');
console.log('');

// Analizar nodos generados
console.log('📱 NODOS GENERADOS:');
result.nodes.forEach((node, index) => {
    console.log(`   ${index + 1}. ${node.number}`);
    console.log(`      - ID: ${node.id}`);
    console.log(`      - Operador: ${node.operator}`);
    console.log(`      - Nivel correlación: ${node.correlationLevel}`);
    console.log(`      - Interacciones: ${node.interactionCount}`);
    console.log(`      - Es objetivo: ${node.isTarget}`);
    console.log('');
});

console.log('🔗 ENLACES GENERADOS:');
result.edges.forEach((edge, index) => {
    console.log(`   ${index + 1}. ${edge.source} → ${edge.target}`);
    console.log(`      - ID: ${edge.id}`);
    console.log(`      - Celdas: [${edge.cellIds.join(', ')}]`);
    console.log(`      - Direccional: ${edge.isDirectional}`);
    console.log(`      - Tipo: ${edge.interactionType}`);
    console.log('');
});

// Estadísticas del resultado
const stats = {
    totalNodes: result.nodes.length,
    totalEdges: result.edges.length,
    targetNode: result.nodes.find(n => n.isTarget),
    correlationDistribution: {
        high: result.nodes.filter(n => n.correlationLevel === 'high').length,
        medium: result.nodes.filter(n => n.correlationLevel === 'medium').length,
        low: result.nodes.filter(n => n.correlationLevel === 'low').length,
        indirect: result.nodes.filter(n => n.correlationLevel === 'indirect').length
    }
};

console.log('📈 ESTADÍSTICAS FINALES:');
console.log(`   - Total nodos: ${stats.totalNodes}`);
console.log(`   - Total enlaces: ${stats.totalEdges}`);
console.log(`   - Nodo objetivo: ${stats.targetNode?.number || 'NO ENCONTRADO'}`);
console.log('   - Distribución de correlación:');
console.log(`     • Target: ${stats.correlationDistribution.high}`);
console.log(`     • Alta (≥5): ${stats.correlationDistribution.high}`);
console.log(`     • Media (≥3): ${stats.correlationDistribution.medium}`);
console.log(`     • Baja (<3): ${stats.correlationDistribution.low}`);
console.log(`     • Indirecta: ${stats.correlationDistribution.indirect}`);

// Validaciones críticas
console.log('');
console.log('🔍 VALIDACIONES CRÍTICAS:');

let criticalIssues = 0;

// 1. Verificar que existe nodo objetivo
if (!stats.targetNode) {
    console.log('❌ CRÍTICO: No se encontró nodo objetivo');
    criticalIssues++;
} else {
    console.log('✅ Nodo objetivo encontrado correctamente');
}

// 2. Verificar que todos los nodos tienen operador
const nodesWithoutOperator = result.nodes.filter(n => !n.operator || n.operator === 'Desconocido');
if (nodesWithoutOperator.length > 0) {
    console.log(`❌ CRÍTICO: ${nodesWithoutOperator.length} nodos sin operador definido`);
    criticalIssues++;
} else {
    console.log('✅ Todos los nodos tienen operador definido');
}

// 3. Verificar que hay enlaces bidireccionales
const bidirectionalCount = result.edges.filter(edge => 
    result.edges.some(otherEdge => 
        edge.source === otherEdge.target && edge.target === otherEdge.source
    )
).length;

console.log(`📊 Enlaces bidireccionales detectados: ${bidirectionalCount / 2}`);

// 4. Verificar algoritmo de correlación
const targetInteractionCount = stats.targetNode?.interactionCount || 0;
if (targetInteractionCount > 0) {
    console.log(`✅ Nodo objetivo tiene ${targetInteractionCount} interacciones`);
} else {
    console.log('❌ MAYOR: Nodo objetivo sin interacciones');
}

// 5. Verificar que los enlaces apuntan a nodos existentes
const nodeIds = new Set(result.nodes.map(n => n.id));
const invalidEdges = result.edges.filter(edge => 
    !nodeIds.has(edge.source) || !nodeIds.has(edge.target)
);

if (invalidEdges.length > 0) {
    console.log(`❌ CRÍTICO: ${invalidEdges.length} enlaces apuntan a nodos inexistentes`);
    criticalIssues++;
} else {
    console.log('✅ Todos los enlaces apuntan a nodos válidos');
}

// 6. Verificar performance con dataset
const performanceScore = mockInteractions.length / (result.nodes.length + result.edges.length);
console.log(`📊 Score de eficiencia: ${performanceScore.toFixed(2)} (interacciones/elementos)`);

console.log('');
console.log('🏁 RESUMEN DEL TESTING:');
console.log(`   - Issues críticos: ${criticalIssues}`);
console.log(`   - Nodos generados: ${result.nodes.length}/${mockInteractions.length} (${((result.nodes.length/mockInteractions.length)*100).toFixed(1)}%)`);
console.log(`   - Enlaces generados: ${result.edges.length}/${mockInteractions.length} (${((result.edges.length/mockInteractions.length)*100).toFixed(1)}%)`);

if (criticalIssues === 0) {
    console.log('✅ ¡ALGORITMO DE TRANSFORMACIÓN FUNCIONA CORRECTAMENTE!');
} else {
    console.log('❌ ALGORITMO REQUIERE CORRECCIONES ANTES DE PRODUCCIÓN');
}

console.log('=' .repeat(70));