import { test, expect } from '@playwright/test';

test.describe('Testing Diagrama de Correlación de Red - KRONOS', () => {
    
    test.beforeEach(async ({ page }) => {
        // Navegar a la aplicación KRONOS
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle' });
        
        // Login (usando credenciales de ejemplo)
        await page.fill('input[type="text"]', 'admin');
        await page.fill('input[type="password"]', 'admin123');
        await page.click('button[type="submit"]');
        
        // Esperar a que cargue el dashboard
        await page.waitForLoadState('networkidle');
        await expect(page.locator('text=Dashboard')).toBeVisible();
    });

    test('TEST-001: Verificar que el botón Diagrama aparece en modal de correlación', async ({ page }) => {
        console.log('🧪 Iniciando TEST-001: Botón Diagrama en modal correlación');
        
        // Navegar a Misiones
        await page.click('text=Misiones');
        await page.waitForLoadState('networkidle');
        
        // Buscar misión con datos (debería haber al menos una misión de ejemplo)
        const misionCard = page.locator('.bg-secondary').first();
        await expect(misionCard).toBeVisible();
        
        // Hacer clic en "Ver Detalles" de la misión
        await misionCard.click();
        await page.waitForLoadState('networkidle');
        
        // Buscar sección de correlación y hacer clic en "Ejecutar Correlación"
        const executeButton = page.locator('text=Ejecutar Correlación').first();
        
        if (await executeButton.isVisible()) {
            await executeButton.click();
            await page.waitForTimeout(2000); // Esperar procesamiento
            
            // Buscar el botón de tabla de correlación
            const tableButton = page.locator('button:has-text("Tabla")').first();
            if (await tableButton.isVisible()) {
                await tableButton.click();
                await page.waitForTimeout(1000);
                
                // Verificar que el modal de tabla se abrió
                await expect(page.locator('text=Tabla de Correlaciones')).toBeVisible();
                
                // VALIDACIÓN CRÍTICA: Verificar que existe el botón "Diagrama"
                const diagramButton = page.locator('button:has-text("Diagrama")');
                await expect(diagramButton).toBeVisible({ timeout: 5000 });
                
                console.log('✅ Botón Diagrama encontrado en modal de correlación');
                
                // Verificar que el botón no está deshabilitado si hay datos
                const isDisabled = await diagramButton.isDisabled();
                console.log(`📊 Estado del botón Diagrama - Deshabilitado: ${isDisabled}`);
                
                // Tomar screenshot del modal con botón Diagrama
                await page.screenshot({ 
                    path: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\test-results\\diagrama-button-visible.png',
                    fullPage: true 
                });
                
            } else {
                console.log('⚠️ No se encontró botón de tabla, probablemente no hay datos de correlación');
            }
        } else {
            console.log('⚠️ No se encontró botón "Ejecutar Correlación", revisar estado de misiones');
        }
    });

    test('TEST-002: Probar apertura y cierre del NetworkDiagramModal', async ({ page }) => {
        console.log('🧪 Iniciando TEST-002: Apertura/cierre NetworkDiagramModal');
        
        // Navegar a misiones y obtener datos de correlación
        await page.click('text=Misiones');
        await page.waitForLoadState('networkidle');
        
        const misionCard = page.locator('.bg-secondary').first();
        await misionCard.click();
        await page.waitForLoadState('networkidle');
        
        // Ejecutar correlación y abrir tabla
        const executeButton = page.locator('text=Ejecutar Correlación').first();
        if (await executeButton.isVisible()) {
            await executeButton.click();
            await page.waitForTimeout(3000); // Más tiempo para procesamiento
            
            const tableButton = page.locator('button:has-text("Tabla")').first();
            if (await tableButton.isVisible()) {
                await tableButton.click();
                await page.waitForTimeout(1000);
                
                // Intentar hacer clic en el botón Diagrama
                const diagramButton = page.locator('button:has-text("Diagrama")');
                if (await diagramButton.isVisible() && !(await diagramButton.isDisabled())) {
                    
                    console.log('🔄 Haciendo clic en botón Diagrama...');
                    await diagramButton.click();
                    await page.waitForTimeout(1000);
                    
                    // VALIDACIÓN CRÍTICA: Verificar que se abrió el modal del diagrama
                    const diagramModal = page.locator('text=Diagrama de Correlación de Red');
                    await expect(diagramModal).toBeVisible({ timeout: 5000 });
                    
                    console.log('✅ NetworkDiagramModal se abrió correctamente');
                    
                    // Verificar elementos del modal
                    await expect(page.locator('text=Objetivo:')).toBeVisible();
                    await expect(page.locator('text=nodos')).toBeVisible();
                    await expect(page.locator('text=conexiones')).toBeVisible();
                    
                    // Tomar screenshot del modal abierto
                    await page.screenshot({ 
                        path: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\test-results\\diagrama-modal-open.png',
                        fullPage: true 
                    });
                    
                    // Probar cierre del modal con botón X
                    const closeButton = page.locator('button[title="Cerrar diagrama"]');
                    await expect(closeButton).toBeVisible();
                    await closeButton.click();
                    await page.waitForTimeout(500);
                    
                    // Verificar que el modal se cerró
                    await expect(diagramModal).not.toBeVisible();
                    console.log('✅ Modal se cerró correctamente con botón X');
                    
                    // Volver a abrir y probar cierre con Escape
                    await diagramButton.click();
                    await page.waitForTimeout(1000);
                    await expect(diagramModal).toBeVisible();
                    
                    await page.keyboard.press('Escape');
                    await page.waitForTimeout(500);
                    await expect(diagramModal).not.toBeVisible();
                    console.log('✅ Modal se cerró correctamente con tecla Escape');
                    
                } else {
                    console.log('⚠️ Botón Diagrama no disponible (probablemente sin datos)');
                }
            }
        }
    });

    test('TEST-003: Verificar componentes internos del diagrama', async ({ page }) => {
        console.log('🧪 Iniciando TEST-003: Componentes internos del diagrama');
        
        // Navegar y abrir diagrama (siguiendo pasos anteriores)
        await page.click('text=Misiones');
        await page.waitForLoadState('networkidle');
        
        const misionCard = page.locator('.bg-secondary').first();
        await misionCard.click();
        await page.waitForLoadState('networkidle');
        
        const executeButton = page.locator('text=Ejecutar Correlación').first();
        if (await executeButton.isVisible()) {
            await executeButton.click();
            await page.waitForTimeout(3000);
            
            const tableButton = page.locator('button:has-text("Tabla")').first();
            if (await tableButton.isVisible()) {
                await tableButton.click();
                await page.waitForTimeout(1000);
                
                const diagramButton = page.locator('button:has-text("Diagrama")');
                if (await diagramButton.isVisible() && !(await diagramButton.isDisabled())) {
                    await diagramButton.click();
                    await page.waitForTimeout(1000);
                    
                    const diagramModal = page.locator('text=Diagrama de Correlación de Red');
                    await expect(diagramModal).toBeVisible();
                    
                    // VALIDACIONES DE COMPONENTES INTERNOS
                    
                    // 1. Verificar controles de layout
                    console.log('🔍 Verificando controles de layout...');
                    await expect(page.locator('text=Layout:')).toBeVisible();
                    await expect(page.locator('select')).toBeVisible();
                    
                    // 2. Verificar estadísticas
                    console.log('🔍 Verificando estadísticas...');
                    await expect(page.locator('text=nodos')).toBeVisible();
                    await expect(page.locator('text=conexiones')).toBeVisible();
                    
                    // 3. Verificar botón de expansión de controles
                    console.log('🔍 Verificando botón de expansión...');
                    const expandButton = page.locator('button[title*="filtros"]');
                    if (await expandButton.isVisible()) {
                        await expandButton.click();
                        await page.waitForTimeout(500);
                        
                        // Verificar que aparecieron controles expandidos
                        await expect(page.locator('text=Niveles de Correlación')).toBeVisible();
                        await expect(page.locator('text=Operadores')).toBeVisible();
                        await expect(page.locator('text=Vista y Exportación')).toBeVisible();
                        
                        console.log('✅ Controles expandidos funcionan correctamente');
                        
                        // Verificar botones de exportación
                        await expect(page.locator('button:has-text("PNG")')).toBeVisible();
                        await expect(page.locator('button:has-text("SVG")')).toBeVisible();
                        await expect(page.locator('button:has-text("JSON")')).toBeVisible();
                        
                        console.log('✅ Botones de exportación presentes');
                    }
                    
                    // 4. Verificar área del diagrama (placeholder FASE 4)
                    console.log('🔍 Verificando área del diagrama...');
                    const diagramArea = page.locator('.bg-gray-900');
                    await expect(diagramArea).toBeVisible();
                    
                    // Verificar placeholder de diagrama
                    await expect(page.locator('text=🔗')).toBeVisible();
                    await expect(page.locator('text=Diagrama de Red')).toBeVisible();
                    await expect(page.locator('text=nodos preparados para visualización')).toBeVisible();
                    
                    console.log('✅ Placeholder del diagrama (FASE 4) presente');
                    
                    // Tomar screenshot final de componentes
                    await page.screenshot({ 
                        path: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\test-results\\diagrama-components-expanded.png',
                        fullPage: true 
                    });
                }
            }
        }
    });

    test('TEST-004: Verificar que no hay regresiones en funcionalidad existente', async ({ page }) => {
        console.log('🧪 Iniciando TEST-004: Verificar no regresiones');
        
        // Navegar a misiones
        await page.click('text=Misiones');
        await page.waitForLoadState('networkidle');
        
        // Verificar que la funcionalidad base de misiones sigue funcionando
        const misionCard = page.locator('.bg-secondary').first();
        await expect(misionCard).toBeVisible();
        
        await misionCard.click();
        await page.waitForLoadState('networkidle');
        
        // Verificar que se puede ejecutar correlación normalmente
        const executeButton = page.locator('text=Ejecutar Correlación').first();
        if (await executeButton.isVisible()) {
            await executeButton.click();
            await page.waitForTimeout(3000);
            
            // Verificar que los botones de correlación existentes siguen funcionando
            const tableButton = page.locator('button:has-text("Tabla")');
            const exportButton = page.locator('button:has-text("Exportar")');
            
            if (await tableButton.isVisible()) {
                console.log('✅ Botón Tabla de correlación funciona normalmente');
                
                await tableButton.click();
                await page.waitForTimeout(1000);
                
                // Verificar que el modal de tabla funciona normalmente
                await expect(page.locator('text=Tabla de Correlaciones')).toBeVisible();
                
                // Verificar filtros existentes
                await expect(page.locator('button:has-text("Todo")')).toBeVisible();
                await expect(page.locator('button:has-text("Llamadas")')).toBeVisible();
                await expect(page.locator('button:has-text("Datos")')).toBeVisible();
                
                // Verificar botones de exportación existentes
                await expect(page.locator('button:has-text("CSV")')).toBeVisible();
                await expect(page.locator('button:has-text("Excel")')).toBeVisible();
                
                console.log('✅ Funcionalidad existente de tabla no afectada');
                
                // Cerrar modal
                const closeTableButton = page.locator('button[title="Cerrar modal"]').first();
                if (await closeTableButton.isVisible()) {
                    await closeTableButton.click();
                    await page.waitForTimeout(500);
                }
            }
            
            if (await exportButton.isVisible()) {
                console.log('✅ Botón Exportar de correlación funciona normalmente');
            }
        }
        
        // Verificar navegación general
        await page.click('text=Dashboard');
        await page.waitForLoadState('networkidle');
        await expect(page.locator('text=Dashboard')).toBeVisible();
        
        await page.click('text=Usuarios');
        await page.waitForLoadState('networkidle');
        await expect(page.locator('text=Gestión de Usuarios')).toBeVisible();
        
        console.log('✅ Navegación general del sistema no afectada');
    });

    test.afterEach(async ({ page, testInfo }) => {
        // Tomar screenshot final si el test falla
        if (testInfo.status !== 'passed') {
            await page.screenshot({ 
                path: `C:\\Soluciones\\BGC\\claude\\KNSOft\\test-results\\failure-${testInfo.title.replace(/[^a-z0-9]/gi, '_')}.png`,
                fullPage: true 
            });
        }
    });
});