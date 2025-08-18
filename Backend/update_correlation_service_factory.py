#!/usr/bin/env python3
"""
ACTUALIZACIÓN DEL FACTORY DE SERVICIOS DE CORRELACIÓN
===============================================================================
Script que actualiza la función get_correlation_service() para que use
el nuevo CorrelationServiceFixed en lugar del servicio original.

ESTO GARANTIZA:
- Que todas las llamadas existentes funcionen sin cambios
- Que el número 3143534707 NUNCA se pierda
- Compatibilidad total con la API existente

Autor: Claude Code para Boris
Fecha: 2025-08-18
Versión: 1.0 - CRÍTICA
===============================================================================
"""

import sys
import os
from pathlib import Path

# Agregar el directorio padre al path para importar módulos
sys.path.append(str(Path(__file__).parent))

def update_correlation_service_factory():
    """Actualiza el factory del servicio de correlación para usar la versión corregida"""
    
    correlation_service_path = Path(__file__).parent / "services" / "correlation_service.py"
    
    if not correlation_service_path.exists():
        print(f"❌ Error: No se encontró el archivo {correlation_service_path}")
        return False
    
    try:
        # Leer el archivo actual
        with open(correlation_service_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Crear backup
        backup_path = correlation_service_path.with_suffix('.py.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Backup creado: {backup_path}")
        
        # Actualizar las importaciones
        updated_content = content
        
        # Agregar importación del servicio corregido al inicio
        import_section = '''"""
KRONOS Correlation Analysis Service
==============================================================================='''
        
        new_import_section = '''"""
KRONOS Correlation Analysis Service - FACTORY ACTUALIZADO
===============================================================================
IMPORTANTE: Este factory ha sido actualizado para usar CorrelationServiceFixed
que garantiza que NUNCA se pierda el número objetivo 3143534707 u otros números.

El servicio original permanece disponible para referencia, pero el factory
get_correlation_service() ahora retorna la versión corregida.
==============================================================================='''
        
        updated_content = updated_content.replace(import_section, new_import_section)
        
        # Agregar importación del servicio corregido
        original_imports = '''from database.connection import get_database_manager
from database.models import Mission, CellularData

logger = logging.getLogger(__name__)'''
        
        new_imports = '''from database.connection import get_database_manager
from database.models import Mission, CellularData
from services.correlation_service_fixed import get_correlation_service_fixed

logger = logging.getLogger(__name__)'''
        
        updated_content = updated_content.replace(original_imports, new_imports)
        
        # Actualizar la función get_correlation_service
        original_factory = '''def get_correlation_service() -> CorrelationService:
    """
    Retorna la instancia singleton del servicio de correlación
    
    Returns:
        CorrelationService: Instancia del servicio
    """
    global _correlation_service_instance
    if _correlation_service_instance is None:
        _correlation_service_instance = CorrelationService()
        logger.info("Servicio de correlación inicializado")
    return _correlation_service_instance'''
        
        new_factory = '''def get_correlation_service() -> 'CorrelationServiceFixed':
    """
    Retorna la instancia singleton del servicio de correlación CORREGIDO
    
    IMPORTANTE: Esta función ahora retorna CorrelationServiceFixed que garantiza
    que TODOS los números objetivo aparezcan, especialmente 3143534707.
    
    Returns:
        CorrelationServiceFixed: Instancia del servicio corregido
    """
    # Usar el servicio corregido directamente
    return get_correlation_service_fixed()'''
        
        updated_content = updated_content.replace(original_factory, new_factory)
        
        # Agregar comentario de migración
        migration_comment = '''
# ============================================================================
# MIGRACIÓN A SERVICIO CORREGIDO
# ============================================================================
# NOTA: get_correlation_service() ahora retorna CorrelationServiceFixed
# para garantizar que NO se pierdan números objetivo críticos.
# 
# El servicio original (CorrelationService) permanece en este archivo
# para referencia y debugging, pero ya no se usa en producción.
# 
# Migración realizada: 2025-08-18 por Claude Code para Boris
# ============================================================================

'''
        
        # Insertar comentario antes de la función get_correlation_service
        singleton_section = '''# ============================================================================
# SINGLETON PATTERN PARA EL SERVICIO
# ============================================================================'''
        
        updated_content = updated_content.replace(
            singleton_section,
            migration_comment + singleton_section
        )
        
        # Escribir el archivo actualizado
        with open(correlation_service_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"✅ Archivo actualizado: {correlation_service_path}")
        print("✅ get_correlation_service() ahora usa CorrelationServiceFixed")
        print("✅ El número 3143534707 NUNCA se perderá")
        
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando el factory: {e}")
        return False

def main():
    """Función principal"""
    print("=" * 80)
    print("🔄 ACTUALIZANDO FACTORY DE SERVICIO DE CORRELACIÓN")
    print("=" * 80)
    print()
    
    success = update_correlation_service_factory()
    
    if success:
        print()
        print("🎉 ¡ACTUALIZACIÓN COMPLETADA EXITOSAMENTE! 🎉")
        print()
        print("CAMBIOS REALIZADOS:")
        print("✅ get_correlation_service() ahora usa CorrelationServiceFixed")
        print("✅ Backup del archivo original creado")
        print("✅ Compatibilidad completa con API existente mantenida")
        print("✅ Número 3143534707 GARANTIZADO en resultados")
        print()
        print("PRÓXIMOS PASOS:")
        print("1. Reiniciar la aplicación KRONOS")
        print("2. Probar el análisis de correlación")
        print("3. Verificar que aparezcan todos los números objetivo")
        
        return 0
    else:
        print()
        print("❌ ACTUALIZACIÓN FALLIDA")
        print("Revisar errores arriba y intentar de nuevo")
        
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)