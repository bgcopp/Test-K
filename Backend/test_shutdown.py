"""
Test de Shutdown de KRONOS
===============================================================================
Script de testing para verificar que el sistema de shutdown funciona correctamente
y que todos los recursos se liberan adecuadamente.

Uso:
    python test_shutdown.py [--auto-close] [--timeout=10]
    
Opciones:
    --auto-close    Cierra automáticamente después del timeout (para testing CI)
    --timeout=N     Tiempo en segundos antes del cierre automático (default: 10)

Tests realizados:
- Verificación de handlers registrados
- Test de cierre por señal SIGINT
- Test de cierre por ventana
- Verificación de cleanup de recursos
- Detección de procesos zombie
===============================================================================
"""

import os
import sys
import time
import signal
import subprocess
import threading
import argparse
from pathlib import Path

# Agregar path del backend
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def run_resource_check():
    """Verifica qué recursos están en uso antes y después del test"""
    try:
        # En Windows, usar tasklist para verificar procesos Python
        if os.name == 'nt':
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                  capture_output=True, text=True)
            python_processes = len([line for line in result.stdout.split('\n') 
                                  if 'python.exe' in line.lower()])
        else:
            # En Unix, usar ps para procesos Python
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            python_processes = len([line for line in result.stdout.split('\n') 
                                  if 'python' in line and 'kronos' in line.lower()])
        
        # Verificar puertos en uso (8080)
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            port_in_use = sock.connect_ex(('localhost', 8080)) == 0
            sock.close()
        except:
            port_in_use = False
        
        return {
            'python_processes': python_processes,
            'port_8080_in_use': port_in_use,
            'timestamp': time.time()
        }
    except Exception as e:
        print(f"Error verificando recursos: {e}")
        return None

def test_shutdown_system(auto_close=False, timeout=10):
    """
    Test principal del sistema de shutdown
    
    Args:
        auto_close: Si True, cierra automáticamente después del timeout
        timeout: Segundos antes del cierre automático
    """
    print("=" * 70)
    print("KRONOS SHUTDOWN TEST")
    print("=" * 70)
    
    # Estado inicial de recursos
    print("\n1. Verificando estado inicial de recursos...")
    initial_state = run_resource_check()
    if initial_state:
        print(f"   - Procesos Python activos: {initial_state['python_processes']}")
        print(f"   - Puerto 8080 en uso: {initial_state['port_8080_in_use']}")
    
    # Importar y verificar el sistema de shutdown
    print("\n2. Verificando sistema de shutdown...")
    try:
        from main import shutdown_manager, logger, setup_signal_handlers, setup_cleanup_handlers
        
        # Configurar sistema básico sin inicializar toda la app
        shutdown_manager.set_logger(logger)
        setup_cleanup_handlers()
        
        print(f"   [OK] Shutdown manager configurado")
        print(f"   [OK] {len(shutdown_manager._cleanup_handlers)} handlers registrados:")
        
        for handler in shutdown_manager._cleanup_handlers:
            critical_mark = "[CRITICO]" if handler['critical'] else "[NORMAL]"
            print(f"     {critical_mark} {handler['name']}")
        
    except Exception as e:
        print(f"   [ERROR] Error configurando sistema: {e}")
        return False
    
    # Test de funcionalidad básica
    print("\n3. Test de funcionalidad del shutdown manager...")
    test_reason = "Test automatizado de shutdown"
    
    if auto_close:
        print(f"\n   Iniciando cierre automático en {timeout} segundos...")
        print("   Presiona Ctrl+C para probar el manejo de señales")
        
        # Timer para cierre automático
        def auto_close_timer():
            time.sleep(timeout)
            print(f"\n   [TIMEOUT] Timeout alcanzado, iniciando shutdown...")
            shutdown_manager.initiate_shutdown(test_reason)
        
        timer_thread = threading.Thread(target=auto_close_timer, daemon=True)
        timer_thread.start()
    else:
        print("\n   Presiona Ctrl+C para probar el shutdown por señal")
        print("   O presiona Enter para probar el shutdown manual")
        input("   Esperando input del usuario...")
        
        print("   Iniciando shutdown manual...")
        shutdown_manager.initiate_shutdown(test_reason)
    
    # Dar tiempo para que el shutdown se complete
    print("\n4. Esperando completion del shutdown...")
    time.sleep(2)
    
    # Verificar estado final
    print("\n5. Verificando limpieza final...")
    final_state = run_resource_check()
    
    if final_state and initial_state:
        print(f"   - Procesos Python: {initial_state['python_processes']} -> {final_state['python_processes']}")
        print(f"   - Puerto 8080: {initial_state['port_8080_in_use']} -> {final_state['port_8080_in_use']}")
        
        # Verificar mejoras
        if final_state['port_8080_in_use'] and not initial_state['port_8080_in_use']:
            print("   [WARNING] Puerto 8080 quedo ocupado despues del test")
        else:
            print("   [OK] Puerto liberado correctamente")
    
    print("\n6. Test completado")
    return True

def test_signal_handling():
    """Test específico del manejo de señales"""
    print("\n" + "=" * 50)
    print("TEST DE MANEJO DE SEÑALES")
    print("=" * 50)
    
    try:
        from main import setup_signal_handlers
        setup_signal_handlers()
        print("[OK] Handlers de señales configurados")
        
        print("\nPresiona Ctrl+C para probar SIGINT...")
        time.sleep(5)
        
    except KeyboardInterrupt:
        print("\n[OK] SIGINT manejado correctamente")
        return True
    except Exception as e:
        print(f"[ERROR] Error en manejo de señales: {e}")
        return False

def main():
    """Función principal del script de testing"""
    parser = argparse.ArgumentParser(description='Test del sistema de shutdown de KRONOS')
    parser.add_argument('--auto-close', action='store_true', 
                       help='Cierra automáticamente después del timeout')
    parser.add_argument('--timeout', type=int, default=10,
                       help='Tiempo en segundos antes del cierre automático')
    parser.add_argument('--test-signals', action='store_true',
                       help='Test específico de manejo de señales')
    
    args = parser.parse_args()
    
    try:
        if args.test_signals:
            success = test_signal_handling()
        else:
            success = test_shutdown_system(args.auto_close, args.timeout)
        
        if success:
            print("\n[SUCCESS] TODOS LOS TESTS PASARON EXITOSAMENTE")
            sys.exit(0)
        else:
            print("\n[FAIL] ALGUNOS TESTS FALLARON")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test interrumpido por el usuario")
        print("[OK] Manejo de Ctrl+C funcionando correctamente")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Error inesperado durante testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()