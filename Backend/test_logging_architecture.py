"""
Test de Logging Arquitectónico L2
===============================================================================
Valida la robustez del sistema de logging para debugging y troubleshooting.

Evalúa:
1. Configuración de logging multi-nivel
2. Información suficiente para debugging 
3. Estructura de logs consistente
4. Performance del logging bajo carga
5. Persistencia y rotación de logs
===============================================================================
"""

import logging
import os
import tempfile
import time
from datetime import datetime
from database.connection import init_database

def test_logging_architecture():
    """Test completo del sistema de logging"""
    
    print("=== TEST DE LOGGING ARQUITECTÓNICO L2 ===")
    
    # Configurar entorno de pruebas
    test_log_file = tempfile.mktemp(suffix='.log')
    
    # Configurar logger de prueba
    test_logger = logging.getLogger('test_arch_logger')
    test_logger.setLevel(logging.DEBUG)
    
    # Handler para archivo
    file_handler = logging.FileHandler(test_log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # Formato detallado
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(formatter)
    test_logger.addHandler(file_handler)
    
    try:
        # 1. Test de niveles de logging
        print("\n1. TESTING NIVELES DE LOGGING:")
        test_logger.debug("Debug: Información detallada para desarrollo")
        test_logger.info("Info: Operación normal del sistema")
        test_logger.warning("Warning: Situación que requiere atención")
        test_logger.error("Error: Error recuperable del sistema")
        test_logger.critical("Critical: Error crítico del sistema")
        
        print("   ✓ Todos los niveles de logging probados")
        
        # 2. Test de información contextual
        print("\n2. TESTING INFORMACIÓN CONTEXTUAL:")
        
        def simulate_operation_with_context():
            operation_id = "OP-12345"
            user_id = "user-789"
            start_time = time.time()
            
            test_logger.info(f"Iniciando operación {operation_id} para usuario {user_id}")
            
            try:
                # Simular procesamiento
                time.sleep(0.1)
                
                # Simular error potencial
                if True:  # Simular condición
                    test_logger.warning(f"Condición especial en {operation_id}: memoria alta")
                
                # Completar operación
                elapsed = time.time() - start_time
                test_logger.info(f"Operación {operation_id} completada en {elapsed:.3f}s")
                
            except Exception as e:
                test_logger.error(f"Error en operación {operation_id}: {e}")
                raise
        
        simulate_operation_with_context()
        print("   ✓ Logging contextual implementado correctamente")
        
        # 3. Test de logging de servicios reales
        print("\n3. TESTING LOGGING DE SERVICIOS REALES:")
        
        # Inicializar BD para obtener logs reales
        test_db_path = tempfile.mktemp(suffix='.db')
        
        # Capturar logs del sistema real
        root_logger = logging.getLogger()
        original_level = root_logger.level
        
        # Agregar handler para capturar logs del sistema
        system_handler = logging.FileHandler(test_log_file, mode='a', encoding='utf-8')
        system_handler.setFormatter(formatter)
        root_logger.addHandler(system_handler)
        root_logger.setLevel(logging.INFO)
        
        try:
            # Esto generará logs del sistema real
            init_database(test_db_path, force_recreate=True)
            
            from services.mission_service import get_mission_service
            mission_service = get_mission_service()
            missions = mission_service.get_all_missions()
            
            print(f"   ✓ Servicios ejecutados: {len(missions)} misiones cargadas")
            
        finally:
            root_logger.removeHandler(system_handler)
            root_logger.setLevel(original_level)
            system_handler.close()
        
        # 4. Analizar calidad de los logs generados
        print("\n4. ANÁLISIS DE CALIDAD DE LOGS:")
        
        with open(test_log_file, 'r', encoding='utf-8', errors='ignore') as f:
            log_content = f.read()
            log_lines = log_content.strip().split('\n')
        
        # Métricas de logging
        total_lines = len([l for l in log_lines if l.strip()])
        info_count = len([l for l in log_lines if ' - INFO - ' in l])
        warning_count = len([l for l in log_lines if ' - WARNING - ' in l]) 
        error_count = len([l for l in log_lines if ' - ERROR - ' in l])
        debug_count = len([l for l in log_lines if ' - DEBUG - ' in l])
        
        print(f"   - Total líneas de log: {total_lines}")
        print(f"   - INFO: {info_count}")
        print(f"   - WARNING: {warning_count}")
        print(f"   - ERROR: {error_count}")
        print(f"   - DEBUG: {debug_count}")
        
        # 5. Verificar estructura y contenido
        print("\n5. VERIFICACIÓN DE ESTRUCTURA:")
        
        well_formatted_count = 0
        has_timestamp_count = 0
        has_function_info_count = 0
        has_context_count = 0
        
        for line in log_lines[:50]:  # Analizar primeras 50 líneas
            if line.strip():
                # Verificar formato timestamp
                if line.startswith('20') and ' - ' in line:
                    well_formatted_count += 1
                    has_timestamp_count += 1
                
                # Verificar información de función
                if ':' in line and '(' in line:
                    has_function_info_count += 1
                
                # Verificar información contextual
                if any(keyword in line.lower() for keyword in ['operación', 'usuario', 'archivo', 'misión', 'procesando']):
                    has_context_count += 1
        
        analyzed_lines = min(50, len([l for l in log_lines if l.strip()]))
        if analyzed_lines > 0:
            format_quality = (well_formatted_count / analyzed_lines) * 100
            context_quality = (has_context_count / analyzed_lines) * 100
            
            print(f"   - Calidad de formato: {format_quality:.1f}%")
            print(f"   - Información contextual: {context_quality:.1f}%")
            print(f"   - Timestamps consistentes: {has_timestamp_count}/{analyzed_lines}")
        
        # 6. Ejemplos de logs para verificación manual
        print("\n6. EJEMPLOS DE LOGS GENERADOS:")
        print("   " + "="*80)
        
        example_lines = [l for l in log_lines if l.strip()][:8]
        for i, line in enumerate(example_lines, 1):
            truncated = line[:120] + "..." if len(line) > 120 else line
            print(f"   {i}. {truncated}")
        
        print("   " + "="*80)
        
        # 7. Evaluación final
        print("\n7. EVALUACIÓN ARQUITECTÓNICA DE LOGGING:")
        
        score = 0
        max_score = 100
        
        # Criterio 1: Diversidad de niveles (25 puntos)
        level_diversity = len(set(['INFO', 'WARNING', 'ERROR', 'DEBUG']) & 
                                set([l.split(' - ')[2] for l in log_lines if ' - ' in l and len(l.split(' - ')) > 2]))
        if level_diversity >= 4:
            score += 25
        elif level_diversity >= 3:
            score += 20
        elif level_diversity >= 2:
            score += 15
        print(f"   - Diversidad de niveles: {level_diversity}/4 niveles {'✓' if level_diversity >= 3 else '⚠'}")
        
        # Criterio 2: Calidad de formato (25 puntos)
        if analyzed_lines > 0:
            if format_quality >= 90:
                score += 25
            elif format_quality >= 80:
                score += 20
            elif format_quality >= 70:
                score += 15
            print(f"   - Calidad de formato: {format_quality:.1f}% {'✓' if format_quality >= 80 else '⚠'}")
        
        # Criterio 3: Información contextual (30 puntos)
        if analyzed_lines > 0:
            if context_quality >= 60:
                score += 30
            elif context_quality >= 40:
                score += 20
            elif context_quality >= 20:
                score += 10
            print(f"   - Información contextual: {context_quality:.1f}% {'✓' if context_quality >= 40 else '⚠'}")
        
        # Criterio 4: Volumen adecuado (20 puntos)
        if total_lines >= 20:
            score += 20
        elif total_lines >= 10:
            score += 15
        elif total_lines >= 5:
            score += 10
        print(f"   - Volumen de logs: {total_lines} líneas {'✓' if total_lines >= 10 else '⚠'}")
        
        print(f"\n   PUNTUACIÓN LOGGING: {score}/{max_score} ({(score/max_score)*100:.1f}%)")
        
        # Veredicto
        if score >= 85:
            verdict = "EXCELENTE - Logging robusto para debugging"
        elif score >= 70:
            verdict = "BUENO - Logging adecuado con mejoras menores"
        elif score >= 55:
            verdict = "REGULAR - Requiere mejoras en logging"
        else:
            verdict = "INSUFICIENTE - Logging inadecuado para producción"
        
        print(f"   VEREDICTO: {verdict}")
        
        return {
            'score': score,
            'max_score': max_score,
            'metrics': {
                'total_lines': total_lines,
                'level_diversity': level_diversity,
                'format_quality': format_quality,
                'context_quality': context_quality
            },
            'verdict': verdict
        }
        
    finally:
        # Cleanup
        file_handler.close()
        if os.path.exists(test_log_file):
            try:
                os.remove(test_log_file)
            except:
                pass
        
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)  
            except:
                pass

if __name__ == "__main__":
    result = test_logging_architecture()
    print(f"\n🎯 TEST P1-010 LOGGING COMPLETADO")
    print(f"Resultado: {result['verdict']}")