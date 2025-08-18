import { test, expect } from '@playwright/test';
import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

/**
 * Tests de validación específica para números objetivo CLARO
 * Verifica que los números críticos (3104277553, 3224274851) se procesen correctamente
 * 
 * Casos cubiertos:
 * 1. Validación directa en base de datos SQLite
 * 2. Verificación de números objetivo específicos
 * 3. Validación de casos reportados por Boris
 * 4. Generación de reportes de validación
 */

test.describe('CLARO Target Numbers Validation', () => {
  const targetNumbers = [
    '3224274851', '3208611034', '3104277553', 
    '3102715509', '3143534707', '3214161903'
  ];

  const criticalNumbers = ['3104277553', '3224274851'];
  let backendPath: string;

  test.beforeAll(() => {
    backendPath = path.join(process.cwd(), 'Backend');
    
    // Verificar que existe el directorio Backend
    expect(fs.existsSync(backendPath)).toBeTruthy();
    
    // Verificar que existe la base de datos
    const dbPath = path.join(backendPath, 'kronos.db');
    console.log(`🔍 Verificando BD en: ${dbPath}`);
    
    if (!fs.existsSync(dbPath)) {
      console.log('⚠️  Base de datos no existe, los tests previos deben ejecutarse primero');
    }
  });

  test('01 - Validación directa de BD con script Python', async () => {
    console.log('🐍 Ejecutando validación Python de números objetivo...');

    await test.step('Ejecutar script verify_target_numbers.py', async () => {
      const scriptPath = path.join(backendPath, 'verify_target_numbers.py');
      
      // Verificar que el script existe
      expect(fs.existsSync(scriptPath)).toBeTruthy();
      
      try {
        // Ejecutar script Python de validación
        const result = execSync(`cd "${backendPath}" && python verify_target_numbers.py`, {
          encoding: 'utf-8',
          timeout: 60000 // 1 minuto timeout
        });
        
        console.log('📊 Resultado de validación Python:');
        console.log(result);
        
        // Verificar que el script se ejecutó sin errores críticos
        expect(result).toBeTruthy();
        expect(result.toLowerCase()).not.toContain('error');
        
        // Buscar indicadores de éxito
        const hasSuccessIndicators = result.includes('ÉXITO') || 
                                   result.includes('encontrados') ||
                                   result.includes('registros');
        
        expect(hasSuccessIndicators).toBeTruthy();
        
      } catch (error) {
        console.error('❌ Error ejecutando script Python:', error);
        throw error;
      }
    });

    await test.step('Verificar reporte JSON generado', async () => {
      // Buscar el reporte más reciente
      const files = fs.readdirSync(backendPath);
      const reportFiles = files.filter(f => f.startsWith('target_numbers_report_') && f.endsWith('.json'));
      
      if (reportFiles.length > 0) {
        // Ordenar por fecha y tomar el más reciente
        reportFiles.sort();
        const latestReport = reportFiles[reportFiles.length - 1];
        const reportPath = path.join(backendPath, latestReport);
        
        console.log(`📄 Analizando reporte: ${latestReport}`);
        
        const reportContent = fs.readFileSync(reportPath, 'utf-8');
        const report = JSON.parse(reportContent);
        
        // Validar estructura del reporte
        expect(report).toHaveProperty('target_numbers');
        expect(report).toHaveProperty('results');
        expect(report).toHaveProperty('summary');
        
        // Validar que se buscaron todos los números objetivo
        expect(report.target_numbers).toEqual(expect.arrayContaining(targetNumbers));
        
        // Validar resultados para números críticos
        criticalNumbers.forEach(number => {
          expect(report.results).toHaveProperty(number);
          const numberResult = report.results[number];
          
          console.log(`📱 ${number}: ${numberResult.total} registros encontrados`);
          
          // Verificar que hay registros para este número
          expect(numberResult.total).toBeGreaterThan(0);
        });
        
        // Verificar resumen general
        expect(report.summary.total_records).toBeGreaterThan(0);
        console.log(`✅ Total de registros en BD: ${report.summary.total_records}`);
        
      } else {
        console.log('⚠️  No se encontró reporte JSON generado');
      }
    });
  });

  test('02 - Validación del caso específico 3104277553 → 3224274851', async () => {
    console.log('🎯 Validando caso específico reportado por Boris...');

    await test.step('Verificar comunicación específica entre números', async () => {
      // Crear script SQL específico para esta validación
      const sqlQuery = `
        SELECT 
          id, operator, tipo_llamada, numero_origen, numero_destino,
          fecha_hora_llamada, duracion_segundos, celda_origen, celda_destino,
          file_upload_id, mission_id
        FROM operator_call_data
        WHERE (numero_origen = '3104277553' AND numero_destino = '3224274851')
           OR (numero_origen = '3224274851' AND numero_destino = '3104277553')
        ORDER BY fecha_hora_llamada DESC
        LIMIT 10;
      `;
      
      const tempSqlPath = path.join(backendPath, 'temp_boris_case_validation.sql');
      fs.writeFileSync(tempSqlPath, sqlQuery);
      
      try {
        // Ejecutar consulta SQLite
        const result = execSync(
          `cd "${backendPath}" && sqlite3 kronos.db < temp_boris_case_validation.sql`,
          { encoding: 'utf-8', timeout: 30000 }
        );
        
        console.log('📞 Registros de comunicación 3104277553 ↔ 3224274851:');
        console.log(result);
        
        // Verificar que hay al menos un registro
        const lines = result.trim().split('\n').filter(line => line.trim().length > 0);
        expect(lines.length).toBeGreaterThan(0);
        
        // Verificar que contiene los números objetivo
        const hasTargetNumbers = result.includes('3104277553') && result.includes('3224274851');
        expect(hasTargetNumbers).toBeTruthy();
        
        console.log(`✅ Encontrados ${lines.length} registros de comunicación entre números críticos`);
        
      } catch (error) {
        console.error('❌ Error en consulta SQL:', error);
        throw error;
      } finally {
        // Limpiar archivo temporal
        if (fs.existsSync(tempSqlPath)) {
          fs.unlinkSync(tempSqlPath);
        }
      }
    });
  });

  test('03 - Validación de cobertura completa de números objetivo', async () => {
    console.log('📊 Validando cobertura completa de números objetivo...');

    await test.step('Verificar todos los números objetivo en BD', async () => {
      const results: Record<string, number> = {};
      
      for (const number of targetNumbers) {
        const sqlQuery = `
          SELECT COUNT(*) as total
          FROM operator_call_data
          WHERE numero_origen = '${number}' 
             OR numero_destino = '${number}' 
             OR numero_objetivo = '${number}';
        `;
        
        try {
          const result = execSync(
            `cd "${backendPath}" && echo "${sqlQuery}" | sqlite3 kronos.db`,
            { encoding: 'utf-8', timeout: 15000 }
          );
          
          const count = parseInt(result.trim()) || 0;
          results[number] = count;
          
          console.log(`📱 ${number}: ${count} registros`);
          
        } catch (error) {
          console.error(`❌ Error consultando ${number}:`, error);
          results[number] = 0;
        }
      }
      
      // Validar que todos los números tienen al menos un registro
      const numbersWithRecords = Object.entries(results).filter(([_, count]) => count > 0);
      const coveragePercentage = (numbersWithRecords.length / targetNumbers.length) * 100;
      
      console.log(`📈 Cobertura: ${numbersWithRecords.length}/${targetNumbers.length} números (${coveragePercentage.toFixed(1)}%)`);
      
      // Verificar cobertura mínima del 80%
      expect(coveragePercentage).toBeGreaterThanOrEqual(80);
      
      // Los números críticos DEBEN tener registros
      criticalNumbers.forEach(number => {
        expect(results[number]).toBeGreaterThan(0);
      });
    });
  });

  test('04 - Validación de integridad de datos CLARO', async () => {
    console.log('🔍 Validando integridad de datos CLARO...');

    await test.step('Verificar estructura de datos cargados', async () => {
      const validationQueries = [
        {
          name: 'Registros con operador CLARO',
          query: "SELECT COUNT(*) FROM operator_call_data WHERE UPPER(operator) LIKE '%CLARO%';"
        },
        {
          name: 'Registros con fechas válidas',
          query: "SELECT COUNT(*) FROM operator_call_data WHERE fecha_hora_llamada IS NOT NULL AND fecha_hora_llamada != '';"
        },
        {
          name: 'Registros con duración válida',
          query: "SELECT COUNT(*) FROM operator_call_data WHERE duracion_segundos >= 0;"
        },
        {
          name: 'Registros con celdas válidas',
          query: "SELECT COUNT(*) FROM operator_call_data WHERE (celda_origen IS NOT NULL AND celda_origen != '') OR (celda_destino IS NOT NULL AND celda_destino != '');"
        }
      ];

      const results: Record<string, number> = {};

      for (const validation of validationQueries) {
        try {
          const result = execSync(
            `cd "${backendPath}" && echo "${validation.query}" | sqlite3 kronos.db`,
            { encoding: 'utf-8', timeout: 15000 }
          );
          
          const count = parseInt(result.trim()) || 0;
          results[validation.name] = count;
          
          console.log(`✅ ${validation.name}: ${count} registros`);
          
        } catch (error) {
          console.error(`❌ Error en validación ${validation.name}:`, error);
          results[validation.name] = 0;
        }
      }

      // Verificar que hay datos válidos
      expect(results['Registros con operador CLARO']).toBeGreaterThan(0);
      expect(results['Registros con fechas válidas']).toBeGreaterThan(0);
      
      // Generar reporte de integridad
      const integrityReport = {
        timestamp: new Date().toISOString(),
        validations: results,
        target_numbers_coverage: targetNumbers.length,
        critical_numbers: criticalNumbers,
        status: 'PASSED'
      };

      const reportPath = path.join(process.cwd(), 'test-results', 'claro-integrity-report.json');
      fs.mkdirSync(path.dirname(reportPath), { recursive: true });
      fs.writeFileSync(reportPath, JSON.stringify(integrityReport, null, 2));
      
      console.log(`📄 Reporte de integridad guardado: ${reportPath}`);
    });
  });

  test('05 - Generación de reporte consolidado de validación', async () => {
    console.log('📋 Generando reporte consolidado de validación...');

    await test.step('Crear reporte final de validación CLARO', async () => {
      const reportData = {
        test_suite: 'CLARO Target Numbers Validation',
        timestamp: new Date().toISOString(),
        target_numbers: targetNumbers,
        critical_numbers: criticalNumbers,
        summary: {
          total_tests: 5,
          passed_tests: 0, // Se actualizará según resultados
          database_path: path.join(backendPath, 'kronos.db'),
          validation_method: 'SQLite + Python scripts'
        },
        validations: {},
        recommendations: []
      };

      // Ejecutar validaciones finales
      const finalValidations = [
        {
          name: 'database_exists',
          query: 'SELECT name FROM sqlite_master WHERE type="table" AND name="operator_call_data";'
        },
        {
          name: 'total_records',
          query: 'SELECT COUNT(*) FROM operator_call_data;'
        },
        {
          name: 'claro_records',
          query: "SELECT COUNT(*) FROM operator_call_data WHERE UPPER(operator) LIKE '%CLARO%';"
        }
      ];

      for (const validation of finalValidations) {
        try {
          const result = execSync(
            `cd "${backendPath}" && echo "${validation.query}" | sqlite3 kronos.db`,
            { encoding: 'utf-8', timeout: 15000 }
          );
          
          const value = result.trim();
          reportData.validations[validation.name] = value;
          
          if (validation.name === 'database_exists' && value.includes('operator_call_data')) {
            reportData.summary.passed_tests++;
          } else if (validation.name !== 'database_exists' && parseInt(value) > 0) {
            reportData.summary.passed_tests++;
          }
          
        } catch (error) {
          reportData.validations[validation.name] = `ERROR: ${error}`;
        }
      }

      // Generar recomendaciones basadas en resultados
      if (parseInt(reportData.validations.total_records) === 0) {
        reportData.recommendations.push('BD vacía - ejecutar tests de carga primero');
      }
      
      if (parseInt(reportData.validations.claro_records) === 0) {
        reportData.recommendations.push('No hay registros CLARO - verificar proceso de carga');
      }

      // Guardar reporte final
      const finalReportPath = path.join(process.cwd(), 'test-results', 'claro-validation-final-report.json');
      fs.mkdirSync(path.dirname(finalReportPath), { recursive: true });
      fs.writeFileSync(finalReportPath, JSON.stringify(reportData, null, 2));
      
      console.log(`📄 Reporte final guardado: ${finalReportPath}`);
      console.log(`✅ Tests pasados: ${reportData.summary.passed_tests}/${reportData.summary.total_tests}`);
      
      // Verificar que al menos la mitad de las validaciones pasaron
      expect(reportData.summary.passed_tests).toBeGreaterThanOrEqual(Math.ceil(reportData.summary.total_tests / 2));
    });
  });
});