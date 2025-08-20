/**
 * Reporter Personalizado para Testing del Diagrama de Correlación
 * 
 * Genera reportes específicos con métricas de performance, 
 * accesibilidad y funcionalidad del diagrama interactivo.
 */

import { Reporter, TestCase, TestResult, FullResult } from '@playwright/test/reporter';
import * as fs from 'fs';
import * as path from 'path';

interface CorrelationTestMetrics {
    testName: string;
    status: 'passed' | 'failed' | 'skipped';
    duration: number;
    phase: 'FASE 1' | 'FASE 2' | 'FASE 3' | 'FASE 4' | 'REGRESIÓN' | 'PERFORMANCE' | 'ACCESIBILIDAD' | 'INTEGRACIÓN';
    category: 'functional' | 'performance' | 'accessibility' | 'regression' | 'integration';
    screenshots: string[];
    errors: string[];
    performance?: {
        loadTime?: number;
        renderTime?: number;
        memoryUsage?: number;
        nodeCount?: number;
        edgeCount?: number;
    };
}

interface CorrelationReportSummary {
    timestamp: string;
    totalTests: number;
    passed: number;
    failed: number;
    skipped: number;
    duration: number;
    phases: {
        [key: string]: {
            total: number;
            passed: number;
            failed: number;
        };
    };
    performance: {
        averageLoadTime: number;
        maxLoadTime: number;
        averageRenderTime: number;
        totalNodesRendered: number;
        totalEdgesRendered: number;
    };
    accessibility: {
        totalChecks: number;
        passed: number;
        failed: number;
    };
    regression: {
        totalChecks: number;
        passed: number;
        failed: number;
    };
}

class CorrelationDiagramReporter implements Reporter {
    private metrics: CorrelationTestMetrics[] = [];
    private outputPath: string;
    private startTime: number = 0;

    constructor() {
        this.outputPath = path.join(process.cwd(), 'test-results', 'correlation-diagram-detailed-report.json');
        
        // Crear directorio si no existe
        const dir = path.dirname(this.outputPath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
    }

    onBegin(): void {
        this.startTime = Date.now();
        console.log('\n🧪 Iniciando testing detallado del Diagrama de Correlación...');
        console.log('════════════════════════════════════════════════════════════');
    }

    onTestEnd(test: TestCase, result: TestResult): void {
        const testName = test.title;
        const phase = this.extractPhaseFromTitle(testName);
        const category = this.extractCategoryFromTitle(testName);
        
        const metric: CorrelationTestMetrics = {
            testName,
            status: result.status,
            duration: result.duration,
            phase,
            category,
            screenshots: result.attachments
                .filter(a => a.name === 'screenshot')
                .map(a => a.path || ''),
            errors: result.errors.map(e => e.message || e.toString()),
            performance: this.extractPerformanceMetrics(result)
        };

        this.metrics.push(metric);

        // Logging en tiempo real
        const statusIcon = result.status === 'passed' ? '✅' : 
                          result.status === 'failed' ? '❌' : '⏭️';
        const phaseIcon = this.getPhaseIcon(phase);
        
        console.log(`${statusIcon} ${phaseIcon} ${testName} (${result.duration}ms)`);
        
        if (result.status === 'failed' && result.errors.length > 0) {
            console.log(`   ❌ Error: ${result.errors[0].message}`);
        }
        
        if (metric.performance) {
            const perf = metric.performance;
            if (perf.loadTime) console.log(`   ⚡ Load Time: ${perf.loadTime}ms`);
            if (perf.nodeCount) console.log(`   📊 Nodes: ${perf.nodeCount}`);
            if (perf.edgeCount) console.log(`   🔗 Edges: ${perf.edgeCount}`);
        }
    }

    onEnd(result: FullResult): void {
        const endTime = Date.now();
        const totalDuration = endTime - this.startTime;

        console.log('\n════════════════════════════════════════════════════════════');
        console.log('📋 Generando reporte detallado...');

        const summary = this.generateSummary(totalDuration);
        
        // Guardar reporte detallado
        const report = {
            summary,
            metrics: this.metrics,
            generatedAt: new Date().toISOString(),
            testEnvironment: {
                platform: process.platform,
                nodeVersion: process.version,
                playwrightVersion: require('@playwright/test/package.json').version
            }
        };

        fs.writeFileSync(this.outputPath, JSON.stringify(report, null, 2));

        // Generar reporte en consola
        this.printConsoleSummary(summary);
        
        // Generar reporte HTML personalizado
        this.generateHTMLReport(report);

        console.log(`\n💾 Reporte detallado guardado en: ${this.outputPath}`);
    }

    private extractPhaseFromTitle(title: string): CorrelationTestMetrics['phase'] {
        if (title.includes('FASE 1')) return 'FASE 1';
        if (title.includes('FASE 2')) return 'FASE 2';
        if (title.includes('FASE 3')) return 'FASE 3';
        if (title.includes('FASE 4')) return 'FASE 4';
        if (title.includes('REGRESIÓN')) return 'REGRESIÓN';
        if (title.includes('PERFORMANCE')) return 'PERFORMANCE';
        if (title.includes('ACCESIBILIDAD')) return 'ACCESIBILIDAD';
        if (title.includes('INTEGRACIÓN')) return 'INTEGRACIÓN';
        return 'FASE 1'; // default
    }

    private extractCategoryFromTitle(title: string): CorrelationTestMetrics['category'] {
        if (title.includes('PERFORMANCE')) return 'performance';
        if (title.includes('ACCESIBILIDAD')) return 'accessibility';
        if (title.includes('REGRESIÓN')) return 'regression';
        if (title.includes('INTEGRACIÓN')) return 'integration';
        return 'functional';
    }

    private getPhaseIcon(phase: string): string {
        const icons: { [key: string]: string } = {
            'FASE 1': '🎭',
            'FASE 2': '⚛️',
            'FASE 3': '🎮',
            'FASE 4': '✨',
            'REGRESIÓN': '🔄',
            'PERFORMANCE': '⚡',
            'ACCESIBILIDAD': '♿',
            'INTEGRACIÓN': '🔌'
        };
        return icons[phase] || '🧪';
    }

    private extractPerformanceMetrics(result: TestResult): CorrelationTestMetrics['performance'] | undefined {
        // Extraer métricas de performance de stdout/stderr si están disponibles
        const stdout = result.stdout.join('\n');
        
        const loadTimeMatch = stdout.match(/Load Time: (\d+)ms/);
        const renderTimeMatch = stdout.match(/Render Time: (\d+)ms/);
        const nodeCountMatch = stdout.match(/Nodes: (\d+)/);
        const edgeCountMatch = stdout.match(/Edges: (\d+)/);
        
        if (loadTimeMatch || renderTimeMatch || nodeCountMatch || edgeCountMatch) {
            return {
                loadTime: loadTimeMatch ? parseInt(loadTimeMatch[1]) : undefined,
                renderTime: renderTimeMatch ? parseInt(renderTimeMatch[1]) : undefined,
                nodeCount: nodeCountMatch ? parseInt(nodeCountMatch[1]) : undefined,
                edgeCount: edgeCountMatch ? parseInt(edgeCountMatch[1]) : undefined
            };
        }
        
        return undefined;
    }

    private generateSummary(totalDuration: number): CorrelationReportSummary {
        const totalTests = this.metrics.length;
        const passed = this.metrics.filter(m => m.status === 'passed').length;
        const failed = this.metrics.filter(m => m.status === 'failed').length;
        const skipped = this.metrics.filter(m => m.status === 'skipped').length;

        // Agrupar por fases
        const phases: { [key: string]: { total: number; passed: number; failed: number } } = {};
        
        for (const metric of this.metrics) {
            if (!phases[metric.phase]) {
                phases[metric.phase] = { total: 0, passed: 0, failed: 0 };
            }
            
            phases[metric.phase].total++;
            if (metric.status === 'passed') phases[metric.phase].passed++;
            if (metric.status === 'failed') phases[metric.phase].failed++;
        }

        // Métricas de performance
        const performanceMetrics = this.metrics.filter(m => m.performance);
        const loadTimes = performanceMetrics
            .map(m => m.performance?.loadTime)
            .filter((t): t is number => t !== undefined);
        
        const renderTimes = performanceMetrics
            .map(m => m.performance?.renderTime)
            .filter((t): t is number => t !== undefined);

        const nodeCounts = performanceMetrics
            .map(m => m.performance?.nodeCount)
            .filter((n): n is number => n !== undefined);

        const edgeCounts = performanceMetrics
            .map(m => m.performance?.edgeCount)
            .filter((e): e is number => e !== undefined);

        // Métricas de accesibilidad y regresión
        const accessibilityTests = this.metrics.filter(m => m.category === 'accessibility');
        const regressionTests = this.metrics.filter(m => m.category === 'regression');

        return {
            timestamp: new Date().toISOString(),
            totalTests,
            passed,
            failed,
            skipped,
            duration: totalDuration,
            phases,
            performance: {
                averageLoadTime: loadTimes.length > 0 ? loadTimes.reduce((a, b) => a + b, 0) / loadTimes.length : 0,
                maxLoadTime: loadTimes.length > 0 ? Math.max(...loadTimes) : 0,
                averageRenderTime: renderTimes.length > 0 ? renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length : 0,
                totalNodesRendered: nodeCounts.length > 0 ? Math.max(...nodeCounts) : 0,
                totalEdgesRendered: edgeCounts.length > 0 ? Math.max(...edgeCounts) : 0
            },
            accessibility: {
                totalChecks: accessibilityTests.length,
                passed: accessibilityTests.filter(t => t.status === 'passed').length,
                failed: accessibilityTests.filter(t => t.status === 'failed').length
            },
            regression: {
                totalChecks: regressionTests.length,
                passed: regressionTests.filter(t => t.status === 'passed').length,
                failed: regressionTests.filter(t => t.status === 'failed').length
            }
        };
    }

    private printConsoleSummary(summary: CorrelationReportSummary): void {
        console.log('\n📊 RESUMEN DE TESTING - DIAGRAMA DE CORRELACIÓN');
        console.log('════════════════════════════════════════════════════════════');
        
        // Resumen general
        const successRate = (summary.passed / summary.totalTests * 100).toFixed(1);
        console.log(`📈 Success Rate: ${successRate}% (${summary.passed}/${summary.totalTests})`);
        console.log(`⏱️  Total Duration: ${(summary.duration / 1000).toFixed(1)}s`);
        console.log(`✅ Passed: ${summary.passed}`);
        console.log(`❌ Failed: ${summary.failed}`);
        console.log(`⏭️  Skipped: ${summary.skipped}`);
        
        // Resumen por fases
        console.log('\n🎭 RESUMEN POR FASES:');
        for (const [phase, stats] of Object.entries(summary.phases)) {
            const phaseRate = (stats.passed / stats.total * 100).toFixed(1);
            const icon = this.getPhaseIcon(phase);
            console.log(`${icon} ${phase}: ${phaseRate}% (${stats.passed}/${stats.total})`);
        }

        // Métricas de performance
        if (summary.performance.averageLoadTime > 0) {
            console.log('\n⚡ MÉTRICAS DE PERFORMANCE:');
            console.log(`📊 Load Time Promedio: ${summary.performance.averageLoadTime.toFixed(0)}ms`);
            console.log(`📊 Load Time Máximo: ${summary.performance.maxLoadTime}ms`);
            console.log(`🔵 Nodos Renderizados: ${summary.performance.totalNodesRendered}`);
            console.log(`🔗 Aristas Renderizadas: ${summary.performance.totalEdgesRendered}`);
        }

        // Métricas de accesibilidad
        if (summary.accessibility.totalChecks > 0) {
            const accessibilityRate = (summary.accessibility.passed / summary.accessibility.totalChecks * 100).toFixed(1);
            console.log(`\n♿ ACCESIBILIDAD: ${accessibilityRate}% (${summary.accessibility.passed}/${summary.accessibility.totalChecks})`);
        }

        // Métricas de regresión
        if (summary.regression.totalChecks > 0) {
            const regressionRate = (summary.regression.passed / summary.regression.totalChecks * 100).toFixed(1);
            console.log(`🔄 REGRESIÓN: ${regressionRate}% (${summary.regression.passed}/${summary.regression.totalChecks})`);
        }

        console.log('\n════════════════════════════════════════════════════════════');
    }

    private generateHTMLReport(report: any): void {
        const htmlPath = path.join(process.cwd(), 'test-results', 'correlation-diagram-custom-report.html');
        
        const html = `
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Testing - Diagrama de Correlación</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #e0e0e0; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 40px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }
        .card { background: #2a2a2a; border-radius: 8px; padding: 20px; border: 1px solid #3a3a3a; }
        .card h3 { margin-top: 0; color: #60a5fa; }
        .metric { display: flex; justify-content: space-between; margin: 10px 0; }
        .metric-label { color: #9ca3af; }
        .metric-value { font-weight: bold; }
        .phase-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .phase-card { background: #2a2a2a; border-radius: 6px; padding: 15px; border-left: 4px solid #60a5fa; }
        .test-details { background: #2a2a2a; border-radius: 8px; padding: 20px; margin-top: 20px; }
        .test-item { margin: 10px 0; padding: 10px; border-radius: 4px; background: #1f1f1f; }
        .passed { border-left: 4px solid #10b981; }
        .failed { border-left: 4px solid #ef4444; }
        .skipped { border-left: 4px solid #f59e0b; }
        .timestamp { color: #6b7280; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🕸️ Reporte de Testing - Diagrama de Correlación</h1>
            <p class="timestamp">Generado: ${new Date(report.summary.timestamp).toLocaleString('es')}</p>
        </div>
        
        <div class="summary">
            <div class="card">
                <h3>📊 Resumen General</h3>
                <div class="metric">
                    <span class="metric-label">Total Tests:</span>
                    <span class="metric-value">${report.summary.totalTests}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Exitosos:</span>
                    <span class="metric-value" style="color: #10b981">${report.summary.passed}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Fallidos:</span>
                    <span class="metric-value" style="color: #ef4444">${report.summary.failed}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Success Rate:</span>
                    <span class="metric-value">${(report.summary.passed / report.summary.totalTests * 100).toFixed(1)}%</span>
                </div>
            </div>
            
            <div class="card">
                <h3>⚡ Performance</h3>
                <div class="metric">
                    <span class="metric-label">Load Time Promedio:</span>
                    <span class="metric-value">${report.summary.performance.averageLoadTime.toFixed(0)}ms</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Load Time Máximo:</span>
                    <span class="metric-value">${report.summary.performance.maxLoadTime}ms</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Nodos Renderizados:</span>
                    <span class="metric-value">${report.summary.performance.totalNodesRendered}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Aristas Renderizadas:</span>
                    <span class="metric-value">${report.summary.performance.totalEdgesRendered}</span>
                </div>
            </div>
            
            <div class="card">
                <h3>♿ Accesibilidad</h3>
                <div class="metric">
                    <span class="metric-label">Tests Ejecutados:</span>
                    <span class="metric-value">${report.summary.accessibility.totalChecks}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Exitosos:</span>
                    <span class="metric-value" style="color: #10b981">${report.summary.accessibility.passed}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Success Rate:</span>
                    <span class="metric-value">${report.summary.accessibility.totalChecks > 0 ? (report.summary.accessibility.passed / report.summary.accessibility.totalChecks * 100).toFixed(1) : 0}%</span>
                </div>
            </div>
        </div>
        
        <h2>🎭 Resultados por Fases</h2>
        <div class="phase-grid">
            ${Object.entries(report.summary.phases).map(([phase, stats]: [string, any]) => `
                <div class="phase-card">
                    <h4>${phase}</h4>
                    <div class="metric">
                        <span>Success Rate:</span>
                        <span>${(stats.passed / stats.total * 100).toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span>Passed:</span>
                        <span style="color: #10b981">${stats.passed}</span>
                    </div>
                    <div class="metric">
                        <span>Failed:</span>
                        <span style="color: #ef4444">${stats.failed}</span>
                    </div>
                </div>
            `).join('')}
        </div>
        
        <div class="test-details">
            <h2>📋 Detalles de Tests</h2>
            ${report.metrics.map((metric: CorrelationTestMetrics) => `
                <div class="test-item ${metric.status}">
                    <h4>${metric.testName}</h4>
                    <p><strong>Fase:</strong> ${metric.phase} | <strong>Duración:</strong> ${metric.duration}ms | <strong>Estado:</strong> ${metric.status}</p>
                    ${metric.errors.length > 0 ? `<p style="color: #ef4444"><strong>Error:</strong> ${metric.errors[0]}</p>` : ''}
                    ${metric.performance ? `
                        <p><strong>Performance:</strong> 
                        ${metric.performance.loadTime ? `Load: ${metric.performance.loadTime}ms ` : ''}
                        ${metric.performance.nodeCount ? `Nodes: ${metric.performance.nodeCount} ` : ''}
                        ${metric.performance.edgeCount ? `Edges: ${metric.performance.edgeCount}` : ''}
                        </p>
                    ` : ''}
                </div>
            `).join('')}
        </div>
    </div>
</body>
</html>`;

        fs.writeFileSync(htmlPath, html);
        console.log(`🌐 Reporte HTML personalizado generado: ${htmlPath}`);
    }
}

export default CorrelationDiagramReporter;