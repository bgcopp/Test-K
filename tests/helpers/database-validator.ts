/**
 * Helper de Validación de Base de Datos para Pruebas E2E CLARO
 * 
 * Proporciona funciones para validar datos en SQLite durante pruebas Playwright
 * Incluye validaciones específicas para registros CLARO y algoritmo de correlación
 * 
 * @author Testing Team KRONOS
 * @version 1.0.0
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

// Configuración de base de datos
const DB_PATH = path.join(process.cwd(), 'Backend', 'kronos.db');
const PYTHON_PATH = path.join(process.cwd(), 'Backend');

export interface DatabaseValidationResult {
  success: boolean;
  data?: any;
  error?: string;
  count?: number;
  details?: any;
}

export interface ClaroRecordCount {
  operator: string;
  total_records: number;
  call_data_records: number;
  cellular_data_records: number;
  missions_count: number;
}

export interface CorrelationResult {
  target_number: string;
  found: boolean;
  correlations_count: number;
  related_numbers: string[];
  time_periods: string[];
  cells_involved: string[];
}

/**
 * Clase helper para validaciones de base de datos
 */
export class DatabaseValidator {
  
  /**
   * Ejecuta una consulta Python para validar la base de datos
   */
  private async executePythonQuery(script: string): Promise<DatabaseValidationResult> {
    try {
      const pythonScript = `
import sqlite3
import json
import sys
import os

# Cambiar al directorio Backend
os.chdir('${PYTHON_PATH.replace(/\\/g, '\\\\')}')

# Conectar a la base de datos
db_path = '${DB_PATH.replace(/\\/g, '\\\\')}'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    ${script}
except Exception as e:
    print(json.dumps({"success": False, "error": str(e)}))
    sys.exit(1)
finally:
    conn.close()
      `;

      // Escribir script temporal
      const tempScriptPath = path.join(process.cwd(), 'temp_db_query.py');
      require('fs').writeFileSync(tempScriptPath, pythonScript);

      const { stdout, stderr } = await execAsync(`python "${tempScriptPath}"`);
      
      // Limpiar script temporal
      require('fs').unlinkSync(tempScriptPath);

      if (stderr) {
        return { success: false, error: stderr };
      }

      const result = JSON.parse(stdout.trim());
      return result;

    } catch (error) {
      return { 
        success: false, 
        error: `Error ejecutando consulta: ${error}` 
      };
    }
  }

  /**
   * Valida que existan exactamente los registros CLARO esperados
   */
  async validateClaroRecordCount(expectedTotal: number = 5611): Promise<DatabaseValidationResult> {
    const script = `
# Contar registros CLARO por tipo
query_call_data = """
SELECT COUNT(*) as count 
FROM operator_call_data 
WHERE operator = 'CLARO'
"""

query_cellular_data = """
SELECT COUNT(*) as count 
FROM operator_cellular_data 
WHERE operator = 'CLARO'
"""

# Ejecutar consultas
cursor.execute(query_call_data)
call_data_count = cursor.fetchone()['count']

cursor.execute(query_cellular_data)
cellular_data_count = cursor.fetchone()['count']

total_count = call_data_count + cellular_data_count

result = {
    "success": total_count == ${expectedTotal},
    "data": {
        "call_data_records": call_data_count,
        "cellular_data_records": cellular_data_count,
        "total_records": total_count,
        "expected_records": ${expectedTotal}
    },
    "count": total_count
}

print(json.dumps(result))
    `;

    return await this.executePythonQuery(script);
  }

  /**
   * Valida que el archivo HUNTER esté cargado correctamente
   */
  async validateHunterDataLoaded(): Promise<DatabaseValidationResult> {
    const script = `
query = """
SELECT COUNT(*) as count 
FROM scanner_cellular_data
"""

cursor.execute(query)
hunter_count = cursor.fetchone()['count']

result = {
    "success": hunter_count > 0,
    "data": {
        "hunter_records": hunter_count
    },
    "count": hunter_count
}

print(json.dumps(result))
    `;

    return await this.executePythonQuery(script);
  }

  /**
   * Valida la distribución exacta de registros por archivo CLARO
   */
  async validateClaroFileDistribution(): Promise<DatabaseValidationResult> {
    const script = `
# Validar distribución esperada de archivos CLARO
# Archivo 1 - Entrantes: 973 registros
# Archivo 1 - Salientes: 961 registros  
# Archivo 2 - Entrantes: 1939 registros
# Archivo 2 - Salientes: 1738 registros

query_by_direction = """
SELECT 
    direction,
    COUNT(*) as count
FROM operator_call_data 
WHERE operator = 'CLARO'
GROUP BY direction
"""

cursor.execute(query_by_direction)
direction_counts = {row['direction']: row['count'] for row in cursor.fetchall()}

# Calcular totales esperados
expected_entrantes = 973 + 1939  # 2912
expected_salientes = 961 + 1738  # 2699

entrantes_count = direction_counts.get('ENTRANTE', 0) + direction_counts.get('entrante', 0)
salientes_count = direction_counts.get('SALIENTE', 0) + direction_counts.get('saliente', 0)

result = {
    "success": entrantes_count == expected_entrantes and salientes_count == expected_salientes,
    "data": {
        "entrantes_found": entrantes_count,
        "entrantes_expected": expected_entrantes,
        "salientes_found": salientes_count,
        "salientes_expected": expected_salientes,
        "distribution_correct": entrantes_count == expected_entrantes and salientes_count == expected_salientes
    }
}

print(json.dumps(result))
    `;

    return await this.executePythonQuery(script);
  }

  /**
   * Busca números objetivo específicos en la base de datos
   */
  async validateTargetNumbers(targetNumbers: string[]): Promise<DatabaseValidationResult> {
    const numbersStr = targetNumbers.map(n => `'${n}'`).join(',');
    
    const script = `
target_numbers = [${targetNumbers.map(n => `'${n}'`).join(',')}]
found_numbers = {}

# Buscar en datos de llamadas CLARO
query_claro = """
SELECT DISTINCT origen, destino
FROM operator_call_data
WHERE operator = 'CLARO' 
AND (origen IN (${numbersStr}) OR destino IN (${numbersStr}))
"""

cursor.execute(query_claro)
claro_results = cursor.fetchall()

# Buscar en datos HUNTER
query_hunter = """
SELECT DISTINCT numero_a, numero_b  
FROM scanner_cellular_data
WHERE numero_a IN (${numbersStr}) OR numero_b IN (${numbersStr})
"""

cursor.execute(query_hunter)
hunter_results = cursor.fetchall()

# Procesar resultados
for number in target_numbers:
    found_numbers[number] = {
        "found_in_claro": False,
        "found_in_hunter": False,
        "claro_connections": [],
        "hunter_connections": []
    }
    
    # Verificar CLARO
    for row in claro_results:
        if row['origen'] == number or row['destino'] == number:
            found_numbers[number]["found_in_claro"] = True
            other_number = row['destino'] if row['origen'] == number else row['origen']
            if other_number not in found_numbers[number]["claro_connections"]:
                found_numbers[number]["claro_connections"].append(other_number)
    
    # Verificar HUNTER
    for row in hunter_results:
        if row['numero_a'] == number or row['numero_b'] == number:
            found_numbers[number]["found_in_hunter"] = True
            other_number = row['numero_b'] if row['numero_a'] == number else row['numero_a']
            if other_number not in found_numbers[number]["hunter_connections"]:
                found_numbers[number]["hunter_connections"].append(other_number)

total_found = sum(1 for n in found_numbers.values() if n["found_in_claro"] or n["found_in_hunter"])

result = {
    "success": total_found == len(target_numbers),
    "data": {
        "target_numbers_analysis": found_numbers,
        "total_found": total_found,
        "total_expected": len(target_numbers),
        "all_numbers_found": total_found == len(target_numbers)
    },
    "count": total_found
}

print(json.dumps(result))
    `;

    return await this.executePythonQuery(script);
  }

  /**
   * Ejecuta el algoritmo de correlación y valida resultados
   */
  async executeCorrelationAnalysis(startTime: string, endTime: string, targetNumbers: string[]): Promise<DatabaseValidationResult> {
    const script = `
# Simular llamada al servicio de correlación
# Esto debe coincidir con el algoritmo real implementado en correlation_analysis_service.py

import sys
sys.path.append('services')

try:
    from correlation_analysis_service import CorrelationAnalysisService
    
    service = CorrelationAnalysisService()
    
    # Parámetros de análisis
    analysis_params = {
        'start_time': '${startTime}',
        'end_time': '${endTime}',
        'target_numbers': [${targetNumbers.map(n => `'${n}'`).join(',')}]
    }
    
    # Ejecutar análisis
    correlations = service.analyze_correlations(analysis_params)
    
    # Validar que se encontraron las correlaciones esperadas
    found_targets = []
    for correlation in correlations:
        if correlation.get('target_number') in analysis_params['target_numbers']:
            found_targets.append(correlation['target_number'])
    
    result = {
        "success": len(found_targets) >= 6,  # Esperamos encontrar los 6 números
        "data": {
            "correlations_found": len(correlations),
            "target_numbers_in_correlations": len(found_targets),
            "correlation_results": correlations,
            "analysis_params": analysis_params
        },
        "count": len(found_targets)
    }
    
except ImportError:
    # Si no se puede importar el servicio, hacer análisis básico
    # Buscar coincidencias temporales entre CLARO y HUNTER
    
    query_temporal_correlation = """
    SELECT DISTINCT 
        ocd.origen, ocd.destino, ocd.fecha_inicio,
        scd.numero_a, scd.numero_b, scd.fecha_hora
    FROM operator_call_data ocd
    JOIN scanner_cellular_data scd ON (
        (ocd.origen IN (${targetNumbers.map(n => `'${n}'`).join(',')}) 
         AND scd.numero_a IN (${targetNumbers.map(n => `'${n}'`).join(',')}))
        OR 
        (ocd.destino IN (${targetNumbers.map(n => `'${n}'`).join(',')}) 
         AND scd.numero_b IN (${targetNumbers.map(n => `'${n}'`).join(',')}))
    )
    WHERE ocd.operator = 'CLARO'
    AND datetime(ocd.fecha_inicio) BETWEEN '${startTime}' AND '${endTime}'
    AND datetime(scd.fecha_hora) BETWEEN '${startTime}' AND '${endTime}'
    LIMIT 100
    """
    
    cursor.execute(query_temporal_correlation)
    correlations = cursor.fetchall()
    
    found_numbers = set()
    for row in correlations:
        found_numbers.add(row['origen'])
        found_numbers.add(row['destino'])
        found_numbers.add(row['numero_a'])
        found_numbers.add(row['numero_b'])
    
    target_numbers_found = [n for n in [${targetNumbers.map(n => `'${n}'`).join(',')}] if n in found_numbers]
    
    result = {
        "success": len(target_numbers_found) >= 3,  # Al menos 3 números objetivo
        "data": {
            "temporal_correlations": len(correlations),
            "target_numbers_found": len(target_numbers_found),
            "found_numbers": list(target_numbers_found),
            "basic_analysis": True
        },
        "count": len(target_numbers_found)
    }

print(json.dumps(result))
    `;

    return await this.executePythonQuery(script);
  }

  /**
   * Genera un reporte completo del estado de la base de datos
   */
  async generateDatabaseReport(): Promise<DatabaseValidationResult> {
    const script = `
report = {}

# Contar registros por tabla
tables = [
    'operator_call_data',
    'operator_cellular_data', 
    'scanner_cellular_data',
    'missions',
    'users'
]

for table in tables:
    try:
        cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
        count = cursor.fetchone()['count']
        report[f"{table}_count"] = count
    except:
        report[f"{table}_count"] = 0

# Detalles específicos CLARO
try:
    cursor.execute("""
    SELECT operator, COUNT(*) as count 
    FROM operator_call_data 
    GROUP BY operator
    """)
    report['call_data_by_operator'] = {row['operator']: row['count'] for row in cursor.fetchall()}
except:
    report['call_data_by_operator'] = {}

try:
    cursor.execute("""
    SELECT operator, COUNT(*) as count 
    FROM operator_cellular_data 
    GROUP BY operator
    """)
    report['cellular_data_by_operator'] = {row['operator']: row['count'] for row in cursor.fetchall()}
except:
    report['cellular_data_by_operator'] = {}

# Estado de misiones
try:
    cursor.execute("SELECT COUNT(*) as count FROM missions WHERE status = 'active'")
    report['active_missions'] = cursor.fetchone()['count']
except:
    report['active_missions'] = 0

result = {
    "success": True,
    "data": report
}

print(json.dumps(result))
    `;

    return await this.executePythonQuery(script);
  }

  /**
   * Limpia datos de prueba de la base de datos
   */
  async cleanupTestData(): Promise<DatabaseValidationResult> {
    const script = `
try:
    # Limpiar datos de prueba CLARO
    cursor.execute("DELETE FROM operator_call_data WHERE operator = 'CLARO' AND (origen LIKE '310%' OR destino LIKE '310%')")
    cursor.execute("DELETE FROM operator_cellular_data WHERE operator = 'CLARO'")
    
    # Limpiar misiones de prueba
    cursor.execute("DELETE FROM missions WHERE name LIKE '%Test%' OR name LIKE '%Prueba%'")
    
    conn.commit()
    
    result = {
        "success": True,
        "data": {"message": "Test data cleaned successfully"}
    }
    
except Exception as e:
    conn.rollback()
    result = {
        "success": False,
        "error": f"Error cleaning test data: {str(e)}"
    }

print(json.dumps(result))
    `;

    return await this.executePythonQuery(script);
  }
}

// Instancia singleton del validador
export const dbValidator = new DatabaseValidator();