import { test, expect } from '@playwright/test';

test.describe('Manual Testing - Diagrama de Correlación', () => {

    test('Verificar aplicación y tomar screenshots', async ({ page }) => {
        console.log('🎯 Iniciando testing manual del diagrama de correlación');
        
        try {
            // 1. Navegar a la aplicación
            console.log('📍 Paso 1: Navegando a KRONOS...');
            await page.goto('http://localhost:8000', { 
                waitUntil: 'domcontentloaded',
                timeout: 10000 
            });
            
            await page.screenshot({ 
                path: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\test-results\\01-login-page.png',
                fullPage: true 
            });
            console.log('✅ Screenshot 1: Página de login capturada');

            // 2. Intentar login
            console.log('📍 Paso 2: Realizando login...');
            
            // Buscar campos de login
            const usernameField = page.locator('input[type="text"]').first();
            const passwordField = page.locator('input[type="password"]').first();
            
            if (await usernameField.isVisible({ timeout: 5000 })) {
                await usernameField.fill('admin');
                await passwordField.fill('admin123');
                
                const loginButton = page.locator('button[type="submit"]');
                await loginButton.click();
                
                await page.waitForTimeout(3000);
                
                await page.screenshot({ 
                    path: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\test-results\\02-post-login.png',
                    fullPage: true 
                });
                console.log('✅ Screenshot 2: Post-login capturado');
            }

            // 3. Navegar a misiones
            console.log('📍 Paso 3: Navegando a Misiones...');
            
            const missionsLink = page.locator('text=Misiones');
            if (await missionsLink.isVisible({ timeout: 5000 })) {
                await missionsLink.click();
                await page.waitForTimeout(2000);
                
                await page.screenshot({ 
                    path: 'C:\\Soluciones\BGC\\claude\\KNSOft\\test-results\\03-missions-page.png',
                    fullPage: true 
                });
                console.log('✅ Screenshot 3: Página de misiones capturada');
            }

            // 4. Buscar misión con datos
            console.log('📍 Paso 4: Buscando misión con datos...');
            
            const missionCard = page.locator('.bg-secondary').first();
            if (await missionCard.isVisible({ timeout: 5000 })) {
                await missionCard.click();
                await page.waitForTimeout(2000);
                
                await page.screenshot({ 
                    path: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\test-results\\04-mission-detail.png',
                    fullPage: true 
                });
                console.log('✅ Screenshot 4: Detalle de misión capturado');
                
                // 5. Buscar botón de correlación
                console.log('📍 Paso 5: Buscando funciones de correlación...');
                
                const correlationButton = page.locator('text=Ejecutar Correlación');
                if (await correlationButton.isVisible({ timeout: 5000 })) {
                    await correlationButton.click();
                    await page.waitForTimeout(5000); // Más tiempo para procesamiento
                    
                    await page.screenshot({ 
                        path: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\test-results\\05-correlation-executed.png',
                        fullPage: true 
                    });
                    console.log('✅ Screenshot 5: Correlación ejecutada');
                    
                    // 6. Buscar botón de tabla
                    console.log('📍 Paso 6: Buscando botón de tabla...');
                    
                    const tableButton = page.locator('button:has-text("Tabla")');
                    if (await tableButton.isVisible({ timeout: 5000 })) {
                        await tableButton.click();
                        await page.waitForTimeout(2000);
                        
                        await page.screenshot({ 
                            path: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\test-results\\06-correlation-table-modal.png',
                            fullPage: true 
                        });
                        console.log('✅ Screenshot 6: Modal de tabla abierto');
                        
                        // 7. VALIDACIÓN CRÍTICA: Buscar botón Diagrama
                        console.log('🔍 VALIDACIÓN CRÍTICA: Buscando botón Diagrama...');
                        
                        const diagramButton = page.locator('button:has-text("Diagrama")');
                        if (await diagramButton.isVisible({ timeout: 3000 })) {
                            console.log('🎉 ¡ÉXITO! Botón Diagrama encontrado');
                            
                            const isDisabled = await diagramButton.isDisabled();
                            console.log(`📊 Estado del botón: ${isDisabled ? 'DESHABILITADO' : 'HABILITADO'}`);
                            
                            if (!isDisabled) {
                                // 8. Intentar abrir diagrama
                                console.log('📍 Paso 8: Abriendo diagrama de red...');
                                
                                await diagramButton.click();
                                await page.waitForTimeout(2000);
                                
                                await page.screenshot({ 
                                    path: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\test-results\\07-network-diagram-modal.png',
                                    fullPage: true 
                                });
                                console.log('✅ Screenshot 7: Modal de diagrama abierto');
                                
                                // 9. Verificar componentes del diagrama
                                const diagramTitle = page.locator('text=Diagrama de Correlación de Red');
                                if (await diagramTitle.isVisible()) {
                                    console.log('✅ Título del diagrama presente');
                                    
                                    // Verificar controles
                                    const layoutControl = page.locator('text=Layout:');
                                    const statsText = page.locator('text=nodos');
                                    
                                    if (await layoutControl.isVisible()) {
                                        console.log('✅ Controles de layout presentes');
                                    }
                                    
                                    if (await statsText.isVisible()) {
                                        console.log('✅ Estadísticas del diagrama presentes');
                                    }
                                    
                                    // 10. Probar expansión de controles
                                    console.log('📍 Paso 10: Probando expansión de controles...');
                                    
                                    const expandButton = page.locator('svg').filter({ hasText: /chevron/i }).first();
                                    if (await expandButton.isVisible({ timeout: 2000 })) {
                                        await expandButton.click();
                                        await page.waitForTimeout(1000);
                                        
                                        await page.screenshot({ 
                                            path: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\test-results\\08-diagram-controls-expanded.png',
                                            fullPage: true 
                                        });
                                        console.log('✅ Screenshot 8: Controles expandidos');
                                    }
                                    
                                    // 11. Probar cierre del diagrama
                                    console.log('📍 Paso 11: Probando cierre del diagrama...');
                                    
                                    const closeButton = page.locator('button').filter({ hasText: /×|close/i }).first();
                                    if (await closeButton.isVisible({ timeout: 2000 })) {
                                        await closeButton.click();
                                        await page.waitForTimeout(1000);
                                        
                                        await page.screenshot({ 
                                            path: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\test-results\\09-diagram-closed.png',
                                            fullPage: true 
                                        });
                                        console.log('✅ Screenshot 9: Diagrama cerrado');
                                    }
                                }
                            } else {
                                console.log('⚠️ Botón Diagrama está deshabilitado (probablemente sin datos suficientes)');
                            }
                        } else {
                            console.log('❌ CRÍTICO: Botón Diagrama NO encontrado');
                        }
                    } else {
                        console.log('⚠️ Botón de tabla no encontrado (sin datos de correlación)');
                    }
                } else {
                    console.log('⚠️ Botón "Ejecutar Correlación" no encontrado');
                }
            } else {
                console.log('⚠️ No se encontraron misiones');
            }

        } catch (error) {
            console.error('❌ Error durante el testing:', error);
            
            await page.screenshot({ 
                path: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\test-results\\error-state.png',
                fullPage: true 
            });
        }

        console.log('🏁 Testing manual completado');
    });
});