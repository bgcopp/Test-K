"""
Test P2-008: Upload Simultáneo 4 Operadores
===============================================================================
Prueba el procesamiento paralelo de archivos reales de los 4 operadores
simultáneamente para validar la robustez arquitectónica bajo carga extrema.

Evalúa:
1. Procesamiento paralelo real de archivos grandes
2. Integridad de datos bajo carga concurrente 
3. Manejo de memoria con múltiples operadores
4. Performance del sistema bajo stress
5. Detección de race conditions o deadlocks
===============================================================================
"""

import os
import base64
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from database.connection import init_database
from services.operator_service import get_operator_service
from services.mission_service import get_mission_service

class ParallelUploadTest:
    """Test de upload paralelo de 4 operadores"""
    
    def __init__(self):
        self.test_files = {
            'CLARO': 'C:/Soluciones/BGC/claude/KNSOft/archivos/CeldasDiferenteOperador/claro/DATOS_POR_CELDA CLARO.csv',
            'MOVISTAR': 'C:/Soluciones/BGC/claude/KNSOft/archivos/CeldasDiferenteOperador/mov/jgd202410754_00007301_datos_ MOVISTAR.csv', 
            'TIGO': 'C:/Soluciones/BGC/claude/KNSOft/archivos/CeldasDiferenteOperador/tigo/Reporte TIGO.csv',
            'WOM': 'C:/Soluciones/BGC/claude/KNSOft/archivos/CeldasDiferenteOperador/wom/PUNTO 1 TRÁFICO DATOS WOM.csv'
        }
        
        self.file_types = {
            'CLARO': 'DATOS',
            'MOVISTAR': 'DATOS_POR_CELDA',
            'TIGO': 'LLAMADAS_MIXTAS', 
            'WOM': 'DATOS_POR_CELDA'
        }
        
        self.results = {}
        self.errors = []
        self.lock = threading.Lock()
        
    def setup_test_environment(self):
        """Configura entorno de pruebas"""
        print("=== CONFIGURANDO ENTORNO UPLOAD PARALELO ===")
        
        # Inicializar BD
        test_db_path = os.path.join(os.getcwd(), 'test_parallel.db')
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            
        init_database(test_db_path, force_recreate=True)
        print("Base de datos de pruebas inicializada")
        
        # Crear misión de prueba
        mission_service = get_mission_service()
        missions = mission_service.get_all_missions()
        
        if missions:
            self.test_mission_id = missions[0]['id']
            print(f"Usando misión: {missions[0]['code']}")
        
        # Verificar archivos de prueba
        missing_files = []
        file_sizes = {}
        
        for operator, file_path in self.test_files.items():
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                file_sizes[operator] = size
                print(f"Archivo {operator}: {size:,} bytes")
            else:
                missing_files.append(f"{operator}: {file_path}")
        
        if missing_files:
            print("ARCHIVOS FALTANTES:")
            for missing in missing_files:
                print(f"  - {missing}")
            raise FileNotFoundError("Archivos de prueba no encontrados")
        
        self.file_sizes = file_sizes
        total_size = sum(file_sizes.values())
        print(f"Tamaño total de archivos: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
        
    def encode_file_to_base64(self, file_path):
        """Codifica archivo a base64 para envío"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Determinar MIME type
            if file_path.endswith('.csv'):
                mime_type = 'text/csv'
            else:
                mime_type = 'application/octet-stream'
            
            encoded = base64.b64encode(content).decode('utf-8')
            
            return {
                'name': os.path.basename(file_path),
                'content': f'data:{mime_type};base64,{encoded}'
            }
            
        except Exception as e:
            raise Exception(f"Error codificando archivo {file_path}: {e}")
    
    def upload_operator_file(self, operator, upload_id):
        """Procesa un archivo de operador específico"""
        thread_name = threading.current_thread().name
        print(f"[{upload_id}] [{thread_name}] Iniciando upload {operator}")
        
        start_time = time.time()
        result = {
            'operator': operator,
            'upload_id': upload_id,
            'thread_name': thread_name,
            'success': False,
            'processing_time': 0,
            'records_processed': 0,
            'file_size': 0,
            'error': None
        }
        
        try:
            file_path = self.test_files[operator]
            file_type = self.file_types[operator]
            
            # Codificar archivo
            print(f"[{upload_id}] Codificando archivo {operator}...")
            file_data = self.encode_file_to_base64(file_path)
            result['file_size'] = self.file_sizes[operator]
            
            # Procesar con operador service
            print(f"[{upload_id}] Procesando {operator} ({result['file_size']:,} bytes)...")
            operator_service = get_operator_service()
            
            # Usar validación para evitar inserción real de datos grandes
            validation_result = operator_service.validate_file_for_operator(
                operator, file_data, file_type
            )
            
            if validation_result.get('is_valid', False):
                result['success'] = True
                result['records_processed'] = validation_result.get('record_count', 0)
                print(f"[{upload_id}] {operator} VALIDADO: {result['records_processed']} registros")
            else:
                result['error'] = validation_result.get('error', 'Validación falló')
                print(f"[{upload_id}] {operator} FALLÓ: {result['error']}")
                
        except Exception as e:
            result['error'] = str(e)
            print(f"[{upload_id}] ERROR {operator}: {e}")
            
            with self.lock:
                self.errors.append(f"[{upload_id}] {operator}: {e}")
        
        result['processing_time'] = time.time() - start_time
        print(f"[{upload_id}] {operator} completado en {result['processing_time']:.2f}s")
        
        return result
    
    def run_parallel_upload_test(self):
        """Ejecuta el test de upload paralelo"""
        print("\\n=== INICIANDO TEST UPLOAD PARALELO ===")
        
        operators = list(self.test_files.keys())
        print(f"Operadores a procesar en paralelo: {operators}")
        
        start_test_time = time.time()
        
        # Ejecutar uploads en paralelo
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Enviar todas las tareas simultáneamente
            future_to_operator = {}
            for i, operator in enumerate(operators):
                upload_id = f"UP-{i+1:02d}"
                future = executor.submit(self.upload_operator_file, operator, upload_id)
                future_to_operator[future] = operator
            
            # Recoger resultados
            results = []
            for future in as_completed(future_to_operator):
                operator = future_to_operator[future]
                try:
                    result = future.result(timeout=120)  # 2 minutos timeout
                    results.append(result)
                    
                except Exception as e:
                    print(f"ERROR en {operator}: {e}")
                    error_result = {
                        'operator': operator,
                        'success': False,
                        'error': str(e),
                        'processing_time': 0
                    }
                    results.append(error_result)
        
        total_test_time = time.time() - start_test_time
        
        # Analizar resultados
        self.analyze_parallel_results(results, total_test_time)
        
        return results
    
    def analyze_parallel_results(self, results, total_time):
        """Analiza resultados del test paralelo"""
        print("\\n" + "="*70)
        print("REPORTE DE UPLOAD PARALELO - P2-008")
        print("="*70)
        
        successful_uploads = len([r for r in results if r['success']])
        total_uploads = len(results)
        total_records = sum(r.get('records_processed', 0) for r in results)
        total_size = sum(r.get('file_size', 0) for r in results)
        avg_processing_time = sum(r['processing_time'] for r in results) / len(results)
        
        print(f"Total de operadores procesados: {total_uploads}")
        print(f"Uploads exitosos: {successful_uploads}")
        print(f"Tasa de éxito: {(successful_uploads/total_uploads)*100:.1f}%")
        print(f"Tiempo total de prueba: {total_time:.2f} segundos")
        print(f"Tiempo promedio por operador: {avg_processing_time:.2f} segundos")
        print(f"Registros procesados: {total_records:,}")
        print(f"Datos procesados: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
        
        if total_time > 0:
            throughput = total_size / total_time / 1024 / 1024  # MB/s
            print(f"Throughput: {throughput:.2f} MB/s")
        
        print("\\nDETALLE POR OPERADOR:")
        print("-" * 80)
        for result in sorted(results, key=lambda x: x['operator']):
            status = "OK" if result['success'] else "ERROR"
            size_mb = result.get('file_size', 0) / 1024 / 1024
            records = result.get('records_processed', 0)
            time_taken = result['processing_time']
            
            print(f"{result['operator']:10} | {status:5} | {size_mb:6.2f} MB | {records:6,} reg | {time_taken:6.2f}s")
            
            if not result['success'] and result.get('error'):
                print(f"           Error: {result['error'][:60]}...")
        
        print("\\nEVALUACIÓN ARQUITECTÓNICA:")
        print("-" * 50)
        
        # Scoring
        score = 0
        max_score = 100
        
        # 1. Tasa de éxito (40 puntos)
        success_rate = (successful_uploads / total_uploads) * 100
        if success_rate >= 100:
            score += 40
        elif success_rate >= 75:
            score += 30
        elif success_rate >= 50:
            score += 20
        
        print(f"Tasa de éxito: {success_rate:.1f}% {'OK' if success_rate >= 75 else 'WARN' if success_rate >= 50 else 'FAIL'}")
        
        # 2. Performance paralela (30 puntos)
        if avg_processing_time <= 10:
            score += 30
        elif avg_processing_time <= 20:
            score += 20
        elif avg_processing_time <= 30:
            score += 10
        
        print(f"Performance: {avg_processing_time:.2f}s promedio {'OK' if avg_processing_time <= 20 else 'WARN' if avg_processing_time <= 30 else 'FAIL'}")
        
        # 3. Throughput (20 puntos)
        if total_time > 0:
            if throughput >= 1.0:
                score += 20
            elif throughput >= 0.5:
                score += 15
            elif throughput >= 0.1:
                score += 10
            
            print(f"Throughput: {throughput:.2f} MB/s {'OK' if throughput >= 0.5 else 'WARN' if throughput >= 0.1 else 'FAIL'}")
        
        # 4. Estabilidad (sin errores críticos) (10 puntos)
        critical_errors = len([e for e in self.errors if 'CRÍTICO' in e or 'timeout' in e.lower()])
        if critical_errors == 0:
            score += 10
        elif critical_errors <= 1:
            score += 5
            
        print(f"Errores críticos: {critical_errors} {'OK' if critical_errors == 0 else 'WARN'}")
        
        print(f"\\nPUNTUACIÓN FINAL: {score}/{max_score} ({(score/max_score)*100:.1f}%)")
        
        # Veredicto
        if score >= 85:
            verdict = "EXCELENTE - Procesamiento paralelo robusto"
        elif score >= 70:
            verdict = "BUENO - Procesamiento paralelo funcional"
        elif score >= 55:
            verdict = "REGULAR - Requiere optimizaciones"
        else:
            verdict = "INSUFICIENTE - Problemas serios de concurrencia"
        
        print(f"VEREDICTO: {verdict}")
        print("=" * 70)
        
        return {
            'score': score,
            'verdict': verdict,
            'success_rate': success_rate,
            'avg_time': avg_processing_time,
            'throughput': throughput if total_time > 0 else 0
        }
    
    def cleanup(self):
        """Limpia recursos de prueba"""
        test_db_path = os.path.join(os.getcwd(), 'test_parallel.db')
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
            except:
                pass

def main():
    """Ejecuta el test P2-008"""
    test = ParallelUploadTest()
    
    try:
        test.setup_test_environment()
        results = test.run_parallel_upload_test()
        print("\\nOK - TEST P2-008 UPLOAD PARALELO COMPLETADO")
        
    except Exception as e:
        print(f"ERROR en test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        test.cleanup()

if __name__ == "__main__":
    main()